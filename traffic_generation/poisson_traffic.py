import numpy as np
import random
import networkx as nx

class TrafficGenerator:
    def __init__(self, city_graph, arrival_rate, simulation_time):
        self.city_graph = city_graph
        self.arrival_rate = arrival_rate
        self.simulation_time = simulation_time  # in minutes
        self.vehicles = []

    def generate_vehicles(self):
        """Generate vehicles with random start and destination."""
        intersections = list(self.city_graph.graph.nodes)  # Get all available intersections
        
        for t in range(self.simulation_time):
            num_vehicles = np.random.poisson(self.arrival_rate)  # Poisson-distributed arrivals
            
            for _ in range(num_vehicles):
                start, destination = random.sample(intersections, 2)  # Pick two different intersections

                try:
                    route = nx.shortest_path(
                        self.city_graph.graph,
                        source=start,
                        target=destination,
                        weight="travel_time")
                except nx.NetworkXNoPath:
                    route = [start]

                if not isinstance(route, list):
                    route = [start, destination]

                self.vehicles.append({
                    "id": len(self.vehicles) + 1, 
                    "start": start, 
                    "destination": destination, 
                    "current_position": start,
                    "entry_time": t,
                    "route": route,
                    "current_edge": None,
                    "progress_on_edge": 0,
                    "travel_time_remaining": 0
                })

    def get_vehicles(self):
        return self.vehicles