#!/bin/bash
#SBATCH --job-name=msipl-massnet
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --partition=bigbatch
#SBATCH --time=08:00:00
#SBATCH --mem=64G
#SBATCH --exclusive
#SBATCH --output=logs/msipl-massnet-%j.out
#SBATCH --error=logs/msipl-massnet-%j.err

_paths="$(dirname "${BASH_SOURCE[0]}")/paths.sh"; [ -f "$_paths" ] || _paths="${SPATIAL_MSIPL_ROOT:-$HOME/msi}/slurm_jobs/paths.sh"; source "$_paths"
set -eo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: sbatch $0 DATASET" >&2
    exit 2
fi

DATASET="$1"
case "$DATASET" in
    GBM108_positive|GBM108_negative|GBM12_1|GBM12_2|GBM22_1|GBM22_2|GBM39_1|GBM39_2) ;;
    *)
        echo "Unknown MassNet dataset: $DATASET" >&2
        exit 2
        ;;
esac

INPUT="$DATA_ROOT/gbm_massnet/$DATASET.h5"
OUTPUT="$PROJECT_ROOT/results/baselines/msipl/massnet/$DATASET"
CHECKPOINT_ROOT="$CHECKPOINT_ROOT/baselines/msipl/massnet"

if [[ -f "$OUTPUT/peak_metrics.json" ]]; then
    echo "Completed peak metrics already exist; refusing to overwrite: $OUTPUT/peak_metrics.json"
    exit 0
fi

mkdir -p "$PROJECT_ROOT/logs" "$OUTPUT" "$CHECKPOINT_ROOT"
cd "$PROJECT_ROOT"
source "$SPATIAL_MSIPL_CONDA_SH"
conda activate msipl_legacy
export OMP_NUM_THREADS=8

python -m py_compile \
    scripts/run_msipl_legacy_gbm.py \
    scripts/evaluate_msipl_massnet_peaks.py

python scripts/run_msipl_legacy_gbm.py \
    --input "$INPUT" \
    --output-dir "$OUTPUT" \
    --checkpoint-root "$CHECKPOINT_ROOT" \
    --epochs 100 \
    --batch-size 128 \
    --latent-dim 5 \
    --intermediate-dim 512 \
    --beta 2.5 \
    --seed 1337

python scripts/evaluate_msipl_massnet_peaks.py \
    --input "$INPUT" \
    --peaks "$OUTPUT/learned_peaks.csv" \
    --output "$OUTPUT"
