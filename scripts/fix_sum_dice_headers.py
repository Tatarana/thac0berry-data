#!/usr/bin/env python3
"""Tabelas 2–20 do DMG: o cabeçalho passa a dizer o dado ("Dice Roll (1d8+1d12)").

Por quê (2026-10-13, backlog do Table Grimoire): o DMG diz que o número de
2 a 20 sai de "1d8 somado a 1d12", mas o cabeçalho só diz "Dice Roll", e a web
deduzia 2d10 pela faixa (outra distribuição: com 1d8+1d12, 9 a 13 têm a mesma
chance; com 2d10 o pico é só o 11). O motor de dados da web passou a ler a
soma no cabeçalho.

Uso:  python scripts/fix_sum_dice_headers.py [--dry-run]
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RULES = os.path.join(ROOT, "data", "rules.json")

# (id da regra, título da tabela): cabeçalho da primeira coluna.
FIXES = {
    ("dmg_ch11_creating_encounter_tables", "Table 54: 2-20 Encounter Table"): "Dice Roll (1d8+1d12)",
    ("dmg_ch11_creating_encounter_tables", "Example: 2-20 Encounter Table for the Desert of Shaar"): "Dice Roll (1d8+1d12)",
}


def main():
    dry = "--dry-run" in sys.argv
    with open(RULES, encoding="utf-8") as f:
        rules = json.load(f)
    found = set()
    changed = 0
    for rule in rules:
        for table in rule["tables"]:
            key = (rule["id"], table["title"])
            if key not in FIXES:
                continue
            found.add(key)
            if table["headers"][0] != FIXES[key]:
                print(f"~ {key[1]}: {table['headers'][0]!r} → {FIXES[key]!r}")
                table["headers"][0] = FIXES[key]
                changed += 1
    missing = set(FIXES) - found
    if missing:
        raise SystemExit(f"tabelas não encontradas: {sorted(missing)}")
    if dry or changed == 0:
        print("(nada gravado)" if dry else "(nada a mudar)")
        return
    with open(RULES, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rules, indent=2, ensure_ascii=False) + "\n")
    print(f"{changed} cabeçalhos gravados")


if __name__ == "__main__":
    main()
