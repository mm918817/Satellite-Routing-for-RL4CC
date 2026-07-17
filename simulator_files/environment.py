import constants
from direction import Direction
import environment as env
from geopy import distance
from skyfield.api import Timescale
from strategy import Strategy
import utils

import json
from flux import Flux

satellites: dict
ground_stations: dict

class PriorityQueue:
    def __init__(self):
        self.queue = []

    def put(self, priority, function, **kwargs):
        self.queue.append((priority, function, kwargs))
        self.queue.sort(key=lambda p: p[0])

    def get(self):
        return self.queue.pop(0)
    
    def is_not_empty(self):
        return True if self.queue else False
    
    def clear(self):
        self.queue.clear()

actions_queue = PriorityQueue()
ready = False
elapsed_time = 0
control_traffic_data = 0 #Bytes

def put(time, function, **kwargs):
    env.actions_queue.put(time, function, **kwargs)

def prepare():
    if env.ready == True:
        raise RuntimeError("Environment is already prepared. Call prepare() kust once before start().")
    
    print("Preparing environment...")
    for i in range(0, constants.SIMULATION_DURATION, constants.TOPOLOGY_UPDATE_TIME):
        env.put(i, topology_builder)

    if constants.ROUTING_STRATEGY in [Strategy.POSITION_SHARING_NO_LB, 
                                      Strategy.POSITION_SHARING_LB_ON_SATURATED_LINK, 
                                      Strategy.POSITION_SHARING_PROGRESSIVE_LB,
                                      Strategy.POSITION_AND_LOAD_STATE_SHARING_ADAPTIVE_LB]:
        for sat in env.satellites.values():
            for i in range(0, constants.SIMULATION_DURATION, constants.SATELLITE_NEIGHBORS_UPDATE_TIME):
                env.put(i, update_satellites_position)
        for sat in env.satellites.values():
            for i in range(0, constants.SIMULATION_DURATION, constants.SATELLITE_NEIGHBORS_UPDATE_TIME):
                env.put(i, sat.update_neighbors)
        for sat in env.satellites.values():
            for i in range(0, constants.SIMULATION_DURATION, constants.SATELLITE_NEIGHBORS_UPDATE_TIME):
                env.put(i, sat._reroute_all)

    env.ready = True
    print("Simulation ready to run.")

def start():
    if env.ready == False:
        raise RuntimeError("Environment is not ready to start. Call prepare() before start().")
    
    print("Simulation started. Configuraton:")
    print("- Routing strategy:", constants.ROUTING_STRATEGY.name)
    print("- Simulation time:", utils.get_current_time().utc_strftime())
    print("- Duration:", constants.SIMULATION_DURATION, "seconds")
    print("- Total traffic in network:", constants.TOTAL_VOLUME_OF_TRAFFIC, "Mbps")
    print("- Involved ground stations:", len(env.ground_stations))
    print("- Topology update scheduled each", constants.TOPOLOGY_UPDATE_TIME, "seconds")
    if constants.ROUTING_STRATEGY in [Strategy.POSITION_SHARING_NO_LB,
                                      Strategy.POSITION_SHARING_LB_ON_SATURATED_LINK,
                                      Strategy.POSITION_SHARING_PROGRESSIVE_LB,
                                      Strategy.POSITION_AND_LOAD_STATE_SHARING_ADAPTIVE_LB]:
        print("- Satellite neighbors information update scheduled each", constants.SATELLITE_NEIGHBORS_UPDATE_TIME, "seconds")
    if constants.ROUTING_STRATEGY == Strategy.POSITION_AND_LOAD_STATE_SHARING_ADAPTIVE_LB:
        print("- Adaptive load balancing weight factor:", constants.LOAD_BALANCING_WEIGHT_FACTOR)
    
    while env.actions_queue.is_not_empty():
        time, action, kwargs = env.actions_queue.get()
        #print("time", time, "action", action) # Controllo delle azioni dalla coda per timestep
        if time != env.elapsed_time:

            # DEBUG Stampe di controllo dei vicini del satellite 100
            log_outgoing_fluxes_for_satellite(100)
            log_outgoing_fluxes_for_satellite(133)
            log_outgoing_fluxes_for_satellite(129)
            log_outgoing_fluxes_for_satellite(154)
            log_outgoing_fluxes_for_satellite(171)

            # Salva le posizioni e vicini aggiornati dei satelliti per questo topology update
            save_satellite_topology_during_simulation()

            # Salva coordinate gs ed a quale satellite sono collegate per questo topology update
            save_ground_station_connections()

            # Stampa le posizioni aggiornate dei satelliti per questo topology update
            log_satellite_positions_for_topology()
            
            # Stampa a quale satellite è collegata ogni GS attiva
            log_ground_station_connections()

            # Stampa flussi in uscita delle gs
            #log_gs_outgoing_fluxes()

            env.elapsed_time = time
            print("Simulating", time, "/", constants.SIMULATION_DURATION, "seconds")
        if kwargs:
            action(kwargs)
        else:
            action()

    print("Simulation ended.")

