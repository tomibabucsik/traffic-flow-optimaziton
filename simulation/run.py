# simulation/run.py

import os
import subprocess
import sys
from optimization.ga import GAOptimizer
import traci
import shutil

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from city_modeling.networkx_graph import CityGraph
from legacy_simulation.main_pygame import setup_grid_city

from .generator import (generate_node_file, generate_edge_file, 
                        generate_route_file, generate_sumo_config)
from .analysis import parse_tripinfo, log_results


SUMO_DIR = "sumo_files"
NETWORK_NAME = "city"

def run_fixed_experiment(config, scale, run_type):
    """Sets up and runs a headless SUMO experiment."""

    # --- 1. Setup Environment (Re-introduced from previous script) ---
    os.makedirs(SUMO_DIR, exist_ok=True)
    city, _, edge_nodes = setup_grid_city(
        rows=config["grid_rows"], cols=config["grid_cols"]
    )
    graph = city.get_graph()
    
    node_file = os.path.join(SUMO_DIR, f"{NETWORK_NAME}.nod.xml")
    edge_file = os.path.join(SUMO_DIR, f"{NETWORK_NAME}.edg.xml")
    net_file = os.path.join(SUMO_DIR, f"{NETWORK_NAME}.net.xml")
    route_file = os.path.join(SUMO_DIR, f"{NETWORK_NAME}.rou.xml")
    config_file = os.path.join(SUMO_DIR, f"{NETWORK_NAME}.sumocfg")
    tripinfo_output = os.path.join(SUMO_DIR, "tripinfo.xml")

    generate_node_file(node_file, graph)
    generate_edge_file(edge_file, graph)
    
    generate_route_file(
        route_file,
        edge_nodes, 
        config["simulation_time"], 
        config["arrival_rate"],
        scale=scale 
    )
    # -------------------------

    subprocess.run(["netconvert", "--node-files", node_file, "--edge-files", edge_file, "-o", net_file], check=True, capture_output=True)
    generate_sumo_config(config_file, net_file, route_file)

    # --- 2. Run Headless Simulation ---
    print(f"\nRunning Headless SUMO Experiment...")
    if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    else:
        sys.exit("Please declare environment variable 'SUMO_HOME'")
    
    sumo_cmd = ["sumo", "-c", config_file, 
                "--junction-taz",
                "--tripinfo-output", tripinfo_output]

    traci.start(sumo_cmd)
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
    traci.close()
    print("✅ Simulation Finished.")

    # --- 3. Analyze and Log Results ---
    print("\nAnalyzing Results...")
    results = parse_tripinfo(tripinfo_output, config["simulation_time"])
    if results:
        log_results(results, scale, run_type)

def run_viewer(config, scale):
    """Generates all files and launches the SUMO GUI for interactive viewing."""
    # --- 1. Setup Environment (Same as the experiment runner) ---
    os.makedirs(SUMO_DIR, exist_ok=True)
    city, _, edge_nodes = setup_grid_city(
        rows=config["grid_rows"], cols=config["grid_cols"]
    )
    graph = city.get_graph()
    
    node_file = os.path.join(SUMO_DIR, f"{NETWORK_NAME}.nod.xml")
    edge_file = os.path.join(SUMO_DIR, f"{NETWORK_NAME}.edg.xml")
    net_file = os.path.join(SUMO_DIR, f"{NETWORK_NAME}.net.xml")
    route_file = os.path.join(SUMO_DIR, f"{NETWORK_NAME}.rou.xml")
    config_file = os.path.join(SUMO_DIR, f"{NETWORK_NAME}.sumocfg")

    generate_node_file(node_file, graph)
    generate_edge_file(edge_file, graph)
    generate_route_file(
        route_file,
        edge_nodes, 
        config["simulation_time"],
        config["arrival_rate"],
        scale=scale
    )
    subprocess.run(["netconvert", "--node-files", node_file, "--edge-files", edge_file, "-o", net_file], check=True, capture_output=True)
    generate_sumo_config(config_file, net_file, route_file)

    # --- 2. Launch SUMO GUI ---
    print(f"\nLaunching SUMO GUI with traffic scale {scale}x. Press 'Play' to start.")
    sumo_gui_cmd = ["sumo-gui", "-c", config_file, "--junction-taz"]
    subprocess.run(sumo_gui_cmd)
    print("\n✅ SUMO GUI closed.")

