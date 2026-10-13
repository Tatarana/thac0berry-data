#!/usr/bin/env python3
"""GT4b (Ravenloft): regras e tabelas do Domains of Dread (livro DoD).

Fonte: as páginas do Domains of Dread no dump da wiki AD&D 2e
(`../thac0berry-data-mining/dumps/adnd2e_pages_current.xml`). O dump não tem as
regras centrais do cenário (powers checks, maldições, as Brumas); tem quatro
classes, a raça Half-Vistani, a seção de perícias de ladrão do Gypsy e duas
transcrições feitas por fãs das tabelas de Fear/Horror/Madness Checks.

Decisões do usuário (2026-10-10):
- livro novo `DoD` ("Domains of Dread"), cenário "Ravenloft" (scripts/build_books.py);
- uma regra por página (Anchorite, Arcanist, Avenger, Gypsy, Half-Vistani),
  uma para as perícias do Gypsy (Tabelas 97–102) e uma para os testes de
  medo, horror e loucura por grupo de classe;
- testes de medo: só os valores em que as duas transcrições dos fãs batem
  (bateram em todos, fora o Rogue 19–20, confirmado pela Tabela 95 do livro);
  a linha "21+" não tem valores em nenhuma das duas e fica de fora.

Rodar de novo não muda nada: regra com o mesmo id já presente é pulada.

Uso:  python scripts/add_ravenloft_dod.py [--dry-run]
"""
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RULES = os.path.join(ROOT, "data", "rules.json")
DUMP = os.path.join(ROOT, "..", "thac0berry-data-mining", "dumps", "adnd2e_pages_current.xml")

BOOK = "DoD"
BOOK_TITLE = "Domains of Dread"
SAVE_HEADERS = ["Experience Level", "Paralyzation, Poison, or Death Magic", "Rod, Staff, or Wand", "Petrification or Polymorph*", "Breath Weapon**", "Spell***"]
CHECK_HEADERS = ["Character Level", "Fear Check", "Horror Check", "Madness Check"]

# --- Leitura do dump e das tabelas wiki ---------------------------------------------


def load_pages(titles):
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
    s = re.sub(r"\{\{br\}\}", " ", s, flags=re.I)
    s = re.sub(r"<br\s*/?>", " ", s, flags=re.I)
    s = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"'{2,}", "", s)
    s = re.sub(r"<nowiki>(.*?)</nowiki>", r"\1", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"^=+\s*(.*?)\s*=+$", r"\1", s.strip())
    s = s.replace("&nbsp;", " ").replace("&amp;", "&")
    return re.sub(r"\s+", " ", s).strip()


def strip_attrs(cell):
    m = re.match(r'^\s*(?:[a-z\-]+\s*=\s*"?[^"|]*"?\s*)+\|(?!\|)(.*)$', cell, re.S)
    return m.group(1) if m else cell


def table_blocks(text):
    """[(início, fim, linhas)] de cada {| … |} (índices de linha), com as linhas da tabela."""
    lines = text.split("\n")
    out = []
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith("{|"):
            start = i
            while i < len(lines) and not lines[i].strip().startswith("|}"):
                i += 1
            out.append((start, i, lines[start:i + 1]))
        i += 1
    return out


def table_rows(block):
    """Todas as linhas da tabela (cabeçalho e corpo juntos), célula a célula."""
    rows, row = [], []
    for raw in block[1:-1]:
        line = raw.strip()
        if line.startswith("|+"):
            continue
        if line.startswith("|-"):
            if row:
                rows.append(row)
            row = []
        elif line.startswith("!"):
            row.extend(clean(strip_attrs(c)) for c in re.split(r"!!|\|\|", line[1:]))
        elif line.startswith("|"):
            row.extend(clean(strip_attrs(c)) for c in re.split(r"\|\|", line[1:]))
        elif line and row:
            row[-1] = (row[-1] + " " + clean(line)).strip()
    if row:
        rows.append(row)
    return rows


LEVEL = re.compile(r"^\d+(?:\s*[-–]\s*\d+)?\+?$")


def body_rows(rows, width):
    """Linhas de dados: a partir da primeira cujo 1º campo é nível/faixa, com `width` células."""
    out = []
    for row in rows:
        cells = [c for c in row]
        while len(cells) > width and cells[-1] == "":
            cells.pop()
        if LEVEL.match(cells[0] if cells else "") or out:
            out.append([c.replace("–", "-") for c in cells])
    return out


# --- Regras ---------------------------------------------------------------------------

