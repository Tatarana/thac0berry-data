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
    "Varics": "Varies",
    "Neutal": "Neutral",
    "Vanes": "Varies",
    "M (6' ta1l)": "M (6' tall)",
}

# Erros de digitação dentro de frases (palavra -> correta), achados comparando com o histórico.
WORD_TYPOS = {
    "Strenght": "Strength", "strenght": "strength", "wepaon": "weapon", "wepaons": "weapons", "Chotic": "Chaotic",
    "Termperate": "Temperate", "Amy remote": "Any remote", "Strangth": "Strength", "drowing": "drowning",
    "Regneration": "Regeneration", "Invisibilty": "Invisibility", "electricty": "electricity", "eath-based": "earth-based",
    "hitt": "hit", "Championj": "Champion", "crasing": "erasing", "additonal": "additional", "ot better": "or better",
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
    # Deslocado a partir da frequência (que se perdeu na fonte).
    "the_abomination_of_diirinka": {0: {"frequency": None, "organization": "Solitary", "activityCycle": "Any", "diet": "Life energy, minerals", "intelligence": "Not ratable", "treasure": "Nil"}},
    "phaerimm": {0: {"treasure": "All possible (G is most common in lair)", "alignment": "Neutral evil"}},
    # Deslocado duas posições a partir da inteligência; o texto confirma 1 ataque
    # de língua de 1d8 e o ácido. Inteligência, alinhamento, moral e XP se perderam.
    "archer_frog": {0: {
        "intelligence": None, "treasure": "Incidental", "alignment": None, "numberAppearing": "1-6",
        "armorClass": "7", "movement": "6, Sw 12", "hitDice": "3", "thac0": "16", "attacks": "1",
        "damage": "1d8", "specialAttacks": "Acid", "specialDefenses": "Nil", "magicResistance": "Nil",
        "size": "M (6' long)", "morale": None, "xp": None,
    }},
    "behemoth": {3: {"name": "Behemoth (Legends & Lore)"}},
    # --- Recuperados do histórico da wiki (dumps/adnd2e_pages_full.xml.7z): a última
    # versão da página com a tabela de estatísticas ROTULADA ("! XP Value:"), antes da
    # conversão para o infobox, que deslocou os campos e perdeu o XP. Conferido campo a
    # campo (2026-10-07); só entra o que a tabela rotulada tem de coerente.
    "cat_winged": {0: {"xp": "975"}, 1: {"xp": "175"}},
    "child_of_the_sea": {0: {"xp": "120"}, 1: {"xp": "650"}},
    "coral": {0: {"xp": "175"}, 1: {"xp": "270 to 2,000"}},
    "giant_clam": {0: {"xp": "175"}, 1: {"xp": "650"}},
    "giant_turtle": {0: {"xp": "5,000"}, 1: {"xp": "3,000"}},
    "gemstone_golem": {0: {"xp": "5,000"}, 1: {"xp": "8,000"}, 2: {"xp": "10,000"}},
    "octo_jelly": {0: {"xp": "2,000"}, 1: {"xp": "4,000"}},
    "sea_demon": {0: {"xp": "9,000"}, 1: {"xp": "15,000"}},
    "shadowrath": {0: {"xp": "1,400"}, 1: {"xp": "2,000"}},
    "lizard_man_athas": {0: {"xp": "65\nPatrol leader: 65\nSubleader: 120\nWar leader: 270"}, 1: {"xp": "975"}},
    "time_dimensional": {0: {"xp": "4,000 or 8,000"}, 1: {"xp": "12,000"}, 2: {"xp": "16,000 or 20,000"}},
    "dragon_kin": {0: {"magicResistance": "Nil"}, 1: {"magicResistance": "Nil"}},
    "dragon_lesser_undead": {0: {"magicResistance": "Same as living"}, 1: {"magicResistance": "Same as living"}},
    "neogi": {0: {"thac0": "15"}},
    "gorse": {0: {"thac0": "20"}},
    "watcher": {0: {"morale": "Average (10)"}},
    "drik": {0: {"morale": "Elite (13-14)"}, 1: {"morale": "Champion (15-16)"}},
    "ruvoka": {0: {"morale": "Champion (15-16)"}, 1: {"morale": "Champion (15-16)"}},
    "tari": {1: {"morale": "Champion (15-16)"}},
    "mimic": {0: {"xp": "7 HD: 975\n8 HD: 1,400"}},
    "spinagon": {0: {"movement": "6, Fl 18 (C)"}},
    "mold_man": {0: {"size": "S-M (2-4½')"}},
    "yuan_ti": {0: {"morale": "Elite (14)\nAbominations: Champion (15)"}},
    "heucuva": {0: {"morale": "Steady (11)"}},
    "foo_creature": {1: {"treasure": "Nil"}},
    # O infobox atual do Haunt está deslocado a partir do HD; a tabela rotulada não.
    "haunt": {0: {"hitDice": "5/victim's hp", "thac0": "15", "attacks": "1/1, as 5-HD monster", "damage": "See below/by weapon",
                  "specialDefenses": "See below", "magicResistance": "Nil", "size": "Variable", "morale": "Champion (16)", "xp": "2,000"}},
    # O tamanho foi parar no XP, e número/CA estão trocados (planta: CA 0, aparece 1-2).
    "giant_bladderwort": {0: {"numberAppearing": "1-2", "armorClass": "0", "size": "L to G", "xp": None}},
    # Dragon Magazine: falta um campo no meio (o THAC0, nos três primeiros) e o resto
    # escorrega para a frente; sobra um número solto no fim ("-11", "-13", "-19%").
    # Valor ambíguo fica vazio. CA e movimento trocados no Gulper e no Angler Fish.
    "craighe": {0: {"thac0": None, "attacks": "3", "damage": "1-2/1-2/1", "specialAttacks": "Dive", "specialDefenses": "Nil", "magicResistance": "Nil", "size": "S (up to 4' wingspan)"}},
    "gulper": {0: {"armorClass": "9", "movement": "Sw 15", "thac0": None, "attacks": "1", "damage": "2d8", "specialAttacks": "Constriction, swallow whole", "specialDefenses": "Nil", "magicResistance": "Nil", "size": "L (12' long)"}},
    "angler_fish": {0: {"armorClass": "8", "movement": "Sw 12", "thac0": None, "attacks": "1", "damage": "2d8 or (some species only) 1d4", "specialAttacks": "Swallow whole", "specialDefenses": "Nil", "magicResistance": "Nil", "size": None, "xp": None}},
    "plague_moth": {0: {"magicResistance": None, "size": "T (1' wingspan)"}},
    "zurchin": {0: {"specialDefenses": None, "size": "T (6\u201d to 1' diameter)", "xp": "120"}},
    # Deslocado para trás a partir da CA (a CA tem o movimento, o movimento tem o HD...).
    # As aranhas conferem com a tabela do DMG: HD 8+8 -> THAC0 11; HD 4+4 -> THAC0 15.
    "spider": {
        0: {"numberAppearing": None, "armorClass": "4", "movement": "9, Wb 12", "hitDice": "8+8", "thac0": "11", "attacks": "1",
            "damage": "2-12", "specialAttacks": "Webs, poison", "specialDefenses": "Jumps", "magicResistance": "Nil"},
        1: {"numberAppearing": None, "armorClass": "4", "movement": "3, Wb 12", "hitDice": "4+4", "thac0": "15", "attacks": "1",
            "damage": "2-8", "specialAttacks": "Webs, poison", "specialDefenses": "Nil", "magicResistance": "Nil"},
    },
    "insect_swarm_athas": {0: {"armorClass": None, "movement": "Fl 18 (A)", "hitDice": "1 per 10 insects", "thac0": "Special",
                               "attacks": "See below", "damage": "See below", "specialAttacks": "See below", "specialDefenses": "Nil", "magicResistance": "Nil"}},
    # Cauda deslocada a partir da resistência a magia; o XP se perdeu na fonte.
    "phthisic": {0: {
        "specialDefenses": "+2 or better weapons to hit, reflects spells, regenerates; Confusion and feeblemind",
        "magicResistance": "Nil", "size": "L (9' tall)", "morale": "Elite (14)", "xp": None,
    }},
}

