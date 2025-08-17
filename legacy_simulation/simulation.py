import time
import math
from city_modeling.networkx_graph import CityGraph
from traffic_generation.poisson_traffic import TrafficGenerator
from traffic_lights.traffic_lights import TrafficLightSystem

class TrafficSimulation:
    def __init__(self, city_graph, vehicles, config, visualize=False):
        self.city_graph = city_graph.get_graph()
        self.vehicles = vehicles
        self.config = config
        self.time_step = config['time_step']  # in seconds
        self.simulation_time = 0  # Track total simulation time in seconds
        self.traffic_light_system = TrafficLightSystem()
        self.traffic_light_cycles = 0
        self.visualize = visualize

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
        self.font = pygame.font.Font(None, 18)
        self.simulation_speed = 0.05  # Slow down: 0.1 simulation seconds per frame
        self.vehicle_speed_factor = 2.0

    def add_traffic_light_system(self, traffic_light_system):
        """Add a traffic light system to the simulation"""
        self.traffic_light_system = traffic_light_system
    
    def move_vehicles(self, time_step):
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
                    continue
                    #print(f"Time {self.simulation_time:.2f}s: Vehicle {vehicle['id']} entered at {vehicle['start']}")
                continue
                
            # Skip if vehicle has reached destination
            route = vehicle["route"]
            if vehicle["current_position"] == route[-1]:
                if vehicle["current_position"] != vehicle.get("last_position", None):
                    #print(f"Time {self.simulation_time}s: Vehicle {vehicle['id']} completed trip at {route[-1]}")
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
                vehicle["travel_time_remaining"] -= time_step * self.vehicle_speed_factor / congestion_factor
                
                # If finished traveling this edge
                if vehicle["travel_time_remaining"] <= 0:
                    #print(f"Time {self.simulation_time}s: Vehicle {vehicle['id']} reached {end}")
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

                if vehicle["completion_time"] != -1:
                    continue
                
                route = vehicle["route"]
                next_node_index = route.index(current_node) + 1
                
                # Check if we haven't reached the end
                if next_node_index < len(route):
                    next_node = route[next_node_index]
                    edge = (current_node, next_node)
                    road = self.city_graph[current_node][next_node]

                    if current_node in self.traffic_light_system.traffic_lights:
                        is_light_green = self.traffic_light_system.is_green(edge)
                        light_state_for_log = "GREEN" if is_light_green else "RED"

                        action = "MOVING" if is_light_green else "WAITING"

                        """
                        print(
                            f"DEBUG @ T={self.simulation_time:.1f}s | "
                            f"Vehicle {vehicle['id']} at Node {current_node} | "
                            f"Wants edge {edge} | "
                            f"Light is {light_state_for_log} | "
                            f"Action: {action}"
                        )
                        """
                    
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
                        #print(f"Time {self.simulation_time}s: Vehicle {vehicle['id']} started on {edge}")
                    # If red light, vehicle stays at current node
                    else:
                        vehicle["total_wait_time"] += time_step
                        if self.simulation_time % 5 == 0:
                            continue
                            #print(f"Time {self.simulation_time}s: Vehicle {vehicle['id']} waiting at {current_node}")
            route = vehicle['route']
            if vehicle['current_position'] == route[-1]:
                if vehicle['completion_time'] == -1:
                    vehicle['completion_time'] = self.simulation_time
                    print(f"Time {self.simulation_time:.2f}s: Vehicle {vehicle['id']} FINISHED trip")

    def draw(self):
        self.screen.fill(self.colors["black"])

        for u, v in self.city_graph.edges():
            start_pos = [int(x * self.scale_factor) + self.offset_x for x in self.node_positions[u]]
            end_pos = [int(x * self.scale_factor) + self.offset_x for x in self.node_positions[v]]
            pygame.draw.line(self.screen, self.colors["white"], start_pos, end_pos, 2)

        for node, data in self.city_graph.nodes(data=True):
            scaled_pos = [int(x * self.scale_factor) + self.offset_x for x in data['pos']]

            pygame.draw.circle(self.screen, self.colors['yellow'], scaled_pos, 6)

            if node in self.traffic_light_system.traffic_lights:
                light = self.traffic_light_system.traffic_lights[node]

                current_allowed_edges = []
                elapsed_time = 0
                for phase in light.phases:
                    if elapsed_time <= light.current_time < elapsed_time + phase['duration']:
                        current_allowed_edges = phase['allowed_edges']
                        break
                    elapsed_time += phase['duration']
                
                for successor in self.city_graph.predecessors(node):
                    succ_pos = [int(x * self.scale_factor) + self.offset_x for x in self.node_positions]

                    dx = succ_pos[0] - scaled_pos[0]
                    dy = succ_pos[1] - scaled_pos[1]
                    norm = math.sqrt(dx**2 + dy**2)
                    if norm == 0: continue

                    indicator_pos = [
                        scaled_pos[0] - (dx / norm) * 15,
                        scaled_pos[1] - (dy / norm) * 15
                    ]

                    edge = (node, successor)
                    is_green = edge in current_allowed_edges

                    color = self.colors["green"] if is_green else self.colors["red"]
                    pygame.draw.circle(self.screen, color, indicator_pos, 5)

        for vehicle in self.vehicles:
            if vehicle["entry_time"] <= self.simulation_time and vehicle['completion_time']:
                vehicle_pos = None

                if vehicle["current_edge"]:
                    start_node, end_node = vehicle["current_edge"]
                    start_pos = [int(x * self.scale_factor) + self.offset_x for x in self.node_positions[start_node]]
                    end_pos = [int(x * self.scale_factor) + self.offset_x for x in self.node_positions[end_node]]

                    progress = vehicle["progress_on_edge"]

                    base_pos = [
                        int(start_pos[0] + (end_pos[0] - start_pos[0]) * progress),
                        int(start_pos[1] + (end_pos[1] - start_pos[1]) * progress)
                    ]

                    lane_offset = 5
                    dx = end_pos[0] - start_pos[0]
                    dy = end_pos[1] - start_pos[1]
                    norm = math.sqrt(dx**2 + dy**2)
                    if norm > 0:
                        udx, udy = dx / norm, dy / norm  # Unit Direction Vector
                        # Perpendicular vector is (-udy, udx)
                        offset_x = -udy * lane_offset
                        offset_y = udx * lane_offset
                        vehicle_pos = [base_pos[0] + offset_x, base_pos[1] + offset_y]
                    else:
                        vehicle_pos = base_pos

                    pygame.draw.rect(self.screen, self.colors["blue"], (*vehicle_pos, 10, 10))

                elif vehicle["current_position"] != vehicle["route"][-1]:
                    pos = [int(x * self.scale_factor) + self.offset_x for x in self.node_positions[vehicle["current_position"]]]
                    pygame.draw.rect(self.screen, self.colors["purple"], (*pos, 10, 10))
                
                if vehicle_pos:
                    text_surface = self.font.render(str(vehicle['id']), True, self.colors['white'])
                    text_rect = text_surface.get_rect(center=(vehicle_pos[0] + 5, vehicle_pos[1] - 5))
                    self.screen.blit(text_surface, text_rect)

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

        try:
            speed_mul = self.config['visualization_speed_multiplier']
            delay = self.time_step / speed_mul if speed_mul > 0 else 0
        except KeyError:
            delay = 0
        
        while running and self.simulation_time < total_time:
            if self.visualize:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
            
            self.move_vehicles(self.time_step)
            self.traffic_light_system.update(self.time_step)
            self.simulation_time += self.time_step

            if self.visualize:
                self.draw()
                if delay > 0:
                    time.sleep(delay)
                self.clock.tick(60)
                
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

                if int(self.simulation_time) % 10 == 0:
                    print(f"Simulation time: {self.simulation_time:.0f}s / {total_time}s")
        
        if self.visualize:
            print(f"Simulation ended at time {self.simulation_time:.2f}s")
            pygame.quit()
        return results