# Introduções das classes: a extração embaralhou as colunas do bloco de requisitos
# (ex.: "Prime Requisite: Race Allowed: / Wisdom 12+ / Charisma 15+ Wisdom");
# os valores vêm do próprio texto de cada página.
INTROS = {
    "Anchorite": (
        "This unusual class of priest",
        "**Ability Requirements:** Wisdom 12, Charisma 15\n**Prime Requisite:** Wisdom\n**Races Allowed:** Human",
    ),
    "Arcanist": (
        "Arcanists are a special breed",
        "**Ability Requirements:** Intelligence 15, Wisdom 15\n**Prime Requisite:** Intelligence\n**Races Allowed:** Half-Vistani, Human",
    ),
    "Avenger": (
        "Avengers are fighters who",
        "**Ability Requirements:** Strength 15, Dexterity 14, Constitution 15\n**Prime Requisites:** Strength, Constitution\n**Races Allowed:** Dwarf, Half-Vistani, Human",
    ),
    "Gypsy": (
        "When most folk think",
        "**Ability Requirements:** Constitution 13, Intelligence 13, Wisdom 13, Charisma 15\n**Prime Requisites:** Dexterity, Charisma\n**Races Allowed:** Half-elf, Half-Vistani, Human",
    ),
    "Half-Vistani": ("The Vistani are, in actuality", ""),
    "Gypsy Thieving Skills": (
        "[TABLE_REF: Table 97",
        "Thieving skills of the gypsy: base scores and the adjustments for race, Dexterity and armor, with the lock quality and climbing modifiers. (The gypsy's saving throws, checks and experience levels are in the Gypsy rule.)",
    ),
}

# Títulos de seção que vieram como linha comum (sem "=="), por página.
HEADINGS = {
    "Anchorite": ["Ability Requirements", "Spells and Magical Items", "Alignment", "Arms and Armor", "Duties of the Anchorite"],
    "Arcanist": ["Ability Requirements", "Alignment", "Spells", "Learning Spells", "Magical Items", "Saving Throw Adjustments", "Forbidden Lore", "Powers Checks", "Horror Checks"],
}

# Trechos errados no texto das páginas: (página, errado, certo).
TEXT_FIXES = [
    # Nota solta copiada de outra classe, embaixo da tabela de progressão do Avenger (que não tem magias).
    ("Avenger", ": ** Maximum spell ability", ""),
    # Hifenização de quebra de linha do PDF.
    ("Anchorite", "understand- ing", "understanding"),
    ("Anchorite", "Demi- plane", "Demiplane"),
    ("Gypsy", "selec- tion", "selection"),
    ("Gypsy", "blood- roses", "blood-roses"),
    ("Gypsy", "outsiders-and", "outsiders—and"),
    ("Gypsy", "two- handed", "two-handed"),
    ("Gypsy", "so- called", "so-called"),
    ("Arcanist", "men- aces", "menaces"),
    ("Arcanist", "them- selves", "themselves"),
    ("Arcanist", "invocation/ evocation", "invocation/evocation"),
    # O título da seção de testes era um comentário de quem transcreveu.
    ("Gypsy", "New mechanic in ravenloft has fear horror madness here are the saves for Gypsy", "Fear, Horror and Madness Checks"),
]


