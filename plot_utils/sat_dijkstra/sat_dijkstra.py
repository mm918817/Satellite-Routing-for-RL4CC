import json
import networkx as nx
from geopy.distance import geodesic
from pathlib import Path

# ----- Script che dato file dei flussi e delle topologie, restituisce un file con i path di dijkstra per ogni flusso -----

class SatelliteNetwork:
    def __init__(self, topology_file, flows_file):
        # Caricamento file JSON
        with open(topology_file, "r") as f:
            self.topologies = json.load(f)

        with open(flows_file, "r") as f:
            self.flows = json.load(f)

        # Lookup topologie per time
        self.topo_by_time = {t["time"]: t for t in self.topologies}

    def sat_distance(self, sat1, sat2):
        """Calcola la distanza in km tra due satelliti usando WGS84"""
        coord1 = (sat1['lat'], sat1['lon'])
        coord2 = (sat2['lat'], sat2['lon'])
        return geodesic(coord1, coord2).kilometers

    def build_graph(self, flow_time):
        """Costruisce il grafo della topologia per un dato time"""
        if flow_time not in self.topo_by_time:
            raise ValueError(f"Topologia per time {flow_time} non trovata.")

        self.topology = self.topo_by_time[flow_time]

        # Lookup satelliti per id
        self.sat_by_id = {sat["id"]: sat for sat in self.topology["satellites"]}

        # -------- Creazione grafo --------
        G = nx.Graph()

        # Aggiunge nodi (cioè ogni satellite)
        for sat_id, sat in self.sat_by_id.items():
            G.add_node(sat_id)

        # Aggiunge archi con peso distanza
        for sat_id, sat in self.sat_by_id.items():
            for direction, neighbor_id in sat["neighbors"].items(): # Per ogni satellite controlla n,s,e,w
                if neighbor_id != "None": # Salta vicini inesistenti (non c'è collegamento)
                    # Aggiunge solo se non esiste già (grafo non orientato)
                    if not G.has_edge(sat_id, neighbor_id):
                        distance = self.sat_distance(sat, self.sat_by_id[neighbor_id])
                        G.add_edge(sat_id, neighbor_id, weight=distance)

        return G

    def compute_flows_dijkstra(self, flow_time):
        """Calcola il percorso più corto per tutti i flussi di un certo time"""
        G = self.build_graph(flow_time)

        # Filtra i flussi per time
        flows_at_time = [f for f in self.flows if f["time"] == flow_time]

        results = []
        for flow in flows_at_time:
            start = flow["start_id"]
            end = flow["end_id"]
            try:
                path = nx.dijkstra_path(G, start, end, weight='weight') # Percorso pesato di satelliti più corto (dove il peso è la distanza)
                distance = nx.dijkstra_path_length(G, start, end, weight='weight') #  Lunghezza del percorso più corto pesato
                results.append({
                    "time": flow_time,  
                    "flow_id": flow["id"],
                    "start_id": start,
                    "end_id": end,
                    "path": path,
                    "distance_km": distance
                })
            except nx.NetworkXNoPath: # Se non c'è un path tra start_id ed end_id
                results.append({
                    "time": flow_time,  
                    "flow_id": flow["id"],
                    "start_id": start,
                    "end_id": end,
                    "path": None,
                    "distance_km": None
                })
        return results
    
def save_results_to_json(results, folder_name="flows_dijkstra_results", filename="dijkstra_results.json"):
    """
    Salva i risultati in un file JSON dentro una cartella.
    La cartella viene creata se non esiste.
    """

    # Percorso della directory dello script
    base_dir = Path(__file__).resolve().parent

    # Percorso della cartella risultati
    output_dir = base_dir / folder_name
    output_dir.mkdir(parents=True, exist_ok=True)

    # Percorso file finale
    output_file = output_dir / filename

    # Scrittura JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Risultati salvati in: {output_file}")

# Utilizza, specificando il "time" usato per selezionare la topologia ed i flussi associati
if __name__ == "__main__":

    network = SatelliteNetwork(
        "satellite_topology.json",
        "flows_src__dst_timeline.json"
    )

    print("Vuoi:")
    print("1 - Calcolare i flow per un time specifico")
    print("2 - Calcolare i flow per TUTTI i time")

    choice = input("Seleziona (1/2): ").strip()

    all_results = []

    if choice == "1":
        flow_time = int(input("Inserisci il valore di time: "))
        flow_results = network.compute_flows_dijkstra(flow_time)
        all_results.extend(flow_results)

    elif choice == "2":
        # Prende tutti i time disponibili nei flussi
        all_times = sorted(set(f["time"] for f in network.flows))

        for t in all_times:
            print(f"\n--- Calcolo flow per time = {t} ---")
            flow_results = network.compute_flows_dijkstra(t)
            all_results.extend(flow_results)

    else:
        raise ValueError("Scelta non valida. Usa 1 o 2.")

    # Salvataggio unico
    save_results_to_json(all_results)

    # Stampa a schermo
    for r in all_results:
        print(r)

    valid_distances = [r["distance_km"] for r in all_results if r["distance_km"] is not None]

    if valid_distances:
        max_dist = max(valid_distances)
        print("\n" + "="*30)
        print(f"DISTANZA MASSIMA TROVATA: {max_dist:.2f} km")
        print("="*30)
    else:
        print("\nNessuna distanza calcolabile trovata.")