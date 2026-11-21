# Divindades: expansão de 101 para 386 (2026-11)

Gerado por `scripts/build_deities.py` (não editar à mão). Fonte: `../thac0berry-data-mining/extract_deities.py` sobre o dump da wiki AD&D 2e + curadoria em `scripts/deity_curation.json`.

## Totais

| Livro | Divindades |
|---|---|
| Faiths & Avatars | 46 |
| Powers & Pantheons | 33 |
| Tales of the Lance | 22 |
| Legends & Lore | 148 |
| Monster Mythology | 127 |
| Dragon Magazine | 10 |
| **Total** | 386 |

### Por panteão

| Livro | Panteão | Total | Forge sim | Forge não | Raça |
|---|---|---|---|---|---|
| Dragon Magazine | African | 10 | 0 | 10 |  |
| Faiths & Avatars | Faerûnian | 46 | 46 | 0 |  |
| Legends & Lore | American Indian | 12 | 0 | 12 |  |
| Legends & Lore | Aztec | 13 | 0 | 13 |  |
| Legends & Lore | Celtic | 11 | 0 | 11 |  |
| Legends & Lore | Chinese | 16 | 0 | 16 |  |
| Legends & Lore | Egyptian | 14 | 0 | 14 |  |
| Legends & Lore | Greek | 21 | 0 | 21 |  |
| Legends & Lore | Indian | 18 | 0 | 18 |  |
| Legends & Lore | Japanese | 16 | 0 | 16 |  |
| Legends & Lore | Nehwon | 8 | 0 | 8 |  |
| Legends & Lore | Norse | 19 | 0 | 19 |  |
| Monster Mythology | Beholder | 2 | 0 | 2 |  |
| Monster Mythology | Dark Folk | 8 | 0 | 8 |  |
| Monster Mythology | Derro | 1 | 0 | 1 |  |
| Monster Mythology | Draconic | 6 | 0 | 6 |  |
| Monster Mythology | Drow | 4 | 4 | 0 | elf |
| Monster Mythology | Duergar | 2 | 2 | 0 | dwarf |
| Monster Mythology | Dwarven | 8 | 8 | 0 | dwarf |
| Monster Mythology | Elven | 9 | 9 | 0 | elf |
| Monster Mythology | Giant | 14 | 0 | 14 |  |
| Monster Mythology | Gnomish | 8 | 8 | 0 | gnome |
| Monster Mythology | Goblinoid | 10 | 0 | 10 |  |
| Monster Mythology | Halfling | 6 | 6 | 0 | halfling |
| Monster Mythology | Illithid | 2 | 0 | 2 |  |
| Monster Mythology | Kobold | 2 | 0 | 2 |  |
| Monster Mythology | Lost Gods | 3 | 0 | 3 |  |
| Monster Mythology | Myconid | 1 | 0 | 1 |  |
| Monster Mythology | Orcish | 6 | 0 | 6 |  |
| Monster Mythology | Scaly Folk | 8 | 0 | 8 |  |
| Monster Mythology | Sea | 8 | 0 | 8 |  |
| Monster Mythology | Sky | 6 | 0 | 6 |  |
| Monster Mythology | Svirfneblin | 1 | 1 | 0 | gnome |
| Monster Mythology | Sylvan | 12 | 0 | 12 |  |
| Powers & Pantheons | Faerûnian | 33 | 33 | 0 |  |
| Tales of the Lance | Dragonlance | 22 | 22 | 0 |  |

### forgeSelectable

- `true`: **139**
- `false`: **247** (só compêndio)

| Livro | true | false |
|---|---|---|
| Faiths & Avatars | 46 | 0 |
| Powers & Pantheons | 33 | 0 |
| Tales of the Lance | 22 | 0 |
| Legends & Lore | 0 | 148 |
| Monster Mythology | 38 | 89 |
| Dragon Magazine | 0 | 10 |

Deuses com `race` (destaque por raça no app): dwarf 10, elf 13, gnome 9, halfling 6.

## Campos novos (todos opcionais no schema)

- `pantheon` (string): panteão de origem (capítulo do LL; panteão da lista da wiki no MoMy; 'African' na Dragon; 'Faerûnian' para FA/PP; 'Dragonlance' para TotL).
- `forgeSelectable` (boolean, ausente = true): se o Forge pode oferecer o deus. Gravado em todos os registros.
- `race` (string): raça-base (`dwarf`, `elf`, `gnome`, `halfling`) dos deuses de semi-humanos.

