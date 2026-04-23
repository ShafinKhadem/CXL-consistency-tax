import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Load data
df = pd.read_csv("parsec.csv")

# Convert ROI_Time(s) to microseconds
df["ROI_Time_us"] = df["ROI_Time(s)"] * 1e6

# Create a column for the group labels
df["Config"] = df.apply(
    lambda row: f"TSO={row['TSO']}, Precise={row['precise_exceptions']}{', double_lsq=True' if row['double_lsq'] else ''}",
    axis=1,
)

# Get unique experiments and configs
experiments = df["Experiment"].unique()

# Add new config for double_lsq
configs = [
    "TSO=False, Precise=False",
    "TSO=True, Precise=False",
    "TSO=True, Precise=False, double_lsq=True",
    "TSO=False, Precise=True",
    "TSO=True, Precise=True",
    "TSO=True, Precise=True, double_lsq=True"
]
colors = ["C0", "C1", "C4", "C2", "C3"]

# Plot each experiment in its own subplot
fig, axes = plt.subplots(
    1,
    len(experiments),
    figsize=(2.5 * len(experiments), 3),
    sharey=False,
    layout="constrained",
)
if len(experiments) == 1:
    axes = [axes]


bar_handles = []
for i, (ax, exp) in enumerate(zip(axes, experiments)):
    exp_data = df[df["Experiment"] == exp]
    roi_times = []
    for config in configs:
        match = exp_data[exp_data["Config"] == config]
        if not match.empty:
            roi_times.append(match["ROI_Time_us"].values[0])
        else:
            roi_times.append(0)  # Or np.nan if you want to leave a gap
    bars = ax.bar(configs, roi_times, color=colors)
    if i == 0:
        bar_handles = bars  # Save handles from the first subplot
    ax.set_xticks([])
    ax.set_xticklabels([])
    ax.set_title(exp)
    ax.set_ylabel("ROI Time (μs)")
    ymin = 0
    ymax = max(roi_times) * 1.15
    ax.set_ylim(ymin, ymax)


fig.legend(
    bar_handles,
    [
        "ARM",
        "ARM + TSO",
        "ARM + TSO (double LSQ)",
        "ARM + Precise exceptions",
        "ARM + TSO + Precise exceptions",
        "ARM + TSO + Precise exceptions (double LSQ)",
    ],
    title="Configurations",
    loc="outside right upper",
)

# plt.tight_layout()
plt.show()
