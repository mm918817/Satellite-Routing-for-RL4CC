import pandas as pd
import numpy as np
import ast
import os

# ----- Script che prende il file csv filtrato e costruire una tabella con varie metriche per ogni episodio -----

# REPORT - Episodi per ogni iterazione (MAX STEP CAP: N)
# ------------------------------------------------------------------------------------------------------------------------------------------------------
# ITER   | EP  | HOLES | DISTANCE   | DIJK_DIST  | DIFF_%   | DEST_OK | STP/30  | DIJK_HOP | LAST_R     | RETURN     | MIN_R    | MAX_R    | MEAN_R   | STD_R   
# ------------------------------------------------------------------------------------------------------------------------------------------------------
# ITER N:  Concluded flows:  % | Optimal route:  % | Avg Deviat from Dijk:  % | EP count: N

base_path = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_path, 'estratto_progress.csv')
output_file = os.path.join(base_path, 'report_episodi_per_iterazione.txt')
summary_csv = os.path.join(base_path, 'summary_iterations.csv')

MAX_STEPS_CAP = 30
MAX_ERR = 0.00001

df = pd.read_csv(file_path)


def parse_list(x):
    if isinstance(x, str):
        try: return ast.literal_eval(x) # Converte stringhe "[1,2,3]" in liste python [1,2,3]
        except: return []
    return x

cols_to_parse = [
    'hist_stats/step_reward', 
    'hist_stats/episode_lengths', 
    'hist_stats/hole_counter', 
    'hist_stats/total_distance',
    'hist_stats/dijkstra_dist',
    'hist_stats/dijkstra_hop',
    'hist_stats/dest_reached',

]

for col in cols_to_parse:
    df[col] = df[col].apply(parse_list)

# ---  HEADER TXT ---
n_step_header = f"STP/{MAX_STEPS_CAP}"
header = (
    f"{'ITER':<6} | {'EP':<3} | {'HOLES':<5} | "
    f"{'DISTANCE':<10} | {'DIJK_DIST':<10} | {'DIFF_%':<8} | {'DEST_OK':<7} | "
    f"{n_step_header:<7} | {'DIJK_HOP':<8} | {'LAST_R':<10} | {'RETURN':<10} | {'MIN_R':<8} | "
    f"{'MAX_R':<8} | {'MEAN_R':<8} | {'STD_R':<8}\n"
)

table_width = len(header.rstrip("\n"))
separator = "-" * table_width + "\n"
iter_separator = "=" * table_width + "\n"

summary_data = [] # Lista dati che andranno nel summary (csv)

