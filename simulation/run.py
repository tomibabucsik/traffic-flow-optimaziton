import os
import subprocess
import sys
import traci
import shutil

from city_modeling.builder import setup_grid_city, setup_arterial_road
from .generator import (generate_node_file, generate_edge_file, 
                        generate_route_file, generate_sumo_config)
from .analysis import parse_tripinfo, log_results
from optimization.ga import GAOptimizer
from optimization.adaptive import AdaptiveTrafficManager

SUMO_DIR = "sumo_files"
NETWORK_NAME = "city"

MAP_BUILDERS = {
    "setup_grid_city": setup_grid_city,
    "setup_arterial_road": setup_arterial_road,
}

def setup_environment(config, scale):
    """
    Sets up the SUMO environment. It can either generate files from a builder
    or use pre-existing files for imported maps.
    Returns the paths to the net_file, route_file, and tripinfo_output.
    """
    print("\nSetting up environment...")
    if os.path.exists(SUMO_DIR):
        shutil.rmtree(SUMO_DIR)
    os.makedirs(SUMO_DIR, exist_ok=True)

    tripinfo_output = os.path.join(SUMO_DIR, "tripinfo.xml")

    # Check if this is an imported map scenario
    if config.get("type") == "imported":
        print(f"   - Using imported map: {config['net_file']}")

        source_net_file = config['net_file']
        dest_net_file = os.path.join(SUMO_DIR, os.path.basename(source_net_file))
        shutil.copy(source_net_file, dest_net_file)
        net_file = dest_net_file

        source_route_file = config['route_file']
        dest_route_file = os.path.join(SUMO_DIR, os.path.basename(source_route_file))
        shutil.copy(source_route_file, dest_route_file)
        route_file = dest_route_file

    else: # It's a generated map scenario
        print("   - Generating map from builder...")
        map_builder_func = MAP_BUILDERS[config['map_builder']]
        map_args = config['map_config']
        city, _, edge_nodes = map_builder_func(**map_args)
        graph = city.get_graph()
        
        node_file = os.path.join(SUMO_DIR, f"{NETWORK_NAME}.nod.xml")
        edge_file = os.path.join(SUMO_DIR, f"{NETWORK_NAME}.edg.xml")
        net_file = os.path.join(SUMO_DIR, f"{NETWORK_NAME}.net.xml")
        route_file = os.path.join(SUMO_DIR, f"{NETWORK_NAME}.rou.xml")

        generate_node_file(node_file, graph)
        generate_edge_file(edge_file, graph)
        generate_route_file(
            route_file, edge_nodes, config["simulation_time"], config["arrival_rate"], scale=scale
        )
        subprocess.run(["netconvert", "--node-files", node_file, "--edge-files", edge_file, "-o", net_file], check=True)

    print("Environment created.")
    return net_file, route_file, tripinfo_output


def run_fixed_experiment(config, scale, run_type):
    net_file, route_file, tripinfo_output = setup_environment(config, scale)
    config_file = os.path.join(SUMO_DIR, f"{NETWORK_NAME}.sumocfg")
    generate_sumo_config(config_file, net_file, route_file)

    print(f"\nRunning Fixed SUMO Experiment...")
    sumo_cmd = ["sumo", "-c", config_file, "--tripinfo-output", tripinfo_output, "--junction-taz", "--no-warnings", "true", "--no-step-log", "true"]
    traci.start(sumo_cmd)
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
    traci.close()
    print("Simulation Finished.")
    
    results = parse_tripinfo(tripinfo_output, config["simulation_time"])
    if results:
        log_results(results, scale, run_type, config.get('scenario_name', 'default'))


def run_ga_experiment(config, scale, run_type):
    net_file, route_file, tripinfo_output = setup_environment(config, scale)
    
    print("\nRunning a baseline simulation with default timings...")
    base_config_file = os.path.join(SUMO_DIR, f"{NETWORK_NAME}.sumocfg")
    generate_sumo_config(base_config_file, net_file, route_file)
    base_sumo_cmd = ["sumo", "-c", base_config_file, "--tripinfo-output", tripinfo_output, "--junction-taz", "--no-warnings", "true", "--no-step-log", "true"]
    
    traci.start(base_sumo_cmd)
    
    tls_ids = traci.trafficlight.getIDList()
    print(f"   - Found {len(tls_ids)} traffic lights in the network.")

    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
    traci.close()
    
    baseline_metrics = parse_tripinfo(tripinfo_output, config["simulation_time"])
    if not baseline_metrics:
        sys.exit("Error: Baseline simulation failed.")

    optimizer = GAOptimizer(config, scale, run_type, SUMO_DIR, net_file, route_file, tripinfo_output, baseline_metrics, tls_ids)
    best_chromosome = optimizer.run()
    
    if best_chromosome:
        final_metrics = optimizer.get_metrics_for_individual(best_chromosome)
        if final_metrics:
            log_results(final_metrics, scale, run_type, config.get('scenario_name', 'default'))

def run_adaptive_experiment(config, scale, run_type):
    net_file, route_file, tripinfo_output = setup_environment(config, scale)
    config_file = os.path.join(SUMO_DIR, f"{NETWORK_NAME}.sumocfg")
    generate_sumo_config(config_file, net_file, route_file)

    print(f"\nRunning Adaptive V2X SUMO Experiment...")
    sumo_cmd = ["sumo", "-c", config_file, "--tripinfo-output", tripinfo_output, "--junction-taz", "--no-warnings", "true", "--no-step-log", "true"]
    traci.start(sumo_cmd)
    
    tls_ids = traci.trafficlight.getIDList()
    adaptive_manager = AdaptiveTrafficManager(tls_ids, config)
    
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        adaptive_manager.step()

    traci.close()
    print("Simulation Finished.")
    
    results = parse_tripinfo(tripinfo_output, config["simulation_time"])
    if results:
        log_results(results, scale, run_type, config.get('scenario_name', 'default'))

def run_viewer(config, scale):
    """
    Generates all necessary files for a scenario and launches the SUMO GUI
    for interactive viewing with default 'fixed' traffic light timings.
    """
    # Use the centralized setup function to handle both generated and imported maps
    net_file, route_file, _ = setup_environment(config, scale)
    
    config_file = os.path.join(SUMO_DIR, f"{NETWORK_NAME}.sumocfg")
    generate_sumo_config(config_file, net_file, route_file)
    scenario_name = config.get('scenario_name', 'N/A')

    print(f"\nLaunching SUMO GUI for scenario '{config['scenario_name']}'...")
    print("   Press 'Play' in the GUI to start the simulation.")
    
    # Command to launch the GUI version of SUMO
    sumo_gui_cmd = ["sumo-gui", "-c", config_file, "--junction-taz"]
    
    try:
        subprocess.run(sumo_gui_cmd)
    except FileNotFoundError:
        print("\nError: 'sumo-gui' command not found.")
        print("   Please ensure that the SUMO 'bin' directory is in your system's PATH environment variable.")
    
    print("\nSUMO GUI closed.")