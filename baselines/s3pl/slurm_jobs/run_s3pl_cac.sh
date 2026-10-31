#!/bin/bash
# Added for Spatial-msiPL (October 2026) as part of the modified S3PL in baselines/s3pl;
# licensed under AGPL-3.0 (baselines/s3pl/LICENSE).
#SBATCH --job-name=s3pl-cac
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --partition=bigbatch
#SBATCH --time=02:00:00
#SBATCH --mem=32G
#SBATCH --output=logs/s3pl-cac-%j.out
#SBATCH --error=logs/s3pl-cac-%j.err

_paths="$(dirname "${BASH_SOURCE[0]}")/paths.sh"; [ -f "$_paths" ] || _paths="${SPATIAL_MSIPL_ROOT:-$HOME/msi}/slurm_jobs/paths.sh"; source "$_paths"
set -eo pipefail

DATASET="${1:-40TopL}"

case "$DATASET" in
    40TopL|160TopL|200TopL|240TopL|280TopL|360TopL|400TopL|520TopL)
        ;;
    *)
        echo "Unknown CAC section: $DATASET" >&2
        exit 2
        ;;
esac

S3PL_ROOT="$PROJECT_ROOT/baselines/s3pl"
DATA_PATH="$DATA_ROOT/cac/${DATASET}.imzML"

source "$SPATIAL_MSIPL_CONDA_SH"
conda activate s3pl_env

cd "$S3PL_ROOT"

python main.py \
    --data_dir "$DATA_PATH" \
    --artifact_root "$PROJECT_ROOT"
