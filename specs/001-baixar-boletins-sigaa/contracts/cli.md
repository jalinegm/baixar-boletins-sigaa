# Contrato da CLI: Baixar Boletins do SIGAA (IFFar)

Contrato de interface da ferramenta de linha de comando.

## Invocação

```text
python -m baixar_boletins <caminho-do-csv> [opções]
```

### Argumentos

| Argumento | Obrigatório | Descrição |
|-----------|-------------|-----------|
| `caminho-do-csv` | Sim | Caminho do arquivo CSV com a coluna `Matricula` (ex.: `T10.csv`) |

### Opções

| Opção | Padrão | Descrição |
|-------|--------|-----------|
| `--pasta` | `boletins` | Pasta de saída dos PDFs |
| `--url` | `https://sig.iffarroupilha.edu.br/sigaa/verMenuTecnicoIntegrado.do` | URL base do SIGAA |
| `--reprocessar` | `false` | Se presente, reprocessa inclusive matrículas já concluídas |
| `--perfil` | `./.perfil-sigaa` | Diretório do perfil persistente do navegador (sessão) |

## Contrato de entrada (CSV)

- O arquivo DEVE conter uma coluna cujo cabeçalho é `Matricula`.
- As demais colunas são ignoradas.
- Valores são lidos como texto; espaços nas bordas são removidos; linhas vazias ignoradas.

## Contrato de saída

- Pasta de saída criada automaticamente se não existir.
- Um arquivo por matrícula encontrada, nomeado `<matricula>.pdf`.
- Arquivo de estado `boletins/.progresso.json` (retomada).

## Códigos de saída

| Código | Significado |
|--------|-------------|
| `0` | Execução concluída (com ou sem matrículas não encontradas, reportadas no relatório) |
| `1` | Erro fatal de entrada (CSV inexistente/vazio/sem coluna `Matricula`) |
| `2` | Erro de navegação não recuperável (estrutura do SIGAA não encontrada) |
| `3` | Sessão não autenticada e usuário não concluiu o login |

## Relatório final (stdout)

Ao final, a ferramenta imprime um resumo com:

- Total de matrículas processadas;
- Total de PDFs gerados (`sucesso`);
- Lista de matrículas `nao_encontrada` e `erro` (nenhuma é omitida);
- Caminho absoluto da pasta de saída.
