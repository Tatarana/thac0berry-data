#!/usr/bin/env python3
"""GT4b (Council of Wyrms): regras com tabelas do Council of Wyrms Setting (CWS).

Fonte: as páginas do livro no dump da wiki AD&D 2e
(`../thac0berry-data-mining/dumps/adnd2e_pages_current.xml`).

Decisões do usuário (2026-10-12): cenário "Council of Wyrms"
(scripts/build_books.py); entram só as páginas com tabelas (uma regra por
página, com o texto inteiro), como nos outros cenários da GT4b.

- Fica de fora a aventura "Not the Draca" (texto de aventura, com uma tabela
  de choque dos filhotes no meio).
- Os geradores de magias aleatórias vêm dentro de uma tabela de layout (duas
  colunas de tabelas): o invólucro sai e cada nível vira uma tabela d100. A
  wiki não tem a tabela de magias de mago do 6º nível (pula do 5º para o 7º).
- As tabelas de expectativa de vida (Tabela 19) vêm "deitadas" (faixas de
  idade no cabeçalho, categorias numa linha só): viram duas colunas.

O resto é o mesmo do Planescape (scripts/add_planescape.py: build_rule,
correções de dados por OCR, --refresh).

Uso:  python scripts/add_council_of_wyrms.py [--dry-run] [--refresh]
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from add_planescape import T, build_rule  # noqa: E402
from add_ravenloft_dod import load_pages, number_chapters  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RULES = os.path.join(ROOT, "data", "rules.json")

BOOKS = {"CWS": "Council of Wyrms Setting"}

METALLIC = ["Gold", "Silver", "Bronze", "Copper", "Brass"]
GEM = ["Amethyst", "Sapphire", "Emerald", "Topaz", "Crystal"]
CHROMATIC = ["Red", "Blue", "Green", "Black", "White"]
ALIGNMENT = {
    "Gold": "lawful good", "Silver": "lawful good", "Bronze": "lawful good", "Copper": "chaotic good",
    "Brass": "chaotic good", "Amethyst": "neutral", "Sapphire": "lawful neutral", "Emerald": "lawful neutral",
    "Topaz": "chaotic neutral", "Crystal": "chaotic neutral", "Red": "chaotic evil", "Blue": "lawful evil",
    "Green": "lawful evil", "Black": "chaotic evil", "White": "chaotic evil",
}
LEVELS = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth", "Ninth"]
LIFESPAN = ["Dragon", "Elf", "Gnome", "Dwarf", "Human"]

PAGES = {
    # --- Personagens ---
    "Player Character Races (CWS)": ("CWS", "Characters", [
        T("Table 1: Racial Ability Requirements"),
        T("Table 2: Racial Ability Adjustments"),
        T("Table 3: Racial Class and Level Limits"),
        T("Table 4: Dragon Information by Age (General)"),
        *[T(f"Table 5: {c} Dragon by Age ({ALIGNMENT[c]})") for c in METALLIC + GEM + CHROMATIC],
    ]),
    "Kindred (CWS)": ("CWS", "Characters", [T("Table 6: Preferred Kindred", ["Dragon", "Elf", "Dwarf", "Gnome"])]),
    "Half-Dragons (CWS)": ("CWS", "Characters", [
        T("Table 7: Half-Dragon Height in Inches"),
        T("Table 7: Half-Dragon Weight in Pounds"),
        T("Table 7: Half-Dragon Starting Age"),
        T("Table 7: Half-Dragon Age Range"),
        T("Table 7: Half-Dragon Thieving Skill Adjustments"),
    ]),
    "Hit Dice and Hit Points (CWS)": ("CWS", "Characters", [T("Table 8: Base Hit Dice")]),
    "Random Hatchling Selection (CWS)": ("CWS", "Characters", [T("Table 9: Random Hatchlings")]),
    "Experience and Advancement (CWS)": ("CWS", "Characters", [
        T("Table 10: Dragon Experience Levels (Gold)"),
        T("Table 10: Dragon Experience Levels (Silver, Red)"),
        T("Table 10: Dragon Experience Levels (Bronze, Amethyst, Blue)"),
        T("Table 10: Dragon Experience Levels (Copper, Sapphire, Green)"),
        T("Table 10: Dragon Experience Levels (Brass, Emerald, Black)"),
        T("Table 10: Dragon Experience Levels (Topaz, White)"),
        T("Table 10: Dragon Experience Levels (Crystal)"),
    ]),
    "Dragon Proficiencies (CWS)": ("CWS", "Proficiencies", [
        T("Table 11: Dragon Proficiency Slots", [
            "Dragon Race", "Combat: Initial", "Combat: #/Level", "Nonproficiency Penalty", "Noncombat: Initial", "Noncombat: #/Level",
        ]),
        T("Table 12: Bonus Proficiencies"),
        T("Table 13A: Dragon Combat Proficiencies"),
        T("Table 13B: Dragon Noncombat Proficiencies"),
    ]),
    "Combat Proficiencies (CWS)": ("CWS", "Proficiencies", [T("Table 14: Size Categories")]),
    "Basic Combat Rules (CWS)": ("CWS", "Combat", [T("Dragon Hit Dice vs. Special Defenses")]),
    "Special and Innate Abilities (CWS)": ("CWS", "Abilities and Magic", [T(f"Psionics by Age: {c} Dragon") for c in GEM]),
    "Spells (CWS)": ("CWS", "Abilities and Magic", [T(f"Spell Slots by Age: {c} Dragon") for c in METALLIC + GEM + CHROMATIC]),
    "Dragons and Magic (CWS)": ("CWS", "Abilities and Magic", [
        T("Table 23: Dragon Weapons"),
        T("Table 24: Dragon Magical Items"),
        T("Table 25: Potions of Dragon Control"),
    ]),
    "Random Spell Generators (CWS)": ("CWS", "Abilities and Magic", [
        *[T(f"Random Priest Spells: {n} Level") for n in LEVELS[:7]],
        *[T(f"Random Wizard Spells: {n} Level") for n in LEVELS if n != "Sixth"],
    ]),
    # --- Vida dos dragões ---
    "Time and Dragons (CWS)": ("CWS", "Dragon Life", [T(f"Table 19: Comparative Lifespans ({r})") for r in LIFESPAN]),
    "Hoards and Dragon Sleep (CWS)": ("CWS", "Dragon Life", [T("Table 20: Bonded Hoard Timetable"), T("Table 21: Ability Losses")]),
    "Mating (CWS)": ("CWS", "Dragon Life", [T("Table 22: Dragon Clutches")]),
    "Io's Blood Culture (CWS)": ("CWS", "Dragon Life", [T("Draconic Name Prefixes")]),
    "Misc. Tables (CWS)": ("CWS", "Misc. Tables", [
        T("Table 26: Dragon Hoard Magic", ["Class", "Hoard Magic"]),
        T("Table 27: Dragon Character THAC0s", ["Dragon", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16+"]),
        T("Table 28: Saving Throws"),
    ]),
}

TEXT_FIXES = [
    ("Hoards and Dragon Sleep (CWS)", "! 1dl00 Roll || Ability Lost", "! 1d100 Roll || Ability Lost"),
    ("Player Character Races (CWS)", "|+ Bronze Dragon, lawful gold", "|+ Bronze Dragon, lawful good"),
    # Faixas com OCR no gerador de magias de sacerdote do 3º nível (18-20 Cure
    # Disease, 25-27 Feign Death; 31-33 Glyph of Warding, 37-40 Locate Object).
    # Ficam como na fonte, sem como reconstruir: no 6º nível, "16-19 Conjure Fire
    # Elemental" sobra (as outras faixas já cobrem 01-00); no de mago do 9º,
    # faltam 37-48 e 54-58.
    ("Random Spell Generators (CWS)", "| 24-24 || [[Dispel Magic", "| 21-24 || [[Dispel Magic"),
    ("Random Spell Generators (CWS)", "| 24-36 || [[Hold Animal", "| 34-36 || [[Hold Animal"),
    # CA "o" no lugar de 0 (dragão de safira, filhote).
    ("Player Character Races (CWS)", "|  1 || 4-10 || 2-5 || o ||", "|  1 || 4-10 || 2-5 || 0 ||"),
]

# Linhas da tabela em formato errado: (página, padrão, troca).
ROW_FIXES = []


def unwrap_layout(text):
    """Tira as tabelas de layout (sem classe) que só põem outras tabelas lado a
    lado: a abertura, os separadores de coluna ("|", "|- style=…") e o fechamento."""
    lines = text.split("\n")
    out = []
    depth = 0
    layout = []  # profundidades das tabelas de layout abertas
    for line in lines:
        s = line.strip()
        if s.startswith("{|"):
            depth += 1
            if s == "{|":
                layout.append(depth)
                continue
        elif s.startswith("|}"):
            closing = depth
            depth -= 1
            if layout and layout[-1] == closing:
                layout.pop()
                continue
        elif layout and layout[-1] == depth and (s == "|" or s.startswith("|-")):
            continue
        out.append(line)
    return "\n".join(out)


def preprocess(page, text):
    text = text.replace("﻿", "")
    if page == "Random Spell Generators (CWS)":
        text = unwrap_layout(text)
    for p, pattern, repl in ROW_FIXES:
        if p == page:
            text, n = pattern.subn(repl, text)
            if n == 0:
                raise SystemExit(f"{page}: nenhuma linha para corrigir ({pattern.pattern})")
    return text


def postprocess(rule):
    for table in rule["tables"]:
        table["rows"] = [r for r in table["rows"] if any(c.strip() for c in r)]
        # Tabela 19 "deitada": faixas de idade no cabeçalho e as categorias numa linha.
        if table["title"].startswith("Table 19:"):
            ages, (names, *rest) = table["headers"], table["rows"]
            if rest:
                raise SystemExit(f"{table['title']}: mais de uma linha")
            table["rows"] = [[a, n] for a, n in zip(ages, names) if a.strip() or n.strip()]
            table["headers"] = ["Age (years)", "Category"]
    return rule


def main():
    dry = "--dry-run" in sys.argv
    refresh = "--refresh" in sys.argv
    with open(RULES, encoding="utf-8") as f:
        rules = json.load(f)
    ids = {r["id"] for r in rules}
    pages = load_pages(list(PAGES))
    added = 0
    for page in PAGES:
        rule = postprocess(build_rule(page, preprocess(page, pages[page]), PAGES, BOOKS, TEXT_FIXES, "council of wyrms"))
        if rule["id"] in ids:
            index = next(i for i, r in enumerate(rules) if r["id"] == rule["id"])
            # O número do capítulo vem de number_chapters, não daqui.
            rule["chapterNumber"] = rules[index]["chapterNumber"]
            if refresh and rules[index] != rule:
                rules[index] = rule
                added += 1
                print(f"~ {rule['id']}: refeita")
            continue
        print(f"+ {rule['id']}: {len(rule['tables'])} tabelas")
        rules.append(rule)
        added += 1
    added += number_chapters(rules, BOOKS)
    if dry or added == 0:
        print("(nada gravado)" if dry else "(nada a mudar)")
        return
    with open(RULES, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rules, indent=2, ensure_ascii=False) + "\n")
    print(f"{added} regras gravadas")


if __name__ == "__main__":
    main()
