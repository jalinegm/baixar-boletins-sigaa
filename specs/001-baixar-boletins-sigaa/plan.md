# Implementation Plan: Baixar Boletins do SIGAA (IFFar)

**Branch**: `001-baixar-boletins-sigaa` | **Date**: 2026-09-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-baixar-boletins-sigaa/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

Automatizar a emissão em lote de boletins escolares do SIGAA IFFar (Ensino Técnico Integrado).
Um comando local lê um CSV com a coluna `Matricula`, cria a pasta `boletins/`, navega no SIGAA até
"Emitir Boletim" e, para cada matrícula, baixa o boletim oficial em PDF (Paisagem, Escala 100) com o
nome `<matricula>.pdf`. Abordagem técnica: automação de navegador com reuso da sessão autenticada do
usuário (sem manipular credenciais), renderização do PDF a partir da visualização de impressão do
próprio SIGAA e retomada idempotente (matrículas já baixadas são puladas).

## Technical Context

**Language/Version**: Python 3.12 (disponível no ambiente Windows do usuário)

**Primary Dependencies**: Playwright (automação de navegador, contexto persistente para reuso de
sessão, `page.pdf()` para renderização em Paisagem/Escala 100)

**Storage**: Sistema de arquivos — pasta `boletins/` (PDFs) + arquivo de estado local
`boletins/.progresso.json` (retomada/relatório)

**Testing**: pytest (testes unitários de parsing/validação de CSV e de relatório; testes de
integração "secos" com páginas simuladas do SIGAA)

**Target Platform**: Windows 10/11 (desktop do usuário)

**Project Type**: CLI (ferramenta de linha de comando, execução local)

**Performance Goals**: Processar um lote de ~31 matrículas (T10.csv) em minutos, sem exigência
estrita de latência; cada matrícula na ordem de segundos

**Constraints**: Não armazenar/transmitir credenciais; reusar a sessão SIGAA já autenticada; manter
Paisagem + Escala 100 em todos os PDFs; tolerar falhas de rede retomando sem refazer o concluído

**Scale/Scope**: Lotes de dezenas a poucas centenas de matrículas por execução; ferramenta de uso
individual (não é serviço compartilhado)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

A constituição do projeto (`.specify/memory/constitution.md`) ainda é o scaffold de placeholder não
preenchido — não define princípios nem gates específicos. Até que seja populada, este plano aplica
os seguintes gates padrão (violação = ERROR):

- **G1 — Ferramenta de propósito único**: nenhuma abstração/framework além do necessário para o
  fluxo de automação.
- **G2 — Sem manipulação de credenciais**: o script NÃO armazena nem transmite usuário/senha.
- **G3 — Saída autêntica**: PDFs DEVEM vir da visualização de impressão do SIGAA, nunca reconstruídos
  a partir de dados raspados.

**Resultado**: todos os gates passam; nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/001-baixar-boletins-sigaa/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
boletins/                     # pasta de saída (criada em tempo de execução)
src/baixar_boletins/
├── __init__.py
├── cli.py                    # ponto de entrada / parsing de argumentos
├── input_csv.py              # leitura e validação do CSV (coluna "Matricula")
├── sigaa_nav.py              # navegação no SIGAA e busca de discente
├── pdf_render.py             # renderização do boletim em PDF (Paisagem, Escala 100)
└── report.py                 # estado de retomada + relatório final
tests/
├── unit/                     # CSV, relatório, normalização de matrícula
└── integration/              # páginas simuladas do SIGAA
requirements.txt
```

**Structure Decision**: Projeto único (CLI). Um pacote `baixar_boletins` com módulos separados por
responsabilidade (entrada, navegação, renderização, relatório), testes unit e de integração, e a
pasta de saída `boletins/` na raiz do repositório.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

Nenhuma violação — seção não aplicável.
