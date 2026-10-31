#!/bin/bash
# Login-node submitter for the C3 training-length analysis: file checks, mkdir and sbatch
# only. Each submission needs a protocol section, a checklist and approval.
#   bash slurm_jobs/submit_training_length.sh INDICES [--concurrency N]
# INDICES: 0-3 (GBM108_positive central/uniform, 40TopL central/uniform).
# The CUDA quarantine is passed as --exclude on the sbatch command line (Slurm does
# not read an SBATCH_EXCLUDE variable). Refuses any row whose output exists.
_paths="$(dirname "${BASH_SOURCE[0]}")/paths.sh"; [ -f "$_paths" ] || _paths="${SPATIAL_MSIPL_ROOT:-$HOME/msi}/slurm_jobs/paths.sh"; source "$_paths"
set -euo pipefail
cd "$PROJECT_ROOT"
indices="${1:?Usage: $0 INDICES [--concurrency N]}"
shift
source slurm_jobs/training_length_sections.sh
concurrency=2
while [ "$#" -gt 0 ]; do
    case "$1" in
        --concurrency) concurrency="${2:?}"; shift 2 ;;
        *) echo "Unknown argument: $1" >&2; exit 2 ;;
    esac
done
expanded="$(test_r_expand_indices "$indices")"
[ -n "$expanded" ] || { echo "Empty index list" >&2; exit 2; }
provenance="$TRAINING_LENGTH_RESULTS/provenance"
mkdir -p logs "$provenance"
# Shared parents are created here, before any array task starts (mkdir race, 66114).
for index in $expanded; do
    (( index >= 0 && index < 4 )) || { echo "Invalid index: $index" >&2; exit 2; }
    section="${TRAINING_LENGTH_SECTIONS[index / 2]}"
    arm="${TRAINING_LENGTH_ARMS[index % 2]}"
    root="$(training_length_result_root "$section" "$arm")"
    [ ! -e "$root/summary.json" ] || { echo "Row $index output exists: $root" >&2; exit 3; }
    mkdir -p "$(dirname "$root")" "$(dirname "$(training_length_fair_root "$section" "$arm")")"
done
exclude="$(sed -e 's/\r$//' -e 's/#.*$//' -e '/^[[:space:]]*$/d' \
           slurm_jobs/gpu_exclude.txt | sort -u | paste -sd, -)"
bash -n slurm_jobs/run_training_length.sh
job="$(sbatch --parsable ${exclude:+--exclude="$exclude"} --array="${indices}%${concurrency}" \
       slurm_jobs/run_training_length.sh)"
echo "${job%%;*} indices=$indices excluded_nodes=$exclude partition=${SBATCH_PARTITION:-script default} submitted_utc=$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
    | tee -a "$provenance/slurm_job_ids.txt"
