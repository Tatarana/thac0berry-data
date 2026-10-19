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

Busca pelos outros kits com a mesma causa (2026-10-18): procurar
`rowspan=`/`colspan=` em `fullText` dá 62 kits, mas 53 (os kits de divindade,
ex. "Azuth, Golemmaster") usam um `colspan="2"` de uma célula só (vira título
de seção, "**Class Information**"/"**Proficiencies**" — não é o bug, já
funciona). Só quebra quando o cabeçalho tem células separadas por `||` *e*
inclui `rowspan=`/`colspan=` (o sinal é `**...rowspan=...||colspan=...**`):
achados 6, todos com o mesmo formato de 2 linhas de cabeçalho (N colunas
fixas + 1 grupo `colspan` com sub-cabeçalho na linha seguinte) — "Feralan",
"Ghosthunter" (Tabela 18, Turning Undead, 13 colunas), "Justifier",
"Mountain Man", "Seeker" e "Votary" (todos kits de guerreiro/variado, Tabelas
de progressão de magia ou de Turn Undead). Mesma reconstrução a partir do
`rawWikitext`, juntando as sub-colunas do grupo com o nome dele.

Busca mais ampla por qualquer linha "- a | b | c" (o dump de emergência, com
ou sem `rowspan=`/`colspan=`) achou mais um, de uma causa diferente: o kit
"Militant Psionicist" tem uma tabela cujo cabeçalho no wikitexto usa "|" em
vez de "!" (sintaxe de wiki válida, só incomum) — `render_table_as_text` só
reconhece "!" como linha de cabeçalho, então nem o cabeçalho nem as linhas de
dado encontram um `headers` pra casar, e tudo vira dump.

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

