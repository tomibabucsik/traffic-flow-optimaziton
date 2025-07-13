import math

class TrafficLight:
    def __init__(self, intersection_id, cycle_time):
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
        self.cycle_count = 0
        print(f"Creating TrafficLight at {intersection_id} with cycle_time={cycle_time}")
        if not isinstance(cycle_time, (int, float)) or cycle_time <= 0:
            raise ValueError(f"Cycle time must be a positive number, got {cycle_time}")
    
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
        old_time = self.current_time
        if self.cycle_time <= 0:
            print(f"Error: Traffic light at {self.intersection_id} has cycle_time={self.cycle_time}")
            raise ValueError(f"Invalid cycle_time: {self.cycle_time}")
        self.current_time = (self.current_time + time_step) % self.cycle_time
        if old_time > self.current_time:
            self.cycle_count += 1
            print(f"INFO: Traffic light at {self.intersection_id} completed cycle {self.cycle_count}.")
    
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
        total_phase_duration = sum(phase['duration'] for phase in traffic_light.phases)

        if not math.isclose(total_phase_duration, traffic_light.cycle_time):
            raise ValueError(
                f"Traffic light {traffic_light.intersection_id}: "
                f"Sum of phase durations ({total_phase_duration}s) does not equal "
                f"the total cycle time ({traffic_light.cycle_time}s)."
            )

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

    def get_cycle_counts(self):
        return {id: light.cycle_count   for id, light in self.traffic_lights.items()}