#!/usr/bin/env python3
"""Correções explícitas nos valores de referência das regras (fixtures/rules/rules-fixtures.json).

O arquivo é gerado pelo código Swift do iPad (thac0berry-ipad/Scripts/rules_fixtures)
e a web compara as regras dela com ele. Quando o Swift tem um erro e o iPad
está pausado (decisão do usuário, 2026-10-12: corrigir só dados e web), a
correção entra aqui, explícita e idempotente, até o Swift ser corrigido.
Enquanto isso, o workflow "Regras (valores de referência)" do iPad acusa
DIFERE: é esperado.

Correções:
- Sacerdote, 19º nível: a PriestTables do app (Models/Character.swift, linha
  do 19º) tem 9 magias de 3º círculo; a Tabela 24 do PHB (regra
  phb_ch03_priest_tables) e o Domains of Dread têm 8. O bônus de Sabedoria
  não depende da tabela, então todo valor derivado do 19º nível perde 1 no
  3º círculo: a linha da tabela, `spellProgression.priest`,
  `slotAllotments.Cleric` e `byClassLevel.Cleric.priestSpellSlots`.

O arquivo é regravado no formato do JSONEncoder do Swift (o mesmo que o
gerador produz: indentação de 2, " : ", array vazio em três linhas).

Uso:  python scripts/fix_rules_fixtures.py [--dry-run]
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FIXTURES = os.path.join(ROOT, "fixtures", "rules", "rules-fixtures.json")

WRONG_19 = [9, 9, 9, 8, 6, 4, 2]
RIGHT_19 = [9, 9, 8, 8, 6, 4, 2]
NOTE = " Correções explícitas por cima do gerado: thac0berry-data/scripts/fix_rules_fixtures.py."


def swift_json(value, indent=0):
    """Como o JSONEncoder do Swift com .prettyPrinted (ordem das chaves preservada)."""
    pad = "  " * indent
    inner = "  " * (indent + 1)
    if isinstance(value, dict):
        if not value:
            return "{\n\n" + pad + "}"
        items = [inner + json.dumps(k, ensure_ascii=False) + " : " + swift_json(v, indent + 1) for k, v in value.items()]
        return "{\n" + ",\n".join(items) + "\n" + pad + "}"
    if isinstance(value, list):
        if not value:
            return "[\n\n" + pad + "]"
        return "[\n" + ",\n".join(inner + swift_json(v, indent + 1) for v in value) + "\n" + pad + "]"
    return json.dumps(value, ensure_ascii=False)


def fix_priest_level_19(f):
    rows = f["tables"]["PriestTables.spellProgressionRows"]
    if rows[18] == RIGHT_19:
        return 0
    if rows[18] != WRONG_19:
        raise SystemExit(f"linha do 19º inesperada: {rows[18]}")
    rows[18] = list(RIGHT_19)
    changes = 1
    # spellProgression.priest[nível][Sabedoria] = slots por círculo.
    for wisdom, slots in f["spellProgression"]["priest"]["19"].items():
        if slots[2] > 0:
            slots[2] -= 1
            changes += 1
    # slotAllotments.Cleric[nível][Sabedoria] = [{caster, count, level}].
    for wisdom, allotments in f["slotAllotments"]["Cleric"]["19"].items():
        for a in allotments:
            if a["caster"] == "divine" and a["level"] == 3:
                a["count"] -= 1
                changes += 1
    # byClassLevel.Cleric[nível].priestSpellSlots.
    slots = f["byClassLevel"]["Cleric"]["19"]["priestSpellSlots"]
    if slots and slots[2] > 0:
        slots[2] -= 1
        changes += 1
    return changes


def main():
    dry = "--dry-run" in sys.argv
    raw = open(FIXTURES, encoding="utf-8").read()
    f = json.loads(raw)
    if swift_json(f) + "\n" != raw:
        raise SystemExit("o formato do arquivo não é o do Swift: regravar mudaria mais do que a correção")
    changes = fix_priest_level_19(f)
    print(f"sacerdote 19º nível: {changes} valores")
    if changes and NOTE not in f["about"]:
        f["about"] += NOTE
    if dry or changes == 0:
        print("(nada gravado)" if dry else "(nada a mudar)")
        return
    with open(FIXTURES, "w", encoding="utf-8", newline="\n") as out:
        out.write(swift_json(f) + "\n")


if __name__ == "__main__":
    main()
