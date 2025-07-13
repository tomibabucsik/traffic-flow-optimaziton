import os
import subprocess
import sys
import traci

# Import setup functions from your original project
from main import setup_grid_city, config
from sumo_generator import (generate_node_file, generate_edge_file, 
                            generate_route_file, generate_sumo_config)

# --- Configuration ---
SUMO_DIR = "sumo_files"
NETWORK_NAME = "city"

# --- Main Execution ---
def main():
    """Generates all necessary files and runs the SUMO simulation."""
    print("🚦 Starting SUMO Environment Setup 🚦")
    
    # 1. Ensure output directory exists
    os.makedirs(SUMO_DIR, exist_ok=True)

    # 2. Use your existing logic to create the city graph object
    city, node_positions, edge_nodes = setup_grid_city(
        rows=config["grid_rows"], cols=config["grid_cols"]
    )
    city_graph = city.get_graph()

    # 3. Generate SUMO specific files
    node_file = os.path.join(SUMO_DIR, f"{NETWORK_NAME}.nod.xml")
    edge_file = os.path.join(SUMO_DIR, f"{NETWORK_NAME}.edg.xml")
    net_file = os.path.join(SUMO_DIR, f"{NETWORK_NAME}.net.xml")
    route_file = os.path.join(SUMO_DIR, f"{NETWORK_NAME}.rou.xml")
    config_file = os.path.join(SUMO_DIR, f"{NETWORK_NAME}.sumocfg")

    generate_node_file(node_file, city_graph)
    generate_edge_file(edge_file, city_graph)
    generate_route_file(route_file, edge_nodes, config["simulation_time"], config["arrival_rate"])
    
    # 4. Build the network using SUMO's netconvert tool
    print("\n🔨 Building SUMO network...")
    subprocess.run(["netconvert", "--node-files", node_file, "--edge-files", edge_file, "-o", net_file], check=True)
    
    # 5. Generate the final SUMO config file
    generate_sumo_config(config_file, net_file, route_file)

    # 6. Start SUMO and TraCI
    print("\n🚀 Launching SUMO with TraCI...")
        
    sumo_cmd = ["sumo-gui", "-c", config_file, "--junction-taz"]
    subprocess.run(sumo_cmd)

    # 7. Run the simulation
    # for step in range(config["simulation_time"]):
    #     traci.simulationStep()
    
    print("\n✅ Simulation Complete")

if __name__ == "__main__":
    main()