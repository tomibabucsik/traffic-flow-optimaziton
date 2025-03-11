

class TrafficLight:
    def __init__(self, intersection_id, cycle_time=60):
        """
        Initialize a traffic light at an intersection
        
        Parameters:
        - intersection_id: ID of the intersection this light controls
        - cycle_time: Total cycle time in seconds
        """
        self.intersection_id = intersection_id
        self.cycle_time = cycle_time
        self.current_time = 0
        self.phases = []  # List of phases (green directions)
    
    def add_phase(self, allowed_edges, duration):
        """
        Add a phase to the traffic light cycle
        
        Parameters:
        - allowed_edges: List of (start, end) tuples representing allowed traffic movements
        - duration: Duration of this phase in seconds
        """
        self.phases.append({
            'allowed_edges': allowed_edges,
            'duration': duration
        })
    
    def update(self, time_step=1):
        """Update traffic light state based on current time"""
        self.current_time = (self.current_time + time_step) % self.cycle_time
    
    def is_green(self, edge):
        """Check if the given edge has a green light"""
        if not self.phases:
            return True  # If no phases defined, always allow movement
        
        # Find current phase
        elapsed_time = 0
        for phase in self.phases:
            if elapsed_time <= self.current_time < elapsed_time + phase['duration']:
                return edge in phase['allowed_edges']
            elapsed_time += phase['duration']
        
        return False


class TrafficLightSystem:
    def __init__(self):
        """Initialize the traffic light system"""
        self.traffic_lights = {}  # {intersection_id: TrafficLight}
    
    def add_traffic_light(self, traffic_light):
        """Add a traffic light to the system"""
        self.traffic_lights[traffic_light.intersection_id] = traffic_light
    
    def update(self, time_step=1):
        """Update all traffic lights"""
        for light in self.traffic_lights.values():
            light.update(time_step)
    
    def is_green(self, edge):
        """Check if the given edge has a green light"""
        start, end = edge
        # Check if the starting node has a traffic light
        if start in self.traffic_lights:
            return self.traffic_lights[start].is_green(edge)
        return True  # No traffic light means always green