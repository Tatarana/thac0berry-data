#!/usr/bin/env python3
"""Tabelas 47 e 48 do PHB (carga e movimento): as colunas perdidas de volta.

Por quê (2026-10-14, achado na correção da Tabela 59 do DMG): na wiki as duas
têm cabeçalho de duas ou três linhas (a coluna da Força ocupa todas). A
importação usou só a linha de baixo como cabeçalho e cortou as linhas na
largura dele:
- Tabela 47 (Character Encumbrance): sumiram a coluna "Severe" e a "Max.
  Carried Weight"; os títulos ficaram deslocados (a Força com o título
  "Unencumbered").
- Tabela 48 (Modified Movement Rates): sumiu a última coluna (movimento 1); a
  segunda linha do cabeçalho (o movimento de quem tem base 6) também.
As tabelas abaixo foram conferidas no dump da wiki (thac0berry-data-mining,
"Encumbrance (PHB)"). Uma busca nas outras tabelas da wiki com cabeçalho de
várias linhas não achou mais nenhuma com coluna faltando.

Uso:  python scripts/fix_phb_tables_47_48.py [--dry-run]
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RULES = os.path.join(ROOT, "data", "rules.json")

T47 = "Table 47: Character Encumbrance"
H47 = ["Strength", "Unencumbered", "Light", "Moderate", "Heavy", "Severe", "Max. Carried Weight"]
R47 = [
    ["2", "0-1", "2", "3", "4", "5-6", "6"],
    ["3", "0-5", "6", "7", "8-9", "10", "10"],
    ["4-5", "0-10", "11-13", "14-16", "17-19", "20-25", "25"],
    ["6-7", "0-20", "21-29", "30-38", "39-46", "47-55", "55"],
    ["8-9", "0-35", "36-50", "51-65", "66-80", "81-90", "90"],
    ["10-11", "0-40", "41-58", "59-76", "77-96", "97-110", "110"],
    ["12-13", "0-45", "46-69", "70-93", "94-117", "118-140", "140"],
    ["14-15", "0-55", "56-85", "86-115", "116-145", "146-170", "170"],
    ["16", "0-70", "71-100", "101-130", "131-160", "161-195", "195"],
    ["17", "0-85", "86-121", "122-157", "158-193", "194-220", "220"],
    ["18", "0-110", "111-149", "150-188", "189-227", "228-255", "255"],
    ["18/01-50", "0-135", "136-174", "175-213", "214-252", "253-280", "280"],
    ["18/51-75", "0-160", "161-199", "200-238", "239-277", "278-305", "305"],
    ["18/76-90", "0-185", "186-224", "225-263", "264-302", "303-330", "330"],
    ["18/91-99", "0-235", "236-274", "275-313", "314-352", "353-380", "380"],
    ["18/00", "0-335", "336-374", "375-413", "414-452", "453-480", "480"],
]

T48 = "Table 48: Modified Movement Rates"
# Cada coluna: o movimento de quem tem base 12 e, entre parênteses, o de quem tem base 6.
H48 = ["Strength (base move 12; base 6 in parentheses)"] + [
    f"{a} ({b})" for a, b in zip([12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1], [6, 5, 5, 4, 4, 3, 3, 2, 2, 1, 1, 1])
]
R48 = [
    ["2", "1", "—", "2", "—", "—", "3", "—", "—", "4", "—", "—", "5"],
    ["3", "5", "—", "6", "—", "7", "—", "—", "8", "—", "9", "—", "—"],
    ["4-5", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21"],
    ["6-7", "20", "23", "26", "29", "32", "35", "38", "41", "44", "47", "50", "53"],
    ["8-9", "35", "40", "45", "50", "55", "60", "65", "70", "75", "80", "85", "89"],
    ["10-11", "40", "46", "52", "58", "64", "70", "76", "82", "88", "94", "100", "106"],
    ["12-13", "45", "53", "61", "69", "77", "85", "93", "101", "109", "117", "125", "133"],
    ["14-15", "55", "65", "75", "85", "95", "105", "115", "125", "135", "145", "155", "165"],
    ["16", "70", "80", "90", "100", "110", "120", "130", "140", "150", "160", "170", "180"],
    ["17", "85", "97", "109", "121", "133", "145", "157", "169", "181", "193", "205", "217"],
    ["18", "110", "123", "136", "149", "162", "175", "188", "201", "214", "227", "240", "253"],
    ["18/01-50", "135", "148", "161", "174", "187", "200", "213", "226", "239", "252", "265", "278"],
    ["18/51-75", "160", "173", "186", "199", "212", "225", "238", "251", "264", "277", "290", "303"],
    ["18/76-90", "185", "198", "211", "224", "237", "250", "263", "276", "289", "302", "315", "328"],
    ["18/91-99", "235", "248", "261", "274", "287", "300", "313", "326", "339", "352", "365", "378"],
    ["18/00", "335", "348", "361", "374", "387", "400", "413", "426", "439", "452", "465", "478"],
]

FIXES = {T47: (H47, R47, 5), T48: (H48, R48, 12)}


def main():
    dry = "--dry-run" in sys.argv
    with open(RULES, encoding="utf-8") as f:
        rules = json.load(f)
    found = {}
    for rule in rules:
        if rule["book"] != "PHB":
            continue
        for table in rule["tables"]:
            if table["title"] in FIXES:
                found.setdefault(table["title"], []).append(table)
    changed = 0
    for title, (headers, rows, old_width) in FIXES.items():
        tables = found.get(title, [])
        if len(tables) != 1:
            raise SystemExit(f"esperava 1 tabela {title!r} no PHB, achei {len(tables)}")
        table = tables[0]
        if table["headers"] == headers and table["rows"] == rows:
            continue
        # As linhas atuais têm de ser o começo das certas (a importação só cortou o fim).
        if table["rows"] != [r[:old_width] for r in rows]:
            raise SystemExit(f"{title}: as linhas atuais não são as esperadas; conferir antes de corrigir")
        table["headers"] = headers
        table["rows"] = rows
        changed += 1
        print(f"~ {title}: {len(headers)} colunas, {len(rows)} linhas")
    if changed == 0:
        print("(nada a mudar)")
        return
    if dry:
        print("(nada gravado)")
        return
    with open(RULES, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rules, indent=2, ensure_ascii=False) + "\n")
    print("gravado")


if __name__ == "__main__":
    main()
