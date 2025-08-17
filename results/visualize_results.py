import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def plot_metric(ax, data, metric, title, y_label):
    """Helper function to plot a single metric on a given axis."""
    # Grouped bar chart requires a specific data format
    data.plot(kind='bar', ax=ax, color=['#1f77b4', '#ff7f0e'], width=0.6)
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_ylabel(y_label, fontsize=12)
    ax.set_xlabel('Traffic Scale Factor', fontsize=12)
    ax.tick_params(axis='x', rotation=0, labelsize=10)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.legend(['Fixed Timings', 'GA Optimized'])

    # Add labels on top of the bars for clarity
    for p in ax.patches:
        ax.annotate(f"{p.get_height():.2f}",
                    (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='center',
                    xytext=(0, 9),
                    textcoords='offset points',
                    fontsize=10)

def create_dashboard(csv_file='results/results.csv'):
    """
    Reads all experiment results and generates a 2x1 dashboard of charts.
    """
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        print(f"Error: The file '{csv_file}' was not found.")
        return

    # Prepare the data: get the last run for each type and scale
    df_fixed = df[df['run_type'] == 'fixed'].groupby('scale_factor').last()
    df_optimized = df[df['run_type'] == 'optimized'].groupby('scale_factor').last()

    # --- Create the 2x1 Subplot Grid ---
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.suptitle('Genetic Algorithm vs. Fixed Timings Performance Dashboard', fontsize=22, fontweight='bold')

    # 1. Total System Wait Time (Overall Congestion)
    wait_time_data = pd.DataFrame({
        'Fixed': df_fixed['total_system_wait_time'],
        'Optimized': df_optimized['total_system_wait_time']
    }).dropna()
    plot_metric(axes[0], wait_time_data, 'total_system_wait_time', 'Overall Congestion', 'Total System Wait Time (s)')

    # 2. Average Travel Time (Vehicle Experience)
    avg_travel_time_data = pd.DataFrame({
        'Fixed': df_fixed['avg_travel_time'],
        'Optimized': df_optimized['avg_travel_time']
    }).dropna()
    plot_metric(axes[1], avg_travel_time_data, 'avg_travel_time', 'Average Vehicle Experience', 'Average Travel Time (s)')

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    
    output_filename = 'ga_performance_dashboard.png'
    plt.savefig(output_filename)
    print(f"\nDashboard chart saved as '{output_filename}'")
    
    plt.show()

if __name__ == '__main__':
    create_dashboard()