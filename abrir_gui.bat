@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo Python nao encontrado. Instale Python 3.10 ou superior com a opcao "Add Python to PATH".
    pause
    exit /b 1
)

python -c "import playwright" >nul 2>nul
if errorlevel 1 (
    echo Preparando o aplicativo. Isso pode demorar alguns minutos na primeira vez...
    python -m pip install -r requirements.txt
    if errorlevel 1 goto erro
)

python -m playwright install chromium
if errorlevel 1 goto erro

set "PYTHONPATH=%~dp0src"
start "" pythonw -m baixar_boletins.gui
if errorlevel 1 goto erro
exit /b 0

:erro
echo Nao foi possivel preparar o aplicativo. Veja a mensagem acima.
pause
exit /b 1
