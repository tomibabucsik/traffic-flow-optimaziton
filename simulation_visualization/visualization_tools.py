from matplotlib.collections import LineCollection
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import networkx as nx
import numpy as np
import os
        

def generate_traffic_report(simulation, vehicles, duration, output_file=None):
    """Generate a comprehensive traffic report with statistics and visualizations"""
    total_vehicles = len(vehicles)
    completed_trips = sum(1 for v in vehicles if v.get("current_position") == v["route"][-1])
    avg_travel_time = sum(
        simulation.simulation_time - v["entry_time"] for v in vehicles 
        if v.get("current_position") == v["route"][-1]
    ) / max(1, completed_trips)
    
    avg_speeds = []
    for v in vehicles:
        if v.get("current_position") == v["route"][-1] and v.get("entry_time", 0) < simulation.simulation_time:
            travel_time = simulation.simulation_time - v["entry_time"]
            if travel_time > 0:
                distance = sum(
                    simulation.city_graph[u][v]["length"] 
                    for u, v in zip(v["route"][:-1], v["route"][1:])
                )
                avg_speeds.append(distance / travel_time)
    avg_speed = sum(avg_speeds) / max(1, len(avg_speeds)) if avg_speeds else 0
    
    report = [
        "================================",
        "TRAFFIC SIMULATION REPORT",
        "================================",
        f"Simulation duration: {duration} seconds",
        f"Total vehicles: {total_vehicles}",
        f"Completed trips: {completed_trips} ({completed_trips/max(1, total_vehicles)*100:.1f}%)",
        f"Vehicles still in transit: {total_vehicles - completed_trips}",
        f"Average travel time: {avg_travel_time:.2f} seconds",
        f"Average speed: {avg_speed:.2f} meters/second",
        f"Traffic light cycles: {simulation.traffic_light_cycles}",
        "",
        "ROUTE ANALYSIS",
        "--------------------------------"
    ]
    
    route_counts = {}
    for vehicle in vehicles:
        if "route" in vehicle:
            route_key = f"{vehicle['route'][0]} → {vehicle['route'][-1]}"
            route_counts[route_key] = route_counts.get(route_key, 0) + 1
    
    for route, count in sorted(route_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
        report.append(f"{route}: {count} vehicles ({count/total_vehicles*100:.1f}%)")
    
    report_str = "\n".join(report)
    print(report_str)
    
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_str)
            print(f"Report saved to {output_file}")
        except IOError as e:
            print(f"Failed to save report: {e}")
    
    return report_str