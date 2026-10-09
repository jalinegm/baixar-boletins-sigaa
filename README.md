# Baixar Boletins do SIGAA (IFFar)

Script local que baixa em lote os boletins escolares ("Boletim Escolar") do SIGAA do
IFFar, a partir de uma lista de matrículas em um arquivo CSV. Cada boletim é salvo em
PDF (Layout Paisagem, Escala 100) com o nome `<matricula>.pdf` na pasta `boletins/`.

## O que você precisa

- **Windows** (é o ambiente de uso previsto).
- **Python 3.10 ou superior** instalado. Se não tiver, baixe em
  <https://www.python.org/downloads/> e, na instalação, marque a opção
  **"Add Python to PATH"**.
- **Acesso ao SIGAA** com uma conta ativa (o login é feito por você, nunca pelo script).

## Como usar (passo a passo)

### 1. Prepare o arquivo CSV

Crie um arquivo CSV (por exemplo, `matriculas.csv`) com uma coluna chamada
`Matrícula` ou `Matricula`. Maiúsculas e minúsculas também são aceitas
(`MATRICULA`, `matricula`, etc.). Na interface gráfica, clique em
**Baixar CSV de exemplo** para salvar um modelo com matrículas fictícias.

Exemplo de conteúdo (`T10.csv`):

```csv
Matricula
2026304855
2026305084
2026305674
```

Coloque o arquivo na mesma pasta do projeto (ou anote o caminho dele).

### 2. Execute

Há duas formas:

**Interface gráfica (recomendada):** dê um duplo clique em `abrir_gui.bat`.
Na janela, clique em **Escolher arquivo CSV** e depois em **Abrir SIGAA e baixar**. Na
primeira execução, o arquivo instala o Playwright e o Chromium automaticamente;
isso pode demorar alguns minutos. O Python 3.10 ou superior ainda precisa estar
instalado, conforme a seção anterior.

Para distribuir a alguém que não tenha Python, execute `build_windows.bat` uma
vez em um computador Windows. Entregue o arquivo `dist/BoletinsSIGAA.exe`; a
pessoa abre a janela com um duplo clique no executável. O Chromium acompanha o
arquivo, por isso ele é grande. Os PDFs e o perfil de acesso ficam na pasta do
executável, que deve estar em um local onde a pessoa possa gravar arquivos.

**Terminal:** dê um duplo clique em `rodar.bat`. Ele vai pedir o nome do CSV
(ex.: `T10.csv`).

**Ou pela linha de comando no PowerShell**, dentro da pasta do projeto.

Para abrir o PowerShell na pasta do projeto: abra a pasta no Explorador de Arquivos,
segure `Shift` e clique com o botão direito em um espaço vazio, depois escolha
**"Abrir janela do PowerShell aqui"**. Ou, já com o PowerShell aberto, navegue até a pasta:

```powershell
cd "C:\caminho\para\projeto-boletim"
```

Em seguida, rode o comando com o nome do seu CSV:

```powershell
.\rodar.bat T10.csv
```

Para passar opções adicionais, acrescente-as após o nome do CSV:

```powershell
.\rodar.bat T10.csv --pasta saida --reprocessar
```

Na primeira execução, o `rodar.bat` instala automaticamente as dependências e o
navegador (Chromium). Isso acontece só uma vez e pode demorar alguns minutos.

### 3. Faça o login e escolha o vínculo

- O navegador abre sozinho na tela do SIGAA.
- Se não estiver logado, **faça o login manualmente** na janela que abriu.
- Após o login, o SIGAA mostra a tela de **escolha de vínculo** (`vinculos.jsf`).
  Escolha o vínculo/perfil desejado. Na interface gráfica, volte à janela do
  aplicativo e clique em **Já escolhi o vínculo · Continuar**. No terminal,
  pressione Enter.

### 4. Acompanhe o resultado

O script busca uma matrícula por vez, gera o PDF em `boletins/` e mostra o
resultado de cada matrícula. Na interface gráfica, selecione uma matrícula
baixada e clique em **Abrir PDF** (ou pressione Enter). O botão
**Interromper após esta matrícula**
termina a operação atual antes de fechar o navegador; uma nova execução retoma
as matrículas pendentes. No terminal, ao final, aparece um resumo:

```
Resumo da execução:
  Total processado: 31
  PDFs gerados: 30
  Não encontradas: 1
  Erros: 0
  Pasta de saída: ...\boletins
```

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
.\rodar.bat T10.csv --pasta saida --reprocessar
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

- **"python" não é reconhecido**: o Python não está no PATH. Reinstale marcando
  "Add Python to PATH", ou use o caminho completo do executável.
- **Navegador não abre / erro de Playwright**: rode no terminal
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
├── T10.csv              # CSV de exemplo
└── src/baixar_boletins/ # código-fonte
```
