# simulation/ga.py

import random
import os
import sys
from simulation.generator import generate_tls_file, generate_sumo_config
from simulation.analysis import parse_tripinfo
import traci

# --- GA Configuration ---
POPULATION_SIZE = 10
N_GENERATIONS = 20
MUTATION_RATE = 0.1
CROSSOVER_RATE = 0.8
# Range for green light durations (e.g., 10 to 60 seconds)
GENE_MIN = 10
GENE_MAX = 60
# ------------------------

class GAOptimizer:
    """
    A simple Genetic Algorithm to optimize traffic light timings.
    
    The 'chromosome' for an individual is a list of green light durations 
    for all phases of all traffic-light-controlled intersections.
    """

    def __init__(self, config, scale, run_type, sumo_dir, net_file, route_file, tripinfo_output):
        self.config = config
        self.scale = scale
        self.run_type = run_type
        self.sumo_dir = sumo_dir
        self.net_file = net_file
        self.route_file = route_file
        self.tripinfo_output = tripinfo_output

        # Identify which intersections have traffic lights (hardcoded from your generator)
        self.tls_intersections = [6, 7, 10, 11]
        
        # Each of the 4 intersections has 2 main phases (North-South, East-West)
        # So, the chromosome length is 4 * 2 = 8
        self.chromosome_length = len(self.tls_intersections) * 2

    def _create_individual(self):
        """Creates a random individual (chromosome)."""
        return [random.randint(GENE_MIN, GENE_MAX) for _ in range(self.chromosome_length)]

    def _run_simulation_for_fitness(self, individual):
        """Runs a SUMO simulation and returns the fitness score."""
        
        # 1. Generate the traffic light file for this specific individual
        tls_file = os.path.join(self.sumo_dir, "city.add.xml")
        generate_tls_file(
            tls_file, 
            self.tls_intersections, 
            individual, 
            self.config["yellow_phase_duration"],
            self.config["all_red_duration"]
        )

        # 2. Generate the SUMO config to use this TLS file
        config_file = os.path.join(self.sumo_dir, "city.sumocfg")
        generate_sumo_config(config_file, self.net_file, self.route_file, additional_files=[tls_file])

        # 3. Run the simulation
        sumo_cmd = ["sumo", "-c", config_file, 
            "--tripinfo-output", self.tripinfo_output,
            "--junction-taz",
            "--no-warnings", "true",
            "--no-step-log", "true"]
        
        traci.start(sumo_cmd)

        for tls_id in self.tls_intersections:
            traci.trafficlight.setProgram(str(tls_id), "1")

        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
        traci.close()

        # 4. Calculate fitness from results
        results = parse_tripinfo(self.tripinfo_output, self.config["simulation_time"])
        if not results or results['completed_vehicles'] == 0:
            return 0  # Penalize solutions with no completed trips

        # Fitness is the inverse of total wait time (we want to minimize wait time)
        total_wait_time = results.get("total_system_wait_time", float('inf'))
        fitness = 1.0 / (1.0 + total_wait_time)
        
        return fitness

    def _selection(self, population, fitnesses):
        """Selects two parents using tournament selection."""
        tournament_size = 3
        selected = []
        for _ in range(2):
            participants_indices = random.sample(range(len(population)), tournament_size)
            best_participant_index = max(participants_indices, key=lambda i: fitnesses[i])
            selected.append(population[best_participant_index])
        return selected[0], selected[1]

    def _crossover(self, parent1, parent2):
        """Performs single-point crossover."""
        if random.random() < CROSSOVER_RATE:
            point = random.randint(1, self.chromosome_length - 1)
            child1 = parent1[:point] + parent2[point:]
            child2 = parent2[:point] + parent1[point:]
            return child1, child2
        return parent1, parent2

    def _mutate(self, individual):
        """Mutates an individual by changing one gene."""
        for i in range(self.chromosome_length):
            if random.random() < MUTATION_RATE:
                individual[i] = random.randint(GENE_MIN, GENE_MAX)
        return individual

    def get_metrics_for_individual(self, individual):
        """
        A helper function that runs a simulation for a single individual
        and returns the full metrics dictionary from parse_tripinfo.
        """
        # 1. Generate the traffic light file for this specific individual
        tls_file = os.path.join(self.sumo_dir, "city.add.xml")
        generate_tls_file(
            tls_file, 
            self.tls_intersections, 
            individual, 
            self.config["yellow_phase_duration"],
            self.config["all_red_duration"]
        )

        # 2. Generate the SUMO config to use this TLS file
        config_file = os.path.join(self.sumo_dir, "city.sumocfg")
        generate_sumo_config(config_file, self.net_file, self.route_file, additional_files=[tls_file])

        # 3. Run the simulation
        sumo_cmd = ["sumo", "-c", config_file, 
                    "--tripinfo-output", self.tripinfo_output,
                    "--junction-taz",
                    "--no-warnings", "true",
                    "--no-step-log", "true"]
        
        traci.start(sumo_cmd)
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
        traci.close()

        # 4. Parse and return the results dictionary
        return parse_tripinfo(self.tripinfo_output, self.config["simulation_time"])

    def run(self):
        """Runs the main genetic algorithm loop."""
        # 1. Initialization
        population = [self._create_individual() for _ in range(POPULATION_SIZE)]
        best_overall_individual = None
        best_overall_fitness = -1

        print("\nStarting Genetic Algorithm Optimization...")
        
        for generation in range(N_GENERATIONS):
            print(f"\n--- Generation {generation + 1}/{N_GENERATIONS} ---")
            
            # 2. Evaluation
            fitnesses = [self._run_simulation_for_fitness(ind) for ind in population]
            
            # Keep track of the best individual found so far
            current_best_fitness = max(fitnesses)
            if current_best_fitness > best_overall_fitness:
                best_overall_fitness = current_best_fitness
                best_overall_individual = population[fitnesses.index(current_best_fitness)]

            print(f"  Best fitness in this generation: {current_best_fitness:.4f}")
            print(f"  Best overall individual so far: {best_overall_individual}")

            # 3. Evolution
            next_population = []
            # Elitism: Keep the best individual from the last generation
            best_index = fitnesses.index(max(fitnesses))
            next_population.append(population[best_index])

            while len(next_population) < POPULATION_SIZE:
                # Selection
                parent1, parent2 = self._selection(population, fitnesses)
                # Crossover
                child1, child2 = self._crossover(parent1, parent2)
                # Mutation
                next_population.append(self._mutate(child1))
                if len(next_population) < POPULATION_SIZE:
                    next_population.append(self._mutate(child2))
            
            population = next_population

        print("\nGA Optimization Finished.")
        print(f"Best solution found: {best_overall_individual}")
        print(f"   - Fitness Score: {best_overall_fitness:.4f}")
        
        return best_overall_individual