"""Extract key stats from stream sweep results into a CSV."""

import os
import re
import pandas as pd

BASE = "/home/hasanat/abrar/cxl_tax"
SWEEP_DIR = f"{BASE}/results/stream_sweep"

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

    m = re.search(r"L_(.+?)__BW_(.+?)__S_(\d+)", entry)
    if not m:
        continue

    L  = m.group(1)
    BW = m.group(2).replace("_s", "/s")
    S  = int(m.group(3))

    rows.append({
        "latency":    L,
        "bandwidth":  BW,
        "streams":    S,
        "simSeconds": read_stat(stats, "simSeconds"),
        "simTicks":   read_stat(stats, "simTicks"),
        "simInsts":   read_stat(stats, "simInsts"),
    })

df = pd.DataFrame(rows)
df = df.sort_values(["latency", "bandwidth", "streams"]).reset_index(drop=True)
outpath = f"{BASE}/results/stream_sweep_summary.csv"
df.to_csv(outpath, index=False)
print(f"Wrote {len(df)} rows to {outpath}")

# Show bandwidth effect at different latencies
for lat in ["40ns", "160ns", "300ns"]:
    print(f"\n=== Bandwidth effect at L={lat}, S=16 ===")
    sub = df[(df["latency"] == lat) & (df["streams"] == 16)].sort_values("bandwidth")
    for _, r in sub.iterrows():
        print(f"  BW={r['bandwidth']:>10s}  simSeconds={r['simSeconds']:.6f}")

# Show stream count effect
print(f"\n=== Stream count effect at L=40ns, BW=12.5GiB/s ===")
sub = df[(df["latency"] == "40ns") & (df["bandwidth"] == "12.5GiB/s")].sort_values("streams")
for _, r in sub.iterrows():
    print(f"  S={int(r['streams']):>2d}  simSeconds={r['simSeconds']:.6f}")

print(f"\n=== Stream count effect at L=300ns, BW=12.5GiB/s ===")
sub = df[(df["latency"] == "300ns") & (df["bandwidth"] == "12.5GiB/s")].sort_values("streams")
for _, r in sub.iterrows():
    print(f"  S={int(r['streams']):>2d}  simSeconds={r['simSeconds']:.6f}")
