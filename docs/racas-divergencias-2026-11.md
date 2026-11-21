# Raças em dados: divergências e raças escondidas (2026-11-20)

Gerado por `scripts/build_races.py` (não edite à mão: mude `scripts/race_curation.json` e rode o script).

## Resumo

- `data/races.json`: **159** raças: as 157 mineradas, com o Bariaur dividido por sexo (+1) e o Half-Vistani, que só existe no app (+1).
- As **17 raças que o app já tinha** (6 do PHB, 10 planares, Half-Vistani) mantêm os valores do app; a mineração só empresta textos (livro, página, visão, idiomas, `content`).

### Jogáveis por cenário (o que aparece no Forge quando o cenário está ligado)

| Grupo | Raças | Quantas |
|---|---|---|
| Player's Handbook | Human, Dwarf, Elf, Gnome, Half-Elf, Halfling | 6 |
| Subraces | Aquatic Elf, Drow, Grey Elf, High Elf, Sylvan Elf, Deep Dwarf, Duergar, Hill Dwarf, Mountain Dwarf, Sundered Dwarf, Forest Gnome, Rock Gnome, Svirfneblin, Furchin, Hairfoot Halfling, Stout Halfling, Tallfellow Halfling | 17 |
| Council of Wyrms | Amethyst Dragon, Black Dragon, Blue Dragon, Brass Dragon, Bronze Dragon, Cloud Dragon, Copper Dragon, Crystal Dragon, Deep Dragon, Emerald Dragon, Gold Dragon, Green Dragon, Mercury Dragon, Mist Dragon, Red Dragon, Sapphire Dragon, Shadow Dragon, Silver Dragon, Steel Dragon, Topaz Dragon, White Dragon, Yellow Dragon | 22 |
| Dark Sun | Athasian Human, Athasian Elf, Athasian Dwarf, Athasian Half-Elf, Athasian Halfling, Athasian Aarakocra, Half-Giant, Mul, Pterran, Thri-Kreen | 10 |
| Forgotten Realms | Aquatic Elf (Sea of Fallen Stars), Aquatic Half-Elf, Noble Malenti, Shalarin, Triton | 5 |
| Greyhawk | Half-Greyhawk Dragon | 1 |
| Planescape | Aasimar, Bariaur (male), Bariaur (female), Genasi (air), Genasi (earth), Genasi (fire), Genasi (water), Githzerai, Modron, Tiefling, Nathri, Nethling | 12 |
| Ravenloft | Half-Vistani | 1 |
| Spelljammer | Dracon, Giff, Gromman, Hadozee, Hurwaet, Lizard Man (Spelljammer), Rastipede, Scro, Xixchil | 9 |

