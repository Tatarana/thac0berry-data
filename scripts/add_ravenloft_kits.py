#!/usr/bin/env python3
"""GT4b (Ravenloft): os kits do artigo "Denizens of Dread" (Dragon Magazine Annual 1998).

Fonte: `../thac0berry-data-mining/data/character_kits/campaign_and_dragon_kits.json`.
A extração gravou a classe desses kits como "Dragon Magazine" e deixou as
proficiências bônus e parte dos requisitos vazias; por isso eles nunca
entraram no kits.json. Aqui cada kit entra com os campos corrigidos à mão,
pelo texto do próprio kit (linha "Class/Race" e as seções de proficiências).

Decisões do usuário (2026-10-12):
- os 6 kits entram com o cenário "Ravenloft" (a web só os mostra quando a
  campanha tem Ravenloft ligado);
- Psychologue também para Gypsy e Bard, que o texto permite "a critério do mestre";
- Warder ("fighter and priest classes"): grupos Warrior e Priest.

Os kits do suplemento "Champions of the Mists" não estão em nenhuma fonte do
data-mining (só os nomes, no artigo "Harrowed Heroes"): ficam de fora.

Rodar de novo não muda nada: kit com o mesmo id já presente é pulado.

Uso:  python scripts/add_ravenloft_kits.py [--dry-run]
"""
import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
KITS = os.path.join(ROOT, "data", "kits.json")
SOURCE = os.path.join(ROOT, "..", "thac0berry-data-mining", "data", "character_kits", "campaign_and_dragon_kits.json")

ALL_CLASSES = ["Fighter", "Paladin", "Ranger", "Mage", "Cleric", "Druid", "Thief", "Bard", "Ninja", "Psionicist", "Anchorite", "Gypsy"]

# Nome no data-mining -> como entra. Classes pela linha "Class/Race" de cada kit.
SPEC = {
    "Danseur": {
        "id": "danseur",
        "name": "Danseur",
        "group": "Rogue",
        # "Bards, gypsies, and thieves may all be danseurs. Additionally, a half-Vistani of any class may be a danseur."
        "classes": ["Bard", "Thief", "Gypsy"],
        "abilities": {"Dexterity": 15, "Charisma": 14},
        "alignments": [],
        "bonus": ["Dancing", "Etiquette"],
        "recommended": ["Tumbling"],
    },
    "Dilettante": {
        "id": "dilettante",
        "name": "Dilettante",
        "group": "Rogue",
        # "No avenger, gypsy, paladin, priest, or psionicist character may be a dilettante."
        "classes": ["Fighter", "Ranger", "Mage", "Thief", "Bard", "Ninja"],
        "abilities": {},
        "alignments": [],
        "bonus": ["Etiquette", "Reading/Writing"],
        "recommended": [],
    },
    "Investigator - Dragon": {
        "id": "investigator_ravenloft",
        "name": "Investigator - Ravenloft",
        "group": "Wizard",
        # "Any class other than avenger may be an investigator."
        "classes": ALL_CLASSES,
        "abilities": {"Intelligence": 13, "Wisdom": 13},
        "alignments": [],
        "bonus": ["Reading/Writing", "Local History"],
        "recommended": ["Ancient History"],
    },
    "Psychologue": {
        "id": "psychologue",
        "name": "Psychologue",
        "group": "Wizard",
        # "Only wizards, priests, and psionicists ... Gypsies or bards may be allowed this kit at the DM's discretion."
        "classes": ["Mage", "Cleric", "Druid", "Anchorite", "Psionicist", "Gypsy", "Bard"],
        "abilities": {"Intelligence": 12, "Wisdom": 12},
        "alignments": [],
        "bonus": ["Fast-talking", "Intimidation"],
        "recommended": [],
    },
    "Stalker": {
        "id": "stalker_ravenloft",
        "name": "Stalker - Ravenloft",
        "group": "Rogue",
        # "Any class or race may take the stalker kit."
        "classes": ALL_CLASSES,
        "abilities": {"Wisdom": 13},
        "alignments": [],
        # Quem não é ranger ganha Tracking como bônus (o ranger ganha outra vantagem; ver o texto).
        "bonus": ["Tracking"],
        "recommended": [],
    },
    "Warder": {
        "id": "warder",
        "name": "Warder",
        "group": "Warrior",
        # "Only fighter and priest classes may be warders." -> grupos Warrior e Priest.
        "classes": ["Fighter", "Paladin", "Ranger", "Cleric", "Druid", "Anchorite"],
        "abilities": {},
        "alignments": ["Lawful Good", "Lawful Neutral", "Lawful Evil"],
        "bonus": ["Alertness"],
        "recommended": ["Healing"],
    },
}

