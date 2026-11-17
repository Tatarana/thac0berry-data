#!/usr/bin/env python3
"""Acrescenta a data/weapons.json as armas fora do PHB que os kits citam.

2026-11-17: os kits curados (scripts/curate_kit_proficiencies.py) citam Katana, Cutlass,
Ninja-to, Gythka... que não existiam no compêndio, então os apps não as ofereciam.
`scripts/kit_weapons.json` traz os números das tabelas dos livros (CFH cap. 5, CNH tab. 24,
CBarbH tab. 41, CRH tab. 58, Dark Sun tab. 30, Thri-Kreen of Athas tab. 3.2, Player's
Option: Combat & Tactics, Arms and Equipment Guide, Dragon Magazine). Nada inventado:
campo que o livro não imprime fica null. `source` = sigla do books.json (ou o título),
`campaignSetting` = mundo da arma (null = qualquer).

Idempotente: troca os registros de mesmo id.
Uso:  python scripts/add_kit_weapons.py [--dry-run]
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
WEAPONS = os.path.join(ROOT, "data", "weapons.json")
NEW = os.path.join(ROOT, "scripts", "kit_weapons.json")


def main():
    weapons = json.load(open(WEAPONS, encoding="utf-8"))
    new = json.load(open(NEW, encoding="utf-8"))
    ids = {w["id"] for w in new}
    kept = [w for w in weapons if w["id"] not in ids]
    names = {w["name"] for w in kept}
    clash = [w["name"] for w in new if w["name"] in names]
    if clash:
        sys.exit(f"nomes já existentes: {clash}")
    out = kept + new
    print(f"{len(kept)} armas + {len(new)} dos kits = {len(out)}")
    if "--dry-run" not in sys.argv:
        with open(WEAPONS, "w", encoding="utf-8", newline="\n") as f:
            # mesmo formato do arquivo: uma linha, sem quebra no fim
            json.dump(out, f, ensure_ascii=False)


if __name__ == "__main__":
    main()
