import pandas as pd

# ----- Script per filtrare il file "progress.csv" preso da cartella in results (TRAINING) -----

# File input ed output
input_file = 'progress.csv'
output_file = 'estratto_progress.csv'

# Lista delle colonne da estrarre
columns_to_extract = [
    'episodes_this_iter',
    'hist_stats/current_time', 
    'hist_stats/step_reward', 
    'hist_stats/hole_counter', 
    'hist_stats/current_sat', 
    'hist_stats/total_distance', 
    'hist_stats/episode_reward', 
    'hist_stats/episode_lengths',
    'hist_stats/dest_reached',
    'hist_stats/dijkstra_dist',
    'hist_stats/dijkstra_hop'
]

try:
    # Legge il CSV
    df = pd.read_csv(input_file)
    
    # Verifica quali colonne sono effettivamente presenti
    existing_columns = [col for col in columns_to_extract if col in df.columns]
    
    if len(existing_columns) < len(columns_to_extract):
        missing = set(columns_to_extract) - set(existing_columns)
        print(f"Attention, some columns were not found: {missing}")

    # Crea il nuovo dataframe e salva
    df_extracted = df[existing_columns]
    df_extracted.to_csv(output_file, index=False)
    
    print(f"The file'{output_file}' was created with {len(existing_columns)} columns.")

except FileNotFoundError:
    print(f"Error: file '{input_file}' not found.")
except Exception as e:
    print(f"An error occurred during the conversion: {e}")