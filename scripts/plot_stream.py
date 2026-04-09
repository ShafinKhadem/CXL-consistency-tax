"""Generate plots from stream sweep results."""

import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

BASE = "/home/hasanat/abrar/cxl_tax"
RESULTS = f"{BASE}/results"

df = pd.read_csv(f"{RESULTS}/stream_sweep_summary.csv")

# Compute slowdown relative to baseline (L=40ns, BW=100GiB/s)
baseline = df[(df["latency"] == "40ns") & (df["bandwidth"] == "100GiB/s")]
baseline_map = baseline.set_index("streams")["simSeconds"].to_dict()
df["slowdown"] = df.apply(
    lambda r: r["simSeconds"] / baseline_map.get(r["streams"], 1.0), axis=1
)

lat_order = ["40ns", "80ns", "160ns", "300ns", "400ns"]
bw_order = ["100GiB/s", "50GiB/s", "25GiB/s", "12.5GiB/s"]

# --- Heatmap: BW vs Latency for S=16 ---
subset = df[df["streams"] == 16].copy()
subset["latency"] = pd.Categorical(subset["latency"], categories=lat_order, ordered=True)
subset["bandwidth"] = pd.Categorical(subset["bandwidth"], categories=bw_order, ordered=True)
pivot = subset.pivot(index="latency", columns="bandwidth", values="slowdown")

plt.figure(figsize=(8, 5))
sns.heatmap(pivot, annot=True, fmt=".2f", cmap="YlOrRd")
plt.title("Stream Read (16 streams): Slowdown vs. baseline")
plt.xlabel("Bandwidth")
plt.ylabel("Latency")
plt.tight_layout()
plt.savefig(f"{RESULTS}/stream_heatmap_S16.png", dpi=150)
plt.close()

# --- Heatmap: BW vs Latency for S=32 ---
subset = df[df["streams"] == 32].copy()
subset["latency"] = pd.Categorical(subset["latency"], categories=lat_order, ordered=True)
subset["bandwidth"] = pd.Categorical(subset["bandwidth"], categories=bw_order, ordered=True)
pivot = subset.pivot(index="latency", columns="bandwidth", values="slowdown")

plt.figure(figsize=(8, 5))
sns.heatmap(pivot, annot=True, fmt=".2f", cmap="YlOrRd")
plt.title("Stream Read (32 streams): Slowdown vs. baseline")
plt.xlabel("Bandwidth")
plt.ylabel("Latency")
plt.tight_layout()
plt.savefig(f"{RESULTS}/stream_heatmap_S32.png", dpi=150)
plt.close()

# --- Line plot: simSeconds vs BW for each latency (S=16) ---
bw_numeric = {"100GiB/s": 100, "50GiB/s": 50, "25GiB/s": 25, "12.5GiB/s": 12.5}
plt.figure(figsize=(9, 6))
for lat in lat_order:
    sub = df[(df["latency"] == lat) & (df["streams"] == 16)].copy()
    sub["bw_val"] = sub["bandwidth"].map(bw_numeric)
    sub = sub.sort_values("bw_val")
    plt.plot(sub["bw_val"], sub["simSeconds"] * 1e3, marker="o", label=lat, linewidth=2)
plt.xlabel("Bandwidth (GiB/s)")
plt.ylabel("Simulated Time (ms)")
plt.title("Stream Read (16 streams): Execution Time vs. Bandwidth")
plt.legend(title="Memory Latency")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f"{RESULTS}/stream_time_vs_bw.png", dpi=150)
plt.close()

# --- Line plot: simSeconds vs streams for low BW, comparing latencies ---
plt.figure(figsize=(9, 6))
for lat in lat_order:
    sub = df[(df["latency"] == lat) & (df["bandwidth"] == "12.5GiB/s")].sort_values("streams")
    plt.plot(sub["streams"], sub["simSeconds"] * 1e3, marker="s", label=lat, linewidth=2)
plt.xlabel("Number of Streams (memory-level parallelism)")
plt.ylabel("Simulated Time (ms)")
plt.title("Stream Read (BW=12.5GiB/s): Execution Time vs. Stream Count")
plt.legend(title="Memory Latency")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f"{RESULTS}/stream_time_vs_streams.png", dpi=150)
plt.close()

# --- Key plot: BW sensitivity ratio (low BW / high BW) vs latency ---
plt.figure(figsize=(9, 6))
lat_ns = {"40ns": 40, "80ns": 80, "160ns": 160, "300ns": 300, "400ns": 400}
for s in [1, 4, 8, 16, 32]:
    ratios = []
    lats = []
    for lat in lat_order:
        high = df[(df["latency"] == lat) & (df["bandwidth"] == "100GiB/s") & (df["streams"] == s)]["simSeconds"].values
        low  = df[(df["latency"] == lat) & (df["bandwidth"] == "12.5GiB/s") & (df["streams"] == s)]["simSeconds"].values
        if len(high) and len(low):
            ratios.append(low[0] / high[0])
            lats.append(lat_ns[lat])
    plt.plot(lats, ratios, marker="o", label=f"S={s}", linewidth=2)
plt.xlabel("Memory Latency (ns)")
plt.ylabel("BW Sensitivity (12.5 GiB/s / 100 GiB/s)")
plt.axhline(y=1.0, color="gray", linestyle="--", alpha=0.5)
plt.title("Bandwidth Sensitivity: How much does 8x less BW hurt?")
plt.legend(title="Streams")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f"{RESULTS}/stream_bw_sensitivity.png", dpi=150)
plt.close()

print("All stream plots generated.")
