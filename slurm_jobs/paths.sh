#!/bin/bash
# Configurable locations for every job script. Each job script sources this file first.
# Override any of them in the environment (for example in ~/.bashrc or before sbatch):
#   SPATIAL_MSIPL_ROOT         this repository              (default: $HOME/msi)
#   SPATIAL_MSIPL_DATA         input HDF5 folders            (default: $SPATIAL_MSIPL_ROOT/data)
#   SPATIAL_MSIPL_CHECKPOINTS  model checkpoints             (default: $SPATIAL_MSIPL_ROOT/checkpoints)
#   SPATIAL_MSIPL_PYTHON       Python of the main environment (default: python3)
#   SPATIAL_MSIPL_RSCRIPT      Rscript for the RCC export      (default: Rscript)
#   SPATIAL_MSIPL_CONDA_SH     conda.sh, for the msiPL environment (default: $HOME/miniconda3/etc/profile.d/conda.sh)
#   MSIPL_REPO                 a clone of msiPL at 1e8d5cf     (default: $SPATIAL_MSIPL_ROOT/baselines/msipl/msiPL)
# The data folder holds gbm_massnet/, cac_msipl/ and rcc_cardinal/ (see README).
PROJECT_ROOT="${SPATIAL_MSIPL_ROOT:-$HOME/msi}"
DATA_ROOT="${SPATIAL_MSIPL_DATA:-$PROJECT_ROOT/data}"
CHECKPOINT_ROOT="${SPATIAL_MSIPL_CHECKPOINTS:-$PROJECT_ROOT/checkpoints}"
SPATIAL_MSIPL_PYTHON="${SPATIAL_MSIPL_PYTHON:-python3}"
SPATIAL_MSIPL_RSCRIPT="${SPATIAL_MSIPL_RSCRIPT:-Rscript}"
SPATIAL_MSIPL_CONDA_SH="${SPATIAL_MSIPL_CONDA_SH:-$HOME/miniconda3/etc/profile.d/conda.sh}"
MSIPL_REPO="${MSIPL_REPO:-$PROJECT_ROOT/baselines/msipl/msiPL}"
export PROJECT_ROOT DATA_ROOT CHECKPOINT_ROOT SPATIAL_MSIPL_PYTHON SPATIAL_MSIPL_RSCRIPT \
    SPATIAL_MSIPL_CONDA_SH MSIPL_REPO
