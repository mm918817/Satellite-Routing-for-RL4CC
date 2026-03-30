@echo off
setlocal enabledelayedexpansion

:: --- CONFIGURAZIONE PERCORSI ---
:: Lista delle cartelle separate da punto e virgola (;)
set "TARGET_DIRS=C:\Users\teo\Desktop\ATesi\prova RL\results\DQN_SatEnvironment_2026-03-30_09-47-39o4_xrvz1;C:\Users\teo\Desktop\ATesi\prova RL\results\DQN_SatEnvironment_2026-03-30_10-58-13c0hhc1nn;C:\Users\teo\Desktop\ATesi\prova RL\results\DQN_SatEnvironment_2026-03-30_10-58-3085up2bv7;C:\Users\teo\Desktop\ATesi\prova RL\results\DQN_SatEnvironment_2026-03-30_12-55-11u455b_hj;C:\Users\teo\Desktop\ATesi\prova RL\results\DQN_SatEnvironment_2026-03-30_12-55-061uqhbazg;C:\Users\teo\Desktop\ATesi\prova RL\results\DQN_SatEnvironment_2026-03-30_13-38-02bh7nl282;C:\Users\teo\Desktop\ATesi\prova RL\results\DQN_SatEnvironment_2026-03-30_13-48-3840vr02lm;C:\Users\teo\Desktop\ATesi\prova RL\results\DQN_SatEnvironment_2026-03-30_14-25-44sxlb0g4p;C:\Users\teo\Desktop\ATesi\prova RL\results\DQN_SatEnvironment_2026-03-30_14-39-032p7tj2uj;C:\Users\teo\Desktop\ATesi\prova RL\results\DQN_SatEnvironment_2026-03-30_16-04-42xgl0kwa0;C:\Users\teo\Desktop\ATesi\prova RL\results\DQN_SatEnvironment_2026-03-30_16-04-42zssctpm2;C:\Users\teo\Desktop\ATesi\prova RL\results\DQN_SatEnvironment_2026-03-30_16-56-39g42ixn6j;C:\Users\teo\Desktop\ATesi\prova RL\results\DQN_SatEnvironment_2026-03-30_16-56-39tjw_cjzw;C:\Users\teo\Desktop\ATesi\prova RL\results\DQN_SatEnvironment_2026-03-30_18-19-28i7gwiydl;C:\Users\teo\Desktop\ATesi\prova RL\results\DQN_SatEnvironment_2026-03-30_18-19-286i0t_lcj;C:\Users\teo\Desktop\ATesi\prova RL\results\DQN_SatEnvironment_2026-03-30_19-09-30ap2uy2i0;C:\Users\teo\Desktop\ATesi\prova RL\results\DQN_SatEnvironment_2026-03-30_19-09-314y5bjhr1"

:: Lo script assume di trovarsi nella stessa cartella dei file .py (A)json_to_csv, (B)csv_filter, (C)csv_dati
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo ===     PIPELINE GENERAZIONE REPORT MULTIPLO     ===
echo.

:: --- SCELTA MODALITÀ (Una volta sola per tutti i target) ---
set "MODE=json"
set /p "USER_INPUT=Scegli modalita [json/csv] (Premi Invio per default 'json'): "

if /i "%USER_INPUT%"=="csv" (
    set "MODE=csv"
)

echo.
echo Modalita selezionata: %MODE%
echo.

:: --- CICLO SULLE CARTELLE TARGET ---
for %%D in ("%TARGET_DIRS:;=" "%") do (
    set "CURRENT_TARGET=%%~D"
    
    echo --------------------------------------------------
    echo Elaborazione cartella: !CURRENT_TARGET!
    echo --------------------------------------------------

    if /i "%MODE%"=="json" (
        if exist "!CURRENT_TARGET!\evaluations.json" (
            :: Script A: Richiede evaluations.json -> Produce estratto_evaluations.csv
            echo Copia di evaluations.json...
            copy /y "!CURRENT_TARGET!\evaluations.json" "%SCRIPT_DIR%\" >nul
            
            echo Esecuzione Script A...
            py json_to_csv.py

            :: Rinomina l'output di A affinché lo script C lo riconosca come input
            echo Preparazione input per Script C...
            move /y "estratto_evaluations.csv" "estratto_progress.csv" >nul
        ) else (
            echo [ERRORE] evaluations.json non trovato in !CURRENT_TARGET!
        )
    ) else (
        if exist "!CURRENT_TARGET!\progress.csv" (
            :: Script B: Richiede progress.csv -> Produce estratto_progress.csv
            echo Copia di progress.csv...
            copy /y "!CURRENT_TARGET!\progress.csv" "%SCRIPT_DIR%\" >nul
            
            echo Esecuzione Script B...
            py csv_filter.py
        ) else (
            echo [ERRORE] progress.csv non trovato in !CURRENT_TARGET!
        )
    )

    :: --- SCRIPT C (Eseguito solo se i file precedenti sono stati creati) ---
    if exist "estratto_progress.csv" (
        echo Esecuzione Script C...
        py csv_dati.py

        echo Spostamento risultati finali...
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
    
    echo Completato per questa cartella.
    echo.
)

echo ===     TUTTE LE OPERAZIONI COMPLETATE     ===
pause