import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import ast
import os

base_path = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_path, 'estratto_progress.csv')

df = pd.read_csv(file_path)

def parse_list(x):
    if isinstance(x, str):
        try: return ast.literal_eval(x)
        except: return []
    return x

df['hist_stats/step_reward'] = df['hist_stats/step_reward'].apply(parse_list)
all_rewards_per_row = [r for r in df['hist_stats/step_reward'] if r]

# --- LOGICA MEDIA MOBILE (SLIDING WINDOW) ---
window_size = 10
# Per saltare dei passi per non avere troppi box (eg. 2 o 5)
step_size = 1 

sliding_rewards = []
sliding_labels = []

for i in range(0, len(all_rewards_per_row) - window_size + 1, step_size):
    # Sliding window da i a i + window_size
    chunk = all_rewards_per_row[i : i + window_size]
    combined_chunk = [reward for sublist in chunk for reward in sublist]
    
    if combined_chunk:
        sliding_rewards.append(combined_chunk)
        # L'etichetta l'intervallo della finestra
        sliding_labels.append(f"{i+1}-{i+window_size}")

# --- GRAFICO BOX PLOT ---
plt.figure(figsize=(15, 7))
ax = plt.gca()

positions = np.arange(1, len(sliding_labels) + 1)

# Se ci sono molti box, riduce la larghezza (widths) e toglie i bordi troppo spessi
bplot = plt.boxplot(sliding_rewards, 
                    positions=positions, 
                    patch_artist=True,
                    showmeans=True,
                    widths=0.7,
                    # Media cerchio rosso  piccolo
                    meanprops={"marker":"o", "markerfacecolor":"red", "markeredgecolor":"none", "markersize":"3"},
                    # outlier piccoli
                    flierprops={"marker": "o", "markersize": 1, "alpha": 0.7})

for patch in bplot['boxes']:
    patch.set_facecolor('lightblue')
    patch.set_linewidth(0.5) # Linee più sottili per alta densità

# Gestione asse X
ax.set_xticks(positions)
ax.set_xticklabels(sliding_labels)
# Mostra poche etichette per evitare sovrapposizioni
ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=15))
plt.xticks(rotation=45)

plt.title(f'Media Mobile Box Plot (Finestra: {window_size}, Passo: {step_size})')
plt.xlabel('Finestra Temporale (Iterazioni)')
plt.ylabel('Step Reward')
plt.grid(axis='y', linestyle=':', alpha=0.4)

# Legenda dei simboli
plt.plot([], [], 'o', color='red', markeredgecolor='black', label='Media Cumulata')
plt.plot([], [], color='orange', label='Mediana Cumulata')
plt.plot([], [], 'o', color='white', markeredgecolor='black', label='Outliers')
plt.legend(loc='best', framealpha=0.9)

plt.tight_layout()
plt.show()

# --- INFO AGGIUNTIVE ---
print(f"Creati {len(sliding_labels)} box con sliding window.")