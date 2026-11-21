#!/usr/bin/env python3
"""Expande data/deities.json (101 -> 386 divindades + heróis mortais) e gera docs/divindades-2026-11.md.

Por quê (2026-11-20): o compêndio só tinha Faiths & Avatars, Powers & Pantheons e os deuses
de Krynn. Agora entram as divindades do Legends & Lore (LL), do Monster Mythology (MoMy) e
dos 10 "Article God" da Dragon Magazine, mineradas por
`../thac0berry-data-mining/extract_deities.py` em `data/deities/*.json`.

Regras:
- Os 101 registros que já existiam (FA, PP, TotL) NÃO mudam de valor. Só ganham os campos
  novos `pantheon` e `forgeSelectable` (de `scripts/deity_curation.json`, bloco `existing`).
- Os registros de LL, MoMy e Dragon são refeitos a cada execução (rodar de novo não muda nada).
- Campos novos, todos opcionais no schema: `pantheon` (string), `forgeSelectable` (boolean;
  ausente = true, aqui sempre gravado) e `race` (string, id-base de data/races.json, só para
  deuses de semi-humanos).
- Id novo = slug do nome; se já existe (outro deus com o mesmo nome em outro panteão, ex. Tyr
  nórdico x Tyr dos Reinos), vira `<id>_<panteão>`; os ids existentes nunca mudam.
- Página minerada sem entrada na curadoria (fonte de panteão nova) faz o script parar.
- Heróis mortais (2026-11): as páginas do LL e do MoMy com `kind: "hero"` na mineração entram DEPOIS de
  todas as divindades (os ids e a ordem das 386 não mudam) com `kind: "hero"` (campo opcional; ausente =
  divindade), `rank` "Hero", `forgeSelectable: false` sempre (decisão do usuário: só compêndio, nunca o
  Forge), `pantheon` pela mesma curadoria (listedPantheon/capítulo), sem `race` e sem exceções por deus.
  Sem portfolio (`""`); as classes vão em `avatarClassLevels` e a ficha em `avatarDescription`.
- Texto: títulos de seção viram linha simples (o app mostra o texto em parágrafos, não
  renderiza markdown de título); tabelas ficam em markdown (o app as desenha).

Uso:  python scripts/build_deities.py [--dry-run] [--mining DIR]
"""
import collections
import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "data", "deities.json")
RACES = os.path.join(ROOT, "data", "races.json")
DOC = os.path.join(ROOT, "docs", "divindades-2026-11.md")
CURATION = os.path.join(ROOT, "scripts", "deity_curation.json")
MINING = os.path.join(ROOT, "..", "thac0berry-data-mining", "data", "deities")

NEW_SOURCES = [("LL", "legends_and_lore.json"), ("MoMy", "monster_mythology.json"), ("Dragon", "dragon_magazine_gods.json")]
EXISTING_CODES = ["FA", "PP", "TotL"]
BASE_RACES = {"human", "elf", "dwarf", "gnome", "half_elf", "halfling"}
ORDER = [c for c, _ in NEW_SOURCES]
COMPARE = ["rank", "plane", "alignment", "status", "portfolio", "aliases", "domainName", "superior", "allies", "foes",
           "symbol", "worshiperAlignments"]


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def slug(text):
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def plain_headings(text):
    return re.sub(r"^#{2,4}[ \t]+(.*)$", r"\1", text, flags=re.MULTILINE)


def is_hero(rec):
    return rec.get("kind") == "hero"


def pick_pantheon(rec, curation):
    table = curation["pantheons"][rec["bookCode"]]
    key = rec["listedPantheon"] if rec["listedPantheon"] in table else rec["chapter"]
    if key not in table:
        raise SystemExit(f"{rec['wikiPageTitle']}: fonte de panteão sem curadoria ({rec['listedPantheon']!r} / {rec['chapter']!r})")
    meta = dict(table[key])
    meta["source"] = key
    over = None if is_hero(rec) else curation["overrides"].get(rec["id"])
    if is_hero(rec):
        meta.pop("race", None)
        meta["forgeSelectable"] = False
    if over:
        meta.update({k: v for k, v in over.items() if k != "why"})
        if "race" not in over:
            meta.pop("race", None)
        meta["override"] = True
    return meta


