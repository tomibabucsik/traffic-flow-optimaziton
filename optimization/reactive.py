import traci

MIN_GREEN_TIME = 10

class ReactiveTrafficManager:
    """
    Manages all controllable traffic lights in the simulation with a robust,
    map-agnostic REACTIVE logic based on queue lengths.
    """
    def __init__(self, tls_ids, config):
        self.config = config
        self.queue_threshold = self.config.get("adaptive_queue_threshold", 5)
        
        self.tls_states = {}
        self.controllable_tls_ids = []

        print("--- Initializing Reactive Traffic Manager (Queue-based) ---")
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
                    print(f"  '{tls_id}' is controllable.")
                else:
                    print(f"  '{tls_id}' is not controllable (less than 2 green phases). Ignoring.")

            except traci.TraCIException:
                print(f"  Could not process logic for '{tls_id}'. Ignoring.")
        
        print(f"--- Reactive control enabled for {len(self.controllable_tls_ids)} intersections. ---")

    def _get_lanes_for_phase(self, tls_id, phase_index):
        """Helper to get all incoming lanes that are green during a specific phase."""
        links = traci.trafficlight.getControlledLinks(tls_id)
        logic = traci.trafficlight.getAllProgramLogics(tls_id)[0]
        phase_state = logic.phases[phase_index].state
        
        green_lanes = set()
        if not links: return []

        for i in range(len(phase_state)):
            if phase_state[i].lower() == 'g':
                for link in links:
                    if link[0][2] == i:
                        in_lane = link[0][0]
                        green_lanes.add(in_lane)
        return list(green_lanes)

    def step(self):
        """
        Called at each simulation step to update traffic light logic.
        """
        for tls_id in self.controllable_tls_ids:
            state = self.tls_states[tls_id]
            state['time_in_current_phase'] += 1

            if state['time_in_current_phase'] < MIN_GREEN_TIME:
                continue

            queue_p1 = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in state['lanes_p1'])
            queue_p2 = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in state['lanes_p2'])

            current_phase = traci.trafficlight.getPhase(tls_id)

            is_phase1_green = current_phase == state['green_phases'][0]
            is_phase2_green = current_phase == state['green_phases'][1]

            if is_phase1_green and queue_p2 > queue_p1 + self.queue_threshold:
                self._switch_to_phase(tls_id, 0)

            elif is_phase2_green and queue_p1 > queue_p2 + self.queue_threshold:
                self._switch_to_phase(tls_id, 1)

    def _switch_to_phase(self, tls_id, current_green_index):
        """
        Handles the transition by setting the appropriate yellow phase.
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