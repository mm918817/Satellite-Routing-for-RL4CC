import json
import matplotlib.pyplot as plt
from collections import Counter

try:
    with open('dijkstra_results.json', 'r') as f:
        data = json.load(f)
except FileNotFoundError:
    print("Error: data.json file not found.")
    data = []

if data:
    # Estrazione della lunghezza di ogni 'path'
    # len(item['path']) cioè quanti nodi ci sono nel percorso dei nodi(satelliti)
    lengths = [len(item['path']) for item in data]

    # Conta le frequenze (quanti path hanno lunghezza 2, quanti 3, ecc.)
    distribution = Counter(lengths)
    
    total_flows = len(data) # Numero totale dei flussi nel file dijkstra

    # Ordina i dati in base alla lunghezza del path)
    sorted_lengths = sorted(distribution.items())
    x_values = [item[0] for item in sorted_lengths]  # Lunghezza del path
    y_values = [(item[1] / total_flows) * 100 for item in sorted_lengths]  # Frequenza (quanti elementi)

    # Stampa i risultati a terminale
    print("Path length distribution(%):")
    for length, percentage in zip(x_values, y_values):
        print(f"Length {length}: {percentage:.2f}%")

    # Creazione del grafico
    plt.figure(figsize=(10, 6))
    bars = plt.bar(x_values, y_values, color='skyblue', edgecolor='navy')

    # Aggiunge le etichette sopra ogni barra
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 0.2, f"{yval:.2f}%", ha='center', va='bottom', fontsize=12)

    plt.xlabel('Number of elements in the Path (Nodes)', fontsize=16)
    plt.ylabel('Frequency percentage (%)', fontsize=16)
    plt.title(f'Length distribution on {total_flows} paths', fontsize=16)
    plt.xticks(x_values, fontsize=14) # Mostra tutti i valori interi sulla X
    plt.yticks(fontsize=14)
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    plt.show()