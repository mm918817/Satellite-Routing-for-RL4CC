import pandas as pd
import matplotlib.pyplot as plt
import os
import time

plt.rcParams.update({
    'font.size': 14, # font size base
    'axes.titlesize': 16,
    'axes.labelsize': 16,
    'xtick.labelsize': 14,
    'ytick.labelsize': 14,
    'legend.fontsize': 13,
    'figure.titlesize': 16
})


# --- CONFIGURAZIONE ---
input_folder = "summaries_csv"  # Cartella dove cerca i summary.csv
output_folder = "plots"        # Dove salva i grafici
os.makedirs(output_folder, exist_ok=True)

X_SCALE = 5 # Evaluation ogni 5 iterazioni, nel summary.csv sono salvate ogni 1
WINDOW_SIZE = 50  # Media mobile eg 10 punti (50 iterazioni reali se X_SCALE=5)
WINDOW_SIZE_OPT = 50 # Media mobile per rotta ottimale e con errori per poter calcolare: media, min e max su questo range di iterazioni
WINDOW_SIZE_OPT_FINAL = 50 # Media mobile per tabella riassuntiva rotta ottimale
WINDOW_SIZE_REWARD = 50 # Media mobile per il reward
# Parametri per la penalità (Per grafico scostamento rispetto a dijktra) 
MAX_PENALTY = 700 # Valore assegnato ad ogni flusso NON concluso (eg: 350%, usare il massimo tra i vari summary, mettere a 0 con anche WINDOW_SIZE ad 1 e vedere il valore massimo che esce)
TOT_FLOWS = 10 # Numero di flussi per ogni valutazione

# --- PARAMETRI ZOOM ---
ENABLE_ZOOM = True
ZOOM_CENTER = 5500      # Dove centrare lo zoom (asse X)
ZOOM_RANGE = 500        # Estensione prima e dopo
ZOOM_Y_LIMIT = 105      # Limite superiore asse Y per i dettagli
PADDING_PCT = 10        # Padding per grafici ptc e reward
PADDING_RWD = 0.20


# File summary.csv da includere
files_to_plot = [

    #"dest 1, step1 1",
    #"dest 1, step1 2",
    #"dest 1, step0 3",
    #"cur E1 reset eps 120k e lr 0.0002, 4000 it",
    #"cur E2 reset eps 120k e lr 0.0002, 4000 it",
    #"imit learning hard 2",
    #"E cur+imit 3900, n_step7 7k it 1",
    #"Curriculum + Imitation",

    #"Objective 1",
    #"Objective 2",
    #"Curriculum",
    #"Curriculum + imitation 1",
    #"Curriculum + imitation 2",
    #"EErf 1",
    #"EErf 2",
    #"Hard imitation",
    #"Soft imitation (EERF)",
    #"5",
    #"6",
    #"7",


    "DOrf",
    "PErf",
    "EErf",
    #"dest din, step0 2"
    #"dest 1, step dijk30 1",
    #"dest 1, step dijk30 2",
    #"dest din, step dijk30 1",
    #"dest din, step dijk30 2",
    #"dest din, step dijk30 11",
    #"dest din, step dijk30 22",
    #"dest 1, step dijk30 1",
    #"dest 1, step dijk30 2",
    #"4"
    #"A1 imit bonus 0.05",
    #"B1 imit bonus 0.05 lr 3k",
    #"B2 imit bonus 0.05 lr 3k",
    #"C1 imit bonus 0.05 lr 3k, eps 0.4",
    #"C2 imit bonus 0.05 lr 3k, eps 0.4",
    #"D1 imit bonus 0.05 lr 3k, eps 0.4, 2k reward",
    #"D2 imit bonus 0.05 lr 3k, eps 0.4, 2k reward",

    #"E1",
    #"E2",
    #"F1",
    #"F2",

    #"D 8k iterazioni",
    #"E 8k iterazioni",
    #"F 8k iterazioni",

    #"E1 - n_step 5",
    #"E2 - n_step 5"
    #"E1 - n_step 5, 2k iter, 120k eps",
    
    #"cur E2 reset eps 120k e lr 0.0002",
    #"cur E3 reset eps 120k e lr 0.0002",
    #"cur E1 reset eps 120k e lr 0.0002, 4000 it",
    #"cur E2 reset eps 120k e lr 0.0002, 4000 it"
    #"old_best",

]

