#!/usr/bin/env python3
"""Tabela 59 do DMG (Encounter Reactions): a coluna "Hostile" de volta.

Por quê (2026-10-14, CT6 do Combat Tracker da web): na wiki a tabela tem
cabeçalho de duas linhas ("Modified Die Roll" ocupando as duas e "Player
Characters are:" sobre as quatro atitudes). A importação pegou só a segunda
linha como cabeçalho e cortou as linhas na largura dele: a coluna da rolagem
ficou com o título "Friendly" e a coluna dos PCs hostis (com os "Flight")
sumiu. A tabela abaixo foi conferida no dump da wiki
(`Encounter Reactions (DMG)`, thac0berry-data-mining).

Uso:  python scripts/fix_dmg_table_59.py [--dry-run]
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RULES = os.path.join(ROOT, "data", "rules.json")

TITLE = "Table 59: Encounter Reactions"
HEADERS = ["Modified Die Roll (2d10)", "Friendly PCs", "Indifferent PCs", "Threatening PCs", "Hostile PCs"]
# Rolagem, e a reação das criaturas conforme os PCs estão: amigáveis, indiferentes, ameaçadores, hostis.
ROWS = [
    ["2 or less", "Friendly", "Friendly", "Friendly", "Flight"],
    ["3", "Friendly", "Friendly", "Friendly", "Flight"],
    ["4", "Friendly", "Friendly", "Cautious", "Flight"],
    ["5", "Friendly", "Friendly", "Cautious", "Flight"],
    ["6", "Friendly", "Friendly", "Cautious", "Cautious"],
    ["7", "Friendly", "Indifferent", "Cautious", "Cautious"],
    ["8", "Indifferent", "Indifferent", "Cautious", "Cautious"],
    ["9", "Indifferent", "Indifferent", "Cautious", "Threatening"],
    ["10", "Indifferent", "Indifferent", "Threatening", "Threatening"],
    ["11", "Indifferent", "Indifferent", "Threatening", "Threatening"],
    ["12", "Cautious", "Cautious", "Threatening", "Threatening"],
    ["13", "Cautious", "Cautious", "Threatening", "Hostile"],
    ["14", "Cautious", "Cautious", "Threatening", "Hostile"],
    ["15", "Cautious", "Threatening", "Threatening", "Hostile"],
    ["16", "Threatening", "Threatening", "Hostile", "Hostile"],
    ["17", "Threatening", "Threatening", "Hostile", "Hostile"],
    ["18", "Threatening", "Threatening", "Hostile", "Hostile"],
    ["19", "Hostile", "Hostile", "Hostile", "Hostile"],
    ["20", "Hostile", "Hostile", "Hostile", "Hostile"],
]


def main():
    dry = "--dry-run" in sys.argv
    with open(RULES, encoding="utf-8") as f:
        rules = json.load(f)
    found = []
    for rule in rules:
        if rule["book"] != "DMG":
            continue
        for table in rule["tables"]:
            if table["title"] == TITLE:
                found.append(table)
    if len(found) != 1:
        raise SystemExit(f"esperava 1 tabela {TITLE!r} no DMG, achei {len(found)}")
    table = found[0]
    # As três primeiras colunas de atitude já estavam certas: só a de hostis faltava.
    old = [row[:4] for row in ROWS]
    if table["headers"] == HEADERS and table["rows"] == ROWS:
        print("(nada a mudar)")
        return
    if table["rows"] != old:
        raise SystemExit("as linhas atuais não são as esperadas; conferir antes de corrigir")
    table["headers"] = HEADERS
    table["rows"] = ROWS
    print(f"~ {TITLE}: {len(HEADERS)} colunas, {len(ROWS)} linhas")
    if dry:
        print("(nada gravado)")
        return
    with open(RULES, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rules, indent=2, ensure_ascii=False) + "\n")
    print("gravado")


if __name__ == "__main__":
    main()
