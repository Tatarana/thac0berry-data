# Kits que faltavam no app (2026-11-20)

`scripts/add_missing_kits_2026_11.py` + `scripts/missing_kits_2026_11.json` (a decisão de cada kit) trouxeram
para `data/kits.json` os kits da mineração (`thac0berry-data-mining/data/character_kits`) que o app não tinha.
O app foi de 506 para **740 kits** (+234). Reproduzir: `python scripts/add_missing_kits_2026_11.py` e depois
`python scripts/curate_kit_proficiencies.py`.

## Os números reais (a comparação grosseira dobrava)

A mineração tem 781 kits: o "~488 fora do app" da comparação grosseira contava cada kit duas vezes
(Skills & Powers 60 era 30, Al-Qadim 56 era 28...). Deduplicando por id, nome e título da página, 274 ficaram
de fora do app. Destes, **234 entraram** e **40 foram descartados**.

### Descartados (40)

- 31 cartas colecionáveis em branco ("Create Your Own", "Create-Your-Own-Rogue"...), rotuladas como kit de algum livro;
- 1 "Checklist: 1-60 (1993 Rare Card Set)" e 2 páginas de lista ("Character Kits", "Dragon Magazine Character Kits");
- 3 duplicatas do Council of Wyrms que a Dragon Magazine adiantou: **Dragon Sage - Dragon** (#207), **Exile -
  Dragon** e **Ward - Dragon** (#206). Ficam as versões do livro (Dragon Sage, Exile, Ward);
- **Dragon Slayers (CWS)**: seção de regras de ataques, não um kit;
- **Gladiator (The Glory of Rome)**: mesmo nome do Gladiator de Skills & Powers, e a ficha guarda o kit pelo nome;
- **Ranger (The Glory of Rome)**: nota dizendo que o ranger não é um arquétipo romano, não um kit.

(31 + 1 + 2 + 3 + 1 + 1 + 1 = 40; o motivo de cada um está em `discard` no JSON da classificação.)

### Entraram (234), por livro

Os rótulos da mineração mentiam: "AD&D 2e Supplements" e "Arabian Adventures" escondiam kits de outros livros, e
o `sourceBook` foi corrigido pela barra lateral da página.

| Livro | Entraram | Visíveis no Forge | Cenário em construção | Escondidos |
|---|---:|---:|---:|---:|
| Player's Option: Skills & Powers | 30 | 30 | 0 | 0 |
| The Complete Book of Gnomes & Halflings | 27 | 27 | 0 | 0 |
| The Complete Book of Dwarves | 24 | 24 | 0 | 0 |
| Arabian Adventures (Al-Qadim) | 24 | 0 | 24 | 0 |
| The Complete Spacefarer's Handbook (Spelljammer) | 20 | 0 | 20 | 0 |
| Red Steel (Savage Coast) | 20 | 0 | 0 | 20 |
| The Complete Book of Humanoids | 19 | 0 | 0 | 19 |
| The Glory of Rome | 12 | 0 | 0 | 12 |
| Council of Wyrms | 9 | 0 | 6 | 3 |
| Wizards & Rogues of the Realms (Forgotten Realms) | 8 | 7 | 0 | 1 |
| The Complete Sha'ir's Handbook (Al-Qadim; era "Spacefarer") | 8 | 0 | 8 | 0 |
| The Complete Gladiator's Handbook (Dark Sun; era "Supplements") | 7 | 0 | 0 | 7 |
| Sages & Specialists (era "Supplements") | 4 | 4 | 0 | 0 |
| The Complete Book of Necromancers (era "Supplements"/"Al-Qadim") | 2 | 2 | 0 | 0 |
| The Planewalker's Handbook (Planescape; era "Al-Qadim") | 2 | 2 | 0 | 0 |
| Thri-Kreen of Athas (Dark Sun; um era "Humanoid's Handbook") | 2 | 2 | 0 | 0 |
| A Guide to the Ethereal Plane | 1 | 1 | 0 | 0 |
| Dragon Magazine (#200, #205, #215, #225, #233, #236, #247, #270) | 15 | 1 | 0 | 14 |
| **Total** | **234** | **100** | **58** | **76** |

### Jogáveis (100 visíveis no Forge)

- **Core (89):** Skills & Powers 30, Complete Book of Dwarves 24, Complete Book of Gnomes & Halflings 27, Sages &
  Specialists 4, Complete Book of Necromancers 2, A Guide to the Ethereal Plane 1, Kshatriya 1.
- **Forgotten Realms (7):** Rogues of Anauroch, Empires of the Sands, Old Empires, Savage North, Vilhon Reach,
  Waterdeep e Wizards of Halruaa (Wizards & Rogues of the Realms; Rogues of the Moonsea fica escondido, ver abaixo).
- **Planescape (2):** Floating Sorcerer e Planewalker Rogue.
- **Dark Sun (2):** Tekchakak e Kiltektet (raça Thri-Kreen).

Por grupo/subclasse do compêndio: Demihuman/Dwarf 24, Demihuman/Halfling 17, Demihuman/Gnome 10, Warrior/Fighter 18,
Warrior/Paladin 1, Rogue/Thief 17, Wizard 10, Psionicist 2, Priest/Any Priest 1.

### Cenário em construção (58): entram com o `setting` certo; a web os esconde

Al-Qadim 32 (Arabian Adventures 24 + Complete Sha'ir's Handbook 8), Spelljammer 20, Council of Wyrms 6. Nenhum
leva `playable: false` (a web já filtra por `settingsUnderConstruction`); aparecem no compêndio com o aviso
"under construction". Isto também esconde o `Dragon Psionicist` (Council of Wyrms), que já estava nos dados e
aparecia com "todos os mundos".

### Escondidos (76, `playable: false` + `hiddenReason`)

| Motivo | Kits |
|---|---:|
| `setting-not-in-forge` | 32: Red Steel (Savage Coast) 20, The Glory of Rome 12 |
| `humanoid-not-playable` | 19: Complete Book of Humanoids (as raças humanoides não são jogáveis) |
| `class-not-in-app` | 13: Complete Gladiator's Handbook 7 (classe Gladiator de Dark Sun) e Masque of the Red Death 6 (classes Tradesman e Mystic) |
| `race-not-playable` | 1: Courier (avariel; a raça Avariel não é jogável em `races.json`) |
| `undecided` | 11, abaixo |

## Decisões de grupo e classe

- **Complete Book of Dwarves e of Gnomes & Halflings:** grupo **Demihuman**, o mesmo do CBE (kits de raça), com as
  subclasses `Dwarf` (já existia), **`Gnome` e `Halfling`** (novas no compêndio). A classe vem de `allowedClasses`.
  `requirements.races` = "Dwarf", "Gnome" ou "Halfling": as subraças entram pela `baseRace` (Mountain Dwarf, Duergar,
  Svirfneblin, Stout Halfling...; testado). Kit multiclasse declarado na página leva `combination`: Champion e
  Temple Guard (Fighter/Cleric), Wayfinder (Fighter/Thief). Kit cuja página não diz a classe (Animal Master, Entertainer,
  Rapid Response Rider, Trader dos anões; Cartographer, Forestwalker, Goblinsticker, Homesteader, Sheriff, Traveller
  dos pequenos) fica aberto a todas as classes que a raça tem (Fighter, Cleric/Specialty Priest, Thief; no gnomo também
  Mage). Gnomo ilusionista = Mage.
- **Skills & Powers:** os kits são abertos a "todas as classes", menos as barradas em cada página. A lista "todas" é a
  das 8 classes do PHB (Fighter, Paladin, Ranger, Mage, Cleric/Specialty Priest, Druid, Thief, Bard): o livro não
  fala de Ninja, Psionicist etc. e não inventei. O grupo do compêndio é só a prateleira, pelo arquétipo do kit:
  **Warrior/Fighter** (Amazon, Animal Master, Barbarian, Cavalier, Explorer, Gladiator, Mariner, Outlaw, Peasant Hero,
  Pirate, Pugilist, Rider, Savage, Scout, Sharpshooter, Soldier, Swashbuckler, Weapon Master), **Rogue/Thief**
  (Acrobat, Assassin, Beggar, Diplomat, Jester, Merchant, Noble, Smuggler, Spy, Thug), **Wizard** (Scholar: lutadores
  não podem) e **Priest/Any Priest** (Mystic). Mudar de prateleira é só trocar `group`/`subclass` no JSON.
  As raças barradas viraram texto em `requirements.races` ("Any except dwarves, aarakocra..."); "orcs" foi omitido
  nas listas de raças barradas para o comparador de raças não barrar o meio-orc (a página fala só em orcs).
- **Humanoides:** grupo da classe (Wizard, Warrior, Rogue, Priest) com `races: "Humanoid"` (nenhuma raça do PHB casa).
- **Gladiator (Dark Sun), MotRD:** subclasses `Gladiator` (Warrior), `Tradesman` (Rogue) e `Mystic` (Priest), só para
  o compêndio mostrar; `allowedClasses` vazio (Gladiator) ou classe inexistente.
- **Kits que a página aponta a classe:** Al-Qadim/Spacefarer/Red Steel/Glory of Rome/humanoides pelo "Character
  Class" e pelo texto de cada página (Askar, Corsair, Faris... Warrior; Ethoist, Kahin, Hakima... Cleric; etc.).
- **Dragon Magazine, um a um:** entra jogável o **Kshatriya** (a seção diz "Indian paladin", como o Shikari "Indian
  ranger"; antes foi excluído como ambíguo, agora é Paladin). **Courier** (avariel; "rogues, fighters, or multiclassed")
  entra escondido pela raça. Os 6 de Masque of the Red Death entram escondidos (classe inexistente). Os 11 abaixo
  ficam para decisão.

## Para decisão do usuário (`hiddenReason: undecided`, 11)

1. **Rogues of the Moonsea** (Forgotten Realms): a página diz que os ladrões de Moonsea "should always be
   non-player characters" (malignos). Entraria visível; deixei escondido.
2. **Dragon PC, Dragon Sage, Ward** (Council of Wyrms): kits genéricos de dragão ou meio-dragão, sem classe própria.
3. **Alakvalt, Sarkany, Boszorkany** (Taltos, Dragon #247): a página não diz a classe (Boszorkany: sacerdote ou mago?).
4. **Mystery Man** (#205): "cannot be specialized mages" sugere mago, mas o texto fala de magia clerical.
5. **Tribal Scout** (#205): troca "find traps" por "detect ambush" (perícias de ladrão), sem nomear a classe.
6. **Zande Witch Woman** (#200): chamada pelos deuses (sacerdotisa?), exige short sword; sacerdote ou guerreira?
7. **Manikin** (#270): kit geral imposto a humanoides capturados por uma "machine cyst", para qualquer classe.

Outras decisões que vale conferir: **Courier** escondido por raça enquanto **Skywarden** e **Talon** (avariel,
já nos dados antes) seguem visíveis; a **raça "Humanoid"** dos kits escondidos; Kshatriya jogável.

## Proficiências e armas

Curadoria estruturada para os 234 em `kit_proficiency_curation.json` (bonus, bonusChoices, required, requiredChoices,
recommended, forbidden; armas: required, requiredChoices, recommended, forbidden, allowed, specialization),
lida do texto de cada página e com os nomes do compêndio. Os escondidos têm entrada com listas vazias (exceto onde a
classificação já trazia dado). Slots: `kit_nonweapon_slots.json` ganhou o Clansdwarf (+2, duas perícias de ofício
da mesma especialidade). Dinheiro inicial só quando a página dá uma fórmula única ("5d4x10 gp"); Highborn
("400 gp, plus 5d4x10") e Patrician ("350 gp, plus 3d6x10") ficam `null`; nos Skills & Powers a variação por classe
("150% do valor da classe") fica no texto.

**Perícias sem regra no compêndio (ficam só no texto):** Gambling (Noble e Pirate de Skills & Powers; só existe
Gaming), Fortify (Etherfarer), Craft (Clansdwarf, Crafts Priest, Outcast: "any Craft proficiency" não é uma
entrada), "Underground (Proficiency)" (Animal Master dos anões) e "Underground Direction Sense" (Rapid Response Rider).
**Armas sem entrada:** Kyorkcha (Kiltektet). Formas desarmadas (Punching, Wrestling, Martial Arts) seguem o
precedente (nome na lista, fora do compêndio). Categorias de armas que a página cita sem enumerar ("polearm",
"ranged weapon", "axe, hammer, mace, pick") foram expandidas só onde o PHB é inequívoco (bows, crossbows, lances, as
cinco espadas); `allowed` foi omitido quando a página lista categorias que eu teria de inventar (Clansdwarf, Crafts
Priest). Os motivos de cada dúvida estão em `doubts` na curadoria.
