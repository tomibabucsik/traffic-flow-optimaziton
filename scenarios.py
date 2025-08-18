"""
This file defines the test scenarios for the traffic optimization project.
Each scenario includes a map configuration and a set of experiments to run.
"""

SCENARIOS = {
    "4x4_grid": {
        "description": "A standard 4x4 grid, good for general testing.",
        "map_builder": "setup_grid_city",
        "map_config": {"rows": 4, "cols": 4},
        "run_types": ["fixed", "optimized", "adaptive"],
        "scales": [2.0, 4.0, 6.0]
    },
    "arterial_road": {
        "description": "A long main road with several cross-streets, testing green wave efficiency.",
        "map_builder": "setup_arterial_road",
        "map_config": {"main_road_length": 5, "cross_streets": 3},
        "run_types": ["fixed", "optimized", "adaptive"],
        "scales": [2.0, 4.0, 6.0]
    },
    # You can easily add more scenarios here in the future
    # "complex_grid": {
    #     "description": "A larger, more complex grid.",
    #     "map_builder": "setup_grid_city",
    #     "map_config": {"rows": 5, "cols": 5},
    #     "run_types": ["fixed", "adaptive"],
    #     "scales": [5.0, 7.0]
    # },
}