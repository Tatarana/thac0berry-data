#!/usr/bin/env python3
"""Tabelas em sintaxe de wiki (MediaWiki) viram tabelas em markdown nos textos.

Por quê (2026-11-18, auditoria de tabelas): 28 proficiências, 3 deuses e 3
resumos de magias de sacerdote guardam o bloco "{| ... |}" da wiki como veio
("| a || b", "|-", "! cabeçalho"). A web desenha tabelas em markdown ("| a | b |"
mais a linha "| --- |"), mas mostra a sintaxe da wiki como texto cru.

Regra:
  - Vale para qualquer texto (string) dos arquivos data/proficiencies.json,
    data/deities.json e data/priest_*.json.
  - "! x !! y" ou "! x" por linha = cabeçalho; "|-" separa linhas; "||" separa
    células; "|+ título" vira a linha em negrito acima da tabela ("**título**",
    que a web usa como título); atributos como `style="..." |` somem.
  - colspan vira células vazias à direita; linha de uma célula só que cobre a
    tabela inteira (nota de rodapé) sai depois da tabela, como texto.
  - Cabeçalho "!" sozinho numa linha, seguido de uma linha de uma célula só
    (Enamor), vira uma linha de duas colunas (rótulo | texto).
  - Tabela sem cabeçalho ganha cabeçalho vazio (a web esconde).
  - Um segundo cabeçalho no meio (depois de duas linhas ou mais) abre outra tabela.
  - Bloco que na verdade é prosa (célula com linha em branco: sonhos, presságios)
    vira só o texto, sem tabela.
  - Bloco cortado sem "|}" (resumo de magia truncado em ~200 caracteres): corta
    dali em diante; se não sobrar nada, o resumo vem do começo da descrição.
  - Idempotente: depois de convertido não sobra "{|" e o script não muda mais nada.
  - Preserva o formato de cada JSON (indentado ou numa linha só), UTF-8 sem BOM, LF.

Uso:  python scripts/fix_wiki_table_syntax.py [--dry-run]
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA = os.path.join(ROOT, "data")
FILES = ["proficiencies.json", "deities.json"] + sorted(
    os.path.basename(p) for p in glob.glob(os.path.join(DATA, "priest_*.json"))
)

BLOCK = re.compile(r"\{\|.*?\|\}", re.S)
ATTRS = re.compile(r"^((?:\s*[A-Za-z-]+\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s|]+))+)\s*\|(?!\|)\s*(.*)$", re.S)


def clean(text):
    return text.replace("'''", "").replace("''", "").strip()


def parse_cells(raw_cells):
    """[(tipo, texto bruto)] -> [(tipo, texto, colspan, rowspan)] sem atributos."""
    cells = []
    for kind, raw in raw_cells:
        colspan = rowspan = 1
        match = ATTRS.match(raw.strip("\n ") if raw.strip() else raw)
        text = raw
        if match:
            colspan_match = re.search(r"colspan\s*=\s*\"?(\d+)", match.group(1))
            colspan = int(colspan_match.group(1)) if colspan_match else 1
            rowspan_match = re.search(r"rowspan\s*=\s*\"?(\d+)", match.group(1))
            rowspan = int(rowspan_match.group(1)) if rowspan_match else 1
            text = match.group(2)
        cells.append((kind, clean(text), colspan, rowspan))
    return cells


def parse_block(block):
    """Devolve (legenda, linhas) ou None se for prosa. Linha = lista de (tipo, texto, colspan)."""
    lines = block.split("\n")[1:]  # sem a linha "{| class=..."
    if lines and lines[-1].strip() == "|}":
        lines = lines[:-1]
    caption = ""
    rows, current = [], []
    last = None  # onde a linha de continuação entra: "caption" ou a última célula
    for line in lines:
        if line.startswith("|+"):
            caption = line[2:].strip()
            last = "caption"
        elif line.startswith("|-"):
            if current:
                rows.append(current)
            current, last = [], None
        elif line.startswith("!") or line.startswith("|"):
            kind = line[0]
            body = line[1:]
            pieces = re.split(r"\|\||!!", body) if kind == "!" else body.split("||")
            for piece in pieces:
                current.append([kind, piece])
            last = "cell"
        elif last == "caption":
            caption += " " + line.strip()
        elif current:
            # "||" numa linha de continuação também separa células.
            first, *more = line.split("||")
            current[-1][1] += "\n" + first
            current.extend([current[-1][0], piece] for piece in more)
    if current:
        rows.append(current)
    parsed = [parse_cells(row) for row in rows]
    if any("\n\n" in text for row in parsed for _, text, _, _ in row):
        return None
    return clean(caption), parsed


def flat(text):
    return re.sub(r"\s*\n\s*", " ", text).strip()


def md_row(cells, width):
    cells = [flat(c).replace("|", "\\|") for c in cells]
    cells += [""] * (width - len(cells))
    return "| " + " | ".join(cells) + " |"


def expand(cells):
    out = []
    for _, text, colspan, _ in cells:
        out.append(text)
        out.extend([""] * (colspan - 1))
    return out


def merge_headers(head_rows):
    """Cabeçalho de várias linhas (rowspan/colspan): um texto por coluna, de cima para baixo."""
    if not head_rows:
        return []
    width = sum(c[2] for c in head_rows[0])
    names = [[] for _ in range(width)]
    occupied = set()
    for r, row in enumerate(head_rows):
        col = 0
        for _, text, colspan, rowspan in row:
            while col in occupied and r > 0:
                col += 1
            for k in range(colspan):
                if col + k < width and text and text not in names[col + k]:
                    names[col + k].append(text)
                if rowspan > 1 and r == 0:
                    occupied.add(col + k)
            col += colspan
    return [" ".join(n) for n in names]


def render_table(headers, rows):
    width = max([len(headers)] + [len(r) for r in rows])
    head = headers or [""] * width
    lines = [md_row(head, width), "| " + " | ".join(["---"] * width) + " |"]
    lines += [md_row(r, width) for r in rows]
    return lines


def convert_block(block):
    parsed = parse_block(block)
    if parsed is None:
        # Prosa dentro da "tabela": só o texto das células.
        inner = block.split("\n")[1:]
        if inner and inner[-1].strip() == "|}":
            inner = inner[:-1]
        if inner and inner[0].strip() == "|":
            inner = inner[1:]
        return "\n".join(inner).strip()
    caption, rows = parsed
    tables = []  # [headers, rows]
    notes = []
    head_rows, body = [], []
    label = None  # cabeçalho "!" de uma célula só, esperando a linha de dados
    span_title = ""

    def close():
        nonlocal head_rows, body
        if body or head_rows:
            tables.append((merge_headers(head_rows), body))
        head_rows, body = [], []

    for cells in rows:
        only_header = all(c[0] == "!" for c in cells)
        text_cells = [c for c in cells if c[1] != ""]
        if only_header and len(cells) == 1 and cells[0][2] > 1 and not body:
            span_title = cells[0][1]
        elif only_header and len(cells) == 1:
            label = cells[0][1]
        elif only_header and not body:
            head_rows.append(cells)
        elif only_header and len(body) >= 2:
            close()
            head_rows = [cells]
        elif len(cells) == 1 and cells[0][2] > 1 and (body or head_rows):
            if cells[0][1]:
                notes.append(cells[0][1].strip())
        elif not text_cells:
            continue
        else:
            row = expand(cells)
            if label is not None and not only_header:
                row = [label] + row
            label = None
            body.append(row)
    if label is not None:
        body.append([label])
    close()

    title = caption
    if span_title:
        title = f"{caption} – {span_title}" if caption else span_title
    out = []
    for index, (head, rows_) in enumerate(tables):
        if index == 0 and title:
            out.append(f"**{title}**")
        if index > 0:
            out.append("")
        out += render_table(head, rows_)
    if not tables and title:
        out.append(title)
    out += notes
    return "\n".join(out)


def convert_text(text):
    """Converte os blocos "{| |}" de um texto; bloco cortado (sem "|}") é removido."""
    def replace(match):
        # Cada tabela começa numa linha própria, e o texto depois também.
        before = text[: match.start()]
        after = text[match.end():]
        out = convert_block(match.group(0))
        if before and not before.endswith("\n"):
            out = "\n" + out
        if after and not after.startswith("\n"):
            out += "\n"
        return out

    new = BLOCK.sub(replace, text)
    if "{|" in new:
        new = new[: new.index("{|")].rstrip()
    return new


def fix_value(value):
    """Percorre o JSON e converte as strings; devolve o valor novo e quantas mudaram."""
    if isinstance(value, str):
        if "{|" not in value:
            return value, 0
        return convert_text(value), 1
    if isinstance(value, list):
        out, n = [], 0
        for item in value:
            new, k = fix_value(item)
            out.append(new)
            n += k
        return out, n
    if isinstance(value, dict):
        out, n = {}, 0
        for key, item in value.items():
            new, k = fix_value(item)
            out[key] = new
            n += k
        return out, n
    return value, 0


def summary_from_full(full):
    """Resumo cortado sem nada útil: começo da descrição, sem o título "==...==", até 150 caracteres."""
    text = re.sub(r"^==[^=\n]+==\s*", "", full or "").strip()
    text = re.sub(r"\s+", " ", text)
    if len(text) <= 150:
        return text
    return text[:150].rsplit(" ", 1)[0].rstrip(",;:") + "…"


def fix_record_summary(record):
    """Resumo de magia que sobrou só com título ("==Errata==") depois do corte."""
    summary = record.get("summary")
    if isinstance(summary, str) and re.fullmatch(r"\s*(==[^=\n]+==)?\s*", summary):
        record["summary"] = summary_from_full(record.get("fullDescription"))


def load_formatted(path):
    with open(path, encoding="utf-8", newline="") as f:
        raw = f.read()
    data = json.loads(raw)
    indented = raw.startswith("[\n")
    if indented:
        dump = lambda d: json.dumps(d, indent=2, ensure_ascii=False) + "\n"
    else:
        dump = lambda d: json.dumps(d, separators=(",", ":"), ensure_ascii=False)
    if dump(data) != raw:
        sys.exit(f"{path}: o formato atual não se reproduz; abortando sem escrever.")
    return data, dump


def main():
    dry = "--dry-run" in sys.argv
    total = 0
    for name in FILES:
        path = os.path.join(DATA, name)
        with open(path, encoding="utf-8") as f:
            if "{|" not in f.read():
                continue
        data, dump = load_formatted(path)
        changed = []
        for record in data:
            new, n = fix_value(record)
            if n:
                if isinstance(new, dict) and "summary" in new:
                    fix_record_summary(new)
                record.clear()
                record.update(new)
                changed.append(record.get("id", "?"))
        if changed:
            total += len(changed)
            print(f"{name}: {len(changed)} registros: {', '.join(changed)}")
            if not dry:
                with open(path, "w", encoding="utf-8", newline="\n") as f:
                    f.write(dump(data))
    print(f"{'(dry-run) ' if dry else ''}{total} registros alterados.")


if __name__ == "__main__":
    main()
