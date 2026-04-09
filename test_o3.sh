#!/usr/bin/env bash
#SBATCH --job-name=QML
#SBATCH --partition=general-cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=01:00:00
#SBATCH --output=test_o3_%j.log

set -euo pipefail

eval "$($HOME/miniconda3/bin/conda shell.bash hook)"
conda activate gem
export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}"

BASE=/home/hasanat/abrar/cxl_tax
GEM5=$BASE/gem5/build/X86/gem5.opt
CFG=$BASE/configs/cxl_tax_se.py
BIN=$BASE/benches/fence_sweep

# Test 1: O3, 300ns, K=1 (fence every store)
echo "=== O3 | 300ns | K=1 ==="
DIR=$BASE/results/o3_test/L300_K1
mkdir -p "$DIR"
$GEM5 -d "$DIR" "$CFG" \
    --bin "$BIN" --args "100000 1" \
    --cpu-type o3 --mem-lat 300ns --mem-bw "25GiB/s"
grep -E "simSeconds|simTicks|simInsts" "$DIR/stats.txt" | head -6

# Test 2: O3, 300ns, K=256 (rare fences)
echo "=== O3 | 300ns | K=256 ==="
DIR=$BASE/results/o3_test/L300_K256
mkdir -p "$DIR"
$GEM5 -d "$DIR" "$CFG" \
    --bin "$BIN" --args "100000 256" \
    --cpu-type o3 --mem-lat 300ns --mem-bw "25GiB/s"
grep -E "simSeconds|simTicks|simInsts" "$DIR/stats.txt" | head -6

# Test 3: O3, 40ns baseline, K=1
echo "=== O3 | 40ns | K=1 ==="
DIR=$BASE/results/o3_test/L40_K1
mkdir -p "$DIR"
$GEM5 -d "$DIR" "$CFG" \
    --bin "$BIN" --args "100000 1" \
    --cpu-type o3 --mem-lat 40ns --mem-bw "100GiB/s"
grep -E "simSeconds|simTicks|simInsts" "$DIR/stats.txt" | head -6

# Test 4: O3, 40ns baseline, K=256
echo "=== O3 | 40ns | K=256 ==="
DIR=$BASE/results/o3_test/L40_K256
mkdir -p "$DIR"
$GEM5 -d "$DIR" "$CFG" \
    --bin "$BIN" --args "100000 256" \
    --cpu-type o3 --mem-lat 40ns --mem-bw "100GiB/s"
grep -E "simSeconds|simTicks|simInsts" "$DIR/stats.txt" | head -6

echo ""
echo "=== All O3 tests complete ==="
