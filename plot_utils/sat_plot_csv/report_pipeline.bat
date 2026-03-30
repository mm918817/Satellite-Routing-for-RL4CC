@echo off
setlocal enabledelayedexpansion

:: --- CONFIGURAZIONE PERCORSI ---
:: Percorso della cartella con i file originali
set "TARGET_DIR=C:\Users\teo\Desktop\ATesi\prova RL\results\DQN_SatEnvironment_2026-03-30_09-47-39o4_xrvz1"
:: Lo script assume di trovarsi nella stessa cartella dei file .py (A)json_to_csv, (B)csv_filter, (C)csv_dati
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"


echo ===    PIPELINE GENERAZIONE REPORT    ===
echo.

:: --- SCELTA MODALITÀ ---
set "MODE=json"
set /p "USER_INPUT=Scegli modalita [json/csv] (Premi Invio per default 'json'): "

if /i "%USER_INPUT%"=="csv" (
    set "MODE=csv"
)

echo.
echo Modalita selezionata: %MODE%
echo Preparazione file in corso...

:: --- LOGICA DI COPIA E ESECUZIONE ---

if /i "%MODE%"=="json" (
    :: Script A: Richiede evaluations.json -> Produce estratto_evaluations.csv
    echo Copia di evaluations.json da Target...
    copy /y "%TARGET_DIR%\evaluations.json" "%SCRIPT_DIR%\" >nul
    
    echo Esecuzione Script A...
    py json_to_csv.py
    
    :: Rinomina l'output di A affinché lo script C lo riconosca come input
    echo Preparazione input per Script C...
    move /y "estratto_evaluations.csv" "estratto_progress.csv" >nul

) else (
    :: Script B: Richiede progress.csv -> Produce estratto_progress.csv
    echo Copia di progress.csv da Target...
    copy /y "%TARGET_DIR%\progress.csv" "%SCRIPT_DIR%\" >nul
    
    echo Esecuzione Script B...
    py csv_filter.py
)

:: --- SCRIPT C ---
echo Esecuzione Script C...
py csv_dati.py

:: --- SPOSTAMENTO RISULTATI NELLA CARTELLA TARGET ---
echo Spostamento risultati finali nella cartella Target...

if exist "report_episodi_per_iterazione.txt" (
    move /y "report_episodi_per_iterazione.txt" "%TARGET_DIR%\" >nul
)
if exist "summary_iterations.csv" (
    move /y "summary_iterations.csv" "%TARGET_DIR%\" >nul
)

:: Pulizia file temporanei di lavoro
del /q "evaluations.json" 2>nul
del /q "progress.csv" 2>nul
del /q "estratto_progress.csv" 2>nul

echo.

echo ===    OPERAZIONE COMPLETATA    ===

pause