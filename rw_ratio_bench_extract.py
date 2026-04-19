import argparse
import csv

#!/usr/bin/env python3
import re
import sys
from pathlib import Path

RUN_RE = re.compile(
    r"Running with ISA=(?P<isa>\w+), SQ size=(?P<sq>\d+), LQ size=(?P<lq>\d+), write-ratio=(?P<wr>\d+)"
)
TOTAL_RE = re.compile(r"total_ops=(?P<ops>\d+)\s+\((?P<mops>[0-9.]+)\s+Mop/s\)")


def parse_log(lines):
    current = None

    for line in lines:
        line = line.strip()

        m = RUN_RE.search(line)
        if m:
            current = {
                "isa": m.group("isa"),
                "sq_size": int(m.group("sq")),
                "lq_size": int(m.group("lq")),
                "write_ratio": int(m.group("wr")),
            }
            continue

        m = TOTAL_RE.search(line)
        if m and current is not None:
            yield {
                **current,
                "total_mops_per_s": float(m.group("mops")),
            }
            current = None


def main():
    ap = argparse.ArgumentParser(
        description="Extract total Mop/s and parameters from gem5 logs."
    )
    ap.add_argument(
        "logfile", nargs="?", help="Path to log file. Reads stdin if omitted."
    )
    ap.add_argument("--csv", action="store_true", help="CSV output (default).")
    args = ap.parse_args()

    if args.logfile:
        with open(args.logfile, "r", encoding="utf-8", errors="replace") as f:
            rows = list(parse_log(f))
    else:
        rows = list(parse_log(sys.stdin))

    writer = csv.DictWriter(
        sys.stdout,
        fieldnames=["isa", "sq_size", "lq_size", "write_ratio", "total_mops_per_s"],
    )
    writer.writeheader()
    writer.writerows(rows)


if __name__ == "__main__":
    main()
