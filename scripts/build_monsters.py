#!/usr/bin/env python3
"""Gera o catálogo de monstros a partir do thac0berry-data-mining.

Fonte: thac0berry-data-mining/data/monsters/*.json (páginas da wiki com o
texto original em `description.rawWikitext`). Os campos estruturados de lá
perderam informação (XP cortado na vírgula, só a 1ª coluna de variantes,
THAC0 lido do campo errado), então este script relê o infobox `{{Creature}}`
direto do texto original. Análise e decisões: 2026-10-07, com o usuário.

- Cada coluna do infobox (`thac01`, `thac02`...) e cada bloco `{{Creature}}`
  da página (`<tabber>`) vira uma variante.
- Cada estatística guarda o texto completo e, quando é um número simples,
  também o valor (para filtrar e ordenar): "11,000" -> 11000; "19 to 15" só texto.
- Páginas sem `{{Creature}}` (cartas colecionáveis de 1992, "See also")
  ficam de fora (decisão do usuário).
- Erros da própria wiki corrigidos: campos de ecologia deslocados (a wiki
  pulou um campo e o resto escorregou, ou trocou dois de lugar), reconhecidos
  pelo vocabulário de cada campo; erros de digitação em TYPOS; casos pontuais
  em MANUAL. O relatório lista cada correção.

Uso:  python scripts/build_monsters.py --out PASTA [--mining CAMINHO]
"""
import argparse
import collections
import glob
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_MINING = os.path.join(ROOT, "..", "thac0berry-data-mining", "data", "monsters")

# Chave do infobox -> (grupo, campo). Variações de grafia da wiki incluídas.
FIELDS = {
    "terrain": ("ecology", "climateTerrain"),
    "frequency": ("ecology", "frequency"),
    "organization": ("ecology", "organization"),
    "activitycycle": ("ecology", "activityCycle"),
    "diet": ("ecology", "diet"),
    "intelligence": ("ecology", "intelligence"),
    "treasure": ("ecology", "treasure"),
    "alignment": ("ecology", "alignment"),
    "align": ("ecology", "alignment"),
    "numberappearing": ("combat", "numberAppearing"),
    "armorclass": ("combat", "armorClass"),
    "movement": ("combat", "movement"),
    "hitdice": ("combat", "hitDice"),
    "thac0": ("combat", "thac0"),
    "thaco": ("combat", "thac0"),
    "noofattacks": ("combat", "attacks"),
    "numberofattacks": ("combat", "attacks"),
    "damageattack": ("combat", "damage"),
    "specialattack": ("combat", "specialAttacks"),
    "specialdefenses": ("combat", "specialDefenses"),
    "specialdefense": ("combat", "specialDefenses"),
    "magicalresistance": ("combat", "magicResistance"),
    "size": ("combat", "size"),
    "moral": ("combat", "morale"),
    "morale": ("combat", "morale"),
    "xp": ("combat", "xp"),
    "name": ("meta", "name"),
    "source": ("meta", "source"),
    "book": ("meta", "source"),
    "note": ("meta", "note"),
    "notes": ("meta", "note"),
    # Birthright (blood hound e afins): campos próprios do cenário.
    "bloodline": ("extra", "Bloodline"),
    "bloodabilities": ("extra", "Blood Abilities"),
    "seeming": ("extra", "Seeming"),
}
IGNORED = {"image", "caption", "width", "style", "class"}

ECOLOGY_ORDER = ["climateTerrain", "frequency", "organization", "activityCycle", "diet", "intelligence", "treasure", "alignment"]

# Erros de digitação da wiki (valor exato -> correto).
TYPOS = {
    "Verv rare": "Very rare",
    "Commnn": "Common",
    "Si1t": "Silt",
    "Averaqge (8-10)": "Average (8-10)",
    "Supre-genius (19)": "Supra-genius (19)",
    "Highly intelligent (13014)": "Highly intelligent (13-14)",
    "Genius (17.18)": "Genius (17-18)",
    "Varies (6.18)": "Varies (6-18)",
    "Semi- (2.4)": "Semi- (2-4)",
    "Semi- (24)": "Semi- (2-4)",
    "Netural Good": "Neutral good",
}

