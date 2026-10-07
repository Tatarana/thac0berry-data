#!/usr/bin/env python3
"""Conserta as listas de armas e proficiências dos kits (data/kits.json).

Problema (varredura de 2026-10-07): o conversor original cortou o texto dos
kits em todas as vírgulas, sem respeitar parênteses, e tratou cabeçalhos como
itens. Afetava 79 de 351 kits:

- `proficiencies.bonus` (entra na ficha ao escolher o kit) com prefixos e
  pontuação: "Proficiency: Endurance", "animal lore. ", "Riding ";
- `proficiencies.recommended` cortado dentro de parênteses: "weaponsmithing
  (crude" + "CRH)", "(rogue" + "double slot) disguise";
- `weapons.recommended` com o cabeçalho dos kits do Faerûn ("Weapon Slots: 4",
  "Nonproficiency Penalty: -2"), que já está em `weaponSlots`;
- outros cortes ("Axe (hand" + "battle" + "or throwing)"), "Required:" e
  "Optional:" dentro de `recommended`, notas truncadas.

Regras (aprovadas pelo usuário, 2026-10-07):
1. Itens com parênteses abertos são juntados de volta.
2. Grupo no começo do item ("(general)", "(rogue, double slot)") sai.
3. Prefixos "Proficiency:", "Recommended:" saem; "Required: X" vai para
   `required`; "Optional: ..." (e o que vem depois) vai para `notes`.
4. Cabeçalho do Faerûn sai de `weapons.recommended`; "Initial Weapons" e
   "Additional Weapons" ficam em `weapons.notes`, com o texto do kit.
5. Nome com qualificador que existe no compêndio vira o nome do compêndio
   ("weaponsmithing (crude, CRH)" -> "Weaponsmithing, Crude"); sigla de livro
   sozinha entre parênteses sai ("camouflage (CRH)" -> "camouflage").
6. Casos fora do padrão: MANUAL, abaixo, conferidos com o texto do kit.

Uso:  python scripts/fix_kit_lists.py [--dry-run]
"""
import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
KITS = os.path.join(ROOT, "data", "kits.json")
PROFICIENCIES = os.path.join(ROOT, "data", "proficiencies.json")

BOOK_TAGS = {"CRH", "CTH", "CFH", "CPrH", "CPH", "CBH", "CWH", "CBDw", "CBDH", "CSH", "POSP", "PO:SP", "CGH", "CEH", "CDwH", "CHH", "CBN", "CNH", "CPsiH", "DMG", "PHB"}
FAERUN_HEADERS = ("Weapon Slots:", "Additional Weapons:", "Nonproficiency Penalty:", "Initial Weapons:")

