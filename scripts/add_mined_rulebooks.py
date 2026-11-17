#!/usr/bin/env python3
"""Regras de 4 livros de "Complete" já extraídos no repo de mineração:
CBE (The Complete Book of Elves), CWH (The Complete Wizard's Handbook), CBN
(The Complete Book of Necromancers) e TOM (Tome of Magic).

Fonte: ../thac0berry-data-mining/data/rules_<livro>/*.json (um arquivo por
capítulo, formato do extract_wizard_rulebooks.py / extract_elves_handbook.py).
Só regras: kits, magias, criaturas e itens desses livros já têm módulos próprios.

Conversão para o schema `rule-entry`:
- o `content` já vem limpo (tabelas em markdown no próprio texto), `tables` fica
  vazio e o Table Grimoire lê as tabelas do markdown;
- `ruleType`: core_rule; dm_guideline nos capítulos/apêndices de mestre (CWH
  "Wizardly Lists", CBN "The Campaign", CBE "Elven Campaigns"); optional_rule em
  CBE "Optional Rules";
- títulos de capítulo sem a explicação entre parênteses que o extrator pôs.

Idempotente: rodar de novo troca as regras desses 4 livros pela versão minerada
(os ids são os mesmos), mantendo a posição no fim do arquivo.

Uso:  python scripts/add_mined_rulebooks.py [--mining CAMINHO] [--dry-run]
"""
import argparse
import glob
import json
import os
import re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RULES = os.path.join(ROOT, "data", "rules.json")

# código -> (pasta no repo de mineração, título do livro)
BOOKS = {
    "CBE": ("rules_complete_book_of_elves", "The Complete Book of Elves"),
    "CWH": ("rules_complete_wizards_handbook", "The Complete Wizard's Handbook"),
    "CBN": ("rules_complete_book_of_necromancers", "The Complete Book of Necromancers"),
    "TOM": ("rules_tome_of_magic", "Tome of Magic"),
}

CHAPTER_TITLE_FIXES = {
    "Wizard Kits (rules, not individual kits)": "Wizard Kits",
    "New Spells (commentary, not individual spell stat blocks)": "New Spells",
    "Wizardly Lists (DM appendix tables)": "Wizardly Lists",
}

RULE_TYPE_BY_CHAPTER = {
    ("CWH", 9): "dm_guideline",
    ("CBN", 9): "dm_guideline",
    ("CBE", 13): "dm_guideline",
    ("CBE", 9): "optional_rule",
}


def convert(record, code):
    chapter_number = record["chapter"]["number"]
    chapter_title = CHAPTER_TITLE_FIXES.get(record["chapter"]["title"], record["chapter"]["title"])
    book_title = BOOKS[code][1]
    topic = record["topic"]
    crumbs = (
        f"{book_title} > Chapter {chapter_number}: {chapter_title} > {topic}"
        if chapter_number
        else f"{book_title} > {chapter_title} > {topic}"
    )
    return {
        "id": record["id"],
        "book": code,
        "chapterNumber": chapter_number,
        "chapterTitle": chapter_title,
        "breadcrumbs": crumbs,
        "topic": topic,
        "ruleType": RULE_TYPE_BY_CHAPTER.get((code, chapter_number), "core_rule"),
        "summary": record["summary"],
        "content": record["content"],
        "tables": [],
        "relatedRuleIds": [],
        "relatedSpells": [],
        "relatedMagicItems": [],
        "searchKeywords": record["searchKeywords"],
    }


def load_book(mining_data, code):
    folder = os.path.join(mining_data, BOOKS[code][0])
    records = []
    for path in sorted(glob.glob(os.path.join(folder, "*.json"))):
        if os.path.basename(path) == "index.json":
            continue
        with open(path, encoding="utf-8") as f:
            records.extend(json.load(f))
    records.sort(key=lambda r: (r["chapter"]["number"], r["topic"].lower()))
    return [convert(r, code) for r in records]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mining", default=os.path.join(ROOT, "..", "thac0berry-data-mining", "data"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with open(RULES, encoding="utf-8") as f:
        rules = json.load(f)

    ours = set(BOOKS)
    kept = [r for r in rules if r["book"] not in ours]
    taken = {r["id"] for r in kept}

    added = []
    for code in BOOKS:
        book_rules = load_book(os.path.abspath(args.mining), code)
        for rule in book_rules:
            if rule["id"] in taken:
                raise SystemExit(f"id repetido: {rule['id']}")
            taken.add(rule["id"])
        added.extend(book_rules)
        print(f"{code}: {len(book_rules)} regras")

    leaks = [r["id"] for r in added if re.search(r"\[\[|\]\]|\{\{|\}\}|<[a-zA-Z/][^>]*>|&[a-z]+;", r["content"])]
    if leaks:
        raise SystemExit(f"markup de wiki sobrou em: {leaks}")

    if args.dry_run:
        print(f"(nada gravado) {len(added)} regras, antes {len(rules)}, depois {len(kept) + len(added)}")
        return
    with open(RULES, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(kept + added, indent=2, ensure_ascii=False) + "\n")
    print(f"{len(added)} regras gravadas (total {len(kept) + len(added)})")


if __name__ == "__main__":
    main()
