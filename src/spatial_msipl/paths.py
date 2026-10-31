"""Configurable locations, read from the environment, with documented defaults.

The same variables as slurm_jobs/paths.sh:
  SPATIAL_MSIPL_ROOT         this repository (default: the folder that holds src/)
  SPATIAL_MSIPL_DATA         input HDF5 folders (default: <root>/data)
  SPATIAL_MSIPL_CHECKPOINTS  model checkpoints (default: <root>/checkpoints)
  MSIPL_REPO                 a clone of msiPL at commit 1e8d5cf
                             (default: <root>/baselines/msipl/msiPL)
"""

import os
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[2]


def project_root():
    return Path(os.environ.get("SPATIAL_MSIPL_ROOT", DEFAULT_ROOT))


def data_root():
    return Path(os.environ.get("SPATIAL_MSIPL_DATA", project_root() / "data"))


def checkpoint_root():
    return Path(os.environ.get("SPATIAL_MSIPL_CHECKPOINTS", project_root() / "checkpoints"))


def msipl_repo():
    return Path(os.environ.get("MSIPL_REPO", project_root() / "baselines" / "msipl" / "msiPL"))
