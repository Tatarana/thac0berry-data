#!/usr/bin/env python3
"""GT4b (Al-Qadim): regras com tabelas do Arabian Adventures (AA) e do
The Complete Sha'ir's Handbook (CShaH).

Fonte: as páginas desses livros no dump da wiki AD&D 2e
(`../thac0berry-data-mining/dumps/adnd2e_pages_current.xml`).

Decisões do usuário (2026-10-12): cenário "Al-Qadim"
(scripts/build_books.py); entram só as páginas com tabelas (uma regra por
página, com o texto inteiro), como nos outros cenários da GT4b.

- Fica de fora o "Guide to Major Illustrations" (legendas das ilustrações).
- Listas de equipamento: o preço vem em três colunas, A/N/B (pedido, normal e
  barganha, como explica a página); o cabeçalho em dois níveis vira um só.
- Tabela 1 (Station): os grupos de kits são linhas de cabeçalho na wiki e
  viram linhas comuns, para não se perderem.
- A tabela de tarefas do gênio está recuada (":{|") e o leitor não a via.

O resto é o mesmo do Planescape (scripts/add_planescape.py: build_rule,
correções de dados por OCR, --refresh).

Uso:  python scripts/add_al_qadim.py [--dry-run] [--refresh]
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

BOOKS = {"AA": "Arabian Adventures", "CShaH": "The Complete Sha'ir's Handbook"}

PRICE = ["Item", "Asking", "Normal", "Bargain"]
PRICE_WT = PRICE + ["Wt. (lbs.)"]
SPELL_LEVELS = ["Caster Level", "1", "2", "3", "4", "5", "6", "7", "8", "9"]

PAGES = {
    # --- Personagens ---
    "Station in Life (AA)": ("AA", "Characters", [T("Table 1: Station", ["Kit", "Station"])]),
    "Kit Descriptions (AA)": ("AA", "Characters", [T("Table 2: Nonweapon Proficiency Group Crossovers")]),
    "Kits (AA)": ("AA", "Characters", [T("Table 3: Character Kit Summary")]),
    "New Proficiencies (AA)": ("AA", "Characters", [T("Table 5: New Proficiencies")]),
    "What's in a Name? (AA)": ("AA", "Characters", [T("Zakharan Names")]),
    # --- Equipamento ---
    "Armor in Fiery Zakhara (AA)": ("AA", "Equipment", [T("Table 6: Armor Class Ratings and Penalties")]),
    "Equipment Lists (AA)": ("AA", "Equipment", [
        T("Zakharan Clothing", PRICE),
        T("Zakharan Daily Food and Lodgings", PRICE),
        T("Zakharan Household Provisions and Bulk Goods", PRICE),
        T("Zakharan Animals", PRICE),
        T("Zakharan Tack and Harness", PRICE_WT),
        T("Zakharan Transport", PRICE),
        T("Zakharan Miscellaneous Equipment", PRICE_WT),
        T("Zakharan Weapons", PRICE),
        T("New Zakharan Weapons", PRICE + ["Weight (lbs.)", "Size", "Type", "Speed", "Damage S-M", "Damage L"]),
        T("Zakharan Armor", PRICE_WT),
        T("Zakharan Services", PRICE),
        T("Zakharan Slaves*", PRICE),
    ]),
    "Desert Survival (AA)": ("AA", "Desert Survival", [T("Table 7: Dehydration"), T("Table 8: Dehydration, Animal")]),
    # --- Magia ---
    "Requesting a Spell (AA)": ("AA", "Magic", [
        T("Sha'ir: Chance of Requesting a Common Wizard Spell", SPELL_LEVELS),
        T("Sha'ir: Chance of Requesting a Foreign Wizard Spell or Priest Spell", SPELL_LEVELS),
    ]),
    "Calling a Genie (AA)": ("AA", "Magic", [T("Genie Task Modifiers", ["Modifier", "Task"])]),
    "Wizard Spells (AA)": ("AA", "Magic", [T("Arabian Adventures Wizard Spells")]),
    "New Spells (CShaH)": ("CShaH", "Magic", [T("Sha'ir's Handbook New Spells")]),
    "Nonweapon Proficiencies (CShaH)": ("CShaH", "Characters", [T("Sha'ir's Handbook Nonweapon Proficiencies")]),
    "Clockwork Devices (CShaH)": ("CShaH", "Clockwork Mages", [
        T("Mechanical Shell Materials"),
        T("Command Vessels"),
        T("Spell Vessels"),
        T("Vessel Installation"),
    ]),
}

TEXT_FIXES = [
    ("Calling a Genie (AA)", ":{|", "{|"),
    ("Kit Descriptions (AA)", "begins with 2 overview", "begins with an overview"),
    ("Equipment Lists (AA)", "(perlb.)", "(per lb.)"),
]

# Preço com OCR na moeda: "15 pp", "6 pg", "2pg" são gp (o livro não usa
# platina nessas listas). Os quatro preços sem número na fonte (pão, perdiz,
# pavão e funda: "cp", "sp", "gp") ficam como estão.
PRICE_OCR = re.compile(r"^(\d[\d,]*)\s*(?:pp|pg)$")


def station_groups(text):
    """Grupos de kits ("! colspan="2" | Warrior Kits") viram linhas comuns."""
    text, n = re.subn(r'^! colspan="2" \| (.+ Kits)\s*$', r"| \1 ||", text, flags=re.M)
    if n == 0:
        raise SystemExit("Station in Life: nenhum grupo de kits")
    return text


PAGE_FIXES = {"Station in Life (AA)": station_groups}


def preprocess(page, text):
    text = text.replace("﻿", "")
    fix = PAGE_FIXES.get(page)
    return fix(text) if fix else text


def postprocess(rule):
    for table in rule["tables"]:
        table["rows"] = [r for r in table["rows"] if any(c.strip() for c in r)]
        if table["headers"][1:4] == ["Asking", "Normal", "Bargain"]:
            table["rows"] = [[r[0]] + [PRICE_OCR.sub(r"\1 gp", c.strip()) for c in r[1:4]] + r[4:] for r in table["rows"]]
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
        rule = postprocess(build_rule(page, preprocess(page, pages[page]), PAGES, BOOKS, TEXT_FIXES, "al-qadim"))
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
