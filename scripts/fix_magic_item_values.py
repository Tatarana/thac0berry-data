#!/usr/bin/env python3
"""Corrige xpValue/goldValue errados dos itens mágicos (data/magic_*.json).

Problema (achado em 2026-10-05): o conversor original guardava como valor o
PRIMEIRO número do texto bruto. Em itens com várias versões isso virava o
rótulo da versão, não um preço: Ring of Protection ficava com 1 xp / 1 gp
("+1: 1,000 xp +2: 2,000 xp…"); Aquatic Armor com 25 ("-25% xp"); Bracer of
Defense com 2 ("AC 2: 4,000 xp…").

Regra, por par (xpValue/rawXP e goldValue/rawValue):
  - MANTÉM o número se ele é um preço que aparece no texto bruto ("N xp" /
    "N gp"; ou, se o texto não traz a unidade, se ele é o único número do
    texto). Isso inclui itens com várias versões em que o número é o preço
    da primeira versão: não está errado, e a ficha mostra o texto completo.
  - ANULA o número (null) quando ele não é nenhum preço do texto: aí era
    rótulo de versão, porcentagem ou lixo de conversão, e os apps passam a
    mostrar o texto bruto.
O texto bruto nunca é alterado; número que já é null fica como está.

Uso:  python scripts/fix_magic_item_values.py [--dry-run]
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
AMOUNT = {"xp": re.compile(r"(\d[\d,]*)\s*xp\b", re.I), "gp": re.compile(r"(\d[\d,]*)\s*gp\b", re.I)}
NUMBER = re.compile(r"\d[\d,]*")


def as_int(text):
    digits = text.replace(",", "")
    return int(digits) if digits else None


def is_real_price(value, raw, unit):
    raw = raw or ""
    amounts = [as_int(a) for a in AMOUNT[unit].findall(raw)]
    if amounts:
        return value in amounts
    numbers = [n for n in (as_int(t) for t in NUMBER.findall(raw)) if n is not None]
    return numbers == [value]


def main():
    dry = "--dry-run" in sys.argv
    changed = {"xp": 0, "gp": 0}
    items_changed = set()
    examples = []
    for path in sorted(glob.glob(os.path.join(ROOT, "data", "magic_*.json"))):
        with open(path, encoding="utf-8") as f:
            original = f.read()
        items = json.loads(original)
        touched = False
        for item in items:
            e = item["economyAndXP"]
            for key, raw_key, unit in (("xpValue", "rawXP", "xp"), ("goldValue", "rawValue", "gp")):
                value = e.get(key)
                if value is None or is_real_price(value, e.get(raw_key), unit):
                    continue
                e[key] = None
                changed[unit] += 1
                items_changed.add(item["id"])
                touched = True
                if len(examples) < 10:
                    examples.append(f"{item['name']}: {key} {value} -> null   ({(e.get(raw_key) or '')[:60]})")
        if touched and not dry:
            # Mesmo formato do arquivo original (JSON compacto, UTF-8).
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(items, ensure_ascii=False, separators=(",", ":")))
    print(f"{'(simulação) ' if dry else ''}itens corrigidos: {len(items_changed)} "
          f"(xpValue anulados: {changed['xp']}, goldValue anulados: {changed['gp']})")
    for line in examples:
        print("  " + line)


if __name__ == "__main__":
    main()
