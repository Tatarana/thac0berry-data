#!/usr/bin/env python3
"""Corrige tabelas quebradas em `description.fullText` (data/kits.json).

Causa raiz (achada no uso, 2026-10-18, kit "Mind Monk"): o conversor de
wikitexto do thac0berry-data-mining (`kit_patch_common.py`,
`render_table_as_text`) não trata cabeçalhos de tabela com duas linhas
(`rowspan`/`colspan`, comuns em tabelas de progressão de magia) — ele (1) não
tira o `rowspan="2" |`/`colspan="3" |` do texto da célula, e (2) sobrescreve
o cabeçalho da primeira linha pelo da segunda em vez de juntar os dois. O
resultado: a contagem de colunas do cabeçalho (3) não bate com a da linha de
dado (5), cai no modo de emergência (`" | ".join`) e vira uma lista de
traços com barras soltas, sem nome de coluna nenhuma.

Cada correção troca o trecho quebrado pelo equivalente bem formado (mesmo
formato das tabelas que deram certo, ex. kit "Equerry": "**Col / Col**" com
"- Col: valor, Col: valor" por linha), lido a partir de `rawWikitext` (que
continua intacto). Os valores não mudam, só a formatação.

Rodar de novo não muda nada (o trecho quebrado já não existe).

Uso:  python scripts/fix_kit_table_text.py [--dry-run]
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
KITS = os.path.join(ROOT, "data", "kits.json")

OLD_MIND_MONK_TABLE = (
    "**rowspan=\"2\" | Mind Monk's Level / rowspan=\"2\" | Casting Level / colspan=\"3\" | Priest Spell Levels**\n\n"
    "**1 / 2 / 3**\n"
    "- 8 | 1 | 1 | — | —\n"
    "- 9 | 2 | 2 | — | —\n"
    "- 10 | 3 | 2 | 1 | —\n"
    "- 11 | 4 | 2 | 2 | —\n"
    "- 12 | 5 | 2 | 2 | 1\n"
    "- 13 | 6 | 3 | 2 | 1\n"
    "- 14 | 7 | 3 | 2 | 2\n"
    "- 15 | 8 | 3 | 3 | 2\n"
    "- 16* | 9 | 3 | 3 | 3"
)

NEW_MIND_MONK_TABLE = (
    "**Mind Monk's Level / Casting Level / Priest Spell Levels 1 / Priest Spell Levels 2 / Priest Spell Levels 3**\n"
    "- Mind Monk's Level: 8, Casting Level: 1, Priest Spell Levels 1: 1, Priest Spell Levels 2: —, Priest Spell Levels 3: —\n"
    "- Mind Monk's Level: 9, Casting Level: 2, Priest Spell Levels 1: 2, Priest Spell Levels 2: —, Priest Spell Levels 3: —\n"
    "- Mind Monk's Level: 10, Casting Level: 3, Priest Spell Levels 1: 2, Priest Spell Levels 2: 1, Priest Spell Levels 3: —\n"
    "- Mind Monk's Level: 11, Casting Level: 4, Priest Spell Levels 1: 2, Priest Spell Levels 2: 2, Priest Spell Levels 3: —\n"
    "- Mind Monk's Level: 12, Casting Level: 5, Priest Spell Levels 1: 2, Priest Spell Levels 2: 2, Priest Spell Levels 3: 1\n"
    "- Mind Monk's Level: 13, Casting Level: 6, Priest Spell Levels 1: 3, Priest Spell Levels 2: 2, Priest Spell Levels 3: 1\n"
    "- Mind Monk's Level: 14, Casting Level: 7, Priest Spell Levels 1: 3, Priest Spell Levels 2: 2, Priest Spell Levels 3: 2\n"
    "- Mind Monk's Level: 15, Casting Level: 8, Priest Spell Levels 1: 3, Priest Spell Levels 2: 3, Priest Spell Levels 3: 2\n"
    "- Mind Monk's Level: 16*, Casting Level: 9, Priest Spell Levels 1: 3, Priest Spell Levels 2: 3, Priest Spell Levels 3: 3"
)

# kit id -> (trecho quebrado, trecho certo)
FIXES = {
    "mind_monk": (OLD_MIND_MONK_TABLE, NEW_MIND_MONK_TABLE),
}


def main():
    dry = "--dry-run" in sys.argv
    with open(KITS, encoding="utf-8") as f:
        kits = json.load(f)
    by_id = {k["id"]: k for k in kits}
    changed = 0
    for kit_id, (old, new) in FIXES.items():
        kit = by_id.get(kit_id)
        if kit is None:
            raise SystemExit(f"kit não encontrado: {kit_id}")
        text = kit["description"]["fullText"]
        if new in text:
            print(f"{kit_id}: já corrigido")
            continue
        if old not in text:
            raise SystemExit(f"{kit_id}: trecho quebrado não encontrado (a ficha mudou?)")
        kit["description"]["fullText"] = text.replace(old, new, 1)
        changed += 1
        print(f"{kit_id}: tabela corrigida")
    if dry or changed == 0:
        print("(dry-run: nada gravado)" if dry else "(nada a corrigir)")
        return
    with open(KITS, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(kits, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
