# Research: Baixar Boletins do SIGAA (IFFar)

Resolução das incógnitas do Technical Context e escolhas de tecnologia para a automação de emissão
em lote de boletins do SIGAA.

## 1. Automação de navegador (core)

- **Decision**: Playwright com **contexto persistente** (`launch_persistent_context`) apontando para
  um diretório de perfil local.
- **Rationale**: O SIGAA é uma aplicação JSF *stateful* (a navegação é feita por postbacks na mesma
  URL, não por links profundos), e o `descricao.txt` exige usar a sessão autenticada do usuário sem
  manipular credenciais. O contexto persistente preserva cookies/sessão entre execuções: na primeira
  execução o usuário faz login manualmente; nas seguintes, a sessão já está ativa.
- **Alternatives considered**:
  - *Selenium*: rejeitado — controle de PDF/impressão mais limitado (não expõe `scale` diretamente) e
    setup mais frágil no Windows.
  - *Requisições HTTP diretas (requests/httpx) com parsing do ViewState*: rejeitado — frágil diante
    de mudanças do JSF, não renderiza o documento oficial e contraria o `descricao.txt` (que manda
    dirigir o navegador).
  - *Anexar ao Chrome do usuário via CDP (remote-debugging-port)*: alternativa viável, porém exige
    reabrir o Chrome com flag especial; o contexto persistente é mais simples de rodar localmente.

## 2. Geração do PDF autêntico

- **Decision**: Renderizar via `page.pdf({ landscape: true, scale: 1.0, print_background: true })`
  na página/aba do Boletim Escolar (após acionar a visualização de impressão do SIGAA).
- **Rationale**: O `page.pdf()` do Playwright respeita o CSS de impressão do SIGAA, produzindo o
  documento oficial idêntico ao que sairia do diálogo de impressão, sem depender de diálogo nativo do
  sistema. `landscape: true` equivale a "Paisagem" e `scale: 1.0` a "Escala 100".
- **Alternatives considered**:
  - *Automatizar o diálogo nativo de impressão (Ctrl+P → Salvar como PDF)*: frágil e dependente do
    SO; usado apenas como fallback se o `page.pdf()` não capturar o layout correto.

## 3. Reuso de sessão / autenticação

- **Decision**: Detectar se a página já está autenticada; se não, pausar e solicitar login manual
  antes de prosseguir.
- **Rationale**: Atende a `FR-010` e a premissa do `descricao.txt` ("não lidar com credenciais").
- **Alternatives considered**:
  - *Armazenar usuário/senha e fazer login programático*: rejeitado (viola G2 e o `descricao.txt`).

## 4. Retomada / idempotência

- **Decision**: Manter um arquivo de estado `boletins/.progresso.json` com o status de cada matrícula
  (`pendente`, `sucesso`, `nao_encontrada`, `erro`). Ao reexecutar, pular as concluídas com sucesso.
- **Rationale**: Atende a `SC-004` e o caso de interrupção por rede/timeout.
- **Alternatives considered**:
  - *Inferir apenas pela presença do arquivo PDF*: rejeitado — não distingue "não encontrada"
    (que deve ser registrada) de "já baixada".

## 5. Leitura do CSV

- **Decision**: Usar a biblioteca `csv` da stdlib (ou `pandas` apenas se já estiver no projeto) para
  ler a coluna `Matricula`; normalizar espaços e deduplicar.
- **Rationale**: Simplicidade e zero dependência extra para um CSV simples como o `T10.csv`.

## 6. Dependências e versões

- **Decision**: Python 3.12 + Playwright (instalado via `pip`), navegador Chromium instalado via
  `playwright install chromium`.
- **Rationale**: Playwright é a opção mais robusta para automação + PDF no Windows e tem API síncrona
  simples para um script CLI.
