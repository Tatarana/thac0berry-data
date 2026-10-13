#!/usr/bin/env python3
"""GT4b (Dragonlance): regras com tabelas do Tales of the Lance (TotL).

Fonte: as páginas do livro no dump da wiki AD&D 2e
(`../thac0berry-data-mining/dumps/adnd2e_pages_current.xml`).

Decisões do usuário (2026-10-12): cenário "Dragonlance"
(scripts/build_books.py); entram só as páginas com tabelas (uma regra por
página, com o texto inteiro), como no Planescape e no Forgotten Realms. Os
deuses de Krynn entram aqui como regras (capítulo "Deities"); levá-los a
data/deities.json fica no backlog.

- A ficha do avatar de cada deus vem em três formatos na wiki ("! Str || Dex"
  com os valores na linha de baixo, "| Str 17 || Dex 25" e "| Str 15 | Dex 20");
  todas viram a mesma tabela de duas colunas (Stat, Value).
- As tabelas dos "Normals" (XP e salvamentos) aparecem iguais em três páginas:
  ficam só em "Normal Group Classes"; no Commoner e no Tinker saem.
- A lista de guildas do Tinker é uma lista em três colunas, não uma tabela:
  vira lista no texto.

O resto é o mesmo do Planescape (scripts/add_planescape.py: build_rule,
correções de dados por OCR, --refresh).

Uso:  python scripts/add_dragonlance.py [--dry-run] [--refresh]
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

BOOKS = {"TotL": "Tales of the Lance"}

DEITIES = [
    "Paladine", "Mishakal", "Majere", "Kiri-Jolith", "Habbakuk", "Branchala", "Solinari",
    "Gilean", "Sirrion", "Reorx", "Chislev", "Zivilyn", "Shinare", "Lunitari",
    "Takhisis", "Sargonnas", "Morgion", "Chemosh", "Zeboim", "Hiddukel", "Nuitari",
]
STAT = ["Stat", "Value"]
NORMALS = [T("Game Information for Normals"), T("Normal Saving Throws")]

PAGES = {
    # --- Raças ---
    "Barbarians (TotL)": ("TotL", "Races", [T("Barbarian Ability Requirements")]),
    "Dwarves (TotL)": ("TotL", "Races", [T("Dwarf Ability Requirements")]),
    "Elves (TotL)": ("TotL", "Races", [T("Elf Ability Requirements")]),
    "Gnomes (TotL)": ("TotL", "Races", [T("Gnome Ability Requirements")]),
    "Gully Dwarves (TotL)": ("TotL", "Races", [T("Gully Dwarf Ability Generation")]),
    "Kender (TotL)": ("TotL", "Races", [T("Kender Ability Requirements")]),
    "Minotaurs (TotL)": ("TotL", "Races", [T("Minotaur Ability Requirements")]),
    "Ogre Ird (TotL)": ("TotL", "Races", [T("Irda Ability Requirements")]),
    "Class/Race Combinations (TotL)": ("TotL", "Races", [T("Class/Race Combinations")]),
    # --- Classes ---
    "Barbarian (TotL)": ("TotL", "Classes", [T("Barbarian Minimum Scores")]),
    "Cavalier (TotL)": ("TotL", "Classes", [T("Cavalier Minimum Scores")]),
    "Mariner (TotL)": ("TotL", "Classes", [T("Mariner Minimum Scores")]),
    "Game Information for Knights of Solamnia (TotL)": ("TotL", "Classes", [
        T("Crown Knight Minimum Scores"),
        T("Crown Knight Advancement Table"),
        T("Sword Knight Minimum Scores"),
        T("Sword Knight Advancement Table"),
        T("Sword Knight Spells Table", ["Knight Level", "1", "2", "3", "4", "5", "6", "7"]),
        T("Rose Knight Minimum Scores"),
        # A wiki repete o título do Sword Knight; os títulos da tabela são "of Roses".
        T("Rose Knight Advancement Table"),
    ]),
    "Game Information for Wizards of High Sorcery (TotL)": ("TotL", "Classes", [
        T("Wizards of High Sorcery Advancement Table"),
        T("Wizard of High Sorcery Spell Progression"),
    ]),
    "Wizard of High Sorcery (TotL)": ("TotL", "Classes", [T("Moon Phase Effects Table"), T("Moon Alignment Effects Table")]),
    "Holy Orders of the Stars (TotL)": ("TotL", "Classes", [T("Holy Orders Advancement Table"), T("Holy Orders Spell Progression", ["Priest Level", "1", "2", "3", "4", "5", "6*", "7**"])]),
    "Normal Group Classes (TotL)": ("TotL", "Classes", NORMALS),
    "Commoner (TotL)": ("TotL", "Classes", [None, None]),
    "Tinker (TotL)": ("TotL", "Classes", [None, None]),
    # --- Deuses ---
    "Descriptions of the True Gods (TotL)": ("TotL", "Deities", [T("The True Gods of Krynn")]),
    **{f"{name} (TotL)": ("TotL", "Deities", [T(f"{name}: Avatar", STAT)]) for name in DEITIES},
    # --- Mundo ---
    "Ansalonian Calendar (TotL)": ("TotL", "World", [T("Ansalonian Calendar: Days"), T("Ansalonian Calendar: Months")]),
    "Exchange Rates Upon Krynn (TotL)": ("TotL", "World", [T("Exchange Rates Upon Krynn", ["Coin", "Copper", "Gold", "Silver", "Iron/Bronze", "Steel", "Platinum"])]),
    # --- Tesouro e Talis ---
    "Random Treasure Determination (TotL)": ("TotL", "Treasure", [T("Random Treasure Determination")]),
    "Individual and Small Lair Treasures (TotL)": ("TotL", "Treasure", [T("Individual and Small Lair Treasures")]),
    "Talis Deck: Random Role-Playing Notes (TotL)": ("TotL", "Talis Deck", [T("Talis Deck: Random Role-Playing Notes")]),
    # Cada naipe é uma linha de seção (com a categoria da recompensa na última coluna).
    "Talis Deck: Random Event Notes (TotL)": ("TotL", "Talis Deck", [
        T("Talis Deck: Random Event Notes", ["# Mood", "Location", "Descrp.", "Hazard", "Event", "Encounter (Lt/Dk)", "Reward *"]),
    ]),
}

TEXT_FIXES = []


def table_span(lines, start=0):
    """(início, fim) da primeira tabela a partir de `start`, com as aninhadas."""
    begin = next(i for i in range(start, len(lines)) if lines[i].lstrip().startswith("{|"))
    depth = 0
    for i in range(begin, len(lines)):
        s = lines[i].lstrip()
        if s.startswith("{|"):
            depth += 1
        elif s.startswith("|}"):
            depth -= 1
            if depth == 0:
                return begin, i
    raise SystemExit("tabela sem fechamento")


def avatar_table(text):
    """A ficha do avatar (três formatos na wiki) vira uma tabela Stat | Value."""
    lines = text.split("\n")
    begin, end = table_span(lines)
    pairs = []
    names = None
    for line in lines[begin + 1:end]:
        s = line.strip()
        if not s or s.startswith(("|-", "|+")):
            continue
        body = s[1:].strip().rstrip("|").strip()
        cells = [c.strip() for c in re.split(r"\s*(?:\|\||!!)\s*", body)] if ("||" in body or "!!" in body) else [c.strip() for c in body.split(" | ")]
        if s.startswith("!"):
            names = cells
            continue
        if names:
            pairs += list(zip(names, cells))
            names = None
            continue
        for cell in cells:
            m = re.match(r"(#AT|THAC0|[A-Za-z]+)\s+(.*)$", cell)
            if not m:
                raise SystemExit(f"célula da ficha do avatar fora do formato: {cell!r}")
            pairs.append((m.group(1), m.group(2)))
    if len(pairs) != 15:
        raise SystemExit(f"ficha do avatar com {len(pairs)} valores (esperado 15): {pairs}")
    labels = {"STR": "Str", "DEX": "Dex", "CON": "Con", "INT": "Int", "WIS": "Wis", "CHA": "Cha"}
    rows = [f"| {labels.get(k.upper(), k)} || {v}" for k, v in pairs]
    table = ['{| class="article-table"', "! Stat || Value"] + [x for r in rows for x in ("|-", r)] + ["|}"]
    return "\n".join(lines[:begin] + table + lines[end + 1:])


def tinker_guilds(text):
    """A lista de guildas em três colunas (uma "tabela" sem bordas) vira lista."""
    lines = text.split("\n")
    begin, end = table_span(lines)
    items = [line for line in lines[begin + 1:end] if line.lstrip().startswith("*")]
    if not items:
        raise SystemExit("Tinker: lista de guildas não encontrada")
    return "\n".join(lines[:begin] + items + lines[end + 1:])


def talis_suits(text):
    """As linhas de naipe ("! Star (Fates) || … || Miscellaneous") são de cabeçalho
    na wiki, e o leitor as descartaria: viram linhas comuns da tabela."""
    text, n = re.subn(r"^! (?!# Mood)(.+\(.+\) \|\|.*)$", r"| \1", text, flags=re.M)
    if n != 7:
        raise SystemExit(f"Talis Deck: {n} naipes (esperados 7)")
    return text


PAGE_FIXES = {f"{name} (TotL)": avatar_table for name in DEITIES}
PAGE_FIXES["Tinker (TotL)"] = tinker_guilds
PAGE_FIXES["Talis Deck: Random Event Notes (TotL)"] = talis_suits


def preprocess(page, text):
    fix = PAGE_FIXES.get(page)
    return fix(text) if fix else text


def main():
    dry = "--dry-run" in sys.argv
    refresh = "--refresh" in sys.argv
    with open(RULES, encoding="utf-8") as f:
        rules = json.load(f)
    ids = {r["id"] for r in rules}
    pages = load_pages(list(PAGES))
    added = 0
    for page in PAGES:
        rule = build_rule(page, preprocess(page, pages[page]), PAGES, BOOKS, TEXT_FIXES, "dragonlance")
        # Linhas vazias na fonte (cabeçalho em dois níveis) saem.
        for table in rule["tables"]:
            table["rows"] = [r for r in table["rows"] if any(c.strip() for c in r)]
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