# Stile linee (se non specificato usa il default di Matplotlib)
file_styles = {
    "Curriculum 1": {"color": "tab:blue", "linestyle": "-", "linewidth": 1.0},
    "Curriculum 2": {"color": "tab:orange", "linestyle": "-", "linewidth": 1.0},
    "Curriculum + imitation 1": {"color": "tab:blue", "linestyle": "-", "linewidth": 1.0},
    "Curriculum + imitation 2": {"color": "tab:orange", "linestyle": "-", "linewidth": 1.0},
    "EErf (hard) 1": {"color": "tab:blue", "linestyle": "-", "linewidth": 1.0},
    "EErf (hard) 2": {"color": "tab:blue", "linestyle": "-", "linewidth": 1.0},
    "EErf 1": {"color": "tab:orange", "linestyle": "-", "linewidth": 1.0},
    "EErf 2": {"color": "tab:orange", "linestyle": "-", "linewidth": 1.0},
    "Peak 1": {"linestyle": "-", "linewidth": 1.0},
    "Peak 2": {"linestyle": "-", "linewidth": 1.0},
    "3": {"linestyle": "-", "linewidth": 0.8},
    "1": {"linestyle": "-", "linewidth": 0.5},
    "2": {"linestyle": "-", "linewidth": 0.5},

    "DOrf": {"color": "tab:blue", "linestyle": "-", "linewidth": 1.0},
    "PErf": {"color": "tab:orange", "linestyle": "-", "linewidth": 1.0},
    "EErf": {"color": "tab:green", "linestyle": "-", "linewidth": 1.0},

    

    "A1 imit bonus 0.05": {"linestyle": "-", "linewidth": 0.5},
    "B1 imit bonus 0.05 lr 3k": {"linestyle": "-", "linewidth": 0.5},
    "B2 imit bonus 0.05 lr 3k": {"linestyle": "-", "linewidth": 0.5},
    "C1 imit bonus 0.05 lr 3k, eps 0.4": {"linestyle": "-", "linewidth": 0.5},
    "C2 imit bonus 0.05 lr 3k, eps 0.4": {"linestyle": "-", "linewidth": 0.5},
    "D1 imit bonus 0.05 lr 3k, eps 0.4, 2k reward": {"linestyle": "-", "linewidth": 0.5},
    "D2 imit bonus 0.05 lr 3k, eps 0.4, 2k reward": {"linestyle": "-", "linewidth": 0.5},

    "D 8k iterazioni": {"linestyle": "-", "linewidth": 0.5},
    "E 8k iterazioni": {"linestyle": "-", "linewidth": 0.5},
    "F 8k iterazioni": {"linestyle": "-", "linewidth": 0.5},

    "bonus 3k 0.4 2k imit 22500": {"linestyle": "-", "linewidth": 0.5},

    "E1": {"linestyle": "-", "linewidth": 0.5},
    "E2": {"linestyle": "-", "linewidth": 0.5},
    "F1": {"linestyle": "-", "linewidth": 0.5},
    "F2": {"linestyle": "-", "linewidth": 0.5},
    
    "bonus 3k 0.4 2k imit 22500": {"linestyle": "-", "linewidth": 0.5},


    #"A1 - dest 1, step dijk30": {"color": "tab:orange", "linestyle": "--","alpha": 0.5, "linewidth": 1},
    #"A2 - dest 1, step dijk30": {"color": "tab:orange", "linestyle": "-", "linewidth": 1},
    "B2 - dest din, step dijk30": {"color": "tab:grey", "linestyle": ":","alpha": 0.5, "linewidth": 1},
    "A1 - n_step 1": {"color": "tab:grey", "linestyle": ":","alpha": 0.5, "linewidth": 1},
    "A3 - n_step 1": {"color": "tab:grey", "linestyle": ":","alpha": 0.5, "linewidth": 1},
    "A2 - n_step 1": {"color": "tab:blue", "linestyle": "-", "linewidth": 1},


    #"cur E1 reset eps 120k e lr 0.0002, 4000 it": {"color": "tab:red", "linestyle": ":","alpha": 0.5, "linewidth": 1},
    #"cur E2 reset eps 120k e lr 0.0002, 4000 it": {"color": "tab:purple", "linestyle": "-", "linewidth": 1},
    #"A2 - dest 1, step dijk30": {"color": "tab:blue", "linestyle": "-", "linewidth": 1},
    #"B3 - dest din, step dijk30": {"color": "tab:orange", "linestyle": "-", "linewidth": 1},
    #"A3 - dest 1, step dijk30": {"color": "tab:grey", "linestyle": ":","alpha": 0.5, "linewidth": 1},
    



    #"E1": {"color": "tab:blue", "linestyle": "-", "alpha": 0.3, "linewidth": 1},
    #"E2": {"color": "tab:orange", "linestyle": "-", "linewidth": 1},
    #"E3": {"color": "tab:green", "linestyle": "-", "linewidth": 1},

    #"dest din, step 0, h5, lr 0.001, gamma 0.99, nn128, 2000 iter": {"linestyle": "--", "linewidth": 1.5},
}

