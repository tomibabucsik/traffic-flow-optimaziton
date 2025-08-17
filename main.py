# main.py

import argparse
from config import CONFIG
from simulation.run import run_fixed_experiment, run_viewer, run_ga_experiment

def main():
    parser = argparse.ArgumentParser(description="Run Traffic Flow Optimization Experiments.")
    
    parser.add_argument(
        "--run-type", 
        type=str, 
        default="fixed", 
        choices=["fixed", "optimized", "view"],
        help="Type of simulation to run"
    )
    
    parser.add_argument(
        "--scale", 
        type=float, 
        default=1.0, 
        help="Traffic scale multiplier."
    )
    
    args = parser.parse_args()

    print(f"Starting experiment: Run Type='{args.run_type}', Traffic Scale={args.scale}x")

    if args.run_type == "fixed":
        run_fixed_experiment(CONFIG, args.scale, args.run_type)
    
    elif args.run_type == "optimized":
        run_ga_experiment(CONFIG, args.scale, args.run_type)
    
    elif args.run_type == "view":
        run_viewer(CONFIG, args.scale)

if __name__ == "__main__":
    main()