"""Generate plots from fault sweep results."""

import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BASE = "/home/hasanat/abrar/cxl_tax"
RESULTS = f"{BASE}/results"

df = pd.read_csv(f"{RESULTS}/fault_sweep_summary.csv")

# Convert fault_prob to float for sorting
df["lam_float"] = df["fault_prob"].astype(float)

# Compute slowdown relative to no-fault baseline at same latency
baselines = {}
for lat in df["latency"].unique():
    base_rows = df[(df["latency"] == lat) & (df["lam_float"] == 0.0)]
    if len(base_rows) > 0:
        baselines[lat] = base_rows["simSeconds"].values[0]

df["slowdown"] = df.apply(
    lambda r: r["simSeconds"] / baselines.get(r["latency"], 1.0), axis=1
)

lat_order = ["40ns", "160ns", "300ns"]
handler_order = ["1us", "5us", "20us"]

# --- Plot 1: Slowdown vs fault probability, per latency (handler=20us) ---
plt.figure(figsize=(9, 6))
for lat in lat_order:
    sub = df[(df["latency"] == lat) & (df["handler"] == "20us") & (df["lam_float"] > 0)].sort_values("lam_float")
    plt.plot(sub["lam_float"], sub["slowdown"], marker="o", label=lat, linewidth=2)
plt.xlabel("Fault Probability (λ)")
plt.ylabel("Slowdown vs. no-fault baseline")
plt.title("Precise Exception Tax: Slowdown vs. Fault Rate (handler=20µs)")
plt.xscale("log")
plt.yscale("log")
plt.legend(title="Memory Latency")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f"{RESULTS}/fault_slowdown_vs_lambda.png", dpi=150)
plt.close()

# --- Plot 2: Slowdown vs fault probability, per handler cost (L=300ns) ---
plt.figure(figsize=(9, 6))
for h in handler_order:
    sub = df[(df["latency"] == "300ns") & (df["handler"] == h) & (df["lam_float"] > 0)].sort_values("lam_float")
    plt.plot(sub["lam_float"], sub["slowdown"], marker="s", label=h, linewidth=2)
plt.xlabel("Fault Probability (λ)")
plt.ylabel("Slowdown vs. no-fault baseline")
plt.title("Precise Exception Tax: Slowdown vs. Fault Rate (L=300ns)")
plt.xscale("log")
plt.yscale("log")
plt.legend(title="Handler Cost")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f"{RESULTS}/fault_slowdown_vs_lambda_by_handler.png", dpi=150)
plt.close()

# --- Plot 3: Absolute time vs latency, per fault prob (handler=20us) ---
plt.figure(figsize=(9, 6))
lat_ns = {"40ns": 40, "160ns": 160, "300ns": 300}
for lam in ["0", "1e-3", "0.01", "0.1", "0.5"]:
    sub = df[(df["fault_prob"] == lam) & (df["handler"] == "20us")].copy()
    if lam == "0":
        sub = df[(df["lam_float"] == 0.0)].drop_duplicates(subset="latency")
    sub["lat_ns"] = sub["latency"].map(lat_ns)
    sub = sub.sort_values("lat_ns")
    label = f"λ={lam}" if lam != "0" else "No faults"
    plt.plot(sub["lat_ns"], sub["simSeconds"] * 1e3, marker="o", label=label, linewidth=2)
plt.xlabel("Memory Latency (ns)")
plt.ylabel("Simulated Time (ms)")
plt.title("Execution Time: Memory Latency × Fault Rate (handler=20µs)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f"{RESULTS}/fault_time_vs_latency.png", dpi=150)
plt.close()

# --- Plot 4: Heatmap — slowdown for L=300ns across lambda x handler ---
sub = df[(df["latency"] == "300ns") & (df["lam_float"] > 0)].copy()
sub = sub.drop_duplicates(subset=["fault_prob", "handler"])
lam_order = ["1e-4", "1e-3", "0.01", "0.05", "0.1", "0.5"]
sub["lam_label"] = pd.Categorical(sub["fault_prob"].astype(str), categories=lam_order, ordered=True)
sub["handler"] = pd.Categorical(sub["handler"], categories=handler_order, ordered=True)
sub = sub.dropna(subset=["lam_label"])
pivot = sub.pivot(index="lam_label", columns="handler", values="slowdown")

import seaborn as sns
plt.figure(figsize=(8, 6))
sns.heatmap(pivot, annot=True, fmt=".1f", cmap="YlOrRd")
plt.title("Precise Exception Tax at L=300ns (CXL far memory)")
plt.xlabel("Handler Cost")
plt.ylabel("Fault Probability (λ)")
plt.tight_layout()
plt.savefig(f"{RESULTS}/fault_heatmap_300ns.png", dpi=150)
plt.close()

print("All fault plots generated.")
