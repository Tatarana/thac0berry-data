#!/usr/bin/env python3
"""Corrige as proficiências bônus de kits cortadas nas vírgulas (data/kits.json).

Problema (achado em 2026-10-07, no teste de multiclasse da web): o conversor
original separou `mechanics.proficiencies.bonus` em TODAS as vírgulas,
inclusive as de dentro dos parênteses. "weaponsmithing (crude, CRH)" virou
"weaponsmithing (crude" + "CRH)", e os apps (web e iPad) acrescentam essas
linhas à ficha ao escolher o kit — o jogador ganhava uma proficiência "CRH)".

Regra: cada lista quebrada é trocada pelos nomes do compêndio
(data/proficiencies.json), na mesma ordem; o resto da lista fica como está.
Só a lista `bonus` (a que entra na ficha); as `recommended` são só texto.

Uso:  python scripts/fix_kit_bonus_proficiencies.py [--dry-run]
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
KITS = os.path.join(ROOT, "data", "kits.json")
PROFICIENCIES = os.path.join(ROOT, "data", "proficiencies.json")

# kit id -> (pedaços quebrados, na ordem) -> nome do compêndio
FIXES = {
    "barbarian_arctic_dwarf": [(["weaponsmithing (crude", "CRH)"], "Weaponsmithing, Crude")],
    "advisor_imperial_fleet": [(["heraldry (space", "CSH)"], "Heraldry, Space")],
    "exile_gray_dwarf": [(["survival (Underdark", "CTH)"], "Survival, Underground")],
    "ironsmith_wandering": [
        (["Blacksmithing", "see below)"], "Blacksmithing"),
        (["languages (racial tongue", "male shield dwarves only)"], "Languages, Modern"),
    ],
}


def replace_run(items, run, name):
    for i in range(len(items) - len(run) + 1):
        if items[i : i + len(run)] == run:
            return items[:i] + [name] + items[i + len(run) :]
    if name in items:
        return items  # já corrigido (rodar de novo não muda nada)
    raise SystemExit(f"pedaços não encontrados: {run}")


def main():
    dry = "--dry-run" in sys.argv
    with open(KITS, encoding="utf-8") as f:
        kits = json.load(f)
    with open(PROFICIENCIES, encoding="utf-8") as f:
        names = {p["name"] for p in json.load(f)}
    by_id = {k["id"]: k for k in kits}
    for kit_id, fixes in FIXES.items():
        bonus = by_id[kit_id]["mechanics"]["proficiencies"]["bonus"]
        before = list(bonus)
        for run, name in fixes:
            if name not in names:
                raise SystemExit(f"{name} não existe em proficiencies.json")
            bonus = replace_run(bonus, run, name)
        by_id[kit_id]["mechanics"]["proficiencies"]["bonus"] = bonus
        print(f"{kit_id}:\n  antes:  {before}\n  depois: {bonus}")
    if dry:
        print("(dry-run: nada gravado)")
        return
    with open(KITS, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(kits, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
