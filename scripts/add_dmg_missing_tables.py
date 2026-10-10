#!/usr/bin/env python3
"""GT4: tabelas do DMG que faltam no rules.json e correções nas que já existem.

Fonte: o dump da wiki AD&D 2e no data-mining
(`../thac0berry-data-mining/dumps/adnd2e_pages_current.xml`), as páginas
"DMG Table N" e as páginas de capítulo do DMG. Os JSON de `rules_dmg` só citam
essas tabelas, sem o conteúdo.

Decisões do usuário (2026-10-10):
- tabelas em dois passos (d6/d10 escolhe a subtabela, d20 nela): a Tabela N
  vira o seletor ("1-2 → Table 89A") e cada subtabela ganha letra (89A, 89B…);
- Tabela 117: "117" é a parte A (Purpose), citada pela 116; "117B" é a parte B
  (Special Purpose Power);
- as 89–110 entram em `dmg_ch10_magical_item_tables`, junto da 88;
- tabelas sem título ganham número quando são numeradas no livro, ou um título
  descritivo quando são exemplos do texto.

Cada tabela nova entra em `tables` e no `content` como `[TABLE_REF: título]`,
depois do parágrafo que a cita (ou no fim), com as notas de rodapé da fonte.
Rodar de novo não muda nada: tabela com o mesmo `tableNumber` já presente na
regra é pulada, e as correções só trocam o que ainda estiver errado.

Uso:  python scripts/add_dmg_missing_tables.py [--dry-run]
"""
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RULES = os.path.join(ROOT, "data", "rules.json")
DUMP = os.path.join(ROOT, "..", "thac0berry-data-mining", "dumps", "adnd2e_pages_current.xml")

# --- Leitura do dump ---------------------------------------------------------------


def load_pages(titles):
    """Texto wiki das páginas pedidas (segue um nível de #REDIRECT)."""
    wanted = set(titles)
    pages = {}
    for _, el in ET.iterparse(DUMP, events=("end",)):
        if el.tag.split("}")[-1] != "page":
            continue
        title = text = ""
        for ch in el.iter():
            tag = ch.tag.split("}")[-1]
            if tag == "title":
                title = ch.text or ""
            elif tag == "text":
                text = ch.text or ""
        el.clear()
        if title in wanted:
            pages[title] = text
    missing = wanted - pages.keys()
    if missing:
        raise SystemExit(f"páginas ausentes no dump: {sorted(missing)}")
    return pages


