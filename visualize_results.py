# visualize_results.py

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def plot_metric(ax, data, metric, title, y_label):
    """Helper function to plot a single metric on a given axis."""
    data.plot(kind='bar', ax=ax, color=['#1f77b4', '#ff7f0e'], width=0.8)
    ax.set_title(title, fontsize=14)
    ax.set_ylabel(y_label, fontsize=10)
    ax.set_xlabel('')
    ax.tick_params(axis='x', rotation=0)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.legend()

    # Add labels on top of the bars
    for p in ax.patches:
        ax.annotate(f"{p.get_height():.1f}", 
                    (p.get_x() + p.get_width() / 2., p.get_height()), 
                    ha='center', va='center', xytext=(0, 9), textcoords='offset points')

def create_dashboard(csv_file='results.csv'):
    """
    Reads all experiment results and generates a 2x2 dashboard of charts.
    """
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        print(f"Error: The file '{csv_file}' was not found.")
        return

    # Prepare the data
    df_fixed = df[df['run_type'] == 'fixed'].groupby('scale_factor').last()
    df_optimized = df[df['run_type'] == 'optimized'].groupby('scale_factor').last()

    # --- Create the 2x2 Subplot Grid ---
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Genetic Algorithm Performance Dashboard', fontsize=20)
    
    # 1. Total System Wait Time (Overall Congestion)
    wait_time_data = pd.DataFrame({
        'Fixed': df_fixed['total_system_wait_time'],
        'Optimized': df_optimized['total_system_wait_time']
    }).dropna()
    plot_metric(axes[0, 0], wait_time_data, 'total_system_wait_time', 'Overall Congestion', 'Total Wait Time (s)')

    # 2. Throughput (Network Efficiency)
    throughput_data = pd.DataFrame({
        'Fixed': df_fixed['completed_vehicles'],
        'Optimized': df_optimized['completed_vehicles']
    }).dropna()
    plot_metric(axes[0, 1], throughput_data, 'completed_vehicles', 'Network Efficiency', 'Completed Vehicles')

    # 3. Std. Dev. of Wait Time (Fairness)
    fairness_data = pd.DataFrame({
        'Fixed': df_fixed['std_dev_wait_time'],
        'Optimized': df_optimized['std_dev_wait_time']
    }).dropna()
    plot_metric(axes[1, 0], fairness_data, 'std_dev_wait_time', 'Fairness of Service', 'Std. Dev. of Wait Time (s)')

    # 4. Total CO2 Emissions (Environmental Impact)
    emissions_data = pd.DataFrame({
        'Fixed': df_fixed['total_co2_emissions'],
        'Optimized': df_optimized['total_co2_emissions']
    }).dropna()
    plot_metric(axes[1, 1], emissions_data, 'total_co2_emissions', 'Environmental Impact', 'Total CO₂ Emissions (g)')

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    output_filename = 'ga_performance_dashboard.png'
    plt.savefig(output_filename)
    print(f"\nDashboard chart saved as '{output_filename}'")
    
    plt.show()

if __name__ == '__main__':
    create_dashboard()