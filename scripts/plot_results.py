"""Generate heatmaps and line plots from fence sweep results."""

import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for cluster
import matplotlib.pyplot as plt
import seaborn as sns

BASE = os.path.expanduser("/home/hasanat/abrar/cxl_tax")
RESULTS = f"{BASE}/results"

df = pd.read_csv(f"{RESULTS}/fence_sweep_summary.csv")

# Compute slowdown relative to baseline (L=40ns, BW=100GiB/s)
baseline = df[(df["latency"] == "40ns") & (df["bandwidth"] == "100GiB/s")]
baseline_map = baseline.set_index("fence_freq")["simSeconds"].to_dict()
df["slowdown"] = df.apply(
    lambda r: r["simSeconds"] / baseline_map.get(r["fence_freq"], 1.0), axis=1
)

# Save enriched CSV
df.to_csv(f"{RESULTS}/fence_sweep_with_slowdown.csv", index=False)

# --- Heatmaps for fixed fence frequencies ---
# Order latencies and bandwidths for sensible axis ordering
lat_order = ["40ns", "80ns", "160ns", "300ns", "400ns"]
bw_order = ["100GiB/s", "50GiB/s", "25GiB/s", "12.5GiB/s"]

for k in [1, 16, 256]:
    subset = df[df["fence_freq"] == k].copy()
    subset["latency"] = pd.Categorical(subset["latency"], categories=lat_order, ordered=True)
    subset["bandwidth"] = pd.Categorical(subset["bandwidth"], categories=bw_order, ordered=True)

    pivot = subset.pivot(index="latency", columns="bandwidth", values="slowdown")

    plt.figure(figsize=(8, 5))
    sns.heatmap(pivot, annot=True, fmt=".2f", cmap="YlOrRd")
    plt.title(f"Slowdown vs. baseline — fence every {k} stores")
    plt.xlabel("Bandwidth")
    plt.ylabel("Latency")
    plt.tight_layout()
    outpath = f"{RESULTS}/heatmap_K{k}.png"
    plt.savefig(outpath, dpi=150)
    plt.close()
    print(f"Saved {outpath}")

# --- Line plot: slowdown vs fence frequency for each latency (fixed BW=25GiB/s) ---
plt.figure(figsize=(9, 6))
for lat in lat_order:
    sub = df[(df["latency"] == lat) & (df["bandwidth"] == "25GiB/s")].sort_values("fence_freq")
    plt.plot(sub["fence_freq"], sub["slowdown"], marker="o", label=lat)

plt.xlabel("Fence Frequency (every K stores)")
plt.ylabel("Slowdown vs. baseline")
plt.title("Consistency Tax: Slowdown vs. Fence Frequency (BW=25GiB/s)")
plt.xscale("log")
plt.legend(title="Memory Latency")
plt.grid(True, alpha=0.3)
plt.tight_layout()
outpath = f"{RESULTS}/slowdown_vs_fence_freq.png"
plt.savefig(outpath, dpi=150)
plt.close()
print(f"Saved {outpath}")

# --- Line plot: slowdown vs latency for each BW (fixed K=16) ---
lat_ns = {"40ns": 40, "80ns": 80, "160ns": 160, "300ns": 300, "400ns": 400}
plt.figure(figsize=(9, 6))
for bw in bw_order:
    sub = df[(df["bandwidth"] == bw) & (df["fence_freq"] == 16)].copy()
    sub["lat_ns"] = sub["latency"].map(lat_ns)
    sub = sub.sort_values("lat_ns")
    plt.plot(sub["lat_ns"], sub["slowdown"], marker="s", label=bw)

plt.xlabel("Memory Latency (ns)")
plt.ylabel("Slowdown vs. baseline")
plt.title("Consistency Tax: Slowdown vs. Memory Latency (K=16)")
plt.legend(title="Bandwidth")
plt.grid(True, alpha=0.3)
plt.tight_layout()
outpath = f"{RESULTS}/slowdown_vs_latency.png"
plt.savefig(outpath, dpi=150)
plt.close()
print(f"Saved {outpath}")

print("\nAll plots generated.")