def build_record(rec, meta, new_id):
    brief = rec["description"]["briefSummary"]
    out = {
        "id": new_id,
        "name": rec["name"],
        "book": rec["book"],
        "bookCode": rec["bookCode"],
        "rank": rec["rank"],
        "plane": rec["plane"],
        "alignment": rec["alignment"],
        "status": rec["status"],
        "portfolio": rec["portfolio"] or "",
        "aliases": rec["aliases"],
        "domainName": rec["domainName"],
        "superior": rec["superior"],
        "allies": rec["allies"],
        "foes": rec["foes"],
        "symbol": rec["symbol"],
        "worshiperAlignments": rec["worshiperAlignments"],
        "avatarClassLevels": (rec["avatar"] or {}).get("classLevels"),
        "avatarDescription": (rec["avatar"] or {}).get("description"),
        "briefSummary": brief,
        "fullText": plain_headings(rec["description"]["fullText"]),
        "categories": ["Dragon Magazine Gods"] if rec["bookCode"] == "Dragon" else
                      [f"{meta['pantheon']} Heroes" if is_hero(rec) else f"{meta['pantheon']} Gods"],
        "pantheon": meta["pantheon"],
        "forgeSelectable": meta["forgeSelectable"],
    }
    if "race" in meta:
        out["race"] = meta["race"]
    if is_hero(rec):
        out["kind"] = "hero"
    return out


def main():
    dry = "--dry-run" in sys.argv
    mining = MINING
    if "--mining" in sys.argv:
        mining = sys.argv[sys.argv.index("--mining") + 1]
    curation = load(CURATION)
    race_ids = {r["id"] for r in load(RACES)}
    for table in curation["pantheons"].values():
        for meta in table.values():
            if "race" in meta and (meta["race"] not in BASE_RACES or meta["race"] not in race_ids):
                raise SystemExit(f"raça desconhecida na curadoria: {meta['race']}")

    current = load(OUT)
    existing = [d for d in current if d["bookCode"] in EXISTING_CODES]
    unknown = {d["bookCode"] for d in current} - set(EXISTING_CODES) - set(ORDER)
    if unknown:
        raise SystemExit(f"bookCode inesperado em deities.json: {unknown}")
    for d in existing:  # só acrescenta os campos novos
        meta = curation["existing"][d["bookCode"]]
        d.setdefault("pantheon", meta["pantheon"])
        d.setdefault("forgeSelectable", meta["forgeSelectable"])

    used = {d["id"] for d in existing}
    by_name = collections.defaultdict(list)
    for d in existing:
        by_name[d["name"].lower()].append(d)
    new, collisions, titles = [], [], set()
    stats = {"mined": {}, "meta": {}}
    batches = []  # (código, [(rec, meta)]); heróis só depois de todas as divindades
    heroes = []
    for code, fname in NEW_SOURCES:
        recs = load(os.path.join(mining, fname))
        stats["mined"][code] = len(recs)
        built, built_heroes = [], []
        for rec in recs:
            if rec["wikiPageTitle"] in titles:
                raise SystemExit(f"página repetida: {rec['wikiPageTitle']}")
            titles.add(rec["wikiPageTitle"])
            (built_heroes if is_hero(rec) else built).append((rec, pick_pantheon(rec, curation)))
        for lst in (built, built_heroes):
            lst.sort(key=lambda rm: (rm[1]["pantheon"], rm[0]["name"].lower()))
        batches.append((code, built))
        heroes.append((code, built_heroes))
    for code, built in batches + heroes:
        for rec, meta in built:
            new_id = rec["id"]
            if new_id in used:
                new_id = f"{rec['id']}_{slug(meta['pantheon'])}"
                if new_id in used:
                    new_id = f"{new_id}_{code.lower()}"
                collisions.append((rec["name"], rec["id"], new_id))
            used.add(new_id)
            out = build_record(rec, meta, new_id)
            new.append(out)
            stats["meta"][new_id] = meta
            by_name[out["name"].lower()].append(out)

    result = existing + new
    # --- divergências: FA/PP re-minerados x registros existentes ---
    diverg = []
    ex_by_id = {d["id"]: d for d in existing}
    for fname, code in (("faiths_and_avatars.json", "FA"), ("powers_and_pantheons.json", "PP")):
        for r in load(os.path.join(mining, fname)):
            d = ex_by_id.get(r["id"])
            if not d:
                diverg.append((r["id"], "(ausente)", "", "existe só na mineração"))
                continue
            mined = dict(r)
            mined.update({"avatarClassLevels": (r["avatar"] or {}).get("classLevels"),
                          "avatarDescription": (r["avatar"] or {}).get("description"),
                          "fullText": r["description"]["fullText"], "briefSummary": r["description"]["briefSummary"]})
            for k in COMPARE + ["avatarClassLevels", "avatarDescription", "fullText", "briefSummary"]:
                if mined.get(k) != d.get(k):
                    diverg.append((r["id"], k, d.get(k), mined.get(k)))

    problems = []
    for d in new:
        for k in ("fullText", "briefSummary", "avatarDescription"):
            v = d.get(k) or ""
            if re.search(r"\[\[|\{\{|'''|^==|Category:|^#{1,6} |<[a-z/]", v, re.M):
                problems.append((d["id"], k))
    if problems:
        raise SystemExit(f"marcação crua da wiki no texto: {problems[:10]}")
    ids = [d["id"] for d in result]
    if len(ids) != len(set(ids)):
        raise SystemExit("id repetido")

    write_doc(existing, new, collisions, by_name, diverg, curation, mining, stats)
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    old = open(OUT, encoding="utf-8").read()
    if dry:
        print(f"(nada gravado) total {len(result)}")
    elif text == old:
        print("nada a mudar")
    else:
        with open(OUT, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print(f"{len(result)} divindades gravadas ({len(existing)} existentes + {len(new)} novas)")


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c).replace("|", "\\|").replace("\n", " ") for c in r) + " |")
    return "\n".join(out)


