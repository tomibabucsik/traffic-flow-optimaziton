import time
import os

from matplotlib import pyplot as plt
from city_modeling.networkx_graph import CityGraph
from traffic_generation.poisson_traffic import TrafficGenerator
from simulation_visualization.simulation import TrafficSimulation
from simulation_visualization.visualization_tools import plot_traffic_snapshot, create_traffic_animation
from traffic_lights.traffic_lights import TrafficLight, TrafficLightSystem

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
            
            # Create traffic light with 60-second cycle
            traffic_light = TrafficLight(node_id, cycle_time=60)
            
            # Define phases - for a cross intersection we typically have 2 or 4 phases
            # Phase 1: North-South movement
            ns_edges = []
            for di, dj in [(-1, 0), (1, 0)]:  # Up and down neighbors
                ni, nj = i + di, j + dj
                if 0 <= ni < rows and 0 <= nj < cols:
                    neighbor_id = node_positions[(ni, nj)]
                    ns_edges.append((neighbor_id, node_id))
                    ns_edges.append((node_id, neighbor_id))
            
            # Phase 2: East-West movement
            ew_edges = []
            for di, dj in [(0, -1), (0, 1)]:  # Left and right neighbors
                ni, nj = i + di, j + dj
                if 0 <= ni < rows and 0 <= nj < cols:
                    neighbor_id = node_positions[(ni, nj)]
                    ew_edges.append((neighbor_id, node_id))
                    ew_edges.append((node_id, neighbor_id))
            
            # Add phases to traffic light
            traffic_light.add_phase(ns_edges, duration=30)  # North-South gets 30 seconds
            traffic_light.add_phase(ew_edges, duration=30)  # East-West gets 30 seconds
            
            # Add traffic light to system
            traffic_light_system.add_traffic_light(traffic_light)
    
    return traffic_light_system

def main():
    print("🚦 Traffic Simulation Started 🚦")

    # Setup grid city (adjustable grid size)
    rows, cols = 4, 4
    city, node_positions = setup_grid_city(rows=rows, cols=cols, road_length=500, speed_limit=50, lanes=2)
    
    # Setup traffic lights
    traffic_light_system = setup_traffic_lights(city, node_positions, rows, cols)

    # Generate traffic
    traffic_gen = TrafficGenerator(city, arrival_rate=5, simulation_time=10)
    traffic_gen.generate_vehicles()
    vehicles = traffic_gen.get_vehicles()
    print(f"🚗 Generated {len(vehicles)} vehicles")

    # Run simulation
    simulation = TrafficSimulation(city, vehicles)
    simulation.add_traffic_light_system(traffic_light_system)
    
    # Store results for analysis
    results = []
    
    simulation_time = 60  # Total simulation duration in seconds
    for t in range(simulation_time):
        simulation.simulation_time = t
        simulation.move_vehicles()
        
        # Collect statistics
        vehicles_in_transit = len([v for v in vehicles if v['current_position'] != v['route'][-1]])
        avg_travel_time = simulation.get_average_travel_time()
        
        results.append({
            'time': t,
            'vehicles_in_transit': vehicles_in_transit,
            'avg_travel_time': avg_travel_time
        })
        
        print(f"⏳ Time {t}s: {vehicles_in_transit} vehicles in transit, Avg travel time: {avg_travel_time:.1f}s")
        
        # Optionally save snapshots at intervals
        if t % 10 == 0:
            plot_traffic_snapshot(city, vehicles, simulation)
            plt_filename = f"traffic_snapshot_t{t}.png"
            plt.savefig(plt_filename)
            plt.close()
            print(f"📸 Saved snapshot to {plt_filename}")
        
        time.sleep(0.1)  # Reduced delay for faster simulation

    # Final visualization
    plot_traffic_snapshot(city, vehicles, simulation)
    
    # Optional: Create animation from the entire simulation
    # comment out if you don't want to create an animation
    try:
        print("🎬 Creating animation...")
        ani = create_traffic_animation(city, simulation, vehicles, frames=min(100, simulation_time))
        ani.save('traffic_simulation.mp4', writer='ffmpeg')
        print("🎬 Animation saved to traffic_simulation.mp4")
    except Exception as e:
        print(f"⚠️ Could not create animation: {e}")

    print("✅ Simulation Complete ✅")
    
    # Print summary statistics
    completed_vehicles = len([v for v in vehicles if v['current_position'] == v['route'][-1]])
    print(f"Statistics:")
    print(f"- Total vehicles: {len(vehicles)}")
    print(f"- Completed trips: {completed_vehicles}")
    print(f"- Final average travel time: {simulation.get_average_travel_time():.1f} seconds")

if __name__ == "__main__":
    main()