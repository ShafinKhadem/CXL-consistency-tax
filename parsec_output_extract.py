import csv
import re

log_file = "parsec.out"  # Change to your log filename
csv_file = "parsec.csv"

with open(log_file, "r") as f:
    lines = f.readlines()

results = []
current_exp = None
current_exp_tso = False

for line in lines:
    run_match = re.match(r"Running (\w+) with .*", line)
    if run_match:
        current_exp = run_match.group(1)
    tso_match = re.match(r"  needs-tso:\s*(\w+)", line)
    if tso_match:
        current_exp_tso = tso_match.group(1)
    roi_match = re.match(r"\[HOOKS\] Total time spent in ROI:\s*([0-9.]+)s", line)
    if roi_match:
        roi_time = roi_match.group(1)
        results.append((current_exp, current_exp_tso, roi_time))

with open(csv_file, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Experiment", "TSO", "ROI_Time(s)"])
    writer.writerows(results)

print(f"Extracted {len(results)} experiments to {csv_file}")