PRIESTS = {"Cleric", "Druid", "Anchorite"}


def class_race_line(full_text):
    m = re.search(r"\*\*Class/Race:\*\*\s*([^\n]+)", full_text)
    return m.group(1).strip() if m else None


def build(raw, spec):
    features = dict(raw["features"])
    line = class_race_line(raw["description"]["fullText"])
    if line:
        features["requirements"] = f"Class/Race: {line} " + (features.get("requirements") or "")
    weapons = dict(raw["mechanics"]["weapons"])
    weapons.setdefault("forbidden", [])
    priests = PRIESTS & set(spec["classes"])
    return {
        "id": spec["id"],
        "name": spec["name"],
        "wikiPageTitle": raw["wikiPageTitle"],
        "redirectAliases": raw.get("redirectAliases") or [],
        "classEligibility": {"classGroup": spec["group"], "subclass": "Ravenloft", "allowedClasses": spec["classes"]},
        "sourceBook": "Dragon Magazine Annual 1998 (Denizens of Dread)",
        "features": features,
        "description": raw["description"],
        "categories": raw["categories"],
        "mechanics": {
            "requirements": {"abilities": spec["abilities"], "alignments": spec["alignments"], "races": None},
            "weapons": weapons,
            "proficiencies": {"bonus": spec["bonus"], "recommended": spec["recommended"], "notes": features.get("nonweaponProficiencies")},
            "armor": {"allowedTypes": "as_class", "shieldsAllowed": "as_class", "metalAllowed": True, "maxArmorClass": None, "notes": features.get("equipment") or ""},
            "turnUndead": (
                {"capable": True, "mode": "allowed", "notes": "The kit does not change turning: priests turn undead as their class does."}
                if priests
                else {"capable": False, "mode": "not_applicable", "notes": "Only priest classes turn undead."}
            ),
            "startingCash": raw["mechanics"].get("startingCash"),
        },
        "deity": None,
        "pantheon": None,
        "setting": "Ravenloft",
        "titleInChurch": None,
    }


def main():
    dry = "--dry-run" in sys.argv
    kits = json.load(open(KITS, encoding="utf-8"))
    raw = json.load(open(SOURCE, encoding="utf-8"))
    items = raw if isinstance(raw, list) else next(v for v in raw.values() if isinstance(v, list))
    by_name = {k["name"]: k for k in items}
    ids = {k["id"] for k in kits}
    names = {k["name"] for k in kits}
    added = 0
    for source_name, spec in SPEC.items():
        if spec["id"] in ids:
            print(f"= {spec['id']}")
            continue
        if spec["name"] in names:
            raise SystemExit(f"nome já usado por outro kit: {spec['name']}")
        kit = build(by_name[source_name], spec)
        kits.append(kit)
        added += 1
        print(f"+ {kit['id']}: {kit['name']} ({', '.join(spec['classes'])}); bônus {spec['bonus']}")
    if dry or added == 0:
        print("(nada gravado)" if dry else "(nada a mudar)")
        return
    with open(KITS, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(kits, indent=2, ensure_ascii=False) + "\n")
    print(f"{added} kits gravados")


if __name__ == "__main__":
    main()
