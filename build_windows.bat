@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 goto erro

python -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto erro

set "PLAYWRIGHT_BROWSERS_PATH=0"
python -m playwright install chromium
if errorlevel 1 goto erro

python -m PyInstaller --noconfirm --clean --onefile --windowed --name BoletinsSIGAA --paths src --icon assets/boletim.ico --add-data "assets/iffar-branco-small.png;assets" --add-data "assets/boletim.ico;assets" app.pyw
if errorlevel 1 goto erro

echo.
echo Aplicativo pronto em dist\BoletinsSIGAA.exe
pause
exit /b 0

:erro
echo Nao foi possivel gerar o aplicativo.
pause
exit /b 1
