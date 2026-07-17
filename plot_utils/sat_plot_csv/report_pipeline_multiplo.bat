@echo off
setlocal enabledelayedexpansion

:: --- CONFIGURAZIONE PERCORSI ---
:: Lista delle cartelle separate da punto e virgola (;)
set "TARGET_DIRS=C:\Users\teo\Desktop\ATesi\prova RL\results\DQN_SatEnvironment_2026-06-21_14-02-30diyye21k;C:\Users\teo\Desktop\ATesi\prova RL\results\DQN_SatEnvironment_2026-06-21_14-02-238n5l_1r8"

:: Lo script assume di trovarsi nella stessa cartella degli script (A)json_to_csv.py, (B)csv_filter.py, (C)csv_dati.py
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo ===     MULTIPLE REPORT GENERATION PIPELINE     ===
echo.

:: --- SCELTA MODALITÀ (Una volta sola per tutti i target) ---
set "MODE=json"
set /p "USER_INPUT=Choose the mode [json/csv] (Press Enter for default 'json'): "

if /i "%USER_INPUT%"=="csv" (
    set "MODE=csv"
)

echo.
echo Selected Mode: %MODE%
echo.

:: --- CICLO SULLE CARTELLE TARGET ---
for %%D in ("%TARGET_DIRS:;=" "%") do (
    set "CURRENT_TARGET=%%~D"
    
    echo --------------------------------------------------
    echo Folder processing: !CURRENT_TARGET!
    echo --------------------------------------------------

    if /i "%MODE%"=="json" (
        if exist "!CURRENT_TARGET!\evaluations.json" (
            :: Script A: Richiede evaluations.json -> Produce estratto_evaluations.csv
            echo Copy of evaluations.json...
            copy /y "!CURRENT_TARGET!\evaluations.json" "%SCRIPT_DIR%\" >nul
            
            echo Script A execution...
            py json_to_csv.py

            :: Rinomina l'output di A affinché lo script C lo riconosca come input
            echo Preparing input for Script C..
            move /y "estratto_evaluations.csv" "estratto_progress.csv" >nul
        ) else (
            echo [ERROR] evaluations.json not found inside !CURRENT_TARGET!
        )
    ) else (
        if exist "!CURRENT_TARGET!\progress.csv" (
            :: Script B: Richiede progress.csv -> Produce estratto_progress.csv
            echo Copy of progress.csv...
            copy /y "!CURRENT_TARGET!\progress.csv" "%SCRIPT_DIR%\" >nul
            
            echo Script B execution...
            py csv_filter.py
        ) else (
            echo [ERROR] progress.csv not found inside !CURRENT_TARGET!
        )
    )

    :: --- SCRIPT C (Eseguito solo se i file precedenti sono stati creati) ---
    if exist "estratto_progress.csv" (
        echo Script C execution...
        py csv_dati.py

        echo Moving final results...
        if exist "report_episodi_per_iterazione.txt" (
            move /y "report_episodi_per_iterazione.txt" "!CURRENT_TARGET!\" >nul
        )
        if exist "summary_iterations.csv" (
            move /y "summary_iterations.csv" "!CURRENT_TARGET!\" >nul
        )
    )

    :: Pulizia file temporanei per il prossimo ciclo
    del /q "evaluations.json" 2>nul
    del /q "progress.csv" 2>nul
    del /q "estratto_progress.csv" 2>nul
    
    echo Completed for this folder.
    echo.
)

echo ===     ALL OPERATIONS COMPLETED     ===
pause