#!/usr/bin/env python3
"""Valida todo JSON de `data/` contra `schemas/`.

Os schemas são o contrato dos dados de referência entre o app iPad e o
futuro backend/web, e espelham exatamente o que o Swift decodifica
(campo obrigatório = o decode do Swift falha sem ele). Ver `schemas/README.md`.

Uso:  python scripts/validate_schemas.py [--strict]
  --strict  campos que o app ignora (desconhecidos pelo schema) viram erro.

Sai com código 1 se: um JSON não bate com o schema, um JSON de data/
não tem schema mapeado, ou há `id` duplicado dentro de um arquivo.
Requer: pip install jsonschema
"""
import copy
import fnmatch
import json
import os
import sys
from collections import Counter

from jsonschema import Draft202012Validator

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RES = os.path.join(ROOT, "data")
SCHEMAS = os.path.join(ROOT, "schemas")

# Arquivo (glob) -> schema. Todo .json de data/ precisa casar com um.
# Arquivos que estão em data/ mas o app NÃO carrega — listados à parte
# pra não passarem despercebidos (e nem quebrarem a validação).
NOT_LOADED = {}

MAPPING = [
    ("sample_spells.json", "spell.schema.json"),
    ("priest_*.json", "spell.schema.json"),
    ("wizard_*.json", "spell.schema.json"),
    ("weapons.json", "weapon.schema.json"),
    ("armor.json", "armor.schema.json"),
    ("mundane_items.json", "mundane-item.schema.json"),
    ("deities.json", "deity.schema.json"),
    ("proficiencies.json", "proficiency.schema.json"),
    ("kits.json", "kit.schema.json"),
    ("magic_*.json", "magic-item.schema.json"),
    ("psionic_powers.json", "psionic-power.schema.json"),
    ("rules.json", "rule-entry.schema.json"),
    ("rules_thac0.json", "rules-thac0.schema.json"),
    ("rules_saving_throws.json", "rules-saving-throws.schema.json"),
    ("rules_experience.json", "rules-experience.schema.json"),
]


def closed(schema):
    """Cópia do schema com additionalProperties:false em todo objeto que
    declara `properties` — usada só pra listar campos que o app ignora."""
    s = copy.deepcopy(schema)

    def walk(node):
        if isinstance(node, dict):
            if "properties" in node and "additionalProperties" not in node:
                node["additionalProperties"] = False
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk(s)
    return s


def path_of(err):
    return "/".join(str(p) for p in err.absolute_path) or "(raiz)"


def check_library_fixtures():
    """library.schema.json (ficha de personagem) não valida nada em data/:
    é testado com fixtures. `valid-minimal.json` precisa passar (também com
    campos desconhecidos proibidos); cada mutação de `invalid-cases.json`
    aplicada a ele precisa falhar, senão o schema deixa passar uma ficha
    que o iPad rejeitaria."""
    folder = os.path.join(ROOT, "fixtures", "library")
    schema = json.load(open(os.path.join(SCHEMAS, "library.schema.json"), encoding="utf-8"))
    validator, closed_validator = Draft202012Validator(schema), Draft202012Validator(closed(schema))
    valid = json.load(open(os.path.join(folder, "valid-minimal.json"), encoding="utf-8"))
    failed = False

    errors = list(closed_validator.iter_errors(valid))
    print(f"{'FAIL' if errors else 'OK  '} {'fixtures/library/valid-minimal.json':36} {'library.schema.json':32} deve passar")
    for e in errors[:10]:
        print(f"     erro  {path_of(e)}: {e.message[:160]}")
    failed |= bool(errors)

    cases = json.load(open(os.path.join(folder, "invalid-cases.json"), encoding="utf-8"))
    for case in cases:
        doc = copy.deepcopy(valid)
        node = doc
        for key in case["path"][:-1]:
            node = node[key]
        if case.get("delete"):
            del node[case["path"][-1]]
        else:
            node[case["path"][-1]] = case["set"]
        passed = validator.is_valid(doc)
        failed |= passed
        where = "/".join(str(p) for p in case["path"])
        print(f"{'FAIL' if passed else 'OK  '} {'fixtures/library/invalid-cases.json':36} deve falhar: {where}")
        if passed:
            print(f"     erro  o schema aceitou: {case['why']}")
    return failed


def main():
    strict = "--strict" in sys.argv
    failed = False
    files = sorted(f for f in os.listdir(RES) if f.endswith(".json"))
    cache = {}
    for fn in files:
        if fn in NOT_LOADED:
            print(f"SKIP {fn:36} não carregado pelo app: {NOT_LOADED[fn]}")
            continue
        schema_name =next((s for pat, s in MAPPING if fnmatch.fnmatch(fn, pat)), None)
        if schema_name is None:
            print(f"FAIL {fn}: nenhum schema mapeado em scripts/validate_schemas.py")
            failed = True
            continue
        if schema_name not in cache:
            schema = json.load(open(os.path.join(SCHEMAS, schema_name), encoding="utf-8"))
            cache[schema_name] = (Draft202012Validator(schema), Draft202012Validator(closed(schema)))
        validator, closed_validator = cache[schema_name]
        data = json.load(open(os.path.join(RES, fn), encoding="utf-8"))

        errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
        extra = [e for e in closed_validator.iter_errors(data) if e.validator == "additionalProperties"]
        dups = []
        if isinstance(data, list):
            dups = [i for i, n in Counter(d.get("id") for d in data if isinstance(d, dict)).items() if n > 1]

        bad = bool(errors or dups or (strict and extra))
        failed |= bad
        count = f"{len(data)} registros" if isinstance(data, list) else "objeto"
        print(f"{'FAIL' if bad else 'OK  '} {fn:36} {schema_name:32} {count}")
        for e in errors[:10]:
            print(f"     erro  {path_of(e)}: {e.message[:160]}")
        if len(errors) > 10:
            print(f"     ... +{len(errors) - 10} erros")
        for i in dups[:10]:
            print(f"     erro  id duplicado: {i}")
        if extra:
            keys = Counter()
            for e in extra:
                for k in e.instance:
                    if k not in e.schema.get("properties", {}):
                        keys[k] += 1
            label = "erro " if strict else "aviso"
            print(f"     {label} campos ignorados pelo app: " + ", ".join(f"{k} ({n}x)" for k, n in keys.most_common()))
    failed |= check_library_fixtures()
    print("\nResultado:", "FALHOU" if failed else "OK")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
