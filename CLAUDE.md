# thac0berry-data: guia para agentes

Dados de referência (JSON) e o contrato deles (JSON Schema), compartilhados pelo app
iPad, pelo backend e pela web. Converse com o usuário em **português**.

## Regras

1. **Proponha e espere o "ok" antes de mudar qualquer dado ou schema.** Estes arquivos
   chegam aos personagens salvos dos jogadores.
2. **Ids são contrato:** nunca renomear, reaproveitar ou apagar um `id` sem aprovação
   (as fichas apontam para eles).
3. **Schema espelha o decode do Swift** (`thac0berry-ipad/THAC0berry.swiftpm/Models`):
   campo obrigatório no schema = o Swift falha sem ele. Ver `schemas/README.md`,
   inclusive a armadilha do `var x = default` com Codable sintetizado.
4. **Toda mudança passa por `python scripts/validate_schemas.py`** e pelo CI
   (`.github/workflows/validate.yml`). Campo novo: opcional, para os dados antigos
   continuarem válidos.
5. **Depois de mudar `data/`, o repo do iPad precisa ser atualizado** com
   `python Scripts/sync_data.py` (lá), senão o app continua com a cópia antiga. O CI do
   iPad acusa a divergência.
6. Arquivos grandes (`kits.json`, `rules.json` ~5 MB): edite com script, não à mão, e
   mantenha UTF-8 sem BOM.
7. Fim de linha: LF (forçado pelo `.gitattributes`). Neste PC o git usa
   `core.autocrlf=true`.