## Regras de decisão (usuário, 2026-11-20)

- Legends & Lore (panteões históricos/literários): `forgeSelectable: false`.
- Monster Mythology de humanoides e monstros (orc, goblinoide, kobold, gigante, dragão, povo escamoso, mar e céu, povo das trevas, silvestres, beholder, illithid, myconid, deuses perdidos, derro): `false`.
- Monster Mythology dos semi-humanos (anões, elfos incluindo drow, gnomos incluindo svirfneblin, halflings, e os duergar): `true`, vale em qualquer cenário, com `race`.
- FA, PP e TotL existentes: `true`.

### Exceções por deus

- `deep_sashelas` (Elven, forgeSelectable true, race elf): A lista da wiki o põe em 'Gods of the Seas' (o livro o imprime no capítulo Seas and Skies), mas o próprio texto diz que ele é o principal deus dos elfos marinhos (raça-base elf) e o panteão élfico clássico o inclui. Tratado como deus de semi-humanos.
- `diirinka` (Derro, forgeSelectable false): Está na lista 'Underdark Dwarves', mas é deus dos derro (WAL 'ce (derro)'); derro não é uma raça-base do app (só duergar é anão). Os outros dois da lista (Laduguer, Diinkarazan) são duergar.

## Dragon Magazine: classificação

