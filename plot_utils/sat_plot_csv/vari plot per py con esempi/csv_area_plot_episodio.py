import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ast
import os

# Caricamento dati
base_path = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_path, 'estratto_progress.csv')

df = pd.read_csv(file_path)

def parse_list(x):
    if isinstance(x, str):
        try:
            return ast.literal_eval(x)
        except:
            return []
    return x

cols_to_fix = ['hist_stats/step_reward', 'hist_stats/hole_counter', 'hist_stats/episode_lengths']
for col in cols_to_fix:
    df[col] = df[col].apply(parse_list)

all_episodes_data = []
iteration_boundaries = [] # Per tracciare dove finisce un'iterazione
total_holes_count = 0
current_global_episode = 0

for i, row in df.iterrows():
    lengths = row['hist_stats/episode_lengths']
    rewards = row['hist_stats/step_reward']
    holes = row['hist_stats/hole_counter']
    
    current_idx = 0
    for length in lengths:
        ep_rewards = rewards[current_idx : current_idx + length]
        ep_holes = holes[current_idx : current_idx + length]
        
        all_episodes_data.append({
            'mean': np.mean(ep_rewards),
            'std': np.std(ep_rewards),
            'min': np.min(ep_rewards),
            'max': np.max(ep_rewards)
        })
        total_holes_count += np.sum(ep_holes)
        current_idx += length
        current_global_episode += 1
    
    # Segna fine dell'iterazione (tranne l'ultima)
    iteration_boundaries.append(current_global_episode)

ep_df = pd.DataFrame(all_episodes_data)

# --- GRAFICO ---
plt.figure(figsize=(14, 7))
x = range(len(ep_df))

# 1. Area Min-Max (chiara)
plt.fill_between(x, ep_df['min'], ep_df['max'], color='gray', alpha=0.15, label='Range Min-Max')

# 2. Area Deviazione Standard
plt.fill_between(x, ep_df['mean'] - ep_df['std'], ep_df['mean'] + ep_df['std'], color='blue', alpha=0.3, label='Std Dev')

# 3. Linea della Media
plt.plot(x, ep_df['mean'], color='blue', linewidth=2, label='Reward Media Episodio')

# 4. Linee Verticali per le Iterazioni
for boundary in iteration_boundaries[:-1]: # Esclude l'ultima
    plt.axvline(x=boundary, color='red', linestyle='--', alpha=0.5, linewidth=1)

# Aggiunta etichetta per le linee rosse solo una volta nella legenda
plt.plot([], [], color='red', linestyle='--', label='Cambio Iterazione')

plt.title('Analisi Reward per episodio: Media, Deviazione e Range (Min-Max)')
plt.xlabel('Numero Episodio (Progressivo)')
plt.ylabel('Step Reward')
plt.legend(loc='best')
plt.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.show()

# --- DATI EXTRA ---
print(f"\n{'='*30}")
print(f"REPORT ANALISI")
print(f"{'='*30}")
print(f"Episodi totali: {len(ep_df)}")
print(f"Iterazioni rilevate: {len(df)}")
print(f"Cadute totali nei 'buchi': {int(total_holes_count)}")
print(f"Miglior reward step mai ottenuto: {ep_df['max'].max():.2f}")
print(f"Peggior reward step mai ottenuto: {ep_df['min'].min():.2f}")
print(f"{'='*30}\n")