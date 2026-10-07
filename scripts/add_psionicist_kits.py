#!/usr/bin/env python3
"""Kits de Psionicist (2026-10-06, pedido do usuário).

Traz os kits com classGroup "Psionicist" do repo de mineração
(thac0berry-data-mining/data/character_kits) para data/kits.json:

- campaign_and_dragon_kits.json, demihuman_and_humanoid_kits.json e
  priest_kits.json (os outros arquivos de kits não têm nenhum);
- o "sensei" já existia aqui cadastrado como kit de clérigo, com o texto do
  Sensei psiônico de The Will and the Way. Decisão do usuário: corrigir o
  registro existente mantendo o id (ids são contrato);
- ambientação: Dark Sun para The Will and the Way e Elves of Athas, Council of
  Wyrms para o livro dele; os da Dragon Magazine ficam sem setting.

Idempotente: rodar de novo substitui os kits de Psionicist pela versão minerada.

Uso: python scripts/add_psionicist_kits.py [--mining CAMINHO]
"""
import argparse
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ['campaign_and_dragon_kits.json', 'demihuman_and_humanoid_kits.json', 'priest_kits.json']
SETTING_BY_SOURCE = {
    'The Will and the Way': 'Dark Sun',
    'Elves of Athas': 'Dark Sun',
    'Council of Wyrms': 'Council of Wyrms',
}


ARMOR_AS_CLASS = {'allowedTypes': 'as_class', 'shieldsAllowed': 'as_class', 'metalAllowed': True, 'maxArmorClass': None, 'notes': ''}
NO_TURNING = {'capable': False, 'mode': 'not_applicable', 'notes': "Psionicist kits don't turn undead — that's a priest class feature."}


# Proficiências bônus (2026-10-06, pedido do usuário): os kits minerados só as
# têm no texto de `features.nonweaponProficiencies`, com notas de rodapé e
# escolhas ("X or Y"). Lista revisada à mão, com os nomes do compêndio
# (proficiencies.json, em minúsculas como nos outros kits). Escolhas e itens que
# não são proficiências do compêndio vão para `proficiencies.notes`.
BONUS = {
    'sensei': ['rejuvenation', 'tumbling'],
    'ascetic_warrior': ['reading/writing'],
    'auditor': ['disguise', 'information gathering'],
    'beastmaster_psionic': ['animal handling', 'animal lore', 'animal training'],
    'charcoal_burner': ['fire-building'],
    'dowser': ['water divining'],
    'dragon_psionicist': ['psioncraft'],
    'empath': ['body language'],
    'gatekeeper': ['alertness'],
    'healer_dragon': ['healing'],
    'mercenary_psionicist': ['riding, land-based'],
    'mind_mage': ['feign magic'],
    'mind_monk': ['religion'],
    'noble_dragon': ['etiquette', 'heraldry'],
    'noble_psionicist': ['etiquette', 'heraldry'],
    'paranaturalist': ['ancient history', 'reading/writing'],
    'psychic_surgeon': ['hypnosis'],
    'spiritualist_psionic': ['seance'],
    'the_voice': ['languages, modern'],
    'thought_agent': ['observation', 'information gathering'],
    'tribal_psionicist': ['weather sense', 'fire-building', 'survival'],
    'untutored_one': ['rejuvenation', 'endurance'],
    'brown_elf': ['meditative focus', 'psionic detection'],
    'psiologist': ['harness subconscious', 'rejuvenation'],
}
BONUS_NOTES = {
    'berranie_seer_seeress': 'Bonus: Animal Handling or Riding, Land-Based (choose one).',
    'mercenary_psionicist': 'Bonus: also Direction Sense or Heraldry (choose one).',
    'dragon_psionicist': 'Bonus: also a racial language and the racial bonus (see Council of Wyrms, Chapter 2).',
    'the_voice': 'Bonus: Languages, Modern covers any two modern languages.',
}


def summary_from_text(full_text, limit=260):
    """Resumo a partir do texto completo (2026-10-07, pedido do usuário): os kits
    da Dragon Magazine vieram com o aviso da wiki (":*This was originally
    published in Dragon Magazine #...*") no lugar do resumo. Usa o primeiro
    parágrafo de verdade (pula avisos ":" e títulos "#"), preferindo o rotulado
    "Description" (ou "Description and Role"), sem o rótulo e sem marcação,
    cortado em frases até ~260 caracteres."""
    paras = [p.strip() for p in full_text.split('\n\n')]
    paras = [p for p in paras if p and not p.startswith(':') and not p.startswith('#')]
    paras.sort(key=lambda p: 0 if p.startswith('**Description') else 1)
    for para in paras:
        para = re.sub(r'^\*\*Description[^*]*:\*\*\s*', '', para)
        para = re.sub(r'\*+', '', para).replace('\n', ' ').strip()
        sentences = re.split(r'(?<=[.!?])\s+', para)
        out = ''
        for s in sentences:
            if out and len(out) + 1 + len(s) > limit:
                break
            out = f'{out} {s}'.strip()
        return out
    return ''


def normalize(kit):
    """Os kits minerados usam um formato de `mechanics` mais antigo; completa os
    campos que o app exige (Models/Kit.swift) com os mesmos padrões dos kits que
    já estão aqui. `requirements.alignment` veio null em todos (o alinhamento
    está no texto de `features.requirements`)."""
    mech = kit['mechanics']
    mech.setdefault('armor', dict(ARMOR_AS_CLASS))
    mech.setdefault('turnUndead', dict(NO_TURNING))
    req = mech['requirements']
    legacy = req.pop('alignment', None)
    req.setdefault('alignments', [legacy] if isinstance(legacy, str) and legacy else (legacy if isinstance(legacy, list) else []))
    weapons = mech['weapons']
    for key in ('required', 'recommended', 'forbidden'):
        weapons.setdefault(key, [])
    weapons.setdefault('notes', None)
    desc = kit['description']
    if desc['briefSummary'].lstrip().startswith(':*This was originally published'):
        desc['briefSummary'] = summary_from_text(desc['fullText'])
    profs = mech.setdefault('proficiencies', {'bonus': [], 'recommended': [], 'notes': None})
    if kit['id'] in BONUS:
        profs['bonus'] = list(BONUS[kit['id']])
    if kit['id'] in BONUS_NOTES:
        profs['notes'] = ' '.join(filter(None, [profs.get('notes'), BONUS_NOTES[kit['id']]]))
    return kit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mining', default=os.path.join(ROOT, '..', 'thac0berry-data-mining', 'data', 'character_kits'))
    args = parser.parse_args()

    mined = []
    for name in FILES:
        with open(os.path.join(args.mining, name), encoding='utf-8') as f:
            mined += [k for k in json.load(f) if k['classEligibility'].get('classGroup') == 'Psionicist']

    path = os.path.join(ROOT, 'data', 'kits.json')
    with open(path, encoding='utf-8') as f:
        kits = json.load(f)

    by_id = {k['id']: i for i, k in enumerate(kits)}
    added = replaced = 0
    for kit in mined:
        kit = normalize(json.loads(json.dumps(kit)))
        setting = SETTING_BY_SOURCE.get(kit['sourceBook'])
        if setting:
            kit['setting'] = setting
        if kit['id'] in by_id:
            kits[by_id[kit['id']]] = kit
            replaced += 1
        else:
            by_id[kit['id']] = len(kits)
            kits.append(kit)
            added += 1

    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(kits, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(f'{len(mined)} kits de Psionicist: {added} novos, {replaced} substituídos; kits.json tem {len(kits)}')


if __name__ == '__main__':
    main()
