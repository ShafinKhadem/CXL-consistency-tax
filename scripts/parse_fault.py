"""Extract stats from fault sweep results."""

import os
import re
import pandas as pd

BASE = "/home/hasanat/abrar/cxl_tax"
SWEEP_DIR = f"{BASE}/results/fault_sweep"

def read_stat(path, key):
    with open(path) as f:
        for line in f:
            if key in line and not line.strip().startswith("#"):
                return float(line.split()[1])
    return None

rows = []
for entry in sorted(os.listdir(SWEEP_DIR)):
    stats = os.path.join(SWEEP_DIR, entry, "stats.txt")
    if not os.path.exists(stats):
        continue

    m = re.search(r"L_(.+?)__lam_(.+?)__T_(.+)", entry)
    if not m:
        continue

    L   = m.group(1)
    LAM = m.group(2)
    T   = m.group(3)

    rows.append({
        "latency":       L,
        "fault_prob":    LAM,
        "handler":       T,
        "simSeconds":    read_stat(stats, "simSeconds"),
        "simInsts":      read_stat(stats, "simInsts"),
        "totalWrites":   read_stat(stats, "totalWrites"),
        "faultCount":    read_stat(stats, "faultCount"),
    })

df = pd.DataFrame(rows)
df = df.sort_values(["latency", "handler", "fault_prob"]).reset_index(drop=True)
outpath = f"{BASE}/results/fault_sweep_summary.csv"
df.to_csv(outpath, index=False)
print(f"Wrote {len(df)} rows to {outpath}")

# Show key results
for lat in ["40ns", "160ns", "300ns"]:
    print(f"\n=== L={lat}, handler=20us ===")
    sub = df[(df["latency"] == lat) & (df["handler"] == "20us")].sort_values("fault_prob")
    for _, r in sub.iterrows():
        fc = f"{int(r['faultCount'])}" if pd.notna(r['faultCount']) else "—"
        print(f"  λ={r['fault_prob']:>6s}  faults={fc:>5s}  simSeconds={r['simSeconds']:.6f}")
