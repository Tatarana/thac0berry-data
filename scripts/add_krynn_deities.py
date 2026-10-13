#!/usr/bin/env python3
"""Deuses de Krynn (Tales of the Lance, TotL) no data/deities.json.

Por quê (2026-10-13, decisão do usuário): na GT4b os 21 deuses entraram
como regras (scripts/add_dragonlance.py); agora vão para o compêndio de
divindades, no mesmo formato dos deuses do Faiths & Avatars, e saem das
regras (fica só "Descriptions of the True Gods", com a lista).

Fonte: as páginas dos deuses no dump da wiki AD&D 2e
(`../thac0berry-data-mining/dumps/adnd2e_pages_current.xml`): o High God e
os 21 deuses. Cada página traz "==Nome, Título (Rank)==", Gender, Home
Plane, Description, Role-Playing Notes, Statistics (AL, WAL, AoC, SY),
Other Names, os avatares com a ficha e os deveres do clero.

Correspondência com os campos do FA: rank (o rank do título), plane (Home
Plane), alignment (AL), worshiperAlignments (WAL), portfolio (AoC), symbol
(SY), aliases (Other Names), avatarClassLevels e avatarDescription (seção
dos avatares, com a ficha em texto). O livro não separa aliados, inimigos,
superior nem domínio: ficam null.

Rodar de novo não muda nada (deus com o mesmo id é pulado; --refresh refaz).

Uso:  python scripts/add_krynn_deities.py [--dry-run] [--refresh]
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from add_dragonlance import DEITIES  # noqa: E402
from add_ravenloft_dod import load_pages  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "data", "deities.json")

BOOK, CODE, CATEGORY = "Tales of the Lance", "TotL", "Krynn Gods"
NAMES = ["High God"] + DEITIES


def plain(text):
    """Marcação da wiki → texto simples (o formato do fullText do FA)."""
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    text = re.sub(r"__(NO)?TOC__", "", text)
    text = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", text)
    text = re.sub(r"'''(.*?)'''", r"\1", text)
    text = text.replace("''", "")
    text = re.sub(r"^=+\s*(.*?)\s*=+\s*$", r"\1", text, flags=re.M)
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def field(text, label):
    m = re.search(rf"^'''{re.escape(label)}:'''\s*(.*)$", text, re.M)
    return plain(m.group(1)).rstrip(".") if m else None


def statistic(stats, key):
    """"AL N; WAL Any; AoC …; SY …" → o valor da chave."""
    # Branchala: "AL NG, WAL Any non-Evil" (vírgula no lugar do ponto e vírgula).
    for part in re.sub(r",\s*(?=(?:AL|WAL|AoC|SY) )", "; ", stats or "").split(";"):
        part = part.strip()
        if part.startswith(key + " "):
            return part[len(key) + 1:].strip().rstrip(".")
    return None


def avatar_lines(table):
    """A ficha do avatar (três formatos na wiki) em texto: "Str 24, Dex 20, …"."""
    pairs, names = [], None
    for line in table.split("\n"):
        s = line.strip()
        if not s or s.startswith(("{|", "|}", "|-", "|+")):
            continue
        body = s[1:].strip().rstrip("|").strip()
        cells = [c.strip() for c in re.split(r"\s*(?:\|\||!!)\s*", body)] if ("||" in body or "!!" in body) else [c.strip() for c in body.split(" | ")]
        if s.startswith("!"):
            names = cells
        elif names:
            pairs += [f"{n} {v}" for n, v in zip(names, cells)]
            names = None
        else:
            pairs += cells
    return ", ".join(plain(p) for p in pairs)


def build(name, text):
    head = re.search(r"^==\s*(.+?)\s*\((Greater|Intermediate|Lesser|Demi)\s*God(?:dess)?\)\s*==\s*$", text, re.M)
    if not head:
        raise SystemExit(f"{name}: título com o rank não encontrado")
    title, rank = head.group(1), f"{head.group(2)} God"
    stats = field(text, "Statistics")
    # Seção dos avatares: do título "==… Avatars (classes)==" até a próxima seção de mesmo nível.
    avatar = re.search(r"^==\s*[^=]*Avatars?\s*\(([^)]*)\)\s*==\s*$(.*?)(?=^==[^=]|\Z)", text, re.M | re.S)
    avatar_classes = avatar.group(1).strip() if avatar else None
    avatar_text = None
    body = text
    if avatar:
        section = avatar.group(2)
        table = re.search(r"^\{\|.*?^\|\}", section, re.M | re.S)
        sheet = avatar_lines(table.group(0)) if table else ""
        prose = plain(re.sub(r"^\{\|.*?^\|\}", "", section, flags=re.M | re.S))
        avatar_text = "\n\n".join(p for p in (prose, sheet) if p)
        body = text[: avatar.start()] + text[avatar.end():]
    description = field(text, "Description") or ""
    full = plain(body.replace(head.group(0), ""))
    full = re.sub(r"^Statistics:.*$\n?", "", full, flags=re.M).strip()
    return {
        "id": re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_"),
        "name": name,
        "book": BOOK,
        "bookCode": CODE,
        "rank": rank,
        "plane": field(text, "Home Plane"),
        "alignment": statistic(stats, "AL"),
        "status": None,
        "portfolio": statistic(stats, "AoC") or title.split(",", 1)[-1].strip(),
        "aliases": field(text, "Other Names"),
        "domainName": None,
        "superior": None,
        "allies": None,
        "foes": None,
        "symbol": statistic(stats, "SY"),
        "worshiperAlignments": statistic(stats, "WAL"),
        "avatarClassLevels": avatar_classes,
        "avatarDescription": avatar_text,
        "briefSummary": re.split(r"(?<=[.!?])\s", description, maxsplit=1)[0],
        "fullText": full,
        "categories": [CATEGORY],
    }


def main():
    dry = "--dry-run" in sys.argv
    refresh = "--refresh" in sys.argv
    with open(OUT, encoding="utf-8") as f:
        deities = json.load(f)
    pages = load_pages([f"{n} (TotL)" for n in NAMES])
    by_id = {d["id"]: i for i, d in enumerate(deities)}
    changed = 0
    for name in NAMES:
        deity = build(name, pages[f"{name} (TotL)"])
        if deity["id"] in by_id:
            i = by_id[deity["id"]]
            if deities[i]["book"] != BOOK:
                raise SystemExit(f"id repetido com outro livro: {deity['id']}")
            if refresh and deities[i] != deity:
                deities[i] = deity
                changed += 1
                print(f"~ {deity['id']}: refeito")
            continue
        deities.append(deity)
        changed += 1
        print(f"+ {deity['id']}: {deity['rank']}, {deity['alignment']}, {deity['portfolio'][:50]}")
    if dry or changed == 0:
        print("(nada gravado)" if dry else "(nada a mudar)")
        return
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(deities, indent=2, ensure_ascii=False) + "\n")
    print(f"{changed} divindades gravadas")


if __name__ == "__main__":
    main()
