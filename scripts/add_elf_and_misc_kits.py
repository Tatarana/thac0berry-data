#!/usr/bin/env python3
"""Kits de elfo (Complete Book of Elves) e kits de livros menores que estavam
fora do app (2026-11-16, pedido do usuário).

Traz do repo de mineração (thac0berry-data-mining/data/character_kits) 30 kits:

- 11 do Complete Book of Elves (CBE, cap. 10), no grupo novo "Demihuman",
  subclass "Elf", só para elfos (`mechanics.requirements.races`). Os kits
  multiclasse (Spellfilcher, Bladesinger, War Wizard, Huntsman, Collector,
  Infiltrator) listam em `allowedClasses` as classes do livro, para aparecer a
  quem tem qualquer uma delas (decisão do usuário: mais flexível), e guardam a
  combinação em `classEligibility.combination` (campo novo, opcional) para o web
  avisar quando a ficha não é essa multiclasse. O Undead Slayer (kit de qualquer
  classe) lista todas as classes;
- 11 de Wizards & Rogues of the Realms (Rogues of the Realms), 3 de Elves of
  Athas (Savage Hunter, Free-Wanderer, Procurer), Hinterland Bandit (The
  Planewalker's Handbook), Guide (Chronomancer Book), Hero, Companion e Hoplite
  (Age of Heroes), nos grupos de classe que já existem;
- corrige o `sourceBook` de Historian, Seer - Chronomancer e Traveler (já aqui,
  como Complete Wizard's Handbook; o sidebar das páginas é o do Chronomancer
  Book). Ids e grupo não mudam.

Por que não é cópia: o `mechanics` minerado desses kits estava errado em vários
(ex.: Bladesinger saía com Força 15/Constituição 15 em vez de 13/13/15/15;
Hero juntava as duas alternativas do requisito num só). Os números abaixo foram
conferidos contra o texto de cada página; nada foi chutado — o que o livro não
diz fica vazio.

Idempotente: o kit com o mesmo id é substituído no lugar.

Uso: python scripts/add_elf_and_misc_kits.py [--mining CAMINHO] [--dry-run]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from add_psionicist_kits import ARMOR_AS_CLASS, NO_TURNING  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
KITS = os.path.join(ROOT, "data", "kits.json")
FILES = ["demihuman_and_humanoid_kits.json", "campaign_and_dragon_kits.json", "wizard_kits.json"]

ALL_CLASSES = ["Fighter", "Paladin", "Ranger", "Mage", "Cleric", "Druid", "Thief", "Bard", "Ninja", "Psionicist", "Anchorite", "Gypsy"]
WARRIORS = ["Fighter", "Paladin", "Ranger"]
PRIESTS = ["Cleric", "Druid", "Specialty Priest"]

NO_ARMOR_NOTE = ""
CAST_ARMOR_NOTE = "Fighter/mages can cast spells only when unarmored or clad in elvenmade or magical armor (CBE, Chapter 10)."
STANDARD_TURNING = {"capable": True, "mode": "allowed", "notes": "Standard turning according to priest class level (druids cannot turn undead)."}

# nome -> especificação curada (conferida no texto da página).
#   group/subclass/allowed: classEligibility; combination: classes juntas (multiclasse)
#   races: requirements.races; abilities: mínimos; cash: startingCash
#   bonus: proficiências bônus (nomes do compêndio, minúsculas); bonus_notes
#   slots: (iniciais, adicionais, penalidade) das armas; setting; armor_note; turn
CBE = dict(group="Demihuman", subclass="Elf", races="Elf", setting=None)
SPECS = {
    "Archer - Elf": dict(CBE, allowed=WARRIORS, cash="5d4x10 gp", bonus=["bowyer/fletcher", "hunting"]),
    "Wilderness Runner": dict(CBE, allowed=WARRIORS, cash="3d10 gp", bonus=["endurance", "running", "set snares"]),
    "Windrider": dict(CBE, allowed=WARRIORS, cash="6d4x10 gp", bonus=["riding, airborne", "animal handling", "animal training"],
                      bonus_notes="Animal Handling and Animal Training are for the mount's species only."),
    "Herbalist": dict(CBE, allowed=PRIESTS, cash="3d6x10 gp", bonus=["healing", "herbalism"], turn=STANDARD_TURNING),
    "Undead Slayer": dict(CBE, allowed=ALL_CLASSES, cash=None, bonus=["blind-fighting"]),
    "Spellfilcher": dict(CBE, allowed=["Mage", "Thief"], combination=["Mage", "Thief"], cash="(2d4+1)x10 gp",
                         bonus=["appraising", "spellcraft", "tightrope walking"]),
    "Bladesinger": dict(CBE, allowed=["Fighter", "Mage"], combination=["Fighter", "Mage"], cash="3d6x10 gp",
                        abilities={"Strength": 13, "Constitution": 13, "Dexterity": 15, "Intelligence": 15},
                        bonus=["blind-fighting", "dancing"], armor_note=CAST_ARMOR_NOTE),
    "War Wizard": dict(CBE, allowed=["Fighter", "Mage"], combination=["Fighter", "Mage"], cash="3d6x10 gp",
                       bonus=["spellcraft"], bonus_notes="Bonus: Spellcraft, plus Engineering or Survival (choose one).",
                       armor_note=CAST_ARMOR_NOTE),
    "Huntsman": dict(CBE, allowed=["Fighter", "Thief"], combination=["Fighter", "Thief"], cash="3d6x10 gp", bonus=["hunting", "tracking"]),
    "Collector": dict(CBE, allowed=["Fighter", "Mage", "Thief"], combination=["Fighter", "Mage", "Thief"], cash="3d8x10 gp",
                      abilities={"Intelligence": 13, "Charisma": 15}, bonus=["ancient history", "engineering"]),
    "Infiltrator": dict(CBE, allowed=["Fighter", "Mage", "Thief"], combination=["Fighter", "Mage", "Thief"], cash="(2d6+2)x10 gp",
                        bonus=["disguise", "forgery", "information gathering", "observation", "tightrope walking"]),
}

# Rogues of the Realms (Wizards & Rogues of the Realms): Dexterity 9, 3 (ou 2) espaços
# de arma + 4 adicionais, penalidade -3; grupo Rogue, ambientação Forgotten Realms.
WRR = dict(group="Rogue", subclass="Thief", allowed=["Thief", "Bard"], setting="Forgotten Realms", races=None)
_WRR_CASH = {
    "Rogues of Cormyr": ("2d6x10 gp", 2, [], None),
    "Rogues of Evermeet": ("3d6x10 gp", 2, [], None),
    "Rogues of Sembia": ("4d6x10 gp", 2, [], "Recommended proficiency: Appraising."),
    "Rogues of the Cold Lands": ("2d6x10 gp", 3, ["survival"], "Bonus: Survival (arctic)."),
    "Rogues of the Dales": ("2d6x10 gp", 2, [], None),
    "Rogues of the Dragon Coast": ("3d6x10 gp", 2, [], None),
    "Rogues of the Elven Wood": ("2d6x10 gp", 2, [], None),
    "Rogues of the Island Kingdoms": ("2d6x10 gp", 2, [], None),
    "Rogues of the Unapproachable East": ("2d6x10 gp", 3, [], None),
    "Rogues of the Vast": ("2d6x10 gp", 2, [], None),
    "Rogues of the Western Heartlands": ("3d6x10 gp", 2, [], None),
}
for _name, (_cash, _slots, _bonus, _note) in _WRR_CASH.items():
    SPECS[_name] = dict(
        WRR, cash=_cash, bonus=_bonus, bonus_notes=_note, slots=(_slots, 4, "-3"),
        abilities={"Dexterity": 9, **({"Constitution": 12} if _name == "Rogues of the Cold Lands" else {})},
    )

EOA = dict(setting="Dark Sun", races="Elf")
SPECS.update({
    "Savage Hunter": dict(EOA, group="Warrior", subclass="Fighter", allowed=["Fighter", "Ranger"], cash="2d4x10 cp", bonus=["tracking"]),
    "Free-Wanderer": dict(EOA, group="Rogue", subclass="Thief", allowed=["Thief", "Bard"], cash="1d6x10 cp", bonus=[]),
    "Procurer": dict(EOA, group="Rogue", subclass="Thief", allowed=["Thief", "Bard"], cash="2d6x30 cp", bonus=["bargain"]),
    "Hinterland Bandit": dict(group="Rogue", subclass="Thief", allowed=["Thief", "Bard"], setting="Planescape", races=None,
                              cash=None, bonus=["riding, land-based"]),
    "Guide": dict(group="Wizard", subclass="Wizard", allowed=["Mage"], setting=None, races=None, cash="(1d4+1)x8 gp",
                  abilities={"Wisdom": 17}, bonus=[],
                  bonus_notes="Required: Future History or Ancient History (choose one)."),
    "Hero": dict(group="Warrior", subclass="Fighter", allowed=["Fighter"], setting=None, races=None, cash=None,
                 bonus=["endurance"]),
    "Companion": dict(group="Warrior", subclass="Fighter", allowed=["Fighter"], setting=None, races=None, cash="3d4x10 gp",
                      abilities={"Strength": 9}, bonus=[], bonus_notes="Required: Reading/Writing and Riding, Land-Based."),
    "Hoplite": dict(group="Warrior", subclass="Fighter", allowed=["Fighter"], setting=None, races=None, cash="3d4x10 gp",
                    abilities={"Strength": 11}, bonus=[], bonus_notes="Required: Ancient History (especially Military History) and Tactics."),
})
# Os requisitos do Hero são "Strength 17+, ou Strength 9+ e Intelligence e Charisma 15+": duas
# alternativas, que `abilities` (só mínimos) não representa; ficam em features.requirements.
SPECS["Hero"]["abilities"] = {}

CHRONOMANCER_SOURCE_FIX = {"Historian", "Seer - Chronomancer", "Traveler"}
CHRONOMANCER_BOOK = "Chronomancer Book"


def to_app_kit(mined, spec):
    kit = json.loads(json.dumps(mined))
    kit["classEligibility"] = {
        "classGroup": spec["group"],
        "subclass": spec["subclass"],
        "allowedClasses": list(spec["allowed"]),
    }
    if spec.get("combination"):
        kit["classEligibility"]["combination"] = list(spec["combination"])

    weapons_text = (kit["features"].get("weaponProficiencies") or "").strip()
    slots = spec.get("slots")
    kit["mechanics"] = {
        "requirements": {"abilities": dict(spec.get("abilities", {})), "alignments": [], "races": spec.get("races")},
        "weapons": {"required": [], "recommended": [], "forbidden": [], "notes": weapons_text or None},
        "weaponSlots": (
            {"initial": slots[0], "additional": slots[1], "nonproficiencyPenalty": slots[2]}
            if slots else {"initial": None, "additional": None, "nonproficiencyPenalty": None}
        ),
        "proficiencies": {"bonus": list(spec.get("bonus", [])), "recommended": [], "notes": spec.get("bonus_notes")},
        "armor": dict(ARMOR_AS_CLASS, notes=spec.get("armor_note", NO_ARMOR_NOTE)),
        "turnUndead": dict(spec.get("turn") or NO_TURNING),
        "startingCash": spec.get("cash"),
    }
    if spec.get("turn") is None:
        kit["mechanics"]["turnUndead"]["notes"] = "Not a priest kit; no turning of its own."
    kit["setting"] = spec.get("setting")
    kit.setdefault("deity", None)
    kit.setdefault("pantheon", None)
    kit.setdefault("titleInChurch", None)
    return kit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mining", default=os.path.join(ROOT, "..", "thac0berry-data-mining", "data", "character_kits"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    mined = {}
    for name in FILES:
        with open(os.path.join(args.mining, name), encoding="utf-8") as f:
            for k in json.load(f):
                mined.setdefault(k["name"], k)

    missing = [n for n in SPECS if n not in mined]
    if missing:
        raise SystemExit(f"kits não achados na mineração: {missing}")

    with open(KITS, encoding="utf-8") as f:
        kits = json.load(f)
    by_id = {k["id"]: i for i, k in enumerate(kits)}

    added = replaced = 0
    for name, spec in SPECS.items():
        kit = to_app_kit(mined[name], spec)
        if kit["id"] in by_id:
            kits[by_id[kit["id"]]] = kit
            replaced += 1
        else:
            by_id[kit["id"]] = len(kits)
            kits.append(kit)
            added += 1

    fixed = 0
    for k in kits:
        if k["name"] in CHRONOMANCER_SOURCE_FIX and k["sourceBook"] != CHRONOMANCER_BOOK:
            k["sourceBook"] = CHRONOMANCER_BOOK
            fixed += 1

    print(f"{len(SPECS)} kits: {added} novos, {replaced} substituídos; {fixed} sourceBook do Chronomancer corrigidos; total {len(kits)}")
    if args.dry_run:
        print("(nada gravado)")
        return
    with open(KITS, "w", encoding="utf-8", newline="\n") as f:
        json.dump(kits, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
