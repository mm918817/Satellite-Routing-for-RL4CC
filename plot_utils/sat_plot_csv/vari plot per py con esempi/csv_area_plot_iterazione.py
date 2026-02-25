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
        try:
            return ast.literal_eval(x)
        except:
            return []
    return x

# Conversione delle colonne da stringhe a liste
cols_to_fix = ['hist_stats/step_reward', 'hist_stats/hole_counter', 'hist_stats/episode_lengths']
for col in cols_to_fix:
    df[col] = df[col].apply(parse_list)

iteration_stats = []
total_holes_count = 0
total_episodes_count = 0

# Itera direttamente sulle righe (ogni riga = una iterazione)
for i, row in df.iterrows():
    rewards = row['hist_stats/step_reward']
    holes = row['hist_stats/hole_counter']
    lengths = row['hist_stats/episode_lengths']
    
    if rewards: # Verifica che ci siano dati
        iteration_stats.append({
            'iteration': i + 1,
            'mean': np.mean(rewards),
            'std': np.std(rewards),
            'min': np.min(rewards),
            'max': np.max(rewards),
            'num_episodes': len(lengths)
        })
        total_holes_count += np.sum(holes)
        total_episodes_count += len(lengths)

# Crea il DataFrame per il plot
iter_df = pd.DataFrame(iteration_stats)

# --- GRAFICO ---
plt.figure(figsize=(12, 6))
ax = plt.gca() # Per avere l'asse con "config avanzata" dinamica
x = iter_df['iteration']

# 1. Area Range Reale (Min-Max)
plt.fill_between(x, iter_df['min'], iter_df['max'], color='gray', alpha=0.1, label='Range Min-Max Iterazione')

# 2. Area Deviazione Standard (Sigma)
plt.fill_between(x, iter_df['mean'] - iter_df['std'], iter_df['mean'] + iter_df['std'], 
                 color='blue', alpha=0.2, label=r'Std Dev ($\sigma$)')

# 3. Linea della Media con marker
plt.plot(x, iter_df['mean'], color='blue', marker='o', markersize=6, linewidth=2, label='Reward Medio Iterazione')


# Gestisce automaticamente quanti numeri mostrare
ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, nbins=10))

plt.title('Reward per Iterazione (Aggregato Episodi)')
plt.xlabel('Numero Iterazione')
plt.ylabel('Step Reward')

plt.legend(loc='best', framealpha=0.8, shadow=True)
plt.grid(axis='y', linestyle=':', alpha=0.6)

plt.tight_layout()
plt.show()

# --- REPORT FINALE ---
print(f"\n{'='*40}")
print(f"REPORT ANALISI PER ITERAZIONE")
print(f"{'='*40}")
print(f"Iterazioni totali: {len(iter_df)}")
print(f"Episodi totali analizzati: {total_episodes_count}")
print(f"Cadute totali nei 'buchi': {int(total_holes_count)}")
print(f"{'-'*40}")
print(f"Miglior reward medio (Iterazione): {iter_df['mean'].max():.4f}")
print(f"Peggior reward medio (Iterazione): {iter_df['mean'].min():.4f}")
print(f"{'='*40}\n")