import json
import numpy as np
from geopy.distance import geodesic
import time
import csv

class RewardValidator:
    def __init__(self, topo_file, eval_file, dijkstra_file, w_step=1.0, w_dest=1.0):
        self.w_step = w_step
        self.w_dest = w_dest
        self.MAX_HOPS = 9 # Da dijkstra_hop_number.py ci sono al max 9 hop

        # Caricamento dati
        with open(topo_file, "r") as f:
            topologies = json.load(f)
        with open(eval_file, "r") as f:
            self.eval_flows = json.load(f)
        with open(dijkstra_file, "r") as f:
            dijkstra_data = json.load(f)

        # Lookup table: self.topo[time][sat_id] -> (dati sat)
        # Per ottenere direttamente i dati del satellite dalla topologia ed id specificati
        # 2 dizionari annidati
        self.topo = {}
        for t_entry in topologies:
            t = t_entry["time"] 
            self.topo[t] = {    # Assegna ogni topologia al suo "time"
                s["id"]: s 
                for s in t_entry["satellites"] # Quindi associa al "time" i satelliti per quella topologia
            }

        # Lookup table: self.dijkstra_lookup [(time, start_id, end_id)] -> (dati flusso)
        # La chiave è una tupla
        self.dijkstra_lookup = {
            (d["time"], d["start_id"], d["end_id"]): d 
            for d in dijkstra_data
        }

    def get_dist(self, s1, s2):
        return geodesic((s1['lat'], s1['lon']), (s2['lat'], s2['lon'])).kilometers

    def run_validation(self, output_path="reward_report"):
        all_rewards = []
        all_distances = []
        report_data = [] # Lista dati per CSV/json

        print(f"{'='*66}")
        print(f"{'REWARD VALIDATION':^60}")
        print(f"{'='*66}\n")

        for flow in self.eval_flows:
            flow_uuid = flow.get("id", "N/A")
            t = flow["time"]
            s_id = flow["start_id"]
            e_id = flow["end_id"]
            
            # Recupera il path dijkstra pre-calcolato
            d_entry = self.dijkstra_lookup.get((t, s_id, e_id))
            if not d_entry:
                print(f" Dijkstra path not found for the {flow_uuid} flow ({s_id}->{e_id}) at time {t}")
                continue

            path = d_entry["path"]
            d_dist = d_entry["distance_km"]
            d_hop = len(path) - 1
            
            # Stato simulato dell'ambiente
            total_reward = 0.0
            dist_tot = 0.0
            step_counter = 0
            current_topo = self.topo[t] # Mappa satelliti per questo specifico tempo
            end_sat = current_topo[e_id]
            jumps_rewards_list = []

            print(f"=> Flow {flow_uuid} | Route: {s_id} -> {e_id} | Time: {t}")
            print(f"{'-'*66}")

            # Simula inoltro(salto) da un sat ad un altro del path Dijkstra
            # eg. 4 sat [100,105,109,112], fa 3 inoltri
            for i in range(1, len(path)):
                prev_id = path[i-1]
                curr_id = path[i]
                step_counter += 1
                # print(f"Salto da {prev_id} ad {curr_id}") #DEBUG

                s_prev = current_topo[prev_id]
                s_curr = current_topo[curr_id]
                
                # Calcola distanza percorsa
                dist_jump = self.get_dist(s_prev, s_curr)
                dist_tot += dist_jump
                # print(f"Aggiunta di {dist_jump} al totale {dist_tot}") #DEBUG

                # --- LOGICA REWARD ---
                if curr_id == e_id:
                    # Reward Destinazione
                    reward = (d_dist / dist_tot) * self.w_dest # Reward destinazione dinamico (dovrebbe essere in base alla distanza di dijkstra)
                    # reward = 1 # Reward fisso ad 1
                    #print(f"Reward dest: {reward}") # Debug
                    label = "FINAL(Dest)"
                else:
                    # Reward Step
                    neighbors_dict = s_prev["neighbors"]
                    neighbor_ids = [int(v) for v in neighbors_dict.values() if v != "None"]
                    
                    # Distanze di tutti i vicini possibili verso la meta
                    dists = {nid: self.get_dist(current_topo[nid], end_sat) for nid in neighbor_ids}
                    
                    d_near = min(dists.values())
                    d_far = max(dists.values())
                    d_current = self.get_dist(s_curr, end_sat)

                    if d_far == d_near:
                        step_dyn_reward = 0.0
                    else:
                        step_dyn_reward = (1 - (d_current - d_near) / (d_far - d_near))
                    
                    # Logica basata sugli step di dijkstra (1/30)
                    if step_counter <= d_hop:
                        reward = (1/30) * step_dyn_reward * self.w_step
                        #reward = reward + 0.05 # Bonus se agente si comporta come dijsktra (imitation learning leggero)
                    else:
                        reward = -((1/30) * step_dyn_reward * self.w_step)
                    #reward = 1 # Reward fisso ad 1 (imitation learning forte)
                    label = f"STEP {step_counter}"

                    #print(f"Reward step: {reward}") # Debug
                
                total_reward += reward
                jumps_rewards_list.append(round(reward, 5))

                print(f"  {label:<12} | {prev_id:>3} -> {curr_id:<3} | Dist: {dist_jump:>7.2f} km | Reward: {reward:>8.5f}")

            # --- PREPARAZIONE DATI PER REPORT ---
            # Creazione riga per report
            route_str = f"{s_id}->{e_id}" # "sat iniziale -> sat finale"
            row = {
                "flow_uuid": flow_uuid,  # ID flusso
                "route": route_str,       
                "time": t,
                "hops": d_hop,
                "total_distance": round(dist_tot, 2),
                "total_reward": round(total_reward, 5)
            }
            
            # Aggiunge i singoli salti (fino a MAX_HOPS)
            for j in range(self.MAX_HOPS):
                column_name = f"jump_{j+1}_reward"
                if j < len(jumps_rewards_list):
                    row[column_name] = jumps_rewards_list[j]
                else:
                    row[column_name] = None

            report_data.append(row)
            all_rewards.append(total_reward)
            all_distances.append(dist_tot)
            # Stampa riassuntiva flusso
            print(f"{'-'*66}")
            print(f"  Result: Tot Distance: {dist_tot:.2f} km | Tot Reward: {total_reward:.5f}\n")

        # --- EXPORT CSV ---
        keys = report_data[0].keys()
        with open(f"{output_path}.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(report_data)

        # --- EXPORT JSON ---
        with open(f"{output_path}.json", "w") as f:
            json.dump(report_data, f, indent=4)

        print("-" * 60)
        print(f"Tot Distance mean: {np.mean(all_distances):.4f} km and Tot Reward mean: {np.mean(all_rewards):.4f}") #Media fatta sui reward totali tra i flussi
        print(f"Report saved: {output_path}.csv and {output_path}.json")

# --- ESECUZIONE ---
validator = RewardValidator(
    topo_file="satellite_topology.json", 
    eval_file="flows_eval.json", 
    dijkstra_file="dijkstra_results.json",
    w_step=1.0, 
    w_dest=1.0
)
validator.run_validation(output_path="report_reward_jumps")
time.sleep(5)