# Casos pontuais (id -> índice da variante -> {campo: valor}), conferidos com o texto da página.
MANUAL = {
    "tarrasque": {0: {"xp": "107,000"}},
    # Ecologia em ordem trocada com valores ambíguos ("Any", "Nil", "Special").
    "mineral_mephit": {0: {"activityCycle": "Any", "diet": "Nil", "intelligence": "Average (8-10)", "treasure": "N", "alignment": "Neutral"}},
    "lightning_mephit": {0: {"activityCycle": "Any", "diet": "Special", "intelligence": "Average (8-10)", "treasure": "Nil", "alignment": "Neutral"}},
    "magman": {0: {"activityCycle": "Any", "diet": "Elemental", "intelligence": "Low", "treasure": "Nil", "alignment": "Chaotic neutral"}},
    "thomil": {0: {"activityCycle": "Any", "diet": "Mineral", "intelligence": "Average (10)", "treasure": "Nil (Q×4,X)", "alignment": "Chaotic neutral"}},
    # "Very rare" partido em dois campos; o ciclo de atividade se perdeu na fonte.
    "hydden": {0: {"frequency": "Very rare", "organization": "Tribal", "activityCycle": None, "intelligence": "Average (8-10)"}},
}


def ecology_kind(value):
    """Que campo de ecologia este valor parece ser (pelo vocabulário); None se não dá para dizer."""
    s = (value or "").strip().lower()
    if not s:
        return None
    if re.match(r"^(very\s+)?(common|uncommon|rare|unique)\b", s):
        return "frequency"
    if re.search(r"\b(semi|low|average|very|high|highly|exceptional|genius|supra|animal|non)\b.*\(\d", s) or re.match(
        r"^(non-?|animal|semi-?|low|average|very|high|exceptional|genius|supra-?genius)\s*(\(|$)", s
    ):
        return "intelligence"
    if re.match(r"^(lawful|chaotic|neutral|true neutral)\b", s):
        return "alignment"
    if re.match(r"^(carnivore|omnivore|herbivore|carnivorous|omnivorous|herbivorous|scavenger)\b", s):
        return "diet"
    if re.match(r"^(day|night|nocturnal|diurnal|dusk|dawn|twilight|crepuscular)\b", s):
        return "activityCycle"
    if re.match(r"^(solitary|tribal|tribe|band|group|clan|pack|colony|flock|herd|family|swarm|school|pair|hive|community|gang|pride|troop)\b", s):
        return "organization"
    if re.search(r"\b[a-z]\b", s) and re.fullmatch(
        r"(nil\s*)?\(?[a-z](\s*[,×x]\s*\d*\s*[a-z]?)*\)?(\s*\(.*\))?|nil \([a-z,×\d]+\)|[a-z](,[a-z])*(;.*)?|.*individuals?.*[a-z],[a-z].*", s
    ):
        return "treasure"
    return None


def fix_ecology(eco):
    """Devolve cada valor ao campo certo quando 2+ estão no lugar errado. (novo, mudou?)"""
    misplaced = [f for f in ECOLOGY_ORDER if ecology_kind(eco.get(f)) not in (None, f)]
    if len(misplaced) < 2:
        return eco, False
    new, loose = {}, []
    for pos, f in enumerate(ECOLOGY_ORDER):
        value = eco.get(f)
        if not value:
            continue
        k = ecology_kind(value)
        if k and k not in new:
            new[k] = value
        else:
            loose.append((pos, value))
    # Sem tipo (terreno, "Any", "See below"): o campo de origem, ou o vizinho de antes
    # (a wiki escorregou uma posição), ou o primeiro livre.
    for pos, value in loose:
        for f in [ECOLOGY_ORDER[pos], ECOLOGY_ORDER[max(pos - 1, 0)], ECOLOGY_ORDER[min(pos + 1, 7)], *ECOLOGY_ORDER]:
            if f not in new:
                new[f] = value
                break
    return {f: new[f] for f in ECOLOGY_ORDER if f in new}, True


FIXES = []
NUMERIC = {"armorClass", "thac0", "xp"}


def creature_blocks(raw):
    """Os blocos {{Creature ...}} da página, respeitando chaves aninhadas."""
    blocks, start = [], 0
    while True:
        i = raw.find("{{Creature", start)
        if i < 0:
            return blocks
        depth, j = 0, i
        while j < len(raw):
            if raw.startswith("{{", j):
                depth += 1
                j += 2
            elif raw.startswith("}}", j):
                depth -= 1
                j += 2
                if depth == 0:
                    break
            else:
                j += 1
        blocks.append(raw[i + len("{{Creature") : j - 2])
        start = j


def split_params(body):
    """Divide nos '|' de primeiro nível (fora de [[...]] e {{...}})."""
    parts, buf, depth = [], [], 0
    i = 0
    while i < len(body):
        two = body[i : i + 2]
        if two in ("[[", "{{"):
            depth += 1
            buf.append(two)
            i += 2
            continue
        if two in ("]]", "}}"):
            depth -= 1
            buf.append(two)
            i += 2
            continue
        if body[i] == "|" and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(body[i])
        i += 1
    parts.append("".join(buf))
    return parts[1:] if parts and not parts[0].strip() else parts


