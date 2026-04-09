#!/usr/bin/env bash
#SBATCH --job-name=compile-bench
#SBATCH --partition=general-cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:10:00
#SBATCH --output=compile_benches_%j.log

set -euo pipefail

cd /home/hasanat/abrar/cxl_tax/benches

echo "=== Compiling fence_sweep ==="
gcc -O2 -static -march=x86-64 -o fence_sweep fence_sweep.c
file fence_sweep

echo "=== Compiling spinlock_counter ==="
gcc -O2 -static -pthread -o spinlock_counter spinlock_counter.c
file spinlock_counter

echo "=== All benchmarks compiled ==="
