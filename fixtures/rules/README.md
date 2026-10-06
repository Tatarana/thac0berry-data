# Valores de referência das regras de jogo

`rules-fixtures.json` é **gerado pelo código Swift do app iPad**
(`thac0berry-ipad/Scripts/rules_fixtures/main.swift`, compilado no CI de lá):
o resultado de cada regra para todas as entradas. Tabelas de atributo (1 a 25,
com 18/01 a 18/00), THAC0, saves, slots de magia, XP, proficiências, perícias de
ladrão e Level Changes, por classe e nível (0 a 21, bordas incluídas), mais as
tabelas das páginas de referência da ficha.

A versão web reimplementa as regras em TypeScript e o CI de lá compara com este
arquivo, valor a valor. Assim as duas implementações não divergem sem ninguém notar.

**Não edite à mão.** Mudou uma regra no iPad: o workflow `rules-fixtures.yml` de lá
acusa a diferença e publica o arquivo novo no branch `generated/rules-fixtures` do
repo `thac0berry-ipad`; copie de lá para cá.

Exceção conhecida: o ajuste racial de ladrão para **Half-Elf** fica de fora, porque
no iPad ele depende da ordem de um dicionário e muda a cada execução (bug registrado
no `TODO.md` do iPad).
