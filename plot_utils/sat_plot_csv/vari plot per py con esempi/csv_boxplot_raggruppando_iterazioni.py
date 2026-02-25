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

# --- RAGGRUPPAMENTO ITERAZIONI( eg 10 iterazioni alla volta) ---
window_size = 10
all_rewards_per_row = [r for r in df['hist_stats/step_reward'] if r]

grouped_rewards = []
grouped_labels = []

for i in range(0, len(all_rewards_per_row), window_size):
    # Prende il blocco di eg. 10 iterazioni
    chunk = all_rewards_per_row[i : i + window_size]
    # Unisce tutti i reward del blocco in una sola lista
    combined_chunk = [reward for sublist in chunk for reward in sublist]
    
    if combined_chunk:
        grouped_rewards.append(combined_chunk)
        # Etichetta come richiesto (eg. 1-10, 11-20...)
        label = f"{i+1}-{i+len(chunk)}"
        grouped_labels.append(label)

# --- GRAFICO BOX PLOT ---
plt.figure(figsize=(12, 7))
ax = plt.gca()

positions = np.arange(1, len(grouped_labels) + 1)

bplot = plt.boxplot(grouped_rewards, 
                    positions=range(1, len(grouped_labels) + 1), 
                    patch_artist=True,
                    showmeans=True,
                    # Media cerchio rosso piccolo
                    meanprops={"marker":"o", "markerfacecolor":"red", "markeredgecolor":"black", "markersize":"5"})

# Colora le scatole di blu chiaro
for patch in bplot['boxes']:
    patch.set_facecolor('lightblue')

# Imposta le etichette per ogni posizione
ax.set_xticks(positions)
ax.set_xticklabels(grouped_labels, rotation=45)

# Limita il numero di etichette visibili ( eg. nbins=10)
ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=12))

plt.title(f'Distribuzione Reward (Aggregato ogni {window_size} Iterazioni)')
plt.xlabel('Intervallo Iterazioni')
plt.ylabel('Step Reward')
plt.grid(axis='y', linestyle=':', alpha=0.6)

# Legenda dei simboli
plt.plot([], [], 'o', color='red', markeredgecolor='black', label='Media')
plt.plot([], [], color='orange', label='Mediana')
plt.plot([], [], 'o', color='white', markeredgecolor='black', label='Outliers (Singoli Step)')
plt.legend(loc='best', framealpha=0.9)



plt.tight_layout()
plt.show()

# --- INFO AGGIUNTIVE ---
print(f"Grafico generato raggruppando {len(all_rewards_per_row)} iterazioni in {len(grouped_labels)} blocchi.")