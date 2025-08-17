# plot_ga_evolution.py

import pandas as pd
import matplotlib.pyplot as plt

def plot_evolution(csv_file='results/results.csv'):
    """
    Reads the results CSV and plots the evolution of the GA's performance
    at a specified traffic scale across different development stages.
    """
    try:
        df = pd.read_csv(csv_file)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    except FileNotFoundError:
        print(f"Error: The file '{csv_file}' was not found.")
        return

    # --- Configuration ---
    # Change this value to plot the evolution for a different traffic scale
    SCALE_TO_PLOT = 6.0 
    # -------------------

    df_filtered = df[
        (df['run_type'] == 'optimized') & (df['scale_factor'] == SCALE_TO_PLOT)
    ].sort_values('timestamp')

    if len(df_filtered) < 2:
        print(f"Not enough data points to plot evolution for scale {SCALE_TO_PLOT}.")
        return

    # Define the stages of your GA development based on your commits
    stages = [
        '1. Initial GA (5 Gens)',
        '2. Increased Gens (20 Gens)',
        '3. Multi-Objective Fitness',
        '4. Tuned Mutation Rate (0.3)'
    ]
    
    # Ensure we only use as many labels as we have data points
    stages = stages[:len(df_filtered)]

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 7))

    # Plot the performance over time
    ax.plot(stages, df_filtered['total_system_wait_time'], marker='o', linestyle='-', color='#2ca02c', markersize=10, label='Total System Wait Time')

    # Add data labels to each point
    for i, txt in enumerate(df_filtered['total_system_wait_time']):
        ax.annotate(f'{txt:.2f}s', (stages[i], df_filtered['total_system_wait_time'].iloc[i]),
                    textcoords="offset points", xytext=(0,10), ha='center', fontsize=12)

    # Formatting the plot
    ax.set_title(f'Evolution of GA Performance at High Congestion (Scale {SCALE_TO_PLOT})', fontsize=18, fontweight='bold')
    ax.set_ylabel('Total System Wait Time (s)', fontsize=14)
    ax.set_xlabel('GA Development Stage', fontsize=14)
    ax.tick_params(axis='x', rotation=15, labelsize=10)
    ax.set_ylim(bottom=0, top=max(df_filtered['total_system_wait_time']) * 1.1)
    
    output_filename = f'ga_evolution_chart_scale_{SCALE_TO_PLOT}.png'
    plt.tight_layout()
    plt.savefig(output_filename)
    print(f"\nGA evolution chart saved as '{output_filename}'")
    
    plt.show()


if __name__ == '__main__':
    plot_evolution()
