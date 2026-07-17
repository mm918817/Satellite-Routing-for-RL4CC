import os
import json
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from datetime import datetime

# ----------------- CONFIG -----------------

# Lightly moves the markers of missing links to distinguish them
NEIGHBOR_OFFSETS = {
    "n": (1.2, 0.0),
    "s": (-1.2, 0.0),
    "e": (0.0, 1.2),
    "w": (0.0, -1.2),
}

DIR_MARKER = {
    "n": "^",
    "s": "v",
    "e": ">",
    "w": "<",
}

NORMAL_LINK_COLOR = "limegreen"
DUPLICATE_LINK_COLOR = "orange"
DATELINE_LINK_COLOR = "purple"
MISSING_LINK_COLOR = "deepskyblue"

Ground_stations = {
    "TOKYO": {"lat": 35.689506, "lon": 139.6917},
    "NEW YORK": {"lat": 40.71277778, "lon": -74.00611111},
    "DAR ES SALAAM": {"lat": -6.816111, "lon": 39.280278},
    "SAN FRANCISCO": {"lat": 37.7775, "lon": -122.41638889},
}

# ----------------- UTILS -----------------

def crosses_dateline(lon1, lon2):
    return abs(lon1 - lon2) > 180
# Calculate the absolute value of the longitude difference 
# If the horizontal distance is > 180 degrees it means that the shortest route passes through the International Date Line (IDL)

# ----------------- PLOT -----------------

def plot_topology(topology, flow_time, output_dir):

    sats = topology["satellites"]
    sat_by_id = {sat["id"]: sat for sat in sats}

    lats = [sat["lat"] for sat in sats]
    lons = [sat["lon"] for sat in sats]
    ids  = [sat["id"]  for sat in sats]

    # Satellite is blue if fully isolated
    colors = []
    for sat in sats:
        neighbors = sat.get("neighbors", {})
        if all(neighbors.get(d) == "None" for d in ["n", "s", "e", "w"]):
            colors.append("blue")
        else:
            colors.append("red")

    print(f" - Number of satellites: {len(ids)}")

    # ---- Draws the map ----
    fig = plt.figure(figsize=(12, 6))
    # Various map format
    #ax = plt.axes(projection=ccrs.Mercator())

    #ax = plt.axes(projection=ccrs.Mollweide())
    ax = plt.axes(projection=ccrs.Robinson())
    #ax = plt.axes(projection=ccrs.Orthographic(central_longitude=-180, central_latitude=0)) # For view near a specified point

    ax.set_global()
    ax.add_feature(cfeature.LAND)
    ax.add_feature(cfeature.OCEAN)
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle=":")

    # ---- Draws the satellites ----
    ax.scatter(
        lons, lats,
        color=colors,
        s=15,
        transform=ccrs.PlateCarree(),
        zorder=3
    )

    for lon, lat, sid in zip(lons, lats, ids):
        ax.text( # Satellites id
            lon, lat, str(sid),
            fontsize=6,
            transform=ccrs.PlateCarree(),
            zorder=4
        )

    # ---- Links and missing neighbors ----
    drawn_links = set() # Avoid duplicates

    for sat in sats:
        lat = sat["lat"]
        lon = sat["lon"]
        sat_id = sat["id"]
        neighbors = sat.get("neighbors", {})

        # Skip fully isolated satellites
        if all(neighbors.get(d) == "None" for d in ["n", "s", "e", "w"]):
            continue

        # Detect duplicate neighbors
        neighbor_ids = [
            nid for nid in neighbors.values() if nid != "None"
        ]
        duplicate_neighbors = {
            nid for nid in neighbor_ids if neighbor_ids.count(nid) > 1
        }

        for direction, (dlat, dlon) in NEIGHBOR_OFFSETS.items():
            neighbor_id = neighbors.get(direction)

            # Missing link marker
            if neighbor_id == "None":
                ax.scatter(
                    lon + dlon,
                    lat + dlat,
                    color=MISSING_LINK_COLOR,
                    s=6,
                    marker=DIR_MARKER[direction],
                    transform=ccrs.PlateCarree(),
                    zorder=5
                )
                continue

            if neighbor_id not in sat_by_id:
                continue

            # Avoid duplicate A<->B lines
            link_key = tuple(sorted((sat_id, neighbor_id)))
            if link_key in drawn_links:
                continue
            drawn_links.add(link_key)

            neigh = sat_by_id[neighbor_id]

            # ---- Choose link color ----
            if neighbor_id in duplicate_neighbors:
                color = DUPLICATE_LINK_COLOR
            elif crosses_dateline(lon, neigh["lon"]):
                color = DATELINE_LINK_COLOR
            else:
                color = NORMAL_LINK_COLOR

            ax.plot(
                [lon, neigh["lon"]],
                [lat, neigh["lat"]],
                color=color,
                linewidth=1.4,
                alpha=0.7,
                transform=ccrs.PlateCarree(),
                zorder=2
            )

    # ---- Ground stations ----
    gs_lats = [v["lat"] for v in Ground_stations.values()]
    gs_lons = [v["lon"] for v in Ground_stations.values()]
    gs_names = list(Ground_stations.keys())

    ax.scatter(
        gs_lons,
        gs_lats,
        color="green",
        s=40,
        marker="^",
        transform=ccrs.PlateCarree(),
        zorder=6
    )

    for lon, lat, name in zip(gs_lons, gs_lats, gs_names):
        ax.text(
            lon, lat, name,
            fontsize=7,
            fontweight="bold",
            transform=ccrs.PlateCarree(),
            ha="left",
            va="bottom",
            zorder=7
        )

    plt.title(f"Satellite topology at time {flow_time}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{flow_time:04d}_topology_{timestamp}.png"
    output_path = os.path.join(output_dir, filename)

    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {output_path}")

# ----------------- MAIN -----------------

topology_path = "satellite_topology.json"
choice = input('Select topology time or type "full" to save all: ').strip()

script_dir = os.path.dirname(os.path.abspath(__file__))

try:
    with open(topology_path, "r") as f:
        topologies = json.load(f)

    topo_by_time = {t["time"]: t for t in topologies}

    if choice.lower() == "full":
        output_dir = os.path.join(script_dir, "plots_full")
        os.makedirs(output_dir, exist_ok=True)

        for t in topologies:
            plot_topology(t, t["time"], output_dir)

    else:
        flow_time = int(choice)
        if flow_time not in topo_by_time:
            raise KeyError

        output_dir = os.path.join(script_dir, "plots_single")
        os.makedirs(output_dir, exist_ok=True)

        plot_topology(topo_by_time[flow_time], flow_time, output_dir)

except Exception as e:
    print(f"Error: {e}")
