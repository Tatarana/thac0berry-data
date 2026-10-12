#!/usr/bin/env python3
"""GT4b (Planescape): regras com tabelas do Planescape Campaign Setting (PCS),
do Planewalker's Handbook (PWH) e do The Inner Planes (TIP).

Fonte: as páginas desses livros no dump da wiki AD&D 2e
(`../thac0berry-data-mining/dumps/adnd2e_pages_current.xml`).

Decisões do usuário (2026-10-12): três livros novos, cenário "Planescape"
(scripts/build_books.py); entram só as páginas com tabelas de verdade (uma
regra por página, com o texto inteiro), não os ~420 artigos dos livros.

Ficam de fora: a citação de abertura do PCS, as fichas de NPC de Sigil, as
duas magias soltas, a caixinha de legenda de cada plano do PCS e as páginas de
plano do TIP, cuja mini-tabela de escolas já está completa na Tabela 2 do PWH.

Cada tabela tem uma entrada explícita em PAGES (título, cabeçalho quando o da
wiki está quebrado ou falta). Erros de OCR e de marcação da fonte estão em
TEXT_FIXES e DICE_FIXES. Rodar de novo não muda nada (regra com o mesmo id é pulada).

Com --refresh, as regras que já existem são refeitas no lugar (mesma posição
no arquivo), para levar uma correção nova do script às páginas já importadas.

Uso:  python scripts/add_planescape.py [--dry-run] [--refresh]
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from add_dmg_missing_tables import parse_tables  # noqa: E402
from add_ravenloft_dod import clean, load_pages, table_blocks, to_markdown  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RULES = os.path.join(ROOT, "data", "rules.json")

BOOKS = {
    "PCS": "Planescape Campaign Setting",
    "PWH": "The Planewalker's Handbook",
    "TIP": "The Inner Planes",
}

SCHOOLS = ["Plane", "Abj", "Alt", "Con/Sum", "Div", "Enc/Cha", "Ill/Pha", "Inv/Evo", "Nec", "Wil", "A", "F", "E", "W"]

# Uma entrada por tabela da página, na ordem: dict(title, headers?, promote?) ;
# "text" = a "tabela" é texto (vira parágrafo); None = sai.
T = lambda title, headers=None, promote=False, flatten=False: {"title": title, "headers": headers, "promote": promote, "flatten": flatten}  # noqa: E731

PAGES = {
    # --- PCS ---
    "Tiefling (PCS)": ("PCS", "Characters", [T("Tiefling Thief Skill Adjustments")]),
    "Player Character Races (PCS)": ("PCS", "Characters", [T("Planar and Prime Races")]),
    "Effects on Spells (PCS)": ("PCS", "Magic", [
        T("Table 1: Spells with Planar Pathways"),
        T("Table 2: School Alterations by Plane", headers=SCHOOLS, promote=True),
    ]),
    "Magical Items (PCS)": ("PCS", "Magic", ["text"]),
    "Nonplayer Character Abbreviations (PCS)": ("PCS", "Characters", [
        T("NPC Abbreviations: Origin", ["Code", "Origin"]),
        T("NPC Abbreviations: Sex and Race", ["Code", "Sex and Race"]),
        T("NPC Abbreviations: Class", ["Code", "Class"]),
        T("NPC Abbreviations: Faction", ["Code", "Faction"]),
    ]),
    # --- PWH ---
    "Tiefling Tables (PWH)": ("PWH", "Characters", [
        T("Tiefling Abilities", ["D100 Roll", "Ability"]),
        T("Tiefling Appearance", ["D100 Roll", "Appearance"]),
        T("Tiefling Special Side Effects", ["D100 Roll", "Side Effect"]),
    ]),
    "Racial Tables (PWH)": ("PWH", "Characters", [
        T("Planar Races: Ability Requirements", ["Race", "STR", "DEX", "CON", "INT", "WIS", "CHA"]),
        T("Planar Races: Ability Adjustments"),
        T("Planar Races: Average Height and Weight"),
        T("Planar Races: Age"),
        T("Planar Races: Aging Effects"),
        T("Planar Races: Level Limits"),
        T("Planar Races: Racial Adjustment for Thieves"),
    ]),
    "Vortices (PWH)": ("PWH", "Travel", [T("Vortices", ["Vortex To", "Where Found", "Occasionally Usurped By"])]),
    "Known Portals and Keys (PWH)": ("PWH", "Travel", [T("Known Portals and Keys", ["Location (Plane, Specific)", "Key", "Destination"])]),
    "New Proficiencies (PWH)": ("PWH", "Characters", [T("Planewalker Proficiencies")]),
    # Lista alfabética em duas colunas no livro: vira uma coluna só, lida coluna por coluna.
    "Languages of the Planes (PWH)": ("PWH", "Characters", [T("Other Planar Languages", ["Language"], flatten=True)]),
    "Mages and Magic (PWH)": ("PWH", "Magic", [
        T("Table 2: School Alterations by Plane", headers=SCHOOLS),
        T("Table 3: Planar Absolutes (Absolute Prohibitions of Magic by Plane)", promote=True),
    ]),
    "Powers and Priests (PWH)": ("PWH", "Magic", [T("Table 4: Priest Level Loss by Plane (Quick Reference)")]),
    "Magical Items (PWH)": ("PWH", "Magic", [T("Table 6: Magical Item Bonus Loss by Plane (Quick Reference)")]),
    "Wizard Spells (PWH)": ("PWH", "Magic", [T("Planewalker Wizard Spells")]),
    "Priest Spells (PWH)": ("PWH", "Magic", [T("Planewalker Priest Spells")]),
    "Tools of the Trade (PWH)": ("PWH", "Equipment", [
        T("Baatorian Green Steel Items"),
        T("Baatorian Green Steel Weapons", ["Item", "Cost (GP)", "Weight (lbs)", "Damage S-M", "Damage L"]),
        T("Bariaur Equipment"),
        T("Sickles and Scythes"),
    ]),
    "New Items (PWH)": ("PWH", "Equipment", [
        T("Fiend Globe"),
        T("Grue Bottle"),
        T("Potion of Elemental Breathing"),
        T("Scroll of Outer-Planar Protection"),
    ]),
    "The Power of Belief (PWH)": ("PWH", "Characters", [T("Belief: Awarding Points", ["Points", "Reason"])]),
    "Priest Level Loss By Plane (PWH)": ("PWH", "Magic", [T("Priest Level Loss by Plane")]),
    "Magical Item Bonus Loss By Plane (PWH)": ("PWH", "Magic", [T("Magical Item Bonus Loss by Plane")]),
    # --- TIP ---
    "Physical Conditions - Salt (TIP)": ("TIP", "Physical Conditions", [
        T("Salt: Successful Saving Throw"),
        T("Salt: Failed Saving Throw"),
    ]),
    "Physical Conditions - Dust (TIP)": ("TIP", "Physical Conditions", [T("Dust: Other Dangers")]),
    "Physical Conditions - Mineral (TIP)": ("TIP", "Physical Conditions", [T("Mineral: Moving About")]),
    "Physical Conditions - Radiance (TIP)": ("TIP", "Physical Conditions", [T("Radiance: Hazards")]),
    "Physical Conditions - Ooze (TIP)": ("TIP", "Physical Conditions", [T("Ooze: Acid Pools"), T("Ooze: Toxic Regions (Poison)")]),
    "Physical Conditions - Magma (TIP)": ("TIP", "Physical Conditions", [T("Magma: Temperature")]),
    "Physical Conditions - Air (TIP)": ("TIP", "Physical Conditions", [
        T("Air: Storms (Force)"),
        T("Air: Storms (Duration)"),
        T("Air: Maelstroms"),
        T("Air: Moving About"),
    ]),
    "Physical Conditions - Water (TIP)": ("TIP", "Physical Conditions", [
        T("Water: Currents (Strength)", ["1D20 Roll", "Strength of Current", "Adjustment"]),
        T("Water: Currents (Duration)", ["1D20 Roll", "Current Lasts"]),
    ]),
    "Physical Conditions - Earth (TIP)": ("TIP", "Physical Conditions", [
        T("Earth: Fossils"),
        T("Earth: Earthquakes"),
        T("Earth: Moving About", ["1D10 Roll", "Type of Earth", "Minimum Strength"]),
    ]),
    "Physical Conditions - Fire (TIP)": ("TIP", "Physical Conditions", [
        T("Fire: Getting Here"),
        T("Fire: Damage by Natural AC"),
    ]),
    "The Sites - Fire (TIP)": ("TIP", "Physical Conditions", [T("Fire: The Crimson Pillar")]),
    "Elemental Pockets (TIP)": ("TIP", "Physical Conditions", [T("Elemental Pockets: Size")]),
    "Combat (TIP)": ("TIP", "Combat", [T("No Gravity: Maximum Attackers", ["Target Size", "Attackers: T", "S", "M", "L", "H", "G"])]),
    "Magic Use (TIP)": ("TIP", "Magic", [
        T("Inner Planes: Priest Restrictions"),
        T("Inner Planes: Magical Items"),
    ]),
}

# Marcação e OCR quebrados na fonte: (página, errado, certo).
TEXT_FIXES = [
    # A tabela de ácido não fecha ("}" no lugar de "|}"): o leitor engoliria o texto seguinte.
    ("Physical Conditions - Ooze (TIP)", "| 6 || Very concentrated || -4 || 1d20\n}", "| 6 || Very concentrated || -4 || 1d20\n|}"),
    # Armas de aço verde: cada uma sobe um degrau de dado; a cimitarra (1d8/1d8) fica 1d10/1d10.
    ("Tools of the Trade (PWH)", "| Scimitar || 60 || 2 || 11d10 || 1d10", "| Scimitar || 60 || 2 || 1d10 || 1d10"),
    ("Effects on Spells (PCS)", "School Aleterations", "School Alterations"),
    ("Physical Conditions - Water (TIP)", "Currants", "Currents"),
    # A fração vem duas vezes ("{{frac|1|2}} ½").
    ("New Items (PWH)", "{{frac|1|2}} ½", "½"),
]

# Dados com letra no lugar de algarismo ("1d1O", "2dl0") ou com espaço ("2d 10").
DICE_FIXES = [
    (re.compile(r"\b(\d+)d1O\b"), r"\1d10"),
    # "2dl0", "1dl2": a letra l (ou I) no lugar do 1.
    (re.compile(r"\b(\d+)d[lI](\d)\b"), r"\1d1\2"),
    (re.compile(r"\b(\d+)d (\d+)\b"), r"\1d\2"),
]


def fix_dice(text):
    for pattern, repl in DICE_FIXES:
        text = pattern.sub(repl, text)
    return text


def build_table(parsed, spec):
    headers = parsed["headers"][-1] if parsed["headers"] else []
    rows = [list(r) for r in parsed["rows"]]
    if spec["promote"] and rows:
        if spec["headers"] is None:
            headers = rows[0]
        rows = rows[1:]
    if spec["headers"] is not None:
        headers = spec["headers"]
    if spec.get("flatten"):
        width = max(len(r) for r in rows)
        rows = [[r[c]] for c in range(width) for r in rows if c < len(r) and r[c].strip()]
    # Linhas de nota dentro da tabela ("* ...", resto vazio) saem para depois dela.
    notes = [f"({m.group(1)}) {m.group(2)}" for r in rows if (m := re.match(r"^(\*+)\s*(.*)$", r[0])) and not any(c.strip() for c in r[1:])]
    rows = [r for r in rows if not (re.match(r"^\*+", r[0]) and not any(c.strip() for c in r[1:]))]
    width = max([len(headers)] + [len(r) for r in rows]) if headers else max([len(r) for r in rows] or [0])
    if headers and len(headers) < width:
        headers = headers + [""] * (width - len(headers))
    rows = [[fix_dice(c) for c in r] + [""] * (width - len(r)) for r in rows]
    number = re.match(r"Table (\d+)", spec["title"])
    table = {"tableNumber": f"Table {number.group(1)}" if number else "", "title": spec["title"], "headers": headers, "rows": rows}
    return table, notes


def slug(text):
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def build_rule(page, text):
    book, chapter, specs = PAGES[page]
    for p, wrong, right in TEXT_FIXES:
        if p == page:
            if wrong not in text:
                raise SystemExit(f"{page}: trecho não encontrado: {wrong!r}")
            text = text.replace(wrong, right)
    # Marcação da wiki que não é conteúdo (barra lateral, índice, imagens) e as
    # frações/sobrescritos, que o conversor não conhece.
    text = re.sub(r"\{\{(Sidebar|Navbox|clear)[^}]*\}\}", "", text, flags=re.I)
    text = re.sub(r"__(NO)?TOC__", "", text)
    text = re.sub(r"\[\[(File|Image):[^\]]*\]\]", "", text, flags=re.I)
    text = re.sub(r"\{\{frac\|(\d+)\|(\d+)\|(\d+)\}\}", r"\1 \2/\3", text)
    text = re.sub(r"\{\{frac\|(\d+)\|(\d+)\}\}", r"\1/\2", text)
    text = re.sub(r"<sup>(\d)</sup>", lambda m: "¹²³⁴⁵⁶⁷⁸⁹"[int(m.group(1)) - 1], text)
    blocks = table_blocks(text)
    parsed = parse_tables(text)
    if len(blocks) != len(specs) or len(parsed) != len(specs):
        raise SystemExit(f"{page}: {len(blocks)}/{len(parsed)} tabelas na página, {len(specs)} esperadas")
    lines = text.split("\n")
    tables = []
    for (start, end, block), table_parsed, spec in reversed(list(zip(blocks, parsed, specs))):
        if spec is None:
            lines[start:end + 1] = []
            continue
        if spec == "text":
            # A "tabela" é um parágrafo de texto (PCS Table 3): fica como texto, com o título em negrito.
            body = " ".join(clean(" ".join(r)) for r in table_parsed["rows"])
            title = table_parsed["caption"] or ""
            lines[start:end + 1] = ["", f"**{title}**" if title else "", "", body, ""]
            continue
        table, notes = build_table(table_parsed, spec)
        tables.insert(0, table)
        # As notas que estavam dentro da tabela vão para logo depois dela; as de
        # fora (": * …") já estão no texto e o to_markdown as formata.
        lines[start:end + 1] = ["", f"[TABLE_REF: {table['title']}]", ""] + ([*notes, ""] if notes else [])
    content = fix_dice(to_markdown("\n".join(lines)))
    # Itálico aberto na wiki sem fechar ("''(A cutter…"): sobra o par de aspas.
    content = content.replace("''", "")
    topic = re.sub(r"\s*\((PCS|PWH|TIP)\)$", "", page)
    first = next((p for p in content.split("\n\n") if p and not p.startswith(("**", "[TABLE_REF", "#", "("))), topic)
    summary = re.split(r"(?<=[.!?])\s", first.strip(), maxsplit=1)[0]
    return {
        "id": f"{book.lower()}_ch00_{slug(topic)}",
        "book": book,
        "chapterNumber": 0,
        "chapterTitle": chapter,
        "breadcrumbs": f"{BOOKS[book]} > {chapter} > {topic}",
        "topic": topic,
        "ruleType": "core_rule",
        "summary": summary,
        "content": content,
        "tables": tables,
        "relatedRuleIds": [],
        "relatedSpells": [],
        "relatedMagicItems": [],
        "searchKeywords": sorted({w for w in re.findall(r"[a-z]+", topic.lower()) if len(w) > 3} | {"planescape"}),
    }


def main():
    dry = "--dry-run" in sys.argv
    refresh = "--refresh" in sys.argv
    with open(RULES, encoding="utf-8") as f:
        rules = json.load(f)
    ids = {r["id"] for r in rules}
    pages = load_pages(list(PAGES))
    added = 0
    for page in PAGES:
        rule = build_rule(page, pages[page])
        if rule["id"] in ids:
            index = next(i for i, r in enumerate(rules) if r["id"] == rule["id"])
            if refresh and rules[index] != rule:
                rules[index] = rule
                added += 1
                print(f"~ {rule['id']}: refeita")
            continue
        print(f"+ {rule['id']}: {len(rule['tables'])} tabelas")
        rules.append(rule)
        added += 1
    if dry or added == 0:
        print("(nada gravado)" if dry else "(nada a mudar)")
        return
    with open(RULES, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rules, indent=2, ensure_ascii=False) + "\n")
    print(f"{added} regras gravadas")


if __name__ == "__main__":
    main()
