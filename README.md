# Boletins SIGAA · IFFar

Aplicativo local que baixa em lote os boletins escolares ("Boletim Escolar") do SIGAA do
IFFar, a partir de uma lista de matrículas em um arquivo CSV. Cada boletim é salvo em
PDF (Layout Paisagem, Escala 100) com o nome `<matricula>.pdf` na pasta `boletins/`.

## Interface gráfica no Windows

1. Baixe o [BoletinsSIGAA.exe da release mais recente](https://github.com/jalinegm/baixar-boletins-sigaa/releases/latest/download/BoletinsSIGAA.exe),
   salve em uma pasta onde você possa gravar arquivos e abra com dois cliques.
   O executável inclui o Chromium: **não é preciso instalar Python**.
2. Na etapa **Arquivo**, clique em **Escolher arquivo CSV**. Se precisar de um
   modelo, clique em **Baixar CSV de exemplo** e substitua as matrículas fictícias.
   Após a seleção, o aplicativo avança para **Acesso ao SIGAA**.
3. Clique em **Abrir SIGAA e baixar**. Faça o login no navegador que abrir.
   Quando o SIGAA pedir o vínculo, escolha o desejado, volte ao aplicativo e
   clique em **Já escolhi o vínculo · Continuar**.
4. Acompanhe o lote na etapa **Boletins**. Selecione uma matrícula marcada como
   **Baixado** para usar **Abrir PDF**, ou clique em **Abrir pasta de PDFs**.

O aplicativo mostra uma etapa por vez. Antes de iniciar o lote, **Voltar ao
arquivo** ou o indicador **Arquivo** permite trocar o CSV ou continuar com o
mesmo. Depois que o lote termina, também é possível clicar em **Arquivo** para
voltar. **Interromper após esta matrícula** encerra o lote após a operação atual;
uma nova execução mantém os PDFs já concluídos. Quando houver erros, use
**Tentar pendentes**.

### Formato do CSV

O arquivo precisa ter uma coluna `Matrícula` ou `Matricula`, com qualquer
combinação de maiúsculas e minúsculas. Coloque uma matrícula por linha:

```csv
Matrícula
123456
789012
```

Os números acima são fictícios. Matrículas duplicadas são ignoradas, e a
interface mostra quantos valores inválidos foram descartados.

### Arquivos gerados

Ao lado do executável, o aplicativo cria `boletins/` para PDFs e progresso e
`.perfil-sigaa/` para a sessão do navegador. Mantenha o executável em uma pasta
com permissão de gravação. **Não publique PDFs nem o perfil do navegador:**
eles contêm dados pessoais e de acesso.

## Executar pelo código-fonte

- **Windows** (é o ambiente de uso previsto).
- **Python 3.10 ou superior** instalado. Se não tiver, baixe em
  <https://www.python.org/downloads/> e, na instalação, marque a opção
  **"Add Python to PATH"**.
- **Acesso ao SIGAA** com uma conta ativa (o login é feito por você, nunca pelo script).

### Abrir a interface ou o terminal

Dê dois cliques em `abrir_gui.bat` para abrir a interface gráfica a partir do
código-fonte. Na primeira execução, o script instala as dependências e o
Chromium; isso pode levar alguns minutos.

Para usar o terminal, dê dois cliques em `rodar.bat` e informe o caminho do CSV,
ou execute no PowerShell, dentro da pasta do projeto:

```powershell
.\rodar.bat matriculas.csv
```

Para gerar o executável portátil, dê dois cliques em `build_windows.bat`. O
resultado fica em `dist/BoletinsSIGAA.exe`.

No terminal, faça o login manualmente no navegador, escolha o vínculo e
pressione Enter para continuar. Cada boletim é salvo como `<matricula>.pdf` em
`boletins/` (paisagem, escala 100%). O progresso e o resumo aparecem no terminal.

## Opções da linha de comando

| Opção | Descrição |
|-------|-----------|
| `csv` | Caminho do arquivo CSV (obrigatório). |
| `--pasta` | Pasta de saída dos PDFs (padrão: `boletins`). |
| `--url` | URL do SIGAA (padrão já configurado para o IFFar). |
| `--reprocessar` | Regrava PDFs de matrículas já concluídas. |
| `--perfil` | Diretório do perfil do navegador (padrão: `./.perfil-sigaa`). |

Exemplo:

```powershell
.\rodar.bat matriculas.csv --pasta saida --reprocessar
```

## Como funciona

- O login fica salvo no perfil persistente do navegador (`.perfil-sigaa/`). Nas próximas
  execuções, o login é reaproveitado; você só faz login de novo quando a sessão expirar.
- O script navega até **Emitir Boletim**, busca cada matrícula, abre o boletim e salva o
  PDF a partir da página oficial do SIGAA.
- O progresso fica salvo em `boletins/.progresso.json`. Se a execução for interrompida,
  rodar de novo **pula as matrículas já baixadas**.
- Matrículas não encontradas ou com erro são registradas no resumo e o processo continua
  com as demais.

## Solução de problemas

- **Python não é reconhecido ao usar os arquivos `.bat`:** reinstale marcando
  **Add Python to PATH**. O `.exe` da release dispensa Python.
- **Chromium não abre ao usar o código-fonte:** rode no terminal
  `python -m playwright install chromium`.
- **Login não concluído dentro do tempo limite**: o script aguarda até 10 minutos; faça o
  login na janela aberta e aguarde.
- **"Comportamento Inesperado" no SIGAA**: a sessão pode ter expirado; feche, rode
  novamente e faça login.

## Estrutura do projeto

```
projeto-boletim/
├── abrir_gui.bat        # abre a interface gráfica por duplo clique
├── build_windows.bat    # gera o executável portátil para distribuição
├── rodar.bat            # atalho para executar (instala dependências na 1ª vez)
├── requirements.txt     # dependências Python
├── pyproject.toml       # definição do pacote
└── src/baixar_boletins/ # código-fonte
```
