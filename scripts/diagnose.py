import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

CSV = "output/results.csv"
OUTDIR = "output/diagnostics"
os.makedirs(OUTDIR, exist_ok=True)

df = pd.read_csv(CSV, parse_dates=['timestamp'])

SCENARIOS = ["4x4_grid", "arterial_road"]

for scenario in SCENARIOS:
    scenario_df = df[df['scenario_name'] == scenario].copy()
    if scenario_df.empty:
        print(f"No data found for scenario '{scenario}', skipping.")
        continue

    scenario_df['scale_factor'] = scenario_df['scale_factor'].astype(float)

    scenario_outdir = os.path.join(OUTDIR, scenario)
    os.makedirs(scenario_outdir, exist_ok=True)

    summary = scenario_df.groupby(['run_type', 'scale_factor']).agg(
        completed=('completed_vehicles', 'sum'),
        avg_travel_time_mean=('avg_travel_time', 'mean'),
        avg_travel_time_median=('avg_travel_time', 'median'),
        avg_wait_time_mean=('avg_wait_time', 'mean'),
        avg_wait_time_median=('avg_wait_time', 'median'),
        total_system_wait=('total_system_wait_time', 'sum'),
        throughput_vpm_mean=('throughput_vpm', 'mean'),
    ).reset_index()

    print(f"\n=== Aggregated Summary ({scenario}) ===")
    print(summary.to_string(index=False))

    plt.figure(figsize=(8, 5))
    sns.lineplot(data=scenario_df, x='scale_factor', y='avg_travel_time', hue='run_type',
                 marker='o', estimator='mean', errorbar=None)
    plt.title(f'{scenario}: Average Travel Time (mean)')
    plt.ylabel('Avg Travel Time (s)')
    plt.xlabel('Scale Factor')
    plt.grid(True)
    plt.savefig(os.path.join(scenario_outdir, f'{scenario}_avg_travel_time_mean.png'), dpi=200)
    plt.close()
    
    plt.figure(figsize=(8, 5))
    sns.lineplot(data=scenario_df, x='scale_factor', y='avg_travel_time', hue='run_type',
                 marker='o', estimator='mean', errorbar=None)
    sns.lineplot(data=scenario_df, x='scale_factor', y='avg_travel_time', hue='run_type',
                 marker='X', estimator='median', errorbar=None, legend=False)
    plt.title(f'{scenario}: Average Travel Time (mean and median)')
    plt.ylabel('Avg Travel Time (s)')
    plt.xlabel('Scale Factor')
    plt.grid(True)
    plt.savefig(os.path.join(scenario_outdir, f'{scenario}_avg_travel_time_mean_median_2lines.png'), dpi=200)
    plt.close()

    plt.figure(figsize=(8, 5))
    sns.lineplot(data=scenario_df, x='scale_factor', y='avg_wait_time', hue='run_type',
                 marker='o', estimator='mean', errorbar=None)
    sns.lineplot(data=scenario_df, x='scale_factor', y='avg_wait_time', hue='run_type',
                 marker='X', estimator='median', errorbar=None, legend=False)
    plt.title(f'{scenario}: Average Wait Time (mean and median)')
    plt.ylabel('Avg Wait Time (s)')
    plt.xlabel('Scale Factor')
    plt.grid(True)
    plt.savefig(os.path.join(scenario_outdir, f'{scenario}_avg_wait_time_mean_median.png'), dpi=200)
    plt.close()

    fig, ax1 = plt.subplots(figsize=(8, 5))
    sns.lineplot(data=scenario_df, x='scale_factor', y='throughput_vpm',
                 hue='run_type', marker='o', ax=ax1, errorbar=None)
    ax1.set_ylabel('Throughput (vehicles/min)')
    ax1.set_xlabel('Scale Factor')
    ax1.grid(True)
    plt.title(f'{scenario}: Throughput by Run Type')
    plt.savefig(os.path.join(scenario_outdir, f'{scenario}_throughput.png'), dpi=200)
    plt.close()

    plt.figure(figsize=(8, 5))
    sns.lineplot(data=scenario_df, x='scale_factor', y='total_system_wait_time',
                 hue='run_type', marker='o', estimator='sum', errorbar=None)
    plt.title(f'{scenario}: Total System Wait Time (sum)')
    plt.ylabel('Total System Wait (s)')
    plt.xlabel('Scale Factor')
    plt.grid(True)
    plt.savefig(os.path.join(scenario_outdir, f'{scenario}_total_wait_sum.png'), dpi=200)
    plt.close()

    print(f"Diagnostic plots saved for {scenario} in {scenario_outdir}")

print(f"\nAll diagnostics completed. Root output folder: {OUTDIR}")