#!/usr/bin/env python3
"""Gera data/races.json (e docs/racas-divergencias-2026-11.md) a partir da mineração.

Por quê (2026-11-20, "Raças em dados" da web): as raças do app web viviam fixas em
`raceKit.ts` (17: PHB, planares, Half-Vistani). Agora vêm daqui, junto com as ~140
raças mineradas dos livros.

Fontes:
- `../thac0berry-data-mining/data/player_races/*.json` (157 registros em 7 arquivos);
- `scripts/race_curation.json` (curadoria, feita à mão):
  * `legacy`: as 17 raças que o app já tinha, com os valores do app (PHB Tabela 7,
    Planewalker's Handbook, Domains of Dread). SÃO A VERDADE: onde a mineração discorda,
    o valor do app fica e a diferença vai para o relatório de divergências;
  * `races`: para cada registro minerado que não é uma das 17, o cenário
    (`campaignSetting`), se é jogável, a raça-base (subraça), o nome gravado na ficha etc.
    Registro minerado sem entrada na curadoria faz o script parar.

O que o script faz com cada registro minerado:
- ids: o id minerado, exceto as 17 (ids estáveis da curadoria: bariaur_male, genasi_fire…);
- limites de nível e combinações: nomes de classe normalizados ("Wizard"/"mage" = Mage,
  "fighter" = Fighter; "Unlimited"/"U" = "unlimited"). Classe que o app não tem
  (Defiler, Gladiator, Preserver…) fica no JSON; o app é que as ignora;
- `baseMovement`: o primeiro número de `speed` ("6, Fl 36 (C)" = 6); sem número = ausente;
- subraça com a seção "Standard <Raça> Abilities" no texto herda da raça-base o que o app
  usa como regra (bônus de CON nos testes, resistência a sono/charme, bônus de combate,
  perícia grátis, demi-bardo). `inheritsFromBase` marca; o app NÃO resolve herança em
  tempo de execução (só `baseRace` para kits, imagem e "é humano?");
- `racialAbilities` (texto da ficha) das jogáveis novas: visão, bônus/resistência e os
  blocos "Special Advantages/Disadvantages" do texto do livro; nenhum número inventado;
- campos de texto minerados ficam como vieram (`content` é markdown).

Uso:  python scripts/build_races.py [--dry-run] [--mining DIR]
"""
import glob
import json
import os
import re
import sys
from collections import OrderedDict

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "data", "races.json")
DOC = os.path.join(ROOT, "docs", "racas-divergencias-2026-11.md")
CURATION = os.path.join(ROOT, "scripts", "race_curation.json")
MINING = os.path.join(ROOT, "..", "thac0berry-data-mining", "data", "player_races")

# As 12 classes do app (web: canonicalClasses). Só elas entram nas regras.
APP_CLASSES = ["Fighter", "Paladin", "Ranger", "Mage", "Cleric", "Druid", "Thief", "Bard", "Ninja", "Psionicist", "Anchorite", "Gypsy"]
# Classes que só aparecem em combinações (o app trata Illusionist como Mage da escola Illusion).
COMBO_CLASSES = APP_CLASSES + ["Illusionist"]

CLASS_ALIASES = {
    "fighter": "Fighter", "figther": "Fighter", "paladin": "Paladin", "ranger": "Ranger",
    "mage": "Mage", "wizard": "Mage", "mage or wizard": "Mage",
    "cleric": "Cleric", "druid": "Druid", "thief": "Thief", "bard": "Bard", "ninja": "Ninja",
    "psionicist": "Psionicist", "psioncist": "Psionicist", "illusionist": "Illusionist",
    "priest": "Priest", "any": "*",
}
PLURALS = {"mages": "mage", "thieves": "thief", "fighters": "fighter", "clerics": "cleric", "rangers": "ranger", "druids": "druid", "bards": "bard", "wizards": "wizard"}
UNLIMITED = {"unlimited", "u", "unlim", "none", "no max lvl", "no max level"}
BASE_ORDER = ["human", "elf", "dwarf", "gnome", "half_elf", "halfling"]
STD_RE = re.compile(r"## Standard (Elf|Dwarf|Gnome|Halfling) Abilities")
BASE_OF_WORD = {"Elf": "elf", "Dwarf": "dwarf", "Gnome": "gnome", "Halfling": "halfling"}
INHERIT_FIELDS = ["constitutionSaveBonus", "spellResistance", "combatModifiers", "bonusProficiencies", "demiBardKits", "bardCombos"]


