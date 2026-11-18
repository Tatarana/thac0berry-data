#!/usr/bin/env python3
"""Corrige tabelas quebradas do data/rules.json (auditoria de 2026-11-18).

O usuário encontrava tabelas quebradas no uso de vez em quando. Uma varredura comparou
as 560 tabelas estruturadas e as tabelas em markdown do `content` com o original da wiki
(dump em thac0berry-data-mining), pareadas pelo conteúdo das células. As correções
CERTAS ficam em `scripts/rules_table_fixes_2026_11.json` (59; as suspeitas ficaram de
fora: DMG Tables 12, 14 e 17, cujo "+" pode ser costume da wiki, e linhas partidas em
markdown). Defeitos corrigidos:

- sinal perdido nos modificadores ("+3" virou "3"): 21 tabelas, inclusive as de atributo
  do PHB, Combat Modifiers, Initiative e Morale;
- células de modelo da wiki ({{Yes}}/{{No}}) descartadas: DMG Table 23 inteira vazia;
- linhas de seção que viraram rótulo (PHB Table 66, Climbing Modifiers: o modificador sumia);
- seções e grupos de cabeçalho perdidos, rowspan achatado, células deslocadas, nomes
  cortados no primeiro espaço (PHB Table 45), restos como "&nbsp;" e datas do Excel
  ("Feb-16" no lugar de "2-16");
- tabelas sem título ("Table") que a web não distinguia: ganham o título, e o
  `[TABLE_REF: Table]` correspondente no `content` (na mesma ordem) passa a usá-lo;
- tabelas em markdown no `content` com dois cabeçalhos colados (35 colunas para 20 dados).

Cada correção confere o "antes"; se o dado já mudou, para e avisa. Rodar de novo não muda
nada (o que já está corrigido é pulado).

Uso:  python scripts/fix_rules_tables_2026_11.py [--dry-run]
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RULES = os.path.join(ROOT, "data", "rules.json")
FIXES = os.path.join(ROOT, "scripts", "rules_table_fixes_2026_11.json")


def table_fix(rule, fix):
    t = rule["tables"][fix["tableIndex"]]
    current = {"headers": t["headers"], "rows": t["rows"]}
    after = {"headers": fix["after"]["headers"], "rows": fix["after"]["rows"]}
    if current == after:
        return False
    before = {"headers": fix["before"]["headers"], "rows": fix["before"]["rows"]}
    if current != before:
        sys.exit(f"{rule['id']} tabela {fix['tableIndex']}: o dado não é o 'antes' esperado")
    t["headers"], t["rows"] = after["headers"], after["rows"]
    return True


def title_fix(rule, fix, ref_slots, original_titles):
    t = rule["tables"][fix["tableIndex"]]
    new = fix["after"]["title"]
    if t["title"] == new:
        return False
    if t["title"] != fix["before"]["title"]:
        sys.exit(f"{rule['id']} tabela {fix['tableIndex']}: título inesperado {t['title']!r}")
    # a n-ésima tabela "Table" corresponde ao n-ésimo "[TABLE_REF: Table]" do texto
    # posição entre as tabelas de mesmo título nos dados ORIGINAIS (renomear uma não desloca as outras)
    titles = original_titles[rule["id"]]
    order = [i for i, x in enumerate(titles) if x == t["title"]].index(fix["tableIndex"])
    ref_slots.setdefault(rule["id"], []).append((order, new))
    t["title"] = new
    return True


def apply_refs(rule, slots):
    parts = rule["content"].split("[TABLE_REF: Table]")
    if len(parts) - 1 < max(o for o, _ in slots) + 1:
        sys.exit(f"{rule['id']}: faltam [TABLE_REF: Table] no texto")
    names = dict(slots)
    out = parts[0]
    for i, rest in enumerate(parts[1:]):
        out += f"[TABLE_REF: {names.get(i, 'Table')}]" + rest
    rule["content"] = out


def header_fix(rule, fix):
    field = fix.get("field", "content")
    text = rule[field]
    old = fix["before"]["headerLine"] + "\n" + fix["before"]["separatorLine"]
    new = fix["after"]["headerLine"] + "\n" + fix["after"]["separatorLine"]
    if new in text:
        return False
    if text.count(old) != 1:
        sys.exit(f"{rule['id']}: cabeçalho markdown não encontrado uma única vez")
    rule[field] = text.replace(old, new)
    return True


def main():
    rules = json.load(open(RULES, encoding="utf-8"))
    by_id = {r["id"]: r for r in rules}
    fixes = json.load(open(FIXES, encoding="utf-8"))
    changed, ref_slots = 0, {}
    original_titles = {r["id"]: [t["title"] for t in r.get("tables") or []] for r in rules}
    for fix in fixes:
        rule = by_id[fix["ruleId"]]
        kind = fix.get("kind")
        if kind == "table_title":
            changed += title_fix(rule, fix, ref_slots, original_titles)
        elif kind == "markdown_table_header":
            changed += header_fix(rule, fix)
        else:
            changed += table_fix(rule, fix)
    for rule_id, slots in ref_slots.items():
        apply_refs(by_id[rule_id], slots)
    print(f"{changed} correções aplicadas de {len(fixes)}")
    if "--dry-run" not in sys.argv:
        with open(RULES, "w", encoding="utf-8", newline="\n") as f:
            json.dump(rules, f, ensure_ascii=False, indent=2)
            f.write("\n")


if __name__ == "__main__":
    main()