# Metriche ed i titoli (grafici che stampa)
metrics = [
    ("pct_concluded", "Completed Flows Percentage (%)", "concluded_plot.png"),
    ("pct_optimal", "Optimal Routes Percentage (%)", "err0_optimal_plot.png"),
    ("pct_err10", "Optimal Routes Percentage, within 10% error (%)", "err10_plot.png"),
    ("pct_err20", "Optimal Routes Percentage, within 20% error (%)", "err20_plot.png"),
    ("pct_err30", "Optimal Routes Percentage, within 30% error (%)", "err30_plot.png"),
    ("pct_err40", "Optimal Routes Percentage, within 40% error (%)", "err40_plot.png"),
    ("pct_err50", "Optimal Routes Percentage, within 50% error (%)", "err50_plot.png"),
    ("mean_diff_iter", "Average Deviation from Dijkstra (%)", "deviation_plot.png"),
    ("mean_reward_iter", "Average Reward per Iteration (min, max)", "reward_plot.png")
]

# --- 1 GENERAZIONE PLOT % METRICHE PER ITERAZIONI---
if not files_to_plot:
    print("No file specified.")
else:
    for column, ylabel, filename in metrics:
        plt.figure(figsize=(12, 6))

        # Lista elementi da non mettere nello zoom (per deviaz. standard, min e max)
        elements_to_hide = [] # Lista elementi da non mettere nello zoom (per deviaz. standard, min e max)

        for file_name in files_to_plot:
            file_path = os.path.join(input_folder, f"{file_name}.csv")
            
            if os.path.exists(file_path):
                df = pd.read_csv(file_path).copy() # Fa una copia non modifica gli originali
                
                # Lista con nomi delle colonne dello scostamento dei singoli episodi da dijkstra e sostistuisce i "-" con la penalità per poter fare calcoli
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
                
                custom_args = file_styles.get(file_name, {}) # Per stile custom, se il file non è nel dizionario usa un dizionario vuoto {} (quindi usa default)
                
                # Lista metriche rotta ottimale e con errori
                pct_error_metrics = ["pct_optimal", "pct_err10", "pct_err20", "pct_err30", "pct_err40", "pct_err50"]
                
                # --- CASE 1: Rotte ottimali e con errore (Media, Min/Max rispetto a finestra specificata)
                if column in pct_error_metrics:
                    # min_periods=1 serve per i primi valori che non hanno 10 valori precedenti, quindi fa media con solo quelli che ha
                    y_smooth = df[column].rolling(window=WINDOW_SIZE_OPT, min_periods=1).mean()
                    y_min_window = df[column].rolling(window=WINDOW_SIZE_OPT, min_periods=1).min()
                    y_max_window = df[column].rolling(window=WINDOW_SIZE_OPT, min_periods=1).max()
                    
                    # ** davanti ad un dizionario permette di spacchettare le coppie chiave e valore
                    # Trasformandole in argomenti per la funzione (usato per gli stili)
                    line, = plt.plot(x_values, y_smooth, label=file_name, **custom_args)
                    fill = plt.fill_between(x_values, y_min_window, y_max_window, color=line.get_color(), alpha=0.1)
                    elements_to_hide.append(fill)

                    plt.title(f"Comparison ({WINDOW_SIZE_OPT}-points Moving Average): {ylabel}")

                # --- CASE 2: Scostamento da Dijkstra (Media, Min/Max e Std Dev rispetto a un'iterazione, cioè riga del csv)
                # Poi viene comunque fatta una meida rispetto alla finestra specificata per rendere più leggibile
                elif column == "mean_diff_iter":
                    y_smooth = df[column].rolling(window=WINDOW_SIZE, min_periods=1).mean()
                    line, = plt.plot(x_values, y_smooth, label=file_name, **custom_args)
                    
                    if ep_cols: # if Per gestire csv vecchi dove non ci sono le colonne ep_cols
                        row_std = df[ep_cols].std(axis=1) # Serie dove ogni elemento è Std dev tra gli ep della riga nel csv
                        row_min = df[ep_cols].min(axis=1) # Serie dove ogni elemento è il valore min tra gli ep della riga nel csv
                        row_max = df[ep_cols].max(axis=1) # Serie dove ogni elemento è ilvalore max tra gli ep della riga nel csv

                        # Smoothing per migliorare visibilità
                        std_smooth = row_std.rolling(window=WINDOW_SIZE, min_periods=1).mean()
                        y_min_smooth = row_min.rolling(window=WINDOW_SIZE, min_periods=1).mean()
                        y_max_smooth = row_max.rolling(window=WINDOW_SIZE, min_periods=1).mean()
                        
                        # Per area deviazione standard
                        fill1 = plt.fill_between(x_values, 
                                        (y_smooth - std_smooth).clip(lower=0), # (media - std_dev) per avere estremo inferiore
                                        (y_smooth + std_smooth).clip(upper=y_max_smooth), # (media + std_dev) per avere estremo superiore
                                        color=line.get_color(), alpha=0.25) # Etichetta  label=f"Std Dev {file_name}"
                        
                        # Per estremi Min/Max, la "," è usata per estrarre la linea dalla lista restituita da plt.plot
                        line_max, = plt.plot(x_values, y_max_smooth, color=line.get_color(), 
                                linestyle='--', linewidth=0.8, alpha=0.5)
                        line_min, = plt.plot(x_values, y_min_smooth, color=line.get_color(), 
                                linestyle='--', linewidth=0.8, alpha=0.5)
                        
                        # Per area tra i minimi e i massimi
                        fill2 = plt.fill_between(x_values, y_min_smooth.clip(lower=0), y_max_smooth, 
                                        color=line.get_color(), alpha=0.05)
                        elements_to_hide.extend([fill1, line_max, line_min, fill2])
                        plt.title(f"Comparison ({WINDOW_SIZE}-points Moving Average): {ylabel}")

                # --- CASE 4: Reward dell'iterazione (Media con ombra Min/Max, di cui si applica una finestra specificata ) ---
                elif column == "mean_reward_iter":
                    y_smooth = df[column].rolling(window=WINDOW_SIZE_REWARD, min_periods=1).mean()
                    y_min_smooth = df["min_reward_iter"].rolling(window=WINDOW_SIZE_REWARD, min_periods=1).mean()
                    y_max_smooth = df["max_reward_iter"].rolling(window=WINDOW_SIZE_REWARD, min_periods=1).mean()
                    
                    line, = plt.plot(x_values, y_smooth, label=file_name, **custom_args)
                    
                    # Area tra il minimo e il massimo dei reward registrati in quell'iterazione
                    fill = plt.fill_between(x_values, y_min_smooth, y_max_smooth, 
                                     color=line.get_color(), alpha=0.15)
                    elements_to_hide.append(fill)

                    plt.title(f"Reward Trend ({WINDOW_SIZE_REWARD}-points Moving Average): {ylabel}")
                # --- CASE 3: Flussi conclusi (Media rispetto alla finestra specificata)
                else:
                    y_smooth = df[column].rolling(window=WINDOW_SIZE, min_periods=1).mean()
                    plt.plot(x_values, y_smooth, label=file_name, **custom_args)
                    plt.title(f"Comparison ({WINDOW_SIZE}-points Moving Average): {ylabel}")

        
        if column == "mean_diff_iter":
            #plt.axhline(y=25, color='gold', linestyle='--', linewidth=0.5, label='Thresholds 25, 50%')
            #plt.axhline(y=50, color='gold', linestyle='--', linewidth=0.5)
            #plt.axhline(y=10, color='black', linestyle='--', linewidth=0.5, label='Threshold 10%')
            #plt.axhline(y=5, color='purple', linestyle='--', linewidth=0.5, label='Threshold 5%')

            plt.axhline(y=50, color='red', linestyle='--', linewidth=0.8, label='50%')
            plt.axhline(y=25, color='orange', linestyle='--', linewidth=0.8, label='25%')
            plt.axhline(y=12.65, color='dodgerblue', linestyle='--', linewidth=0.8, label='Heuristic alg, 12.65%')
            #plt.axhline(y=10, color='dodgerblue', linestyle='--', linewidth=0.8, label='10%')
            #plt.axhline(y=3.5, color='blue', linestyle='--', linewidth=0.8, label='value %')
            plt.axhline(y=5,  color='limegreen', linestyle='--', linewidth=0.8, label='5%')


        plt.xlabel("Iterations")
        plt.ylabel(ylabel)
        plt.grid(True, linestyle='--', alpha=0.6)

        # Scala asse Y fissa a 100 per le percentuali
        if column.startswith("pct"):
            plt.ylim(0, 105)

        plt.legend(loc='best') # Mostra quale linea appartiene a quale file
        
        # Salva il grafico "Full View"
        plt.savefig(os.path.join(output_folder, filename), dpi=300)
        print(f"Generated graph: {filename}")

        # Generazione ZOOM
        if ENABLE_ZOOM:

            # Imposta elementi deviaz. standard, min e max invisibili per lo zoom
            for el in elements_to_hide:
                el.set_visible(False)

            plt.xlim(ZOOM_CENTER - ZOOM_RANGE, ZOOM_CENTER + ZOOM_RANGE)
            
            # Imposta il limite Y
            if column == "mean_diff_iter":
                plt.ylim(0, ZOOM_Y_LIMIT)
            else:
                # Per fare focus automatico su asse y
                ax = plt.gca() # Recupera assi grafico 
                visible_y = []

                # Estrae tutti i valori della x ed y delle righe tracciate nel grafico
                for line in ax.get_lines():
                    xdata = line.get_xdata()
                    ydata = line.get_ydata()
                    
                    # Crea una maschera per selezionare i dati dentro lo zoom
                    mask = (xdata >= ZOOM_CENTER - ZOOM_RANGE) & (xdata <= ZOOM_CENTER + ZOOM_RANGE)
                    
                    if len(ydata) > 2: # Esclude le linee di soglia (hanno solo 2 punti)
                        visible_y.extend(ydata[mask])

                # Se ci sono dati validi nello zoom stringe l'asse Y intorno
                if visible_y:
                    y_min, y_max = min(visible_y), max(visible_y)
                    
                    if column.startswith("pct"):
                        #padding = (y_max - y_min) * 0.05 if y_max != y_min else 2 # padding 5% sopra e sotto
                        plt.ylim(max(0, y_min - PADDING_PCT), min(105, y_max + PADDING_PCT))
                    
                    elif column == "mean_reward_iter":
                        plt.ylim(max(0, y_min - PADDING_RWD), min(105, y_max + PADDING_RWD))

            plt.title(f"ZOOM {ZOOM_CENTER} (Range ±{ZOOM_RANGE}): {ylabel}")
            zoom_filename = f"zoom_{ZOOM_CENTER}_{filename}"
            plt.savefig(os.path.join(output_folder, zoom_filename), dpi=300)
            print(f"Generated zoom graph: {zoom_filename}")
            
        plt.close()    

    # --- 2 GENERAZIONE GRAFICO MAX PERFORMANCE PER ERRORE ---
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

    plt.title("Maximum Accuracy achieved for Error Threshold")
    plt.xlabel("Tolerated Error Threshold (%)")
    plt.ylabel("Maximum Percentage Reached (%)")
    plt.ylim(0, 105)
    plt.xticks(error_thresholds) # Forza i valori 0, 10, 20... sull'asse x
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(loc='best')   
    
    summary_filename = "max_performance_error_summary.png"
    plt.savefig(os.path.join(output_folder, summary_filename), dpi=300)
    plt.close()
    print(f"Error summary graph, generated: {summary_filename}")

