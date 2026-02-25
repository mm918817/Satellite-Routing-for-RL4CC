from ray.rllib.env.env_context import EnvContext
from gymnasium.spaces import Discrete, Box
import gymnasium as gym
import numpy as np
import json
from RL4CC.environment.base_environment import BaseEnvironment
from geopy.distance import geodesic

class SatEnvironment(BaseEnvironment):
    def __init__(self, env_config: EnvContext):

            # Carico tutta la configurazione(gestione)
            seed = self.load_configuration(env_config)

            # Ridefinizione spazi sovrascrivendo quelli base_environment
            self.define_observation_space()
            self.define_action_space()

            self.reset(seed=seed)

    def load_configuration(self, env_config):
        """
        Estende il load del BaseEnvironment di RL4CC.
        Carica le configurazioni temporali ed i JSON con info satellitari.
        """
        super().load_configuration(env_config)

        self.is_evaluation = env_config.get("is_evaluation", False) # Flag se sono in evaluation

        if self.is_evaluation: # Se in eval, inizializza contatore sequenziale flussi
                self.flow_index = 0

        # Caricamento file JSON dai file di config
        with open(env_config["flows_file"], "r") as f:
            self.flows = json.load(f)

        with open(env_config["topology_file"], "r") as f:
            self.topologies = json.load(f)

        with open(env_config["flows_dijkstra"], "r") as f:  # json con dijkstra calcolato per ogni flusso in ogni topologia
            self.flows_dijkstra = json.load(f)

        # Lookup Dijkstra: (time, start_id, end_id) -> item
        self.dijkstra_by_key = {
            (item["time"], item["start_id"], item["end_id"]): item
            for item in self.flows_dijkstra
        }

        # Lookup topologie: (time) -> topologia associata
        self.topo_by_time = {t["time"]: t for t in self.topologies}

        # Peso per regolare reward step intermedio
        self.w_step = env_config["step_weight"]
        print("parametro reward per step è", self.w_step)

        # Peso per regolare reward raggiunta la destinazione
        self.w_dest = env_config["dest_weight"]
        print("parametro reward raggiunta destinazione è", self.w_dest)
        

        return None  # seed, nel base_environment questa funzione restituisce un seed da passare al reset


    def define_observation_space(self):
        """
        Osservazione con le coordinate:
         - del satellite attuale
         - dei 3 suoi vicini(si toglie il satellite precedente)
         - del satellite finale
        [cur_lat, cur_lon,
        lat1, lon1,
        lat2, lon2,
        lat3, lon3,
        end_lat, end_lon]
        """
        # Tutti i satelliti possibili
        #self.valid_sat_ids = sorted([100, 102, 103, 104, 106, 107, 108, 109, 110, 111, 112, 113, 114, 116, 117, 118, 119, 
        #                             120, 121, 122, 123, 125, 126, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 
        #                             139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 
        #                             156, 157, 158, 159, 160, 163, 164, 165, 166, 167, 168, 171, 172, 173, 180])
        
        # range lat -90,+90 , range lon -180,+180 , per valori None considero -190 per entrambi lat e lon.
        self.min_lat_lon = -190
        self.max_lat_lon = 190

        self.observation_space = Box(
            low = self.min_lat_lon,
            high = self.max_lat_lon,
            shape = (10,),
            dtype = np.float32
        )


    def define_action_space(self):
        """
        Azione = scegliere uno tra 4 possibili vicini (nord, sud, est, ovest)
        (Si rimuove il satellite da cui si è arrivati quindi sono 3 azioni)
        """
        self.action_space = Discrete(3)


    def observation(self):
        obs = np.array([self.cur_lat, self.cur_lon,
                        self.lat1, self.lon1,
                        self.lat2, self.lon2,
                        self.lat3, self.lon3,
                        self.end_lat, self.end_lon])
        info = {
            "current_time": self.current_time,
            "step_reward": self.last_reward,
            "hole_counter" : self.hole_counter,
            "current_sat": self.current_sat,
            "total_distance": self.dist_tot,
            "dest_reached": self.dest_reached,
            "dijkstra_dist":self.dijkstra_dist,
            "dijkstra_hop":self.dijkstra_hop,

        }

        return obs, info
    

    def reset(self, seed=None, options=None):
        """
        Sceglie un flow random dal json ed inizializza i valori associati per l'inizio dell'episodio
        Recupera la topologia associata al flow e crea una mappa con i satelliti presenti al suo interno
        Inizializza id satellite corrente, il satellite precedente, il reward e la distanza totale
        Inizializza i valori per l'osservazione e calcola la prima osservazione usando compute_first_neighbors
        """       
       # Inizializza gli attributi prima di super
        self.current_sat = 0
        self.previous_sat = None
        self.start_id = 0
        self.end_id = 0
        self.dist_tot = 0.0 # distanza totale accumulata
        self.last_reward = 0.0 # reward iniziale = 0 , usato in observation
        self.current_time = self.min_time
        self.hole_counter = 0
        self.dest_reached = 0
        self.dijkstra_dist = 0.0 
        self.dijkstra_hop = 0
        self.step_counter = 0
        # lat e lon dei satelliti dell'osservazione
        self.cur_lat = -190.0
        self.cur_lon = -190.0
        self.lat1 = -190.0
        self.lon1 = -190.0
        self.lat2 = -190.0
        self.lon2 = -190.0
        self.lat3 = -190.0
        self.lon3 = -190.0
        self.end_lat = -190.0
        self.end_lon = -190.0

        
        super().reset(seed=seed)

        if self.is_evaluation:
            # Selezione flow SEQUENZIALE per la valutazione
            self.current_flow = self.flows[self.flow_index]        
            self.flow_index = (self.flow_index + 1) % len(self.flows)
            print(f"EVAL FLOW (Index {self.flow_index}):", self.current_flow)
        else:
            # Selezione flow RANDOM per il training
            self.current_flow = np.random.choice(self.flows)
            print("TRAIN FLOW (Random):", self.current_flow)

        self.start_id = self.current_flow["start_id"]
        self.end_id = self.current_flow["end_id"]
        flow_time = self.current_flow["time"]
        print("FLOW:", self.current_flow) # DEBUG flow

        # Recupero dijkstra per il flusso selezionato
        key = (flow_time, self.start_id, self.end_id)
        dijkstra_entry = self.dijkstra_by_key.get(key)
        if dijkstra_entry is None:
            raise ValueError(f"Nessun risultato Dijkstra per {key}")
        self.dijkstra_dist = dijkstra_entry["distance_km"] # Distanza dijkstra da inizio a fine flusso
        self.dijkstra_hop = (len(dijkstra_entry["path"])-1) # Hop dijkstra da inizio a fine flusso
        print(f"DIJKSTRA: distanza {self.dijkstra_dist}, hop {self.dijkstra_hop}") # DEBUG dijkstra


        # Topologia associata al time
        self.topology = self.topo_by_time[flow_time]

        # Lookup per i satelliti dell'attuale topologia: (id) -> satellite
        self.sat_by_id = {
            sat["id"]: sat for sat in self.topology["satellites"]
        }

        # Lookup per ottenere l'id di un satellite date le coordinate : (lat, lon) -> id sat
        self.sat_by_coords = {
            (sat["lat"], sat["lon"]): sat_id
            for sat_id, sat in self.sat_by_id.items()
        }

        self.current_sat = self.start_id

        self.cur_lat = self.sat_by_id[self.current_sat]["lat"]
        self.cur_lon = self.sat_by_id[self.current_sat]["lon"]
        self.end_lat = self.sat_by_id[self.end_id]["lat"]
        self.end_lon = self.sat_by_id[self.end_id]["lon"]

        f_obs = self.compute_first_neighbors(self.current_sat)
        # Aggiorno le variabili lat e lon dei vicini per l'inizio, dalla prima osservazione
        self.lat1 = f_obs[2]
        self.lon1 = f_obs[3]
        self.lat2 = f_obs[4]
        self.lon2 = f_obs[5]
        self.lat3 = f_obs[6]
        self.lon3 = f_obs[7]
        print("-- LAT primo sat vicino:", self.lat1) # DEBUG lat
        obs, info = self.observation()


        return obs, info


    def step(self, action):
        """
        In base all'action presa imposta i nuovi valori usati dall'osservazione:
        La lat e lon del nuovo satellite corrente così come quelle dei suoi vicini
        escludendo il satellite da cui si arriva.
        """
        terminated = False
        truncated = False


        self.current_time += self.time_step # update time
        self.step_counter += 1 
        s_obs, s_info = self.observation()
        print(" -- ACTION selected:", action) # DEBUG action
        idx = 2 + (action * 2)
        act_lat = s_obs[idx]
        act_lon = s_obs[idx+1]
        print(" -- LAT selected by action:", act_lat) # DEBUG lat

        if act_lat < -189.0 and act_lon < -189.0 : # Vicino non valido, agente sta fermo e non fa nulla
            self.last_reward = -1 # update reward
            self.hole_counter += 1
 
            s_obs, s_info = self.observation() # Per aggiornare il valore di hole_counter

            blocked = (self.hole_counter >=5) # Se sto fermo almeno 5 volte
            if blocked:
                print(" OOO Agente fermo per troppi step OOO ")
                truncated = True
            timeout = (self.current_time >= self.max_time and not blocked)
            if timeout:
                print(" OOO Timeout OOO ") 
                truncated = True
            print("reward None", self.last_reward) # DEBUG reward            
            return s_obs, self.last_reward, terminated, truncated, s_info

        # self.hole_counter = 0  # Per resettare il counter se l'agente si libera dal vicolo cieco prima del cap

        # Aggiorna i valori che verranno usati dalla nuova osservazione
        self.cur_lat = act_lat
        self.cur_lon = act_lon
        
        self.previous_sat = self.current_sat
        self.current_sat = self.sat_by_coords[(self.cur_lat, self.cur_lon)]
        cur_info = self.sat_by_id[self.current_sat]

        new_neighbors = cur_info["neighbors"]
        dirs = ["n", "s", "e", "w"]

        seen = set() # Per tenere traccia se si ripete un satellite tra i vicini
        filtered_neighbors = [] # Rimuove satellite da cui sono arrivato
        
        for d in dirs:
            n_id = new_neighbors[d]
            if n_id != "None":
                n_id = int(n_id)
                # Ignora se è il sat precedente e se è già stato messo (per evitare stesso vicino 2 volte)
                if n_id != self.previous_sat and n_id not in seen:
                    filtered_neighbors.append(n_id)
                    seen.add(n_id)

        while len(filtered_neighbors) < 3: # Controllo per quando ho 2 volte lo stesso vicino, ed ho solo 2 valori in filtered_neighbors
            filtered_neighbors.append("None")

        lat_lon_values = [] # Recupera lat e lon dei nuovi vicini ed aggiorna i valori dell'osservazione
        
        for n_id in filtered_neighbors:
            if n_id == "None": # Se è None assegna valori sfavorevoli
                lat_lon_values.append((-190.0, -190.0))
            else:
                sat = self.sat_by_id[n_id]
                lat_lon_values.append((sat["lat"], sat["lon"]))

        print(" -- salto da",self.previous_sat, self.current_sat)
        print(" -- tutto lat lon",lat_lon_values)
        self.lat1, self.lon1 = lat_lon_values[0]
        print(" -- COPPIA lat lon 0:", lat_lon_values[0]) # DEBUG lat
        self.lat2, self.lon2 = lat_lon_values[1]
        print(" -- COPPIA lat lon 1:", lat_lon_values[1]) # DEBUG lat
        self.lat3, self.lon3 = lat_lon_values[2]
        print(" -- COPPIA lat lon 2:", lat_lon_values[2]) # DEBUG lat
        
        reward = self.compute_reward() # Update reward
        self.last_reward = reward

        terminated = (self.current_sat == self.end_id)
        truncated = (self.current_time >= self.max_time)
        if terminated:
            print(" ooo episodio completato con successo ooo")
        if truncated and not terminated:
            print(" ooo Timeout ooo")
            reward = -1
            self.last_reward = reward

        obs, info = self.observation()

        return obs, reward, terminated, truncated, info


    def compute_reward(self):
        """
        Reward:
        - (DESTINAZIONE) Se current_sat è l'end_id ->  self.dijkstra_dist / self.dist_tot
        - (STEP) Altrimenti -> 1 - [(d(current, end) - d(near, end)) / (d(far, end) - d(near, end))]
        -- Nel secondo caso, calcolo per il sat scelto rispetto ai sat disponibili dal precedente satellite
        -- Vengono scartati i sat None e si considerano solo satelliti dove è possibile calcolare le distanze
        """
        # Aggiorna distanza totale percorsa
        end_sat = self.sat_by_id[self.end_id]
        self.dist_jump = self.sat_distance(self.sat_by_id[self.previous_sat], self.sat_by_id[self.current_sat])
        self.dist_tot += self.dist_jump

     # --- REWARD DESTINAZIONE ---
        if self.current_sat == self.end_id: # Se ho raggiunto la destinazione
            # Non tiene conto della divisione zero, ma i file flussi non possono avere stesso inizio e destinazione
            #reward = (self.dijkstra_dist / self.dist_tot)*self.w_dest # Reward destinazione dinamico
            reward = 1 # Reward destinazione fisso ad 1
            self.dest_reached = 1
            print("reward raggiunta destinazione", reward) # DEBUG reward            
            return reward

        # --- REWARD STEP ---
        # Vicini del previous_sat
        neighbors = self.sat_by_id[self.previous_sat]["neighbors"]

        # Converte in interi, sono i vicini del sat "precedente"
        # Quindi ho almeno il sat da cui siamo arrivati al "precedente" ed il sat scelto in questo step (cioè dal "precedente")
        neighbor_ids = []
        for d in ["n", "s", "e", "w"]:
            n = neighbors[d]
            if n != "None":
                neighbor_ids.append(int(n))
        if not neighbor_ids:
            print ("-- ERRORE -- vicini non esistenti ")
            # return -1  # Fallback se non ci sono vicini validi, non dovrebbe capitare

        # Calcola le distanze rispetto a end_id
        distances = {nid: self.sat_distance(self.sat_by_id[nid], end_sat) for nid in neighbor_ids}

        # Trova id satellite più vicino e più lontano
        near_sat_id = min(distances, key=distances.get) # chiave in distances che ha il valore associato minimo
        far_sat_id = max(distances, key=distances.get) # chiave in distances che ha il valore associato massimo 

        d_current = self.sat_distance(self.sat_by_id[self.current_sat], end_sat)
        d_near = distances[near_sat_id]
        d_far = distances[far_sat_id]

        # Evita divisione per zero (non dovrebbe succedere mai)
        if d_far == d_near:
            print ("- d_far uguale a d_near", d_far, d_near) # DEBUG reward
            return 0.0 
        # Non posso avere divisione per zero, perchè ho sempre almeno un satellite da cui arrivo ed uno dove posso andare per le distanze
        # Molto difficilmente hanno esattamente la stessa distanza dalla destinazione, 
        # ed il caso vicini tutti None è gestito implicitamente nello step (se non ho action valida sto fermo)
        step_dyn_reward = ((1 - (d_current - d_near) / (d_far - d_near))) 
        if self.step_counter <= self.dijkstra_hop: # Reward step (1/30*dinamico) se impiego <= step di dijkstra, altrimenti -(1/30*dinamico), mettendo w_step ad 1
            reward = ((1/30)*step_dyn_reward*self.w_step) # 1/30 perchè 30 è il numero max di step per episodio
        else:
            reward = -((1/30)*step_dyn_reward*self.w_step)
        #reward = ((1 - (d_current - d_near) / (d_far - d_near))*self.w_step) # Reward step dinamico in base a bontà del vicino scelto
        print ("reward step è", reward) # DEBUG reward
        return reward

    def compute_first_neighbors(self, sat_id):
        """
        - Crea un array per i 10 valori delle coordinate che poi ritornerà
        
        - Aggiorna i valori per l'osservazione iniziale, con i 3 vicini validi scelti in base ai criteri:
        -- Se per il sat iniziale ho un satellite vicino "None" lo scarto e tengo gli altri vicini 
        (se ho 2 None considero un'altra volta il satellite migliore, 
        non dovrebbe capitare 3 None perchè le stazioni non sono vicine a fasce dei poli, ma nel caso dovrebbe prendere 3 volte la stessa scelta)
        -- Altrimenti dei satelliti vicini ordino in base alla distanza da quello finale e scarto il più lontano
        
        [cur_lat, cur_lon,
        lat1, lon1,
        lat2, lon2,
        lat3, lon3,
        end_lat, end_lon]
        """
        first_obs = np.full(10, self.min_lat_lon, dtype=np.float64)

        # Satellite iniziale
        cur_sat = self.sat_by_id[sat_id]
        first_obs[0] = self.cur_lat
        first_obs[1] = self.cur_lon

        neighbors = cur_sat["neighbors"]
        dirs = ["n", "s", "e", "w"]

        accepted_neighbors = []
        
        has_none = any(neighbors[d] == "None" for d in dirs) # Controllo se esiste almeno un vicino "None"
        if has_none: # Salvo gli altri vicini validi
            for d in dirs:
                n_id = neighbors[d]
                if n_id != "None":
                    accepted_neighbors.append(int(n_id))
        else:
            # Tutti i vicini sono validi: calcolo la distanza di ciascun vicino da end_id
            distances = [] # Ogni elemento (id_sat, dist_ad_end)

            for d in dirs:
                n_id = int(neighbors[d])
                dist = self.sat_distance(self.sat_by_id[n_id], self.sat_by_id[self.end_id])
                distances.append((n_id, dist))

            # Ordina i vicini in base alla distanza (cioè il valore 1 dell'elemento x in distances) dall'end (più vicino prima)
            distances.sort(key=lambda x: x[1])

            # Salva solo gli id ordinati dalle tuple in distances
            accepted_neighbors = [n_id for n_id, _ in distances]
       
        # Controllo se ho avuto più di un None iniziale faccio padding, inserendo dall'inizio, con sat migliore fino ad avere 3 sat
        if 0 < len(accepted_neighbors) < 3:
            best_neighbor = accepted_neighbors[0]
            while len(accepted_neighbors) < 3:
                accepted_neighbors.insert(0, best_neighbor)

        # Inserisce lat e lon dei 3 vicini accettati (i più vicini), valori first_obs[da 2 a 7]
        idx = 2
        for n_id in accepted_neighbors[:3]: 
            n_sat = self.sat_by_id[n_id]
            print ("SATELLITE VICINO ---", n_sat) # DEBUG first neighbors
            first_obs[idx] = n_sat["lat"]
            first_obs[idx + 1] = n_sat["lon"]
            idx += 2

        # Satellite finale
        first_obs[8] = self.end_lat
        first_obs[9] = self.end_lon

        return first_obs

    def sat_distance(self, sat1, sat2):
        """
        Calcola la distanza in km tra due satelliti usando il modello WGS84 con geopy

        """
        coord1 = (sat1['lat'], sat1['lon'])
        coord2 = (sat2['lat'], sat2['lon'])

        distance = geodesic(coord1, coord2).kilometers
        return distance