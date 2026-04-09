#!/usr/bin/env bash
#SBATCH --job-name=gem5-build
#SBATCH --partition=general-cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=gem5_build_%j.log

set -euo pipefail

# Activate conda environment
eval "$($HOME/miniconda3/bin/conda shell.bash hook)"
conda activate gem

# Ensure conda's shared libraries are visible to the linker
export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}"

cd /home/hasanat/abrar/cxl_tax/gem5

echo "Starting gem5 build at $(date)"
scons build/X86/gem5.opt -j${SLURM_CPUS_PER_TASK}
echo "Build finished at $(date)"
