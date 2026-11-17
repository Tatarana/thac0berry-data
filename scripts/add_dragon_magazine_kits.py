#!/usr/bin/env python3
"""Kits da Dragon Magazine que estavam fora do app (2026-11-16, pedido do usuário:
"não achei o Spellarcher").

O dump tem 168 páginas de kit da Dragon Magazine; todas foram mineradas
(thac0berry-data-mining), mas só 30 (os psiônicos e poucos mais) estavam em
kits.json. Este script traz os que têm a classe comprovada pela PRÓPRIA página:

- o título da seção diz o tipo ("Spellarcher (Fighter/Mage kit)", "Sohei
  (Priest Kit)", "Delver (Dwarven-Rogue Kit)"), ou
- o texto diz a classe sem ambiguidade (ex.: "Shikari (Indian ranger)", os
  kits de guerreiros africanos e de nativos americanos), listado em MANUAL.

O `classGroup` minerado NÃO é usado: a detecção por substring original errou
muitos (Sohei, um kit de sacerdote, vinha como Warrior; Fiend Slayer e
Spiritualist, de mago, como Al-Qadim e Priest; Earthstoker, de druida, como
Wizard). Os kits de meio-elfo do artigo "The Complete Half-Elf" (#214) são
multiclasse e vão para o grupo Demihuman, como os do Complete Book of Elves.

Ficam de fora (listados na saída): kits do Masque of the Red Death (outro
sistema de classes: Mystic, Tradesman...), kits de dragões e meio-dragões (o
app não tem a raça) e os de classe ambígua no texto.

`mechanics` só leva o que o texto garante: o dinheiro inicial (quando há uma
fórmula de dados) e o necessário ao app; requisitos de atributo e
proficiências bônus ficam só no texto (`features`), sem número chutado.

Idempotente: kit com o mesmo id é substituído no lugar. Kit cujo NOME já existe
no app (a ficha guarda o kit pelo nome) é pulado e listado.

Uso: python scripts/add_dragon_magazine_kits.py [--mining CAMINHO] [--dry-run]
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from add_psionicist_kits import ARMOR_AS_CLASS, NO_TURNING, summary_from_text  # noqa: E402
from add_elf_and_misc_kits import STANDARD_TURNING  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
KITS = os.path.join(ROOT, "data", "kits.json")

WARRIORS = ["Fighter", "Paladin", "Ranger"]
PRIESTS = ["Cleric", "Druid", "Specialty Priest"]
ROGUES = ["Thief", "Bard"]
CLASS_WORD = {"mage": "Mage", "wizard": "Mage", "cleric": "Cleric", "druid": "Druid", "ranger": "Ranger",
              "thief": "Thief", "fighter": "Fighter", "paladin": "Paladin"}


def elig(group, subclass, allowed, **extra):
    return dict(group=group, subclass=subclass, allowed=list(allowed), **extra)


def from_hint(hint):
    """Tipo do kit pelo título da seção ("Fighter/Mage kit"); None se não for um que conhecemos."""
    h = hint.lower().strip()
    if h in ("warrior kit",):
        return elig("Warrior", "Fighter", WARRIORS)
    if h == "fighter kit":
        return elig("Warrior", "Fighter", ["Fighter"])
    if h == "fighter or ranger kit":
        return elig("Warrior", "Fighter", ["Fighter", "Ranger"])
    if h == "ranger kit":
        return elig("Warrior", "Ranger", ["Ranger"])
    if h == "paladin kit":
        return elig("Warrior", "Paladin", ["Paladin"])
    if h == "thief kit":
        return elig("Rogue", "Thief", ["Thief"])
    if h == "rogue kit":
        return elig("Rogue", "Thief", ROGUES)
    if h == "bard kit":
        return elig("Rogue", "Bard", ["Bard"])
    if h == "ninja kit":
        return elig("Rogue", "Ninja", ["Ninja"])
    if h in ("priest kit", "monk kit"):
        return elig("Priest", "Any Priest", PRIESTS)
    if h == "druid kit":
        return elig("Priest", "Druid", ["Druid"])
    if h in ("wizard kit", "wizards kit", "divination wizard kit", "necromancer kit"):
        return elig("Wizard", "Wizard", ["Mage"])
    if h == "warrior or rogue kit":
        return elig("Warrior", "Fighter", WARRIORS + ROGUES)
    if h == "priest or wizard kit":
        return elig("Priest", "Any Priest", PRIESTS + ["Mage"])
    if h == "dwarven-rogue kit":
        return elig("Demihuman", "Dwarf", ROGUES, races="Dwarf")
    if h == "dwarven-priest kit":
        return elig("Demihuman", "Dwarf", PRIESTS, races="Dwarf")
    m = re.fullmatch(r"((?:mage|cleric|druid|ranger|thief|fighter)(?:/(?:mage|cleric|druid|ranger|thief|fighter))+) kit", h)
    if m:  # multiclasse do artigo "The Complete Half-Elf" (#214)
        classes = [CLASS_WORD[c] for c in m.group(1).split("/")]
        return elig("Demihuman", "Half-Elf", classes, races="Half-Elf", combination=classes)
    return None


# Sem classe no título, mas o texto da página é inequívoco.
MANUAL = {
    "Shikari": elig("Warrior", "Ranger", ["Ranger"]),                       # "Shikari (Indian ranger)"
    "Baule Diviner": elig("Wizard", "Wizard", ["Mage"]),                    # adivinhos, "wizards"
    "Bokor": elig("Wizard", "Wizard", ["Mage"]),                            # "an evil sorcerer"
    "Houngan": elig("Wizard", "Wizard", ["Mage"]),                          # "Mages who take this kit..."
    "Mambo": elig("Wizard", "Wizard", ["Mage"]),                            # a versão feminina do Houngan
    "Slayer-Mage - Dragon": elig("Wizard", "Wizard", ["Mage"]),             # "a wizard trained to battle dragons"
    "Eastern Woodland Warrior": elig("Warrior", "Fighter", ["Fighter", "Ranger"]),
    "Great Plains Warrior": elig("Warrior", "Fighter", ["Fighter", "Ranger"]),
    "Southwest Desert Warrior": elig("Warrior", "Fighter", ["Fighter", "Ranger"]),
    "Ashanti Warrior": elig("Warrior", "Fighter", ["Fighter", "Ranger"]),
    "Benin Hunter": elig("Warrior", "Fighter", ["Fighter", "Ranger"]),
    "Bornu Horseman": elig("Warrior", "Fighter", ["Fighter", "Ranger"]),
    "Kalahari Bushman": elig("Warrior", "Fighter", ["Fighter", "Ranger"]),
    "Kongo Pygmy": elig("Warrior", "Fighter", ["Fighter", "Ranger"]),
    "Kushite Elephant Warrior": elig("Warrior", "Fighter", ["Fighter", "Ranger"]),
    "Shaman - Dragon": elig("Priest", "Any Priest", PRIESTS),               # "a priest of ... nature"
    "Animal Priestess": elig("Priest", "Any Priest", PRIESTS),
    "Kongo Witch Doctor": elig("Priest", "Any Priest", PRIESTS),            # "clerics and specialty priests"
    "Legba": elig("Priest", "Any Priest", PRIESTS),                         # "the priests of the elements"
    "Obeah-Man": elig("Priest", "Any Priest", PRIESTS),
    "Poro": elig("Priest", "Any Priest", PRIESTS),
    "Bikaver": elig("Priest", "Any Priest", PRIESTS),                       # Taltos: "essentially priests"
    "Varazslo": elig("Wizard", "Wizard", ["Mage"]),                         # Taltos: warlock
    "Allati": elig("Warrior", "Barbarian", ["Fighter"]),                    # Taltos: "a barbarian taltos kit"
    "Zelganok": elig("Warrior", "Fighter", WARRIORS),                       # Taltos: "a mystic warrior"
    "Skywarden": elig("Demihuman", "Avariel", ["Fighter", "Cleric"], races="Avariel"),  # "open to fighters, clerics, and fighter/clerics"
    "Talon": elig("Demihuman", "Avariel", WARRIORS, races="Avariel"),       # avariel guerreiros
    "Caradhaker": elig("Demihuman", "Dwarf", ["Fighter", "Cleric", "Thief"], races="Dwarf"),  # "any class normally available to dwarves"
}
# Kits do Masque of the Red Death, #215/#236 ("Attack as: Mystic"): classes próprias do cenário.
MOTRD = {"Athlete", "Lawyer", "Scientist", "Thespian - Dragon", "Enthusiast", "Exorcist"}
EXCLUDED = {
    **{n: "Masque of the Red Death (MotRD): usa classes próprias (Mystic, Tradesman…)" for n in MOTRD},
    "Dragon Sage": "kit de dragão (Council of Wyrms): o app não tem a raça",
    "Dragon Sage - Dragon": "kit de dragão (Council of Wyrms): o app não tem a raça",
    "Exile - Dragon": "kit de meio-dragão: o app não tem a raça",
    "Ward - Dragon": "kit de meio-dragão: o app não tem a raça",
    "Manikin": "modificação de constructo, 'qualquer classe': não é um kit de personagem comum",
    "Zande Witch Woman": "classe ambígua no texto (guerreira ou sacerdotisa?)",
    "Tribal Scout": "classe ambígua no texto (ladino ou guerreiro?)",
    "Mystery Man": "classe ambígua no texto (lida com magia de mago, minerado como Priest)",
    "Sarkany": "Taltos: a página não diz a classe",
    "Alakvalt": "Taltos: a página não diz a classe",
    "Boszorkany": "Taltos: ambígua (sacerdote ou mago?)",
    "Courier": "Avariel: a página não diz a classe",
    "Kshatriya": "classe ambígua no texto (guerreiro sagrado, paladino?)",
}

DICE_RE = re.compile(r"\(?\s*(\d+d\d+(?:\s*[+-]\s*\d+)?)\s*\)?\s*(?:[x×*]\s*(\d+))?\s*(gp|cp|sp)?", re.I)


def starting_cash(wealth_text):
    """Só quando o texto traz fórmula de dados E moeda gp/cp/sp explícita (ex. '3d6x10 gp',
    '(3d4+3) x 30 cp'); rúpias, 'ceramic pieces' etc. ficam None, sem converter na moeda errada."""
    m = DICE_RE.search(wealth_text or "")
    if not m or not m.group(3):
        return None
    dice = re.sub(r"\s+", "", m.group(1))
    if m.group(2):
        dice = f"({dice})x{m.group(2)}" if re.search(r"[+-]", dice) else f"{dice}x{m.group(2)}"
    return f"{dice} {m.group(3).lower()}"


def issue_of(kit):
    m = re.search(r"Dragon Magazine #?(\d+)", kit["description"]["rawWikitext"][:800])
    return m.group(1) if m else None


def section_hint(kit):
    head = re.search(r"^==\s*([^=\n]+?)\s*==", kit["description"]["rawWikitext"], re.M)
    head = head.group(1) if head else ""
    m = re.search(r"\(([^)]*kit[^)]*)\)", head, re.I)
    return m.group(1) if m else ""


def to_app_kit(mined, spec):
    kit = json.loads(json.dumps(mined))
    ce = {"classGroup": spec["group"], "subclass": spec["subclass"], "allowedClasses": list(spec["allowed"])}
    if spec.get("combination"):
        ce["combination"] = list(spec["combination"])
    kit["classEligibility"] = ce
    issue = issue_of(mined)
    kit["sourceBook"] = f"Dragon Magazine #{issue}" if issue else "Dragon Magazine"
    kit["redirectAliases"] = kit.get("redirectAliases", [])
    priest = spec["group"] == "Priest"
    weapons_text = (kit["features"].get("weaponProficiencies") or "").strip()
    kit["mechanics"] = {
        "requirements": {"abilities": {}, "alignments": [], "races": spec.get("races")},
        "weapons": {"required": [], "recommended": [], "forbidden": [], "notes": weapons_text or None},
        "weaponSlots": {"initial": None, "additional": None, "nonproficiencyPenalty": None},
        "proficiencies": {"bonus": [], "recommended": [], "notes": None},
        "armor": dict(ARMOR_AS_CLASS),
        "turnUndead": dict(STANDARD_TURNING if priest else NO_TURNING),
        "startingCash": starting_cash(kit["features"].get("wealthOptions")),
    }
    if not priest:
        kit["mechanics"]["turnUndead"]["notes"] = "Not a priest kit; no turning of its own."
    desc = kit["description"]
    brief = desc.get("briefSummary", "")
    if brief.lstrip().startswith(":*This was originally published") or not brief.strip():
        brief = summary_from_text(desc["fullText"])
    desc["briefSummary"] = re.sub(r"\*+", "", brief).strip()
    kit["setting"] = None
    kit.setdefault("deity", None)
    kit.setdefault("pantheon", None)
    kit.setdefault("titleInChurch", None)
    return kit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mining", default=os.path.join(ROOT, "..", "thac0berry-data-mining", "data", "character_kits"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with open(os.path.join(args.mining, "campaign_and_dragon_kits.json"), encoding="utf-8") as f:
        mined = json.load(f)
    with open(KITS, encoding="utf-8") as f:
        kits = json.load(f)
    by_id = {k["id"]: i for i, k in enumerate(kits)}
    app_titles = {k["wikiPageTitle"] for k in kits}
    app_names = {k["name"].lower() for k in kits}

    todo, excluded, unclassified, name_clash = [], [], [], []
    for k in mined:
        cats = k.get("categories") or []
        if "Dragon Magazine Character Kits" not in cats or k["wikiPageTitle"] in app_titles:
            continue
        name = k["name"]
        if name in EXCLUDED:
            excluded.append((name, EXCLUDED[name]))
            continue
        spec = MANUAL.get(name) or from_hint(section_hint(k))
        if not spec:
            unclassified.append((name, section_hint(k)))
            continue
        if name.lower() in app_names:
            name_clash.append(name)
            continue
        todo.append((k, spec))

    added = replaced = 0
    for k, spec in todo:
        kit = to_app_kit(k, spec)
        if kit["id"] in by_id:
            kits[by_id[kit["id"]]] = kit
            replaced += 1
        else:
            by_id[kit["id"]] = len(kits)
            kits.append(kit)
            added += 1

    fixed_summaries = 0
    for k in kits:
        brief = k["description"]["briefSummary"]
        if brief.lstrip().startswith(":*This was originally published"):
            k["description"]["briefSummary"] = re.sub(r"\*+", "", summary_from_text(k["description"]["fullText"])).strip()
            fixed_summaries += 1

    print(f"{len(todo)} kits da Dragon Magazine: {added} novos, {replaced} substituídos; kits.json: {len(kits)}; {fixed_summaries} resumos antigos com o aviso da wiki corrigidos")
    print(f"Fora ({len(excluded)}):")
    for name, why in sorted(excluded):
        print(f"  - {name}: {why}")
    if unclassified:
        print(f"SEM CLASSE ({len(unclassified)}): {unclassified}")
    if name_clash:
        print(f"NOME JÁ NO APP ({len(name_clash)}): {name_clash}")
    if args.dry_run:
        print("(nada gravado)")
        return
    with open(KITS, "w", encoding="utf-8", newline="\n") as f:
        json.dump(kits, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