# Primeira correção (2026-10-18), no formato de lista; trocada pela tabela em
# markdown abaixo a pedido do usuário (2026-10-19).
LIST_MIND_MONK_TABLE = (
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

# Tabela em markdown ("| … |" + linha "---"), como as tabelas dos suplementos
# em rules.json; a ficha do kit na web a mostra como tabela de verdade.
NEW_MIND_MONK_TABLE = (
    "**Mind Monk's Spell Advancement**\n\n"
    "| Mind Monk's Level | Casting Level | Priest Spell Level 1 | Priest Spell Level 2 | Priest Spell Level 3 |\n"
    "| --- | --- | --- | --- | --- |\n"
    "| 8 | 1 | 1 | — | — |\n"
    "| 9 | 2 | 2 | — | — |\n"
    "| 10 | 3 | 2 | 1 | — |\n"
    "| 11 | 4 | 2 | 2 | — |\n"
    "| 12 | 5 | 2 | 2 | 1 |\n"
    "| 13 | 6 | 3 | 2 | 1 |\n"
    "| 14 | 7 | 3 | 2 | 2 |\n"
    "| 15 | 8 | 3 | 3 | 2 |\n"
    "| 16* | 9 | 3 | 3 | 3 |"
)

OLD_FERALAN_TABLE = (
    "**rowspan=\"2\" | Feralan Level / rowspan=\"2\" | Casting Level / colspan=\"2\" | Priest Spell Level***\n\n"
    "**1 / 2**\n"
    "- 1-7 | — | — | —\n"
    "- 8-9 | 1 | 1 | —\n"
    "- 10-11 | 2 | 2 | —\n"
    "- 12-13 | 3 | 2 | 1\n"
    "- 14-15 | 4 | 2 | 2\n"
    "- 16+ | 5 | 3 | 2"
)

NEW_FERALAN_TABLE = (
    "**Feralan Level / Casting Level / Priest Spell Level* 1 / Priest Spell Level* 2**\n"
    "- Feralan Level: 1-7, Casting Level: —, Priest Spell Level* 1: —, Priest Spell Level* 2: —\n"
    "- Feralan Level: 8-9, Casting Level: 1, Priest Spell Level* 1: 1, Priest Spell Level* 2: —\n"
    "- Feralan Level: 10-11, Casting Level: 2, Priest Spell Level* 1: 2, Priest Spell Level* 2: —\n"
    "- Feralan Level: 12-13, Casting Level: 3, Priest Spell Level* 1: 2, Priest Spell Level* 2: 1\n"
    "- Feralan Level: 14-15, Casting Level: 4, Priest Spell Level* 1: 2, Priest Spell Level* 2: 2\n"
    "- Feralan Level: 16+, Casting Level: 5, Priest Spell Level* 1: 3, Priest Spell Level* 2: 2"
)

OLD_GHOSTHUNTER_TABLE = (
    "**rowspan=\"2\" | Ghosthunter / colspan=\"13\" | Category of Undead**\n\n"
    "**1 / 2 / 3 / 4 / 5 / 6 / 7 / 8 / 9 / 10 / 11 / 12 / 13**\n"
    "- 1 | 10 | 13 | 16 | 19 | 20 | — | — | — | — | — | — | — | —\n"
    "- 2 | 7 | 10 | 13 | 16 | 19 | 20 | — | — | — | — | — | — | —\n"
    "- 3 | 4 | 7 | 10 | 13 | 16 | 19 | 20 | — | — | — | — | — | —\n"
    "- 4 | T | 4 | 7 | 10 | 13 | 16 | 19 | 20 | — | — | — | — | —\n"
    "- 5 | T | T | 4 | 7 | 10 | 13 | 16 | 19 | 20 | — | — | — | —\n"
    "- 6 | D | T | T | 4 | 7 | 10 | 13 | 16 | 19 | 20 | — | — | —\n"
    "- 7 | D | D | T | T | 4 | 7 | 10 | 13 | 16 | 19 | 20 | — | —\n"
    "- 8 | D* | D | D | T | T | 4 | 7 | 13 | 10 | 16 | 19 | 20 | —\n"
    "- 9 | D* | D* | D | D | T | T | 4 | 7 | 10 | 13 | 16 | 19 | 20\n"
    "- 10-11 | D* | D* | D* | D | D | T | T | 4 | 7 | 10 | 13 | 16 | 19\n"
    "- 12-13 | D* | D* | D* | D* | D | D | T | T | 4 | 7 | 10 | 13 | 16\n"
    "- 14+ | D* | D* | D* | D* | D* | D | D | T | T | 4 | 7 | 10 | 13"
)

NEW_GHOSTHUNTER_TABLE = (
    "**Ghosthunter / Category of Undead 1 / Category of Undead 2 / Category of Undead 3 / Category of Undead 4 / Category of Undead 5 / Category of Undead 6 / Category of Undead 7 / Category of Undead 8 / Category of Undead 9 / Category of Undead 10 / Category of Undead 11 / Category of Undead 12 / Category of Undead 13**\n"
    "- Ghosthunter: 1, Category of Undead 1: 10, Category of Undead 2: 13, Category of Undead 3: 16, Category of Undead 4: 19, Category of Undead 5: 20, Category of Undead 6: —, Category of Undead 7: —, Category of Undead 8: —, Category of Undead 9: —, Category of Undead 10: —, Category of Undead 11: —, Category of Undead 12: —, Category of Undead 13: —\n"
    "- Ghosthunter: 2, Category of Undead 1: 7, Category of Undead 2: 10, Category of Undead 3: 13, Category of Undead 4: 16, Category of Undead 5: 19, Category of Undead 6: 20, Category of Undead 7: —, Category of Undead 8: —, Category of Undead 9: —, Category of Undead 10: —, Category of Undead 11: —, Category of Undead 12: —, Category of Undead 13: —\n"
    "- Ghosthunter: 3, Category of Undead 1: 4, Category of Undead 2: 7, Category of Undead 3: 10, Category of Undead 4: 13, Category of Undead 5: 16, Category of Undead 6: 19, Category of Undead 7: 20, Category of Undead 8: —, Category of Undead 9: —, Category of Undead 10: —, Category of Undead 11: —, Category of Undead 12: —, Category of Undead 13: —\n"
    "- Ghosthunter: 4, Category of Undead 1: T, Category of Undead 2: 4, Category of Undead 3: 7, Category of Undead 4: 10, Category of Undead 5: 13, Category of Undead 6: 16, Category of Undead 7: 19, Category of Undead 8: 20, Category of Undead 9: —, Category of Undead 10: —, Category of Undead 11: —, Category of Undead 12: —, Category of Undead 13: —\n"
    "- Ghosthunter: 5, Category of Undead 1: T, Category of Undead 2: T, Category of Undead 3: 4, Category of Undead 4: 7, Category of Undead 5: 10, Category of Undead 6: 13, Category of Undead 7: 16, Category of Undead 8: 19, Category of Undead 9: 20, Category of Undead 10: —, Category of Undead 11: —, Category of Undead 12: —, Category of Undead 13: —\n"
    "- Ghosthunter: 6, Category of Undead 1: D, Category of Undead 2: T, Category of Undead 3: T, Category of Undead 4: 4, Category of Undead 5: 7, Category of Undead 6: 10, Category of Undead 7: 13, Category of Undead 8: 16, Category of Undead 9: 19, Category of Undead 10: 20, Category of Undead 11: —, Category of Undead 12: —, Category of Undead 13: —\n"
    "- Ghosthunter: 7, Category of Undead 1: D, Category of Undead 2: D, Category of Undead 3: T, Category of Undead 4: T, Category of Undead 5: 4, Category of Undead 6: 7, Category of Undead 7: 10, Category of Undead 8: 13, Category of Undead 9: 16, Category of Undead 10: 19, Category of Undead 11: 20, Category of Undead 12: —, Category of Undead 13: —\n"
    "- Ghosthunter: 8, Category of Undead 1: D*, Category of Undead 2: D, Category of Undead 3: D, Category of Undead 4: T, Category of Undead 5: T, Category of Undead 6: 4, Category of Undead 7: 7, Category of Undead 8: 13, Category of Undead 9: 10, Category of Undead 10: 16, Category of Undead 11: 19, Category of Undead 12: 20, Category of Undead 13: —\n"
    "- Ghosthunter: 9, Category of Undead 1: D*, Category of Undead 2: D*, Category of Undead 3: D, Category of Undead 4: D, Category of Undead 5: T, Category of Undead 6: T, Category of Undead 7: 4, Category of Undead 8: 7, Category of Undead 9: 10, Category of Undead 10: 13, Category of Undead 11: 16, Category of Undead 12: 19, Category of Undead 13: 20\n"
    "- Ghosthunter: 10-11, Category of Undead 1: D*, Category of Undead 2: D*, Category of Undead 3: D*, Category of Undead 4: D, Category of Undead 5: D, Category of Undead 6: T, Category of Undead 7: T, Category of Undead 8: 4, Category of Undead 9: 7, Category of Undead 10: 10, Category of Undead 11: 13, Category of Undead 12: 16, Category of Undead 13: 19\n"
    "- Ghosthunter: 12-13, Category of Undead 1: D*, Category of Undead 2: D*, Category of Undead 3: D*, Category of Undead 4: D*, Category of Undead 5: D, Category of Undead 6: D, Category of Undead 7: T, Category of Undead 8: T, Category of Undead 9: 4, Category of Undead 10: 7, Category of Undead 11: 10, Category of Undead 12: 13, Category of Undead 13: 16\n"
    "- Ghosthunter: 14+, Category of Undead 1: D*, Category of Undead 2: D*, Category of Undead 3: D*, Category of Undead 4: D*, Category of Undead 5: D*, Category of Undead 6: D, Category of Undead 7: D, Category of Undead 8: T, Category of Undead 9: T, Category of Undead 10: 4, Category of Undead 11: 7, Category of Undead 12: 10, Category of Undead 13: 13"
)

OLD_JUSTIFIER_TABLE = (
    "**rowspan=\"2\" | Justifier Level / rowspan=\"2\" | Casting Level / colspan=\"3\" | Priest Spell Level**\n\n"
    "**1 / 2 / 3**\n"
    "- 1-9 | — | — | — | —\n"
    "- 10 | 1 | 1 | — | —\n"
    "- 11 | 2 | 2 | — | —\n"
    "- 12 | 3 | 2 | 1 | —\n"
    "- 13 | 4 | 2 | 2 | —\n"
    "- 14 | 5 | 2 | 2 | 1\n"
    "- 15 | 6 | 2 | 2 | 2\n"
    "- 16+ | 7 | 3 | 2 | 2"
)

NEW_JUSTIFIER_TABLE = (
    "**Justifier Level / Casting Level / Priest Spell Level 1 / Priest Spell Level 2 / Priest Spell Level 3**\n"
    "- Justifier Level: 1-9, Casting Level: —, Priest Spell Level 1: —, Priest Spell Level 2: —, Priest Spell Level 3: —\n"
    "- Justifier Level: 10, Casting Level: 1, Priest Spell Level 1: 1, Priest Spell Level 2: —, Priest Spell Level 3: —\n"
    "- Justifier Level: 11, Casting Level: 2, Priest Spell Level 1: 2, Priest Spell Level 2: —, Priest Spell Level 3: —\n"
    "- Justifier Level: 12, Casting Level: 3, Priest Spell Level 1: 2, Priest Spell Level 2: 1, Priest Spell Level 3: —\n"
    "- Justifier Level: 13, Casting Level: 4, Priest Spell Level 1: 2, Priest Spell Level 2: 2, Priest Spell Level 3: —\n"
    "- Justifier Level: 14, Casting Level: 5, Priest Spell Level 1: 2, Priest Spell Level 2: 2, Priest Spell Level 3: 1\n"
    "- Justifier Level: 15, Casting Level: 6, Priest Spell Level 1: 2, Priest Spell Level 2: 2, Priest Spell Level 3: 2\n"
    "- Justifier Level: 16+, Casting Level: 7, Priest Spell Level 1: 3, Priest Spell Level 2: 2, Priest Spell Level 3: 2"
)

OLD_MOUNTAIN_MAN_TABLE = (
    "**rowspan=\"2\" | Mountain Man Level / rowspan=\"2\" | Casting Level / colspan=\"3\" | Priest Spell Level**\n\n"
    "**1 / 2 / 3**\n"
    "- 1-9 | — | — | — | —\n"
    "- 10-11 | 1 | 1 | — | —\n"
    "- 12-13 | 2 | 2 | — | —\n"
    "- 14-15 | 3 | 2 | 1 | —\n"
    "- 16+ | 4 | 2 | 2 | —"
)

NEW_MOUNTAIN_MAN_TABLE = (
    "**Mountain Man Level / Casting Level / Priest Spell Level 1 / Priest Spell Level 2 / Priest Spell Level 3**\n"
    "- Mountain Man Level: 1-9, Casting Level: —, Priest Spell Level 1: —, Priest Spell Level 2: —, Priest Spell Level 3: —\n"
    "- Mountain Man Level: 10-11, Casting Level: 1, Priest Spell Level 1: 1, Priest Spell Level 2: —, Priest Spell Level 3: —\n"
    "- Mountain Man Level: 12-13, Casting Level: 2, Priest Spell Level 1: 2, Priest Spell Level 2: —, Priest Spell Level 3: —\n"
    "- Mountain Man Level: 14-15, Casting Level: 3, Priest Spell Level 1: 2, Priest Spell Level 2: 1, Priest Spell Level 3: —\n"
    "- Mountain Man Level: 16+, Casting Level: 4, Priest Spell Level 1: 2, Priest Spell Level 2: 2, Priest Spell Level 3: —"
)

OLD_SEEKER_TABLE = (
    "**rowspan=\"2\" | Seeker Level / rowspan=\"2\" | Casting Level / colspan=\"4\" | Priest Spell Levels**\n\n"
    "**1 / 2 / 3 / 4**\n"
    "- 1-5 | — | — | — | — | —\n"
    "- 6 | 1 | 1 | — | — | —\n"
    "- 7 | 2 | 2 | — | — | —\n"
    "- 8 | 3 | 2 | 1 | — | —\n"
    "- 9 | 4 | 2 | 2 | — | —\n"
    "- 10 | 5 | 2 | 2 | 1 | —\n"
    "- 11 | 6 | 3 | 2 | 1 | —\n"
    "- 12 | 7 | 3 | 2 | 2 | —\n"
    "- 13 | 8 | 3 | 3 | 2 | 1\n"
    "- 14 | 9 | 3 | 3 | 3 | 1\n"
    "- 15 | 10 | 4 | 4 | 3 | 1\n"
    "- 16+ | 11 | 4 | 4 | 3 | 2"
)

NEW_SEEKER_TABLE = (
    "**Seeker Level / Casting Level / Priest Spell Levels 1 / Priest Spell Levels 2 / Priest Spell Levels 3 / Priest Spell Levels 4**\n"
    "- Seeker Level: 1-5, Casting Level: —, Priest Spell Levels 1: —, Priest Spell Levels 2: —, Priest Spell Levels 3: —, Priest Spell Levels 4: —\n"
    "- Seeker Level: 6, Casting Level: 1, Priest Spell Levels 1: 1, Priest Spell Levels 2: —, Priest Spell Levels 3: —, Priest Spell Levels 4: —\n"
    "- Seeker Level: 7, Casting Level: 2, Priest Spell Levels 1: 2, Priest Spell Levels 2: —, Priest Spell Levels 3: —, Priest Spell Levels 4: —\n"
    "- Seeker Level: 8, Casting Level: 3, Priest Spell Levels 1: 2, Priest Spell Levels 2: 1, Priest Spell Levels 3: —, Priest Spell Levels 4: —\n"
    "- Seeker Level: 9, Casting Level: 4, Priest Spell Levels 1: 2, Priest Spell Levels 2: 2, Priest Spell Levels 3: —, Priest Spell Levels 4: —\n"
    "- Seeker Level: 10, Casting Level: 5, Priest Spell Levels 1: 2, Priest Spell Levels 2: 2, Priest Spell Levels 3: 1, Priest Spell Levels 4: —\n"
    "- Seeker Level: 11, Casting Level: 6, Priest Spell Levels 1: 3, Priest Spell Levels 2: 2, Priest Spell Levels 3: 1, Priest Spell Levels 4: —\n"
    "- Seeker Level: 12, Casting Level: 7, Priest Spell Levels 1: 3, Priest Spell Levels 2: 2, Priest Spell Levels 3: 2, Priest Spell Levels 4: —\n"
    "- Seeker Level: 13, Casting Level: 8, Priest Spell Levels 1: 3, Priest Spell Levels 2: 3, Priest Spell Levels 3: 2, Priest Spell Levels 4: 1\n"
    "- Seeker Level: 14, Casting Level: 9, Priest Spell Levels 1: 3, Priest Spell Levels 2: 3, Priest Spell Levels 3: 3, Priest Spell Levels 4: 1\n"
    "- Seeker Level: 15, Casting Level: 10, Priest Spell Levels 1: 4, Priest Spell Levels 2: 4, Priest Spell Levels 3: 3, Priest Spell Levels 4: 1\n"
    "- Seeker Level: 16+, Casting Level: 11, Priest Spell Levels 1: 4, Priest Spell Levels 2: 4, Priest Spell Levels 3: 3, Priest Spell Levels 4: 2"
)

OLD_VOTARY_TABLE = (
    "**rowspan=\"2\" | Votary Level / rowspan=\"2\" | Casting Level / colspan=\"4\" | Priest Spell Levels**\n\n"
    "**1 / 2 / 3 / 4**\n"
    "- 6 | 1 | 1 | — | — | —\n"
    "- 7 | 2 | 2 | — | — | —\n"
    "- 8 | 3 | 2 | 1 | — | —\n"
    "- 9 | 4 | 3 | 2 | — | —\n"
    "- 10 | 5 | 3 | 2 | 1 | —\n"
    "- 11 | 6 | 4 | 2 | 1 | —\n"
    "- 12 | 7 | 4 | 2 | 2 | —\n"
    "- 13 | 8 | 4 | 2 | 2 | 1\n"
    "- 14 | 9 | 4 | 3 | 2 | 1\n"
    "- 15 | 9 | 4 | 4 | 2 | 1\n"
    "- 16 | 9 | 4 | 4 | 3 | 1\n"
    "- 17 | 9 | 4 | 4 | 3 | 2\n"
    "- 18 | 9 | 4 | 4 | 3 | 3\n"
    "- 19 | 9 | 4 | 4 | 4 | 3\n"
    "- 20 | 9 | 4 | 4 | 4 | 4"
)

NEW_VOTARY_TABLE = (
    "**Votary Level / Casting Level / Priest Spell Levels 1 / Priest Spell Levels 2 / Priest Spell Levels 3 / Priest Spell Levels 4**\n"
    "- Votary Level: 6, Casting Level: 1, Priest Spell Levels 1: 1, Priest Spell Levels 2: —, Priest Spell Levels 3: —, Priest Spell Levels 4: —\n"
    "- Votary Level: 7, Casting Level: 2, Priest Spell Levels 1: 2, Priest Spell Levels 2: —, Priest Spell Levels 3: —, Priest Spell Levels 4: —\n"
    "- Votary Level: 8, Casting Level: 3, Priest Spell Levels 1: 2, Priest Spell Levels 2: 1, Priest Spell Levels 3: —, Priest Spell Levels 4: —\n"
    "- Votary Level: 9, Casting Level: 4, Priest Spell Levels 1: 3, Priest Spell Levels 2: 2, Priest Spell Levels 3: —, Priest Spell Levels 4: —\n"
    "- Votary Level: 10, Casting Level: 5, Priest Spell Levels 1: 3, Priest Spell Levels 2: 2, Priest Spell Levels 3: 1, Priest Spell Levels 4: —\n"
    "- Votary Level: 11, Casting Level: 6, Priest Spell Levels 1: 4, Priest Spell Levels 2: 2, Priest Spell Levels 3: 1, Priest Spell Levels 4: —\n"
    "- Votary Level: 12, Casting Level: 7, Priest Spell Levels 1: 4, Priest Spell Levels 2: 2, Priest Spell Levels 3: 2, Priest Spell Levels 4: —\n"
    "- Votary Level: 13, Casting Level: 8, Priest Spell Levels 1: 4, Priest Spell Levels 2: 2, Priest Spell Levels 3: 2, Priest Spell Levels 4: 1\n"
    "- Votary Level: 14, Casting Level: 9, Priest Spell Levels 1: 4, Priest Spell Levels 2: 3, Priest Spell Levels 3: 2, Priest Spell Levels 4: 1\n"
    "- Votary Level: 15, Casting Level: 9, Priest Spell Levels 1: 4, Priest Spell Levels 2: 4, Priest Spell Levels 3: 2, Priest Spell Levels 4: 1\n"
    "- Votary Level: 16, Casting Level: 9, Priest Spell Levels 1: 4, Priest Spell Levels 2: 4, Priest Spell Levels 3: 3, Priest Spell Levels 4: 1\n"
    "- Votary Level: 17, Casting Level: 9, Priest Spell Levels 1: 4, Priest Spell Levels 2: 4, Priest Spell Levels 3: 3, Priest Spell Levels 4: 2\n"
    "- Votary Level: 18, Casting Level: 9, Priest Spell Levels 1: 4, Priest Spell Levels 2: 4, Priest Spell Levels 3: 3, Priest Spell Levels 4: 3\n"
    "- Votary Level: 19, Casting Level: 9, Priest Spell Levels 1: 4, Priest Spell Levels 2: 4, Priest Spell Levels 3: 4, Priest Spell Levels 4: 3\n"
    "- Votary Level: 20, Casting Level: 9, Priest Spell Levels 1: 4, Priest Spell Levels 2: 4, Priest Spell Levels 3: 4, Priest Spell Levels 4: 4"
)

OLD_MILITANT_PSIONICIST_TABLE = (
    "- Level | Dis. | Sci. | Dev.\n"
    "- 1 | 1 | — | 1\n"
    "- 2 | 1 | — | 1\n"
    "- 3 | 1 | — | 1\n"
    "- 4 | 1 | 1 | 2"
)

# Variante C do mesmo bug: a tabela usa "|" em vez de "!" na linha de
# cabeçalho (sintaxe wiki válida, mas rara) — render_table_as_text só
# reconhece "!" como cabeçalho, então nem detecta um; toda linha, cabeçalho
# incluso, cai no dump de emergência.
NEW_MILITANT_PSIONICIST_TABLE = (
    "**Level / Dis. / Sci. / Dev.**\n"
    "- Level: 1, Dis.: 1, Sci.: —, Dev.: 1\n"
    "- Level: 2, Dis.: 1, Sci.: —, Dev.: 1\n"
    "- Level: 3, Dis.: 1, Sci.: —, Dev.: 1\n"
    "- Level: 4, Dis.: 1, Sci.: 1, Dev.: 2"
)

# kit id -> (trecho quebrado, ou tupla de versões antigas; trecho certo)
FIXES = {
    "mind_monk": ((OLD_MIND_MONK_TABLE, LIST_MIND_MONK_TABLE), NEW_MIND_MONK_TABLE),
    "militant_psionicist": (OLD_MILITANT_PSIONICIST_TABLE, NEW_MILITANT_PSIONICIST_TABLE),
    "feralan": (OLD_FERALAN_TABLE, NEW_FERALAN_TABLE),
    "ghosthunter": (OLD_GHOSTHUNTER_TABLE, NEW_GHOSTHUNTER_TABLE),
    "justifier": (OLD_JUSTIFIER_TABLE, NEW_JUSTIFIER_TABLE),
    "mountain_man": (OLD_MOUNTAIN_MAN_TABLE, NEW_MOUNTAIN_MAN_TABLE),
    "seeker": (OLD_SEEKER_TABLE, NEW_SEEKER_TABLE),
    "votary": (OLD_VOTARY_TABLE, NEW_VOTARY_TABLE),
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
        found = next((o for o in (old if isinstance(old, tuple) else (old,)) if o in text), None)
        if found is None:
            raise SystemExit(f"{kit_id}: trecho quebrado não encontrado (a ficha mudou?)")
        kit["description"]["fullText"] = text.replace(found, new, 1)
        changed += 1
        print(f"{kit_id}: tabela corrigida")
    if dry or changed == 0:
        print("(dry-run: nada gravado)" if dry else "(nada a corrigir)")
        return
    with open(KITS, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(kits, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
