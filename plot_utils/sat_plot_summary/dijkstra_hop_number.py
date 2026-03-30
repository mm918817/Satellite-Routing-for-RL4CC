import json
import matplotlib.pyplot as plt
from collections import Counter

try:
    with open('dijkstra_results.json', 'r') as f:
        data = json.load(f)
except FileNotFoundError:
    print("Errore: Il file data.json non è stato trovato.")
    data = []

if data:
    # Estrazione della lunghezza di ogni 'path'
    # len(item['path']) cioè quanti nodi ci sono nel percorso dei nodi(satelliti)
    lengths = [len(item['path']) for item in data]

    # Conta le frequenze (quanti path hanno lunghezza 2, quanti 3, ecc.)
    distribution = Counter(lengths)
    
    # Ordina i dati in base alla lunghezza del path)
    sorted_lengths = sorted(distribution.items())
    x_values = [item[0] for item in sorted_lengths]  # Lunghezza del path
    y_values = [item[1] for item in sorted_lengths]  # Frequenza (quanti elementi)

    # Stampa i risultati testuali a terminale
    print("Distribuzione lunghezze path:")
    for length, count in sorted_lengths:
        print(f"Lunghezza {length}: {count} elementi")

    # Creazione del grafico
    plt.figure(figsize=(10, 6))
    bars = plt.bar(x_values, y_values, color='skyblue', edgecolor='navy')

    # Aggiunge le etichette sopra ogni barra
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 0.1, yval, ha='center', va='bottom')

    plt.xlabel('Numero di elementi nel Path (Nodi)')
    plt.ylabel('Frequenza (Conteggio)')
    plt.title('Distribuzione della lunghezza dei percorsi')
    plt.xticks(x_values) # Mostra tutti i valori interi sulla X
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    plt.show()