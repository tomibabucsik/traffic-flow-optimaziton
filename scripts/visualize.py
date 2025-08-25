import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import argparse
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scenarios import SCENARIOS
from city_modeling.builder import setup_grid_city, setup_arterial_road
from city_modeling.graph_visualization import GraphVisualization

def plot_comparison(ax, data, metric, title, y_label):
    """Helper function to plot a comparison bar chart for a single metric."""
    colors = {'fixed': '#1f77b4', 'optimized': '#ff7f0e', 'adaptive': '#2ca02c'}
    
    plot_colors = [colors[col] for col in data.columns if col in colors]

    data.plot(kind='bar', ax=ax, width=0.8, color=plot_colors)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_ylabel(y_label, fontsize=10)
    ax.set_xlabel('Algorithm Type', fontsize=10)
    ax.tick_params(axis='x', rotation=0, labelsize=10)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.legend(data.columns)

    for p in ax.patches:
        ax.annotate(f"{p.get_height():.1f}",
                    (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='center', xytext=(0, 9), textcoords='offset points', fontsize=9)

def create_dashboard(csv_file='output/results.csv'):
    """
    Reads the final, clean results and generates a comprehensive dashboard
    comparing all algorithms across all scenarios.
    """
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        print(f"Error: The file '{csv_file}' was not found. Please run the test suites first.")
        return

    scenarios = df['scenario_name'].unique()
    
    fig, axes = plt.subplots(len(scenarios), 2, figsize=(16, 6 * len(scenarios)), squeeze=False)
    fig.suptitle('Performance Comparison', fontsize=24, fontweight='bold')

    for i, scenario in enumerate(scenarios):
        scenario_df = df[df['scenario_name'] == scenario]
        
        # Group all run types at once
        last_runs = scenario_df.groupby(['scale_factor', 'run_type']).last().unstack()
        
        wait_time_data = last_runs['total_system_wait_time'][['fixed', 'optimized', 'adaptive']].dropna(how='all')
        plot_comparison(axes[i, 0], wait_time_data, 'total_system_wait_time', f'{scenario}: Overall Congestion', 'Total Wait Time (s)')

        travel_time_data = last_runs['avg_travel_time'][['fixed', 'optimized', 'adaptive']].dropna(how='all')
        plot_comparison(axes[i, 1], travel_time_data, 'avg_travel_time', f'{scenario}: Vehicle Experience', 'Average Travel Time (s)')

    plt.tight_layout(rect=[0, 0.03, 1, 0.96])
    
    output_filename = 'output/performance_dashboard.png'
    plt.savefig(output_filename)
    print(f"\nDashboard chart saved as '{output_filename}'")
    
    plt.show()

def plot_evolution(csv_file='output/results.csv'):
    try:
        df = pd.read_csv(csv_file)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    except FileNotFoundError:
        return
    SCALE_TO_PLOT = 6.0 
    df_filtered = df[(df['run_type'] == 'optimized') & (df['scale_factor'] == SCALE_TO_PLOT)].sort_values('timestamp')
    if len(df_filtered) < 2:
        return
    stages = ['1. Initial GA (5 Gens)', '2. Increased Gens (20 Gens)', '3. Multi-Objective Fitness', '4. Tuned Mutation Rate (0.3)']
    stages = stages[:len(df_filtered)]
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(stages, df_filtered['total_system_wait_time'], marker='o', linestyle='-', color='#2ca02c', markersize=10, label='Total System Wait Time')
    for i, txt in enumerate(df_filtered['total_system_wait_time']):
        ax.annotate(f'{txt:.2f}s', (stages[i], df_filtered['total_system_wait_time'].iloc[i]), textcoords="offset points", xytext=(0,10), ha='center', fontsize=12)
    ax.set_title(f'Evolution of GA Performance at High Congestion (Scale {SCALE_TO_PLOT})', fontsize=18, fontweight='bold')
    ax.set_ylabel('Total System Wait Time (s)', fontsize=14)
    ax.set_xlabel('GA Development Stage', fontsize=14)
    ax.tick_params(axis='x', rotation=15, labelsize=10)
    ax.set_ylim(bottom=0, top=max(df_filtered['total_system_wait_time']) * 1.1)
    output_filename = f'output/ga_evolution_chart_scale_{SCALE_TO_PLOT}.png'
    plt.tight_layout()
    plt.savefig(output_filename)
    print(f"\nGA evolution chart saved as '{output_filename}'")
    plt.show()

MAP_BUILDERS = {"setup_grid_city": setup_grid_city, "setup_arterial_road": setup_arterial_road}
def visualize_scenario_map(scenario_name):
    if scenario_name not in SCENARIOS:
        return
    scenario = SCENARIOS[scenario_name]
    if scenario.get("type") == "generated":
        print(f"--- Visualizing map for scenario: {scenario_name} ---")
        map_builder_func = MAP_BUILDERS[scenario['map_builder']]
        map_args = scenario['map_config']
        city_graph_obj, _, _ = map_builder_func(**map_args)
        visualizer = GraphVisualization(city_graph_obj)
        visualizer.draw_city_graph()
        print("Plot window opened. Close the plot to exit.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Visualization tools for the traffic optimization project.")
    parser.add_argument("tool", choices=['dashboard', 'evolution', 'map'], help="The visualization tool to run.")
    parser.add_argument("--scenario", help="The scenario name (required for 'map' tool).")
    args = parser.parse_args()

    if args.tool == 'dashboard':
        create_dashboard()
    elif args.tool == 'evolution':
        plot_evolution()
    elif args.tool == 'map':
        if not args.scenario:
            print("Error: --scenario is required when using the 'map' tool.")
        else:
            visualize_scenario_map(args.scenario)