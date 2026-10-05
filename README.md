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
data/                  41 arquivos JSON (UTF-8)
schemas/               JSON Schema de cada arquivo + README com o mapeamento
scripts/
  validate_schemas.py  valida data/ contra schemas/
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
