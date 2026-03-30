import pandas as pd
import matplotlib.pyplot as plt
import os
import time

# --- CONFIGURAZIONE ---
input_folder = "summaries_csv"  # cartella summary.csv
output_folder = "plots"        # Dove salva i grafici
os.makedirs(output_folder, exist_ok=True)

X_SCALE = 5 # Evaluation ogni 5 iterazioni, nel summary.csv sono salvate ogni 1
WINDOW_SIZE = 1  # Media mobile su 10 punti (50 iterazioni reali se X_SCALE=5)

# Parametri per la penalità (Per scostamento rispetto a dijktra) 
MAX_PENALTY = 0 # Valore assegnato ad ogni flusso NON concluso (eg: 350%, usare il massimo tra i vari summary, o provare prima con 0 e vedere il valore massimo che esce)
TOT_FLOWS = 10 # Numero di flussi per ogni valutazione

# File summary.csv da includere
files_to_plot = [

    "summary_iterations"

]

# Stile linee (se non specificato usa il default di Matplotlib)
file_styles = {

    #"dest 1, step 0, h5, lr 0.001, gamma 0.99, nn128, 2000 iter": {"color": "black", "linestyle": "-", "linewidth": 2.5},
    #"dest din, step 0, h5, lr 0.001, gamma 0.99, nn128, 2000 iter": {"linestyle": "--", "linewidth": 1.5},
}

# Metriche ed i titoli (grafici che stampa)
metrics = [
    ("pct_concluded", "Percentuale Flussi Conclusi (%)", "concluded_plot.png"),
    ("pct_optimal", "Percentuale Rotte Ottimali (%)", "err0_optimal_plot.png"),
    ("pct_err10", "Percentuale Rotte Ottimali, entro errore 10% (%)", "err10_plot.png"),
    ("pct_err20", "Percentuale Rotte Ottimali, entro errore 20% (%)", "err20_plot.png"),
    ("pct_err30", "Percentuale Rotte Ottimali, entro errore 30% (%)", "err30_plot.png"),
    ("pct_err40", "Percentuale Rotte Ottimali, entro errore 40% (%)", "err40_plot.png"),
    ("pct_err50", "Percentuale Rotte Ottimali, entro errore 50% (%)", "err50_plot.png"),
    ("mean_diff_iter", "Scostamento Medio da Dijkstra (%)", "deviation_plot.png")
]

# --- 1. GENERAZIONE PLOT % METRICHE PER ITERAZIONI---
if not files_to_plot:
    print("Nessun file specificato.")
else:
    for column, ylabel, filename in metrics:
        plt.figure(figsize=(12, 6))
        
        for file_name in files_to_plot:
            file_path = os.path.join(input_folder, f"{file_name}.csv")
            
            if os.path.exists(file_path):
                df = pd.read_csv(file_path).copy() # Fa una copia non modifica gli originali
                
                # sostistuisce i "-" con la penalità per poter fare calcoli
                ep_cols = [c for c in df.columns if c.startswith('ep')]
                if ep_cols:
                    for col in ep_cols:
                        df[col] = pd.to_numeric(df[col].replace("-", MAX_PENALTY))

                # -- Per penalizzare metrica mean_diff_iter --
                n_concluded = df['pct_concluded'] / (TOT_FLOWS) # (eg: 40% -> 4)
                n_failed = TOT_FLOWS - n_concluded

                # Segue la logica: ((n_concluded * media_attuale) + (n_failed * penalità)) / 10
                df['mean_diff_iter'] = (
                    (n_concluded * df['mean_diff_iter']) + 
                    (n_failed * MAX_PENALTY)
                ) / TOT_FLOWS
                # --------------------------------------------

                x_values = df['iteration'] * X_SCALE
                # min_periods=1 serve per i primi valori che non hanno 10 valori precedenti, quindi fa media con solo quelli che ha
                y_smooth = df[column].rolling(window=WINDOW_SIZE, min_periods=1).mean() 
                
                custom_args = file_styles.get(file_name, {}) # Per stile custom, se il file non è nel dizionario usa un dizionario vuoto {} (quindi usa default)

                # ** davanti ad un dizionario permette di spacchettare le coppie chiave e valore
                # Trasformandole in argomenti per la funzione (usato per gli stili)
                line, = plt.plot(x_values, y_smooth, label=file_name, **custom_args)
                if column == "mean_diff_iter" and ep_cols:
                    # Solo per grafico scostamento calcola min e max tra gli episodi per ogni riga
                    row_min = df[ep_cols].min(axis=1)
                    row_max = df[ep_cols].max(axis=1)
                    
                    # Applica la media mobile per coerenza visiva
                    y_min_smooth = row_min.rolling(window=WINDOW_SIZE, min_periods=1).mean()
                    y_max_smooth = row_max.rolling(window=WINDOW_SIZE, min_periods=1).mean()
                    
                    # Area ombreggiata con stesso colore della linea ma trasparente
                    plt.fill_between(x_values, y_min_smooth, y_max_smooth, color=line.get_color(), alpha=0.15)
            else:
                print(f"File non trovato: {file_path}")

        # Formattazione grafica
        plt.title(f"Confronto (Media Mobile {WINDOW_SIZE} punti): {ylabel}")
        plt.xlabel("Iterazioni")
        plt.ylabel(ylabel)
        plt.grid(True, linestyle='--', alpha=0.6)

        # Scala asse Y fissa a 100 per le percentuali
        if column.startswith("pct"):
            plt.ylim(0, 105)

        plt.legend(loc='best') # Mostra quale linea appartiene a quale file
        
        # Salva il grafico
        plt.savefig(os.path.join(output_folder, filename), dpi=300)
        plt.close()
        print(f"Grafico generato: {filename}")

    # --- 2. GENERAZIONE GRAFICO MAX PERFORMANCE PER ERRORE ---
    plt.figure(figsize=(10, 6))
    
    error_thresholds = [0, 10, 20, 30, 40, 50]
    error_columns = ["pct_optimal", "pct_err10", "pct_err20", "pct_err30", "pct_err40", "pct_err50"]

    for file_name in files_to_plot:
        file_path = os.path.join(input_folder, f"{file_name}.csv")
        
        if os.path.exists(file_path):
            df = pd.read_csv(file_path).copy()
          
            max_values = [df[col].max() for col in error_columns]
            
            custom_args = file_styles.get(file_name, {})
            plt.plot(error_thresholds, max_values, marker='o', label=file_name, **custom_args) 

    plt.title("Massima Accuratezza raggiunta per Soglia di Errore")
    plt.xlabel("Soglia di Errore Tollerata (%)")
    plt.ylabel("Massima Percentuale Raggiunta (%)")
    plt.ylim(0, 105)
    plt.xticks(error_thresholds) # Forza i valori 0, 10, 20... sull'asse x
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(loc='best')   
    
    summary_filename = "max_performance_error_summary.png"
    plt.savefig(os.path.join(output_folder, summary_filename), dpi=300)
    plt.close()
    print(f"Grafico riassuntivo errore, generato: {summary_filename}")

print("Processo completato con successo!")
time.sleep(5)