def norm_class(raw):
    s = str(raw).strip()
    if ":" in s:
        s = s.split(":")[-1].strip()
    s = re.sub(r"\s*\(.*?\)\s*", " ", s).strip()
    return CLASS_ALIASES.get(s.lower(), s[:1].upper() + s[1:])


def norm_limit(value):
    if isinstance(value, int):
        return value
    text = str(value).strip().lower()
    if text in UNLIMITED:
        return "unlimited"
    m = re.match(r"^(\d+)\b", text)
    return int(m.group(1)) if m else None


def norm_limits(rows):
    """[{class, levelLimit}] normalizado; devolve (lista, qualquer_classe_ilimitada)."""
    out, any_unlimited = [], False
    for row in rows or []:
        cls = norm_class(row["class"])
        limit = norm_limit(row["levelLimit"])
        if limit is None:
            continue
        if cls == "*":
            any_unlimited = any_unlimited or limit == "unlimited"
            continue
        out.append({"class": cls, "levelLimit": limit})
    return out, any_unlimited


def norm_combos(rows):
    out = []
    for text in rows or []:
        tokens = [t.strip() for t in re.sub(r"^and\s+", "", str(text).strip(), flags=re.I).rstrip(".").split("/")]
        combo = []
        for t in tokens:
            t = PLURALS.get(t.lower(), t.lower())
            cls = CLASS_ALIASES.get(t)
            if not cls or cls == "*":
                combo = None
                break
            combo.append(cls)
        if combo and len(combo) > 1 and combo not in out:
            out.append(combo)
    return out


def first_int(text):
    m = re.match(r"^\s*(\d+)\b", str(text or ""))
    return int(m.group(1)) if m else None


STOP = re.compile(r"\n## |\n\*\*(Racial Adjustment|Table|[A-Za-z ]*Racial Adjustment)|\nMulticlass Notes|\n\*\*[A-Za-z ]*Class Level", re.I)


def specials(content):
    """Os blocos 'Special Advantages/Disadvantages' do texto do livro, sem markdown de negrito."""
    if not content:
        return ""
    m = re.search(r"(Special (Advantages|Features|Abilities|Traits)|RACIAL ABILITIES|Racial Abilities)", content)
    if not m:
        return ""
    text = content[m.start():]
    stop = STOP.search(text)
    if stop:
        text = text[: stop.start()]
    text = text.replace("**", "")
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def compose_abilities(rec, base_text):
    parts = []
    if rec.get("vision"):
        parts.append(f"Vision: {rec['vision'].strip()}")
    if rec.get("attackBonus"):
        parts.append(f"Attack bonus: {rec['attackBonus'].strip()}")
    if rec.get("resistance"):
        parts.append(f"Resistance: {rec['resistance'].strip()}")
    body = specials(rec.get("content"))
    if body:
        parts.append(body)
    text = "\n".join(parts)
    if base_text:
        text += f"\n\nThe standard abilities of the base race apply unless stated above:\n{base_text}"
    return text.strip() or None


def load_mined(mining):
    by = OrderedDict()
    for f in sorted(glob.glob(os.path.join(mining, "*.json"))):
        if f.endswith("index.json"):
            continue
        for r in json.load(open(f, encoding="utf-8")):
            r["_file"] = os.path.basename(f)
            if r["id"] in by:
                sys.exit(f"id minerado repetido: {r['id']}")
            by[r["id"]] = r
    return by


TEXT_FIELDS = ["size", "speed", "hitPoints", "armorClass", "languages", "vision", "height", "weight", "attackBonus", "resistance", "alignment", "briefSummary"]
MINED_TEXTS = ["abilityScoreRequirementsText", "abilityScoreAdjustmentsText", "classLevelLimitsText", "classCombinationsText"]