# Tabelas de cada página, na ordem: (título, cabeçalhos, largura) ou None (sai do texto).
SPELLS7 = [f"Spells {n}" for n in ["1", "2", "3", "4", "5", "6*", "7**"]]
SPELLS9 = [f"Spells {n}" for n in range(1, 10)]
PAGES = {
    "Anchorite": ("Anchorite (domains of dread)", [
        ("Anchorite Progression", ["Level", "XP Needed", "Hit Dice (d8)", "THAC0"] + SPELLS7),
        ("Anchorite Saving Throws", SAVE_HEADERS),
    ]),
    "Arcanist": ("Arcanist (domains of dread)", [
        ("Arcanist Progression", ["Level", "XP Needed", "Hit Dice (d4)", "THAC0"] + SPELLS9),
        ("Arcanist Saving Throws", SAVE_HEADERS),
    ]),
    "Avenger": ("Avenger (domains of dread)", [
        ("Avenger Progression", ["Level", "XP Needed", "Hit Dice (d10)", "THAC0", "Attacks/Round"]),
        ("Avenger Saving Throws", SAVE_HEADERS),
    ]),
    "Gypsy": ("Gypsy (domains of dread)", [
        ("Gypsy Progression", ["Level", "XP Needed", "Hit Dice (d6)", "THAC0", "Weapon Proficiency Slots", "Nonweapon Proficiency Slots"]),
        ("Gypsy Saving Throws", SAVE_HEADERS),
        ("Table 95: Gypsy Fear, Horror and Madness Checks", CHECK_HEADERS),
        ("Table 104: Gypsy Spell Progression", ["Gypsy Level", "Wizard Spells 1", "Wizard Spells 2", "Wizard Spells 3", "Wizard Spells 4"]),
    ]),
    "Half-Vistani": ("Half-Vistani (domains of dread)", [
        ("Table 66: Half-Vistani Physical Characteristics", ["Trait", "Formula"]),
        ("Table 67: Half-Vistani Aging Effects", ["Age", "Years", "Effects"]),
        ("Table 68: Vistani Ancestry", ["Roll", "Tribal Heritage"]),
    ]),
    # Seção de perícias do Gypsy: as Tabelas 94–96 repetem os saves, os testes e o XP
    # da página do Gypsy e saem; ficam as 97–102.
    "Gypsy Thieving Skills": ("Raven loft fear horror madness tables", [
        None, None, None,
        ("Table 97: Thieving Skill Base Scores", ["Skill", "Base Score"]),
        ("Table 98: Thieving Skill Racial Adjustments", ["Skill", "Dwarf", "Elf", "Gnome", "Half-Elf", "Halfling"]),
        ("Table 99: Thieving Skill Dexterity Adjustments", ["Dexterity", "Pick Pockets", "Open Locks", "Find/Remove Traps", "Move Silently", "Hide in Shadows"]),
        ("Table 100: Thieving Skill Armor Adjustments", ["Skill", "No Armor", "Elven Chain", "Padded, Hide or Studded Leather"]),
        ("Table 101: Lock Quality Adjustments", ["Quality", "Adjustment"]),
        ("Table 102: Thief Climbing Modifiers", ["Situation", "Adjustment"]),
    ]),
}

# Células erradas nas tabelas: (título, valor errado, certo).
CELL_FIXES = [
    # Separador de milhar com ponto (padrão europeu) na tabela do Anchorite.
    ("Anchorite Progression", re.compile(r"^(\d{1,3})\.(\d{3})(?:\.(\d{3}))?$"), lambda m: ",".join(g for g in m.groups() if g)),
    # Sem o sinal na fonte; no PHB, superfície inclinada para dentro facilita a escalada (+25%).
    ("Table 102: Thief Climbing Modifiers", re.compile(r"^25%$"), lambda m: "+25%"),
    # "-" solto (nowiki) nas casas sem magia.
    ("Table 104: Gypsy Spell Progression", re.compile(r"^-$"), lambda m: "—"),
]

META = {
    "Anchorite": ("Characters", "core_rule", ["anchorite", "priest", "ezra", "church of ezra", "ravenloft"]),
    "Arcanist": ("Characters", "core_rule", ["arcanist", "wizard", "occult", "ravenloft"]),
    "Avenger": ("Characters", "core_rule", ["avenger", "fighter", "warrior", "revenge", "ravenloft"]),
    "Gypsy": ("Characters", "core_rule", ["gypsy", "rogue", "divination", "gypsy lore", "knife", "ravenloft"]),
    "Gypsy Thieving Skills": ("Characters", "core_rule", ["gypsy", "thieving skills", "thief", "climbing", "locks", "ravenloft"]),
    "Half-Vistani": ("Characters", "core_rule", ["half-vistani", "vistani", "glomorgo", "race", "ravenloft"]),
}


def slug(text):
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def to_markdown(text, headings=()):
    """Texto wiki → o markdown das regras (títulos ##/###, negrito, notas "(*) …")."""
    out = []
    for raw in text.split("\n"):
        line = raw.rstrip()
        if re.match(r"^\s*(\{\{[^}]*\}\}\.?|__TOC__|\[\[Category:[^\]]*\]\])\s*$", line) or line.strip().startswith("{{Navbox"):
            continue
        if line.strip() in headings:
            out += ["", "### " + line.strip(), ""]
            continue
        line = re.sub(r"^\{\{stub\}\}\.?", "", line)
        h = re.match(r"^\s*(=+)\s*(.*?)\s*=+\s*$", line)
        if h:
            level = "## " if len(h.group(1)) <= 2 else "### "
            out.append("")
            out.append(level + clean(h.group(2)))
            out.append("")
            continue
        line = re.sub(r"<nowiki>(.*?)</nowiki>", r"\1", line)
        note = re.match(r"^\s*:?\s*(\*+)\s*(.*)$", line)
        if note and line.strip().startswith((":", "*")):
            out.append(f"({note.group(1)}) {clean(note.group(2))}")
            continue
        line = re.sub(r"^:\s*", "", line)
        line = re.sub(r"'''(.*?)'''", r"**\1**", line)
        line = re.sub(r"''(.*?)''", r"*\1*", line)
        line = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", line)
        out.append(line.strip())
    md = "\n".join(out)
    # Notas seguidas: uma por linha, sem linha em branco no meio.
    md = re.sub(r"(\(\*+\) [^\n]*)\n\n(?=\(\*+\) )", r"\1\n", md)
    md = re.sub(r"\n(\(\*+\) )", r"\n\1", md)
    return re.sub(r"\n{3,}", "\n\n", md).strip()


