import itertools

import matplotlib.pyplot as plt
import pandas as pd

# 1. Match your LaTeX document font size (e.g., 11pt)
FONT_SIZE = 11

plt.rcParams.update(
    {
        "font.size": FONT_SIZE,  # Global font size
        "axes.labelsize": FONT_SIZE,  # x and y labels
        "axes.titlesize": FONT_SIZE,  # Title
        "xtick.labelsize": FONT_SIZE,  # x-axis ticks
        "ytick.labelsize": FONT_SIZE,  # y-axis ticks
        "legend.fontsize": FONT_SIZE,  # Legend
        "figure.titlesize": FONT_SIZE,  # Suptitle
    }
)

# Load data
df = pd.read_csv("rw_ratio_bench.csv")

# Filter for lq_size == sq_size
df = df[df["lq_size"] == df["sq_size"]]

# Prepare subplots
fig, axes = plt.subplots(2, 2, figsize=(8, 6.5))


precise_exceptions_values = [False, True]
tso_values = [False, True]
titles = [
    "ARM",
    "ARM + TSO",
    "ARM + Precise Exceptions",
    "ARM + TSO + Precise Exceptions",
]

for ax, (precise_exceptions, tso), title in zip(
    axes.flat, itertools.product(precise_exceptions_values, tso_values), titles
):
    subset = df[(df["TSO"] == tso) & (df["precise_exceptions"] == precise_exceptions)]
    for write_ratio in sorted(subset["write_ratio"].unique()):
        data = subset[subset["write_ratio"] == write_ratio]
        ax.plot(
            data["lq_size"],
            data["total_mops_per_s"],
            marker="o",
            label=f"Write Ratio {write_ratio}%",
        )
    ax.set_title(title)
    ax.set_xlabel("LQ/SQ Size")
    ax.set_ylabel("Throughput (Mops/s)")  # Always set y-label
    ax.legend(loc="lower right")
    # Set x-axis ticks to the actual LQ/SQ values
    ax.set_xticks([8, 16, 32, 64, 128])

# Set the same y-axis limits for all subplots for visual consistency
all_y = df["total_mops_per_s"]
ymin, ymax = all_y.min(), all_y.max()
margin = 0.05 * (ymax - ymin)
for ax in axes.flat:
    ax.set_ylim(ymin, ymax + margin)

plt.tight_layout()
plt.show()
