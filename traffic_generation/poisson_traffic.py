import numpy as np
import random
import networkx as nx

class TrafficGenerator:
    def __init__(self, city_graph, arrival_rate, simulation_time, edge_nodes=None):
        self.city_graph = city_graph
        self.arrival_rate = arrival_rate / 60
        self.simulation_time = simulation_time
        self.vehicles = []
        self.entry_exit_nodes = edge_nodes if edge_nodes else list(self.city_graph.graph.nodes)

    def generate_vehicles(self):
        """Generate vehicles with random start and destination."""

        if len(self.entry_exit_nodes) < 2:
            raise ValueError("City graph must have at least 2 entry/exit nodes")
        
        for t in range(self.simulation_time):
            num_vehicles = np.random.poisson(self.arrival_rate)  # Poisson-distributed arrivals
            
            for _ in range(num_vehicles):
                start, destination = random.sample(self.entry_exit_nodes, 2)  # Pick two different intersections

                try:
                    route = nx.shortest_path(
                        self.city_graph.graph,
                        source=start,
                        target=destination,
                        weight="travel_time")
                except nx.NetworkXNoPath:
                    route = [start]

                self.vehicles.append({
                    "id": len(self.vehicles) + 1, 
                    "start": start, 
                    "destination": destination, 
                    "current_position": start,
                    "entry_time": t,
                    "route": route,
                    "completion_time": -1,
                    "total_wait_time": 0.0,
                    "current_edge": None,
                    "progress_on_edge": 0,
                    "travel_time_remaining": 0
                })

    def get_vehicles(self):
        return self.vehicles