def reset():
    print("Resetting environment...")
    env.actions_queue.clear()
    env.elapsed_time = 0
    env.control_traffic_data = 0
    update_satellites_position()
    for satellite in env.satellites.values():
        satellite.remove_link(Direction.NORTH)
        satellite.remove_link(Direction.SOUTH)
        satellite.remove_link(Direction.EAST)
        satellite.remove_link(Direction.WEST)
        satellite.state = 0.0
    for gs in env.ground_stations.values():
        for flux, _, end_time in gs.outgoing_fluxes:
            if end_time == None:
                gs.close_outgoing_flux(flux)
        gs.outgoing_fluxes.clear()
        gs.incoming_fluxes.clear()
        gs.DEBUG_dropped_incoming_fluxes.clear()    
    env.ready = False
    print("Environment reset.")

def update_satellites_position():
    for sat in env.satellites.values():
        sat._update_position()
        sat._update_gs_link()
    for gs in env.ground_stations.values():
        gs.reattach()

def topology_builder():
    update_satellites_position()
    temp_satellites = {}
    for key, sat in env.satellites.items():
        temp_satellites[key] = [sat.get_latitude(), 
                                sat.get_longitude(), 
                                None, #Northern link
                                None, #Southern link
                                None, #Eastern link
                                None] #Western link
    
    distances = list()
    for key, sat in temp_satellites.items():
        if sat[0] > constants.LATITUDE_CUTOFF or sat[0] < -constants.LATITUDE_CUTOFF:
            sat[2] = None
            sat[3] = None
            sat[4] = None
            sat[5] = None
            continue
        for key_link, sat_link in temp_satellites.items():
            if key == key_link:
                continue
            if sat_link[0] > constants.LATITUDE_CUTOFF or sat_link[0] < -constants.LATITUDE_CUTOFF:
                continue
            dist = distance.distance((sat_link[0], sat_link[1]), (sat[0], sat[1])).km
            if dist > 5100:
                continue
            distances.append({'distance': dist, 'sat1': key, 'sat2': key_link})
    distances.sort(key=lambda x: x['distance'])
    
    for dist in distances:
        key = dist['sat1']
        sat_key = dist['sat2']
        sat = temp_satellites.get(key)
        sat_link = temp_satellites.get(sat_key)

        if sat_key in sat[2:6]: # Se sat è già presente per un link, passa al prossimo
            continue

        # --- Gestione dei link tra satelliti ---

        # Valutazione fatta tra due satelliti vicini, "sat" e "sat_link"

        # PRIMA veniva fatto un primo controllo Nord/sud con valori fissi
        # Poi un secondo controllo per l'Est e poi un altro controllo per l'Ovest
        # Probabilmente per i valori fissi e per come si avvicinano i meridiani ai poli sbagliava quale controllo fare 
        # assegnando in certi casi dei sat al link sbagliato


        # Logica Nord/Sud (Intra-plane)
        # Verifica che se la differenza di longitudine è meno di 7 gradi
        # Con anche il caso se le due longitudini sono vicino alla linea di cambio data
        # e la loro somma supera i 353 su 360 (360-7)
        if (abs(sat[1] - sat_link[1]) < 7 or 
            abs(sat[1] - sat_link[1]) > 353):
            
            # Controlla latitudine per capire chi è sotto o sopra e se lo slot è libero
            if sat[0] < sat_link[0] and sat[2] is None and sat_link[3] is None:
                sat[2] = sat_key
                sat_link[3] = key
            elif sat[0] > sat_link[0] and sat[3] is None and sat_link[2] is None:
                sat[3] = sat_key
                sat_link[2] = key
        
        # Logica Est/Ovest (Inter-plane)
        else:
            # Calcola la differenza di longitudine normalizzando per via della linea di cambio data
            # eg. lat sat=170, lat sat_link=-170 (sono vicini longitudinalmente), -340<-180, quindi +360 si ottiene 20
            # Stessa cosa avessi sat=-170 e sat_link=170 applicava -360
            diff_lon = sat_link[1] - sat[1]
            if diff_lon > 180: diff_lon -= 360
            if diff_lon < -180: diff_lon += 360

            # Se diff_lon > 0, sat_link è ad EST di sat
            if diff_lon > 0 and sat[4] is None and sat_link[5] is None:
                sat[4] = sat_key
                sat_link[5] = key
            # Se diff_lon < 0, sat_link è ad OVEST di sat
            elif diff_lon < 0 and sat[5] is None and sat_link[4] is None:
                sat[5] = sat_key
                sat_link[4] = key

    if constants.DEBUG:
        print("Linking phase completed. Applying...")

    for key, sat in temp_satellites.items():
        satellite = env.satellites.get(key)
        north_link = env.satellites.get(sat[2])
        south_link = env.satellites.get(sat[3])
        east_link = env.satellites.get(sat[4])
        west_link = env.satellites.get(sat[5])
        satellite.add_link(north_link, Direction.NORTH) if north_link != None else satellite.remove_link(Direction.NORTH)
        satellite.add_link(south_link, Direction.SOUTH) if south_link != None else satellite.remove_link(Direction.SOUTH)
        satellite.add_link(east_link, Direction.EAST) if east_link != None else satellite.remove_link(Direction.EAST)
        satellite.add_link(west_link, Direction.WEST) if west_link != None else satellite.remove_link(Direction.WEST)

    if constants.DEBUG:
        print("Applied.")

