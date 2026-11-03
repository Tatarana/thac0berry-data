"""
Preço e peso das armas (PHB, Table 44 "Weapons", em data/rules.json) em
data/weapons.json, para a etapa de equipamento do The Forge (web,
2026-11-02). Campos novos, opcionais, no padrão de armor.json:

  cost         "15 gp" (texto do livro; "—" quando o livro não cobra nada)
  weight       "4 lbs."
  ammunition   nas armas de disparo: { name, cost, quantity, weight }
               ("Long bow (Flight arrow)": a flecha, 3 sp por 12)

Armas que não estão na tabela do PHB (Bill, Lasso, Maul, Net, Nunchaku,
Scythe) ficam sem preço.

Uso:
    python scripts/add_weapon_costs.py           # só mostra
    python scripts/add_weapon_costs.py --write   # grava data/weapons.json
"""

import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
WEAPONS = os.path.join(ROOT, 'data', 'weapons.json')
RULES = os.path.join(ROOT, 'data', 'rules.json')


def phb_rows():
    rules = json.load(open(RULES, encoding='utf-8'))
    entries = rules if isinstance(rules, list) else next(v for v in rules.values() if isinstance(v, list))
    for r in entries:
        if r.get('book') != 'PHB':
            continue
        for t in r.get('tables', []):
            if t.get('title') == 'Weapons' and 'Cost' in t.get('headers', []):
                return t['rows']
    raise SystemExit('Table 44 (Weapons) não encontrada em rules.json')


def clean(name):
    return re.sub(r'\s+\d+$', '', name).strip()


def cost_text(text):
    text = text.strip().rstrip('.')
    return '—' if text in ('—', '-', '') else text


def weight_text(text):
    text = text.strip()
    if text in ('*', '—', '-', ''):
        return None
    return f'{text} lbs.'


def build_index():
    """Nome da linha (com o grupo, quando a linha é uma variante) → linha."""
    index = {}
    group = None
    for row in phb_rows():
        name, cost, weight = clean(row[0]), row[1], row[2]
        if cost == '—' and weight == '—':
            group = name
            continue
        index[name.lower()] = row
        if group:
            index[f'{group} {name}'.lower()] = row
    return index


# Nomes de weapons.json que a tabela escreve diferente.
ALIASES = {
    'two-handed sword': 'two-hand. sword',
    'bastard sword (one-handed grip)': 'bastard sword one-handed',
    'bastard sword (two-handed grip)': 'bastard sword two-handed',
}
# Munição: o nome entre parênteses → a linha da tabela.
AMMO = {
    'flight arrow': 'flight arrow',
    'sheaf arrow': 'sheaf arrow',
    'hand quarrel': 'hand quarrel',
    'heavy quarrel': 'heavy quarrel',
    'light quarrel': 'light quarrel',
    'bullet': 'sling bullet',
    'stone': 'sling stone',
}


def ammo_price(text):
    """'3sp/12' → ('3 sp', 12); '1 cp.' → ('1 cp', 1)."""
    text = text.replace(' ', '').rstrip('.')
    if text in ('—', '-', ''):
        return '—', 1
    m = re.match(r'(\d+)(gp|sp|cp)(?:/(\d+))?$', text)
    if not m:
        return text, 1
    return f'{m.group(1)} {m.group(2)}', int(m.group(3) or 1)


def main():
    write = '--write' in sys.argv
    index = build_index()
    weapons = json.load(open(WEAPONS, encoding='utf-8'))
    missing = []
    changed = 0
    for w in weapons:
        name = w['name']
        base, ammo = name, None
        m = re.match(r'(.+?) \((.+)\)$', name)
        if m and m.group(2).lower() in AMMO:
            base, ammo = m.group(1), m.group(2)
        key = ALIASES.get(name.lower(), base.lower())
        row = index.get(key)
        if not row:
            missing.append(name)
            continue
        w['cost'] = cost_text(row[1])
        weight = weight_text(row[2])
        if weight:
            w['weight'] = weight
        if ammo:
            arow = index.get(AMMO[ammo.lower()])
            if arow:
                price, quantity = ammo_price(arow[1])
                w['ammunition'] = {'name': clean(arow[0]), 'cost': price, 'quantity': quantity, 'weight': weight_text(arow[2])}
        changed += 1
        print(f"{name}: {w['cost']}, {w.get('weight')}" + (f" · ammo {w['ammunition']}" if 'ammunition' in w else ''))
    print(f'\n{changed} armas com preço; sem preço no PHB: {missing}')
    if write:
        # Mesmo formato do arquivo: JSON compacto, numa linha, sem quebra no fim.
        with open(WEAPONS, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(weapons, f, ensure_ascii=False)
        print('Gravado em', WEAPONS)


if __name__ == '__main__':
    main()