# Casos fora do padrão (kit -> campos novos), conferidos com features.* do kit.
MANUAL = {
    "nobleman_priest": {
        "proficiencies.bonus": ["Etiquette", "Heraldry", "Riding, Land-Based"],
        "proficiencies.recommended": ["Animal Training", "Dancing", "Gaming", "Hunting", "Local History", "Musical Instrument", "Reading/Writing"],
        "proficiencies.notes": "Warrior proficiencies cost double slots unless the priest class has a nonweapon proficiency group crossover including the Warrior group.",
    },
    "adviser": {
        "proficiencies.notes": "Reading lips is a rogue proficiency (double slot); disguise is a rogue proficiency that costs one slot (see Special Benefits).",
    },
    "outlaw_druid": {
        "proficiencies.notes": "Disguise is a rogue proficiency (double slot).",
    },
    "gladiator_fugitive_hillsfar": {
        "proficiencies.recommended": ["Blind-fighting", "endurance", "gaming", "healing", "jumping", "local history", "tumbling"],
        "proficiencies.notes": "Possibly one minor General skill gained prior to capture (agriculture, brewing, cobbling, cooking, fire-building, fishing, pottery, swimming, weaving, etc.).",
    },
    "tunnelrat_faer_n": {
        # A fonte está deslocada uma posição (o número de slots sumiu): os valores
        # vão para os rótulos certos, sem inventar o número de slots.
        "features.weaponProficiencies": "Initial Weapons: Dagger, dart, hand crossbow, knife, short sword, punching, wrestling; Additional Weapon Proficiency Slots: 4; Additional Weapons: Standard thief, excluding quarterstaff, including punching and wrestling; Nonproficiency Penalty: -3",
        "weapons.recommended": [],
        "weapons.notes": "Initial Weapons: Dagger, dart, hand crossbow, knife, short sword, punching, wrestling; Additional Weapons: Standard thief, excluding quarterstaff, including punching and wrestling",
        "weaponSlots": {"initial": None, "additional": 4, "nonproficiencyPenalty": "-3"},
    },
    "deathslayer": {
        "weapons.recommended": ["dagger", "dart", "knife", "sling", "staff"],
        "weapons.notes": "The Deathslayer may learn any of the standard wizard's weapons.",
    },
    "peasant_wizard": {
        "weapons.required": ["Bow (any)", "dagger", "knife", "spear", "dart", "sling"],
        "weapons.recommended": [],
        "weapons.notes": "Required (player's choice) — one of these.",
    },
    "barbarian_berserker_priest": {
        "weapons.recommended": ["Battle axe", "sword/bastard", "bow (any)", "sling", "warhammer"],
        "weapons.notes": "Naturally, the priesthood may limit the priest's choice of weapons and not allow him to learn all these.",
        "proficiencies.recommended": [
            "Animal Handling", "Animal Training", "Direction Sense", "Fire-Building", "Riding, Land-Based", "Weather Sense",
            "Blind-Fighting", "Hunting", "Mountaineering", "Running", "Set Snares", "Survival", "Tracking", "Herbalism", "Jumping",
        ],
        "proficiencies.notes": "Some of these are outside the priest's Nonweapon Proficiency Group Crossovers and will cost twice the listed slots if taken (PHB, page 55). The DM may require this priest to take a proficiency in the tribal specialty (Fishing, Agriculture, etc.).",
    },
    "totemic_druid": {
        "proficiencies.recommended": ["animal handling", "animal training", "healing", "herbalism", "animal lore", "survival"],
        "proficiencies.notes": "Totemic Druids have a reduced number of proficiency slots (see Special Hindrances).",
    },
    "ironsmith_wandering": {
        "proficiencies.notes": "Disguise is a bonus proficiency for female shield dwarves only; languages (racial tongue) for male shield dwarves only.",
    },
    # Notas "; None" (sobra do corte): sem nota.
    "warriors_of_the_moonsea": {"proficiencies.notes": None},
    "warriors_of_the_savage_north": {"proficiencies.notes": None},
    "warriors_of_the_shining_south": {"proficiencies.notes": None},
    "wizards_of_the_vast": {"proficiencies.notes": None},
    "wizards_of_the_western_heartlands": {"proficiencies.notes": None},
    # O BOM antes do número impediu a leitura dos slots iniciais;
    # "Nonproficiency Penalty: 3" é erro de transcrição (ladrão: -3).
    "warriors_of_the_old_empires": {"weaponSlots": {"initial": 4, "additional": 3, "nonproficiencyPenalty": "-2"}},
    "lorefinder": {"weaponSlots": {"initial": 2, "additional": 4, "nonproficiencyPenalty": "-3"}},
    "thug_waterdeep": {"weaponSlots": {"initial": 3, "additional": 4, "nonproficiencyPenalty": "-3"}},
}


def load_compendium():
    d = json.load(open(PROFICIENCIES, encoding="utf-8"))
    items = d if isinstance(d, list) else next(v for v in d.values() if isinstance(v, list))
    return {norm(p["name"]): p["name"] for p in items}


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def join_parens(items):
    """Junta pedaços cortados dentro de parênteses."""
    out, buf = [], None
    for it in items:
        buf = it if buf is None else f"{buf}, {it}"
        if buf.count("(") <= buf.count(")"):
            out.append(buf)
            buf = None
    if buf is not None:
        out.append(buf)
    return out


def clean_item(it, compendium):
    it = re.sub(r"\s+", " ", it.replace("\ufeff", "")).strip().rstrip(".").strip()
    it = re.sub(r"\bseabased\b", "sea-based", it)
    it = re.sub(r"^(Proficiency|Recommended)\s*:\s*", "", it)
    # Grupo no começo: "(general) heraldry", "(rogue, double slot) disguise".
    it = re.sub(r"^\((general|priest|warrior|rogue|wizard|psionicist)[^)]*\)\s*", "", it, flags=re.I)
    m = re.match(r"^(.*?)\s*\(([^)]*)\)$", it)
    if m:
        base, inner = m.group(1).strip(), m.group(2)
        parts = [p.strip() for p in inner.split(",") if p.strip()]
        kept = [p for p in parts if p not in BOOK_TAGS]
        if not kept:
            it = base
        else:
            qualifier = ", ".join(kept)
            candidate = compendium.get(norm(f"{base}, {qualifier}")) or compendium.get(norm(f"{base} {qualifier}"))
            it = candidate if candidate else f"{base} ({qualifier})"
    return it