def group_of(rec):
    if rec.get("hiddenReason") == "humanoid-not-playable":
        return "Complete Book of Humanoids"
    setting = rec.get("campaignSetting")
    if setting:
        return setting
    if rec.get("hiddenReason") == "undecided":
        return "Other"
    return "Subraces" if rec.get("baseRace") else "Player's Handbook"


def build(mined, cur):
    records, legacy_ids = [], {}
    # 1) as 17 do app
    for e in cur["legacy"]:
        m = mined.get(e["minedId"]) if e.get("minedId") else None
        r = OrderedDict()
        r["id"] = e["id"]
        r["name"] = e["name"]
        for key in ("label", "gender", "aliases"):
            if key in e:
                r[key] = e[key]
        r["playable"] = True
        r["campaignSetting"] = e["campaignSetting"]
        r["group"] = None
        r["source"] = {"label": e["sourceLabel"], "book": m["sourceBook"] if m else None, "page": m["sourcePage"] if m else None, "category": m["sourceCategory"] if m else None, "minedId": e.get("minedId")}
        for key in TEXT_FIELDS:
            if m and m.get(key) is not None:
                r[key] = m[key]
        for key in ("abilityScoreRequirements", "abilityScoreAdjustments", "noLevelLimit", "classLevelLimits", "classCombinations", "bardCombos", "demiBardKits",
                    "baseMovement", "spellResistance", "racialAbilities", "combatModifiers", "constitutionSaveBonus", "singleClassBonus", "bonusProficiencies", "kitForms", "ruleId"):
            if key in e:
                r[key] = e[key]
        if m and m.get("content"):
            r["content"] = m["content"]
        records.append(r)
        legacy_ids[e["id"]] = r
    # 2) o resto
    legacy_mined = {e["minedId"] for e in cur["legacy"] if e.get("minedId")}
    for mid, m in mined.items():
        if mid in legacy_mined:
            continue
        c = cur["races"].get(mid)
        if c is None:
            sys.exit(f"raça minerada sem curadoria: {mid}")
        r = OrderedDict()
        r["id"] = mid
        r["name"] = c.get("name", m["name"])
        if c.get("name") and c["name"] != m["name"]:
            r["aliases"] = [m["name"]]
        r["playable"] = c["playable"]
        if c.get("hiddenReason"):
            r["hiddenReason"] = c["hiddenReason"]
        if c.get("duplicateOf"):
            r["duplicateOf"] = c["duplicateOf"]
        r["campaignSetting"] = c["campaignSetting"]
        if c.get("baseRace"):
            r["baseRace"] = c["baseRace"]
        label = m["sourceBook"].split(":")[0].strip().strip('"')
        r["source"] = {"label": label, "book": m["sourceBook"], "page": m["sourcePage"], "category": m["sourceCategory"], "minedId": mid}
        for key in TEXT_FIELDS:
            if m.get(key) is not None:
                r[key] = m[key]
        for key in MINED_TEXTS:
            if m.get(key) is not None:
                r[key] = m[key]
        reqs = c["abilityScoreRequirements"] if "abilityScoreRequirements" in c else m["abilityScoreRequirements"]
        if reqs:
            r["abilityScoreRequirements"] = reqs
        if m.get("abilityScoreAdjustments"):
            r["abilityScoreAdjustments"] = [{"ability": a["ability"], "modifier": a["modifier"]} for a in m["abilityScoreAdjustments"]]
        limits, any_unlimited = norm_limits(c.get("classLevelLimits", m["classLevelLimits"]))
        if limits:
            r["classLevelLimits"] = limits
        if c.get("noLevelLimit") or any_unlimited:
            r["noLevelLimit"] = True
        combos = norm_combos(m["classCombinations"])
        if combos:
            r["classCombinations"] = combos
        move = first_int(m.get("speed"))
        if move is not None:
            r["baseMovement"] = move
        if c.get("note"):
            r["note"] = c["note"]
        if m.get("content"):
            r["content"] = m["content"]
        r["_noInherit"] = c.get("noInherit", [])
        records.append(r)
    by_id = {r["id"]: r for r in records}
    # 3) subraças: herança da raça-base, nome de forma do kit, texto da ficha
    for r in records:
        base = by_id.get(r.get("baseRace")) if r.get("baseRace") else None
        if r.get("baseRace") and base is None:
            sys.exit(f"baseRace inexistente: {r['id']} -> {r['baseRace']}")
        no_inherit = r.pop("_noInherit", [])
        std = None
        if base and r["source"]["minedId"] in mined:
            m = STD_RE.search(mined[r["source"]["minedId"]].get("content") or "")
            std = m and BASE_OF_WORD[m.group(1)] == r["baseRace"]
        if std:
            copied = [k for k in INHERIT_FIELDS if k in base and k not in no_inherit]
            for k in copied:
                r[k] = base[k]
            r["inheritsFromBase"] = copied
        if r["id"] not in legacy_ids and r["playable"]:
            r["racialAbilities"] = compose_abilities(r | {"content": mined[r["source"]["minedId"]].get("content")}, base.get("racialAbilities") if std else None)
            if r["racialAbilities"] is None:
                del r["racialAbilities"]
        if not r.get("baseRace") and "kitForms" not in r:
            words = re.findall(r"[a-z]+", re.sub(r"\(.*?\)", "", r["name"].lower()))
            if words:
                r["kitForms"] = [words[-1], words[-1] + "s"]
        r["group"] = group_of(r)
    # ordem: as 17 do app primeiro; depois por grupo, raça-base e nome
    order = {e["id"]: i for i, e in enumerate(cur["legacy"])}
    group_rank = {"Player's Handbook": 0, "Subraces": 1}
    rest = sorted(
        (r for r in records if r["id"] not in order),
        key=lambda r: (group_rank.get(r["group"], 2), r["group"], BASE_ORDER.index(r["baseRace"]) if r.get("baseRace") in BASE_ORDER else 99, r["name"]),
    )
    return [by_id[e["id"]] for e in cur["legacy"]] + rest


