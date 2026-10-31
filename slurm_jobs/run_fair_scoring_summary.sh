#!/bin/bash
# Separate CPU job: collection-level decision table from completed section
# results. Refuses to mix results from different code, parameters or approvals.
#   sbatch slurm_jobs/run_fair_scoring_summary.sh bin_level_only
#   sbatch slurm_jobs/run_fair_scoring_summary.sh with_approved_partitions
#SBATCH --job-name=fair-scoring-summary
#SBATCH --partition=batch
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:20:00
#SBATCH --output=logs/fair-scoring-summary-%j.out
#SBATCH --error=logs/fair-scoring-summary-%j.err

_paths="$(dirname "${BASH_SOURCE[0]}")/paths.sh"; [ -f "$_paths" ] || _paths="${SPATIAL_MSIPL_ROOT:-$HOME/msi}/slurm_jobs/paths.sh"; source "$_paths"
set -euo pipefail
: "${SLURM_JOB_ID:?Submit with sbatch}"
VARIANT="${1:?Usage: sbatch $0 bin_level_only|with_approved_partitions}"
case "$VARIANT" in bin_level_only|with_approved_partitions) ;; *) echo "Bad variant" >&2; exit 2 ;; esac
ROOT="$PROJECT_ROOT/results/diagnostics/fair_scoring_baselines/$VARIANT"
cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT/src:$PROJECT_ROOT/scripts${PYTHONPATH:+:$PYTHONPATH}"
"$SPATIAL_MSIPL_PYTHON" -u scripts/summarise_fair_scoring_baselines.py \
    --root "$ROOT" --output "$ROOT/summary_${SLURM_JOB_ID}"
