import traci

# --- Adaptive Logic Configuration ---
MIN_GREEN_TIME = 10  # Minimum time a phase must remain green (seconds)
# ------------------------------------

class AdaptiveTrafficManager:
    """
    Manages all traffic lights in the simulation with a V2X-like adaptive logic.
    """
    def __init__(self, tls_ids, config):
        self.tls_ids = tls_ids
        self.config = config
        self.queue_threshold = self.config.get("adaptive_queue_threshold", 3)
        
        # State tracking for each traffic light
        self.tls_states = {}
        for tls_id in self.tls_ids:
            # Initialize state for each traffic light
            self.tls_states[tls_id] = {
                'current_phase_index': 0,
                'time_in_current_phase': 0
            }
            
            # This logic assumes a standard 4-way intersection where the first
            # two controlled lanes are for the North-South approaches.
            # This is a simplification; a more robust system might map lanes dynamically.
            controlled_lanes = traci.trafficlight.getControlledLanes(tls_id)
            self.tls_states[tls_id]['ns_lanes'] = controlled_lanes[:len(controlled_lanes)//2]
            self.tls_states[tls_id]['ew_lanes'] = controlled_lanes[len(controlled_lanes)//2:]

    def step(self):
        """
        Called at each simulation step to update traffic light logic.
        """
        for tls_id in self.tls_ids:
            state = self.tls_states[tls_id]
            state['time_in_current_phase'] += 1

            # Only consider switching if the minimum green time has passed
            if state['time_in_current_phase'] < MIN_GREEN_TIME:
                continue

            # --- V2X Data Gathering: Count waiting vehicles ---
            # Sum the number of halted vehicles on the incoming lanes for each direction
            ns_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in state['ns_lanes'])
            ew_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in state['ew_lanes'])

            # --- Decision Logic ---
            # Get the current green phase from Traci (0 is NS-Green, 2 is EW-Green in our default plan)
            current_phase = traci.trafficlight.getPhase(tls_id)

            # If North-South is green, only switch if the East-West queue has a significant advantage
            if current_phase == 0 and ew_queue > ns_queue + self.queue_threshold:
                self._switch_to_phase(tls_id, 2)

            # If East-West is green, only switch if the North-South queue has a significant advantage
            elif current_phase == 2 and ns_queue > ew_queue + self.queue_threshold:
                self._switch_to_phase(tls_id, 0)

    def _switch_to_phase(self, tls_id, next_phase_index):
        """
        Handles the transition between green phases, including yellow lights.
        """
        current_phase = traci.trafficlight.getPhase(tls_id)
        
        # Prevent switching if already in the target phase or in a yellow phase
        if current_phase == next_phase_index or current_phase % 2 != 0:
            return

        # Set the intermediate yellow phase
        # (Phase 1 is the yellow for NS, Phase 3 is the yellow for EW)
        yellow_phase_index = current_phase + 1
        traci.trafficlight.setPhase(tls_id, yellow_phase_index)
        
        # We don't need to manually set the next green phase. SUMO's traffic
        # light logic will automatically advance to the next phase in the
        # program definition after the yellow phase duration expires.
        
        # Reset the timer for the new phase
        self.tls_states[tls_id]['time_in_current_phase'] = 0