def run_ga_experiment(config, scale, run_type):
    """Sets up the environment and runs the GA optimizer."""

    print("\nCleaning up previous simulation files...")
    if os.path.exists(SUMO_DIR):
        shutil.rmtree(SUMO_DIR)
    # --- 1. Setup Common Environment Files (once) ---
    if 'SUMO_HOME' not in os.environ:
        sys.exit("Please declare environment variable 'SUMO_HOME'")

    print("\nSetting up base environment for GA...")
    os.makedirs(SUMO_DIR, exist_ok=True)
    city, _, edge_nodes = setup_grid_city(
        rows=config["grid_rows"], cols=config["grid_cols"]
    )
    graph = city.get_graph()
    
    node_file = os.path.join(SUMO_DIR, f"{NETWORK_NAME}.nod.xml")
    edge_file = os.path.join(SUMO_DIR, f"{NETWORK_NAME}.edg.xml")
    net_file = os.path.join(SUMO_DIR, f"{NETWORK_NAME}.net.xml")
    route_file = os.path.join(SUMO_DIR, f"{NETWORK_NAME}.rou.xml")
    tripinfo_output = os.path.join(SUMO_DIR, "tripinfo.xml")

    generate_node_file(node_file, graph)
    generate_edge_file(edge_file, graph)
    generate_route_file(
        route_file, edge_nodes, config["simulation_time"], config["arrival_rate"], scale=scale
    )
    subprocess.run([
        "netconvert", "--node-files", node_file, "--edge-files", edge_file, "-o", net_file
    ], check=True)

    print("\nRunning a baseline simulation with default timings...")
    
    # Generate a config file WITHOUT the GA's additional file
    base_config_file = os.path.join(SUMO_DIR, f"{NETWORK_NAME}.sumocfg")
    generate_sumo_config(base_config_file, net_file, route_file)

    # Build the SUMO command for the baseline run
    base_sumo_cmd = ["sumo", "-c", base_config_file,
                     "--tripinfo-output", tripinfo_output,
                     "--junction-taz",
                     "--no-warnings", "true",
                     "--no-step-log", "true"]

    # Run the baseline simulation
    traci.start(base_sumo_cmd)
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
    traci.close()

    # Get the baseline metrics
    baseline_metrics = parse_tripinfo(tripinfo_output, config["simulation_time"])
    if not baseline_metrics:
        sys.exit("Error: Baseline simulation failed to produce results.")
    
    print(f"  - Baseline Wait Time: {baseline_metrics['total_system_wait_time']:.2f}")
    print(f"  - Baseline Travel Time: {baseline_metrics['avg_travel_time']:.2f}")

    # --- 2. Initialize and Run the GA Optimizer ---        
    optimizer = GAOptimizer(
        config=config,
        scale=scale,
        run_type=run_type,
        sumo_dir=SUMO_DIR,
        net_file=net_file,
        route_file=route_file,
        tripinfo_output=tripinfo_output,
        baseline_metrics=baseline_metrics
    )
    best_chromosome = optimizer.run()
    
    print(f"\nRunning final simulation with best chromosome to log results...")
    if best_chromosome:
        # Use the optimizer's helper method to get the metrics
        final_metrics = optimizer.get_metrics_for_individual(best_chromosome)
        
        if final_metrics:
            log_results(final_metrics, scale, run_type)
        else:
            print("Could not get final metrics. Results not logged.")
    else:
        print("GA did not produce a best chromosome. Results not logged.")