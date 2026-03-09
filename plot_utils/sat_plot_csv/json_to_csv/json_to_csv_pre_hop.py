import json
import pandas as pd
import os

# ----- Script per convertire il file "evaluations.json" in un csv filtrato preso da cartella in results (EVALUATION) -----

# File input ed output
input_json = 'evaluations.json' 
output_csv = 'estratto_evaluations.csv'

# Mappatura dei valori interessati: Chiave JSON -> Nome colonna CSV
mapping = {
    'current_time': 'hist_stats/current_time',
    'step_reward': 'hist_stats/step_reward',
    'hole_counter': 'hist_stats/hole_counter',
    'current_sat': 'hist_stats/current_sat',
    'total_distance': 'hist_stats/total_distance',
    'episode_reward': 'hist_stats/episode_reward',
    'episode_lengths': 'hist_stats/episode_lengths',
    'dest_reached': 'hist_stats/dest_reached',
    'dijkstra_dist': 'hist_stats/dijkstra_dist'
}

def process_json_to_csv(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"Errore: Il file '{input_path}' non esiste.")
        return

    try:
        with open(input_path, 'r') as f:
            data = json.load(f)

        rows = [] # Righe per costruire il dataframe, una riga è un'evaluation

        for eval_entry in data.get('evaluations', []):
            # Crea un dizionario per la riga corrente
            row_data = {}
            
            # Recupera fino a sampler_results e hist_stats
            sampler_results = eval_entry.get('sampler_results', {})
            hist_stats = sampler_results.get('hist_stats', {})

            # -- Valore scalare (mentre glialtri valori sono liste di elementi)
            row_data['episodes_this_iter'] = sampler_results.get('episodes_this_iter')


            # -- Valore lista di elementi (per ogni colonna desiderata, prende la lista e la converte in stringa JSON)
            for json_key, csv_column in mapping.items():
                values_list = hist_stats.get(json_key, [])
                # Converte la lista in una stringa tipo "[1, 2, 3]"
                row_data[csv_column] = json.dumps(values_list)
            
            rows.append(row_data)

        # Crea il DataFrame
        df = pd.DataFrame(rows)

        # Ordina le colonne come sono nel progress.csv filtrato
        final_columns = [
            'episodes_this_iter',
            'hist_stats/current_time',
            'hist_stats/step_reward',
            'hist_stats/hole_counter',
            'hist_stats/current_sat',
            'hist_stats/total_distance',
            'hist_stats/episode_reward',
            'hist_stats/episode_lengths',
            'hist_stats/dest_reached',
            'hist_stats/dijkstra_dist'
        ]
        
        # Salvataggio (usiamo il quoting per evitare che le virgole nelle liste rompano il CSV)
        df.to_csv(output_path, columns=final_columns, index=False)
        
        print(f"Successo! Creato '{output_path}' con {len(df)} righe (una per iterazione).")

    except Exception as e:
        print(f"Si è verificato un errore: {e}")

if __name__ == "__main__":
    process_json_to_csv(input_json, output_csv)