#!/usr/bin/env bash
#SBATCH --job-name=QML
#SBATCH --partition=general-cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=02:00:00
#SBATCH --array=0-9
#SBATCH --output=results/fault_sweep/slurm_%A_%a.log

set -euo pipefail

eval "$($HOME/miniconda3/bin/conda shell.bash hook)"
conda activate gem
export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}"

BASE=/home/hasanat/abrar/cxl_tax
GEM5=$BASE/gem5/build/X86/gem5.opt
CFG=$BASE/configs/cxl_tax_se.py
BIN=$BASE/benches/fence_sweep
OUT=$BASE/results/fault_sweep

# Parameter arrays
# 3 latencies x 7 fault probs x 3 handler costs = 63 combos
# + pad to 70 (10 per task, 7 tasks used, 3 tasks idle)
LATENCIES=(40ns 160ns 300ns)
LAMBDAS=(0 1e-4 1e-3 0.01 0.05 0.1 0.5)
HANDLERS=(1us 5us 20us)

TASK_ID=${SLURM_ARRAY_TASK_ID}
START=$((TASK_ID * 7))
END=$((START + 7))

# Total combos = 63
TOTAL=63

for ((i=START; i<END && i<TOTAL; i++)); do
    T_IDX=$((i % 3))
    LAM_IDX=$(( (i / 3) % 7 ))
    L_IDX=$(( i / 21 ))

    L=${LATENCIES[$L_IDX]}
    LAM=${LAMBDAS[$LAM_IDX]}
    T=${HANDLERS[$T_IDX]}

    DIR="$OUT/L_${L}__lam_${LAM}__T_${T}"
    mkdir -p "$DIR"

    echo "[$i] Running: L=$L lambda=$LAM handler=$T"

    if [ "$LAM" = "0" ]; then
        # No fault injection — skip --fault-prob to use normal cache hierarchy
        $GEM5 -d "$DIR" "$CFG" \
            --bin "$BIN" --args "100000 16" \
            --cpu-type o3 \
            --mem-lat "$L" --mem-bw "50GiB/s"
    else
        $GEM5 -d "$DIR" "$CFG" \
            --bin "$BIN" --args "100000 16" \
            --cpu-type o3 \
            --mem-lat "$L" --mem-bw "50GiB/s" \
            --fault-prob "$LAM" --handler "$T"
    fi

    echo "[$i] Done: L=$L lambda=$LAM handler=$T"
done

echo "Array task $TASK_ID complete."
