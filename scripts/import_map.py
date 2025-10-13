
import os
import sys
import subprocess
import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Configuration ---
MAPS_DIR = "map_assets"
BBOX = BBOX = "18.970,46.515,19.000,46.535" # coordinates from OSM
SCENARIO_NAME = "kalocsa"
# -------------------

def import_and_prepare_map():
    """
    Downloads a map from OpenStreetMap, converts it for SUMO,
    and generates random traffic for it.
    """
    os.makedirs(MAPS_DIR, exist_ok=True)

    osm_file = os.path.join(MAPS_DIR, f"{SCENARIO_NAME}.osm.xml")
    net_file = os.path.join(MAPS_DIR, f"{SCENARIO_NAME}.net.xml")
    route_file = os.path.join(MAPS_DIR, f"{SCENARIO_NAME}.rou.xml")

    # --- 1. Download Map Data from OpenStreetMap ---
    print(f"--- Downloading map data for '{SCENARIO_NAME}' ---")
    osm_api_url = f"https://api.openstreetmap.org/api/0.6/map?bbox={BBOX}"
    response = requests.get(osm_api_url)
    if response.status_code == 200:
        with open(osm_file, 'wb') as f:
            f.write(response.content)
        print(f"Map data saved to {osm_file}")
    else:
        sys.exit(f"Failed to download map data. Status code: {response.status_code}")

    # --- 2. Convert OSM Map to SUMO Network ---
    print(f"\n--- Converting map to SUMO format ---")
    netconvert_cmd = [
        "netconvert",
        "--osm-files", osm_file,
        "-o", net_file,
        "--geometry.remove",
        "--ramps.guess",
        "--junctions.join",
        "--tls.guess-signals",
        "--tls.join"
    ]
    subprocess.run(netconvert_cmd, check=True)
    print(f"SUMO network file created: {net_file}")

    # --- 3. Generate Random Traffic ---
    print(f"\n--- Generating random traffic routes ---")
    random_trips_script = os.path.join(os.environ['SUMO_HOME'], 'tools', 'randomTrips.py')
    random_trips_cmd = [
        sys.executable,
        random_trips_script,
        "-n", net_file,
        "-r", route_file,
        "-e", "5400",
        "-p", "1.0",
        "--validate"
    ]
    subprocess.run(random_trips_cmd, check=True)
    print(f"Random traffic routes created: {route_file}")
    print(f"\nScenario '{SCENARIO_NAME}' is ready to be used!")

if __name__ == "__main__":
    if 'SUMO_HOME' not in os.environ:
        sys.exit("Please declare environment variable 'SUMO_HOME'")
    import_and_prepare_map()