def build_page_rule(key, text):
    page_title, specs = PAGES[key]
    for page, wrong, right in TEXT_FIXES:
        if page == key:
            if wrong not in text:
                raise SystemExit(f"{key}: trecho não encontrado: {wrong!r}")
            text = text.replace(wrong, right)
    blocks = table_blocks(text)
    if len(blocks) != len(specs):
        raise SystemExit(f"{key}: {len(blocks)} tabelas na página, {len(specs)} esperadas")
    lines = text.split("\n")
    tables = []
    # Troca cada tabela pelo [TABLE_REF] (de trás para frente, para os índices valerem).
    for (start, end, block), spec in reversed(list(zip(blocks, specs))):
        if spec is None:
            # Sai a tabela e as notas logo abaixo dela.
            stop = end + 1
            while stop < len(lines) and (not lines[stop].strip() or re.match(r"^\s*(:|<nowiki>\*|\*)", lines[stop])):
                stop += 1
            lines[start:stop] = []
            continue
        title, headers = spec
        rows = table_rows(block)
        if key == "Half-Vistani" or key == "Gypsy Thieving Skills":
            # Cabeçalho próprio numa linha; o corpo é o resto (exceto o cabeçalho repetido).
            rows = [r for r in rows if [c.lower() for c in r] != [h.lower() for h in headers] and r[0] not in ("Trait", "Age", "Roll", "Skill", "Dexterity", "Quality", "Situation")]
            rows = [r[: len(headers)] for r in rows]
        else:
            rows = body_rows(rows, len(headers))
        for fix_title, pattern, repl in CELL_FIXES:
            if fix_title == title:
                rows = [[pattern.sub(repl, c) for c in r] for r in rows]
        bad = [r for r in rows if len(r) != len(headers)]
        if bad:
            raise SystemExit(f"{title}: linhas com largura errada: {bad[:3]}")
        number = re.match(r"Table (\d+)", title)
        tables.insert(0, {"tableNumber": f"Table {number.group(1)}" if number else "", "title": title, "headers": headers, "rows": rows})
        lines[start:end + 1] = ["", f"[TABLE_REF: {title}]", ""]
    text = "\n".join(lines)
    head = ""
    intro = INTROS.get(key)
    if intro:
        cut = text.find(intro[0])
        if cut < 0:
            raise SystemExit(f"{key}: início do texto não encontrado")
        # Guarda as tabelas que estavam antes do corte (ex.: progressão do Avenger).
        refs = re.findall(r"\[TABLE_REF: [^\]]*\]", text[:cut])
        head = "\n\n".join([p for p in [intro[1]] + refs if p]) + "\n\n"
        text = text[cut:]
    content = (head + to_markdown(text, HEADINGS.get(key, ()))).strip()
    topic = key
    chapter, rule_type, keywords = META[key]
    first = next(p for p in content.split("\n\n") if not p.startswith(("**", "[TABLE_REF", "#")))
    summary = re.split(r"(?<=[.!?])\s", first.strip(), maxsplit=1)[0]
    return {
        "id": f"dod_ch00_{slug(key)}",
        "book": BOOK,
        "chapterNumber": 0,
        "chapterTitle": chapter,
        "breadcrumbs": f"{BOOK_TITLE} > {chapter} > {topic}",
        "topic": topic,
        "ruleType": rule_type,
        "summary": summary,
        "content": content,
        "tables": tables,
        "relatedRuleIds": [],
        "relatedSpells": [],
        "relatedMagicItems": [],
        "searchKeywords": keywords,
    }


