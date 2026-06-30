import json
import os
from geopy.distance import geodesic

def process_satellite_topology():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(base_dir, 'satellite_topology.json')
    output_file = os.path.join(base_dir, 'topology_report.json')

    if not os.path.exists(input_file):
        print(f"Error: '{input_file}' file not found in the script folder")
        return

    with open(input_file, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print("Error: JSON file is not correctly formatted")
            return

    report = []
    all_time_averages = []

    print("--- Start of processing ---")

    for entry in data:
        timestamp = entry.get('time')
        satellites = entry.get('satellites', [])
        
        sat_coords = {s['id']: (s['lat'], s['lon']) for s in satellites}
        unique_links = set()
        distances = []

        for s in satellites:
            u_id = s['id']
            u_pos = (s['lat'], s['lon'])
            
            for direction, v_id in s['neighbors'].items():
                if v_id is not None and v_id in sat_coords:
                    # Coppia ordinata per evitare duplicati
                    link_key = tuple(sorted((u_id, v_id)))
                    
                    if link_key not in unique_links:
                        unique_links.add(link_key)
                        v_pos = sat_coords[v_id]
                        # Calcolo geodetico WGS84
                        dist = geodesic(u_pos, v_pos).kilometers
                        distances.append(dist)
        
        # Calcolo media per il timestamp corrente
        if distances:
            mean_dist = sum(distances) / len(distances)
            all_time_averages.append(mean_dist)
        else:
            mean_dist = 0
        
        report.append({
            "time": timestamp,
            "hop_mean_distance_km": round(mean_dist, 3),
            "active_links_count": len(distances)
        })

    # Scrittura del report JSON
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=4)
    
    # Calcolo e stampa della media globale (media delle medie)
    if all_time_averages:
        global_avg = sum(all_time_averages) / len(all_time_averages)
        print(f"Report saved in: {output_file}")
        print("-" * 50)
        print(f"GLOBAL MEAN (among all topologies): {global_avg:.3f} km")
        print("-" * 50)
    else:
        print("No valid data found to calculate the mean")

if __name__ == "__main__":
    process_satellite_topology()