#!/usr/bin/env python3
"""GT4b (Thri-Kreen): regras com tabelas do Thri-Kreen of Athas (TKA).

Fonte: as páginas do livro no dump da wiki AD&D 2e
(`../thac0berry-data-mining/dumps/adnd2e_pages_current.xml`).

Decisões do usuário (2026-10-12): o livro entra no cenário "Dark Sun"
(scripts/build_books.py), sem cenário próprio; só as páginas com tabelas (uma
regra por página, com o texto inteiro), como nos outros cenários da GT4b.

- Quase todas as "tabelas" do livro na wiki são caixas de texto ("Jeral vs.
  To'ksa", "Molting"…: uma tabela de uma célula só). Nas páginas que entram,
  as caixas viram texto comum (unwrap_boxes); as páginas que só têm caixas
  ficam de fora.
- Tabela 2.1: o XP e a habilidade ganha vêm na mesma célula ("175 leap") e o
  cabeçalho está deslocado; vira Stage, Age, …, XP, Abilities.

O resto é o mesmo do Planescape (scripts/add_planescape.py: build_rule,
correções de dados por OCR, --refresh).

Uso:  python scripts/add_thri_kreen.py [--dry-run] [--refresh]
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

BOOKS = {"TKA": "Thri-Kreen of Athas"}

STAGES = ["Stage", "Age (years)", "Size", "Move", "Claw/Bite", "Level", "HD", "THAC0", "XP", "Abilities"]

PAGES = {
    "Thri-Kreen PCs Character Classes (TKA)": ("TKA", "Characters", [
        T("Thri-Kreen Ability Adjustments (base roll: 5d4)"),
        T("Thri-Kreen Physical Characteristics"),
    ]),
    "Character Classes (TKA)": ("TKA", "Characters", [
        T("Table 7.1: Thri-Kreen Level Limits"),
        # Lista em duas colunas no livro: uma coluna só, lida coluna por coluna.
        T("Thri-Kreen Multiclass Combinations", ["Combination"], flatten=True),
    ]),
    "Stages of Life (TKA)": ("TKA", "Characters", [T("Table 2.1: Thri-Kreen Stages of Growth")]),
    "Chatkcha (and Kyorkcha) (TKA)": ("TKA", "Combat", [
        T("Table 3.1: Specialist Attacks per Round with Chatkcha (or Kyorkcha)", ["Level", "Thri-Kreen", "Non-Kreen"]),
    ]),
    "Combat Skills (TKA)": ("TKA", "Combat", [T("Table 3.3: Specialist Attacks per Round with Bite or Claw", promote=True)]),
    "Other Thri-Kreen Weapons (TKA)": ("TKA", "Combat", [
        T("Table 3.2: Weapons List", [
            "Item", "Cost¹", "Weight", "Size", "Type", "Speed Factor", "Damage S-M", "Damage L", "ROF", "Range S", "Range M", "Range L",
        ]),
    ]),
    "Language and Communication (TKA)": ("TKA", "Language", [T("Thri-Kreen Names")]),
    "Glossary (TKA)": ("TKA", "Language", [T("Thri-Kreen Glossary")]),
}

TEXT_FIXES = []


def unwrap_boxes(text):
    """Caixas de texto (tabela cuja primeira linha é só "|" ou "!") viram texto
    comum: saem a abertura, a linha da célula e o fechamento; o que estiver
    dentro (inclusive uma tabela de verdade) fica."""
    lines = text.split("\n")
    out = []
    depth = 0
    boxes = []  # profundidades das caixas abertas
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if s.startswith("{|"):
            depth += 1
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and lines[j].strip() in ("|", "!"):
                boxes.append(depth)
                i = j + 1
                continue
        elif s.startswith("|}"):
            closing = depth
            depth -= 1
            if boxes and boxes[-1] == closing:
                boxes.pop()
                i += 1
                continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)


def preprocess(page, text):
    return unwrap_boxes(text.replace("﻿", ""))


def split_stages(table):
    # "175 leap" → XP 175, Abilities "leap"; "975**" fica só XP.
    rows = []
    for r in table["rows"]:
        m = re.match(r"^([\d,]+\**)\s*(.*)$", r[-1].strip())
        if not m:
            raise SystemExit(f"Tabela 2.1: XP fora do formato: {r[-1]!r}")
        rows.append(r[:-1] + [m.group(1), m.group(2)])
    table["rows"] = rows
    table["headers"] = STAGES


def postprocess(rule):
    for table in rule["tables"]:
        table["rows"] = [r for r in table["rows"] if any(c.strip() for c in r)]
        if table["title"].startswith("Table 2.1:"):
            split_stages(table)
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
        rule = postprocess(build_rule(page, preprocess(page, pages[page]), PAGES, BOOKS, TEXT_FIXES, "thri-kreen"))
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
