import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import argparse

def create_dashboard(csv_file='output/results.csv', output_filename='output/performance_dashboard.png'):
    """
    Reads simulation results and generates:
      1. A main comparison dashboard (2xN grid for Total Wait Time and Avg Travel Time)
      2. A multi-panel line chart per scenario showing metric trends across scale factors.
    """

    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        print(f"Error: The file '{csv_file}' was not found.")
        return

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    latest_runs_df = df.drop_duplicates(subset=['scenario_name', 'run_type', 'scale_factor'], keep='last')

    scenarios = latest_runs_df['scenario_name'].unique()
    algo_order = ['fixed', 'reactive', 'adaptive', 'optimized']
    present_algos = [a for a in algo_order if a in latest_runs_df['run_type'].unique()]

    plt.style.use('seaborn-v0_8-whitegrid')
    sns.set_palette("Set2")

    fig, axes = plt.subplots(len(scenarios), 2, figsize=(18, 7 * len(scenarios)), squeeze=False)

    for i, scenario in enumerate(scenarios):
        scenario_df = latest_runs_df[latest_runs_df['scenario_name'] == scenario]

        ax1 = axes[i, 0]
        metric1 = 'total_system_wait_time'
        pivot1 = scenario_df.pivot_table(index='run_type', columns='scale_factor', values=metric1).reindex(present_algos)
        pivot1.plot(kind='bar', ax=ax1, width=0.8)
        ax1.set_title(f'{scenario}: Overall Congestion', fontsize=16, fontweight='bold')
        ax1.set_ylabel('Total System Wait Time (s)', fontsize=12)
        ax1.set_xlabel('')
        ax1.tick_params(axis='x', rotation=0, labelsize=12)
        if ax1.get_legend():
            ax1.get_legend().remove()

        ax2 = axes[i, 1]
        metric2 = 'avg_travel_time'
        pivot2 = scenario_df.pivot_table(index='run_type', columns='scale_factor', values=metric2).reindex(present_algos)
        pivot2.plot(kind='bar', ax=ax2, width=0.8)
        ax2.set_title(f'{scenario}: Vehicle Experience', fontsize=16, fontweight='bold')
        ax2.set_ylabel('Average Travel Time (s)', fontsize=12)
        ax2.set_xlabel('')
        ax2.tick_params(axis='x', rotation=0, labelsize=12)
        if ax2.get_legend():
            ax2.get_legend().remove()

        for ax, pivot_df in [(ax1, pivot1), (ax2, pivot2)]:
            num_algos = len(pivot_df.index)
            for patch_index, bar in enumerate(ax.patches):
                height = bar.get_height()
                if np.isnan(height):
                    continue
                ax.annotate(f'{height:.0f}',
                            xy=(bar.get_x() + bar.get_width()/2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=9, fontweight='bold')

                scale_index = patch_index // num_algos
                algo_index = patch_index % num_algos
                current_algo = pivot_df.index[algo_index]
                current_scale = pivot_df.columns[scale_index]

                if current_algo != 'fixed' and 'fixed' in pivot_df.index:
                    baseline_value = pivot_df.loc['fixed', current_scale]
                    if pd.notna(baseline_value) and baseline_value > 0:
                        improvement = ((height - baseline_value) / baseline_value) * 100
                        color = '#2ca02c' if improvement < 0 else '#d62728'
                        sign = '' if improvement < 0 else '+'
                        ax.annotate(f'({sign}{improvement:.1f}%)',
                                    xy=(bar.get_x() + bar.get_width()/2, height),
                                    xytext=(0, -15),
                                    textcoords="offset points",
                                    ha='center', va='bottom', fontsize=8, color=color)

    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, [f"{float(l):.1f}x" for l in labels], loc='upper center',
               bbox_to_anchor=(0.5, 1.0), ncol=len(labels), fontsize=14, title='Traffic Scale Factor')
    fig.suptitle('Algorithm Performance Dashboard', fontsize=24, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.95])

    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
    plt.savefig(output_filename, bbox_inches='tight', dpi=300)
    print(f"\tDashboard saved as '{output_filename}'")

    metrics = ['avg_travel_time', 'avg_wait_time', 'throughput_vpm', 'total_system_wait_time']
    metric_titles = {
        'avg_travel_time': 'Average Travel Time (s)',
        'avg_wait_time': 'Average Wait Time (s)',
        'throughput_vpm': 'Throughput (vehicles/min)',
        'total_system_wait_time': 'Total System Wait Time (s)'
    }

    line_output_dir = os.path.join(os.path.dirname(output_filename), 'metric_trends')
    os.makedirs(line_output_dir, exist_ok=True)

    for scenario in scenarios:
        scenario_df = latest_runs_df[latest_runs_df['scenario_name'] == scenario]
        fig, axs = plt.subplots(2, 2, figsize=(14, 10))
        axs = axs.flatten()

        for j, metric in enumerate(metrics):
            sns.lineplot(
                data=scenario_df,
                x='scale_factor',
                y=metric,
                hue='run_type',
                style='run_type',
                markers=True,
                dashes=False,
                ax=axs[j]
            )
            axs[j].set_title(f"{metric_titles[metric]}", fontsize=14, fontweight='bold')
            axs[j].set_xlabel("Scale Factor")
            axs[j].set_ylabel(metric_titles[metric])
            axs[j].grid(True, alpha=0.3)
            axs[j].legend(title='Run Type', fontsize=10)

        plt.suptitle(f"{scenario}: Metric Trends", fontsize=20, fontweight='bold')
        plt.tight_layout(rect=[0, 0, 1, 0.95])

        scenario_plot_path = os.path.join(line_output_dir, f"{scenario}_metric_trends.png")
        plt.savefig(scenario_plot_path, dpi=300)
        plt.close()
        print(f"Saved multi-panel trend plot: {scenario_plot_path}")

    print("\nAll scenario trend plots saved successfully.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate a performance dashboard from simulation results.")
    parser.add_argument('--csv_file', type=str, default='output/results.csv', help="Path to the input results CSV file.")
    parser.add_argument('--output_file', type=str, default='output/performance_dashboard.png', help="Path to save the output dashboard image.")
    args = parser.parse_args()

    create_dashboard(csv_file=args.csv_file, output_filename=args.output_file)
    plt.show()
