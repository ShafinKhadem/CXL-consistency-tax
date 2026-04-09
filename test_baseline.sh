#!/usr/bin/env bash
#SBATCH --job-name=gem5-test
#SBATCH --partition=general-cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:30:00
#SBATCH --output=test_baseline_%j.log

set -euo pipefail

eval "$($HOME/miniconda3/bin/conda shell.bash hook)"
conda activate gem
export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}"

BASE=/home/hasanat/abrar/cxl_tax
GEM5=$BASE/gem5/build/X86/gem5.opt
CFG=$BASE/configs/cxl_tax_se.py
BIN=$BASE/benches/fence_sweep
OUTDIR=$BASE/results/test_baseline

mkdir -p "$OUTDIR"

echo "=== Test run: fence_sweep baseline (40ns, 100GiB/s, K=16) ==="
$GEM5 -d "$OUTDIR" "$CFG" \
    --bin "$BIN" \
    --args "1000 16" \
    --mem-lat 40ns \
    --mem-bw "100GiB/s"

echo ""
echo "=== Key stats ==="
grep -E "simSeconds|simTicks|simInsts" "$OUTDIR/stats.txt" | head -6

echo ""
echo "=== Test complete ==="
