#!/usr/bin/env python3
"""Gera data/books.json: a lista de livros das regras, com cenário e ordem.

Por quê (2026-10-08, Table Grimoire da web, decisão 6 do usuário): a lista de
livros estava fixa no código (web `bookOrder`, iPad
`RulesCompendiumView.bookOrder`), e nada dizia a qual cenário de campanha cada
livro pertence. Um livro de cenário novo no rules.json (ex.: `RL`, Ravenloft)
não apareceria em lugar nenhum sem mudar código.

Fonte: o título vem do `breadcrumbs` das regras (o trecho antes do primeiro
" > "); a ordem e o cenário, da tabela BOOKS abaixo (escolhas explícitas).
Todo livro do rules.json precisa estar em BOOKS (senão o script para), e todo
livro de BOOKS precisa existir no rules.json.

Cenário: "Core" para os livros gerais; senão o mesmo nome que magias, itens
mágicos e monstros já usam ("Dark Sun", "Ravenloft", "Forgotten Realms"…).

Uso:  python scripts/build_books.py [--dry-run]
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RULES = os.path.join(ROOT, "data", "rules.json")
OUT = os.path.join(ROOT, "data", "books.json")

# Ordem do Rules Compendium do iPad; livro novo de cenário entra aqui (GT4).
BOOKS = [
    ("PHB", "Core"),
    ("DMG", "Core"),
    ("CPrH", "Core"),
    ("CFH", "Core"),
    ("CPaH", "Core"),
    ("CRH", "Core"),
    ("CBarbH", "Core"),
    ("CBH", "Core"),
    ("CNH", "Core"),
    ("CTH", "Core"),
    ("CPsiH", "Core"),
    ("DSC", "Dark Sun"),
    ("DK", "Dark Sun"),
    ("WatW", "Dark Sun"),
]


def main():
    dry = "--dry-run" in sys.argv
    with open(RULES, encoding="utf-8") as f:
        rules = json.load(f)
    titles = {}
    for rule in rules:
        titles.setdefault(rule["book"], rule["breadcrumbs"].split(" > ")[0].strip())
    codes = [code for code, _ in BOOKS]
    missing = sorted(set(titles) - set(codes))
    unused = [code for code in codes if code not in titles]
    if missing or unused:
        raise SystemExit(f"livros fora de BOOKS: {missing}; em BOOKS sem regras: {unused}")
    books = [{"id": code, "title": titles[code], "setting": setting, "order": i + 1} for i, (code, setting) in enumerate(BOOKS)]
    for book in books:
        print(f"{book['order']:>2} {book['id']:<7} {book['setting']:<9} {book['title']}")
    if dry:
        print("(dry-run: nada gravado)")
        return
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(books, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
