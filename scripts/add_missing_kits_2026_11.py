#!/usr/bin/env python3
"""Kits minerados que o app não tinha (2026-11-20, pedido do usuário: "incluir os kits que a
mineração tem e o app não").

Fonte: thac0berry-data-mining/data/character_kits/*.json (781 kits; o app tinha 506). A
comparação por nome/id/título deixa 274 de fora; destes, 40 são descartados (cartas
colecionáveis "Create Your Own"/"Checklist", páginas de lista, duplicatas e não-kits) e 234
entram. A decisão de cada um (grupo, classe, raça, cenário, jogável ou escondido, requisitos,
dinheiro, curadoria de proficiências e armas) está em `scripts/missing_kits_2026_11.json`,
lida kit a kit das páginas; este script só a aplica:

- `classEligibility` / `mechanics` vêm da classificação, não do `mechanics` minerado (que errou
  em vários kits, ver add_elf_and_misc_kits.py); o que a página não diz fica vazio;
- `sourceBook`: o livro de verdade (o rótulo minerado "AD&D 2e Supplements", "Arabian Adventures"
  etc. escondia kits de outros livros: Complete Book of Necromancers, Planewalker's Handbook...);
  kits da Dragon Magazine levam "Dragon Magazine #N";
- campos novos (opcionais): `playable: false` + `hiddenReason` + `note` nos kits que o app não
  oferece (raça ou classe que o app não tem, cenário fora da lista do Forge, decisão pendente).
  Os kits dos cenários em construção (Al-Qadim, Council of Wyrms, Spelljammer) NÃO levam
  `playable: false`: a web já os esconde pelo cenário (settingsUnderConstruction);
- a curadoria de proficiências e armas de cada kit é gravada em kit_proficiency_curation.json
  (e em kit_nonweapon_slots.json, quando o kit foge do padrão da classe) e aplicada por
  `python scripts/curate_kit_proficiencies.py`, que aborta se faltar entrada.

Idempotente: o kit com o mesmo id é substituído no lugar.

Uso: python scripts/add_missing_kits_2026_11.py [--mining CAMINHO] [--dry-run]
     python scripts/curate_kit_proficiencies.py
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from add_psionicist_kits import ARMOR_AS_CLASS, NO_TURNING, summary_from_text  # noqa: E402
from add_elf_and_misc_kits import STANDARD_TURNING  # noqa: E402
from add_dragon_magazine_kits import issue_of  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
KITS = os.path.join(ROOT, "data", "kits.json")
SPEC = os.path.join(ROOT, "scripts", "missing_kits_2026_11.json")
CURATION = os.path.join(ROOT, "scripts", "kit_proficiency_curation.json")
NONWEAPON_SLOTS = os.path.join(ROOT, "scripts", "kit_nonweapon_slots.json")
FILES = ["campaign_and_dragon_kits.json", "demihuman_and_humanoid_kits.json", "wizard_kits.json",
         "priest_kits.json", "rogue_kits.json", "warrior_kits.json"]

DRUID_ONLY_TURNING = {"capable": False, "mode": "forbidden", "notes": "Druids cannot turn undead as a core class rule."}


def clean_summary(kit):
    desc = kit["description"]
    brief = (desc.get("briefSummary") or "").strip()
    bad = (not brief or brief.startswith((":", "<", "#", "center")) or "frameless" in brief or not brief[0].isupper())
    if bad:
        brief = summary_from_text(desc["fullText"])
    return re.sub(r"\*+", "", brief).strip()


def turn_undead(spec):
    priest = spec["group"] == "Priest"
    allowed = spec["allowed"]
    if not priest:
        return dict(NO_TURNING, notes="Not a priest kit; no turning of its own.")
    if allowed and all(c == "Druid" for c in allowed):
        return dict(DRUID_ONLY_TURNING)
    return dict(STANDARD_TURNING)


def to_app_kit(mined, spec):
    kit = json.loads(json.dumps(mined))
    ce = {"classGroup": spec["group"], "subclass": spec["subclass"], "allowedClasses": list(spec["allowed"])}
    if spec.get("combination"):
        ce["combination"] = list(spec["combination"])
    kit["classEligibility"] = ce
    if spec.get("sourceBook"):
        kit["sourceBook"] = spec["sourceBook"]
    elif kit["sourceBook"] == "Dragon Magazine":
        issue = issue_of(mined)
        kit["sourceBook"] = f"Dragon Magazine #{issue}" if issue else "Dragon Magazine"
    kit["redirectAliases"] = kit.get("redirectAliases", [])
    weapons_text = (kit["features"].get("weaponProficiencies") or "").strip()
    slots = spec.get("slots")
    kit["mechanics"] = {
        "requirements": {"abilities": dict(spec.get("abilities", {})), "alignments": list(spec.get("alignments", [])), "races": spec.get("races")},
        "weapons": {"required": [], "recommended": [], "forbidden": [], "notes": weapons_text or None},
        "weaponSlots": (
            {"initial": slots[0], "additional": slots[1], "nonproficiencyPenalty": slots[2]}
            if slots else {"initial": None, "additional": None, "nonproficiencyPenalty": None}
        ),
        "proficiencies": {"bonus": [], "recommended": [], "notes": None},
        "armor": dict(ARMOR_AS_CLASS),
        "turnUndead": turn_undead(spec),
        "startingCash": spec.get("cash"),
    }
    kit["description"]["briefSummary"] = clean_summary(kit)
    kit["setting"] = spec.get("setting")
    kit.setdefault("deity", None)
    kit.setdefault("pantheon", None)
    kit.setdefault("titleInChurch", None)
    # Escondidos: o app guarda o kit, mas não o oferece (README, "Kits que faltavam").
    kit.pop("playable", None)
    kit.pop("hiddenReason", None)
    kit.pop("note", None)
    if spec.get("playable") is False:
        kit["playable"] = False
        kit["hiddenReason"] = spec["hiddenReason"]
        if spec.get("note"):
            kit["note"] = spec["note"]
    elif spec.get("note"):
        kit["note"] = spec["note"]
    return kit


def merge_by_id(items, new, key="id"):
    index = {e[key]: i for i, e in enumerate(items)}
    for e in new:
        if e[key] in index:
            items[index[e[key]]] = e
        else:
            index[e[key]] = len(items)
            items.append(e)
    return items


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mining", default=os.path.join(ROOT, "..", "thac0berry-data-mining", "data", "character_kits"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    classification = json.load(open(SPEC, encoding="utf-8"))
    specs = classification["kits"]

    mined = {}
    for name in FILES:
        with open(os.path.join(args.mining, name), encoding="utf-8") as f:
            for k in json.load(f):
                mined.setdefault(k["id"], k)
    missing = [i for i in specs if i not in mined]
    if missing:
        raise SystemExit(f"kits não achados na mineração: {missing}")

    kits = json.load(open(KITS, encoding="utf-8"))
    by_id = {k["id"]: i for i, k in enumerate(kits)}
    names = {k["name"].lower(): k["id"] for k in kits}
    new = []
    for i, spec in specs.items():
        k = to_app_kit(mined[i], spec)
        clash = names.get(k["name"].lower())
        if clash and clash != k["id"]:
            raise SystemExit(f"nome já existe no app ({clash}): {k['name']}; a ficha guarda o kit pelo nome")
        new.append(k)
    names_new = [k["name"].lower() for k in new]
    if len(set(names_new)) != len(names_new):
        raise SystemExit("nomes repetidos entre os kits novos")

    added = replaced = 0
    for k in new:
        if k["id"] in by_id:
            kits[by_id[k["id"]]] = k
            replaced += 1
        else:
            by_id[k["id"]] = len(kits)
            kits.append(k)
            added += 1

    curation = json.load(open(CURATION, encoding="utf-8"))
    merge_by_id(curation, [dict(id=i, **spec["curation"]) for i, spec in specs.items()])
    slots = json.load(open(NONWEAPON_SLOTS, encoding="utf-8"))
    for i, spec in specs.items():
        if spec.get("nws"):
            slots[i] = spec["nws"]

    print(f"{len(specs)} kits: {added} novos, {replaced} substituídos; kits.json: {len(kits)}; descartados: {len(classification['discard'])}")
    if args.dry_run:
        print("(nada gravado)")
        return
    with open(KITS, "w", encoding="utf-8", newline="\n") as f:
        json.dump(kits, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(CURATION, "w", encoding="utf-8", newline="\n") as f:
        json.dump(curation, f, ensure_ascii=False, indent=1)
        f.write("\n")
    with open(NONWEAPON_SLOTS, "w", encoding="utf-8", newline="\n") as f:
        json.dump(slots, f, ensure_ascii=False, indent=1)
        f.write("\n")


if __name__ == "__main__":
    main()
