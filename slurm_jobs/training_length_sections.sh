#!/bin/bash
# Shared definitions for the C3 training-length analysis: the two development sections, both core arms, seed 1. Reuses the Test R
# input, GMM K, K_bin and legacy-list helpers so the production settings are shared.
_paths="$(dirname "${BASH_SOURCE[0]}")/paths.sh"; [ -f "$_paths" ] || _paths="${SPATIAL_MSIPL_ROOT:-$HOME/msi}/slurm_jobs/paths.sh"; source "$_paths"
source "$PROJECT_ROOT/slurm_jobs/test_r_sections.sh"
TRAINING_LENGTH_SECTIONS=(GBM108_positive 40TopL)
TRAINING_LENGTH_ARMS=(central_only uniform_mean)
TRAINING_LENGTH_SNAPSHOTS="10 25 50"
TRAINING_LENGTH_RESULTS="$PROJECT_ROOT/results/experiments/training_length_20261030"
TRAINING_LENGTH_CHECKPOINTS="${TRAINING_LENGTH_CHECKPOINTS:-$CHECKPOINT_ROOT/spatial_msipl/training_length_20261030}"
TRAINING_LENGTH_FAIR="$PROJECT_ROOT/results/diagnostics/fair_scoring_baselines/training_length_20261030/bin_level_only"

training_length_result_root() { echo "$TRAINING_LENGTH_RESULTS/$1_seed1/$2"; }      # section arm
training_length_checkpoint_dir() { echo "$TRAINING_LENGTH_CHECKPOINTS/$1_seed1/$2"; }
training_length_fair_root() { echo "$TRAINING_LENGTH_FAIR/$1_seed1/$2"; }
