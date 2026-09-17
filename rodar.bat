@echo off
setlocal
cd /d "%~dp0"

python -c "import playwright" 2>nul
if not errorlevel 1 goto pronto

echo Instalando dependencias - primeira vez...
python -m pip install -r requirements.txt
python -m playwright install chromium

:pronto
if not "%~1"=="" goto tem_csv
set /p CSV=Digite o nome do arquivo CSV (ex.: T10.csv): 
set "PYTHONPATH=%~dp0src"
python -m baixar_boletins "%CSV%"
goto fim

:tem_csv
set "PYTHONPATH=%~dp0src"
python -m baixar_boletins %*
goto fim

:fim
endlocal