def write_doc(existing, new, collisions, by_name, diverg, curation, mining, stats):
    allr = [d for d in existing + new if not is_hero(d)]  # as tabelas de divindades não contam os heróis
    heroes = [d for d in new if is_hero(d)]
    new = [d for d in new if not is_hero(d)]
    L = []
    a = L.append
    a("# Divindades: expansão de 101 para %d (2026-11), mais %d heróis mortais\n" % (len(allr), len(heroes)))
    a("Gerado por `scripts/build_deities.py` (não editar à mão). Fonte: `../thac0berry-data-mining/extract_deities.py` "
      "sobre o dump da wiki AD&D 2e + curadoria em `scripts/deity_curation.json`.\n")
    a("## Totais\n")
    books = collections.Counter(d["book"] for d in allr)
    a(md_table(["Livro", "Divindades"], [(b, n) for b, n in books.items()] + [("**Total**", len(allr))]) + "\n")
    a("### Por panteão\n")
    pan = collections.defaultdict(lambda: [0, 0, 0, set()])
    for d in allr:
        p = pan[(d["book"], d["pantheon"])]
        p[0] += 1
        p[1 if d["forgeSelectable"] else 2] += 1
        if d.get("race"):
            p[3].add(d["race"])
    a(md_table(["Livro", "Panteão", "Total", "Forge sim", "Forge não", "Raça"],
               [(b, p, v[0], v[1], v[2], ", ".join(sorted(v[3]))) for (b, p), v in sorted(pan.items())]) + "\n")
    t = sum(1 for d in allr if d["forgeSelectable"])
    a(f"### forgeSelectable\n\n- `true`: **{t}**\n- `false`: **{len(allr) - t}** (só compêndio)\n")
    byb = collections.defaultdict(lambda: [0, 0])
    for d in allr:
        byb[d["book"]][0 if d["forgeSelectable"] else 1] += 1
    a(md_table(["Livro", "true", "false"], [(b, v[0], v[1]) for b, v in byb.items()]) + "\n")
    a("Deuses com `race` (destaque por raça no app): " + ", ".join(
        f"{r} {n}" for r, n in sorted(collections.Counter(d['race'] for d in allr if d.get('race')).items())) + ".\n")

    a("## Campos novos (todos opcionais no schema)\n")
    a("- `pantheon` (string): panteão de origem (capítulo do LL; panteão da lista da wiki no MoMy; 'African' na Dragon; "
      "'Faerûnian' para FA/PP; 'Dragonlance' para TotL).\n"
      "- `forgeSelectable` (boolean, ausente = true): se o Forge pode oferecer o deus. Gravado em todos os registros.\n"
      "- `race` (string): raça-base (`dwarf`, `elf`, `gnome`, `halfling`) dos deuses de semi-humanos.\n"
      "- `kind` (string): `\"hero\"` nos heróis mortais (seção abaixo); ausente = divindade. Só os %d heróis têm o campo.\n" % len(heroes))

    a("## Heróis mortais (`kind: \"hero\"`)\n")
    a("Decisão do usuário (2026-11-21): os heróis do Legends & Lore (LL) e do Monster Mythology (MoMy) entram no "
      "**compêndio**, nunca no Forge: `forgeSelectable: false`, `rank` \"Hero\" (o posto próprio da página, como "
      "'Dwarf Hero', fica só no minerado, `rankRaw`, para o compêndio agrupá-los num posto só), `pantheon` pela mesma "
      "curadoria das divindades (lista da wiki / capítulo), sem `race`. Sem `portfolio` (\"\", campo obrigatório). "
      "As classes vão em `avatarClassLevels` e a ficha do herói (Str/Dex..., Special Att/Def, magias) em `avatarDescription`, "
      "no mesmo formato do avatar dos deuses; o `alignment` sai da linha `AL` da ficha ('any' nos cavaleiros genéricos; "
      "Naciens e Pa Hsien não têm ficha: `alignment` null). Os ids vêm depois dos das divindades, então os ids das 386 "
      "não mudam; nome repetido ganharia o sufixo do panteão (ver a tabela de nomes repetidos).\n")
    hp = collections.defaultdict(list)
    for d in heroes:
        hp[(d["book"], d["pantheon"])].append(d)
    a(md_table(["Livro", "Panteão", "Heróis", "Nomes (id)"],
               [(b, p, len(v), ", ".join(f"{x['name']} (`{x['id']}`)" for x in v)) for (b, p), v in sorted(hp.items())]) + "\n")
    a("Total: **%d** (" % len(heroes) + ", ".join(f"{b} {n}" for b, n in collections.Counter(d['book'] for d in heroes).items()) + ").\n")
    a("Zinzerena e Diancastra (MoMy) constam como 'Hero' na lista da wiki, mas o livro as trata como divindades "
      "(com avatar): ficam entre as divindades, como antes. Heracles (LL) é 'Demigod' na lista e também continua divindade.\n")

    a("## Regras de decisão (usuário, 2026-11-20)\n")
    a("- Legends & Lore (panteões históricos/literários): `forgeSelectable: false`.\n"
      "- Monster Mythology de humanoides e monstros (orc, goblinoide, kobold, gigante, dragão, povo escamoso, mar e céu, "
      "povo das trevas, silvestres, beholder, illithid, myconid, deuses perdidos, derro): `false`.\n"
      "- Monster Mythology dos semi-humanos (anões, elfos incluindo drow, gnomos incluindo svirfneblin, halflings, e os "
      "duergar): `true`, vale em qualquer cenário, com `race`.\n"
      "- FA, PP e TotL existentes: `true`.\n")
    a("### Exceções por deus\n")
    for k, v in curation["overrides"].items():
        a(f"- `{k}` ({v['pantheon']}, forgeSelectable {str(v['forgeSelectable']).lower()}"
          + (f", race {v['race']}" if 'race' in v else "") + f"): {v['why']}")
    a("")

    a("## Dragon Magazine: classificação\n")
    a(curation["dragonMagazine"]["_about"] + "\n")
    rows = [(d["name"], d["id"], d["alignment"], d["forgeSelectable"], curation["dragonMagazine"].get(d["id"], ""))
            for d in new if d["bookCode"] == "Dragon"]
    a(md_table(["Deus", "id", "AL", "forgeSelectable", "Motivo"], rows) + "\n")
    a("A lista da wiki ('List of Gods & Avatars') ainda cita deuses da Dragon #191, #263-265 e Polyhedron (Rillifane "
      "Rallathil, Woden, Thunor, Atroa, Beshaba/Tymora/Xvim...), mas **não há página deles no dump**: ficam de fora.\n")

    a("## Descartados (não são divindades)\n")
    disc = load(os.path.join(mining, "descartadas.json"))
    groups = collections.defaultdict(list)
    for d in disc:
        groups[(d["book"], d["reason"].split(" (posto")[0])].append(re.sub(r"\s*\([^()]*\)$", "", d["title"]))
    for (book, reason), names in sorted(groups.items()):
        a(f"- **{book}**, {reason} ({len(names)}): " + ", ".join(sorted(names)) + ".")
    a("\nOutras exclusões conscientes: Iuz, Vecna, Dendar, Kezef, Ityak-Ortheel, Asmodeus, Graz'zt, Pazrael, Eltab, "
      "Rainha do Caos, Blizzard (páginas de monstro/NPC com infobox Creature, outro formato); Asclepius (AoH, livro "
      "Age of Heroes, fora do escopo). Os heróis mortais não são mais descartados: ver a seção acima.\n")

    a("## Divergências com os registros existentes\n")
    a("### Mineração x deities.json (FA e PP re-minerados)\n")
    if diverg:
        a(md_table(["id", "campo", "no app (vale)", "na mineração"], [(i, k, repr(x)[:80], repr(y)[:80]) for i, k, x, y in diverg]) + "\n")
        a("O valor do app fica. (Tiamat: a wiki tem 'Letter Power', erro de digitação; o app já corrigiu para 'Lesser Power'.)\n")
    else:
        a("Nenhuma.\n")
    a("Os 22 de Krynn (TotL) vêm de `scripts/add_krynn_deities.py`, direto do dump; não passam pela mineração e não foram comparados.\n")
    a("### Mesmo nome em panteões diferentes\n")
    a("Nomes iguais não foram fundidos (são fichas diferentes: o Set dos Reinos é o do PP, o Set egípcio é o do LL). "
      "O id novo ganha o sufixo do panteão; o do app não muda. `findDeityByName` do app devolve o primeiro, que é o existente.\n")
    rows = []
    for name, group in by_name.items():
        if len(group) > 1:
            for d in group:
                rows.append((d["name"], d["id"], d["book"], d["pantheon"], d["rank"], d["alignment"]))
    a(md_table(["Nome", "id", "Livro", "Panteão", "Posto", "AL"], rows) + "\n")

    a("## Correções e limites do texto minerado\n")
    a("- **Alinhamentos do OCR**: a wiki do LL/MoMy traz 'eg', 'en', 'Ig', 'In' (o OCR trocou c->e e l->I). Corrigidos "
      "para CG, CN, LG, LN (Corellon Larethian, Erevan Ilesere e Hanali Celanil confirmam a troca). Incerto só onde o "
      "livro não confere, por exemplo Odin 'CG'.\n"
      "- **Postos**: 'Goddess' vira 'God', plural vira singular ('Lesser Gods' = 'Lesser God'), 'Intermediated' vira "
      "'Intermediate'. Valor original no minerado (`rankRaw`).\n")
    byrank = [d for d in new if d["rank"] is None]
    a("- **Sem posto (`rank` null)**: " + ", ".join(d["name"] for d in byrank) + " (Dragon não traz posto; Stillsong é 'Unknown').\n")
    a("- **Posto vindo da lista da wiki** (a página não tem título de posto): Annam e Yondalla (Greater God).\n"
      "- **The Dark God**: o título diz 'Intermediate/Lesser God: Power Varies'; ficou 'Intermediate God'.\n")
    nop = [d["name"] for d in new if not d["portfolio"]]
    a(f"- **Sem portfolio (`portfolio` = \"\", campo obrigatório no schema)**, a página não tem linha 'Statistics' ({len(nop)}): " + ", ".join(nop) + ".\n")
    noa = [d["name"] for d in new if not d["alignment"]]
    a(f"- **Sem alinhamento** ({len(noa)}): " + ", ".join(noa) + ".\n")
    a("- Os dragões do MoMy (Io, Bahamut, Tiamat, Chronepsis, Faluzure, Aasterinian) usam o formato 'Further Statistics': "
      "só o símbolo foi extraído.\n"
      "- `plane`, `aliases`, `domainName`, `superior`, `allies`, `foes` ficam null: LL/MoMy/Dragon não trazem esses campos.\n"
      "- O avatar vai em texto ('Str 22, Dex 18, ...') como nos deuses de Krynn.\n")

    a("## Questões em aberto (decisão do usuário)\n")
    a("1. Heróis mortais: decidido, entram no compêndio com `kind: \"hero\"` (seção acima).\n"
      "2. Duergar (Laduguer, Diinkarazan) e drow como `forgeSelectable: true` (race dwarf/elf): confirmado pela regra "
      "'semi-humanos', mas são Underdark malignos.\n"
      "3. Deep Sashelas como deus élfico (override acima).\n"
      "4. Nomes repetidos (Set, Isis, Osiris, Tyr...): mostrar o panteão ao lado do nome na lista?\n"
      "5. Mulhorandi, Untheric e Chultan (PP) ficaram em 'Faerûnian'; se quiser sub-panteões é só trocar a curadoria.\n"
      "6. Reorx (TotL) é deus de anões/gnomos, mas ficou só 'Dragonlance' sem `race`.\n"
      "7. Asclepius (AoH) e os deuses da Dragon sem página no dump.\n")
    with open(DOC, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
