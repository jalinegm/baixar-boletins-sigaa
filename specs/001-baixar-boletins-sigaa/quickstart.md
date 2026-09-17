# Quickstart / Guia de Validação: Baixar Boletins do SIGAA (IFFar)

Cenários executáveis para validar a feature de ponta a ponta. Consulte o contrato em
[contracts/cli.md](contracts/cli.md) e o modelo em [data-model.md](data-model.md).

## Pré-requisitos

1. Python 3.12 instalado no Windows.
2. Dependências instaladas: `pip install -r requirements.txt`.
3. Navegador do Playwright instalado: `python -m playwright install chromium`.
4. Conta SIGAA ativa (o login é feito manualmente, nunca pelo script).

## Execução básica

```powershell
python -m baixar_boletins T10.csv
```

**Resultado esperado**:
1. A pasta `boletins/` é criada (se não existir).
2. Na primeira execução, o navegador abre; se não estiver logado, o script pausa para login manual.
3. Cada matrícula encontrada gera `boletins/<matricula>.pdf` (Paisagem, Escala 100).
4. O relatório final lista sucessos, não encontradas e o caminho da pasta.

## Cenários de validação

| # | Cenário | Comando / ação | Resultado esperado |
|---|---------|----------------|--------------------|
| 1 | Lote completo | `python -m baixar_boletins T10.csv` | 1 PDF por matrícula encontrada; contagem no relatório |
| 2 | Retomada idempotente | executar o mesmo comando de novo | matrículas já baixadas são puladas; sem duplicar |
| 3 | CSV sem coluna `Matricula` | apontar para CSV inválido | erro claro, código de saída `1` |
| 4 | Matrícula inexistente | CSV com uma matrícula fictícia | reportada como "não encontrada"; processo continua |
| 5 | Reprocessamento forçado | `python -m baixar_boletins T10.csv --reprocessar` | todos os PDFs são regravados |

## Verificação do resultado

- Abrir alguns PDFs gerados e confirmar que correspondem ao layout oficial do SIGAA (Paisagem).
- Conferir se o número de PDFs + não encontradas + erros = total de matrículas do CSV.
