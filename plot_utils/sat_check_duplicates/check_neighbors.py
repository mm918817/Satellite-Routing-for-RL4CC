import json
from collections import defaultdict
import os

# ----- Script che stampa i satelliti doppi presenti nelle topology per i diversi time -----

script_dir = os.path.dirname(os.path.realpath(__file__))
file_path = os.path.join(script_dir, "satellite_topology.json")

with open(file_path, "r") as f:
    topologies = json.load(f)


# Lookup topologie per time
topo_by_time = {t["time"]: t for t in topologies}

# ---------------- Functions ----------------

# Trova satelliti con vicini duplicati in una topologia
def satellites_with_duplicate_neighbors(topology):
    result = []

    for sat in topology["satellites"]:
        neighbors = sat.get("neighbors", {})

        # Prende solo vicini validi (ignora "None")
        valid_neighbors = [v for v in neighbors.values() if v != "None"]

        seen = set()
        duplicates = set()

        for v in valid_neighbors:
            if v in seen:
                duplicates.add(v)
            else:
                seen.add(v)

        if duplicates:
            result.append({
                "satellite_id": sat["id"],
                "duplicate_neighbors": list(duplicates)
            })

    return result

# Controlla tutte le topologie
def find_duplicates_in_all_topologies(topologies):
    result = defaultdict(list)

    for topo in topologies:
        time = topo["time"]
        duplicates = satellites_with_duplicate_neighbors(topo)

        if duplicates:
            result[time].extend(duplicates)

    return result


# Esecuzione

all_duplicates = find_duplicates_in_all_topologies(topologies)


# Stampa risultati

if not all_duplicates:
    print("Nessun satellite con vicini duplicati trovato.")
else:
    for time, sats in all_duplicates.items():
        print(f"\nTime {time}:")
        for s in sats:
            print(
                f"  Satellite {s['satellite_id']} "
                f"-> vicini duplicati {s['duplicate_neighbors']}"
            )
