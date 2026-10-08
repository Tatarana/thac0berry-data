# Schemas dos dados de referência

Contrato dos JSON em `data/` (magias, kits, regras, itens…). É a fonte de verdade do **formato** desses dados para o app iPad e,
no futuro, para o backend e a versão web. JSON Schema draft 2020-12.

Validar: `python scripts/validate_schemas.py` (requer `pip install jsonschema`).
O CI (`.github/workflows/validate.yml`) roda isso a cada push.

## Arquivo → schema

| Arquivos | Schema | Modelo Swift (repo `thac0berry-ipad`, pasta `THAC0berry.swiftpm/`) |
|---|---|---|
| `sample_spells.json`, `priest_*.json`, `wizard_*.json` | `spell.schema.json` | `Models/Spell.swift` |
| `weapons.json` | `weapon.schema.json` | `Models/Weapon.swift` |
| `armor.json` | `armor.schema.json` | `Models/ArmorPiece.swift` |
| `mundane_items.json` | `mundane-item.schema.json` | `Models/MundaneItem.swift` |
| `deities.json` | `deity.schema.json` | `Models/Deity.swift` |
| `proficiencies.json` | `proficiency.schema.json` | `Models/Proficiency.swift` |
| `kits.json` | `kit.schema.json` | `Models/Kit.swift` |
| `magic_*.json` | `magic-item.schema.json` | `Models/MagicItem.swift` |
| `psionic_powers.json` | `psionic-power.schema.json` | `Models/PsionicPower.swift` |
| `rules.json` | `rule-entry.schema.json` | `Models/Rule.swift` |
| `books.json` | `book.schema.json` | — (por enquanto só web; gerado por `scripts/build_books.py`; o iPad ainda usa `RulesCompendiumView.bookOrder`) |
| `rules_thac0.json` | `rules-thac0.schema.json` | `Store/RuleEngine/CoreRuleset/Thac0ByLevelProvider.swift` |
| `rules_saving_throws.json` | `rules-saving-throws.schema.json` | `Store/RuleEngine/CoreRuleset/SavingThrowsByLevelProvider.swift` |
| `rules_experience.json` | `rules-experience.schema.json` | `Models/ExperienceProgressionTable.swift` |
| `monsters/monsters_index.json` | `monster-index.schema.json` | — (só web; ferramenta do DM) |
| `monsters/monsters_*.json` | `monster.schema.json` | — (só web; gerado por `scripts/build_monsters.py`; subpasta fora do `sync_data.py` do iPad) |

## Como o schema espelha o Swift

O schema descreve o que o **decode do Swift aceita**, não o que "parece certo":

- `let x: T` no Swift → `x` em `required`, sem `null`.
- `let x: T?` (Codable sintetizado) ou `decodeIfPresent` num `init(from:)`
  próprio → opcional, aceita `null`.
- **Pegadinha:** `var x: T = valorPadrão` com Codable **sintetizado** continua
  exigindo a chave no JSON — o default do struct não vale pro decoder. Por
  isso `SpellDamage.bonus`, `isHealing` etc. são obrigatórios. (Foi esse o
  bug dos `priest_*.json` na v1.81–v1.86, ver `TODO.md`.)
- Campos a mais no JSON são aceitos (o decoder ignora). O validador lista
  esses campos como aviso; `--strict` transforma em erro. Hoje não há nenhum.

## Regra de mudança

Mudou um modelo Swift que decodifica um desses arquivos (repo `thac0berry-ipad`) →
atualize o schema aqui **na mesma entrega**. Campo novo em modelo existente entra como
opcional (`decodeIfPresent ?? default` no Swift, fora de `required` no schema), senão
os arquivos antigos deixam de decodificar. O backend e a web leem os mesmos schemas.

## Ficha de personagem: `library.schema.json`

Formato do `library.json` do iPad e do backup exportado em Settings: campanhas,
sessões, caderno, personagens, folhas de magia e efeitos ativos. Não é dado de
referência (não há arquivo em `data/`); é o contrato da ficha entre iPad, web e backend.

- **Gerado, não escrito à mão:** `python Scripts/gen_library_schema.py` no repo
  `thac0berry-ipad` lê os modelos Swift e grava aqui. O CI do iPad (`data.yml`) acusa
  quando o schema daqui não bate com o código de lá.
- Tipos com `init(from:)` próprio (`ProficiencyEntry`, `CharacterClass`) são escritos à
  mão dentro do gerador; um decode próprio novo sem essa entrada faz o gerador falhar.
- **Datas:** ISO-8601 **sem fração de segundo** (`2026-10-05T12:00:00Z`). O
  `toISOString()` do JavaScript grava `.000Z`, que o iPad recusa.
- **UUID:** o iPad grava em maiúsculas; aceita os dois.
- Um personagem ou campanha que não bate com o schema é descartado pelo iPad sozinho
  (`LossyArray`), sem levar os outros junto, e sem aviso na tela.
- Testes: `fixtures/library/valid-minimal.json` precisa passar; cada mutação de
  `fixtures/library/invalid-cases.json` precisa falhar (são fichas que o iPad
  rejeitaria). Rodam junto com `scripts/validate_schemas.py`.
- Nunca commitar backup real de jogador como fixture.
