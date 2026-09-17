# Data Model: Baixar Boletins do SIGAA (IFFar)

Modelo de dados leve para a ferramenta CLI. Não há banco de dados; a persistência é feita em
arquivos (PDFs na pasta `boletins/` e estado de execução em `boletins/.progresso.json`).

## Entidades

### Matricula

Identificador único do discente no SIGAA.

| Campo | Tipo | Regras |
|-------|------|--------|
| `numero` | string (10 dígitos) | Obrigatório; vindo da coluna `Matricula` do CSV; normalizado (trim); duplicados removidos |
| `valida` | boolean | `false` se vazia ou malformada (registrada como inválida no relatório) |

### Boletim (PDF)

Documento oficial renderizado pelo SIGAA.

| Campo | Tipo | Regras |
|-------|------|--------|
| `matricula` | string | Referência à matrícula de origem |
| `arquivo` | caminho | `boletins/<matricula>.pdf` |
| `layout` | string fixo | `Paisagem` (landscape), `Escala 100` (scale 1.0) |

### ResultadoExecucao

Estado agregado da execução, refletido no arquivo de estado e no relatório final.

| Campo | Tipo | Regras |
|-------|------|--------|
| `por_matricula` | mapa `matricula -> status` | `pendente`, `sucesso`, `nao_encontrada`, `erro`, `invalida` |
| `total_sucesso` | inteiro | Quantidade de PDFs gerados |
| `total_nao_encontradas` | inteiro | Matrículas sem resultado na busca |
| `total_erros` | inteiro | Falhas de rede/navegação |
| `pasta_saida` | caminho | `boletins/` |

## Transições de estado (por matrícula)

```text
pendente ──(busca ok + PDF salvo)──▶ sucesso
pendente ──(busca sem resultado)────▶ nao_encontrada
pendente ──(falha de rede/timeout)──▶ erro          (retomável)
pendente ──(formato inválido)───────▶ invalida
```

Regra de retomada: apenas matrículas em `pendente` ou `erro` são reprocessadas; `sucesso`,
`nao_encontrada` e `invalida` são preservadas entre execuções.

## Relações

- Um CSV (entrada) contém N `Matricula`.
- Cada `Matricula` processada gera 0 ou 1 `Boletim (PDF)`.
- A execução produz 1 `ResultadoExecucao` (relatório final + arquivo de estado).