def log_control_traffic_message(bytes: int):
    env.control_traffic_data += bytes


def log_ground_station_connections():
    """
    Stampa le ground station attive ed a quale satellite sono collegate
    per ogni Topology Update.
    """
    print(f"\n Ground Station connections at t={env.elapsed_time}s")
    print("-----------------------------------------------------------------------")

    for gs_name, gs in sorted(env.ground_stations.items()):
        if hasattr(gs, "sat") and gs.sat:
            sat = str(gs.sat.get_name())
            gs_lat, gs_lon = gs.lat, gs.lon

            print(f"GS {gs_name:15s}:  lat = {gs_lat:8.3f}°,   lon = {gs_lon:8.3f}°, Connessa a: Sat {sat:^4s}")

        else:
            print(f"GS {gs_name:15s}:  lat = {gs_lat:8.3f}°,   lon = {gs_lon:8.3f}°, Nessuna connessione attiva")

    print("-----------------------------------------------------------------------\n")

 
def log_satellite_positions_for_topology():
    """
    Stampa la posizione (latitudine e longitudine) ed i vicini (neighbors) aggiornati di tutti i satelliti
    una volta per ogni Topology Update.
    """
    print(f"\n TOPOLOGY UPDATE at t={env.elapsed_time}s")
    print("-----------------------------------------------------------------------------------------------------")
    for sat_id, sat in sorted(env.satellites.items()):
        lat = sat.get_latitude()
        lon = sat.get_longitude()
             
        # Recupera i nomi dei satelliti tramite il "target" per ogni link di un satellite
        n = str(sat._links[Direction.NORTH].target.get_name()) if sat._links[Direction.NORTH].target else "None"
        s = str(sat._links[Direction.SOUTH].target.get_name()) if sat._links[Direction.SOUTH].target else "None"
        e = str(sat._links[Direction.EAST].target.get_name()) if sat._links[Direction.EAST].target else "None"
        w = str(sat._links[Direction.WEST].target.get_name()) if sat._links[Direction.WEST].target else "None"

        print(f"Sat {sat_id:03d}:  lat = {lat:8.3f}°,   lon = {lon:8.3f}°, | Links:  n = {n:^4s},   s = {s:^4s},   e = {e:^4s},   w = {w:^4s}")

    print("-----------------------------------------------------------------------------------------------------\n")


from direction import Direction

