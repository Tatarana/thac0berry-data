#!/usr/bin/env python3
"""Aplica a curadoria de proficiências e armas dos kits (data/kits.json).

Problema (2026-11-17): `mechanics.proficiencies` e `mechanics.weapons` vieram do conversor
com nomes em minúsculas, pedaços de frase ("or sling", "No bonuses", "requirements") e
listas vazias em kits cujo texto lista bônus (ex.: Spellarcher). Os apps davam zero
proficiência bônus a ~50 kits e não sabiam das escolhas, obrigações e proibições.

A curadoria (lida kit a kit do texto do livro, nomes do compêndio) fica em
`scripts/kit_proficiency_curation.json`. Este script substitui, em cada kit:
  proficiencies: bonus, bonusChoices, required, requiredChoices, recommended, forbidden
  weapons:       required, requiredChoices, recommended, forbidden, allowed, specialization
Os campos `notes` (texto do livro) ficam como estão. Campos novos são opcionais no schema.

Uso:  python scripts/curate_kit_proficiencies.py [--dry-run]
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
KITS = os.path.join(ROOT, "data", "kits.json")
PROFICIENCIES = os.path.join(ROOT, "data", "proficiencies.json")
CURATION = os.path.join(ROOT, "scripts", "kit_proficiency_curation.json")

# Grafias diferentes da mesma arma fora do PHB (mantém uma só).
WEAPON_ALIASES = {
    "Martial arts": "Martial Arts",
    "Sabre": "Saber",
    "Main gauche": "Main-gauche",
    "Belaying Pin": "Belaying pin",
    "Bolas": "Bola",
}

PROF_FIELDS = ["bonus", "bonusChoices", "required", "requiredChoices", "recommended", "forbidden"]
WEAPON_FIELDS = ["required", "requiredChoices", "recommended", "forbidden", "allowed"]


def weapon(name):
    return WEAPON_ALIASES.get(name, name)


def dedupe(items):
    seen, out = set(), []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def main():
    dry = "--dry-run" in sys.argv
    kits = json.load(open(KITS, encoding="utf-8"))
    names = {p["name"] for p in json.load(open(PROFICIENCIES, encoding="utf-8"))}
    curation = {c["id"]: c for c in json.load(open(CURATION, encoding="utf-8"))}

    missing = [k["id"] for k in kits if k["id"] not in curation]
    extra = sorted(set(curation) - {k["id"] for k in kits})
    if missing or extra:
        sys.exit(f"curadoria não bate com kits.json: faltam {missing[:5]}, sobram {extra[:5]}")

    changed = 0
    for kit in kits:
        c = curation[kit["id"]]
        prof, weap = kit["mechanics"]["proficiencies"], kit["mechanics"]["weapons"]
        before = json.dumps([prof, weap], sort_keys=True)

        for f in PROF_FIELDS:
            value = c["proficiencies"].get(f, [])
            flat = [x for group in value for x in group] if f.endswith("Choices") else value
            bad = [x for x in flat if x not in names]
            if bad:
                sys.exit(f"{kit['id']}.{f}: fora do compêndio: {bad}")
            if f in ("bonus", "recommended"):
                prof[f] = dedupe(value)
            elif value:
                prof[f] = value if f.endswith("Choices") else dedupe(value)
            else:
                prof.pop(f, None)

        for f in WEAPON_FIELDS:
            value = c["weapons"].get(f, [])
            value = [[weapon(x) for x in g] for g in value] if f.endswith("Choices") else dedupe([weapon(x) for x in value])
            if f in ("required", "recommended", "forbidden"):
                weap[f] = value
            elif value:
                weap[f] = value
            else:
                weap.pop(f, None)
        spec = c["weapons"].get("specialization")
        if spec:
            weap["specialization"] = {
                "weapons": dedupe([weapon(x) for x in spec.get("weapons", [])]),
                "mustSpecialize": bool(spec.get("mustSpecialize")),
                "othersForbidden": bool(spec.get("othersForbidden")),
            }
        else:
            weap.pop("specialization", None)

        if json.dumps([prof, weap], sort_keys=True) != before:
            changed += 1

    print(f"{changed} de {len(kits)} kits mudaram")
    if not dry:
        with open(KITS, "w", encoding="utf-8", newline="\n") as f:
            json.dump(kits, f, ensure_ascii=False, indent=2)
            f.write("\n")


if __name__ == "__main__":
    main()
