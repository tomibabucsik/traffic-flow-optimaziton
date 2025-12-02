
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
        self.config = config or {}
        self.prediction_window = self.config.get("adaptive_prediction_window", PREDICTION_TIME_WINDOW)
        self.lookahead_edges = int(self.config.get("adaptive_lookahead_edges", 5))
        self.max_vehicles_to_process = int(self.config.get("adaptive_max_vehicles", 0))
        self.log_interval = int(self.config.get("adaptive_log_interval", 300))
        
        self.tls_states = {}
        self.controllable_tls_ids = []

        self.controlled_edges = set()

        self._edge_travel_time_cache = {}
        self._last_cache_time = None

        self._last_log_time = -1

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

                    lanes_p1 = self._get_lanes_for_phase(tls_id, green_phases[0])
                    lanes_p2 = self._get_lanes_for_phase(tls_id, green_phases[1])

                    self.controllable_tls_ids.append(tls_id)
                    
                    self.tls_states[tls_id] = {
                        'time_in_current_phase': 0,
                        'green_phases': green_phases[:2],
                        'yellow_phases': yellow_phases[:2],
                        'lanes_p1': lanes_p1,
                        'lanes_p2': lanes_p2
                    }

                    for lane in lanes_p1 + lanes_p2:
                        try:
                            edge_id = traci.lane.getEdgeID(lane)
                            self.controlled_edges.add(edge_id)
                        except traci.TraCIException:
                            continue

                    print(f"  '{tls_id}' is controllable. Phase 1 lanes: {lanes_p1}, Phase 2 lanes: {lanes_p2}")
                else:
                    print(f"  '{tls_id}' is not controllable (less than 2 green phases). Ignoring.")

            except traci.TraCIException:
                print(f"  Could not process logic for '{tls_id}'. Ignoring.")
        
        print(f"--- Predictive control enabled for {len(self.controllable_tls_ids)} intersections. ---")
        print(f"--- Controlled edges count: {len(self.controlled_edges)} ---")
        if self.max_vehicles_to_process > 0:
            print(f"--- Vehicle processing limited to {self.max_vehicles_to_process} vehicles per step ---")

    def _get_lanes_for_phase(self, tls_id, phase_index):
        """Return list of incoming lane IDs that are green during a specific phase."""
        links = traci.trafficlight.getControlledLinks(tls_id)
        logic = traci.trafficlight.getAllProgramLogics(tls_id)[0]
        phase_state = logic.phases[phase_index].state
        
        green_lanes = []
        if not links:
            return green_lanes

        for i in range(len(phase_state)):
            if phase_state[i].lower() == 'g':
                if i < len(links) and links[i]:
                    incoming_lane = links[i][0][0]
                    green_lanes.append(incoming_lane)
        return list(dict.fromkeys(green_lanes))

    def _refresh_edge_cache_if_needed(self, sim_time):
        """
        Cache edge traveltimes for the current simulation time so we don't call
        traci.edge.getTraveltime(...) repeatedly for the same edge within a step.
        """
        if self._last_cache_time == sim_time:
            return
        self._edge_travel_time_cache.clear()
        for edge_id in list(self.controlled_edges):
            try:
                self._edge_travel_time_cache[edge_id] = traci.edge.getTraveltime(edge_id)
            except traci.TraCIException:
                continue
        self._last_cache_time = sim_time

    def _get_edge_traveltime_cached(self, edge_id):
        return self._edge_travel_time_cache.get(edge_id, None)

    def _calculate_arrival_pressure(self, tls_id, sim_time):
        """
        Calculates the arrival pressure for the two controlled phases of a TLS.
        Optimized to only examine relevant vehicles and use cached traveltimes.
        """
        state = self.tls_states[tls_id]
        pressure = [0, 0]

        self._refresh_edge_cache_if_needed(sim_time)

        all_vehicle_ids = traci.vehicle.getIDList()
        total_vehicles = len(all_vehicle_ids)

        if self.max_vehicles_to_process > 0 and total_vehicles > self.max_vehicles_to_process:
            import random
            sampled = random.sample(all_vehicle_ids, self.max_vehicles_to_process)
            vehicle_iter = sampled
        else:
            vehicle_iter = all_vehicle_ids

        controlled_edges_local = self.controlled_edges
        lookahead = self.lookahead_edges
        pred_window = self.prediction_window

        for veh_id in vehicle_iter:
            try:
                route_edges = traci.vehicle.getRoute(veh_id)
                current_edge = traci.vehicle.getRoadID(veh_id)
                if not current_edge or not route_edges:
                    continue

                try:
                    current_index = route_edges.index(current_edge)
                except ValueError:
                    continue

                route_slice = route_edges[current_index: current_index + lookahead]

                if not any(edge in controlled_edges_local for edge in route_slice):
                    continue

                estimated_travel_time = 0.0

                for i, edge_id in enumerate(route_slice):
                    if i == 0:
                        lane_id = traci.vehicle.getLaneID(veh_id)
                        if not lane_id:
                            continue
                        lane_length = traci.lane.getLength(lane_id)
                        pos_on_lane = traci.vehicle.getLanePosition(veh_id)
                        speed = traci.vehicle.getSpeed(veh_id)
                        if speed is None:
                            speed = 0.0
                        if speed > 0.1:
                            time_to_end = (lane_length - pos_on_lane) / speed
                        else:
                            cached_tt = self._get_edge_traveltime_cached(edge_id=route_edges[0]) if route_edges else None
                            time_to_end = cached_tt if cached_tt is not None else float('inf')
                        estimated_travel_time += time_to_end
                    else:
                        cached_tt = self._get_edge_traveltime_cached(edge_id)
                        if cached_tt is not None:
                            estimated_travel_time += cached_tt
                        else:
                            try:
                                estimated_travel_time += traci.edge.getTraveltime(edge_id)
                            except traci.TraCIException:
                                estimated_travel_time += 0.0

                    if estimated_travel_time > pred_window:
                        break

                    for lane in state['lanes_p1']:
                        try:
                            lane_edge = traci.lane.getEdgeID(lane)
                        except traci.TraCIException:
                            continue
                        if lane_edge == edge_id and estimated_travel_time <= pred_window:
                            pressure[0] += 1
                            raise StopIteration

                    for lane in state['lanes_p2']:
                        try:
                            lane_edge = traci.lane.getEdgeID(lane)
                        except traci.TraCIException:
                            continue
                        if lane_edge == edge_id and estimated_travel_time <= pred_window:
                            pressure[1] += 1
                            raise StopIteration

            except StopIteration:
                continue
            except traci.TraCIException:
                continue

        return pressure

    def step(self):
        """
        Called at each simulation step to update traffic light logic based on arrival pressure.
        This method contains light-weight guards & logging so long predictive runs show progress.
        """
        sim_time = traci.simulation.getTime()
        if self._last_log_time < 0 or (sim_time - self._last_log_time) >= self.log_interval:
            try:
                active_veh = len(traci.vehicle.getIDList())
            except traci.TraCIException:
                active_veh = -1
            print(f"[Adaptive] sim_time={sim_time}, active_veh={active_veh}, controllable_tls={len(self.controllable_tls_ids)}")
            self._last_log_time = sim_time

        for tls_id in self.controllable_tls_ids:
            state = self.tls_states[tls_id]
            state['time_in_current_phase'] += 1

            if state['time_in_current_phase'] < MIN_GREEN_TIME:
                continue

            pressure_p1, pressure_p2 = self._calculate_arrival_pressure(tls_id, sim_time)

            try:
                current_phase = traci.trafficlight.getPhase(tls_id)
            except traci.TraCIException:
                continue

            is_phase1_green = current_phase == state['green_phases'][0]
            is_phase2_green = current_phase == state['green_phases'][1]
            
            if is_phase1_green and pressure_p2 > pressure_p1:
                self._switch_to_phase(tls_id, 0)

            elif is_phase2_green and pressure_p1 > pressure_p2:
                self._switch_to_phase(tls_id, 1)

    def _switch_to_phase(self, tls_id, current_green_index):
        """
        Sets the yellow phase that follows the currently green index.
        """
        state = self.tls_states[tls_id]
        yellow_phase_to_set = state['yellow_phases'][current_green_index]
        
        try:
            current_actual_phase = traci.trafficlight.getPhase(tls_id)
            if current_actual_phase in state['green_phases']:
                traci.trafficlight.setPhase(tls_id, yellow_phase_to_set)
                state['time_in_current_phase'] = 0
        except traci.TraCIException:
            pass