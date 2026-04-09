"""Extract key stats from O3 fence sweep results into a CSV."""

import os
import re
import pandas as pd

BASE = "/home/hasanat/abrar/cxl_tax"
SWEEP_DIR = f"{BASE}/results/fence_sweep_o3"

def read_stat(path, key):
    with open(path) as f:
        for line in f:
            if line.startswith(key):
                return float(line.split()[1])
    return None

rows = []
for entry in sorted(os.listdir(SWEEP_DIR)):
    stats = os.path.join(SWEEP_DIR, entry, "stats.txt")
    if not os.path.exists(stats):
        continue

    # Dir name: L_40ns__BW_100GiB_s__K_1
    m = re.search(r"L_(.+?)__BW_(.+?)__K_(\d+)", entry)
    if not m:
        continue

    L  = m.group(1)
    BW = m.group(2).replace("_s", "/s")  # restore 100GiB_s -> 100GiB/s
    K  = int(m.group(3))

    rows.append({
        "latency":    L,
        "bandwidth":  BW,
        "fence_freq": K,
        "simSeconds": read_stat(stats, "simSeconds"),
        "simTicks":   read_stat(stats, "simTicks"),
        "simInsts":   read_stat(stats, "simInsts"),
    })

df = pd.DataFrame(rows)
df = df.sort_values(["latency", "bandwidth", "fence_freq"]).reset_index(drop=True)
outpath = f"{BASE}/results/fence_sweep_o3_summary.csv"
df.to_csv(outpath, index=False)
print(f"Wrote {len(df)} rows to {outpath}")

# Quick comparison
baseline = df[(df["latency"] == "40ns") & (df["bandwidth"] == "100GiB/s")]
baseline_map = baseline.set_index("fence_freq")["simSeconds"].to_dict()
df["slowdown"] = df.apply(
    lambda r: r["simSeconds"] / baseline_map.get(r["fence_freq"], 1.0), axis=1
)

# Show fence freq effect
print("\n=== Fence frequency effect (L=300ns, BW=25GiB/s) ===")
sub = df[(df["latency"] == "300ns") & (df["bandwidth"] == "25GiB/s")].sort_values("fence_freq")
for _, r in sub.iterrows():
    print(f"  K={int(r['fence_freq']):>3d}  simSeconds={r['simSeconds']:.6f}  slowdown={r['slowdown']:.2f}x")

print("\n=== Bandwidth effect (L=300ns, K=16) ===")
sub = df[(df["latency"] == "300ns") & (df["fence_freq"] == 16)].sort_values("bandwidth")
for _, r in sub.iterrows():
    print(f"  BW={r['bandwidth']:>10s}  simSeconds={r['simSeconds']:.6f}  slowdown={r['slowdown']:.2f}x")

print("\n=== Latency effect (BW=25GiB/s, K=1) ===")
sub = df[(df["bandwidth"] == "25GiB/s") & (df["fence_freq"] == 1)].sort_values("latency")
for _, r in sub.iterrows():
    print(f"  L={r['latency']:>5s}  simSeconds={r['simSeconds']:.6f}  slowdown={r['slowdown']:.2f}x")