# Valor numérico que a fonte erra (o texto fica). Vazio: o Neogi foi resolvido pelo histórico.
NO_VALUE = set()

# Lixo de OCR no texto da descrição (sequência exata -> correta).
TEXT_TYPOS = {
    "area &an; do": "area as do",
    "saving &row; vs.": "saving throw vs.",
    "like a <cloak of bravery": "like a cloak of bravery",
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
    # Frações da wiki ({{frac|1|2}} = ½; {{frac|2|1|2}} = 2 1/2): antes eram apagadas
    # junto com os outros modelos, e o "HD ½" do Brownie sumia.
    t = re.sub(r"\{\{\s*frac\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|?\s*\}\}", r"\1 \2/\3", t, flags=re.I)
    t = re.sub(r"\{\{\s*frac\s*\|\s*1\s*\|\s*2\s*\|?\s*\}\}", "½", t, flags=re.I)
    t = re.sub(r"\{\{\s*frac\s*\|\s*1\s*\|\s*4\s*\|?\s*\}\}", "¼", t, flags=re.I)
    t = re.sub(r"\{\{\s*frac\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|?\s*\}\}", r"\1/\2", t, flags=re.I)
    t = t.replace("1⁄2", "½")
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


MORALE = r"(unreliable|unsteady|average|steady|very steady|elite|champion|fanatic|fearless)\b"
SIZE = r"[TSMLHG]\s*\("

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
    # Se a moral e o XP originais já são moral e XP, o deslocamento acabou antes
    # (Dragon-kin, Lesser Undead Dragon): tamanho, moral e XP ficam; a resistência
    # a magia, que receberia o tamanho, se perdeu na fonte.
    tail_ok = bool(re.match(MORALE, flat.get("morale") or "", re.I)) and bool(re.match(r"[\d,]+|varies|variable", flat.get("xp") or "", re.I))
    last = STAT_ORDER.index("magicResistance") if tail_ok else len(STAT_ORDER) - 1
    for i, field in enumerate(STAT_ORDER[:last]):
        value = flat.get(STAT_ORDER[i + 1])
        if value:
            out[field] = value
    if tail_ok:
        for field in ("size", "morale", "xp"):
            if flat.get(field):
                out[field] = flat[field]
    return out, True


def variant(col, page_name, single, mid=None, index=0):
    col = {k: TYPOS.get(v, v) for k, v in col.items()}
    for bad, good in WORD_TYPOS.items():
        col = {k: re.sub(rf"\b{re.escape(bad)}\b", good, v) for k, v in col.items()}
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
    if re.match(MORALE, flat.get("size") or "", re.I) and re.match(SIZE, flat.get("morale") or ""):
        FIXES.append((mid, name, "tamanho e moral trocados", None))
        flat["size"], flat["morale"] = flat["morale"], flat["size"]
    elif re.match(SIZE, flat.get("morale") or "") and not re.match(SIZE, flat.get("size") or ""):
        # Tamanho na moral e um valor perdido no tamanho (Laerti "-15"): a moral se perdeu.
        FIXES.append((mid, name, f"tamanho estava na moral (tamanho na fonte: {flat.get('size')!r})", None))
        flat["size"], flat["morale"] = flat["morale"], None
    if flat.get("movement"):
        flat["movement"] = re.sub(r"\bCI\b", "Cl", re.sub(r"\bFI\b", "Fl", flat["movement"]))
    manual = dict(MANUAL.get(mid, {}).get(index, {}))
    name = manual.pop("name", name)
    flat.update(manual)
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
            out[group][field] = {"text": value, "value": None if (mid, index, field) in NO_VALUE else number(field, value)}
        elif field == "hitDice":
            out[group][field] = {"text": value, "value": hit_dice_value(value)}
        else:
            out[group][field] = value
    # THAC0 "0" de quem não ataca (0 ataques): "não ataca", não o melhor THAC0 do jogo.
    t0 = out["combat"].get("thac0")
    if t0 and t0["text"] == "0" and (flat.get("attacks") or "").strip().lower() in ("0", "nil", "none"):
        t0["value"] = None
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
    sections = {k: clean_text(v) for k, v in (d.get("sections") or {}).items() if v and clean_text(v)}
    full = clean_text(d.get("fullText") or "") or None
    summary = clean_text(d.get("briefSummary") or "") or None
    # Resumo que é só referência ("From Dragon Magazine #261", "See Grell..."): o 1º parágrafo.
    if not summary or re.match(r"Player's Option|From |See ", summary) or len(summary) < 40:
        summary = first_paragraph(full) or summary
    return {
        "id": m["id"],
        "name": m["name"],
        "aliases": m.get("redirectAliases") or [],
        "collection": m.get("sourceCategory"),
        "sources": m.get("sources") or [],
        "variants": variants,
        "description": {"summary": summary, "sections": sections, "fullText": full},
        "categories": m.get("categories") or [],
    }, unknown


def clean_text(text):
    """Texto da descrição: entidades HTML, tags, sobras do <tabber> ("Drik=", "|-|") e a
    linha "=" que sobra de subtítulos "=== Combat===" no começo das seções."""
    t = text or ""
    for bad, good in TEXT_TYPOS.items():
        t = t.replace(bad, good)
    t = html.unescape(t)
    t = re.sub(r"<[^>]+>", "", t)
    t = "\n".join(line for line in t.split("\n") if not re.fullmatch(r"\s*\|-\|\s*|[^\n=]{1,80}=\s*|\s*=+\s*", line))
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def first_paragraph(full):
    """Resumo quando a fonte não tem: o 1º parágrafo de texto (sem título nem a linha psiônica), até 2 frases."""
    for para in (full or "").split("\n\n"):
        p = para.strip()
        # Pula título, a linha psiônica, referência ("From Dragon...", "See Grell...") e rótulo curto.
        if not p or p.startswith(("#", "Player's Option", "|", "From ", "See ")) or p.endswith(":") or len(p) < 60:
            continue
        sentences = re.split(r"(?<=[.!?])\s+", p)
        return " ".join(sentences[:2])[:400]
    return None


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
