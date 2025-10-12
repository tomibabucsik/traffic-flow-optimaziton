
import traci
import sys

MIN_GREEN_TIME = 10
PREDICTION_TIME_WINDOW = 45

class AdaptiveTrafficManager:
    """
    Manages all controllable traffic lights in the simulation with a predictive,
    "arrival pressure" based logic using V2I data.
    """
    def __init__(self, tls_ids, config):
        self.config = config
        
        self.prediction_window = self.config.get("adaptive_prediction_window", PREDICTION_TIME_WINDOW)
        
        self.tls_states = {}
        self.controllable_tls_ids = []

        print("--- Initializing Predictive Adaptive Traffic Manager ---")
        for tls_id in tls_ids:
            try:
                logic = traci.trafficlight.getAllProgramLogics(tls_id)[0]
                
                green_phases = []
                yellow_phases = []
                
                for i, phase in enumerate(logic.phases):
                    if 'g' in phase.state.lower() and 'y' not in phase.state.lower():
                        green_phases.append(i)
                
                if len(green_phases) >= 2:
                    for green_idx in green_phases:
                        if green_idx + 1 < len(logic.phases):
                            yellow_phases.append(green_idx + 1)
                        else:
                            yellow_phases.append(0) 

                    self.controllable_tls_ids.append(tls_id)
                    
                    self.tls_states[tls_id] = {
                        'time_in_current_phase': 0,
                        'green_phases': green_phases[:2],
                        'yellow_phases': yellow_phases[:2],
                        'lanes_p1': self._get_lanes_for_phase(tls_id, green_phases[0]),
                        'lanes_p2': self._get_lanes_for_phase(tls_id, green_phases[1])
                    }
                    print(f"  '{tls_id}' is controllable. Phase 1 lanes: {self.tls_states[tls_id]['lanes_p1']}, Phase 2 lanes: {self.tls_states[tls_id]['lanes_p2']}")
                else:
                    print(f"  '{tls_id}' is not controllable (less than 2 green phases). Ignoring.")

            except traci.TraCIException:
                print(f"  Could not process logic for '{tls_id}'. Ignoring.")
        
        print(f"--- Predictive control enabled for {len(self.controllable_tls_ids)} intersections. ---")

    def _get_lanes_for_phase(self, tls_id, phase_index):
        """Helper to get all incoming lanes that are green during a specific phase."""
        links = traci.trafficlight.getControlledLinks(tls_id)
        logic = traci.trafficlight.getAllProgramLogics(tls_id)[0]
        phase_state = logic.phases[phase_index].state
        
        green_lanes = set()
        if not links: return []

        for i in range(len(phase_state)):
            if phase_state[i].lower() == 'g':
                if i < len(links):
                    incoming_lane = links[i][0][0]
                    green_lanes.add(incoming_lane)
        return list(green_lanes)

    def _calculate_arrival_pressure(self, tls_id):
        """
        Calculates the "arrival pressure" for the two controlled phases of a TLS
        by estimating the arrival time of all vehicles in the network.
        """
        state = self.tls_states[tls_id]
        pressure = [0, 0] 
        
        all_vehicle_ids = traci.vehicle.getIDList()

        for veh_id in all_vehicle_ids:
            try:
                route_edges = traci.vehicle.getRoute(veh_id)
                current_edge = traci.vehicle.getRoadID(veh_id)

                if not current_edge or current_edge not in route_edges:
                    continue
                
                current_index = route_edges.index(current_edge)
                
                estimated_travel_time = 0
                
                for i, edge_id in enumerate(route_edges[current_index:]):
                    if i == 0:
                        # --- FIX #2: Replaced incorrect function calls with the correct TraCI API. ---
                        lane_id = traci.vehicle.getLaneID(veh_id)
                        lane_length = traci.lane.getLength(lane_id)
                        pos_on_lane = traci.vehicle.getLanePosition(veh_id) # Correct function
                        speed = traci.vehicle.getSpeed(veh_id)
                        time_to_end_of_edge = (lane_length - pos_on_lane) / speed if speed > 0.1 else float('inf')
                        estimated_travel_time += time_to_end_of_edge
                    else:
                        estimated_travel_time += traci.edge.getTraveltime(edge_id)
                    
                    for lane in state['lanes_p1']:
                        if traci.lane.getEdgeID(lane) == edge_id:
                            if estimated_travel_time <= self.prediction_window:
                                pressure[0] += 1
                            break
                    else:
                        for lane in state['lanes_p2']:
                            if traci.lane.getEdgeID(lane) == edge_id:
                                if estimated_travel_time <= self.prediction_window:
                                    pressure[1] += 1
                                break
                        else:
                            continue
                    break 
            
            except traci.TraCIException:
                continue
        
        return pressure

    def step(self):
        """
        Called at each simulation step to update traffic light logic based on arrival pressure.
        """
        for tls_id in self.controllable_tls_ids:
            state = self.tls_states[tls_id]
            state['time_in_current_phase'] += 1

            if state['time_in_current_phase'] < MIN_GREEN_TIME:
                continue

            pressure_p1, pressure_p2 = self._calculate_arrival_pressure(tls_id)

            current_phase = traci.trafficlight.getPhase(tls_id)

            is_phase1_green = current_phase == state['green_phases'][0]
            is_phase2_green = current_phase == state['green_phases'][1]
            
            if is_phase1_green and pressure_p2 > pressure_p1:
                self._switch_to_phase(tls_id, 0)

            elif is_phase2_green and pressure_p1 > pressure_p2:
                self._switch_to_phase(tls_id, 1)

    def _switch_to_phase(self, tls_id, current_green_index):
        """
        Handles the transition by setting the appropriate yellow phase.
        `current_green_index` is 0 if phase 1 was green, 1 if phase 2 was green.
        """
        state = self.tls_states[tls_id]
        yellow_phase_to_set = state['yellow_phases'][current_green_index]
        
        try:
            current_actual_phase = traci.trafficlight.getPhase(tls_id)
            if current_actual_phase in state['green_phases']:
                traci.trafficlight.setPhase(tls_id, yellow_phase_to_set)
                state['time_in_current_phase'] = 0
        except traci.TraCIException as e:
            pass