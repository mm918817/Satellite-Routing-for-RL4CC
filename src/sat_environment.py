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

        # Caricamento file JSON dai file di config
        with open(env_config["flows_file"], "r") as f:
            self.flows = json.load(f)

        with open(env_config["topology_file"], "r") as f:
            self.topologies = json.load(f)

        # Peso per regolare reward step intermedio
        self.w_step = env_config["step_weight"]
        print("parametro reward per step è", self.w_step)

        # Peso per regolare reward raggiunta la destinazione
        self.w_dest = env_config["dest_weight"]
        print("parametro reward raggiunta destinazione è", self.w_dest)
        
        # Lookup topologie per time per accesso veloce
        self.topo_by_time = {t["time"]: t for t in self.topologies}

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

        # Random flow
        self.current_flow = np.random.choice(self.flows)
        self.start_id = self.current_flow["start_id"]
        self.end_id = self.current_flow["end_id"]
        flow_time = self.current_flow["time"]
        print("FLOW:", self.current_flow) # DEBUG flow

        # Topologia associata al time
        self.topology = self.topo_by_time[flow_time]

        # Lookup per i satelliti dell'attuale topologia
        self.sat_by_id = {
            sat["id"]: sat for sat in self.topology["satellites"]
        }

        # Lookup per ottenere un satellite date le coordinate 
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
        # Aggiorno i variabili lat e lon dei vicini per l'osservazione
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

        self.current_time += self.time_step # update time
        s_obs, s_info = self.observation()
        print(" -- ACTION selected:", action) # DEBUG action
        idx = 2 + (action * 2)
        act_lat = s_obs[idx]
        act_lon = s_obs[idx+1]
        print(" -- LAT selected by action:", act_lat) # DEBUG lat

        if act_lat < -189.0 and act_lon < -189.0 : # Vicino non valido, agente sta fermo e non fa nulla
            self.last_reward = -1 # update reward
            self.hole_counter += 1
            done = False
            truncated = (self.current_time >= self.max_time)
            if truncated:
                print(" OOO Timeout OOO ")
            print("reward None", self.last_reward) # DEBUG reward            
            return s_obs, self.last_reward, done, truncated, s_info

        # Aggiorna i valori che verranno usati dalla nuova osservazione
        self.cur_lat = act_lat
        self.cur_lon = act_lon
        
        self.previous_sat = self.current_sat
        self.current_sat = self.sat_by_coords[(self.cur_lat, self.cur_lon)]
        cur_info = self.sat_by_id[self.current_sat]

        new_neighbors = cur_info["neighbors"]
        dirs = ["n", "s", "e", "w"]

        filtered_neighbors = [] # Rimuove satellite da cui sono arrivato
        for d in dirs:
            n_id = new_neighbors[d]
            if n_id == "None":
                filtered_neighbors.append("None")
            else:
                n_id = int(n_id)
                if n_id != self.previous_sat:
                    filtered_neighbors.append(n_id)

        while len(filtered_neighbors) < 3: # Controllo per quando ho 2 volte lo stesso vicino, ed ho solo 2 valori in filtered_neighbors
            filtered_neighbors.append("None")

        lat_lon_values = [] # Recupera lat e lon dei nuovi vicini ed aggiorna i valori dell'osservazione
        for n_id in filtered_neighbors:
            if n_id == "None":
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

        done = (self.current_sat == self.end_id)
        truncated = (self.current_time >= self.max_time)
        if done:
            print(" ooo episodio completato con successo ooo")
        if truncated:
            print(" ooo Timeout ooo")

        obs, info = self.observation()

        return obs, reward, done, truncated, info


    def compute_reward(self):
        """
        Reward:
        - Se current_sat è l'end_id ->  dist_start_end / self.dist_tot  (reward se arrivo destinazione)
        - Altrimenti -> 1 - [(d(current, end) - d(near, end)) / (d(far, end) - d(near, end))] (reward per step)
        """
        # Aggiorna distanza totale percorsa
        end_sat = self.sat_by_id[self.end_id]
        self.dist_jump = self.sat_distance(self.sat_by_id[self.previous_sat], self.sat_by_id[self.current_sat])
        self.dist_tot += self.dist_jump

        if self.current_sat == self.end_id: # Se ho raggiunto la destinazione
            start_sat = self.sat_by_id[self.start_id]
            dist_start_end = self.sat_distance(start_sat, end_sat)
            if self.dist_tot == 0:
                return 1.0  # caso limite
            reward = (dist_start_end / self.dist_tot)*self.w_dest
            print("reward raggiunta destinazione", reward) # DEBUG reward            
            return reward

    
        # Vicini del previous_sat
        neighbors = self.sat_by_id[self.previous_sat]["neighbors"]

        # Converte in interi o None
        neighbor_ids = []
        for d in ["n", "s", "e", "w"]:
            n = neighbors[d]
            if n != "None":
                neighbor_ids.append(int(n))
        if not neighbor_ids:
            return -0.01  # fallback se non ci sono vicini validi, dovrebbe tenere almeno il satellite da cui arriviamo e quello in cui siamo arrivati

        # Calcola le distanze rispetto a end_id
        distances = {nid: self.sat_distance(self.sat_by_id[nid], end_sat) for nid in neighbor_ids}

        # Trova id satellite più vicino e più lontano
        near_sat_id = min(distances, key=distances.get) # chiave in distances che ha il valore associato minimo
        far_sat_id = max(distances, key=distances.get) # chiave in distances che ha il valore associato massimo 

        d_current = self.sat_distance(self.sat_by_id[self.current_sat], end_sat)
        d_near = distances[near_sat_id]
        d_far = distances[far_sat_id]

        # Evita divisione per zero
        if d_far == d_near:
            print ("- d_far uguale a d_near", d_far, d_near) # DEBUG reward
            return 0.0 

        reward = (1 - (d_current - d_near) / (d_far - d_near))*self.w_step
        print ("reward step è", reward) # DEBUG reward
        return reward

    def compute_first_neighbors(self, sat_id):
        """
        Crea un'osservazione iniziale, con i vicini validi scelti in base ai criteri:
        -Se per il sat iniziale ho un satellite vicino "None" lo scarto e tengo gli altri vicini
        -Altrimenti dei satelliti vicini ordino in base alla distanza da quello finale e scarto il più lontano

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

        # Inserisce lat e lon dei 3 vicini accettati
        idx = 2
        for n_id in accepted_neighbors[:3]: 
            n_sat = self.sat_by_id[n_id]
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