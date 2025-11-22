@echo off
REM
REM Script di avvio Fauna Manager per Windows
REM Verifica dipendenze, installa se necessario e avvia l'interfaccia
REM

setlocal enabledelayedexpansion

REM Banner
echo ========================================
echo   Fauna Manager - pyArchInit
echo   Gestione Schede Faunistiche
echo ========================================
echo.

REM Ottieni la directory dello script
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM 1. Verifica Python
echo [i] Verifica installazione Python...

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo [+] Python !PYTHON_VERSION! trovato
) else (
    where py >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        set PYTHON_CMD=py
        for /f "tokens=2" %%i in ('py --version 2^>^&1') do set PYTHON_VERSION=%%i
        echo [+] Python !PYTHON_VERSION! trovato
    ) else (
        echo [-] Python non trovato!
        echo [i] Installa Python 3.7+ da https://www.python.org/
        pause
        exit /b 1
    )
)

REM 2. Verifica pip
echo [i] Verifica pip...

%PYTHON_CMD% -m pip --version >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set PIP_CMD=%PYTHON_CMD% -m pip
    echo [+] pip trovato
) else (
    echo [-] pip non trovato!
    pause
    exit /b 1
)

REM 3. Verifica dipendenze
echo [i] Verifica dipendenze Python...

set MISSING_DEPS=
set DEPS_COUNT=0

REM Controlla PyQt5
%PYTHON_CMD% -c "import PyQt5" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [!] PyQt5 non installato
    set MISSING_DEPS=!MISSING_DEPS! PyQt5
    set /a DEPS_COUNT+=1
)

REM Controlla reportlab
%PYTHON_CMD% -c "import reportlab" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [!] reportlab non installato
    set MISSING_DEPS=!MISSING_DEPS! reportlab
    set /a DEPS_COUNT+=1
)

REM Se ci sono dipendenze mancanti
if !DEPS_COUNT! GTR 0 (
    echo.
    echo [!] Dipendenze mancanti:!MISSING_DEPS!
    echo.
    set /p INSTALL_DEPS="Vuoi installarle ora? (s/n): "

    if /i "!INSTALL_DEPS!"=="s" (
        echo [i] Installazione dipendenze...

        if exist requirements.txt (
            %PIP_CMD% install -r requirements.txt
        ) else (
            %PIP_CMD% install PyQt5 reportlab
        )

        if !ERRORLEVEL! EQU 0 (
            echo [+] Dipendenze installate con successo
        ) else (
            echo [-] Errore nell'installazione delle dipendenze
            pause
            exit /b 1
        )
    ) else (
        echo [!] Alcune funzionalita potrebbero non funzionare senza le dipendenze
    )
)

echo.

REM 4. Verifica database pyArchInit
echo [i] Verifica database pyArchInit...

set DB_PATH=%USERPROFILE%\pyarchinit\pyarchinit_DB_folder\pyarchinit_db.sqlite

if not exist "%DB_PATH%" (
    echo [!] Database pyArchInit non trovato in: %DB_PATH%
    echo [i] Il database verra selezionato all'avvio dell'interfaccia
) else (
    echo [+] Database pyArchInit trovato

    REM Verifica se le tabelle fauna esistono
    %PYTHON_CMD% -c "import sqlite3; conn = sqlite3.connect(r'%DB_PATH%'); cursor = conn.cursor(); cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\" AND name=\"fauna_table\"'); result = cursor.fetchone(); conn.close(); exit(0 if result else 1)" >nul 2>nul

    if !ERRORLEVEL! EQU 0 (
        echo [+] Tabelle fauna gia installate
    ) else (
        echo [!] Tabelle fauna non installate
        set /p INSTALL_TABLES="Vuoi installarle ora? (s/n): "

        if /i "!INSTALL_TABLES!"=="s" (
            echo [i] Installazione tabelle...
            %PYTHON_CMD% install_db.py

            if !ERRORLEVEL! EQU 0 (
                echo [+] Tabelle installate con successo
            ) else (
                echo [-] Errore nell'installazione delle tabelle
                pause
                exit /b 1
            )
        )
    )
)

echo.

REM 5. Avvio interfaccia
echo [+] Avvio Fauna Manager...
echo.

REM Aggiungi directory corrente al PYTHONPATH
set PYTHONPATH=%SCRIPT_DIR%;%PYTHONPATH%

REM Avvia l'interfaccia
%PYTHON_CMD% qgis_integration.py

REM Codice di uscita
set EXIT_CODE=%ERRORLEVEL%

echo.
if %EXIT_CODE% EQU 0 (
    echo [+] Fauna Manager chiuso correttamente
) else (
    echo [-] Fauna Manager chiuso con errori (codice: %EXIT_CODE%)
)

pause
exit /b %EXIT_CODE%
