#!/usr/bin/env python3
"""Troca os resumos de regra que eram nota de rodapé ou tabela (data/rules.json).

Na extração, o `summary` de algumas regras de tabela pegou a primeira linha de
texto, que era a nota de rodapé da tabela (": ** This award can be…",
":* Only if…", "* Abjure (Pr 4)"). O asterisco ali é a marca da nota, não
markdown, e o ": " é sobra do formato da wiki. A lista de regras (iPad e web)
mostrava isso como resumo. As notas continuam no `content`, junto da tabela;
só o `summary` muda (2026-10-13). Também tira a marca de abertura sem par de
dois resumos cortados antes do fechamento do negrito/itálico.

Na segunda leva (2026-10-13), 7 regras que começam direto com uma tabela
markdown (CFH, CBH, WATW) tinham como resumo as linhas da tabela ("| Item |
Cost | …"), que a lista mostrava numa linha só, com barras e traços. Ganharam
uma frase que descreve a tabela.

Na terceira leva (2026-10-13), 6 regras que são só a imagem de uma ficha em
branco (CBarbH, CPaH, CBH) tinham, no resumo e no texto, o código de imagem
da wiki ("File:Paladin Kit Sheet.png|thumb|…"), sem a imagem. Aqui o `content`
também muda: os dois viram uma frase dizendo o que a ficha é.

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
    # Segunda leva: resumos que eram as linhas de uma tabela markdown.
    ("cfh_ch00_armor_fitting", "| Race Trying To Wear Armor",
     "Chance that armor built for one race (dwarf, elf, gnome, half-elf, "
     "halfling or human) fits a character of another race."),
    ("cfh_ch00_combat_modifiers_for_darkness_and_blindness",
     "**Combat Modifiers for Darkness and Blindness**",
     "Melee and missile attack penalties for fog, rain, snow, twilight and "
     "darkness, and the bonus for characters with infravision."),
    ("cfh_ch00_martial_arts_results", "**Martial Arts Results Table**",
     "Results of a martial arts attack by attack roll: the maneuver (punch, "
     "kick, bash…), its damage and the chance of a knockout."),
    ("cfh_ch00_one_handed_or_two_handed_weapons", "| Item | Cost",
     "Harpoon, javelin, spear, long spear and trident used one-handed or "
     "two-handed: cost, weight, size, type, speed factor and damage."),
    ("cfh_ch00_piecemeal_armor", "|  | Bonus to AC Per Type of Piece:",
     "Armor Class bonus of each piece of armor (breast plate, arms, legs) "
     "compared to the full suit, for each armor type."),
    ("cbh_ch07_fundamentals_of_music", "Accent: To stress or emphasize",
     "Glossary of musical terms for bards, from accent, beat and dynamics to "
     "tempo, tone and voice range."),
    ("watw_ch04_new_nonweapon_proficiencies", "**New Nonweapon Proficiencies**",
     "New nonweapon proficiencies: Psychic Defense (general); Crystal Focus, "
     "Power Manipulation and Psionic Lore (psionicist); Information Gathering "
     "(rogue). Slots, ability and modifier of each."),
]

# Terceira leva: regras que são só a imagem de uma ficha em branco do livro.
# Resumo e texto eram o código de imagem da wiki ("File:….png|thumb|…"), sem a
# imagem. Os dois viram uma frase dizendo o que a ficha é.
# (id da regra, começo do texto antigo, frase nova).
SHEETS = [
    ("cbarbh_ch08_barbarian_character_record_sheets", "File:Barbarian Fighter Record Sheet.png",
     "Blank record sheets for barbarian characters (fighter and shaman, with a "
     "second page). The sheets are images in the book and are not reproduced "
     "here."),
    ("cbarbh_ch08_barbarian_kit_sheet", "File:Barbarian Humanoid Character Kit Design Sheet.png",
     "Blank sheet for designing a barbarian or humanoid character kit. The sheet "
     "is an image in the book and is not reproduced here."),
    ("cpah_ch10_paladin_character_record_sheets", "File:Paladin Character Record Sheet 1.png",
     "Blank record sheets for paladin characters (three pages). The sheets are "
     "images in the book and are not reproduced here."),
    ("cpah_ch10_paladin_kit_sheet", "File:Paladin Kit Sheet.png",
     "Blank sheet for recording a paladin kit. The sheet is an image in the "
     "book and is not reproduced here."),
    ("cbh_ch10_bard_character_record_sheet", "File:Bard Character Record Sheet 1 (CBH).png",
     "Blank record sheets for bard characters (three pages). The sheets are "
     "images in the book and are not reproduced here."),
    ("cbh_ch10_bard_kit_record_sheet", "File:Bard Kit Record Sheet (CBH).png",
     "Blank sheet for recording a bard kit. The sheet is an image in the book "
     "and is not reproduced here."),
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
    for rule_id, old_start, new in SHEETS:
        rule = by_id.get(rule_id)
        if rule is None:
            raise SystemExit(f"regra não encontrada: {rule_id}")
        if rule["summary"] == new and rule["content"] == new:
            continue
        if not rule["content"].startswith(old_start):
            raise SystemExit(f"{rule_id}: texto inesperado: {rule['content'][:60]!r}")
        rule["summary"] = new
        rule["content"] = new
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
