#!/usr/bin/env bash
#SBATCH --job-name=QML
#SBATCH --partition=general-cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:30:00
#SBATCH --output=test_stream_%j.log

set -euo pipefail

eval "$($HOME/miniconda3/bin/conda shell.bash hook)"
conda activate gem
export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}"

BASE=/home/hasanat/abrar/cxl_tax
GEM5=$BASE/gem5/build/X86/gem5.opt
CFG=$BASE/configs/cxl_tax_se.py
BIN=$BASE/benches/stream_read

# Compile
echo "=== Compiling stream_read ==="
cd $BASE/benches
gcc -O2 -static -march=x86-64 -o stream_read stream_read.c
file stream_read

# Test 1: 40ns, 100GiB/s (fast)
echo "=== O3 | 40ns | 100GiB/s | 16 streams ==="
DIR=$BASE/results/stream_test/L40_BW100
mkdir -p "$DIR"
$GEM5 -d "$DIR" "$CFG" \
    --bin "$BIN" --args "50000 16" \
    --cpu-type o3 --mem-lat 40ns --mem-bw "100GiB/s"
grep -E "simSeconds|simInsts" "$DIR/stats.txt" | head -4

# Test 2: 40ns, 12.5GiB/s (same latency, low BW)
echo "=== O3 | 40ns | 12.5GiB/s | 16 streams ==="
DIR=$BASE/results/stream_test/L40_BW12
mkdir -p "$DIR"
$GEM5 -d "$DIR" "$CFG" \
    --bin "$BIN" --args "50000 16" \
    --cpu-type o3 --mem-lat 40ns --mem-bw "12.5GiB/s"
grep -E "simSeconds|simInsts" "$DIR/stats.txt" | head -4

# Test 3: 300ns, 100GiB/s
echo "=== O3 | 300ns | 100GiB/s | 16 streams ==="
DIR=$BASE/results/stream_test/L300_BW100
mkdir -p "$DIR"
$GEM5 -d "$DIR" "$CFG" \
    --bin "$BIN" --args "50000 16" \
    --cpu-type o3 --mem-lat 300ns --mem-bw "100GiB/s"
grep -E "simSeconds|simInsts" "$DIR/stats.txt" | head -4

# Test 4: 300ns, 12.5GiB/s
echo "=== O3 | 300ns | 12.5GiB/s | 16 streams ==="
DIR=$BASE/results/stream_test/L300_BW12
mkdir -p "$DIR"
$GEM5 -d "$DIR" "$CFG" \
    --bin "$BIN" --args "50000 16" \
    --cpu-type o3 --mem-lat 300ns --mem-bw "12.5GiB/s"
grep -E "simSeconds|simInsts" "$DIR/stats.txt" | head -4

echo ""
echo "=== All stream tests complete ==="
