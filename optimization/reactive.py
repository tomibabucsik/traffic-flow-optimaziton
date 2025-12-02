import traci

MIN_GREEN_TIME = 10

class ReactiveTrafficManager:
    """
    Manages all controllable traffic lights in the simulation with a robust,
    map-agnostic REACTIVE logic based on queue lengths.
    """
    def __init__(self, tls_ids, config):
        self.config = config or {}
        self.queue_threshold = self.config.get("adaptive_queue_threshold", 5)
        self.log_interval = int(self.config.get("reactive_log_interval", 300))

        self.tls_states = {}
        self.controllable_tls_ids = []
        self._last_log_time = -1

        print("--- Initializing Reactive Traffic Manager (Queue-based, Optimized) ---")
        for tls_id in tls_ids:
            try:
                logics = traci.trafficlight.getAllProgramLogics(tls_id)
                if not logics:
                    continue
                logic = logics[0]

                green_phases = []
                yellow_phases = []

                for i, phase in enumerate(logic.phases):
                    if "g" in phase.state.lower() and "y" not in phase.state.lower():
                        green_phases.append(i)

                if len(green_phases) < 2:
                    print(f"  '{tls_id}' is not controllable (less than 2 green phases). Ignoring.")
                    continue

                for g_idx in green_phases:
                    next_idx = g_idx + 1 if g_idx + 1 < len(logic.phases) else 0
                    yellow_phases.append(next_idx)

                lanes_p1 = self._get_lanes_for_phase(tls_id, green_phases[0])
                lanes_p2 = self._get_lanes_for_phase(tls_id, green_phases[1])

                if not lanes_p1 or not lanes_p2:
                    print(f"  '{tls_id}' has incomplete phase lanes, skipping.")
                    continue

                self.controllable_tls_ids.append(tls_id)
                self.tls_states[tls_id] = {
                    "time_in_current_phase": 0,
                    "green_phases": green_phases[:2],
                    "yellow_phases": yellow_phases[:2],
                    "lanes_p1": lanes_p1,
                    "lanes_p2": lanes_p2
                }

                print(f"  '{tls_id}' is controllable with {len(lanes_p1)} + {len(lanes_p2)} lanes.")

            except traci.TraCIException:
                print(f"  Could not process logic for '{tls_id}', ignoring.")
                continue

        print(f"--- Reactive control enabled for {len(self.controllable_tls_ids)} intersections. ---")

    def _get_lanes_for_phase(self, tls_id, phase_index):
        """Safely extract incoming lanes for a phase, compatible with nested controlled links."""
        try:
            logic = traci.trafficlight.getAllProgramLogics(tls_id)[0]
            phase_state = logic.phases[phase_index].state
            controlled_links = traci.trafficlight.getControlledLinks(tls_id)
        except traci.TraCIException:
            return []

        green_lanes = set()
        if not controlled_links:
            return []

        for link_group in controlled_links:
            for link in link_group:
                try:
                    in_lane, out_lane, _ = link
                except (TypeError, ValueError):
                    continue

                link_index = controlled_links.index(link_group)
                if link_index < len(phase_state) and phase_state[link_index].lower() == "g":
                    green_lanes.add(in_lane)

        valid_lanes = [l for l in green_lanes if ":" not in l]
        return list(dict.fromkeys(valid_lanes))

    def step(self):
        """Called each simulation step to update signal logic."""
        sim_time = traci.simulation.getTime()
        if self._last_log_time < 0 or (sim_time - self._last_log_time) >= self.log_interval:
            print(f"[Reactive] sim_time={sim_time}, controllable_tls={len(self.controllable_tls_ids)}")
            self._last_log_time = sim_time

        for tls_id in self.controllable_tls_ids:
            try:
                state = self.tls_states[tls_id]
                state["time_in_current_phase"] += 1

                if state["time_in_current_phase"] < MIN_GREEN_TIME:
                    continue

                queue_p1 = sum(
                    traci.lane.getLastStepHaltingNumber(lane)
                    for lane in state["lanes_p1"]
                    if traci.lane.getIDList().__contains__(lane)
                )
                queue_p2 = sum(
                    traci.lane.getLastStepHaltingNumber(lane)
                    for lane in state["lanes_p2"]
                    if traci.lane.getIDList().__contains__(lane)
                )

                current_phase = traci.trafficlight.getPhase(tls_id)
                is_phase1_green = current_phase == state["green_phases"][0]
                is_phase2_green = current_phase == state["green_phases"][1]

                if is_phase1_green and queue_p2 > queue_p1 + self.queue_threshold:
                    self._switch_to_phase(tls_id, 0)
                elif is_phase2_green and queue_p1 > queue_p2 + self.queue_threshold:
                    self._switch_to_phase(tls_id, 1)

            except traci.TraCIException:
                continue

    def _switch_to_phase(self, tls_id, current_green_index):
        """Transition to yellow after the current green."""
        try:
            state = self.tls_states[tls_id]
            yellow_phase_to_set = state["yellow_phases"][current_green_index]
            current_actual_phase = traci.trafficlight.getPhase(tls_id)
            if current_actual_phase in state["green_phases"]:
                traci.trafficlight.setPhase(tls_id, yellow_phase_to_set)
                state["time_in_current_phase"] = 0
        except traci.TraCIException:
            pass