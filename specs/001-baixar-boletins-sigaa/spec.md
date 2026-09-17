# Feature Specification: Baixar Boletins do SIGAA (IFFar)

**Feature Branch**: `001-baixar-boletins-sigaa`

**Created**: 2026-09-16

**Status**: Draft

**Input**: User description: "use @descricao.txt para planejar um script fácil de rodar localmente que receba um csv com lista de matriculas como entrada, crie uma pasta local escrita boletins, abra a url https://sig.iffarroupilha.edu.br/sigaa/ensino/tecnico_integrado/menu.jsf e baixe um a um em .pdf. use o arquivo @T10.csv para teste."

## Clarifications

### Session 2026-09-16

- Q: Should the script remember the SIGAA login between runs, or require a manual login every time it runs? → A: Remember the login (persistent browser profile); ask for manual login only when the session expires.
- Q: Should the script pause between matrículas to avoid overloading (or being blocked by) the SIGAA? → A: Fixed short pause (1–2 seconds) between matrículas.
- Q: How should the script handle a transient network failure (timeout/connection lost) while processing a matrícula? → A: Retry automatically up to 3 times; if it still fails, mark as "error" and continue to the next matrícula.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Baixar boletins em lote a partir de um CSV (Priority: P1)

Um usuário (servidor do IFFar) possui uma lista de matrículas de alunos em um arquivo CSV.
Ele executa um único comando local, que lê o CSV, cria uma pasta `boletins/` e, para cada
matrícula, abre o SIGAA, navega até "Ensino Técnico Integrado > Documentos de Discentes >
Emitir Boletim", busca o discente e salva o boletim oficial em PDF (Layout Paisagem, Escala
100), nomeando o arquivo com o número da matrícula (ex.: `2026304855.pdf`). Ao final, o
usuário recebe um relatório com quantos PDFs foram gerados, quais matrículas não foram
encontradas e onde os arquivos foram salvos.

**Why this priority**: É o objetivo central do projeto — automatizar a tarefa manual e
repetitiva de emitir boletins um a um no SIGAA.

**Independent Test**: Fornecer o `T10.csv` (31 matrículas) e verificar que a pasta
`boletins/` passa a conter um PDF por matrícula encontrada, com o conteúdo oficial
renderizado pelo SIGAA.

**Acceptance Scenarios**:

1. **Given** um CSV válido com coluna `Matricula`, **When** o usuário executa o comando, **Then** a pasta `boletins/` é criada e um PDF por matrícula encontrada é salvo com o nome `<matricula>.pdf`.
2. **Given** uma matrícula que não existe ou está inativa no SIGAA, **When** a busca não retorna resultado, **Then** a matrícula é registrada como "não encontrada" no relatório final e o processo continua para a próxima.
3. **Given** uma sessão SIGAA não autenticada, **When** o script detecta que não está logado, **Then** ele pausa e solicita que o usuário faça login manualmente antes de continuar.

---

### User Story 2 - Relatório de execução e retomada (Priority: P2)

Ao final (ou em caso de interrupção), o usuário consegue ver um resumo do que foi baixado e
reexecutar o script sem baixar novamente os PDFs já obtidos.

**Why this priority**: Garante confiabilidade e evita retrabalho em lotes grandes ou quando
o processo falha no meio.

**Independent Test**: Executar o script duas vezes seguidas e confirmar que a segunda
execução pula as matrículas já baixadas (ou informa que todas já existem), além de exibir o
resumo final.

**Acceptance Scenarios**:

1. **Given** que alguns PDFs já existem na pasta `boletins/`, **When** o script é reexecutado, **Then** ele pula as matrículas já baixadas e processa apenas as restantes (ou informa que todas já existem).
2. **Given** uma execução concluída, **When** o usuário lê o resumo, **Then** vê a contagem de sucessos, de falhas/não encontradas e o caminho da pasta de saída.

---

### Edge Cases