def fix_list(items, compendium):
    """Lista limpa + o que saiu dela: required (de "Required:") e notes (de "Optional:")."""
    required, optional, out = [], [], []
    in_optional = False
    for it in join_parens([i for i in items if i is not None]):
        raw = it.replace("﻿", "").strip()
        if raw.startswith("Required:") or raw.startswith("''Required"):
            required.append(clean_item(re.sub(r"^''?Required[^:]*:''\s*|^Required:\s*", "", raw), compendium))
            continue
        if raw.startswith("Optional:"):
            in_optional = True
            raw = raw[len("Optional:"):].strip()
        if in_optional:
            optional.append(raw)
            continue
        c = clean_item(raw, compendium)
        if c:
            out.append(c)
    return out, required, optional


def faerun_notes(features_text):
    """'Initial Weapons' e 'Additional Weapons' do texto do kit, para weapons.notes."""
    keep = []
    for part in (features_text or "").split(";"):
        p = part.strip().rstrip(".")
        if p.startswith("Initial Weapons:") or p.startswith("Additional Weapons:"):
            keep.append(p)
    return "; ".join(keep) or None


def set_path(kit, path, value):
    obj = kit
    keys = path.split(".")
    if keys[0] in ("weapons", "proficiencies"):
        obj = kit["mechanics"]
    elif keys[0] == "weaponSlots":
        kit["mechanics"]["weaponSlots"] = value
        return
    for k in keys[:-1]:
        obj = obj.setdefault(k, {}) if obj.get(k) is not None else obj.__setitem__(k, {}) or obj[k]
    obj[keys[-1]] = value


def main():
    dry = "--dry-run" in sys.argv
    compendium = load_compendium()
    data = json.load(open(KITS, encoding="utf-8"))
    kits = data if isinstance(data, list) else data["kits"]
    report = []
    for kit in kits:
        before = json.dumps(kit, ensure_ascii=False, sort_keys=True)
        m = kit.get("mechanics") or {}
        weapons = m.get("weapons") or None
        profs = m.get("proficiencies") or None
        if weapons is not None:
            rec = weapons.get("recommended") or []
            if any(str(i).startswith(FAERUN_HEADERS) for i in rec):
                # Faerûn: o cabeçalho já está em weaponSlots; o texto vai para as notas.
                weapons["recommended"] = []
                weapons["notes"] = faerun_notes((kit.get("features") or {}).get("weaponProficiencies"))
            else:
                out, req, opt = fix_list(rec, compendium)
                weapons["recommended"] = out
                if req:
                    weapons["required"] = (weapons.get("required") or []) + [r for r in req if r not in (weapons.get("required") or [])]
                if opt:
                    note = "Optional: " + ", ".join(opt) + "."
                    weapons["notes"] = f"{weapons['notes']} {note}".strip() if weapons.get("notes") else note
            if weapons.get("required"):
                weapons["required"] = fix_list(weapons["required"], compendium)[0]
        if profs is not None:
            for field in ("bonus", "recommended"):
                if profs.get(field):
                    profs[field] = fix_list(profs[field], compendium)[0]
        for path, value in MANUAL.get(kit.get("id"), {}).items():
            set_path(kit, path, value)
        if json.dumps(kit, ensure_ascii=False, sort_keys=True) != before:
            report.append((kit["id"], json.loads(before), kit))

    for kid, old, new in report:
        print(f"## {kid}")
        for sec in ("weapons", "proficiencies"):
            o = (old.get("mechanics") or {}).get(sec) or {}
            n = (new.get("mechanics") or {}).get(sec) or {}
            for k in sorted(set(o) | set(n)):
                if o.get(k) != n.get(k):
                    print(f"  {sec}.{k}:\n    - {json.dumps(o.get(k), ensure_ascii=False)}\n    + {json.dumps(n.get(k), ensure_ascii=False)}")
        if (old.get("mechanics") or {}).get("weaponSlots") != (new.get("mechanics") or {}).get("weaponSlots"):
            print(f"  weaponSlots: {old['mechanics'].get('weaponSlots')} -> {new['mechanics'].get('weaponSlots')}")
        if (old.get("features") or {}) != (new.get("features") or {}):
            print("  features.weaponProficiencies corrigido")
    print(f"\n{len(report)} kits alterados")
    if not dry:
        with open(KITS, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")


if __name__ == "__main__":
    main()
