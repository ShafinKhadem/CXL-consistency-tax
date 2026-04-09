#!/usr/bin/env bash
#SBATCH --job-name=QML
#SBATCH --partition=general-cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=02:00:00
#SBATCH --array=0-9
#SBATCH --output=results/stream_sweep/slurm_%A_%a.log

set -euo pipefail

eval "$($HOME/miniconda3/bin/conda shell.bash hook)"
conda activate gem
export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}"

BASE=/home/hasanat/abrar/cxl_tax
GEM5=$BASE/gem5/build/X86/gem5.opt
CFG=$BASE/configs/cxl_tax_se.py
BIN=$BASE/benches/stream_read
OUT=$BASE/results/stream_sweep

# Parameter arrays
LATENCIES=(40ns 80ns 160ns 300ns 400ns)
BANDWIDTHS=("100GiB/s" "50GiB/s" "25GiB/s" "12.5GiB/s")
STREAMS=(1 4 8 16 32)

# 5 x 4 x 5 = 100 combos, 10 array tasks, 10 each
TASK_ID=${SLURM_ARRAY_TASK_ID}
START=$((TASK_ID * 10))
END=$((START + 10))

for ((i=START; i<END; i++)); do
    S_IDX=$((i % 5))
    BW_IDX=$(( (i / 5) % 4 ))
    L_IDX=$(( i / 20 ))

    L=${LATENCIES[$L_IDX]}
    BW=${BANDWIDTHS[$BW_IDX]}
    S=${STREAMS[$S_IDX]}

    DIR="$OUT/L_${L}__BW_${BW//\//_}__S_${S}"
    mkdir -p "$DIR"

    echo "[$i] Running: L=$L BW=$BW S=$S"
    $GEM5 -d "$DIR" "$CFG" \
        --bin "$BIN" \
        --args "50000 $S" \
        --cpu-type o3 \
        --mem-lat "$L" \
        --mem-bw "$BW"

    echo "[$i] Done: L=$L BW=$BW S=$S"
done

echo "Array task $TASK_ID complete."