- CSV vazio ou sem a coluna `Matricula`: o script encerra com mensagem de erro clara.
- Matrículas duplicadas no CSV: processadas apenas uma vez, com aviso ao usuário.
- Matrícula malformada (espaços, caracteres inválidos): normalizada ou reportada como inválida.
- Conexão perdida ou timeout no meio do processo: o progresso é registrado e permite retomar sem refazer o que já foi concluído.
- Discente com múltiplos registros na busca: o script seleciona o discente correspondente à matrícula exata.
- Estrutura de menus do SIGAA alterada: a falha é reportada de forma legível em vez de travar silenciosamente.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O script DEVE aceitar como entrada o caminho de um arquivo CSV contendo uma coluna nomeada `Matricula`.
- **FR-002**: O script DEVE criar (se não existir) uma pasta local chamada `boletins` no diretório de execução para armazenar os PDFs.
- **FR-003**: O script DEVE abrir a URL `https://sig.iffarroupilha.edu.br/sigaa/ensino/tecnico_integrado/menu.jsf` e navegar até a funcionalidade "Emitir Boletim" (Documentos de Discentes).
- **FR-004**: Para cada matrícula, o script DEVE marcar o campo "Matrícula", preencher o número (limpando o valor anterior) e acionar a busca.
- **FR-005**: O script DEVE selecionar o discente correspondente na tabela de resultados ("Selecionar Discente") para abrir o Boletim Escolar.
- **FR-006**: O script DEVE gerar cada boletim a partir da visualização de impressão oficial do SIGAA, não reconstruindo o documento a partir de dados raspados.
- **FR-007**: O script DEVE salvar cada boletim como PDF com Layout Paisagem e Escala 100, nomeando o arquivo com o número da matrícula (`<matricula>.pdf`).
- **FR-008**: O script DEVE registrar em um relatório final as matrículas não encontradas ou com erro, em vez de ignorá-las silenciosamente.
- **FR-009**: O script DEVE exibir um resumo final com o total de PDFs gerados, as matrículas não encontradas e o caminho da pasta de saída.
- **FR-010**: O script DEVE reutilizar o login do SIGAA entre execuções (perfil persistente do navegador), solicitando login manual apenas quando a sessão expirar, sem lidar diretamente com credenciais.
- **FR-011**: O script DEVE aplicar uma pausa curta fixa (1–2 segundos) entre o processamento de uma matrícula e a próxima, para evitar sobrecarregar o SIGAA.
- **FR-012**: O script DEVE tentar novamente (até 3 tentativas) uma matrícula cujo processamento falhou por erro transitório de rede; se ainda falhar, DEVE marcá-la como "erro" no relatório e continuar com a próxima matrícula.

### Key Entities *(include if feature involves data)*

- **Matrícula**: Identificador único do discente no SIGAA; origem do nome do arquivo PDF.
- **Boletim (PDF)**: Documento oficial renderizado pelo SIGAA (notas, faltas, situação), salvo como `<matricula>.pdf`.
- **Relatório de execução**: Resumo final com sucessos, matrículas não encontradas, erros e caminho da pasta de saída.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um lote de 31 matrículas (`T10.csv`) é processado gerando um PDF por matrícula encontrada, com intervenção manual limitada ao login.
- **SC-002**: 100% dos PDFs gerados correspondem ao layout oficial do SIGAA (Paisagem, Escala 100).
- **SC-003**: O relatório final reporta 100% das matrículas não encontradas ou com erro, sem omissões.
- **SC-004**: Reexecutar o script não duplica trabalho: matrículas já baixadas são puladas na segunda execução.
- **SC-005**: O usuário consegue iniciar o processo com um único comando local, sem editar código.

## Assumptions

- O usuário possui uma conta SIGAA ativa e faz login manual apenas na primeira execução (ou quando a sessão expirar); a sessão é reutilizada entre execuções e o script não armazena nem manipula credenciais.
- O arquivo CSV usa a coluna exata `Matricula` (como em `T10.csv`).
- A pasta de saída `boletins/` é criada no diretório atual de execução.
- O ambiente alvo é Windows (computador do usuário), e o script deve ser simples de executar localmente.
- Layout Paisagem e Escala 100 são fixos para todos os boletins do lote.
- A estrutura de menus do SIGAA descrita em `descricao.txt` permanece estável durante a execução.
