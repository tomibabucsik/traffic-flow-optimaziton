import time
from city_modeling.networkx_graph import CityGraph
from traffic_generation.poisson_traffic import TrafficGenerator
from traffic_lights.traffic_lights import TrafficLightSystem

class TrafficSimulation:
    def __init__(self, city_graph, vehicles, time_step=1):
        self.city_graph = city_graph.get_graph()
        self.vehicles = vehicles
        self.time_step = time_step  # in seconds
        self.simulation_time = 0  # Track total simulation time in seconds
        self.traffic_light_system = TrafficLightSystem()
    
    def add_traffic_light_system(self, traffic_light_system):
        """Add a traffic light system to the simulation"""
        self.traffic_light_system = traffic_light_system
    
    def move_vehicles(self):
        """Move vehicles along their route based on road properties, congestion and traffic lights"""
        # Update traffic lights
        self.traffic_light_system.update(self.time_step)
        
        # First, reset current flow counts on all edges
        for u, v in self.city_graph.edges():
            self.city_graph[u][v]['current_flow'] = 0
            
        # Count vehicles on each edge to calculate congestion
        for vehicle in self.vehicles:
            if vehicle["current_edge"]:
                start, end = vehicle["current_edge"]
                self.city_graph[start][end]['current_flow'] += 1
        
        # Now move each vehicle
        for vehicle in self.vehicles:
            # Skip if vehicle hasn't entered yet
            if vehicle["entry_time"] > self.simulation_time:
                continue
                
            # Skip if vehicle has reached destination
            route = vehicle["route"]
            if vehicle["current_position"] == route[-1]:
                continue
                
            # If vehicle is between nodes (on an edge)
            if vehicle["current_edge"]:
                start, end = vehicle["current_edge"]
                road = self.city_graph[start][end]
                
                # Calculate congestion factor (slows down as flow approaches capacity)
                congestion_factor = 1.0
                if road['capacity'] > 0:
                    flow_ratio = road['current_flow'] / road['capacity']
                    # BPR (Bureau of Public Roads) function for travel time adjustment
                    if flow_ratio < 1:
                        congestion_factor = 1 + 0.15 * (flow_ratio ** 4)
                    else:
                        congestion_factor = 1 + 0.15 * flow_ratio ** 4
                
                # Reduce time remaining based on congestion
                vehicle["travel_time_remaining"] -= self.time_step / congestion_factor
                
                # If finished traveling this edge
                if vehicle["travel_time_remaining"] <= 0:
                    vehicle["current_position"] = end
                    vehicle["current_edge"] = None
                    vehicle["progress_on_edge"] = 0
                else:
                    # Update progress (for visualization)
                    total_time = road["travel_time"] * congestion_factor
                    vehicle["progress_on_edge"] = 1 - (vehicle["travel_time_remaining"] / total_time)
            
            # If vehicle is at a node and needs to move to the next edge
            else:
                current_node = vehicle["current_position"]
                next_node_index = route.index(current_node) + 1
                
                # Check if we haven't reached the end
                if next_node_index < len(route):
                    next_node = route[next_node_index]
                    edge = (current_node, next_node)
                    road = self.city_graph[current_node][next_node]
                    
                    # Check traffic light
                    if self.traffic_light_system.is_green(edge):
                        # Calculate congestion factor
                        congestion_factor = 1.0
                        if road['capacity'] > 0:
                            flow_ratio = road['current_flow'] / road['capacity']
                            if flow_ratio < 1:
                                congestion_factor = 1 + 0.15 * (flow_ratio ** 4)
                            else:
                                congestion_factor = 1 + 0.15 * flow_ratio ** 4
                        
                        # Start traveling on this edge
                        vehicle["current_edge"] = edge
                        vehicle["travel_time_remaining"] = road["travel_time"] * congestion_factor
                        vehicle["progress_on_edge"] = 0
                    # If red light, vehicle stays at current node
    
    def get_traffic_density(self):
        """Return traffic density information for each edge"""
        density = {}
        for u, v in self.city_graph.edges():
            flow = self.city_graph[u][v]['current_flow']
            capacity = self.city_graph[u][v]['capacity']
            ratio = flow / capacity if capacity > 0 else 0
            density[(u, v)] = {
                'flow': flow,
                'capacity': capacity,
                'ratio': ratio
            }
        return density
    
    def get_average_travel_time(self):
        """Calculate average travel time for completed trips"""
        completed = [v for v in self.vehicles if v["current_position"] == v["route"][-1]]
        if not completed:
            return 0
        
        total_time = sum(
            self.simulation_time - v["entry_time"] 
            for v in completed
        )
        return total_time / len(completed)
    
    def get_traffic_light_states(self):
        """Get current state of all traffic lights"""
        states = {}
        for node_id, light in self.traffic_light_system.traffic_lights.items():
            current_allowed = []
            
            # Find current phase
            elapsed_time = 0
            for phase in light.phases:
                if elapsed_time <= light.current_time < elapsed_time + phase['duration']:
                    current_allowed = phase['allowed_edges']
                    break
                elapsed_time += phase['duration']
            
            states[node_id] = current_allowed
        
        return states
    
    def run_simulation(self, total_time):
        """Run the step-based simulation"""
        results = []
        
        for t in range(total_time):
            self.simulation_time = t
            self.move_vehicles()
            
            # Collect stats
            vehicles_in_transit = len([
                v for v in self.vehicles 
                if v['entry_time'] <= t and v['current_position'] != v['route'][-1]
            ])
            
            avg_travel_time = self.get_average_travel_time()
            
            results.append({
                'time': t,
                'vehicles_in_transit': vehicles_in_transit,
                'avg_travel_time': avg_travel_time,
                'density': self.get_traffic_density(),
                'traffic_lights': self.get_traffic_light_states()
            })
            
            print(f"Time {t}s: {vehicles_in_transit} vehicles in transit, "
                  f"Avg travel time: {avg_travel_time:.1f}s")
            
            time.sleep(self.time_step)  # Simulate real-time delay
            
        return results