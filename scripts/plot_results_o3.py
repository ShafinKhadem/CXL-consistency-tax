"""Generate heatmaps and line plots from O3 fence sweep results."""

import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

BASE = "/home/hasanat/abrar/cxl_tax"
RESULTS = f"{BASE}/results"

df = pd.read_csv(f"{RESULTS}/fence_sweep_o3_summary.csv")

# Compute slowdown relative to baseline (L=40ns, BW=100GiB/s)
baseline = df[(df["latency"] == "40ns") & (df["bandwidth"] == "100GiB/s")]
baseline_map = baseline.set_index("fence_freq")["simSeconds"].to_dict()
df["slowdown"] = df.apply(
    lambda r: r["simSeconds"] / baseline_map.get(r["fence_freq"], 1.0), axis=1
)
df.to_csv(f"{RESULTS}/fence_sweep_o3_with_slowdown.csv", index=False)

lat_order = ["40ns", "80ns", "160ns", "300ns", "400ns"]
bw_order = ["100GiB/s", "50GiB/s", "25GiB/s", "12.5GiB/s"]

# --- Heatmaps ---
for k in [1, 16, 256]:
    subset = df[df["fence_freq"] == k].copy()
    subset["latency"] = pd.Categorical(subset["latency"], categories=lat_order, ordered=True)
    subset["bandwidth"] = pd.Categorical(subset["bandwidth"], categories=bw_order, ordered=True)
    pivot = subset.pivot(index="latency", columns="bandwidth", values="slowdown")

    plt.figure(figsize=(8, 5))
    sns.heatmap(pivot, annot=True, fmt=".2f", cmap="YlOrRd")
    plt.title(f"O3CPU: Slowdown vs. baseline — fence every {k} stores")
    plt.xlabel("Bandwidth")
    plt.ylabel("Latency")
    plt.tight_layout()
    plt.savefig(f"{RESULTS}/o3_heatmap_K{k}.png", dpi=150)
    plt.close()

# --- Line plot: slowdown vs fence frequency per latency (BW=25GiB/s) ---
plt.figure(figsize=(9, 6))
for lat in lat_order:
    sub = df[(df["latency"] == lat) & (df["bandwidth"] == "25GiB/s")].sort_values("fence_freq")
    plt.plot(sub["fence_freq"], sub["slowdown"], marker="o", label=lat, linewidth=2)
plt.xlabel("Fence Frequency (every K stores)")
plt.ylabel("Slowdown vs. baseline")
plt.title("O3CPU: Consistency Tax vs. Fence Frequency (BW=25GiB/s)")
plt.xscale("log")
plt.legend(title="Memory Latency")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f"{RESULTS}/o3_slowdown_vs_fence_freq.png", dpi=150)
plt.close()

# --- Line plot: slowdown vs latency per K (BW=25GiB/s) ---
lat_ns = {"40ns": 40, "80ns": 80, "160ns": 160, "300ns": 300, "400ns": 400}
plt.figure(figsize=(9, 6))
for k in [1, 4, 16, 64, 256]:
    sub = df[(df["fence_freq"] == k) & (df["bandwidth"] == "25GiB/s")].copy()
    sub["lat_ns"] = sub["latency"].map(lat_ns)
    sub = sub.sort_values("lat_ns")
    plt.plot(sub["lat_ns"], sub["slowdown"], marker="s", label=f"K={k}", linewidth=2)
plt.xlabel("Memory Latency (ns)")
plt.ylabel("Slowdown vs. baseline")
plt.title("O3CPU: Consistency Tax vs. Memory Latency (BW=25GiB/s)")
plt.legend(title="Fence Frequency")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f"{RESULTS}/o3_slowdown_vs_latency.png", dpi=150)
plt.close()

# --- Line plot: simSeconds vs K for 40ns vs 300ns (shows absolute cost) ---
plt.figure(figsize=(9, 6))
for lat, bw, style in [("40ns", "100GiB/s", "-"), ("300ns", "25GiB/s", "--")]:
    sub = df[(df["latency"] == lat) & (df["bandwidth"] == bw)].sort_values("fence_freq")
    plt.plot(sub["fence_freq"], sub["simSeconds"] * 1e6, marker="o", linestyle=style,
             label=f"L={lat}, BW={bw}", linewidth=2)
plt.xlabel("Fence Frequency (every K stores)")
plt.ylabel("Simulated Time (µs)")
plt.title("O3CPU: Absolute Execution Time — Local DDR vs. Far CXL")
plt.xscale("log")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f"{RESULTS}/o3_absolute_time.png", dpi=150)
plt.close()

print("All O3 plots generated.")