# --- divergências entre a mineração e o app (as 17) ------------------------------------

ABILITIES = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]


def fmt_req(req):
    return ", ".join(f"{a} {req[a]['min']}/{req[a]['max']}" for a in ABILITIES) if req else "—"


def fmt_adj(rows):
    d = {}
    for a in rows or []:
        d[a["ability"]] = d.get(a["ability"], 0) + a["modifier"]
    return ", ".join(f"{a} {v:+d}" for a, v in d.items() if v) or "—"


def adj_dict(rows):
    d = {}
    for a in rows or []:
        d[a["ability"]] = d.get(a["ability"], 0) + a["modifier"]
    return {k: v for k, v in d.items() if v}


def split_bariaur(m):
    """A página do Bariaur mistura os dois sexos: ajustes (4 + 4), limites ('MALE:'/'FEMALE:')."""
    adj = m["abilityScoreAdjustments"] or []
    male_adj, female_adj = adj[:4], adj[4:]
    male, female, current = [], [], None
    for row in m["classLevelLimits"] or []:
        name = str(row["class"])
        if name.upper().startswith("MALE:"):
            current = male
        elif name.upper().startswith("FEMALE:"):
            current = female
        if current is not None:
            current.append(row)
    return {"male": (male_adj, male), "female": (female_adj, female)}


def lim_dict(rows):
    d = {}
    for row in rows or []:
        cls = norm_class(row["class"])
        lim = norm_limit(row["levelLimit"])
        if cls in APP_CLASSES and lim is not None:
            d[cls] = lim
    return d


def combo_set(combos):
    return {tuple(sorted(c)) for c in combos if all(x in COMBO_CLASSES for x in c)}


def fmt_lim(d):
    return ", ".join(f"{k} {v}" for k, v in d.items()) or "—"


def fmt_combos(s):
    return ", ".join("/".join(c) for c in sorted(s)) or "—"


