# thac0berry-data

Dados de referência do THAC0berry (AD&D 2ª edição): magias, kits, proficiências,
divindades, regras, armas, armaduras, itens mágicos e comuns, poderes psiônicos e as
tabelas de THAC0, jogadas de proteção e experiência. Também guarda o contrato desses
dados (JSON Schema).

É a **fonte única** desses dados para os três projetos:

| Repo | Como usa |
|---|---|
| [`thac0berry-ipad`](https://github.com/Tatarana/thac0berry-ipad) | Copia `data/*.json` para `THAC0berry.swiftpm/Resources/` (o Swift Playgrounds precisa dos arquivos dentro do projeto). O CI de lá acusa se a cópia divergir daqui. |
| [`thac0berry-web`](https://github.com/Tatarana/thac0berry-web) | Lê os JSON no build ou serve como arquivos estáticos |
| [`thac0berry-backend`](https://github.com/Tatarana/thac0berry-backend) | Só se alguma regra no servidor precisar deles |

## Estrutura

```
data/                  42 arquivos JSON (UTF-8)
schemas/               JSON Schema de cada arquivo + README com o mapeamento
scripts/
  validate_schemas.py  valida data/ contra schemas/
  build_races.py       gera data/races.json e docs/racas-divergencias-2026-11.md (mineração + race_curation.json)
  add_mined_rulebooks.py      regras de CBE, CWH, CBN e TOM (vêm de ../thac0berry-data-mining)
  add_elf_and_misc_kits.py    30 kits curados à mão (CBE e livros menores)
  add_dragon_magazine_kits.py 119 kits da Dragon Magazine
```

## Validar

```bash
pip install jsonschema
python scripts/validate_schemas.py
```

O CI roda a mesma validação a cada push.

## Regras

- **Ids são contrato.** Fichas salvas apontam para magias, kits, itens e proficiências
  por `id`. Nunca renomeie nem reaproveite um id. Para retirar um registro, avise
  antes: as fichas que apontam para ele perdem o vínculo.
- **Mudou o formato → mude o schema na mesma entrega**, e o modelo Swift no repo do
  iPad. Detalhes em [`schemas/README.md`](schemas/README.md).
- Os dados vêm de fontes de AD&D 2e convertidas por scripts. Confira os valores contra
  os livros antes de usar em mesa.

## Kits importados da mineração (2026-11-16)

Os três scripts `add_*` são idempotentes (trocam os registros que criaram, mesmos ids) e
leem `../thac0berry-data-mining/data`.

- **Grupo `Demihuman`** (subclass = raça: Elf, Half-Elf, Dwarf, Avariel), com `mechanics.requirements.races`.
- **`classEligibility.combination`** (opcional): kit de multiclasse, ex. Spellarcher = `[Fighter, Mage]`.
  O app mostra o kit a quem tem qualquer uma das classes e só avisa se a ficha não é essa multiclasse.
- **CBE, CWH, CBN, TOM**: 202 regras em `rules.json` e 4 livros em `books.json`.
- **Kits da Dragon Magazine** (`sourceBook` = "Dragon Magazine #N"): a classe vem do título da
  seção da própria página ("Fighter/Mage kit") ou de uma tabela manual no script, nunca do
  `classGroup` minerado, que estava errado em muitos kits (Sohei, Fiend Slayer, Earthstoker...).
  `mechanics` sai quase vazio: requisitos de atributo, proficiências bônus e slots ficam só no
  texto (`features`). `startingCash` só com fórmula de dados e moeda gp/cp/sp explícita.
  Fora (19, lista em `EXCLUDED` e `MANUAL`): 6 do Masque of the Red Death (classes próprias),
  kits de dragão e 9 com classe ambígua (Zande Witch Woman, Tribal Scout, Mystery Man, Sarkany,
  Alakvalt, Boszorkany, Courier, Kshatriya, Manikin).
- Nomes de kit precisam ser únicos (a ficha guarda o kit pelo nome). Já existe um duplicado:
  "Forester" (ids `forester` e `forester_the_complete`).

## Proficiências e armas dos kits (2026-11-17)

`scripts/curate_kit_proficiencies.py` aplica `scripts/kit_proficiency_curation.json`: os 506
kits lidos um a um do texto do livro, com nomes do compêndio (`proficiencies.json`; armas do
PHB por `weapons.json`, as de fora em maiúscula: Ninja-to, Katana, Cutlass...). O arquivo de
curadoria guarda também `doubts` e `unmatched` (nomes sem entrada no compêndio), que o script
não grava. Para corrigir um kit: edite a curadoria e rode o script de novo.

Campos novos (opcionais, ausentes quando vazios):
- `proficiencies.bonusChoices`: de cada lista o jogador ganha uma, de graça ("Hunting or Fishing").
- `proficiencies.required` / `requiredChoices`: o kit obriga a tomar (gasta slots).
- `proficiencies.forbidden`: o kit proíbe (os apps só avisam, não bloqueiam).
- `weapons.requiredChoices`: arma obrigatória com escolha ("sickle or scythe").
- `weapons.allowed`: as únicas armas do kit. Alguns kits limitam só as armas iniciais (ver
  `doubts` na curadoria); por isso os apps tratam como aviso.
- `weapons.specialization`: `{weapons, mustSpecialize, othersForbidden}` (Spellarcher: arco
  longo, obrigatório, nenhuma outra). `weapons: []` + `othersForbidden` = não especializa.

### Armas dos kits e slots de perícia (2026-11-17)

- `scripts/add_kit_weapons.py` acrescenta a `weapons.json` as 48 armas fora do PHB citadas
  pelos kits (`scripts/kit_weapons.json`: CFH, CNH, CBarbH, CRH, Dark Sun, Thri-Kreen,
  Combat & Tactics, Arms and Equipment Guide, Dragon). `source` = sigla do livro (PO:C&T = Combat & Tactics, AEG = Arms and Equipment Guide);
  `campaignSetting` (novo, opcional) = mundo da arma. Sem número no livro: null, nunca inventado.
  Sem fonte nenhuma: Framea, Garrote, Razor, Rumal, Stone hammer, Throwing hammer, Small pick.
- `mechanics.nonweaponSlots` (novo, opcional, `{initial, bonus, perLevels, notes}`): só os 32
  kits que fogem do padrão da classe (`scripts/kit_nonweapon_slots.json`, aplicado por
  `curate_kit_proficiencies.py`). `initial` troca o número inicial da classe, `bonus` soma,
  `perLevels` = um slot novo a cada N níveis.
- Perícias citadas com outro nome viraram as do compêndio (Spellcasting = Spellcraft,
  Acrobatics = Tumbling, Small boat use = Boating...). Sem regra em fonte nenhuma, ficam só no
  texto: Thieves' Cant, Climbing, Baking, Path Lore, Planes Lore, Spellweaving, Teaching.

## Raças em dados (2026-11-20)

`data/races.json` (schema `race.schema.json`, só a web lê por enquanto): 159 raças, 83 jogáveis.
Gerado por `scripts/build_races.py` a partir de `../thac0berry-data-mining/data/player_races`
(157 registros) e da curadoria `scripts/race_curation.json`. Para mudar uma raça, edite a
curadoria e rode o script de novo (não edite o JSON à mão).

- **As 17 raças que o app web tinha em código** (6 do PHB, 10 planares, Half-Vistani) vêm da
  curadoria com os valores do app (PHB Tabela 7, Planewalker's Handbook, Domains of Dread): são a
  verdade. A mineração só empresta textos. Onde ela discorda, nada é trocado e a diferença vai
  para [`docs/racas-divergencias-2026-11.md`](docs/racas-divergencias-2026-11.md), que o script
  regenera junto com o JSON.
- `name` é o texto que a ficha grava no campo Raça (não muda para as 17); `id` é estável
  (`human`, `bariaur_male`, `genasi_fire`, `modron`…; as demais usam o id minerado).
- `playable: false` + `hiddenReason`: 30 humanoides do Complete Book of Humanoids, raças de
  cenários que não estão no Forge (Dragonlance, Kara-Tur, Savage Coast, Celts, Vikings), 2
  duplicatas e as "para decisão" (Dragon Magazine sem cenário claro). O cenário real fica em
  `campaignSetting`. Council of Wyrms (22 dragões) e Spelljammer (9) são jogáveis no dado, mas o
  cenário está em construção na web, então o filtro as esconde.
- Subraças têm `baseRace` (id de uma das 6 raças do PHB). Regras só vêm da raça-base quando o
  texto da subraça traz "Standard <Raça> Abilities" (`inheritsFromBase` lista o que foi
  copiado). Limites de nível, requisitos, ajustes e combinações são sempre os da própria raça.
- `classLevelLimits` e `classCombinations` guardam todas as classes da mineração (nomes
  normalizados: Wizard = Mage); o app só usa as 12 classes que tem.
- Duplicatas da mineração: Hill Dwarf (cópia escondida), Aquatic Elf (CBE `aquatic_elf`; Sea of
  Fallen Stars `aquatic_elf_sea_of_fallen_stars`), Kender (CBGH e Monstrous Compendium),
  Athasian Halfling (Dark Sun vale; a do CBGH fica escondida).
- O `sync_data.py` do iPad copia `races.json` junto com os outros arquivos do primeiro nível de
  `data/` (o app não o lê; o CI de lá acusa a divergência até rodar o sync).

