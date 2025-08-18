import argparse
from scenarios import SCENARIOS
from city_modeling.builder import setup_grid_city, setup_arterial_road
from city_modeling.graph_visualization import GraphVisualization

# A dictionary to map builder names from scenarios.py to the actual functions
MAP_BUILDERS = {
    "setup_grid_city": setup_grid_city,
    "setup_arterial_road": setup_arterial_road,
}

def visualize_scenario_map(scenario_name):
    """
    Generates and displays a visual plot of a scenario's map.
    """
    if scenario_name not in SCENARIOS:
        print(f"Error: Scenario '{scenario_name}' not found in scenarios.py.")
        print("Available scenarios:", ", ".join(SCENARIOS.keys()))
        return

    scenario = SCENARIOS[scenario_name]
    print(f"--- 🗺️  Visualizing map for scenario: {scenario_name} ---")

    # 1. Get the correct map builder function and its arguments
    map_builder_func = MAP_BUILDERS[scenario['map_builder']]
    map_args = scenario['map_config']

    # 2. Call the builder to create the in-memory CityGraph object
    city_graph_obj, _, _ = map_builder_func(**map_args)

    # 3. Use your existing GraphVisualization class to draw the plot
    visualizer = GraphVisualization(city_graph_obj)
    visualizer.draw_city_graph()
    print("✅ Plot window opened. Close the plot to exit.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Visualize a scenario's map layout.")
    parser.add_argument(
        "scenario", 
        type=str, 
        help=f"The name of the scenario map to visualize. Available: {', '.join(SCENARIOS.keys())}"
    )
    args = parser.parse_args()
    visualize_scenario_map(args.scenario)