def divergences(cur, mined):
    rows = []
    for e in cur["legacy"]:
        mid = e.get("minedId")
        if not mid:
            rows.append((e["name"], "(toda a raça)", "não existe na mineração", "valores do app (Domains of Dread)", e["sourceLabel"]))
            continue
        m = mined[mid]
        name = e["name"]
        src = e["sourceLabel"]
        if mid == "bariaur":
            sex = split_bariaur(m)[e["gender"]]
            mined_adj_rows, mined_lim_rows = sex
            rows.append((name, "ficha da raça", "uma página só para os dois sexos (ajustes e limites misturados; requisitos de um sexo só)", f"uma raça por sexo ({e['gender']})", src))
        else:
            mined_adj_rows, mined_lim_rows = m["abilityScoreAdjustments"], m["classLevelLimits"]
        if m["name"] != name:
            rows.append((name, "nome", m["name"], f"{name} (nome gravado na ficha)", src))
        # requisitos
        mr = m["abilityScoreRequirements"]
        if (mr or None) != (e["abilityScoreRequirements"] or None):
            rows.append((name, "requisitos de atributo", fmt_req(mr), fmt_req(e["abilityScoreRequirements"]), src))
        # ajustes
        if adj_dict(mined_adj_rows) != adj_dict(e["abilityScoreAdjustments"]):
            rows.append((name, "ajustes de atributo", fmt_adj(mined_adj_rows), fmt_adj(e["abilityScoreAdjustments"]), src))
        # limites de nível (só as classes do app)
        ml = lim_dict(mined_lim_rows)
        al = lim_dict(e["classLevelLimits"])
        if e.get("noLevelLimit"):
            al = {"(todas as classes)": "unlimited"}
            ml = ml if ml else {"(todas as classes)": "unlimited"} if (m["classLevelLimitsText"] or "").lower().startswith("all") else ml
        if ml != al:
            extra = [c for c in al if c not in ml]
            note = src + ("; " + ", ".join({"Psionicist": "Psionicist = CPsiH Table 1", "Ninja": "Ninja = CNH", "Gypsy": "Gypsy = Domains of Dread"}[c] for c in extra if c in ("Psionicist", "Ninja", "Gypsy")) if any(c in ("Psionicist", "Ninja", "Gypsy") for c in extra) else "")
            rows.append((name, "limites de nível (classes do app)", fmt_lim(ml), fmt_lim(al), note))
        # combinações
        mc = combo_set(norm_combos(m["classCombinations"]))
        ac = combo_set(e["classCombinations"])
        if mc != ac:
            rows.append((name, "combinações de classe", fmt_combos(mc), fmt_combos(ac), src))
        # movimento
        mm = first_int(m["speed"])
        if mm != e["baseMovement"]:
            rows.append((name, "movimento base", str(m["speed"]), f'{e["baseMovement"]}"', src))
    return rows


# --- relatório -------------------------------------------------------------------------

REASONS = [
    ("humanoid-not-playable", "Humanoides não jogáveis (Complete Book of Humanoids)"),
    ("setting-not-in-forge", "Cenário que não está na lista do Forge"),
    ("undecided", "Para decisão do usuário (sem cenário do Forge claro, ou sem regra utilizável no app)"),
    ("duplicate", "Registros duplicados (o id canônico fica jogável)"),
]


