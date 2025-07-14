import os
import subprocess
import sys
import traci
import xml.etree.ElementTree as ET
import argparse
import csv
from datetime import datetime

from main import setup_grid_city, config
from sumo_generator import (generate_node_file, generate_edge_file, 
                            generate_route_file, generate_sumo_config)

SUMO_DIR = "sumo_files"
NETWORK_NAME = "city"
RESULTS_CSV = "results.csv"

def parse_tripinfo_output(file_path):
    """"Parses the tripinfo.xml output from SUMO and prints summary report"""
    tree = ET.parse(file_path)
    root = tree.getroot()

    travel_times = []
    wait_times = []

    travel_times = [float(trip.get('duration')) for trip in root.findall('tripinfo')]
    wait_times = [float(trip.get('timeLoss')) for trip in root.findall('tripinfo')]
    
    if not travel_times:
        return None

    num_completed = len(travel_times)
    metrics = {
        "completed_vehicles": num_completed,
        "avg_travel_time": sum(travel_times) / num_completed,
        "avg_wait_time": sum(wait_times) / num_completed,
        "throughput_vpm": num_completed / (config["simulation_time"] / 60.0)
    }
    return metrics

def log_results_to_csv(metrics, scale_factor):
    """Appends a row of results to the main CSV log file."""
    file_exists = os.path.isfile(RESULTS_CSV)
    
    with open(RESULTS_CSV, 'a', newline='') as f:
        writer = csv.writer(f)
        # Write header only if the file is new
        if not file_exists:
            writer.writerow(['timestamp', 'scale_factor', 'completed_vehicles', 'avg_travel_time', 'avg_wait_time', 'throughput_vpm'])
        
        # Write the data row
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            scale_factor,
            metrics['completed_vehicles'],
            f"{metrics['avg_travel_time']:.2f}",
            f"{metrics['avg_wait_time']:.2f}",
            f"{metrics['throughput_vpm']:.2f}"
        ])
    print(f"✅ Results logged to {RESULTS_CSV}")

def run(args):
    """Sets up and runs a headless SUMO experiment, then analyzes the results."""
    # --- 1. Setup Environment (same as before) ---
    os.makedirs(SUMO_DIR, exist_ok=True)
    city, _, edge_nodes = setup_grid_city(rows=config["grid_rows"], cols=config["grid_cols"])
    graph = city.get_graph()
    
    node_file = os.path.join(SUMO_DIR, f"{NETWORK_NAME}.nod.xml")
    edge_file = os.path.join(SUMO_DIR, f"{NETWORK_NAME}.edg.xml")
    net_file = os.path.join(SUMO_DIR, f"{NETWORK_NAME}.net.xml")
    route_file = os.path.join(SUMO_DIR, f"{NETWORK_NAME}.rou.xml")
    config_file = os.path.join(SUMO_DIR, f"{NETWORK_NAME}.sumocfg")
    tripinfo_output = os.path.join(SUMO_DIR, "tripinfo.xml")

    generate_node_file(node_file, graph)
    generate_edge_file(edge_file, graph)
    generate_route_file(route_file, edge_nodes, config["simulation_time"], config["arrival_rate"], scale=args.scale)
    subprocess.run(["netconvert", "--node-files", node_file, "--edge-files", edge_file, "-o", net_file], check=True, capture_output=True)
    generate_sumo_config(config_file, net_file, route_file)
    
    # --- 2. Run Headless Simulation with TraCI ---
    print("\n🚀 Running Headless SUMO Experiment...")
    if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    else:
        sys.exit("Please declare environment variable 'SUMO_HOME'")

    # Launch SUMO (not sumo-gui) and tell it to generate the tripinfo file
    sumo_cmd = ["sumo", "-c", config_file, 
                "--junction-taz",
                "--tripinfo-output", tripinfo_output]

    traci.start(sumo_cmd)
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
    traci.close()
    print("✅ Simulation Finished.")

    # --- 3. Analyze Results ---
    print("\n📊 Analyzing Results...")
    results = parse_tripinfo_output(tripinfo_output)
    if results:
        log_results_to_csv(results, args.scale)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a SUMO traffic simulation experiment.")
    parser.add_argument("--scale", type=float, default=1.0, help="Traffic scale multiplier (e.g., 0.5 for light, 2.0 for heavy).")
    args = parser.parse_args()
    
    run(args)