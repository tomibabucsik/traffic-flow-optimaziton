import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

CSV = "output/results.csv"
OUTDIR = "output/diagnostics"
os.makedirs(OUTDIR, exist_ok=True)

df = pd.read_csv(CSV, parse_dates=['timestamp'])

df4 = df[df['scenario_name'] == '4x4_grid'].copy()
df4['scale_factor'] = df4['scale_factor'].astype(float)

summary = df4.groupby(['run_type','scale_factor']).agg(
    completed=('completed_vehicles','sum'),
    avg_travel_time_mean=('avg_travel_time','mean'),
    avg_travel_time_median=('avg_travel_time','median'),
    avg_wait_time_mean=('avg_wait_time','mean'),
    avg_wait_time_median=('avg_wait_time','median'),
    total_system_wait=('total_system_wait_time','sum'),
    throughput_vpm_mean=('throughput_vpm','mean'),
).reset_index()
print("=== Aggregated summary (4x4_grid) ===")
print(summary.to_string(index=False))

plt.figure(figsize=(8,5))
sns.lineplot(data=df4, x='scale_factor', y='avg_travel_time', hue='run_type', marker='o', estimator='mean', ci=None)
sns.lineplot(data=df4, x='scale_factor', y='avg_travel_time', hue='run_type', marker='X', estimator='median', ci=None, legend=False)
plt.title('4x4_grid: Average Travel Time (mean and median)')
plt.ylabel('Avg Travel Time (s)')
plt.xlabel('Scale Factor')
plt.grid(True)
plt.savefig(os.path.join(OUTDIR, '4x4_avg_travel_time_mean_median.png'), dpi=200)
plt.close()

plt.figure(figsize=(8,5))
sns.lineplot(data=df4, x='scale_factor', y='avg_wait_time', hue='run_type', marker='o', estimator='mean', ci=None)
sns.lineplot(data=df4, x='scale_factor', y='avg_wait_time', hue='run_type', marker='X', estimator='median', ci=None, legend=False)
plt.title('4x4_grid: Avg Wait Time (mean and median)')
plt.ylabel('Avg Wait Time (s)')
plt.xlabel('Scale Factor')
plt.grid(True)
plt.savefig(os.path.join(OUTDIR, '4x4_avg_wait_time_mean_median.png'), dpi=200)
plt.close()

fig, ax1 = plt.subplots(figsize=(8,5))
sns.lineplot(data=df4, x='scale_factor', y='throughput_vpm', hue='run_type', marker='o', ax=ax1, ci=None)
ax1.set_ylabel('Throughput (vpm)')
ax1.set_xlabel('Scale Factor')
ax1.grid(True)
plt.title('4x4_grid: Throughput by Run Type')
plt.savefig(os.path.join(OUTDIR, '4x4_throughput.png'), dpi=200)
plt.close()

plt.figure(figsize=(8,5))
sns.lineplot(data=df4, x='scale_factor', y='total_system_wait_time', hue='run_type', marker='o', estimator='sum', ci=None)
plt.title('4x4_grid: Total System Wait Time (sum)')
plt.ylabel('Total System Wait (s)')
plt.xlabel('Scale Factor')
plt.grid(True)
plt.savefig(os.path.join(OUTDIR, '4x4_total_wait_sum.png'), dpi=200)
plt.close()

print(f"Diagnostic plots saved to {OUTDIR}")