def md_escape(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def write_doc(records, rows, mined):
    playable = [r for r in records if r["playable"]]
    L = []
    L.append("# Raças em dados: divergências e raças escondidas (2026-11-20)")
    L.append("")
    L.append("Gerado por `scripts/build_races.py` (não edite à mão: mude `scripts/race_curation.json` e rode o script).")
    L.append("")
    L.append("## Resumo")
    L.append("")
    L.append(f"- `data/races.json`: **{len(records)}** raças: as 157 mineradas, com o Bariaur dividido por sexo (+1) e o Half-Vistani, que só existe no app (+1).")
    L.append("- As **17 raças que o app já tinha** (6 do PHB, 10 planares, Half-Vistani) mantêm os valores do app; a mineração só empresta textos (livro, página, visão, idiomas, `content`).")
    L.append("")
    L.append("### Jogáveis por cenário (o que aparece no Forge quando o cenário está ligado)")
    L.append("")
    L.append("| Grupo | Raças | Quantas |")
    L.append("|---|---|---|")
    groups = {}
    for r in playable:
        groups.setdefault(r["group"], []).append(r["name"])
    for g in sorted(groups, key=lambda g: ({"Player's Handbook": 0, "Subraces": 1}.get(g, 2), g)):
        L.append(f"| {g} | {md_escape(', '.join(groups[g]))} | {len(groups[g])} |")
    L.append("")
    L.append("`Council of Wyrms` (22 dragões) e `Spelljammer` (9 raças do Spacefarer's Handbook) estão como jogáveis no dado, mas o cenário está em construção "
             "(`settingsUnderConstruction` na web): nenhum seletor mostra essas raças enquanto isso valer.")
    L.append("")
    L.append("## Divergências: mineração × valores do app")
    L.append("")
    L.append("Decisão do usuário: os valores do app são a verdade; nenhum foi trocado. A coluna \"Fonte provável\" diz de onde veio o valor do app.")
    L.append("Só entram as classes do app nos limites e as combinações com classes do app; o dado completo da mineração segue em `races.json` nos campos `*Text`.")
    L.append("")
    L.append("| Raça | Campo | Mineração | App (mantido) | Fonte provável do valor do app |")
    L.append("|---|---|---|---|---|")
    for race, field, a, b, src in rows:
        L.append(f"| {md_escape(race)} | {md_escape(field)} | {md_escape(a)} | {md_escape(b)} | {md_escape(src)} |")
    L.append("")
    L.append(f"Total: {len(rows)} divergências em {len({r[0] for r in rows})} raças.")
    L.append("")
    L.append("## Raças escondidas")
    L.append("")
    L.append("`playable: false` + `hiddenReason`. Nunca aparecem no Forge nem na ficha; `matchRace` também não as reconhece (texto livre numa ficha continua texto livre).")
    L.append("")
    for reason, title in REASONS:
        items = [r for r in records if r.get("hiddenReason") == reason]
        L.append(f"### {title} ({len(items)})")
        L.append("")
        if reason == "setting-not-in-forge":
            by = {}
            for r in items:
                by.setdefault(r["campaignSetting"], []).append(r)
            for setting in sorted(by):
                L.append(f"- **{setting}** ({len(by[setting])}): " + ", ".join(r["name"] for r in by[setting]))
        else:
            L.append("| Id | Nome | Origem | Observação |")
            L.append("|---|---|---|---|")
            for r in items:
                L.append(f"| `{r['id']}` | {md_escape(r['name'])} | {md_escape(r['source']['book'] or '')} | {md_escape(r.get('note') or (('duplica ' + r['duplicateOf']) if r.get('duplicateOf') else ''))} |")
        L.append("")
    L.append("### Para decisão do usuário")
    L.append("")
    L.append("Sem cenário do Forge claro no texto ou na fonte (artigos da Dragon Magazine e afins). Se alguma deve virar jogável, é só mudar `playable`/`campaignSetting` em `scripts/race_curation.json`:")
    L.append("")
    for r in [r for r in records if r.get("hiddenReason") == "undecided"]:
        L.append(f"- {r['name']} (`{r['id']}`): {r['source']['book']}" + (f". {r['note']}" if r.get("note") else ""))
    L.append("")
    L.append("## Escolhas de classificação que valem uma conferida")
    L.append("")
    L.append("- **Sea of Fallen Stars** é livro dos Forgotten Realms: Aquatic Elf (SofS), Aquatic Half-Elf, Triton, Shalarin e Noble Malenti ficaram jogáveis em `Forgotten Realms`.")
    L.append("- **Half-Greyhawk Dragon** (Dragon #206) cita Greyhawk: jogável em `Greyhawk`. Os outros half-dragons do mesmo artigo não citam cenário: escondidos (decisão).")
    L.append("- **Githyanki Outcast** (Guide to the Astral Plane): só tem limites para Warlock, Githwarriors e gish; com as 12 classes do app, todas dariam aviso. Escondido (decisão).")
    L.append("- **Dryad** cita Krynn só em exemplos; o artigo é geral: escondida (decisão).")
    L.append("- **Sundered Dwarf**: sem cenário no texto do Complete Book of Dwarves: subraça Core.")
    L.append("- **Hengeyokai** e as **Half-Chiang/Shen Lung** são de Kara-Tur (Oriental Adventures); **Aranea, Lupin, Rakasta, Tortle** são de Red Steel (Savage Coast); **Fomorian** e **The Sidhe** são do Celts Campaign Sourcebook; **Trollborn** é de Vikings.")
    L.append("- **Stout Halfling** e **Tallfellow Halfling**: o livro dá \"+1 DEX or CON\" / \"+1 DEX or WIS\"; o dado estruturado só tem o +1 DEX. O app aplica só o +1 DEX; a escolha fica no texto (`abilityScoreAdjustmentsText`).")
    L.append("")
    L.append("## Ids, nomes e duplicatas")
    L.append("")
    L.append("- Ids: o id minerado (`drow`, `athasian_elf`…), exceto as 17 do app, que têm ids estáveis (`human`, `half_elf`, `bariaur_male`, `genasi_fire`, `modron`…). `source.minedId` liga ao registro minerado.")
    L.append("- `name` é o texto que a ficha grava no campo Raça (não muda para as 17: \"Genasi (fire)\", \"Bariaur (male)\"…). Os nomes antigos/mineirados ficam em `aliases` e o `matchRace` os aceita (\"Rogue Modron\" = Modron; \"Human (Standard)\" = Human).")
    L.append("- Nomes repetidos na mineração: **Hill Dwarf** (`hill_dwarf` fica; `hill_dwarf_mountain_dwarves` é cópia, escondida), **Aquatic Elf** (CBE = `aquatic_elf`; Sea of Fallen Stars = `aquatic_elf_sea_of_fallen_stars`, nome \"Aquatic Elf (Sea of Fallen Stars)\"), **Kender** (CBGH = `kender`; Dragonlance MC = `kender_mc`, nome \"Kender (Monstrous Compendium)\"), **Athasian Halfling** (Dark Sun = `athasian_halfling`; CBGH = escondida).")
    L.append("- Outros nomes limpos para a ficha: Mul, Svirfneblin, Furchin, Tinker Gnome, Bakali (o nome minerado fica em `aliases`).")
    L.append("")
    L.append("## Subraças: `baseRace` e o que se herda")
    L.append("")
    L.append("`baseRace` = id de uma das 6 raças do PHB. A web o usa para: (1) kits com restrição de raça (um kit \"Elf\" aceita Drow, High Elf, Athasian Elf…; \"Any except elf\" também as exclui); (2) imagem do Forge (sem arte própria, usa a da raça-base); (3) \"é humano?\" (classe dupla: Athasian Human); (4) tabela de altura/peso/idade (a da raça-base).")
    L.append("")
    L.append("Regras que **não** viajam por `baseRace`: só entram no dado de uma subraça quando o texto dela traz a seção \"Standard <Raça> Abilities\" (o livro diz que as habilidades padrão valem). Nesse caso o script copia da raça-base: bônus de CON nos testes de resistência, resistência a sono/charme, bônus de combate, perícia grátis (Endurance dos anões) e demi-bardo. `inheritsFromBase` lista o que foi copiado. Exceções: Drow (resistência a magia própria, só em texto). As subraças de Dark Sun e de Sea of Fallen Stars (menos o Aquatic Elf) não herdam: têm regras próprias no livro do cenário.")
    L.append("")
    L.append("Não herdam em nenhuma subraça: limites de nível, requisitos, ajustes e combinações (sempre os da própria raça), nem o texto de habilidades da ficha, montado do texto do livro.")
    L.append("")
    return "\n".join(L) + "\n"


def main():
    dry = "--dry-run" in sys.argv
    mining = MINING
    if "--mining" in sys.argv:
        mining = sys.argv[sys.argv.index("--mining") + 1]
    mined = load_mined(mining)
    cur = json.load(open(CURATION, encoding="utf-8"))
    records = build(mined, cur)
    names = [r["name"].lower() for r in records]
    dup = {n for n in names if names.count(n) > 1}
    if dup:
        sys.exit(f"nome repetido: {sorted(dup)}")
    ids = [r["id"] for r in records]
    if len(set(ids)) != len(ids):
        sys.exit("id repetido")
    rows = divergences(cur, mined)
    doc = write_doc(records, rows, mined)
    print(f"{len(records)} raças ({sum(1 for r in records if r['playable'])} jogáveis); {len(rows)} divergências")
    if dry:
        return
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.makedirs(os.path.dirname(DOC), exist_ok=True)
    with open(DOC, "w", encoding="utf-8", newline="\n") as f:
        f.write(doc)


if __name__ == "__main__":
    main()
