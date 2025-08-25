import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse
from scenarios import SCENARIOS
from simulation.run import run_viewer
from config import CONFIG


def view_scenario(scenario_name, scale):
    """
    Prepares and launches the SUMO GUI for a specified scenario.
    """
    if scenario_name not in SCENARIOS:
        print(f"Error: Scenario '{scenario_name}' not found in scenarios.py.")
        print("Available scenarios:", ", ".join(SCENARIOS.keys()))
        return

    scenario = SCENARIOS[scenario_name]
    
    full_config = CONFIG.copy()
    full_config.update(scenario)

    full_config['scenario_name'] = scenario_name

    if scale is None:
        scale = scenario['scales'][0]

    print(f"--- Preparing to view scenario: {scenario_name} at scale {scale}x ---")
    run_viewer(full_config, scale)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launch the SUMO GUI to view a traffic scenario.")
    parser.add_argument(
        "scenario", 
        type=str, 
        help=f"The name of the scenario to view. Available: {', '.join(SCENARIOS.keys())}"
    )
    parser.add_argument(
        "--scale", 
        type=float, 
        help="Optional traffic scale to view. Defaults to the first scale in the scenario definition."
    )
    args = parser.parse_args()
    view_scenario(args.scenario, args.scale)
