#!/usr/bin/env python3
"""Corrige erros de OCR no texto das regras (data/rules.json).

Cada correção é explícita: regra, trecho errado (como palavra inteira) e o
certo. Achados no uso (2026-10-08, ficha "Psionic Combat" do Dark Sun):
"MTHACO"/"THACOs" com a letra O no lugar do zero. MTHAC0 (Mental THAC0) e
MAC (Mental Armor Class) são termos do Dark Sun e ficam como estão.

Rodar de novo não muda nada (o trecho errado já não existe).

Uso:  python scripts/fix_rules_ocr.py [--dry-run]
"""
import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RULES = os.path.join(ROOT, "data", "rules.json")

# (id da regra, errado, certo): o errado é trocado como palavra inteira, no `content`.
FIXES = [
    # Dark Sun, Psionic Combat: "MTHACO roll", "MTHACO bonuses", "Table 2: MTHACO Modifiers".
    ("dsc_ch00_psionic_combat", "MTHACO", "MTHAC0"),
    # "Table 4: THACOs and MTHACOs".
    ("dsc_ch00_psionic_combat", "THACOs", "THAC0s"),
    ("dsc_ch00_psionic_combat", "MTHACOs", "MTHAC0s"),
]


def main():
    dry = "--dry-run" in sys.argv
    with open(RULES, encoding="utf-8") as f:
        rules = json.load(f)
    by_id = {rule["id"]: rule for rule in rules}
    total = 0
    for rule_id, wrong, right in FIXES:
        rule = by_id.get(rule_id)
        if rule is None:
            raise SystemExit(f"regra não encontrada: {rule_id}")
        pattern = re.compile(rf"\b{re.escape(wrong)}\b")
        rule["content"], n = pattern.subn(right, rule["content"])
        total += n
        print(f"{rule_id}: {wrong} -> {right}: {n}")
    if dry or total == 0:
        print("(nada gravado)" if dry else "(nada a corrigir)")
        return
    with open(RULES, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rules, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