# - Scrittura del file -
with open(output_file, 'w') as f:
    f.write(f"REPORT - Episodi per ogni iterazione (MAX STEP CAP: {MAX_STEPS_CAP})\n")
    f.write("ATTENZIONE! I valori di \"Avg Deviat from Dijk\" in questo txt e della colonna \"mean_diff_iter\" nel summary.csv\n")
    f.write("Sono rispetto ai flussi conclusi, vengono aggiustati nei plot delle percentuali con una penalizzazione specificata\n")
    f.write(separator)
    f.write(header)
    f.write(separator)
    
    for idx, row in df.iterrows(): # Itera sulle righe del csv, ogni riga è un'iterazione (un'insieme di episodi)
        iterazione = idx + 1
        
        # Valori come rewards (o anche distances) sono salvati uno dopo l'altro(per step), nella stessa lista, per episodi diversi
        # Quindi per ogni episodio si usano come delle "window" per recuperare tutti gli  elementi che lo compongono
        lengths = row['hist_stats/episode_lengths'] # Lista con lunghezza di ogni episodio
        rewards = row['hist_stats/step_reward']
        holes = row['hist_stats/hole_counter']
        distances = row['hist_stats/total_distance']
        dijkstra = row['hist_stats/dijkstra_dist']
        dijkstra_hop = row['hist_stats/dijkstra_hop']
        dest_reached = row['hist_stats/dest_reached']

        ep_count = len(lengths) # Numero di episodi per l'iterazione
        concluded = 0  # Contatore dei flussi conclusi
        optimal = 0 # Contatore se i flussi sono ottimali, cioè uguali a dijkstra 
        err10 = err20 = err30 = err40 = err50 = 0 # Contatori se i flussi sono ottimali, cioè uguali a dijkstra entro una % di errore

        iteration_diffs = [] # Lista per salvare gli scostamenti(%) degli episodi andati a buon fine
        episodes_diffs = {} # Dict per scostamenti sulle colonne singole del csv

        # -- Calcola statistiche aggregate per % di: flussi conclusi, ottimali, scostamento di dijkstra --
        current_idx_tmp = 0 # Puntatore ad un range(window) di elementi per un episodio
        for ep_i, length in enumerate(lengths):
            first_idx = current_idx_tmp
            last_idx = current_idx_tmp + length - 1

            diff_to_save = "-" # Valore di default "-" per flusso NON concluso (quindi non ho scostamento da dijkstra)

            try:
                d_ok = dest_reached[last_idx] # L'elemento all'ultima posizione di di dest_reached mi dice se sono arrivato a destinazione(1) o no(0)

                # Se l'agente è arrivato a destinazione calcolo lo scostamento rispetto a dijkstra
                if d_ok:
                    concluded += 1
                    dist_val = distances[last_idx] # Recupera la distanza all'ultimo step dell'episodio (quella maggiore per l'ep)
                    dijk_val = dijkstra[first_idx] # Recupera dijkstra al primo step dell'episodio (comunque è uguale per ogni step in un ep)
                    
                    # Calcolo scostamento: ((Dist / Dijk) - 1) * 100
                    if dijk_val > 0:
                        diff_pct = round(max(0.0,((dist_val / dijk_val) - 1) * 100), 2) # max per evitare -0.00% (per errori calcoli all'ultimo valore, per via dell'ultimo valore episodio)
                        iteration_diffs.append(diff_pct)
                        diff_to_save = diff_pct # Valore numerico dell'episodio per il CSV
                        
                        if diff_pct < 11.0: err10 += 1
                        if diff_pct < 21.0: err20 += 1
                        if diff_pct < 31.0: err30 += 1
                        if diff_pct < 41.0: err40 += 1
                        if diff_pct < 51.0: err50 += 1
                 
                    if (abs(dist_val - dijk_val) < MAX_ERR):
                        optimal += 1            
            except IndexError:
                pass
            # Scostamento del singolo episodio (numero o "-")
            episodes_diffs[f"ep{ep_i+1}_diff"] = diff_to_save 
            current_idx_tmp += length

        # Metriche aggregate
        pct_concluded = (concluded / ep_count * 100) if ep_count > 0 else 0 
        pct_optimal = (optimal / ep_count * 100) if ep_count > 0 else 0 

        pct_err10 = (err10 / ep_count * 100) if ep_count > 0 else 0
        pct_err20 = (err20 / ep_count * 100) if ep_count > 0 else 0
        pct_err30 = (err30 / ep_count * 100) if ep_count > 0 else 0
        pct_err40 = (err40 / ep_count * 100) if ep_count > 0 else 0
        pct_err50 = (err50 / ep_count * 100) if ep_count > 0 else 0 
        
        mean_diff_iter = round(np.mean(iteration_diffs), 2) if iteration_diffs else 0.0 # % Media dello scostamento per l'intera iterazione (rispetto ai flussi conclusi)

        # Salvataggio dati riga titoletto iterazione per summary.csv
        row_summary = {
            "iteration": iterazione,
            "pct_concluded": pct_concluded,
            "pct_optimal": pct_optimal,
            "pct_err10": pct_err10,
            "pct_err20": pct_err20,
            "pct_err30": pct_err30,    
            "pct_err40": pct_err40,            
            "pct_err50": pct_err50,            
            "mean_diff_iter": mean_diff_iter
        }
        
        row_summary.update(episodes_diffs) # Unione delle colonne degli ep individuali
        summary_data.append(row_summary)

        if iterazione > 1:
            f.write(iter_separator)

        # --- TITOLETTO STAT AGGREGATE ITERAZIONE nel TXT ---
        title_line = (
            f"ITER {iterazione}:  "
            f"Concluded flows: {pct_concluded:6.2f}% | "
            f"Optimal route: {pct_optimal:6.2f}% | "
            f"Ptc Err: {pct_err10:6.2f}%,{pct_err20:6.2f}%,{pct_err30:6.2f}%,{pct_err40:6.2f}%,{pct_err50:6.2f}% | "
            f"Avg Deviat from Dijk: {mean_diff_iter:6.2f}% | "
            f"EP count: {ep_count}\n"
        )

        f.write(title_line)
        f.write(separator)
        
        # -- Seconda passata per statistiche individuali per episodio --
        current_idx = 0
        for ep_num, length in enumerate(lengths):
            ep_rewards = rewards[current_idx : current_idx + length]
            ep_return = np.sum(ep_rewards) if ep_rewards else 0.0
            first_val_idx = current_idx
            last_val_idx = current_idx + length - 1
            
            try:
                ep_hole = holes[last_val_idx]
                ep_dist = distances[last_val_idx]
                ep_dijkstra = dijkstra[first_val_idx] 
                ep_dijkstra_hop = dijkstra_hop[first_val_idx]      
                ep_dest = int(dest_reached[last_val_idx]) # Convertito in int per la tabella
                last_step_reward = rewards[last_val_idx]
                
                # Calcolo percentuale per la riga
                if ep_dest == 1 and ep_dijkstra > 0:
                    ep_diff_pct = max(0.0, ((ep_dist / ep_dijkstra) - 1) * 100) # max per evitare -0.00% per via dell'ultimo valore episodio
                    ep_diff_str = f"{ep_diff_pct:>7.2f}%"
                else:
                    ep_diff_str = f"{'-':^8}" # Se non raggiunto o errore, mette un trattino
                    
            except IndexError:
                ep_hole = ep_dist = ep_dijkstra = ep_dijkstra_hop = ep_dest = last_step_reward = np.nan
                ep_diff_str = f"{'-':^8}"

            if ep_rewards:
                min_r, max_r = np.min(ep_rewards), np.max(ep_rewards)
                mean_r, std_r = np.mean(ep_rewards), np.std(ep_rewards)
            else:
                min_r, max_r, mean_r, std_r, last_step_reward = 0, 0, 0, 0, 0

            # --- SCRITTURA RIGA ---
            line = (
                f"{iterazione:<6} | {ep_num + 1:<3} | "
                f"{ep_hole:<5} | {ep_dist:<10.2f} | {ep_dijkstra:<10.2f} | {ep_diff_str} | "
                f"{ep_dest:<7} | {length:<7} | {ep_dijkstra_hop:<8} | "
                f"{last_step_reward:<10.4f} | {ep_return:<10.4f} | {min_r:<8.4f} | {max_r:<8.4f} | "
                f"{mean_r:<8.4f} | {std_r:<8.4f}\n"
            )
            f.write(line)
            current_idx += length

# --- SALVATAGGIO summary.csv ---
summary_df = pd.DataFrame(summary_data)

# Riordina le colonne per avere scostamento degli ep in ordine (prima aggregate, poi episodi ordinati)
cols = [c for c in summary_df.columns if not c.startswith('ep')] + \
       sorted([c for c in summary_df.columns if c.startswith('ep')], key=lambda x: int(x.split('_')[0][2:]))

summary_df = summary_df[cols]

# Riempie i valori mancanti (se alcune iterazioni hanno meno episodi) con "-"
summary_df = summary_df.fillna("-")

summary_df.to_csv(summary_csv, index=False)

print(f"Processo completato.")
print(f"Report TXT: {output_file}")
print(f"Summary CSV: {summary_csv}")
