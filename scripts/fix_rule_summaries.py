#!/usr/bin/env python3
"""Troca os resumos de regra que eram nota de rodapé de tabela (data/rules.json).

Na extração, o `summary` de algumas regras de tabela pegou a primeira linha de
texto, que era a nota de rodapé da tabela (": ** This award can be…",
":* Only if…", "* Abjure (Pr 4)"). O asterisco ali é a marca da nota, não
markdown, e o ": " é sobra do formato da wiki. A lista de regras (iPad e web)
mostrava isso como resumo. As notas continuam no `content`, junto da tabela;
só o `summary` muda (2026-10-13). Também tira a marca de abertura sem par de
dois resumos cortados antes do fechamento do negrito/itálico.

Cada troca é explícita: regra, resumo antigo (conferido) e resumo novo.
Rodar de novo não muda nada (o resumo antigo já não existe).

Uso:  python scripts/fix_rule_summaries.py [--dry-run]
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RULES = os.path.join(ROOT, "data", "rules.json")

# (id da regra, começo do resumo antigo, resumo novo).
FIXES = [
    ("dmg_ch08_experience_tables", ": ** This award can be greater",
     "Tables 31–34: creature experience point values, Hit Dice value modifiers, "
     "common individual awards and individual class awards."),
    ("phb_ch02_character_race_tables", "* Halfling fighters do not roll",
     "Tables 7–12: racial ability requirements, racial abilities, Constitution "
     "saving throw bonuses, average height and weight, age and aging effects."),
    ("phb_ch03_priest_tables", ": ** See section on hierophant druids",
     "Tables 23–24: priest experience levels and priest spell progression."),
    ("phb_ch03_warrior_tables", "* Optional character class.",
     "Tables 13–19: class ability minimums, warrior experience levels, warrior "
     "melee attacks per round, fighter's followers, paladin spell progression, "
     "ranger abilities and ranger's followers."),
    ("phb_ch06_armor_list", ":* See table 46",
     "Cost and weight of armor, helmets and shields. Table 46 gives the Armor "
     "Class of each armor type."),
    ("phb_ch06_encumbrance", "* Encumbrance Tables",
     "A natural desire is to have your character own one of everything. Sadly, "
     "there are limits to how much your character can carry. These limits are "
     "determined by encumbrance."),
    ("phb_ch06_miscellaneous_equipment", ":* These items weigh little",
     "Cost and weight of miscellaneous adventuring equipment, from backpacks "
     "and lanterns to rope, tents and tools."),
    ("phb_ch06_transport", "* Movement rates for this equipment",
     "Cost of boats, ships, carriages, chariots and wagons. Movement rates are "
     "given in the DMG."),
    ("phb_ch07_spell_index", "* Abjure (Pr 4)",
     "Alphabetical index of the priest (Pr) and wizard (Wiz) spells, with the "
     "level of each."),
    ("phb_ch14_climbing_tables", ":* Only if the optional proficiency",
     "Tables 65–67: base climbing success rates, climbing modifiers and rates "
     "of climbing."),
    ("cpsih_ch09_related_reading", "- * - Denotes a new entry",
     "Fiction and nonfiction about psionics, suggested reading for a psionics "
     "campaign."),
    ("pwh_ch00_racial_tables", "U= Unlimited N/A=",
     "Planar races: ability requirements, ability adjustments, average height "
     "and weight, age, aging effects, level limits and thief skill "
     "adjustments."),
]

# (id da regra, marca do começo): resumo cortado antes do fechamento do
# negrito/itálico, então a marca de abertura ficava sem par e aparecia crua.
UNPAIRED = [
    ("dk_ch05_the_brown_elf", "**"),
    ("tka_ch00_thri_kreen_pcs_character_classes", "*"),
]


def main():
    dry = "--dry-run" in sys.argv
    with open(RULES, encoding="utf-8") as f:
        rules = json.load(f)
    by_id = {rule["id"]: rule for rule in rules}
    total = 0
    for rule_id, old_start, new in FIXES:
        rule = by_id.get(rule_id)
        if rule is None:
            raise SystemExit(f"regra não encontrada: {rule_id}")
        if rule["summary"] == new:
            continue
        if not rule["summary"].startswith(old_start):
            raise SystemExit(f"{rule_id}: resumo inesperado: {rule['summary'][:60]!r}")
        rule["summary"] = new
        total += 1
        print(f"{rule_id}: {new}")
    for rule_id, mark in UNPAIRED:
        rule = by_id.get(rule_id)
        if rule is None:
            raise SystemExit(f"regra não encontrada: {rule_id}")
        summary = rule["summary"]
        if summary.startswith(mark) and summary.count("*") == len(mark):
            rule["summary"] = summary[len(mark):]
            total += 1
            print(f"{rule_id}: tira o {mark} sem par do começo")
    if dry or total == 0:
        print("(nada gravado)" if dry else "(nada a corrigir)")
        return
    with open(RULES, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rules, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
