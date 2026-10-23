#!/usr/bin/env python3
"""Corrige tabelas da DMG que a extração da wiki estragou (data/rules.json).

Achado no uso (2026-10-23, "Racial Level Restrictions" quebrada na web) e
conferido com o wikitexto original (dump em thac0berry-data-mining). Dois
defeitos do extrator, os dois no cabeçalho das tabelas:

1. Canto do cabeçalho vazio ("!" sem texto, a célula acima da coluna de
   rótulos): o extrator descartou essa célula e cortou cada linha no tamanho
   do cabeçalho — a ÚLTIMA COLUNA sumiu e as outras ficaram uma coluna para a
   direita do cabeçalho. Tabelas 1 a 6 (Method I–VI: o personagem #5 inteiro;
   nas Tabelas 1 e 2 também a linha final "Suggested Class") e Tabela 7
   (Racial Class and Level Limits: a coluna Halfling).
2. Subtítulo no meio da tabela (linha só de "!"): o extrator jogou fora, e as
   linhas abaixo parecem do primeiro grupo. Tabela 34 (Individual Class
   Awards: tudo parecia de Warrior), Tabela 46 (Character Saving Throws: as
   faixas de Rogues, Warriors e Wizards sem o grupo) e Tabela 57 (Surprise
   Modifiers: sem "PC Party is:"/"Conditions are:"; e "+2" tinha virado "2").
   O subtítulo vira a primeira coluna, como na Tabela 60 do PHB.

Busca pelos outros casos (mesma data): todas as tabelas estruturadas do
rules.json comparadas com o original da wiki, pareadas pelas linhas; só estas
dez perdiam informação (as demais que mudaram de forma — General Traits,
Racial Ability Adjustments do CWS — foram reorganizadas sem perda).

Cada correção confere o cabeçalho de antes e grava cabeçalho e linhas do
original. Rodar de novo não muda nada.

Uso:  python scripts/fix_dmg_table_columns.py [--dry-run]
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RULES = os.path.join(ROOT, "data", "rules.json")

ABILITIES = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]
CHARACTERS = ["#1", "#2", "#3", "#4", "#5"]


def method(scores, suggested=None):
    rows = [[name, *values] for name, values in zip(ABILITIES, scores)]
    if suggested:
        rows.append(["Suggested Class", *suggested])
    return ["Ability", *CHARACTERS], rows


SAVE_HEADERS = [
    "Group",
    "Experience Level",
    "Paralyzation, Poison, or Death Magic",
    "Rod, Staff, or Wand",
    "Petrification or Polymorph*",
    "Breath Weapon**",
    "Spells***",
]
SAVES = {
    "Priests": [
        ["1-3", "10", "14", "13", "16", "15"],
        ["4-6", "9", "13", "12", "15", "14"],
        ["7-9", "7", "11", "10", "13", "12"],
        ["10-12", "6", "10", "9", "12", "11"],
        ["13-15", "5", "9", "8", "11", "10"],
        ["16-18", "4", "8", "7", "10", "9"],
        ["19+", "2", "6", "5", "8", "7"],
    ],
    "Rogues": [
        ["1-4", "13", "14", "12", "16", "15"],
        ["5-8", "12", "12", "11", "15", "13"],
        ["9-12", "11", "10", "10", "14", "11"],
        ["13-16", "10", "8", "9", "13", "9"],
        ["17-20", "9", "6", "8", "12", "7"],
        ["21+", "8", "7", "4", "11", "5"],
    ],
    "Warriors": [
        ["0", "16", "18", "17", "20", "19"],
        ["1-2", "14", "16", "15", "17", "17"],
        ["3-4", "13", "15", "14", "16", "16"],
        ["5-6", "11", "13", "12", "13", "14"],
        ["7-8", "10", "12", "11", "12", "13"],
        ["9-10", "8", "10", "9", "9", "11"],
        ["11-12", "7", "9", "8", "8", "10"],
        ["13-14", "5", "7", "6", "5", "8"],
        ["15-16", "4", "6", "5", "4", "7"],
        ["17+", "3", "5", "4", "4", "6"],
    ],
    "Wizards": [
        ["1-5", "14", "11", "13", "15", "12"],
        ["6-10", "13", "9", "11", "13", "10"],
        ["11-15", "11", "7", "9", "11", "8"],
        ["16-20", "10", "5", "7", "9", "6"],
        ["21+", "8", "3", "5", "7", "4"],
    ],
}

# (regra, título) -> (cabeçalho de antes, cabeçalho certo, linhas certas)
FIXES = {
    ("dmg_ch01_player_character_ability_scores", "Table 1: Method I Characters"): (
        CHARACTERS,
        *method(
            [["10", "8", "13", "6", "16"], ["8", "7", "8", "15", "10"], ["12", "8", "9", "10", "14"],
             ["13", "8", "14", "9", "12"], ["12", "10", "11", "9", "13"], ["7", "12", "14", "7", "8"]],
            ["Ma", "Cl", "F/Ma", "Th", "F"],
        ),
    ),
    ("dmg_ch01_player_character_ability_scores", "Table 2: Method II Characters"): (
        CHARACTERS,
        *method(
            [["12", "11", "9", "9", "15"], ["10", "15", "12", "13", "14"], ["11", "11", "16", "14", "14"],
             ["13", "11", "12", "13", "14"], ["16", "13", "13", "11", "13"], ["10", "11", "14", "9", "12"]],
            ["Cl", "Th", "Cl", "Ma", "F"],
        ),
    ),
    ("dmg_ch01_player_character_ability_scores", "Table 3: Method III Characters"): (
        CHARACTERS,
        *method(
            [["15", "13", "14", "15", "14"], ["11", "12", "9", "10", "12"], ["15", "13", "13", "12", "14"],
             ["7", "8", "8", "9", "11"], ["8", "7", "7", "6", "9"], ["7", "12", "7", "7", "11"]]
        ),
    ),
    ("dmg_ch01_player_character_ability_scores", "Table 4: Method IV Characters"): (
        CHARACTERS,
        *method(
            [["15", "14", "15", "16", "15"], ["13", "10", "13", "15", "13"], ["13", "12", "15", "13", "13"],
             ["13", "9", "13", "12", "13"], ["13", "9", "11", "13", "12"], ["10", "9", "11", "13", "12"]]
        ),
    ),
    ("dmg_ch01_player_character_ability_scores", "Table 5: Method V Characters"): (
        CHARACTERS,
        *method(
            [["17", "15", "16", "14", "18/37"], ["14", "14", "13", "15", "12"], ["15", "14", "14", "15", "17"],
             ["13", "11", "10", "14", "8"], ["13", "10", "11", "15", "8"], ["9", "13", "8", "7", "9"]]
        ),
    ),
    ("dmg_ch01_player_character_ability_scores", "Table 6: Method VI Characters"): (
        CHARACTERS,
        *method(
            [["17", "15", "16", "17", "18/71"], ["12", "11", "11", "13", "12"], ["12", "9", "12", "18", "14"],
             ["11", "9", "10", "11", "11"], ["9", "9", "10", "8", "10"], ["8", "8", "9", "9", "13"]]
        ),
    ),
    ("dmg_ch02_racial_level_restrictions", "Table 7: Racial Class and Level Limits*"): (
        ["Human", "Dwarf", "Elf", "Gnome", "Half-elf", "Halfling"],
        ["Class", "Human", "Dwarf", "Elf", "Gnome", "Half-elf", "Halfling"],
        [
            ["Bard", "U", "X", "X", "X", "U", "X"],
            ["Cleric", "U", "10", "12", "9", "14", "8"],
            ["Druid", "U", "X", "X", "X", "9", "X"],
            ["Fighter", "U", "15", "12", "11", "14", "9"],
            ["Illus.", "U", "X", "X", "15", "X", "X"],
            ["Mage", "U", "X", "15", "X", "12", "X"],
            ["Paladin", "U", "X", "X", "X", "X", "X"],
            ["Ranger", "U", "X", "15", "X", "16", "X"],
            ["Thief", "U", "12", "12", "13", "12", "15"],
        ],
    ),
    ("dmg_ch08_experience_tables", "Table 34: Individual Class Awards"): (
        ["Warrior", "Award"],
        ["Group", "Action", "Award"],
        [
            ["Warrior", "Per Hit Die of creature defeated", "10 XP/level"],
            ["Priest", "Per successful use of a granted power", "100 XP"],
            ["Priest", "Spells cast to further ethos", "100 XP/spell level*"],
            ["Priest", "Making potion or scroll", "XP value"],
            ["Priest", "Making permanent magical item", "XP value"],
            ["Wizard", "Spells cast to overcome foes or problems", "50 XP/spell level"],
            ["Wizard", "Spells successfully researched", "500 XP/spell level"],
            ["Wizard", "Making potion or scroll", "XP value"],
            ["Wizard", "Making permanent magical item", "XP value"],
            ["Rogue", "Per successful use of a special ability", "200 XP"],
            ["Rogue", "Per gold piece value of treasure obtained", "2 XP"],
            ["Rogue", "Per Hit Die of creatures defeated (bard only)", "5 XP"],
        ],
    ),
    ("dmg_ch09_the_saving_throw", "Table 46: Character Saving Throws"): (
        [
            "Character Group and Experience Level",
            "Paralyzation, Poison, or Death Magic",
            "Rod, Staff, or Wand",
            "Petrification or Polymorph*",
            "Breath Weapon**",
            "Spells***",
        ],
        SAVE_HEADERS,
        [[group, *row] for group, rows in SAVES.items() for row in rows],
    ),
    ("dmg_ch11_surprise", "Table 57: Surprise Modifiers"): (
        ["Other Party is:", "Group's Modifier"],
        ["Situation", "Condition", "Group's Modifier"],
        [
            ["Other party is", "Silenced", "-2"],
            ["Other party is", "Invisible", "-2"],
            ["Other party is", "Distinctive odor (smoke, powerful stench, etc.)", "+2"],
            ["Other party is", "Every 10 members", "+1"],
            ["Other party is", "Camouflaged", "-1 to -3"],
            ["PC party is", "Fleeing", "-2"],
            ["PC party is", "In poor light", "-1"],
            ["PC party is", "In darkness", "-4"],
            ["PC party is", "Panicked", "-2"],
            ["PC party is", "Anticipating attack*", "+2"],
            ["PC party is", "Suspicious*", "+2"],
            ["Conditions are", "Rainy", "-1"],
            ["Conditions are", "Heavy fog", "-2"],
            ["Conditions are", "Extremely still", "+2"],
        ],
    ),
}


def main():
    dry = "--dry-run" in sys.argv
    with open(RULES, encoding="utf-8") as f:
        rules = json.load(f)
    by_id = {r["id"]: r for r in rules}
    changed = 0
    for (rule_id, title), (old_headers, headers, rows) in FIXES.items():
        rule = by_id.get(rule_id)
        if rule is None:
            raise SystemExit(f"regra não encontrada: {rule_id}")
        table = next((t for t in rule.get("tables") or [] if t.get("title") == title), None)
        if table is None:
            raise SystemExit(f"{rule_id}: tabela não encontrada: {title}")
        if table["headers"] == headers and table["rows"] == rows:
            print(f"{title}: já corrigida")
            continue
        if table["headers"] != old_headers:
            raise SystemExit(f"{title}: cabeçalho inesperado {table['headers']} (a tabela mudou?)")
        widths = {len(r) for r in rows}
        if widths != {len(headers)}:
            raise SystemExit(f"{title}: linhas com largura {widths}, cabeçalho {len(headers)}")
        table["headers"] = headers
        table["rows"] = rows
        changed += 1
        print(f"{title}: corrigida ({len(headers)} colunas, {len(rows)} linhas)")
    if dry or changed == 0:
        print("(dry-run: nada gravado)" if dry else "(nada a corrigir)")
        return
    with open(RULES, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rules, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
