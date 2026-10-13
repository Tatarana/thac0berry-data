#!/usr/bin/env python3
"""GT4b (Forgotten Realms): regras com tabelas do Sea of Fallen Stars (SofS),
do Faiths & Avatars (FA) e do Powers & Pantheons (PP).

Fonte: as páginas desses livros no dump da wiki AD&D 2e
(`../thac0berry-data-mining/dumps/adnd2e_pages_current.xml`).

Decisões do usuário (2026-10-12): cenário "Forgotten Realms"
(scripts/build_books.py); entram só as páginas com tabelas de verdade (uma
regra por página, com o texto inteiro), como no Planescape.

- SofS: todas as páginas com tabela, menos a letra "S" da enciclopédia (uma
  lista de guerras no meio do glossário) e "Sites and Landmarks" (a legenda do
  mapa de Myth Nantar, que é texto em forma de tabela).
- FA: o apêndice das classes de sacerdote, as seis classes, o índice de magias
  e as tabelas estendidas do "Format of Deity Entries". As páginas de cada deus
  ficam de fora: os deuses do FA e do PP já estão em data/deities.json.
- PP: os apelidos dos deuses e as magias novas. Ficam de fora o "Format of
  Deity Entries" (as mesmas tabelas do FA), o índice de magias com páginas dos
  dois livros e a lista de locais (só nomes e páginas).

O resto é o mesmo do Planescape (scripts/add_planescape.py: build_rule,
correções de dados por OCR, --refresh). Correções da fonte em TEXT_FIXES
(literais) e ROW_FIXES (linhas da tabela em formato errado).

Uso:  python scripts/add_forgotten_realms.py [--dry-run] [--refresh]
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

BOOKS = {
    "SofS": "Sea of Fallen Stars",
    "FA": "Faiths & Avatars",
    "PP": "Powers & Pantheons",
}

DYNASTY = ["Monarch", "Reign in DR (total)"]
CLASS_BOX = ["Requirement", "Value"]

PAGES = {
    # --- SofS ---
    "Serôsian Sentient Races (SofS)": ("SofS", "Characters", [T("Serôs PC Races"), T("Serôs NPC Races")]),
    "Shalarin Phonics (SofS)": ("SofS", "Characters", [
        T("Shalarin Phonics: Castes"),
        T("Shalarin Phonics: Name Structure"),
        T("Shalarin Phonics: Clan Names"),
    ]),
    "The Dukars (SofS)": ("SofS", "Characters", [
        T("Table 12: Dukar Experience-Point Table"),
        T("Table 13: Dukar Proficiencies"),
        T("Table 14: Dukar Spell Progression"),
        T("Table 15: Peacekeeper Paths"),
    ]),
    "Vision (SofS)": ("SofS", "Undersea Rules", [T("Table 1: Shallows Vision Table"), T("Table 2: Gloom Vision Table")]),
    "Effects of the Depths (SofS)": ("SofS", "Undersea Rules", [T("Table 4: Maximum Safe Depths"), T("Table 5: Aquatic Movement Rates")]),
    # Cabeçalho partido na fonte ("Type{{br}}Dwellers* || Penalties to Surface").
    "Underwater Combat (SofS)": ("SofS", "Undersea Rules", [T("Table 6: Combat Modifiers", ["Type", "Penalties to Surface Dwellers*"])]),
    "Underwater Equipment (SofS)": ("SofS", "Equipment", [T("Table 7: Common Serôsian Weapons")]),
    "Underwater Spellcasting (SofS)": ("SofS", "Magic", [T("Table 8: Underwater Spellcasting Penalties", ["Aspect", "Penalty"])]),
    "The Depths (SofS)": ("SofS", "Undersea Rules", [T("Table 9: Sea of Fallen Stars Depth Zones")]),
    "Undersea Sociology (SofS)": ("SofS", "Equipment", [T("Table 10: Serôsian Pearl Money System", promote=True)]),
    # Os dois calendários intercalados na ordem do ano, como no livro (um lado vazio em cada linha).
    "Time Measurement (SofS)": ("SofS", "Lore", [T("Table 11a: Calendars", ["Faerûnian Month: Days (Total)", "Serôs Song: Days (Total)"], promote=True)]),
    "History of Serôs (SofS)": ("SofS", "Lore", [T("Table 11b: Epochs of Serôs")]),
    "Current Inner Sea Ruling Dynasties (SofS)": ("SofS", "Lore", [
        T("Last Dynasty of Aleaxtis/First Dynasty of Kurrimal (Sahuagin)"),
        T("Dynasty of Eadraal (Merfolk)"),
        T("Dynasty of As'arem (Shalarin)"),
        T("Dynasty of Es'daan (Shalarin)"),
        T("Dynasty of Es'purr (Shalarin)"),
        T("Dynasty of Es'rath (Shalarin)"),
        T("Dynasty of Es'roch (Shalarin)"),
        T("Dynasty of Olleth (Morkoth)"),
        T("Dynasty of Naramyr (Sea Elf)"),
        T("Dynasty of Selu'Maraar (Sea Elf)"),
        T("Dynasty of Xedran Reefs (Ixitxachitl)"),
    ]),
    "Religions of Serôs (SofS)": ("SofS", "Lore", [T("Shalarin Names of the Gods")]),
    "Faerûn's Spells for the Seas (SofS)": ("SofS", "Magic", [T("Faerûnian Wizard Spells for the Seas")]),
    "Faerûnian Flotsam in Serôs (SofS)": ("SofS", "Magic", [T("Trident of Amahl: Command Modes")]),
    "Building Notes (SofS)": ("SofS", "Lore", [
        T("Myth Nantar Buildings: Depth and Clearing Time (Class A, 1d4)", ["1d4", "Depth/Clearing Time"]),
        T("Myth Nantar Buildings: Depth and Clearing Time (Class B, 1d6)", ["1d6", "Depth/Clearing Time"]),
        T("Myth Nantar Buildings: Depth and Clearing Time (Class C, 1d8)", ["1d8", "Depth/Clearing Time"]),
        T("Myth Nantar Buildings: Height (Class B, 1d8)", ["1d8", "Stories"]),
        T("Myth Nantar Buildings: Height (Class C, 1d6)", ["1d6", "Stories"]),
        T("Myth Nantar Buildings: Function (1d10)", ["1d10", "Class B", "Class C"]),
    ]),
    # --- FA ---
    "Appendix 1: Priest Classes (FA)": ("FA", "Priest Classes", [
        T("Expanded Priest Experience Levels"),
        T("Racial Class and Level Limits"),
    ]),
    "Cleric (FA)": ("FA", "Priest Classes", [T("Cleric: Requirements", CLASS_BOX)]),
    "Crusader (FA)": ("FA", "Priest Classes", [T("Crusader: Requirements", CLASS_BOX)]),
    "Druid (FA)": ("FA", "Priest Classes", [T("Druid: Requirements", CLASS_BOX)]),
    "Monk (FA)": ("FA", "Priest Classes", [T("Monk: Requirements", CLASS_BOX)]),
    "Mystic (FA)": ("FA", "Priest Classes", [T("Mystic: Requirements", CLASS_BOX)]),
    "Shaman (FA)": ("FA", "Priest Classes", [T("Shaman: Requirements", CLASS_BOX), T("Shaman: Spirit Allies")]),
    "Format of Deity Entries (FA)": ("FA", "Deities", [
        T("Extended Calculated THAC0s Table"),
        T("Extended Priest Spell Progression Table"),
        T("Extended Wizard Spell Progression Table"),
        T("Extended Bard Spell Progression Table"),
    ]),
    "Appendix 2: Spell Index (FA)": ("FA", "Magic", [T("Faiths & Avatars Spell Index")]),
    # --- PP ---
    "Appendix 1: Aliases (PP)": ("PP", "Deities", [T("Aliases of the Powers")]),
    "Appendix 3a: New Spells (PP)": ("PP", "Magic", [T("Powers & Pantheons New Spells")]),
}

TEXT_FIXES = [
    ("Crusader (FA)", "conflict wnosSnaat the forefront", "conflict who stand at the forefront"),
    # Dia que vem a cada 4 anos (como o Shieldmeet) e o nome do feriado (Higharvestide).
    ("Time Measurement (SofS)", "| || Sashelsong (1 (1/4 yrs.))", "| || Sashelsong 1 (1/4 yrs.)"),
    # (depois do ROW_FIXES do calendário, que já tirou os parênteses)
    ("Time Measurement (SofS)", "| Higharvessong: 1 (274) ||", "| Higharvestide: 1 (274) ||"),
]


def building_function_row(m):
    # "| 1 B: Warehouse{{br}}C: Warehouse": uma célula só com o número e as duas
    # classes; vira três colunas (1d10, Classe B, Classe C).
    roll, b, c = m.group(1), m.group(2), m.group(3)
    return f"| {roll} || {b.strip()} || {c.strip()}"


# (página, padrão, troca): linhas de tabela em formato errado na fonte.
ROW_FIXES = [
    ("Building Notes (SofS)", re.compile(r"^\| (\d+) B: (.*?)\{\{br\}\}C: (.*)$", re.M), building_function_row),
]


def calendar_cell(m):
    # "Hammer (30 (30)" ou "Homesong (36 (108))": mês, dias e o total do ano.
    return f"{m.group(1).strip()}: {m.group(2)} ({m.group(3)})"


ROW_FIXES.append(("Time Measurement (SofS)", re.compile(r"([A-Z][\w' ]*?) \(\s*(\d+) \((\d+)\)\)?"), calendar_cell))

# Em todas as páginas: o BOM do começo, o travessão do cp1252 (0x97) e a linha
# "… Article"/"… Appendix" de abertura (link para o livro, não é texto).
GENERIC_FIXES = [
    (re.compile("\ufeff"), ""),
    (re.compile("\x97"), "—"),
    (re.compile(r"^:?(''\s*)?\[\[(Sea of Fallen Stars|Powers & Pantheons|Faiths & Avatars)\]\] (Article|Appendix)('')?", re.M), ""),
]


def preprocess(page, text):
    for pattern, repl in GENERIC_FIXES:
        text = pattern.sub(repl, text)
    for p, pattern, repl in ROW_FIXES:
        if p == page:
            text, n = pattern.subn(repl, text)
            if n == 0:
                raise SystemExit(f"{page}: nenhuma linha para corrigir ({pattern.pattern})")
    return text


def main():
    dry = "--dry-run" in sys.argv
    refresh = "--refresh" in sys.argv
    with open(RULES, encoding="utf-8") as f:
        rules = json.load(f)
    ids = {r["id"] for r in rules}
    pages = load_pages(list(PAGES))
    added = 0
    for page in PAGES:
        rule = build_rule(page, preprocess(page, pages[page]), PAGES, BOOKS, TEXT_FIXES, "forgotten realms")
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
