@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo   Ru-Zeiterfassung - EXE Build
echo ============================================
echo Arbeitsordner: %cd%
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo FEHLER: Python wurde nicht gefunden.
    echo Bitte Python von https://www.python.org/downloads/ installieren
    echo und beim Setup "Add Python to PATH" anhaken.
    goto :ende_fehler
)
echo [OK] Python gefunden:
python --version

echo.
echo [1/3] Abhaengigkeiten installieren (customtkinter, pyinstaller)...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 goto :ende_fehler
echo [OK] Abhaengigkeiten installiert.

echo.
echo [2/3] Mit PyInstaller bauen (Ordner-Modus - weniger Virenscanner-Fehlalarme)...
set ICONOPT=
if exist "icon.ico" set ICONOPT=--icon "icon.ico"
set VEROPT=
if exist "version.txt" set VEROPT=--version-file "version.txt"
rmdir /s /q build dist >nul 2>&1
del /q "Ru-Zeiterfassung.spec" >nul 2>&1
python -m PyInstaller --noconfirm --onedir --windowed --noupx ^
    --name "Ru-Zeiterfassung" ^
    %ICONOPT% %VEROPT% ^
    --add-data "icon.ico;." ^
    ru_zeiterfassung.py
if errorlevel 1 goto :ende_fehler

if not exist "dist\Ru-Zeiterfassung\Ru-Zeiterfassung.exe" (
    echo FEHLER: Build lief durch, aber dist\Ru-Zeiterfassung\Ru-Zeiterfassung.exe fehlt.
    goto :ende_fehler
)

echo.
echo [3/3] ZIP-Paket erstellen...
powershell -NoProfile -Command "Compress-Archive -Path 'dist\Ru-Zeiterfassung' -DestinationPath 'dist\Ru-Zeiterfassung.zip' -Force"
if not exist "dist\Ru-Zeiterfassung.zip" goto :ende_fehler

echo.
echo Fertig!
echo   Ordner:  %cd%\dist\Ru-Zeiterfassung\  (Ru-Zeiterfassung.exe darin starten)
echo   ZIP:     %cd%\dist\Ru-Zeiterfassung.zip  (zum Weitergeben / Herunterladen)
echo.
pause
exit /b 0

:ende_fehler
echo.
echo Build ABGEBROCHEN. Fehler oben lesen/beheben und erneut ausfuehren.
pause
exit /b 1