def clean(cell):
    s = cell
    s = re.sub(r"\{\{frac\|(\d+)\|(\d+)\}\}", r"\1/\2", s)
    s = re.sub(r"\{\{br\}\}", " ", s, flags=re.I)
    s = re.sub(r"<br\s*/?>", " ", s, flags=re.I)
    s = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"'{2,}", "", s)
    s = re.sub(r"<nowiki>(.*?)</nowiki>", r"\1", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("&nbsp;", " ").replace("&amp;", "&")
    return re.sub(r"\s+", " ", s).strip()


def strip_attrs(cell):
    """'colspan=2 | valor' → 'valor' (atributo antes de um | simples)."""
    m = re.match(r'^\s*(?:[a-z\-]+\s*=\s*"?[^"|]*"?\s*)+\|(?!\|)(.*)$', cell, re.S)
    return m.group(1) if m else cell


def note_line(line):
    """': * texto' ou ":''* texto''" → '* texto' (nota de rodapé da wiki)."""
    m = re.match(r"^:\s*(.*)$", line.strip())
    if not m:
        return None
    text = clean(m.group(1))
    return text if text.startswith("*") else None


def parse_tables(text):
    """[{caption, heading, headers, rows, notes}] na ordem da página."""
    out = []
    lines = text.split("\n")
    heading = section = sub = None
    i = 0
    while i < len(lines):
        h = re.match(r"^\s*(=+)\s*(.*?)\s*\1\s*$", lines[i])
        if h:
            heading = clean(h.group(2))
            if len(h.group(1)) == 2:
                section = heading
            if len(h.group(1)) <= 3:
                sub = heading
        if not lines[i].strip().startswith("{|"):
            i += 1
            continue
        start = i
        table = {"caption": None, "heading": heading, "section": section, "sub": sub, "headers": [], "rows": [], "notes": []}
        row, header_row = [], False
        i += 1

        def flush():
            if not row:
                return
            if header_row and not table["rows"]:
                table["headers"].append(list(row))
            else:
                table["rows"].append(list(row))

        while i < len(lines) and not lines[i].strip().startswith("|}"):
            line = lines[i].strip()
            if line.startswith("|+"):
                table["caption"] = clean(line[2:])
            elif line.startswith("|-"):
                flush()
                row, header_row = [], False
            elif line.startswith("!"):
                header_row = True
                row.extend(clean(strip_attrs(c)) for c in re.split(r"!!|\|\|", line[1:]))
            elif line.startswith("|"):
                row.extend(clean(strip_attrs(c)) for c in re.split(r"\|\|", line[1:]))
            elif line and row:
                row[-1] = (row[-1] + " " + clean(line)).strip()
            i += 1
        flush()
        # Notas logo antes e logo depois da tabela.
        before = []
        j = start - 1
        while j >= 0 and (note_line(lines[j]) or not lines[j].strip()):
            if note_line(lines[j]):
                before.insert(0, note_line(lines[j]))
            j -= 1
        after = []
        j = i + 1
        while j < len(lines) and (note_line(lines[j]) or not lines[j].strip()):
            if note_line(lines[j]):
                after.append(note_line(lines[j]))
            j += 1
        table["notes"] = before + after
        out.append(table)
        i += 1
    return out


def find(tables, pattern, nth=0):
    hits = [t for t in tables if re.search(pattern, f"{t['caption'] or ''} {t['heading'] or ''}")]
    if len(hits) <= nth:
        raise SystemExit(f"tabela não encontrada: {pattern} #{nth}")
    return hits[nth]


def single_header(t):
    """Cabeçalho de uma linha só (a última, a mais específica)."""
    if not t["headers"]:
        raise SystemExit(f"tabela sem cabeçalho: {t['caption'] or t['heading']}")
    return t["headers"][-1]


# --- Tabelas novas -----------------------------------------------------------------

# Seletor + subtabelas: (número, título, dado do seletor, página, [(letra, faixa), ...]).
SPLIT = [
    ("89", "Potions and Oils", "D6", "DMG Table 89", [("A", "1-2"), ("B", "3-4"), ("C", "5-6")]),
    ("90", "Scrolls", "D6", "DMG Table 90", [("A", "1-4"), ("B", "5-6")]),
    ("91", "Rings", "D6", "DMG Table 91", [("A", "1-4"), ("B", "5-6")]),
    ("96", "Miscellaneous Magic: Jewels, Jewelry, Phylacteries", "D6", "DMG Table 96", [("A", "1-3"), ("B", "4-6")]),
    ("104", "Miscellaneous Magic: The Weird Stuff", "D6", "DMG Table 104", [("A", "1-3"), ("B", "4-6")]),
    ("110", "Special Weapons", "D10", "Magical Weapons List (DMG)", None),  # faixas lidas da página
]

# Tabelas simples: (número, título, página, padrão do título na página).
SIMPLE = [
    ("55", "Dungeon Level", "DMG Table 55", r"Table 55"),
    ("56", "Frequency & Chance of Wilderness Encounters", "DMG Table 56", r"Table 56"),
    ("61", "Fields of Study", "DMG Table 61", r"Table 61"),
    ("62", "Sage Modifiers", "DMG Table 62", r"Table 62"),
    ("63", "Research Times", "DMG Table 63", r"Table 63"),
    ("66", "European Titles", "DMG Table 66", r"Table 66"),
    ("67", "Oriental Titles", "DMG Table 67", r"Table 67"),
    ("68", "Religious Titles", "DMG Table 68", r"Table 68"),
    ("69", "NPC Spell Costs", "DMG Table 69", r"Table 69"),
    ("70", "General Traits", "DMG Table 70", r"Table 70"),
    ("92", "Rods", "DMG Table 92", r"Table 92"),
    ("93", "Staves", "DMG Table 93", r"Table 93"),
    ("94", "Wands", "DMG Table 94", r"Table 94"),
    ("95", "Miscellaneous Magic: Books, Librams, Manuals, Tomes", "DMG Table 95", r"Table 95"),
    ("97", "Miscellaneous Magic: Cloaks and Robes", "DMG Table 97", r"Table 97"),
    ("98", "Miscellaneous Magic: Boots, Bracers, Gloves", "DMG Table 98", r"Table 98"),
    ("99", "Miscellaneous Magic: Girdles, Hats, Helms", "DMG Table 99", r"Table 99"),
    ("100", "Miscellaneous Magic: Bags, Bottles, Pouches, Containers", "DMG Table 100", r"Table 100"),
    ("101", "Miscellaneous Magic: Candles, Dusts, Ointments, Incense, and Stones", "DMG Table 101", r"Table 101"),
    ("102", "Miscellaneous Magic: Household Items and Tools", "DMG Table 102", r"Table 102"),
    ("103", "Miscellaneous Magic: Musical Instruments", "DMG Table 103", r"Table 103"),
    ("105", "Armor Type", "Armor and Shields Lists (DMG)", r"Table 105"),
    ("106", "Armor Class Adjustment", "Armor and Shields Lists (DMG)", r"Table 106"),
    ("107", "Special Armors", "Armor and Shields Lists (DMG)", r"Table 107"),
    ("109", "Attack Roll Adjustment", "Magical Weapons List (DMG)", r"Table 109"),
]

# Regra de destino de cada número (o resto vai para dmg_ch10_magical_item_tables).
TARGET = {
    "54": "dmg_ch11_creating_encounter_tables",
    "55": "dmg_ch11_creating_encounter_tables",
    "56": "dmg_ch11_dming_encounters",
    "61": "dmg_ch12_the_assassin_the_spy_and_the_sage",
    "62": "dmg_ch12_the_assassin_the_spy_and_the_sage",
    "63": "dmg_ch12_the_assassin_the_spy_and_the_sage",
    "66": "dmg_ch12_officials_and_social_rank",
    "67": "dmg_ch12_officials_and_social_rank",
    "68": "dmg_ch12_officials_and_social_rank",
    "69": "dmg_ch12_spellcasters",
    "70": "dmg_ch12_personality",
}
ITEM_TABLES = "dmg_ch10_magical_item_tables"

PAGES = sorted({p for _, _, p, _ in SIMPLE} | {s[3] for s in SPLIT} | {
    "DMG Table 54", "Magical Weapons List (DMG)", "Intelligent Weapons (DMG)",
    "Terrain Obstacles and Hindrances (DMG)", "Movement on Water (DMG)",
})


def new_table(number, title, headers, rows, notes=()):
    return {"number": number, "title": f"Table {number}: {title}", "headers": headers, "rows": rows, "notes": list(notes)}


def build_new(pages):
    out = []
    parsed = {name: parse_tables(text) for name, text in pages.items()}

    # 54: a wiki repete a linha 20 no fim (a tabela vai de 2 a 20).
    t = find(parsed["DMG Table 54"], r"Table 54")
    rows = t["rows"]
    while len(rows) > 1 and rows[-1] == rows[-2]:
        rows = rows[:-1]
    # Cabeçalho da fonte ("Dice Roll"): o 2-20 é 1d8 + 1d12 (texto da regra).
    out.append(new_table("54", "2-20 Encounter Table", single_header(t), rows, t["notes"]))

    for number, title, page, pattern in SIMPLE:
        t = find(parsed[page], pattern)
        headers = single_header(t)
        rows = t["rows"]
        if number == "56":
            # Cabeçalho em dois níveis: "Time of Day" cobre as seis faixas de horário.
            headers = ["Terrain Type", "Encounter Chance"] + [f"Time of Day: {h}" for h in t["headers"][-1]]
        if number == "70":
            # A 70 tem dois dados: d20 (traço geral) e d100 (traço específico, que
            # já diz o geral). O motor rola a primeira coluna: fica o d100, com o
            # traço geral repetido em cada linha.
            general, fixed = "", []
            for row in rows:
                if row[0].strip():
                    general = f"{row[1]} ({row[0]})"
                fixed.append([row[2], row[3], general])
            headers, rows = ["D100 Roll", "Specific Trait", "General Trait (D20)"], fixed
        if number == "62":
            # Cabeçalho em dois níveis ("Situation" / "Question is:") e um grupo
            # "Library is:" no meio das linhas: o grupo vai para o rótulo de cada linha.
            group, fixed = t["headers"][-1][0].rstrip(":"), []
            for row in rows:
                if row[0].endswith(":") and not row[1].strip():
                    group = row[0].rstrip(":")
                elif row[0] == "Rushed":
                    fixed.append(["Rushed", row[1]])
                else:
                    fixed.append([f"{group} {row[0].lower()}", row[1]])
            headers, rows = ["Situation", "Success Chance Penalty"], fixed
        out.append(new_table(number, title, headers, rows, t["notes"]))

    for number, title, die, page, subs in SPLIT:
        tables = parsed[page]
        if number == "110":
            subtables = [t for t in tables if re.match(r"Subtable [A-Z]", t["caption"] or "") and "Table 110" in (t["section"] or "")]
            subs = []
            for t in subtables:
                m = re.match(r"Subtable ([A-Z])\s*\(?([\d\-]+)\)?", t["caption"])
                subs.append((m.group(1), m.group(2)))
            picked = subtables
        else:
            picked = [find(tables, rf"Subtable {letter}\b") for letter, _ in subs]
        selector_rows = [[rng, f"Table {number}{letter}: {title}, Subtable {letter}"] for letter, rng in subs]
        out.append(new_table(number, title, [f"{die} Roll", "Subtable"], selector_rows))
        # As notas valem para todas as subtabelas: uma vez só, depois da última.
        notes = []
        for t in picked:
            notes += [n for n in t["notes"] if n not in notes]
        for i, ((letter, rng), t) in enumerate(zip(subs, picked)):
            last = i == len(picked) - 1
            out.append(new_table(f"{number}{letter}", f"{title}, Subtable {letter}", single_header(t), t["rows"], notes if last else []))

    # 108: as duas subtabelas lado a lado numa tabela só.
    t = find(parsed["Magical Weapons List (DMG)"], r"Table 108")
    left = [[r[0], r[1]] for r in t["rows"] if r[0].strip()]
    right = [[r[2], r[3]] for r in t["rows"] if len(r) > 3 and r[2].strip()]
    out.append(new_table("108", "Weapon Type", ["D6 Roll", "Subtable"],
                         [["1-2", "Table 108A: Weapon Type, Subtable A"], ["3-6", "Table 108B: Weapon Type, Subtable B"]], t["notes"]))
    out.append(new_table("108A", "Weapon Type, Subtable A", ["D20 Roll", "Weapon"], left))
    out.append(new_table("108B", "Weapon Type, Subtable B", ["D20 Roll", "Weapon"], right))
    return out


# --- Tabelas que já existem sem número --------------------------------------------

# (regra, índice em `tables`, número novo ou None, título novo, refazer pela wiki?)
RETITLE = [
    ("dmg_ch10_placement_of_treasure", 1, "84", "Table 84: Treasure Types (Individual and Small Lair Treasures)", None),
    ("dmg_ch10_treasure_tables", 1, "84", "Table 84: Treasure Types (Individual and Small Lair Treasures)", None),
    ("dmg_ch11_creating_encounter_tables", 0, None, "Example: Encounters for the Desert of Shaar", None),
    ("dmg_ch11_creating_encounter_tables", 1, None, "Example: 2-20 Encounter Table for the Desert of Shaar", None),
    ("dmg_ch11_creating_encounter_tables", 2, None, "Example: D100 Encounter Table for the Desert of Shaar", None),
    ("dmg_ch12_employing_hirelings", 1, None, "Example: Targash's Monthly Wages", None),
    ("dmg_ch10_scrolls", 0, None, "Spell Scroll Type", None),
    # As três abaixo são refeitas com as linhas da wiki: a extração perdeu os
    # sinais "+" (75) e o "+2" do começo da última linha virou título (117B).
    ("dmg_ch14_terrain_obstacles_and_hindrances", 0, "75", "Table 75: Terrain Modifiers", ("Terrain Obstacles and Hindrances (DMG)", r"Table 75")),
    ("dmg_ch14_movement_on_water", 2, "78", "Table 78: Sailing Movement Modifiers", ("Movement on Water (DMG)", r"Table 78")),
    ("dmg_ch10_intelligent_weapons", 4, "117", "Table 117: Special Purpose Weapons, Purpose", ("Intelligent Weapons (DMG)", r"Table 117")),
    ("dmg_ch10_intelligent_weapons", 5, "117B", "Table 117B: Special Purpose Weapons, Special Purpose Power", ("Intelligent Weapons (DMG)", r"Table 117")),
]

# --- Outras correções --------------------------------------------------------------

# "0" sozinho na última linha de tabelas d100 → "00" (zero perdido na extração).
ZERO_FIX = [
    ("dmg_ch10_treasure_tables", "Table 85: Gem Table"),
    ("dmg_ch10_intelligent_weapons", "Table 116: Weapon Extraordinary Powers"),
    ("dmg_ch10_intelligent_weapons", "Table 118: Languages Spoken by Weapon"),
    ("dmg_ch10_potions", "Table 111: Potion Compatibility"),
    ("phb_ch03_rogue_tables", "Table 31: Thief's Followers"),
    ("phb_ch03_warrior_tables", "Leader"),
    ("phb_ch03_warrior_tables", "Troops/Followers"),
    ("phb_ch03_warrior_tables", "Elite Units"),
    ("phb_ch03_warrior_tables", "Table 19: Ranger's Followers"),
]

# Trechos do `content` (markdown): (regra, errado, certo).
CONTENT_FIX = [
    # CRH-21: a linha do resultado 8 saiu como "6".
    ("crh_ch02_species_enemy", "| 6 | Seawolf, lyc. (includes greater) |", "| 8 | Seawolf, lyc. (includes greater) |"),
    # CRH-65: cabeçalho de três níveis da wiki achatado errado; fica numa linha só.
    (
        "crh_ch00_1st_edition_ranger",
        "|  | Spell Level | Spell Level | Spell Level | Spell Level | Spell Level |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| Ranger Level | Druidic | Druidic | Druidic | Magic-User** | Magic-User** 1 | Magic-User** 2 | Magic-User** 3 | Magic-User** 1 | Magic-User** 2 |\n"
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n",
        "| Ranger Level | Druidic 1 | Druidic 2 | Druidic 3 | Magic-User** 1 | Magic-User** 2 |\n"
        "| --- | --- | --- | --- | --- | --- |\n",
    ),
]


# --- Aplicação ---------------------------------------------------------------------


def insert_ref(rule, number, block):
    """Põe o bloco depois do parágrafo que cita 'Table N' (fora de [TABLE_REF]); senão, no fim."""
    content = rule["content"]
    base = re.match(r"\d+", number).group(0)
    for m in re.finditer(rf"(?<!TABLE_REF: )Table\s+{base}\b", content):
        end = content.find("\n\n", m.end())
        end = len(content) if end < 0 else end
        # Depois das tabelas que já estão ali (mantém a ordem dos números).
        while content.startswith("\n\n[TABLE_REF:", end) or content.startswith("\n\n(*", end):
            nxt = content.find("\n\n", end + 2)
            end = len(content) if nxt < 0 else nxt
        rule["content"] = content[:end] + "\n\n" + block + content[end:]
        return
    rule["content"] = content.rstrip("\n") + "\n\n" + block + "\n"


def main():
    dry = "--dry-run" in sys.argv
    with open(RULES, encoding="utf-8") as f:
        rules = json.load(f)
    by_id = {rule["id"]: rule for rule in rules}
    pages = load_pages(PAGES)
    changes = 0

    # Tabelas novas.
    item_rule = by_id[ITEM_TABLES]
    pending_items = []
    def order(t):
        m = re.match(r"(\d+)([A-Z]?)", t["number"])
        return int(m.group(1)), m.group(2)

    for t in sorted(build_new(pages), key=order):
        rule = by_id[TARGET.get(t["number"], ITEM_TABLES)]
        tables = rule.setdefault("tables", [])
        number = f"Table {t['number']}"
        if any(x.get("tableNumber") == number for x in tables):
            continue
        tables.append({"tableNumber": number, "title": t["title"], "headers": t["headers"], "rows": t["rows"]})
        # O [TABLE_REF] fica sozinho no parágrafo (o parser do iPad e da web só
        # o reconhece assim); as notas vêm no parágrafo seguinte, como "(*) …"
        # ("* " no começo da linha viraria item de lista e perderia o asterisco).
        block = f"[TABLE_REF: {t['title']}]"
        if t["notes"]:
            block += "\n\n" + "\n".join(re.sub(r"^(\*+)\s*", r"(\1) ", n) for n in t["notes"])
        if rule is item_rule:
            pending_items.append(block)
        else:
            insert_ref(rule, t["number"], block)
        changes += 1
        print(f"+ {rule['id']}: {t['title']} ({len(t['rows'])} linhas)")
    if pending_items:
        item_rule["content"] = item_rule["content"].rstrip("\n") + "\n\n" + "\n\n".join(pending_items) + "\n"

    # Tabelas sem número / título.
    parsed = {}
    for rule_id, index, number, title, source in RETITLE:
        rule = by_id[rule_id]
        t = rule["tables"][index]
        if t["title"] == title:
            continue
        old_ref = f"[TABLE_REF: {t['title']}]"
        if old_ref not in rule["content"]:
            raise SystemExit(f"{rule_id}: {old_ref} não está no content")
        rule["content"] = rule["content"].replace(old_ref, f"[TABLE_REF: {title}]", 1)
        t["title"] = title
        if number:
            t["tableNumber"] = f"Table {number}"
        if source:
            page, pattern = source
            tables = parsed.setdefault(page, parse_tables(pages[page]))
            hits = [x for x in tables if re.search(pattern, f"{x['caption'] or ''} {x['heading'] or ''} {x['sub'] or ''}")]
            # A 117 tem duas tabelas na mesma seção: A (Purpose) e B (Power).
            src = hits[1] if number == "117B" else hits[0]
            if single_header(src) != t["headers"] and [h.lower() for h in single_header(src)] != [h.lower() for h in t["headers"]]:
                raise SystemExit(f"{title}: cabeçalho difere da wiki: {single_header(src)} x {t['headers']}")
            t["rows"] = src["rows"]
        changes += 1
        print(f"~ {rule_id}[{index}]: {title}")

    # "0" → "00".
    for rule_id, title in ZERO_FIX:
        t = next(x for x in by_id[rule_id]["tables"] if x["title"] == title)
        if t["rows"][-1][0].strip() == "0":
            t["rows"][-1][0] = "00"
            changes += 1
            print(f"~ {rule_id}: {title}: 0 -> 00")

    # Tabela 88: as faixas vão de 01 a 100.
    t88 = next(x for x in item_rule["tables"] if x.get("tableNumber") == "Table 88")
    if t88["headers"][0] == "D20 Roll":
        t88["headers"][0] = "D100 Roll"
        changes += 1
        print("~ Table 88: D20 Roll -> D100 Roll")

    for rule_id, wrong, right in CONTENT_FIX:
        rule = by_id[rule_id]
        if wrong in rule["content"]:
            rule["content"] = rule["content"].replace(wrong, right, 1)
            changes += 1
            print(f"~ {rule_id}: content corrigido")
        elif right not in rule["content"]:
            raise SystemExit(f"{rule_id}: trecho não encontrado")

    if dry or changes == 0:
        print("(nada gravado)" if dry else "(nada a mudar)")
        return
    with open(RULES, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rules, indent=2, ensure_ascii=False) + "\n")
    print(f"{changes} mudanças gravadas")


if __name__ == "__main__":
    main()