def build_checks_rule(pages):
    """Fear/Horror/Madness Checks por grupo: valores em que as duas transcrições batem."""
    blank = [table_rows(b) for _, _, b in table_blocks(pages["Blank horror table domains of dread"])]
    compat = [table_rows(b) for _, _, b in table_blocks(pages["Ravenloft Character Compatibility"])]
    # Ordem das tabelas em cada página (a primeira da "blank" é um modelo vazio).
    by_group_b = dict(zip(["Priest", "Rogue", "Warrior", "Wizard", "Psionicist"], blank[1:]))
    by_group_c = dict(zip(["Warrior", "Rogue", "Wizard", "Priest", "Psionicist"], compat))
    gypsy = {r[0].replace("–", "-"): r[1:4] for r in body_rows(table_rows(table_blocks(pages["Gypsy (domains of dread)"])[2][2]), 4)}
    tables, content = [], [
        "Fear, horror and madness check numbers by class group and level (*Domains of Dread*).",
        "These tables were compiled from two fan transcriptions on the AD&D 2e wiki; every value below appears the same in both (the rogue's 19–20 row is confirmed by Table 95, the gypsy's checks). Levels above 20 have no values in either transcription.",
    ]
    for group in ["Warrior", "Priest", "Rogue", "Wizard", "Psionicist"]:
        b = {r[0].replace("–", "-").replace(" ", ""): r[-3:] for r in by_group_b[group] if LEVEL.match(r[0].replace("–", "-").replace(" ", ""))}
        c = {r[0].replace("–", "-").replace(" ", ""): r[1:4] for r in by_group_c[group] if LEVEL.match(r[0].replace("–", "-").replace(" ", ""))}
        rows = []
        for level in c:
            values = c[level]
            if b.get(level) != values:
                # Única divergência conhecida: Rogue 19–20 ("X" numa das cópias), confirmada pela Tabela 95.
                if not (group == "Rogue" and gypsy.get(level) == values):
                    raise SystemExit(f"{group} {level}: transcrições diferentes: {b.get(level)} x {values}")
            rows.append([level] + values)
        title = f"{group} Fear, Horror and Madness Checks"
        tables.append({"tableNumber": "", "title": title, "headers": CHECK_HEADERS, "rows": rows})
        content.append(f"[TABLE_REF: {title}]")
    return {
        "id": "dod_ch00_fear_horror_and_madness_checks",
        "book": BOOK,
        "chapterNumber": 0,
        "chapterTitle": "Fear, Horror and Madness",
        "breadcrumbs": f"{BOOK_TITLE} > Fear, Horror and Madness > Fear, Horror and Madness Checks",
        "topic": "Fear, Horror and Madness Checks",
        "ruleType": "table_reference",
        "summary": content[0],
        "content": "\n\n".join(content),
        "tables": tables,
        "relatedRuleIds": [],
        "relatedSpells": [],
        "relatedMagicItems": [],
        "searchKeywords": ["fear check", "horror check", "madness check", "ravenloft"],
    }


def number_chapters(rules, books):
    """Numera os capítulos dos livros importados da wiki (que não têm número):
    1, 2, 3… na ordem em que cada `chapterTitle` aparece no rules.json. Sem
    isso, todas as regras do livro tinham o capítulo 0 e a web as agrupava num
    capítulo só, com o nome do primeiro. Devolve quantas regras mudaram."""
    order = {}
    changed = 0
    for rule in rules:
        if rule["book"] not in books:
            continue
        titles = order.setdefault(rule["book"], [])
        if rule["chapterTitle"] not in titles:
            titles.append(rule["chapterTitle"])
        number = titles.index(rule["chapterTitle"]) + 1
        if rule["chapterNumber"] != number:
            rule["chapterNumber"] = number
            changed += 1
    return changed


def main():
    dry = "--dry-run" in sys.argv
    with open(RULES, encoding="utf-8") as f:
        rules = json.load(f)
    ids = {r["id"] for r in rules}
    pages = load_pages([p for p, _ in PAGES.values()] + ["Blank horror table domains of dread", "Ravenloft Character Compatibility"])
    new = [build_page_rule(key, pages[PAGES[key][0]]) for key in ["Anchorite", "Arcanist", "Avenger", "Gypsy", "Gypsy Thieving Skills", "Half-Vistani"]]
    new.append(build_checks_rule(pages))
    added = 0
    for rule in new:
        print(f"{'=' if rule['id'] in ids else '+'} {rule['id']}: {len(rule['tables'])} tabelas, {len(rule['content'])} caracteres")
        if rule["id"] in ids:
            continue
        rules.append(rule)
        added += 1
    added += number_chapters(rules, ["DoD"])
    if dry or added == 0:
        print("(nada gravado)" if dry else "(nada a mudar)")
        return
    with open(RULES, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rules, indent=2, ensure_ascii=False) + "\n")
    print(f"{added} regras gravadas")


if __name__ == "__main__":
    main()
