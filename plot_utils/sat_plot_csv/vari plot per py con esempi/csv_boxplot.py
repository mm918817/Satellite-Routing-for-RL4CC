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

# Preparazione dati, una lista di liste (una lista di reward per ogni iterazione)
all_iterations_rewards = []
iteration_labels = []

for i, row in df.iterrows():
    rewards = row['hist_stats/step_reward']
    if rewards:
        all_iterations_rewards.append(rewards)
        iteration_labels.append(i + 1)

# --- GRAFICO BOX PLOT ---
plt.figure(figsize=(12, 7))
ax = plt.gca()

# Creazione del Box Plot
# patch_artist=True permette di colorare l'interno delle scatole
# showmeans=True aggiunge un punto per la media (e la linea della mediana)
bplot = plt.boxplot(all_iterations_rewards, 
                    positions=iteration_labels, 
                    patch_artist=True,
                    showmeans=True,
                    meanprops={"marker":"o", "markerfacecolor":"red", "markeredgecolor":"black", "markersize":"3"})

# Colora le scatole di blu chiaro
for patch in bplot['boxes']:
    patch.set_facecolor('lightblue')

if len(iteration_labels) > 20:
    interval = max(1, len(iteration_labels) // 15) # Mostra circa 20 etichette totali
    ax.set_xticks(iteration_labels[::interval])
    ax.set_xticklabels(iteration_labels[::interval])
else:
    ax.set_xticks(iteration_labels)


plt.title('Distribuzione Reward per Iterazione (Box Plot)')
plt.xlabel('Numero Iterazione')
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
print(f"Grafico generato per {len(all_iterations_rewards)} iterazioni.")
print("La scatola rappresenta il 50% centrale dei dati (IQR).")
print("I 'baffi' mostrano l'estensione dei dati, i punti isolati sono gli outlier.")