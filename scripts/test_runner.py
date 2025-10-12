import argparse
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scenarios import SCENARIOS
from simulation.run import run_fixed_experiment, run_ga_experiment, run_adaptive_experiment, run_reactive_experiment
from config import CONFIG

from city_modeling.builder import setup_grid_city, setup_arterial_road
from city_modeling.graph_visualization import GraphVisualization

MAP_BUILDERS = {
    "setup_grid_city": setup_grid_city,
    "setup_arterial_road": setup_arterial_road,
}

def run_test_suite(scenario_name):
    """
    Visualizes the scenario map for confirmation, then runs the full suite of tests.
    """
    if scenario_name not in SCENARIOS:
        print(f"Error: Scenario '{scenario_name}' not found in scenarios.py.")
        print("Available scenarios:", ", ".join(SCENARIOS.keys()))
        return

    scenario = SCENARIOS[scenario_name]

    if scenario.get("type") == "generated":
        print(f"--- Displaying map for scenario: {scenario_name} ---")
        print("    Close the plot window to begin the simulation suite.")
        try:
            map_builder_func = MAP_BUILDERS[scenario['map_builder']]
            map_args = scenario['map_config']
            city_graph_obj, _, _ = map_builder_func(**map_args)
            
            visualizer = GraphVisualization(city_graph_obj)
            visualizer.draw_city_graph()
        except Exception as e:
            print(f"Could not visualize map. Error: {e}")
            if input("Continue without map visualization? (y/n): ").lower() != 'y':
                print("Aborting test suite.")
                return
    else:
        print(f"--- Cannot auto-visualize imported map: {scenario_name} ---")
        print("    You can view the .net.xml file in sumo-gui to see the map.")


    print(f"\n--- Starting Test Suite for Scenario: {scenario_name} ---")
    print(f"    Description: {scenario['description']}")
    
    for run_type in scenario['run_types']:
        for scale in scenario['scales']:
            print(f"\n--- Running: Type='{run_type}', Scale={scale}x ---")
            
            full_config = CONFIG.copy()
            full_config.update(scenario)
            full_config['scenario_name'] = scenario_name

            if scenario.get("type") == "generated":
                full_config['map_builder'] = scenario['map_builder']
                full_config['map_config'] = scenario['map_config']
            else: # It's an imported map
                full_config['net_file'] = scenario['net_file']
                full_config['route_file'] = scenario['route_file']

            if run_type == "fixed":
                run_fixed_experiment(full_config, scale, run_type)
            elif run_type == "optimized":
                run_ga_experiment(full_config, scale, run_type)
            elif run_type == "adaptive":
                run_adaptive_experiment(full_config, scale, run_type)
            elif run_type == "reactive":
                run_reactive_experiment(full_config, scale, run_type)

    print(f"\n--- Test Suite for Scenario: {scenario_name} Finished ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a suite of traffic optimization experiments.")
    parser.add_argument(
        "scenario", 
        type=str, 
        help=f"The name of the scenario to run. Available: {', '.join(SCENARIOS.keys())}"
    )
    args = parser.parse_args()
    run_test_suite(args.scenario)
