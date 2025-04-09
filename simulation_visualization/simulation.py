import time
import pygame
from city_modeling.networkx_graph import CityGraph
from traffic_generation.poisson_traffic import TrafficGenerator
from traffic_lights.traffic_lights import TrafficLightSystem

pygame.init()

class TrafficSimulation:
    def __init__(self, city_graph, vehicles, time_step=1):
        self.city_graph = city_graph.get_graph()
        self.vehicles = vehicles
        self.time_step = time_step  # in seconds
        self.simulation_time = 0  # Track total simulation time in seconds
        self.traffic_light_system = TrafficLightSystem()
        self.traffic_light_cycles = 0

        # Setup for visualization
        self.screen_width, self.screen_height = 800, 800
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Traffic Simulation")
        self.clock = pygame.time.Clock()
        self.colors = {
            "black": (0, 0, 0),
            "white": (255, 255, 255),
            "red": (255, 0, 0),
            "green": (0, 255, 0),
            "blue": (0, 0, 255),
            "yellow": (255, 255, 0),
            "purple": (128, 0, 128)
        }
        self.node_positions = {node: data['pos'] for node, data in self.city_graph.nodes(data=True)}
        # Calculate scaling factor with padding
        max_x = max(x for x, y in self.node_positions.values()) or 1
        max_y = max(y for x, y in self.node_positions.values()) or 1
        self.scale_factor = min(
            (self.screen_width - 100) / max_x,  # 100 pixels padding
            (self.screen_height - 100) / max_y
        )
        self.offset_x = (self.screen_width - max_x * self.scale_factor) / 2
        self.offset_y = (self.screen_height - max_y * self.scale_factor) / 2
        self.simulation_speed = 0.05  # Slow down: 0.1 simulation seconds per frame
        self.vehicle_speed_factor = 2.0

    def add_traffic_light_system(self, traffic_light_system):
        """Add a traffic light system to the simulation"""
        self.traffic_light_system = traffic_light_system
    
    def move_vehicles(self):
        """Move vehicles along their route based on road properties, congestion and traffic lights"""
        # Update traffic lights
        self.traffic_light_system.update(self.simulation_speed)
        self.traffic_light_cycles = sum(self.traffic_light_system.get_cycle_counts().values())
        
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
            if vehicle["entry_time"] > self.simulation_time:
                if abs(vehicle["entry_time"] - self.simulation_time) < self.simulation_speed:
                    print(f"Time {self.simulation_time:.2f}s: Vehicle {vehicle['id']} entered at {vehicle['start']}")
                continue
                
            # Skip if vehicle has reached destination
            route = vehicle["route"]
            if vehicle["current_position"] == route[-1]:
                if vehicle["current_position"] != vehicle.get("last_position", None):
                    print(f"Time {self.simulation_time}s: Vehicle {vehicle['id']} completed trip at {route[-1]}")
                    vehicle["last_position"] = vehicle["current_position"]
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
                vehicle["travel_time_remaining"] -= self.simulation_speed * self.vehicle_speed_factor / congestion_factor
                
                # If finished traveling this edge
                if vehicle["travel_time_remaining"] <= 0:
                    print(f"Time {self.simulation_time}s: Vehicle {vehicle['id']} reached {end}")
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
                        print(f"Time {self.simulation_time}s: Vehicle {vehicle['id']} started on {edge}")
                    # If red light, vehicle stays at current node
                    else:
                        if self.simulation_time % 5 == 0:
                            print(f"Time {self.simulation_time}s: Vehicle {vehicle['id']} waiting at {current_node}")

    def draw(self):
        self.screen.fill(self.colors["black"])

        for u, v in self.city_graph.edges():
            start_pos = [int(x * self.scale_factor) + self.offset_x for x in self.node_positions[u]]
            end_pos = [int(x * self.scale_factor) + self.offset_x for x in self.node_positions[v]]
            pygame.draw.line(self.screen, self.colors["white"], start_pos, end_pos, 2)

        for node, pos in self.node_positions.items():
            scaled_pos = [int(x * self.scale_factor) + self.offset_x for x in pos]
            if node in self.traffic_light_system.traffic_lights:
                light = self.traffic_light_system.traffic_lights[node]
                elapsed_time = 0
                color = self.colors["red"]  # Default to red
                for i, phase in enumerate(light.phases):
                    if elapsed_time <= light.current_time < elapsed_time + phase["duration"]:
                        # Phase 0: NS green, EW red
                        if i == 0:
                            color = self.colors["green"]  # NS green
                        # Phase 1: EW green, NS red
                        elif i == 1:
                            color = self.colors["red"]  # NS red (since we're showing NS state)
                        # Debug print
                        if self.simulation_time % 5 < self.simulation_speed:
                            direction = "NS" if i == 0 else "EW"
                            print(f"Time {self.simulation_time:.2f}s: Node {node} light {color}, Phase {i} ({direction}), Current time {light.current_time:.2f}")
                        break
                    elapsed_time += phase["duration"]
                pygame.draw.circle(self.screen, color, scaled_pos, 12)
            else:
                pygame.draw.circle(self.screen, self.colors["yellow"], scaled_pos, 6)

        for vehicle in self.vehicles:
            if vehicle["entry_time"] <= self.simulation_time:
                if vehicle["current_edge"]:
                    start, end = vehicle["current_edge"]
                    start_pos = [int(x * self.scale_factor) + self.offset_x for x in self.node_positions[start]]
                    end_pos = [int(x * self.scale_factor) + self.offset_x for x in self.node_positions[end]]
                    progress = vehicle["progress_on_edge"]
                    vehicle_pos = [
                        int(start_pos[0] + (end_pos[0] - start_pos[0]) * progress),
                        int(start_pos[1] + (end_pos[1] - start_pos[1]) * progress)
                    ]
                    pygame.draw.rect(self.screen, self.colors["blue"], (*vehicle_pos, 10, 10))
                    if self.simulation_time % 5 < self.simulation_speed:
                        print(f"Time {self.simulation_time:.2f}s: Drawing Vehicle {vehicle['id']} on {vehicle['current_edge']}")
                elif vehicle["current_position"] != vehicle["route"][-1]:
                    pos = [int(x * self.scale_factor) + self.offset_x for x in self.node_positions[vehicle["current_position"]]]
                    pygame.draw.rect(self.screen, self.colors["purple"], (*pos, 10, 10))
                    if self.simulation_time % 5 < self.simulation_speed:
                        print(f"Time {self.simulation_time:.2f}s: Drawing Vehicle {vehicle['id']} waiting at {vehicle['current_position']}")

        pygame.display.flip()
        self.clock.tick(60)
        
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
        running = True
        results = []
        frame_count = 0
        
        while running and self.simulation_time < total_time:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            self.simulation_time += self.simulation_speed
            self.move_vehicles()
            self.draw()
            
            frame_count += 1
            if frame_count % 60 == 0:  # Print every second (60 frames)
                print(f"Real time: {frame_count // 60}s, Simulation time: {self.simulation_time:.2f}s")
            
            vehicles_in_transit = len([
                v for v in self.vehicles 
                if v['entry_time'] <= self.simulation_time and v['current_position'] != v['route'][-1]
            ])
            avg_travel_time = self.get_average_travel_time()
            
            results.append({
                'time': self.simulation_time,
                'vehicles_in_transit': vehicles_in_transit,
                'avg_travel_time': avg_travel_time,
                'density': self.get_traffic_density(),
                'traffic_lights': self.get_traffic_light_states()
            })
        
        print(f"Simulation ended after {frame_count} frames, {frame_count / 60:.1f} real seconds")
        pygame.quit()
        return results