def log_outgoing_fluxes_for_satellite(sat_id: int):
    """
    Stampa i flussi in uscita per il satellite sat_id durante un Topology Update
    sia da "Fluxes" che per ciascun link: N, S, E, W.
    Per ogni flusso mostra

       - direzione di arrivo (N,S,E,W)
       - alias_id
       - id originale
       - rate (Mbps)
       - ttl residuo
       - stato
       - destinazione (lat,lon)
    """
    if sat_id not in env.satellites:
        print(f"Satellite {sat_id} non esiste.")
        return
    
    sat = env.satellites[sat_id]
    
    print(f"\n Fluxes(Flows) from Satellite {sat_id} at t={env.elapsed_time}s")
    print("-------------------------------------------------------------------------------")

    directions = {
        "N": Direction.NORTH,
        "S": Direction.SOUTH,
        "E": Direction.EAST,
        "W": Direction.WEST
    }

    # Sezione aggiuntiva per stampare anche i .fluxes per ogni satellite sat_id
    # Controllo aggiuntivo che stampa pure se il link è Laser o Radio (evita direttamente i "None")
    for num, tuple in sat.fluxes.items():
        if (tuple[1] == None):
            print(
                f"alias id: {num},  "
                f" id: {tuple[0].id}, " 
                f" link: {tuple[1]} " 
            )
        else:
            print(
                f"alias id: {num},  "
                f" id: {tuple[0].id}, "
                #f" link parent state: {tuple[1]._parent.state}, "
                f" flux state: {tuple[0].state},  "
                f" capacity: {tuple[1].capacity}, " 

                f" tipolink: {tuple[1]}."
            )

    found_any = False

    # Per ogni direzione controlla se ci sono flussi attivi
    for label, d in directions.items():
        link = sat._links[d]
        #if link is None or not link.is_active():
        #    continue

        for alias_id, flux in link.fluxes.items():
            found_any = True
            print(
                f"From {label}:  "
                f"Flow alias={alias_id}, "
                f"id={flux.id}, "
                f"rate={flux.rate} Mbps "
                f"on {link.capacity} Mbps, "
                f"ttl={flux.ttl}, "
                f"state={flux.state}, "
                f"destination=({flux.destination[0]:.2f},{flux.destination[1]:.2f})"
            )

    if not found_any:
        print("Nessun flusso in uscita.")
    
    print("-------------------------------------------------------------------------------\n")

if not hasattr(env, "flux_log"):
    env.flux_log = {}           # dict[int timestep] = list of events
    env.flux_log_file = "flux_timeline.json" 


def log_gs_outgoing_fluxes():
    print("fluxes fo the ground stations -----")
    for gs_name, gs in sorted(env.ground_stations.items()):
        print("gs:",gs_name)

        for flux, start_time, end_time in gs.outgoing_fluxes:
            # Qui, hai accesso diretto a ciascun elemento per nome
            print(f"Flusso: {flux.id}")
            print(f"Inizio Invio: {start_time}")
            print(f"Fine Invio: {end_time}")


def save_satellite_topology_during_simulation(filename: str = f"satellite_topology{constants.SIMULATION_DURATION}.json"):
    """
    Registra e salva in un file JSON le posizioni aggiornate di tutti i satelliti
    ed i loro vicini ad ogni Topology Update durante la simulazione.

    La funzione accumula le posizioni e vicini nel file ogni volta che topology_builder() viene eseguito.
    """
    # Se è la prima chiamata, inizializza la struttura globale
    if not hasattr(env, "_satellite_topology_log"):
        env._satellite_topology_log = []
        env._satellite_position_filename = filename
        print(f"\n Salvataggio topologia dei satelliti in '{filename}'")

    # Crea uno snapshot per l’istante corrente
    satellites_neighbors = []
    
    for sat_id, sat in sorted(env.satellites.items()):
        # Recupera l'ID del satellite collegato (target) per ogni link.
        # Se il link non è stabilito (None), salva "None".
        n_target = sat._links[Direction.NORTH].target.get_name() if sat._links[Direction.NORTH].target else "None"
        s_target = sat._links[Direction.SOUTH].target.get_name() if sat._links[Direction.SOUTH].target else "None"
        e_target = sat._links[Direction.EAST].target.get_name() if sat._links[Direction.EAST].target else "None"
        w_target = sat._links[Direction.WEST].target.get_name() if sat._links[Direction.WEST].target else "None"
        
        # Struttura dati per un singolo satellite (ID, latitudine, longitudine e i suoi vicini)
        satellite_data = {
            "id": sat_id,
            "lat": sat.get_latitude(),
            "lon": sat.get_longitude(),
            "neighbors": {
                "n": n_target,
                "s": s_target,
                "e": e_target,
                "w": w_target
            }
        }
        satellites_neighbors.append(satellite_data)

    snapshot = {
        "time": env.elapsed_time,
        "satellites": satellites_neighbors
    }

    # Aggiunge lo snapshot al log in memoria
    env._satellite_topology_log.append(snapshot)

    # Sovrascrive il file JSON progressivamente 
    with open(env._satellite_position_filename, "w", encoding="utf-8") as f:
        json.dump(env._satellite_topology_log, f, indent=2)

    print(f" --- Salvato posizioni e vicini dei satelliti al topology update t={env.elapsed_time}s "
          f"({len(snapshot['satellites'])} satelliti)")