def clean(text):
    t = text
    t = re.sub(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>", "", t, flags=re.S)
    t = re.sub(r"\{\{\s*br\s*\}\}|<br\s*/?>", "\n", t, flags=re.I)
    t = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", t)
    t = re.sub(r"\{\{[^{}]*\}\}", "", t)
    t = re.sub(r"'{2,}", "", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = html.unescape(t).replace("\u00a0", " ")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in t.split("\n")]
    return "\n".join(line for line in lines if line).strip()


def parse_block(body):
    """Colunas do infobox: {n: {chave: valor}}; chave sem número vale para todas."""
    shared, columns, unknown = {}, collections.defaultdict(dict), collections.Counter()
    for part in split_params(body):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        key = key.strip().lower()
        m = re.fullmatch(r"(thac0|thaco|[a-z_]+?)(\d*)", key)
        if not m:
            continue
        base, n = m.group(1), m.group(2)
        if base in IGNORED or base.startswith("caption") or base.startswith("image"):
            continue
        if base not in FIELDS:
            unknown[base] += 1
            continue
        value = clean(value)
        if n:
            columns[int(n)][base] = value
        else:
            shared[base] = value
    if not columns:
        columns[1] = {}
    # Coluna "solta" com poucos campos é erro de digitação da wiki ("treasure12"
    # no Xorn, por "treasure2"): vai para a coluna do último dígito.
    real = {n for n, c in columns.items() if len(c) >= 3}
    for n in [n for n in columns if n not in real and real]:
        target = n % 10
        if target in real:
            for k, v in columns.pop(n).items():
                columns[target].setdefault(k, v)
    return [{**shared, **columns[n]} for n in sorted(columns)], unknown


# Número no começo seguido de ressalva: "15" + linha dos líderes, "6 (10)", "-3 (base)".
LEADING = re.compile(r"(-?\d{1,3}(?:,\d{3})+|-?\d+)(?=\s*\n|\s+\()")


def number(field, text):
    """Valor de CA, THAC0 ou XP: o número inteiro, ou o primeiro antes de uma ressalva."""
    if not text:
        return None
    if re.fullmatch(r"-?\d{1,3}(,\d{3})+|-?\d+", text):
        raw = text
    else:
        m = LEADING.match(text)
        if not m:
            return None
        raw = m.group(1)
    if "," in raw and field != "xp":
        return None
    value = int(raw.replace(",", ""))
    # THAC0 e CA fora da escala de AD&D (o "27" do Unicow) é erro da fonte: só o texto.
    if field == "thac0" and not -10 <= value <= 21 or field == "armorClass" and not -12 <= value <= 10:
        return None
    return value


def hit_dice_value(text):
    """Dados de vida inteiros para ordenar: "6+6" -> 6, "10" -> 10, "15 (base)" -> 15, "1/2" -> 0."""
    if not text:
        return None
    m = re.fullmatch(r"(\d+)\s*([+-]\s*\d+)?", text) or re.match(r"(\d+)\s*([+-]\s*\d+)?(?=\s*\n|\s+\()", text)
    if m:
        return int(m.group(1))
    return 0 if re.fullmatch(r"1/2|½|1-\d hp|\d hp", text) else None


STAT_ORDER = ECOLOGY_ORDER + [
    "numberAppearing", "armorClass", "movement", "hitDice", "thac0", "attacks", "damage",
    "specialAttacks", "specialDefenses", "magicResistance", "size", "morale", "xp",
]


def shift_back(flat):
    """Infobox sem o terreno com tudo escorregado uma posição (a frequência no
    terreno... a moral no XP): cada valor volta uma casa; o XP se perdeu na fonte."""
    if flat.get("climateTerrain") or ecology_kind(flat.get("organization")) != "frequency":
        return flat, False
    out = {k: v for k, v in flat.items() if k not in STAT_ORDER}
    for i, field in enumerate(STAT_ORDER[:-1]):
        value = flat.get(STAT_ORDER[i + 1])
        if value:
            out[field] = value
    return out, True


def variant(col, page_name, single, mid=None, index=0):
    col = {k: TYPOS.get(v, v) for k, v in col.items()}
    name = col.get("name") or page_name if not single else page_name
    # Campo do infobox -> campo de saída, num dicionário só (texto).
    flat, extra = {}, {}
    for key, value in col.items():
        group, field = FIELDS[key]
        if group == "meta":
            continue
        if group == "extra":
            extra[field] = value
        else:
            flat[field] = value
    flat, shifted = shift_back(flat)
    if shifted:
        FIXES.append((mid, name, "infobox inteiro deslocado uma posição (XP perdido na fonte)", None))
    eco = {f: flat[f] for f in ECOLOGY_ORDER if flat.get(f)}
    fixed, changed = fix_ecology(eco)
    if changed:
        FIXES.append((mid, name, eco, fixed))
    flat = {**{k: v for k, v in flat.items() if k not in ECOLOGY_ORDER}, **fixed}
    flat.update(MANUAL.get(mid, {}).get(index, {}))
    flat = {k: v for k, v in flat.items() if v}

    out = {"name": name, "source": col.get("source") or None, "ecology": {}, "combat": {}}
    if col.get("note"):
        out["note"] = col["note"]
    if extra:
        out["extra"] = extra
    for field in STAT_ORDER:
        value = flat.get(field)
        if not value:
            continue
        group = "ecology" if field in ECOLOGY_ORDER else "combat"
        if field in NUMERIC:
            out[group][field] = {"text": value, "value": number(field, value)}
        elif field == "hitDice":
            out[group][field] = {"text": value, "value": hit_dice_value(value)}
        else:
            out[group][field] = value
    return out


def convert(m):
    raw = (m.get("description") or {}).get("rawWikitext") or ""
    blocks = creature_blocks(raw)
    if not blocks:
        return None, collections.Counter()
    unknown = collections.Counter()
    cols = []
    for b in blocks:
        c, u = parse_block(b)
        cols.extend(c)
        unknown += u
    single = len(cols) == 1
    variants = [variant(c, m["name"], single, m["id"], i) for i, c in enumerate(cols)]
    d = m.get("description") or {}
    sections = {k: v for k, v in (d.get("sections") or {}).items() if v}
    return {
        "id": m["id"],
        "name": m["name"],
        "aliases": m.get("redirectAliases") or [],
        "collection": m.get("sourceCategory"),
        "sources": m.get("sources") or [],
        "variants": variants,
        "description": {"summary": d.get("briefSummary") or None, "sections": sections, "fullText": d.get("fullText") or None},
        "categories": m.get("categories") or [],
    }, unknown


def index_entry(mon):
    v0 = mon["variants"][0]
    xs = [v["combat"].get("xp", {}).get("value") for v in mon["variants"]]
    xs = [x for x in xs if x is not None]
    hds = [v["combat"].get("hitDice", {}).get("value") for v in mon["variants"]]
    hds = [h for h in hds if h is not None]
    return {
        "id": mon["id"],
        "name": mon["name"],
        "collection": mon["collection"],
        "variants": len(mon["variants"]),
        "climateTerrain": v0["ecology"].get("climateTerrain"),
        "frequency": v0["ecology"].get("frequency"),
        "hitDice": v0["combat"].get("hitDice", {}).get("text"),
        "hitDiceMin": min(hds) if hds else None,
        "hitDiceMax": max(hds) if hds else None,
        "xpMin": min(xs) if xs else None,
        "xpMax": max(xs) if xs else None,
        "summary": mon["description"]["summary"],
    }


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--mining", default=DEFAULT_MINING)
    args = ap.parse_args()
    monsters, skipped, unknown = [], [], collections.Counter()
    for f in sorted(glob.glob(os.path.join(args.mining, "*.json"))):
        if os.path.basename(f) == "index.json":
            continue
        for m in json.load(open(f, encoding="utf-8")):
            mon, u = convert(m)
            unknown += u
            if mon is None:
                skipped.append(m["id"])
            else:
                monsters.append(mon)
    os.makedirs(args.out, exist_ok=True)
    by_collection = collections.defaultdict(list)
    for mon in monsters:
        by_collection[mon["collection"]].append(mon)
    for coll, items in by_collection.items():
        items.sort(key=lambda x: x["name"].lower())
        with open(os.path.join(args.out, f"monsters_{slug(coll)}.json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(items, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
    index = sorted((index_entry(m) | {"file": f"monsters_{slug(m['collection'])}.json"} for m in monsters), key=lambda x: x["name"].lower())
    with open(os.path.join(args.out, "monsters_index.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(index, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    nvar = sum(len(m["variants"]) for m in monsters)
    print(f"monstros: {len(monsters)} (variantes: {nvar}); fora (sem {{{{Creature}}}}): {len(skipped)}")
    print("chaves desconhecidas no infobox:", unknown.most_common(15))
    print(f"correções de campos em {len(FIXES)} casos:")
    for mid, name, before, after in FIXES:
        print(f"  {mid} | {name}")
        if after is None:
            print("     ", before)
        else:
            print("     antes: ", json.dumps(before, ensure_ascii=False))
            print("     depois:", json.dumps(after, ensure_ascii=False))


if __name__ == "__main__":
    main()
