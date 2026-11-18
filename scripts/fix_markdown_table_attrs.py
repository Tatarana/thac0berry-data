#!/usr/bin/env python3
"""Refaz 6 tabelas em markdown que vieram com atributos da wiki (2026-11-18).

Problema: na conversão da wiki, algumas tabelas dos textos guardaram os atributos de
estilo das células (`style="text-align:center;" |`, `rowspan="2" |`) e, em várias, cada
célula virou uma linha sozinha. Até a v0.144 a web mostrava esses textos crus; com as
tabelas de texto renderizadas (thac0berry-web), elas viravam tabelas tortas.

Registros (os únicos fora de kits.json com `style=` numa linha de tabela):
  bracers_of_defense, bag_of_holding_1991_card_set, bucknard_s_everfull_purse_1991_card_set,
  cloak_of_elvenkind_1991_card_set, banner_protection_ii, scant_wand_of_storms,
  wizard-2-summon-equine-beings.
Regra: a tabela inteira (do primeiro ao último "|" do bloco) é trocada pela versão
limpa abaixo, com os mesmos valores, na ordem do livro. Rodar de novo não muda nada.

Uso:  python scripts/fix_markdown_table_attrs.py [--dry-run]
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

# (arquivo, id, campo pontilhado, primeira linha do bloco quebrado, tabela nova)
FIXES = [
    ("magic_armor_and_shields.json", "bracers_of_defense", "description.fullText",
     '| style="text-align: center;" | D100 Roll',
     "| D100 Roll | Armor Class |\n| --- | --- |\n| 01-05 | 8 |\n| 06-15 | 7 |\n| 16-35 | 6 |\n"
     "| 36-50 | 5 |\n| 51-70 | 4 |\n| 71-85 | 3 |\n| 86-00 | 2 |"),
    ("magic_miscellaneous_a_to_m.json", "bag_of_holding_1991_card_set", "description.fullText",
     '| style="text-align:center;" | D100 |',
     "| D100 | Weight | Weight Limit | Volume (cubic ft.) |\n| --- | --- | --- | --- |\n"
     "| 1-30 | 15 lbs. | 250 lbs. | 30 |\n| 31-70 | 15 lbs. | 500 lbs. | 70 |\n"
     "| 71-90 | 35 lbs. | 1000 lbs. | 150 |\n| 91-00 | 60 lbs. | 1500 lbs. | 250 |"),
    ("magic_miscellaneous_a_to_m.json", "bucknard_s_everfull_purse_1991_card_set", "description.fullText",
     '| style="text-align:center;" | D100 |',
     "| D100 | CP | SP | EP | GP | PP | Gems* |\n| --- | --- | --- | --- | --- | --- | --- |\n"
     "| 1-50 | — | 26 | 26 | 26 | — | — |\n| 51-90 | 26 | — | 26 | — | 26 | — |\n"
     "| 91-00 | 26 | — | 26 | — | — | 26 |"),
    ("magic_miscellaneous_a_to_m.json", "cloak_of_elvenkind_1991_card_set", "description.fullText",
     '| style="border:none;" | Heavy growth |',
     "| Surroundings | Invisibility |\n| --- | --- |\n| Heavy growth | 100% |\n| Light growth | 99% |\n"
     "| Open fields | 95% |\n| Rocky terrain | 98% |\n| Near buildings | 90% |\n| Brightly lit room | 50% |\n"
     "| Torch/lantern light | 95% |\n| Infravision | 90% |\n| Light / Continual Light | 50% |"),
    ("magic_miscellaneous_a_to_m.json", "banner_protection_ii", "description.fullText",
     '| style="width:75px;"|Roll | Protection granted |',
     None),  # só o cabeçalho: "| Roll | Protection granted |"
    ("magic_rods_staves_wands.json", "scant_wand_of_storms", "description.fullText",
     '| style="text-align: center;" |Effect',
     "| Effect Attempted | Chance for Severe Weather | Type of Weather | Charges Drained |\n"
     "| --- | --- | --- | --- |\n| Wall of Fog | 10% | Thick, persistent fog | 3 |\n"
     "| Precipitation | 10% | Rain or snow squall | 3 |\n| Gust of Wind | 20% | Gale or tornado | 4 |\n"
     "| Cloudburst | 20% | Hailstorm or severe snow | 4 |\n| Chain lightning | 30% | Lightning storm | 5 |\n"
     "| Influence weather | 30% | Heavy rain or blizzard | 5 |"),
    ("wizard_level_2.json", "wizard-2-summon-equine-beings", "fullDescription",
     '| rowspan="2" | Creature Called',
     "| Creature Called | Chance of Success in Plains/Hills | Chance of Success in Forest | Chance of Success in Coastal |\n"
     "| --- | --- | --- | --- |\n| 4d4 Ponies | 30%* | 25% | 35% |\n| 4d4 Mules | 35% | 30% | 25% |\n"
     "| 4d4 Horses | 40%* | 20% | 30% |\n| 4d2 Centaurs | 20% | 30% | 10% |\n| 1d4 Pegasi | 10% | 30% | 10% |\n"
     "| 1d4 Hippogriffs | 30%** | 10% | 10% |\n| 4d4 Hippocampi | - | - | 30% |\n| 1d2 Unicorns*** | 10% | 30% | 10% |"),
]


def block_end(text, start):
    """Fim do bloco da tabela: segue enquanto a linha começa ou termina com "|" (célula com
    quebra de linha dentro, como "Weight\nLimit |", continua o bloco)."""
    end, pos = start, start
    for line in text[start:].split("\n"):
        if not (line.startswith("|") or line.rstrip().endswith("|")):
            break
        end = pos + len(line)
        pos += len(line) + 1
    return end


def get(record, dotted):
    obj = record
    for key in dotted.split(".")[:-1]:
        obj = obj[key]
    return obj, dotted.split(".")[-1]


def main():
    dry = "--dry-run" in sys.argv
    by_file = {}
    for f, *_ in FIXES:
        by_file.setdefault(f, None)
    changed = 0
    for fname in by_file:
        path = os.path.join(ROOT, "data", fname)
        raw = open(path, encoding="utf-8").read()
        data = json.loads(raw)
        index = {r["id"]: r for r in data}
        touched = False
        for f, rid, field, first, new in FIXES:
            if f != fname:
                continue
            obj, key = get(index[rid], field)
            text = obj[key]
            at = text.find(first)
            if at < 0:
                continue  # já corrigido
            if new is None:
                obj[key] = text.replace(first, "| Roll | Protection granted |", 1)
            else:
                end = block_end(text, at)
                obj[key] = text[:at] + new + text[end:]
            changed += 1
            touched = True
            print(f"{rid}: tabela refeita")
        if touched and not dry:
            indent = 2 if raw.startswith("[\n  {") else (1 if raw.startswith("[\n {") else None)
            out = json.dumps(data, ensure_ascii=False, indent=indent)
            if raw.endswith("\n"):
                out += "\n"
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(out)
    print(f"{changed} tabelas refeitas")


if __name__ == "__main__":
    main()
