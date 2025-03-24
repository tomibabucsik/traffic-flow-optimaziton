import time
import os

from matplotlib import animation, pyplot as plt
import numpy as np
from city_modeling.networkx_graph import CityGraph
from traffic_generation.poisson_traffic import TrafficGenerator
from simulation_visualization.simulation import TrafficSimulation
from simulation_visualization.visualization_tools import generate_traffic_report
from traffic_lights.traffic_lights import TrafficLight, TrafficLightSystem

config = {
    "grid_rows": 4,
    "grid_cols": 4,
    "road_length": 500,  # meters
    "speed_limit": 50,   # km/h
    "lanes": 2,
    "simulation_time": 180,  # seconds
    "arrival_rate": 5,      # vehicles/minute
    "traffic_light_cycle": 60,  # seconds
    "phase_duration": 30,       # seconds
    "time_step": 1            # seconds
}

def setup_grid_city(rows=3, cols=3, road_length=100, speed_limit=50, lanes=2):
    """Generate a grid-based city layout with intersections and roads"""
    city = CityGraph()

    # Create intersections (grid-based nodes)
    node_positions = {}
    node_id = 1
    for i in range(rows):
        for j in range(cols):
            node_positions[(i, j)] = node_id
            city.add_intersection(node_id, (i * road_length, j * road_length))  # Position in meters
            node_id += 1

    # Create roads (edges connecting adjacent nodes in both directions)
    for (i, j), node_id in node_positions.items():
        # Connect right (→)
        if j < cols - 1:
            right_node = node_positions[(i, j + 1)]
            city.add_road(node_id, right_node, length=road_length, speed_limit=speed_limit, lanes=lanes)
            city.add_road(right_node, node_id, length=road_length, speed_limit=speed_limit, lanes=lanes)
        
        # Connect down (↓)
        if i < rows - 1:
            down_node = node_positions[(i + 1, j)]
            city.add_road(node_id, down_node, length=road_length, speed_limit=speed_limit, lanes=lanes)
            city.add_road(down_node, node_id, length=road_length, speed_limit=speed_limit, lanes=lanes)

    return city, node_positions

def setup_traffic_lights(city, node_positions, rows, cols):
    """Setup traffic lights at intersections"""
    traffic_light_system = TrafficLightSystem()
    
    # Add traffic lights to all internal intersections (not at the edges)
    for i in range(1, rows-1):
        for j in range(1, cols-1):
            node_id = node_positions[(i, j)]
            traffic_light = TrafficLight(node_id, cycle_time=config["traffic_light_cycle"])
            
            ns_edges = []
            for di, dj in [(-1, 0), (1, 0)]:
                ni, nj = i + di, j + dj
                if 0 <= ni < rows and 0 <= nj < cols:
                    neighbor_id = node_positions[(ni, nj)]
                    ns_edges.append((neighbor_id, node_id))
                    ns_edges.append((node_id, neighbor_id))
            
            ew_edges = []
            for di, dj in [(0, -1), (0, 1)]:
                ni, nj = i + di, j + dj
                if 0 <= ni < rows and 0 <= nj < cols:
                    neighbor_id = node_positions[(ni, nj)]
                    ew_edges.append((neighbor_id, node_id))
                    ew_edges.append((node_id, neighbor_id))
            
            traffic_light.add_phase(ns_edges, duration=config["phase_duration"])
            traffic_light.add_phase(ew_edges, duration=config["phase_duration"])
            traffic_light_system.add_traffic_light(traffic_light)
    
    return traffic_light_system

def main():
    print("🚦 Traffic Simulation Started 🚦")

    # Setup grid city (adjustable grid size)
    city, node_positions = setup_grid_city(
        rows=config["grid_rows"], cols=config["grid_cols"],
        road_length=config["road_length"], speed_limit=config["speed_limit"],
        lanes=config["lanes"]
    )
    
    # Setup traffic lights
    traffic_light_system = setup_traffic_lights(city, node_positions, config["grid_rows"], config["grid_cols"])

    # Generate traffic
    traffic_gen = TrafficGenerator(city, config["arrival_rate"], config["simulation_time"])
    traffic_gen.generate_vehicles()
    vehicles = traffic_gen.get_vehicles()
    print(f"🚗 Generated {len(vehicles)} vehicles")

    # Run simulation
    simulation = TrafficSimulation(city, vehicles)
    simulation.add_traffic_light_system(traffic_light_system)
    
    for t in range(config["simulation_time"]):
        simulation.simulation_time = t
        simulation.move_vehicles()
        
        # Collect statistics
        vehicles_in_transit = len([v for v in vehicles if v['current_position'] != v['route'][-1]])
        avg_travel_time = simulation.get_average_travel_time()
        
        # Detailed output every 5 seconds
        if t % 5 == 0 or t == config["simulation_time"] - 1:
            print(f"\n⏳ Time {t}s:")
            print(f"  Vehicles in transit: {vehicles_in_transit}")
            print(f"  Completed trips: {len(vehicles) - vehicles_in_transit}")
            print(f"  Avg travel time: {avg_travel_time:.1f}s")
            
            # Traffic density
            density = simulation.get_traffic_density()
            congested_edges = [(edge, data['ratio']) for edge, data in density.items() if data['ratio'] > 0.8]
            if congested_edges:
                print("  Congested edges (flow/capacity > 0.8):")
                for edge, ratio in congested_edges[:3]:  # Limit to top 3
                    print(f"    {edge}: {ratio:.2f}")
            
            # Traffic light states
            light_states = simulation.get_traffic_light_states()
            print("  Traffic light states:")
            for node, allowed in light_states.items():
                state = "Green" if allowed else "Red"
                allowed_str = ", ".join(f"{e[0]}→{e[1]}" for e in allowed) if allowed else "None"
                print(f"    Node {node}: {state} ({allowed_str})")
            
            # Vehicle sample (first 3 in transit)
            in_transit = [v for v in vehicles if v['entry_time'] <= t and v['current_position'] != v['route'][-1]]
            if in_transit:
                print("  Sample of vehicles in transit (up to 3):")
                for v in in_transit[:3]:
                    pos = v['current_position'] if not v['current_edge'] else f"on {v['current_edge']}"
                    print(f"    ID {v['id']}: At {pos}, Route {v['route'][0]}→{v['route'][-1]}")

    print("✅ Simulation Complete ✅")

    report_path = os.path.join("output", "traffic_report.txt")
    generate_traffic_report(simulation, vehicles, config["simulation_time"], output_file=report_path)
    
    # Print summary statistics
    completed_vehicles = len([v for v in vehicles if v['current_position'] == v['route'][-1]])
    print(f"Statistics:")
    print(f"- Total vehicles: {len(vehicles)}")
    print(f"- Completed trips: {completed_vehicles}")
    print(f"- Final average travel time: {simulation.get_average_travel_time():.1f} seconds")

if __name__ == "__main__":
    main()