def save_ground_station_connections(filename: str = "ground_station_connections.json"):
    """
    Registra e salva in un file JSON le coordinate delle ground station
    ed ad ogni Topology Update le connessioni con il satellite più vicino.
    """
    
    # Inizializzazione della struttura globale
    if not hasattr(env, "_gs_log"):
        env._gs_log = {
            "gs_coordinates": {},
            "temporal_connections": []      
        }
        env._gs_filename = filename
        print(f"\n Salvataggio connessioni GS in '{filename}'")

    # Se è la prima chiamata popola i dati statici
    if not env._gs_log["gs_coordinates"]:
        for gs_name, gs in env.ground_stations.items():
            env._gs_log["gs_coordinates"][gs_name] = {
                "lat": gs.lat,
                "lon": gs.lon
            }

    # Creazione dello snapshot per l'istante corrente
    current_connections = []
    
    for gs_name, gs in sorted(env.ground_stations.items()):
        sat_connected = None
        
        if hasattr(gs, "sat") and gs.sat:
            sat_connected = gs.sat.get_name()
            
        # Struttura dati con nome ed id satellite
        gs_connection_data = {
            "name": gs_name,
            "connected_sat_id": sat_connected
        }
        current_connections.append(gs_connection_data)

    # Struttura del log per l'attuale istante temporale
    snapshot = {
        "time": env.elapsed_time,
        "connections": current_connections
    }

    # Aggiunge lo snapshot al log in memoria
    env._gs_log["temporal_connections"].append(snapshot)

    # Sovrascrive il file JSON progressivamente
    with open(env._gs_filename, "w", encoding="utf-8") as f:
        json.dump(env._gs_log, f, indent=2)
            
    print(f" --- Salvato connessioni GS al t={env.elapsed_time}s")


def save_flux_event_timestep(sat_id: int, flux: Flux):
    """
    Salva in un json le informazioni sui flussi "in arrivo" divisi per Topology Update
    cioè:
        - id satellite su cui arriva
        - id del flusso
        - alias_id del flusso in arrivo
        - rate del traffico occupato dal flusso
        - time to live
        - coordinate destinazione
        - distanza percorsa dal flusso
        - lista degli "step" (satelliti)
    """
    t = env.elapsed_time

    # Prima volta per creare l'array
    if t not in env.flux_log:
        env.flux_log[t] = []

    # Se si vuole direttamente il nome della gs alla destination
    #for gs in ground_stations.values():
    #    if (gs.lat == flux.destination[0] and gs.lon == flux.destination[1]):
    #        flux_gs_name = gs.name 

    env.flux_log[t].append({
        "satellite": sat_id,
        "id": flux.id,
        "alias_id": flux.alias_id,
        "rate": flux.rate, #Mbps ,(supponendo di avere pacchetti da 2Kb fare *1000 /2 ) 
        "ttl": flux.ttl,
        "destination": list(flux.destination),
        "travelled_distance": flux.travelled_distance, #km
        "steps": [s.get_name() for s in flux.steps]
         
    })

    # Salva su JSON incrementale
    with open(env.flux_log_file, "w", encoding="utf-8") as f:
        json.dump(env.flux_log, f, indent=2)

if not hasattr(env, "flux_packet_log"):
    env.flux_packet_log = []          # lista di flussi
    last_timestamp = constants.SIMULATION_DURATION - constants.TOPOLOGY_UPDATE_TIME
    env.flux_packet_log_file = f"flows_src__dst_timeline{constants.SIMULATION_DURATION}.json"

def save_src_dst_timestep(sat_id: int, flux: Flux):
    """
    Salva in un json le informazioni sui flussi ()
    cioè:
        - id del flusso
        - id satellite sorgente
        - id satellite destinazione
        - t dell'istante temporale
    """
    t = env.elapsed_time

    if any(e["id"] == flux.id and e["time"] == t for e in env.flux_packet_log):
        return

    sat_connected = None

    for gs in env.ground_stations.values():
        if (gs.lat == flux.destination[0] and gs.lon == flux.destination[1]):
        
            if hasattr(gs, "sat") and gs.sat:
                sat_connected = gs.sat.get_name()
            break

    # Evita di salvare un evento in cui start == end
    if (sat_connected is not None and sat_id == sat_connected):
        return 
    
    env.flux_packet_log.append({
        "id": flux.id,
        "start_id": sat_id,
        # "alias_id": flux.alias_id, #DEBUG
        "end_id": sat_connected,
        # "destination": list(flux.destination), #DEBUG
        "time": t,   
    })

    # Salva su JSON incrementale
    with open(env.flux_packet_log_file, "w", encoding="utf-8") as f:
        json.dump(env.flux_packet_log, f, indent=2)
