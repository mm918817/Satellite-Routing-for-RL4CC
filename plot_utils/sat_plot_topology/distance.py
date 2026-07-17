from geopy.distance import geodesic
import time

def distanza_tra_satelliti_geopy(sat1, sat2):
    """
    Calcola la distanza in km tra due satelliti usando il modello WGS84 con geopy:

    Args:
        sat1 (dict): satellite 1 con chiavi 'lat' e 'lon'
        sat2 (dict): satellite 2 con chiavi 'lat' e 'lon'
    
    Returns:
        float: distanza in chilometri
    """
    coord1 = (sat1['lat'], sat1['lon'])
    coord2 = (sat2['lat'], sat2['lon'])
    
    # Calcola la distanza geodetica WGS84
    distanza = geodesic(coord1, coord2).kilometers
    return distanza

# Esempio con il formato file flows, modificare valori lat e lon per testare la distanze tra i satelliti di interesse
satellite1 = {
        "id": 100,
        "lat": -7.96404708782039,
        "lon": -129.6134719871254,
        "neighbors": {
          "n": 133,
          "s": 129,
          "e": 154,
          "w": 171
        }
      }

satellite2 =       {
        "id": 102,
        "lat": 21.594519514297964,
        "lon": 114.56251779560228,
        "neighbors": {
          "n": 111,
          "s": 112,
          "e": 146,
          "w": 160
        }
      }

print(f"Distance between satellites(WGS84):  {distanza_tra_satelliti_geopy(satellite1, satellite2):.3f} km")
time.sleep(5)