# --- 3 GENERAZIONE TABELLA VALORE FINALE PER ROTTE OTTIMALI CONSIDERANDO ERRORE ---
print("\nGenerate final value summary table for optimal routes...")

final_results = []
error_columns = ["pct_optimal", "pct_err10", "pct_err20", "pct_err30", "pct_err40", "pct_err50"]

for file_name in files_to_plot:
    file_path = os.path.join(input_folder, f"{file_name}.csv")
    
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        
        # Dizionario per contenere i dati della riga corrente, dove la prima colonna è il nome della configurazione
        row_data = {"Configuration": file_name}
        
        for col in error_columns:
            if col in df.columns:
                # Calcola la media mobile come fatto nei grafici (Case 1)
                y_smooth = df[col].rolling(window=WINDOW_SIZE_OPT_FINAL, min_periods=1).mean()
                final_val = y_smooth.iloc[-1] # Prende l'ultimo valore "smussato" in base alla window size impostata
                
                # Valore massimo smussato, se si vuole solo IL massimo fare best_val = df[col].max()
                #y_smooth = df[col].rolling(window=WINDOW_SIZE_OPT, min_periods=1).mean()
                #best_val = y_smooth.max()
                #row_data[col] = f"{best_val:.2f}%"


                row_data[col] = f"{final_val:.2f}%" # Lo salva associato alla colonna (chiave) corrispondente
            else:
                row_data[col] = "N/A"
        
        final_results.append(row_data)

# Creazione DataFrame finale
df_final_table = pd.DataFrame(final_results)

# Rinomina le colonne per renderle più leggibili nella tabella
rename_dict = {
    "pct_optimal": "Optimal (0%)",
    "pct_err10": "Error ≤10%",
    "pct_err20": "Error ≤20%",
    "pct_err30": "Error ≤30%",
    "pct_err40": "Error ≤40%",
    "pct_err50": "Error ≤50%"
}
df_final_table = df_final_table.rename(columns=rename_dict)

# Salvataggio come file CSV
table_filename = os.path.join(output_folder, "final_performance_table.csv")
df_final_table.to_csv(table_filename, index=False)

# Stampa a terminale la tabella per debug
print("\n--- LAST ITERATION PERFORMANCE (Moving Average) ---")
print(df_final_table.to_string(index=False))
print(f"\nTable saved at: {table_filename}")

print("\nProcess Completed!")
time.sleep(5)