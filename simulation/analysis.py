# simulation/analysis.py

import os
import csv
from datetime import datetime
import xml.etree.ElementTree as ET

RESULTS_CSV = "results.csv"

def parse_tripinfo(tripinfo_file, simulation_time):
    """Parses tripinfo.xml and returns a dictionary of metrics."""
    tree = ET.parse(tripinfo_file)
    root = tree.getroot()
    travel_times = [float(trip.get('duration')) for trip in root.findall('tripinfo')]
    wait_times = [float(trip.get('timeLoss')) for trip in root.findall('tripinfo')]
    
    if not travel_times: return None

    num_completed = len(travel_times)
    metrics = {
        "completed_vehicles": num_completed,
        "avg_travel_time": sum(travel_times) / num_completed,
        "avg_wait_time": sum(wait_times) / num_completed,
        "throughput_vpm": num_completed / (simulation_time / 60.0),
        "total_system_wait_time": num_completed * (sum(wait_times) / num_completed)
    }
    return metrics

def log_results(metrics, scale_factor, run_type):
    """Appends a row of results to the main CSV log file."""
    file_exists = os.path.isfile(RESULTS_CSV)
    
    with open(RESULTS_CSV, 'a', newline='') as f:
        fieldnames = ['timestamp', 'run_type', 'scale_factor', 'completed_vehicles', 'avg_travel_time', 'avg_wait_time', 'throughput_vpm', 'total_system_wait_time']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        # Prepare the data row
        row = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'run_type': run_type,
            'scale_factor': scale_factor,
            'completed_vehicles': metrics['completed_vehicles'],
            'avg_travel_time': f"{metrics['avg_travel_time']:.2f}",
            'avg_wait_time': f"{metrics['avg_wait_time']:.2f}",
            'throughput_vpm': f"{metrics['throughput_vpm']:.2f}",
            'total_system_wait_time': f"{metrics['total_system_wait_time']:.2f}"
        }
        writer.writerow(row)

    print(f"✅ Results logged to {RESULTS_CSV}")