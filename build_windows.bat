@echo off
REM ==========================================================================
REM  Maple Lane Finds - Windows build
REM  Makes:  dist\MapleLaneFinds.exe              (the game, a single file)
REM          dist\MapleLaneFinds-Setup-X.Y.Z.exe  (the installer, needs Inno Setup 6)
REM  You need Python 3.10+ to BUILD. Players do NOT need Python.
REM ==========================================================================
setlocal
cd /d "%~dp0"
echo.
echo === Maple Lane Finds - Windows build ===
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found. Install Python 3.12 from https://www.python.org/downloads/
    echo and tick "Add python.exe to PATH" during setup, then run this file again.
    goto :fail
)

if not exist .venv (
    echo Creating a private Python environment in .venv ...
    python -m venv .venv || goto :fail
)
call .venv\Scripts\activate.bat || goto :fail

echo Installing build tools (first run takes a minute) ...
python -m pip install --quiet --upgrade pip || goto :fail
python -m pip install --quiet -r requirements.txt "pyinstaller>=6.6" || goto :fail

for /f "usebackq delims=" %%v in (`python -c "from game.version import VERSION; print(VERSION)"`) do set VERSION=%%v
echo Building version %VERSION% ...

python tools\make_version_info.py || goto :fail
pyinstaller --noconfirm --clean MapleLaneFinds.spec || goto :fail
if not exist dist\MapleLaneFinds.exe goto :fail
echo.
echo  [OK] Game built: dist\MapleLaneFinds.exe
echo.

REM ---- installer (Inno Setup 6) ----
set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not defined ISCC (
    where iscc >nul 2>nul && set "ISCC=iscc"
)
if not defined ISCC (
    echo  [!] Inno Setup 6 was not found, so the installer was skipped.
    echo      Get it free from https://jrsoftware.org/isdl.php , install it, then run this file again.
    goto :done
)
"%ISCC%" /Q /DMyAppVersion=%VERSION% installer\MapleLaneFinds.iss || goto :fail
echo  [OK] Installer built: dist\MapleLaneFinds-Setup-%VERSION%.exe

:done
echo.
echo All done!
if not defined CI pause
exit /b 0

:fail
echo.
echo  [X] The build stopped because of an error (see the messages above).
if not defined CI pause
exit /b 1
