# AGENTS.md

Guia para agentes de IA (e desenvolvedores) que forem trabalhar neste repositório.

## Visão geral

Script local (Python + Playwright) que baixa em lote os boletins escolares do SIGAA
IFFar a partir de uma lista de matrículas em CSV, gerando um PDF por matrícula em
`boletins/`. O login é feito manualmente pelo usuário; o script não lida com credenciais.

## Como executar

Há duas formas equivalentes:

```powershell
# Forma simples (recomendada para o usuário final)
.\rodar.bat T10.csv

# Direto pelo módulo (exige que src/ esteja no PYTHONPATH)
$env:PYTHONPATH = "src"
python -m baixar_boletins T10.csv
```

O `rodar.bat` instala `requirements.txt` e o Chromium do Playwright na primeira execução.

## Dependências e instalação

```powershell
python -m pip install -r requirements.txt
python -m playwright install chromium
```

Não há suíte de testes, linter ou type-checker configurados neste projeto.

## Estrutura

```
src/baixar_boletins/
├── cli.py        # argument parsing, orquestração do lote e resumo final
├── sigaa_nav.py  # navegação no SIGAA (login, vínculo, busca, boletim)
├── input_csv.py  # leitura/validação do CSV (coluna "Matricula")
├── pdf_render.py # geração do PDF a partir da página (Paisagem, Escala 100)
├── report.py     # controle de progresso (.progresso.json) e resumo
├── __main__.py   # entry point para `python -m baixar_boletins`
└── __init__.py
```

## Convenções

- Mensagens exibidas ao usuário em **português**; código e identificadores em inglês.
- Não adicionar comentários desnecessários ao código.
- Manter o estilo existente (PEP 8, nomes em `snake_case`).
- O fluxo SIGAA é stateful (JSF): use os seletores/constantes já definidos em
  `sigaa_nav.py` e não reestruture a navegação sem necessidade.
- O perfil persistente do navegador (`.perfil-sigaa/`), a saída (`boletins/`) e os
  artefatos de depuração (`debug/`) são ignorados pelo git.

## Pontos de atenção

- O login é manual; nunca implementar envio automático de credenciais.
- Após o login, o SIGAA exibe a tela de vínculo (`vinculos.jsf`); o script espera o
  usuário escolher o vínculo e pressionar Enter antes de iniciar a busca.
- Os PDFs contêm dados de alunos: não commitá-los nem os deixar visíveis no GitHub.
