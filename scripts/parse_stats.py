"""Extract key stats from fence sweep results into a CSV."""

import os
import re
import pandas as pd

BASE = "/home/hasanat/abrar/cxl_tax"
SWEEP_DIR = f"{BASE}/results/fence_sweep"

def read_stat(path, key):
    """Extract a single stat value from a gem5 stats.txt file."""
    with open(path) as f:
        for line in f:
            if line.startswith(key):
                return float(line.split()[1])
    return None

rows = []
for root, dirs, files in os.walk(SWEEP_DIR):
    if "stats.txt" not in files:
        continue

    stats = os.path.join(root, "stats.txt")

    # Path looks like: .../L_40ns_BW_100GiB/s_K_1/stats.txt
    # Reconstruct the full path relative to sweep dir
    relpath = os.path.relpath(root, SWEEP_DIR)  # e.g. "L_40ns_BW_100GiB/s_K_1"
    full = relpath.replace(os.sep, "/")          # normalize

    m = re.search(r"L_(.+?)_BW_(.+?)/s_K_(\d+)", full)
    if not m:
        continue

    L  = m.group(1)
    BW = m.group(2) + "/s"  # restore the "/s" that became a directory
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
outpath = f"{BASE}/results/fence_sweep_summary.csv"
df.to_csv(outpath, index=False)
print(f"Wrote {len(df)} rows to {outpath}")
print(df.to_string(index=False))