`Council of Wyrms` (22 dragões) e `Spelljammer` (9 raças do Spacefarer's Handbook) estão como jogáveis no dado, mas o cenário está em construção (`settingsUnderConstruction` na web): nenhum seletor mostra essas raças enquanto isso valer.

## Divergências: mineração × valores do app

Decisão do usuário: os valores do app são a verdade; nenhum foi trocado. A coluna "Fonte provável" diz de onde veio o valor do app.
Só entram as classes do app nos limites e as combinações com classes do app; o dado completo da mineração segue em `races.json` nos campos `*Text`.

| Raça | Campo | Mineração | App (mantido) | Fonte provável do valor do app |
|---|---|---|---|---|
| Human | nome | Human (Standard) | Human (nome gravado na ficha) | PHB Table 7 |
| Dwarf | limites de nível (classes do app) | Cleric 10, Fighter 15, Thief 12 | Cleric 10, Fighter 15, Thief 12, Ninja unlimited, Psionicist 8 | PHB Table 7; Ninja = CNH, Psionicist = CPsiH Table 1 |
| Dwarf | combinações de classe | Cleric/Fighter, Fighter/Thief | Cleric/Fighter, Fighter/Psionicist, Fighter/Thief, Psionicist/Thief | PHB Table 7 |
| Elf | limites de nível (classes do app) | Cleric 12, Fighter 12, Mage 15, Thief 12, Ranger 15 | Cleric 12, Fighter 12, Mage 15, Ranger 15, Thief 12, Psionicist 7 | PHB Table 7; Psionicist = CPsiH Table 1 |
| Gnome | limites de nível (classes do app) | Fighter 11, Thief 13, Cleric 9 | Cleric 9, Fighter 11, Thief 13, Psionicist 9 | PHB Table 7; Psionicist = CPsiH Table 1 |
| Half-Elf | nome | Half-Elf (PHB) | Half-Elf (nome gravado na ficha) | PHB Table 7 |
| Half-Elf | limites de nível (classes do app) | Bard unlimited, Cleric 14, Druid 9, Fighter 14, Mage 12, Ranger 16, Thief 12 | Bard unlimited, Cleric 14, Druid 9, Fighter 14, Mage 12, Ranger 16, Thief 12, Psionicist 7, Gypsy unlimited | PHB Table 7; Psionicist = CPsiH Table 1, Gypsy = Domains of Dread |
| Half-Elf | combinações de classe | Cleric/Fighter, Cleric/Fighter/Mage, Cleric/Mage, Cleric/Ranger, Druid/Fighter, Druid/Fighter/Mage, Druid/Mage, Druid/Ranger, Fighter/Mage, Fighter/Mage/Thief, Fighter/Thief, Mage/Thief | Cleric/Fighter, Cleric/Fighter/Mage, Cleric/Mage, Cleric/Ranger, Druid/Fighter, Druid/Fighter/Mage, Druid/Mage, Druid/Ranger, Fighter/Mage, Fighter/Thief, Mage/Thief | PHB Table 7 |
| Halfling | limites de nível (classes do app) | Cleric 8, Fighter 9, Thief 15 | Cleric 8, Fighter 9, Thief 15, Ninja unlimited, Psionicist 10 | PHB Table 7; Ninja = CNH, Psionicist = CPsiH Table 1 |
| Halfling | combinações de classe | Fighter/Thief | Fighter/Psionicist, Fighter/Thief, Psionicist/Thief | PHB Table 7 |
| Aasimar | combinações de classe | Bard/Fighter, Bard/Mage, Fighter/Mage, Mage/Ranger, Mage/Thief | Bard/Cleric, Bard/Fighter, Bard/Mage, Cleric/Fighter, Cleric/Mage, Cleric/Ranger, Fighter/Mage, Mage/Ranger, Mage/Thief | The Planewalker's Handbook |
| Bariaur (male) | ficha da raça | uma página só para os dois sexos (ajustes e limites misturados; requisitos de um sexo só) | uma raça por sexo (male) | The Planewalker's Handbook |
| Bariaur (male) | nome | Bariaur | Bariaur (male) (nome gravado na ficha) | The Planewalker's Handbook |
| Bariaur (male) | requisitos de atributo | STR 3/18, DEX 3/17, CON 5/18, INT 9/18, WIS 11/18, CHA 3/18 | STR 10/18, DEX 3/18, CON 11/18, INT 3/18, WIS 3/17, CHA 3/18 | The Planewalker's Handbook |
| Bariaur (female) | ficha da raça | uma página só para os dois sexos (ajustes e limites misturados; requisitos de um sexo só) | uma raça por sexo (female) | The Planewalker's Handbook |
| Bariaur (female) | nome | Bariaur | Bariaur (female) (nome gravado na ficha) | The Planewalker's Handbook |
| Genasi (air) | nome | Air Genasi (aka Wind Dukes) | Genasi (air) (nome gravado na ficha) | The Planewalker's Handbook |
| Genasi (earth) | nome | Earth Genasi (aka Stone Princes OR Stone Champions) | Genasi (earth) (nome gravado na ficha) | The Planewalker's Handbook |
| Genasi (fire) | nome | Fire Genasi (aka Flame Lords) | Genasi (fire) (nome gravado na ficha) | The Planewalker's Handbook |
| Genasi (water) | nome | Water Genasi (aka Sea Kings) | Genasi (water) (nome gravado na ficha) | The Planewalker's Handbook |
| Genasi (water) | combinações de classe | Fighter/Thief | Cleric/Fighter, Fighter/Thief | The Planewalker's Handbook |
| Modron | nome | Rogue Modron | Modron (nome gravado na ficha) | The Planewalker's Handbook |
| Tiefling | combinações de classe | Fighter/Mage, Fighter/Thief, Mage/Thief | Cleric/Fighter, Cleric/Thief, Fighter/Mage, Fighter/Thief, Mage/Thief | The Planewalker's Handbook |
| Half-Vistani | (toda a raça) | não existe na mineração | valores do app (Domains of Dread) | Domains of Dread |

Total: 24 divergências em 16 raças.

## Raças escondidas

`playable: false` + `hiddenReason`. Nunca aparecem no Forge nem na ficha; `matchRace` também não as reconhece (texto livre numa ficha continua texto livre).

### Humanoides não jogáveis (Complete Book of Humanoids) (30)

| Id | Nome | Origem | Observação |
|---|---|---|---|
| `aarakocra` | Aarakocra | The Complete Book of Humanoids: Aarakocra (CBOH) |  |
| `alaghi` | Alaghi | Complete Book of Humanoids Alaghi (CBOH) |  |
| `beastman` | Beastman | Complete Book of Humanoids Beastman (CBOH) |  |
| `bladeback_saurial` | Bladeback Saurial | Complete Book of Humanoids Saurial (CBOH) |  |
| `bugbear` | Bugbear | Complete Book of Humanoids Bugbear (CBOH) |  |
| `bullywug` | Bullywug | Complete Book of Humanoids: Bullywug, Advanced (CBOH) |  |
| `centaur` | Centaur | Complete Book of Humanoids Centaur (CBOH) |  |
| `finback_saurial` | Finback Saurial | Complete Book of Humanoids Saurial (CBOH) |  |
| `firbolg` | Firbolg | Complete Book of Humanoids Giant-kin, Firbolg (CBOH) Celts Campaign Sourcebook |  |
| `flind` | Flind | Complete Book of Humanoids Gnoll, Flind (CBOH) |  |
| `flyer_saurial` | Flyer Saurial | Complete Book of Humanoids Saurial (CBOH) |  |
| `fremlin` | Fremlin | Complete Book of Humanoids Fremlin (CBOH) |  |
| `gnoll` | Gnoll | Complete Book of Humanoids Gnoll (CBOH) |  |
| `goblin` | Goblin | Complete Book of Humanoids Goblin (CBOH) |  |
| `half_ogre` | Half-Ogre | Complete Book of Humanoids Ogre, Half-Ogre (CBOH) |  |
| `half_orc` | Half-Orc | Complete Book of Humanoids: Orc, Half-Orc (CBOH) |  |
| `hobgoblin` | Hobgoblin | Complete Book of Humanoids Hobgoblin (CBOH) |  |
| `hornhead_saurial` | Hornhead Saurial | Complete Book of Humanoids Saurial (CBOH) |  |
| `kobold` | Kobold | Complete Book of Humanoids: Kobold (CBOH) |  |
| `lizard_man_standard` | Lizard Man (Standard) | Complete Book of Humanoids: Lizard Man (CBOH) |  |
| `mongrelman` | Mongrelman | Complete Book of Humanoids Mongrelman (CBOH) |  |
| `ogre` | Ogre | Complete Book of Humanoids Ogre, Half-Ogre (CBOH) |  |
| `ogre_mage` | Ogre Mage | Complete Book of Humanoids Ogre Mage (CBOH) |  |
| `orc` | Orc | Complete Book of Humanoids: Orc, Half-Orc (CBOH) |  |
| `pixie` | Pixie | Complete Book of Humanoids Pixie (CBOH) |  |
| `satyr` | Satyr | Complete Book of Humanoids Satyr (CBOH) |  |
| `standard_minotaur` | Standard Minotaur | Complete Book of Humanoids: Minotaur (CBOH) |  |
| `swanmay` | Swanmay | Complete Book of Humanoids Swanmay (CBOH) |  |
| `voadkyn` | Voadkyn | Complete Book of Humanoids Giant-kin, Voadkyn (CBOH) |  |
| `wemic` | Wemic | Complete Book of Humanoids Wemic (CBOH) |  |

### Cenário que não está na lista do Forge (18)

- **Celts** (2): Fomorian, The Sidhe
- **Dragonlance** (8): Gully Dwarf, Tinker Gnome, Half-Elf (Krynn), Kender, Kender (Monstrous Compendium), Bakali, Krynn Minotaur, Silver Half-Dragon (Krynn)
- **Kara-Tur** (3): Half-Chiang Lung, Half-Shen Lung, Hengeyokai
- **Savage Coast** (4): Aranea, Lupin, Rakasta, Tortle
- **Vikings** (1): Trollborn

### Para decisão do usuário (sem cenário do Forge claro, ou sem regra utilizável no app) (26)

| Id | Nome | Origem | Observação |
|---|---|---|---|
| `avariel` | Avariel | Dragon Magazine #233: On Wings of Eagles (Article) |  |
| `snow_elf` | Snow Elf | In the Frost and the Snow (Article) - Dragon #155 |  |
| `bronze_half_dragon` | Bronze Half-Dragon | Dragon #206 |  |
| `crabman` | Crabman | Dragon Magazine #250: Crabman (Article Race) |  |
| `drow_dragon` | Drow-Dragon | Dragon #206 |  |
| `dryad` | Dryad | Dragon #251: Beyond the Tree (Article) |  |
| `gibberling` | Gibberling | Dragon #265: Gibberling (Article Race) |  |
| `gold_half_dragon` | Gold Half-Dragon | Dragon #206 |  |
| `grimlock` | Grimlock | Dragon #265: Primitive PCs (Article) |  |
| `iron_half_dragon` | Iron Half-Dragon | Dragon #206 |  |
| `koalinth` | Koalinth | Dragon Magazine #250: Koalinth (Article Race) |  |
| `liminal` | Liminal | Dragon Magazine #250: Liminal (Article Race) |  |
| `locathah` | Locathah | Dragon Magazine #250: Locathah (Article Race) |  |
| `malenti` | Malenti | Dragon Magazine #250: Malenti (Article Race) |  |
| `merfolk` | Merfolk | Dragon Magazine #250: Merfolk (Article Race) |  |
| `mold_man_vegepygmy` | Mold Man (Vegepygmy) | Dragon #265: Primitive PCs (Article) |  |
| `pahari` | Pahari | Dragon Magazine #250: Pahari (Article Race) |  |
| `quaggoth` | Quaggoth | Dragon #265: Primitive PCs (Article) |  |
| `selkie` | Selkie | Dragon Magazine #250: Selkie (Article Race) |  |
| `silver_half_dragon` | Silver Half-Dragon | Dragon #206 |  |
| `steel_half_dragon` | Steel Half-Dragon | Dragon #206 |  |
| `su_folk` | Su-folk | Dragon #265: Primitive PCs (Article) |  |
| `troglodyte` | Troglodyte | Dragon #265: Primitive PCs (Article) |  |
| `vodyanoi` | Vodyanoi | Dragon Magazine #250: Vodyanoi (Article Race) |  |
| `yeti` | Yeti | Dragon #265: Primitive PCs (Article) |  |
| `githyanki_outcast` | Githyanki Outcast | A Guide to the Astral Plane: Githyanki as Player Characters (GAP) | Só tem limites para Warlock, Githwarriors e gish (classes que o app não tem): todas as classes do app dariam aviso. |

### Registros duplicados (o id canônico fica jogável) (2)

| Id | Nome | Origem | Observação |
|---|---|---|---|
| `hill_dwarf_mountain_dwarves` | Hill Dwarf (duplicate entry) | The Complete Book of Dwarves: Hill Dwarves (CBD) | Mesmo conteúdo de Hill Dwarf; a página minerada se chama 'Mountain Dwarves', mas Mountain Dwarf já existe em mountain_dwarf. |
| `athasian_halfling_the_complete_book_of_gnomes_halflings` | Athasian Halfling (CBGH) | The Complete Book of Gnomes & Halflings: Athasian Halfling (CBGH) | Versão do Complete Book of Gnomes & Halflings; vale a do Dark Sun Campaign Setting (athasian_halfling). |

### Para decisão do usuário

Sem cenário do Forge claro no texto ou na fonte (artigos da Dragon Magazine e afins). Se alguma deve virar jogável, é só mudar `playable`/`campaignSetting` em `scripts/race_curation.json`:

- Avariel (`avariel`): Dragon Magazine #233: On Wings of Eagles (Article)
- Snow Elf (`snow_elf`): In the Frost and the Snow (Article) - Dragon #155
- Bronze Half-Dragon (`bronze_half_dragon`): Dragon #206
- Crabman (`crabman`): Dragon Magazine #250: Crabman (Article Race)
- Drow-Dragon (`drow_dragon`): Dragon #206
- Dryad (`dryad`): Dragon #251: Beyond the Tree (Article)
- Gibberling (`gibberling`): Dragon #265: Gibberling (Article Race)
- Gold Half-Dragon (`gold_half_dragon`): Dragon #206
- Grimlock (`grimlock`): Dragon #265: Primitive PCs (Article)
- Iron Half-Dragon (`iron_half_dragon`): Dragon #206
- Koalinth (`koalinth`): Dragon Magazine #250: Koalinth (Article Race)
- Liminal (`liminal`): Dragon Magazine #250: Liminal (Article Race)
- Locathah (`locathah`): Dragon Magazine #250: Locathah (Article Race)
- Malenti (`malenti`): Dragon Magazine #250: Malenti (Article Race)
- Merfolk (`merfolk`): Dragon Magazine #250: Merfolk (Article Race)
- Mold Man (Vegepygmy) (`mold_man_vegepygmy`): Dragon #265: Primitive PCs (Article)
- Pahari (`pahari`): Dragon Magazine #250: Pahari (Article Race)
- Quaggoth (`quaggoth`): Dragon #265: Primitive PCs (Article)
- Selkie (`selkie`): Dragon Magazine #250: Selkie (Article Race)
- Silver Half-Dragon (`silver_half_dragon`): Dragon #206
- Steel Half-Dragon (`steel_half_dragon`): Dragon #206
- Su-folk (`su_folk`): Dragon #265: Primitive PCs (Article)
- Troglodyte (`troglodyte`): Dragon #265: Primitive PCs (Article)
- Vodyanoi (`vodyanoi`): Dragon Magazine #250: Vodyanoi (Article Race)
- Yeti (`yeti`): Dragon #265: Primitive PCs (Article)
- Githyanki Outcast (`githyanki_outcast`): A Guide to the Astral Plane: Githyanki as Player Characters (GAP). Só tem limites para Warlock, Githwarriors e gish (classes que o app não tem): todas as classes do app dariam aviso.

## Escolhas de classificação que valem uma conferida

- **Sea of Fallen Stars** é livro dos Forgotten Realms: Aquatic Elf (SofS), Aquatic Half-Elf, Triton, Shalarin e Noble Malenti ficaram jogáveis em `Forgotten Realms`.
- **Half-Greyhawk Dragon** (Dragon #206) cita Greyhawk: jogável em `Greyhawk`. Os outros half-dragons do mesmo artigo não citam cenário: escondidos (decisão).
- **Githyanki Outcast** (Guide to the Astral Plane): só tem limites para Warlock, Githwarriors e gish; com as 12 classes do app, todas dariam aviso. Escondido (decisão).
- **Dryad** cita Krynn só em exemplos; o artigo é geral: escondida (decisão).
- **Sundered Dwarf**: sem cenário no texto do Complete Book of Dwarves: subraça Core.
- **Hengeyokai** e as **Half-Chiang/Shen Lung** são de Kara-Tur (Oriental Adventures); **Aranea, Lupin, Rakasta, Tortle** são de Red Steel (Savage Coast); **Fomorian** e **The Sidhe** são do Celts Campaign Sourcebook; **Trollborn** é de Vikings.
- **Stout Halfling** e **Tallfellow Halfling**: o livro dá "+1 DEX or CON" / "+1 DEX or WIS"; o dado estruturado só tem o +1 DEX. O app aplica só o +1 DEX; a escolha fica no texto (`abilityScoreAdjustmentsText`).

## Ids, nomes e duplicatas

- Ids: o id minerado (`drow`, `athasian_elf`…), exceto as 17 do app, que têm ids estáveis (`human`, `half_elf`, `bariaur_male`, `genasi_fire`, `modron`…). `source.minedId` liga ao registro minerado.
- `name` é o texto que a ficha grava no campo Raça (não muda para as 17: "Genasi (fire)", "Bariaur (male)"…). Os nomes antigos/mineirados ficam em `aliases` e o `matchRace` os aceita ("Rogue Modron" = Modron; "Human (Standard)" = Human).
- Nomes repetidos na mineração: **Hill Dwarf** (`hill_dwarf` fica; `hill_dwarf_mountain_dwarves` é cópia, escondida), **Aquatic Elf** (CBE = `aquatic_elf`; Sea of Fallen Stars = `aquatic_elf_sea_of_fallen_stars`, nome "Aquatic Elf (Sea of Fallen Stars)"), **Kender** (CBGH = `kender`; Dragonlance MC = `kender_mc`, nome "Kender (Monstrous Compendium)"), **Athasian Halfling** (Dark Sun = `athasian_halfling`; CBGH = escondida).
- Outros nomes limpos para a ficha: Mul, Svirfneblin, Furchin, Tinker Gnome, Bakali (o nome minerado fica em `aliases`).

## Subraças: `baseRace` e o que se herda

`baseRace` = id de uma das 6 raças do PHB. A web o usa para: (1) kits com restrição de raça (um kit "Elf" aceita Drow, High Elf, Athasian Elf…; "Any except elf" também as exclui); (2) imagem do Forge (sem arte própria, usa a da raça-base); (3) "é humano?" (classe dupla: Athasian Human); (4) tabela de altura/peso/idade (a da raça-base).

Regras que **não** viajam por `baseRace`: só entram no dado de uma subraça quando o texto dela traz a seção "Standard <Raça> Abilities" (o livro diz que as habilidades padrão valem). Nesse caso o script copia da raça-base: bônus de CON nos testes de resistência, resistência a sono/charme, bônus de combate, perícia grátis (Endurance dos anões) e demi-bardo. `inheritsFromBase` lista o que foi copiado. Exceções: Drow (resistência a magia própria, só em texto). As subraças de Dark Sun e de Sea of Fallen Stars (menos o Aquatic Elf) não herdam: têm regras próprias no livro do cenário.

Não herdam em nenhuma subraça: limites de nível, requisitos, ajustes e combinações (sempre os da própria raça), nem o texto de habilidades da ficha, montado do texto do livro.

