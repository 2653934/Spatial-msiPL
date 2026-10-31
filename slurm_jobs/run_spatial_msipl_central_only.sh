#!/bin/bash
#SBATCH --job-name=central-vae
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --partition=bigbatch
#SBATCH --time=16:00:00
#SBATCH --mem=32G
#SBATCH --exclusive
#SBATCH --output=logs/central-vae-%j.out
#SBATCH --error=logs/central-vae-%j.err

_paths="$(dirname "${BASH_SOURCE[0]}")/paths.sh"; [ -f "$_paths" ] || _paths="${SPATIAL_MSIPL_ROOT:-$HOME/msi}/slurm_jobs/paths.sh"; source "$_paths"
set -eo pipefail

INPUT="$DATA_ROOT/gbm_massnet/GBM108_positive.h5"
OUTPUT="$PROJECT_ROOT/results/experiments/spatial_msipl_reconstruction/GBM108_positive_seed1/central_only"
CHECKPOINT_OUTPUT="$CHECKPOINT_ROOT/spatial_msipl/reconstruction/GBM108_positive_seed1/central_only"
FINAL_CHECKPOINT="$CHECKPOINT_OUTPUT/checkpoint.pt"
LATEST_CHECKPOINT="$CHECKPOINT_OUTPUT/checkpoint_latest.pt"

if [[ -f "$FINAL_CHECKPOINT" ]]; then
    echo "Completed checkpoint already exists; refusing to overwrite: $FINAL_CHECKPOINT"
    exit 0
fi

cd "$PROJECT_ROOT"
source "$SPATIAL_MSIPL_CONDA_SH"
conda activate s3pl_env
export PYTHONPATH="$PROJECT_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
export OMP_NUM_THREADS=4

python -c 'import sys, torch; sys.exit(0 if torch.cuda.is_available() else "CUDA is unavailable; centre-only training stopped before loading the model.")'

RESUME_ARGUMENTS=()
if [[ -f "$LATEST_CHECKPOINT" ]]; then
    echo "Resuming centre-only VAE from: $LATEST_CHECKPOINT"
    RESUME_ARGUMENTS=(--resume-checkpoint "$LATEST_CHECKPOINT")
else
    echo "Starting the matched 100-epoch centre-only VAE baseline"
fi

python -m unittest discover -s src/spatial_msipl/tests -v
python -u scripts/train_spatial_msipl_production.py \
    --input "$INPUT" \
    --output "$OUTPUT" \
    --checkpoint-output "$CHECKPOINT_OUTPUT" \
    --variant central_only \
    --epochs 100 \
    --batch-size 128 \
    --hidden-dim 512 \
    --latent-dim 5 \
    --learning-rate 0.001 \
    --seed 1 \
    --checkpoint-interval 5 \
    "${RESUME_ARGUMENTS[@]}"