Os 10 deuses 'Article God' vêm de um único artigo, 'The Deities of Africa' (Dragon #215). Nenhum é do Forgotten Realms, de Dragonlance nem de panteão de semi-humanos: todos ficam só no compêndio.

| Deus | id | AL | forgeSelectable | Motivo |
|---|---|---|---|---|
| Ananse | ananse | LG | False | Aranha-mensageira dos Ashanti; panteão africano. |
| Animal Spirits | animal_spirits | lion man LN, antelope man CG, porcupine man N, chameleon man NG | False | Espíritos-animais da mitologia dos Bushmen (grupo, não um deus único); panteão africano. |
| Asase Ya | asase_ya | N | False | Deusa-terra dos Ashanti; panteão africano. |
| Bumba | bumba | LN | False | Deus-criador dos Bakuba; panteão africano. |
| Cagn | cagn | CN | False | Mantis (Kaggen), deus bushman; panteão africano. |
| Gauna | gauna | CE | False | Deus-do-mal dos Khoikhoi/Bushmen; panteão africano. |
| Khonvum | khonvum | NG | False | Caçador do céu dos Bushmen; panteão africano. |
| Leza | leza | CG | False | Deus-supremo dos Bantu centrais; panteão africano. |
| Nyame | nyame | LG | False | Deus-do-céu dos Ashanti; panteão africano. |
| So | so | LG | False | Deus-trovão dos Ewe/Fon; panteão africano. |

A lista da wiki ('List of Gods & Avatars') ainda cita deuses da Dragon #191, #263-265 e Polyhedron (Rillifane Rallathil, Woden, Thunor, Atroa, Beshaba/Tymora/Xvim...), mas **não há página deles no dump**: ficam de fora.

## Descartados (não são divindades)

- **Legends & Lore**, heroi mortal (tipo 'Hero' na lista da wiki), nao e divindade (44): Arthur, Average Knight of Quality, Average Knight of Renown, Axayacatl, Bedevere, Beowulf, Cu Chulainn, Empress Jingo, Fafhrd, Fjalar, Galahad, Gareth, Garlon, Gawaine, Gray Mouser, Guinevere, Hiawatha, Kay, Lady of the Lake, Lamorak, Launcelot, Merlin, Mordred, Morgan le Fay, Movarl, Naciens, Nezahualcoytl, Nezahuldilli, Ningauble of the Seven Eyes, Odysseus, Pa Hsien, Palomides, Percivale, Plugh, Qagwaaz, Raiko, Sheelba of the Eyeless Face, Sigurd, Skirnir, Stoneribs, The Green Knight, Theseus, Tristram, Yanauluha.
- **Legends & Lore**, pagina de capitulo, introducao ou creditos do livro (13): Ch 1, Ch 10, Ch 11, Ch 2, Ch 3, Ch 4, Ch 5, Ch 6, Ch 7, Ch 8, Ch 9, Credits, Introduction.
- **Legends & Lore**, pagina de regra ou texto de apoio, sem titulo de posto nem 'Statistics: AL' (8): Ascetic Characters, Aztec Monsters, Dharma, Karma, and Reincarnation, Generals of the Animal Spirits, Lankhmar Encounter Tables, The Master of the Hunt, The Pious Knights, The Wild Hunt.
- **Legends & Lore**, texto geral do capitulo (historia, cultura, panteao), sem ficha de divindade (11): American Indian Mythology, Arthurian Mythology, Aztec Mythology, Celtic Mythology, Chinese Mythology, Egyptian Mythology, Greek Mythology, Indian Mythology, Japanese Mythology, Nehwon Mythology, Norse Mythology.
- **Monster Mythology**, heroi mortal (4): Gerdreg, Gnarldan Steelshield, Kaldair Swiftfoot, Lafarallinn.
- **Monster Mythology**, pagina de capitulo, introducao ou creditos do livro (13): Abbreviations, Ch 0, Ch 1, Ch 2, Ch 3, Ch 4, Ch 5, Ch 6, Ch 7, Ch 8, Ch 9, Credits, Introduction.
- **Monster Mythology**, pagina de regra ou texto de apoio, sem titulo de posto nem 'Statistics: AL' (11): Appendix 1: Avatars in Game Play, Appendix 2: Deities and Game Worlds, Avatars, Deities Included in This Book, Deities and the Campaign, Divine Abilities, Explanatory Notes, Integrating Human and Nonhuman Pantheons, Nonhuman Deities as Archetypal Powers, Priests and Priesthoods, Running Divine Beings.
- **Monster Mythology**, texto geral do capitulo (historia, cultura, panteao), sem ficha de divindade (8): Goblinoid Deities, Gods of the Dark Folk, Gods of the Demihumans, Gods of the Giants, Gods of the Scaly Folk, Gods of the Seas and Skies, Gods of the Underdark, The Sylvan Gods.
- **Powers & Pantheons**, apendice (aliases, locais, indice de magias, magias novas, monstros) (5): Appendix 1: Aliases, Appendix 2: Locations, Appendix 3: Spell Index, Appendix 3a: New Spells, Appendix 4: Monsters.
- **Powers & Pantheons**, capitulo ou texto de panteao (sem ficha de divindade) (11): Ch 1, Ch 2, Ch 3, Ch 4, Ch 5, Ch 6, Chultan Pantheon, Faerunian Pantheon (Demipowers), Mulhorandi & Untheric Pantheons, Prominent Temples, The Dawn of Time.
- **Powers & Pantheons**, modulo de aventura de um templo (capitulo Prominent Temples), nao e divindade (5): Cathedral of the Emerald Scale, Citadel of Black Ash, Cloister of St Ramedar, House of the Moon, The Flaming Brazier.
- **Powers & Pantheons**, pagina de apoio do livro (creditos, sobre o produto) (2): About This Product, Credits.
- **Powers & Pantheons**, pagina de monstro (formato Creature/Combat), fora deste schema (como Iuz e Vecna) (3): Dendar, Ityak-Ortheel, Kezef.

Outras exclusões conscientes: Iuz, Vecna, Dendar, Kezef, Ityak-Ortheel, Asmodeus, Graz'zt, Pazrael, Eltab, Rainha do Caos, Blizzard (páginas de monstro/NPC com infobox Creature, outro formato); Asclepius (AoH, livro Age of Heroes, fora do escopo). Heróis mortais (44 do LL, 4 do MoMy) ficaram de fora: o MoMy e o LL os separam dos deuses (tipo 'Hero' na lista). Pendência para decisão do usuário.

## Divergências com os registros existentes

### Mineração x deities.json (FA e PP re-minerados)

| id | campo | no app (vale) | na mineração |
|---|---|---|---|
| tiamat | rank | 'Lesser Power' | 'Letter Power' |

O valor do app fica. (Tiamat: a wiki tem 'Letter Power', erro de digitação; o app já corrigiu para 'Lesser Power'.)

Os 22 de Krynn (TotL) vêm de `scripts/add_krynn_deities.py`, direto do dump; não passam pela mineração e não foram comparados.

### Mesmo nome em panteões diferentes

Nomes iguais não foram fundidos (são fichas diferentes: o Set dos Reinos é o do PP, o Set egípcio é o do LL). O id novo ganha o sufixo do panteão; o do app não muda. `findDeityByName` do app devolve o primeiro, que é o existente.

| Nome | id | Livro | Panteão | Posto | AL |
|---|---|---|---|---|---|
| Oghma | oghma | Faiths & Avatars | Faerûnian | Greater Power | N |
| Oghma | oghma_celtic | Legends & Lore | Celtic | Intermediate God | NG |
| Tyr | tyr | Faiths & Avatars | Faerûnian | Greater Power | LG |
| Tyr | tyr_norse | Legends & Lore | Norse | Intermediate God | LG |
| Anhur | anhur | Powers & Pantheons | Faerûnian | Lesser Power | CG |
| Anhur | anhur_egyptian | Legends & Lore | Egyptian | Lesser God | CG |
| Geb | geb | Powers & Pantheons | Faerûnian | Lesser Power | N |
| Geb | geb_egyptian | Legends & Lore | Egyptian | Intermediate God | NG |
| Isis | isis | Powers & Pantheons | Faerûnian | Intermediate Power | NG |
| Isis | isis_egyptian | Legends & Lore | Egyptian | Intermediate God | LG |
| Osiris | osiris | Powers & Pantheons | Faerûnian | Intermediate Power | LG |
| Osiris | osiris_egyptian | Legends & Lore | Egyptian | Intermediate God | LG |
| Set | set | Powers & Pantheons | Faerûnian | Intermediate Power | LE |
| Set | set_egyptian | Legends & Lore | Egyptian | Intermediate God | LE |
| Thoth | thoth | Powers & Pantheons | Faerûnian | Intermediate Power | N |
| Thoth | thoth_egyptian | Legends & Lore | Egyptian | Lesser God | N |
| Tiamat | tiamat | Powers & Pantheons | Faerûnian | Lesser Power | LE |
| Tiamat | tiamat_draconic | Monster Mythology | Draconic | Lesser God | None |

## Correções e limites do texto minerado

- **Alinhamentos do OCR**: a wiki do LL/MoMy traz 'eg', 'en', 'Ig', 'In' (o OCR trocou c->e e l->I). Corrigidos para CG, CN, LG, LN (Corellon Larethian, Erevan Ilesere e Hanali Celanil confirmam a troca). Incerto só onde o livro não confere, por exemplo Odin 'CG'.
- **Postos**: 'Goddess' vira 'God', plural vira singular ('Lesser Gods' = 'Lesser God'), 'Intermediated' vira 'Intermediate'. Valor original no minerado (`rankRaw`).

- **Sem posto (`rank` null)**: Stillsong, Ananse, Animal Spirits, Asase Ya, Bumba, Cagn, Gauna, Khonvum, Leza, Nyame, So (Dragon não traz posto; Stillsong é 'Unknown').

- **Posto vindo da lista da wiki** (a página não tem título de posto): Annam e Yondalla (Greater God).
- **The Dark God**: o título diz 'Intermediate/Lesser God: Power Varies'; ficou 'Intermediate God'.

- **Sem portfolio (`portfolio` = "", campo obrigatório no schema)**, a página não tem linha 'Statistics' (8): Spirits, Aasterinian, Bahamut, Chronepsis, Faluzure, Io, Tiamat, Zinzerena.

- **Sem alinhamento** (7): Spirits, Aasterinian, Bahamut, Chronepsis, Faluzure, Io, Tiamat.

- Os dragões do MoMy (Io, Bahamut, Tiamat, Chronepsis, Faluzure, Aasterinian) usam o formato 'Further Statistics': só o símbolo foi extraído.
- `plane`, `aliases`, `domainName`, `superior`, `allies`, `foes` ficam null: LL/MoMy/Dragon não trazem esses campos.
- O avatar vai em texto ('Str 22, Dex 18, ...') como nos deuses de Krynn.

## Questões em aberto (decisão do usuário)

1. Os 4+44 heróis mortais (Arthur, Fafhrd, Gnarldan Steelshield, Kaldair Swiftfoot, Lafarallinn...) entram como 'divindade'? Hoje não.
2. Duergar (Laduguer, Diinkarazan) e drow como `forgeSelectable: true` (race dwarf/elf): confirmado pela regra 'semi-humanos', mas são Underdark malignos.
3. Deep Sashelas como deus élfico (override acima).
4. Nomes repetidos (Set, Isis, Osiris, Tyr...): mostrar o panteão ao lado do nome na lista?
5. Mulhorandi, Untheric e Chultan (PP) ficaram em 'Faerûnian'; se quiser sub-panteões é só trocar a curadoria.
6. Reorx (TotL) é deus de anões/gnomos, mas ficou só 'Dragonlance' sem `race`.
7. Asclepius (AoH) e os deuses da Dragon sem página no dump.

