# Changes to S3PL

This folder contains a modified copy of S3PL v1.0.0 (https://github.com/CeMOS-IS/S3PL, commit `660e3d9`),
with files added for this project. It is licensed under the GNU Affero General Public
License v3.0 (`LICENSE`, copied unchanged from upstream). Every modified file starts with
a notice; `changes_from_660e3d9.diff` holds the full diff against upstream.

Why the code was changed: an HDF5 data source so S3PL reads the same inputs as the
other methods; explicit seeds and a configurable output root; an opt-in shuffled-
neighbour control; and the TIC/normalisation option recorded in `config.json`. The
released defaults are unchanged (tests in `tests/` check this).

## Modified upstream files
- `config.json`
- `main.py`
- `test.py`
- `tests/fixtures/pre_seed_flags/train.py`
- `train.py`
- `utils/create_pearson_labels.py`
- `utils/helpers.py`
- `utils/PeakEvaluation.py`

## Unchanged upstream files
- `data_configs.py`
- `model/Attention3DConvAutoencoder.py`

## Files added for this project (also AGPL-3.0)
- `environment.yml`
- `scripts/prepare_msipl_cac_h5.py`
- `slurm_jobs/prepare_msipl_cac_pilot.sh`
- `slurm_jobs/run_s3pl_cac.sh`
- `slurm_jobs/run_s3pl_cac_seeds.sh`
- `slurm_jobs/run_s3pl_gbm_seed_screen_array.sh`
- `slurm_jobs/run_s3pl_massnet_gbm.sh`
- `slurm_jobs/run_s3pl_rcc.sh`
- `slurm_jobs/submit_s3pl_cac_seeds.sh`
- `slurm_jobs/submit_s3pl_gbm_seed_screen.sh`
- `slurm_jobs/submit_s3pl_rcc.sh`
- `tests/fixtures/pre_seed_flags/README.md`
- `tests/fixtures/pre_test_n/data_source.py`
- `tests/test_frozen_patch_context.py`
- `tests/test_h5_data_source.py`
- `tests/test_nonlocal_shuffle.py`
- `tests/test_seed_flags_default.py`
- `utils/data_source.py`
- `utils/nonlocal_shuffle.py`
