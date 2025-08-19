"""
This file defines the test scenarios for the traffic optimization project.
Each scenario includes a map configuration and a set of experiments to run.
"""

SCENARIOS = {
    "4x4_grid": {
        "description": "A standard 4x4 grid, good for general testing.",
        "type": "generated",
        "simulation_time": 450,
        "map_builder": "setup_grid_city",
        "map_config": {"rows": 4, "cols": 4},
        "run_types": ["fixed", "optimized", "adaptive"],
        "scales": [2.0, 4.0, 6.0]
    },
    "arterial_road": {
        "description": "A long main road with several cross-streets.",
        "type": "generated",
        "simulation_time": 900,
        "map_builder": "setup_arterial_road",
        "map_config": {"main_road_length": 5, "cross_streets": 3},
        "run_types": ["fixed", "optimized", "adaptive"],
        "scales": [2.0, 4.0, 6.0]
    },
    "budapest_downtown": {
        "description": "A real-world map section from downtown Budapest.",
        "type": "imported",
        "simulation_time": 5400,
        "net_file": "assets/maps/budapest_downtown.net.xml",
        "route_file": "assets/maps/budapest_downtown.rou.xml",
        "run_types": ["fixed", "optimized", "adaptive"],
        "scales": [1.0]
    }
}