import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import ast
import os

base_path = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_path, 'estratto_progress.csv')

# Caricamento dati
df = pd.read_csv(file_path)

def parse_list(x):
    if isinstance(x, str):
        try: return ast.literal_eval(x)
        except: return []
    return x

# Conversione colonne
cols_to_fix = ['hist_stats/step_reward', 'hist_stats/episode_lengths']
for col in cols_to_fix:
    df[col] = df[col].apply(parse_list)

# --- LOGICA CUMULATA (Ogni 10 iterazioni) ---
window_size = 10
all_rewards_per_row = [r for r in df['hist_stats/step_reward'] if r]

grouped_rewards = []
grouped_labels = []

# Cicla aumentando il limite superiore ogni volta (10, 20, 30...)
for i in range(window_size, len(all_rewards_per_row) + 1, window_size):
    # Prende tutte le iterazioni da 0 fino alla posizione i corrente (Cumulata)
    chunk = all_rewards_per_row[0 : i] 
    
    # Unisce tutti i reward accumulati finora in una sola lista
    combined_chunk = [reward for sublist in chunk for reward in sublist]
    
    if combined_chunk:
        grouped_rewards.append(combined_chunk)
        # Etichetta che mostra l'intervallo cumulato (eg. "1-20", "1-30"...)
        label = f"1-{i}"
        grouped_labels.append(label)

# --- GRAFICO BOX PLOT ---
plt.figure(figsize=(12, 7))
ax = plt.gca()

positions = np.arange(1, len(grouped_labels) + 1)

bplot = plt.boxplot(grouped_rewards, 
                    positions=positions, 
                    patch_artist=True,
                    showmeans=True,
                    # Media cerchio rosso piccolo
                    meanprops={"marker":"o", "markerfacecolor":"red", "markeredgecolor":"black", "markersize":"5"})

# Colora le scatole di blu chiaro
for patch in bplot['boxes']:
    patch.set_facecolor('lightblue')

# Imposta le etichette per ogni posizione (1-10, 1-20, 1-30...)
ax.set_xticks(positions)
ax.set_xticklabels(grouped_labels, rotation=45)

# Limita il numero di etichette visibili per non affollare l'asse
ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=12))

plt.title(f'Distribuzione Reward Cumulata (Progressiva ogni {window_size} Iterazioni)')
plt.xlabel('Iterazioni Accumulate')
plt.ylabel('Step Reward')
plt.grid(axis='y', linestyle=':', alpha=0.6)

# Legenda dei simboli
plt.plot([], [], 'o', color='red', markeredgecolor='black', label='Media Cumulata')
plt.plot([], [], color='orange', label='Mediana Cumulata')
plt.plot([], [], 'o', color='white', markeredgecolor='black', label='Outliers')
plt.legend(loc='best', framealpha=0.9)

plt.tight_layout()
plt.show()

# --- INFO AGGIUNTIVE ---
print(f"Grafico generato: l'ultimo box rappresenta la media di tutte le {len(all_rewards_per_row)} iterazioni.")