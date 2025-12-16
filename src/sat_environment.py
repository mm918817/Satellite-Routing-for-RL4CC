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

        # Lookup topologie per time per accesso veloce
        self.topo_by_time = {t["time"]: t for t in self.topologies}

        return None  # seed, nel base_environment questa funzione restituisce un seed da passare al reset


    def define_observation_space(self):
        """
        Osservazione semplice con satellite corrente e satellite finale
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
        Se un vicino è "None" si sostituisce con il satellite precedente,
        Se si hanno tutti vicini possibili si scarta quello da cui si è arrivati
        (selezione azioni fatta in compute_valid_moves)
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
            "reward": self.last_reward,
            "current_sat": self.current_sat
        }

        return obs, info
    

    def reset(self, seed=None, options=None):
        """
        Sceglie un flow random dal json ed inizializza i valori associati per l'inizio dell'episodio
        Recupera la topologia associata al flow e crea una mappa con i satelliti presenti al suo interno
        Inizializza id satellite corrente, il satellite precedente (usato per filtrare i vicini al primo step), il reward e la distanza totale
        """       
       # Inizializza gli attributi prima di super
        self.current_sat = 0
        self.previous_sat = None
        self.start_id =0
        self.end_id = 0
        self.dist_tot = 0.0
        self.last_reward = 0.0

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

        self.current_sat = self.start_id
        self.previous_sat = None

        self.cur_lat = self.sat_by_id[self.current_sat]["lat"]
        self.cur_lon = self.sat_by_id[self.current_sat]["lon"]
        self.end_lat = self.sat_by_id[self.end_id]["lat"]
        self.end_lon = self.sat_by_id[self.end_id]["lon"]

        # reward iniziale = 0 , usato in observation
        self.last_reward = 0.0

        # distanza totale accumulata
        self.dist_tot = 0.0

        f_obs = self.compute_first_neighbors(self.current_sat)
        # Aggiorno i variabili lat e lon dei vicini per l'osservazione
        self.lat1 = f_obs[2]
        self.lon1 = f_obs[3]
        self.lat2 = f_obs[4]
        self.lon2 = f_obs[5]
        self.lat3 = f_obs[6]
        self.lon3 = f_obs[7]
        obs, info = self.observation()


        return f_obs, info


    def step(self, action):
        """
        Seleziona i vicini del satellite attuale e prende un'azione tra quelle disponibili
        Aggiorna gli stati dopo lo step e salva il reward
        """

        sat_info = self.sat_by_id[self.current_sat]
        neighbors = sat_info["neighbors"]

        valid_next = self.compute_valid_moves(neighbors)
        next_sat = valid_next[action]

        # update state
        self.previous_sat = self.current_sat
        self.current_sat = next_sat
        self.current_time += self.time_step

        # reward
        reward = self.compute_reward()
        self.last_reward = reward

        done = (next_sat == self.end_id)
        truncated = (self.current_time >= self.max_time) # con truncated = done # agente impara a finire il tempo?

        obs, info = self.observation()

        return obs, reward, done, truncated, info


    def compute_reward(self):
        """
        Reward:
        - Se current_sat è l'end_id ->  dist_start_end / self.dist_tot
        - Altrimenti -> 1 - [(d(current, end) - d(near, end)) / (d(far, end) - d(near, end))]
        """

        if self.previous_sat is None:
            return 0 # Se non c'è previous, sono all'inizio

        # Aggiorna distanza totale percorsa
        end_sat = self.sat_by_id[self.end_id]
        self.dist_tot += self.sat_distance(self.sat_by_id[self.previous_sat], self.sat_by_id[self.current_sat])

        if self.current_sat == self.end_id: # Se ho raggiunto la destinazione
            start_sat = self.sat_by_id[self.start_id]
            dist_start_end = self.sat_distance(start_sat, end_sat)
            if self.dist_tot == 0:
                return 1.0  # caso limite
            return dist_start_end / self.dist_tot
    
        # Vicini del previous_sat
        neighbors = self.sat_by_id[self.previous_sat]["neighbors"]

        # Converte in interi o None
        neighbor_ids = []
        for d in ["n", "s", "e", "w"]:
            n = neighbors[d]
            if n != "None":
                neighbor_ids.append(int(n))
        if not neighbor_ids:
            return -0.01  # fallback se non ci sono vicini validi, dovrebbe tenere almeno il satellite da cui arriviamo e quello in cui siamo

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
            return 0.0

        reward = 1 - (d_current - d_near) / (d_far - d_near)
        return reward

    def compute_first_neighbors(self, sat_id):
        """
        Crea un'osservazione iniziale, con i vicini validi scelti in base ai criteri:
        -Se per il sat iniziale ho un satellite vicino "None" lo scarto e tengo gli altri vicini
        -Altrimenti dei satelliti vicini scarto: la direzione n se sono sopra/sull'equatore oppure scarto direzione s se sono sotto l'equatore

        [cur_lat, cur_lon,
        lat1, lon1,
        lat2, lon2,
        lat3, lon3,
        end_lat, end_lon]
        """
        first_obs = np.full(10, self.min_lat_lon)

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
            # Tutti i vicini sono validi:
            for d in dirs:
                accepted_neighbors.append(int(neighbors[d]))

            # Regola su latitudine dove scarto la direzione n se sono sopra/sull'equatore e scarto direzione s se sono sotto l'equatore
            if self.cur_lat >= 0:
                # scarta nord (usa la posizione di "n" in dirs per scartare il valore corrispondente in accepted_neighbors)
                accepted_neighbors.pop(dirs.index("n"))
            else:
                accepted_neighbors.pop(dirs.index("s")) # scarta sud

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

    def compute_valid_moves(self, neighbors):
        """
        Creazione dei valori possibili per i vicini:
        Se tutti sono possibili si scarta il sat precedente
        Altrimenti se c'è un "None" si ha sat precedente come opzione
        """

        dirs = ["n", "s", "e", "w"]

        has_none = any(neighbors[d] == "None" for d in dirs) # Controlla se ci sono dei vicini con "None"

        valid_next = []

        for d in dirs:
            nxt = neighbors[d]

            if nxt == "None":
                if self.previous_sat is not None: # Evita di aggiungere il None del primo step
                    valid_next.append(self.previous_sat)

            else:
                nxt = int(nxt)
                valid_next.insert(0, nxt)

        # Se non c'è nessun "None", allora il nodo ha 4 vicini effettivi
        # Quindi si elimina il nodo da cui sei arrivato
        if not has_none and self.previous_sat is not None:
            valid_next = [s for s in valid_next if s != self.previous_sat]

        # Garantisce che ci siano 3 mosse
        while len(valid_next) < 3:
            valid_next.append(self.previous_sat)

        return valid_next[:3] # Tiene solo i primi 3
    

    def sat_distance(self, sat1, sat2):
        """
        Calcola la distanza in km tra due satelliti usando il modello WGS84 con geopy

        """
        coord1 = (sat1['lat'], sat1['lon'])
        coord2 = (sat2['lat'], sat2['lon'])

        distance = geodesic(coord1, coord2).kilometers
        return distance