# Spatial-msiPL

**Spatial-aware peak ranking for mass spectrometry imaging (MSI).** This project builds on
two earlier methods, and its name credits the first:

- **msiPL** (Abdelmoula et al., 2021): unsupervised peak learning with a variational
  autoencoder. Code: <https://github.com/wabdelmoula/msiPL> (we use commit `1e8d5cf`).
- **S3PL** (Weigand et al., 2026, arXiv:2603.10487): self-supervised spatial peak learning
  and the mSCF1 evaluation used here. Code: <https://github.com/CeMOS-IS/S3PL> (v1.0.0,
  commit `660e3d9`).

Spatial-msiPL feeds the msiPL encoder each pixel's 3×3 neighbourhood (or only the centre
pixel), fits a Gaussian mixture to the latent means, and ranks m/z bins either by
Integrated Gradients (IG) through the encoder or by the correlation of each ion image with
the mixture's posterior maps. Every ranking is scored under one fair protocol (the same
segmentation and the same number of bins, K_bin) against label-free baselines (Moran's I,
mean intensity, variance), the original msiPL and S3PL, on three public collections.

This repository accompanies the Honours research report *Spatial Aware Peak Ranking in Mass
Spectrometry Imaging* (University of the Witwatersrand, 2026). Release `v1.0` was the first
cited; `v1.1` adds the label-free K analysis and two report figures (see below).
It contains only the code that produces the report's tables and figures, the small summary
files they are built from, and a check that the scripts rebuild them. Exploratory and
superseded analyses are kept in the private research repository and are not part of this
release.

## Datasets

None of the raw data is redistributed. The three collections are those used by S3PL.

| Collection | Tissue | Source | Original publication |
|---|---|---|---|
| GBM | Mouse PDX glioblastoma; 8 sections from 4 PDX lines (MALDI FT-ICR) | NIH Metabolomics Workbench study **ST002045** (project PR001292), doi:[10.21228/M8Q70T](https://doi.org/10.21228/M8Q70T) | Abdelmoula et al., MassNet, *Bioinformatics* 38(7), 2022, doi:10.1093/bioinformatics/btac032 |
| CAC | Human colorectal adenocarcinoma; 8 of 52 serial sections of one tumour (DESI) | MetaboLights **[MTBLS415](https://www.ebi.ac.uk/metabolights/MTBLS415)**; the 8 sections as shared by the S3PL authors (linked from the S3PL README) | Inglese et al., *Chemical Science* 8(5), 2017 |
| RCC | Human renal cell carcinoma; 8 runs, each a matched cancer/normal pair (DESI) | Bioconductor **[CardinalWorkflows](https://bioconductor.org/packages/CardinalWorkflows) 1.44.0**, `rcc` dataset | Dill et al., *Anal. Bioanal. Chem.*, 2010 (as cited in `CardinalWorkflows/man/rcc-data.Rd`) |

Archives used, with SHA-256:

| Archive | Contents | SHA-256 |
|---|---|---|
| `ST002045_massNet.7z` | GBM MassNet HDF5 (85,062 bins) | `7b1f296b4a0d6b8a8057b02d254db32f72cb56f73ee0a5b56ed12432dcaaafe1` |
| `gbm_data.zip` | GBM imzML and masks (used only to validate the HDF5) | `a69a42464932c5c2af95b7fb2259cf7fd9590ff86ff0e5f170398e9519aa097f` |
| `cac_data.zip` | CAC imzML, 8 sections (1,481 bins) | `30274f25c9d276f0e091154090d359aa302fe3f14d46eef699145a879d0f298e` |
| `CardinalWorkflows_1.44.0.tar.gz` | RCC (`rcc.rda`; 10,200 bins) | `301a38159adc03243459095b5d7836f5900687e48e332b5e704b98e28a18c485` |

**Layout the code reads** (under `$SPATIAL_MSIPL_DATA`, default `data/`):

- `gbm_massnet/<section>.h5`: the MassNet HDF5 files as released (`Data`, `mzArray`,
  `Class_Label`, `xLocation`, `yLocation`). These spectra are already TIC-normalised.
- `cac_msipl/<section>.h5`: from the CAC imzML and masks with
  `baselines/s3pl/scripts/prepare_msipl_cac_h5.py --input … --mask … --output … --audit …`
  (job `slurm_jobs/run_msipl_cac_section.sh`).
- `rcc_cardinal/RCC_<run>.h5`: from `rcc.rda` with
  `Rscript scripts/rcc_feasibility_export.R <rcc.rda> <export_dir> <report.json>`
  (job `slurm_jobs/run_rcc_feasibility.sh`). Labels: 0 cancer, 1 normal, 2 unannotated.

The CAC masks have three classes: 0 is background (it surrounds the tissue in every
section); 1 and 2 are tumour and healthy tissue in an order the dataset does not document.

## Environment

The results were produced on a Slurm cluster (NVIDIA RTX 3090 for training; Intel
i5-14400 and i9-10940X CPU nodes for ranking). Three environments are given in
`environment/`:

- `spatial_msipl.yml`: Python 3.11.5, PyTorch 2.3.0 (CUDA 12.1), NumPy 2.4.6, SciPy 1.18.1,
  scikit-learn 1.9.0, h5py 3.16.0, matplotlib 3.11.2, pandas 3.0.5 and statsmodels 0.15.0. Everything except msiPL
  and the RCC export runs here.
- `msipl_legacy.yml`: Python 3.6.10, NumPy 1.14.2, TensorFlow 1.8.0, Keras 2.1.5, for msiPL.
- `rcc_export.yml`: R 4.5.3 with Cardinal 3.12.1, CardinalIO 1.8.0 and rhdf5 2.56.1.

**Locations** are set by environment variables (defaults in brackets), read by
`slurm_jobs/paths.sh` and `src/spatial_msipl/paths.py`:

| Variable | Meaning | Default |
|---|---|---|
| `SPATIAL_MSIPL_ROOT` | this repository | `$HOME/msi` (jobs); the repository (Python) |
| `SPATIAL_MSIPL_DATA` | input HDF5 folders | `<root>/data` |
| `SPATIAL_MSIPL_CHECKPOINTS` | model checkpoints | `<root>/checkpoints` |
| `SPATIAL_MSIPL_PYTHON` | Python of `spatial_msipl` | `python3` |
| `SPATIAL_MSIPL_RSCRIPT`, `SPATIAL_MSIPL_CONDA_SH` | R and conda for the other two environments | `Rscript`, `$HOME/miniconda3/etc/profile.d/conda.sh` |
| `MSIPL_REPO` | your msiPL clone | `baselines/msipl/msiPL` |
| `SPATIAL_MSIPL_RESULTS`, `SPATIAL_MSIPL_FIGURE_OUTPUT` | figure inputs and outputs | `results/`, `report_figures/output/` |
| `SPATIAL_MSIPL_RECORDED_ROOT` | the root recorded in saved provenance paths | `<project-root>/`, matching the sanitised release summaries |

GPU submitters exclude the nodes listed in `slurm_jobs/gpu_exclude.txt` (empty by default).
Partition names (`batch`, `bigbatch`) are those of our cluster; change them in the
`#SBATCH` lines or with `SBATCH_PARTITION`.

**msiPL** is not redistributed. Clone it and create the legacy model file once:

```bash
git clone https://github.com/wabdelmoula/msiPL.git baselines/msipl/msiPL
git -C baselines/msipl/msiPL checkout 1e8d5cf
python baselines/msipl/make_legacy_model.py      # writes Computational_Model_legacy.py
```

## How to run each stage

Each stage is a Slurm job script in `slurm_jobs/` (S3PL jobs in `baselines/s3pl/slurm_jobs/`);
the comment block at the top of each script gives its usage. Outputs go under `results/`,
and every script refuses to overwrite an existing output.

1. **Data** (above): GBM HDF5, CAC and RCC conversions.
2. **Legacy msiPL and the budget K_bin**: `run_msipl_massnet_gbm.sh`, `tune_msipl_massnet_beta.sh`,
   `run_msipl_cac_section.sh`, `run_msipl_rcc.sh`. On GBM and CAC, K_bin is the tuned msiPL
   peak count; on RCC it is S3PL's released target (`run_rcc_preparation.sh`).
3. **Spatial-msiPL, seed 1** (training, GMM, IG, matched evaluation):
   `run_spatial_msipl_central_only.sh`, `run_spatial_msipl_production.sh`,
   `run_spatial_msipl_gbm_validation_training.sh`, `run_spatial_msipl_cac_validation_training.sh`,
   then `run_spatial_msipl_gbm_attribution.sh` and `run_spatial_msipl_cac_attribution.sh`;
   RCC: `submit_rcc.sh`.
4. **Seeds 2 and 3**: `submit_test_r.sh`. **IG completeness reruns** (more IG steps where
   the completeness check failed): `submit_ig_steps.sh`.
5. **Fair scoring** (all rankings and baselines at K_bin, bin level and P1 peaks):
   `submit_peak_partition_audit.sh`, `submit_fair_scoring.sh`, `run_fair_scoring_summary.sh`,
   `run_rcc_fair_scoring.sh`, and the `fair` stage of `submit_test_r.sh`.
6. **Neighbourhood variants**: attention, 5×5/7×7/9×9 windows and centre masking
   (`run_spatial_attention_context_*.sh`, `run_spatial_window_pilot_*.sh`,
   `submit_window_e79_campaign.sh`, `submit_centremask_campaign.sh`), scored with
   `run_fair_scoring_extra_arm.sh`.
7. **VAE vs PCA segmentation**: `submit_segmentation_control_v.sh`.
8. **msiPL budget re-tune** (msiPL re-thresholded at 0.5–2 × K_bin, count-matched scoring):
   `submit_msipl_retune.sh sweep …`, then `submit_msipl_retune.sh score …`.
9. **Ranking-stage timing**: `run_ranking_stage_timing.sh`.
10. **S3PL**: `baselines/s3pl/slurm_jobs/` (CAC, GBM, RCC and the seed runs).
11. **Training length** (scores and loss at epochs 10/25/50/100 on the development
    sections): `submit_training_length.sh`, then `scripts/summarise_training_length.py`.
12. **Label-free K** (GMM K chosen by BIC instead of the class count; seed 1):
    `submit_label_free_k.sh bic …`, then `submit_label_free_k.sh ig 64 …` (128–1024 only
    where IG completeness fails), then `submit_label_free_k.sh fair …`, then
    `scripts/summarise_label_free_k.py`.
13. **Summaries, tables and figures** (local, no GPU): the summarisers below, then
    `python tools/check_regeneration.py`.

Tests: `python -m unittest discover -s src -t src` with `PYTHONPATH=src:scripts`
(tests needing PyTorch, HDF5 inputs or bash skip when these are absent);
`slurm_jobs/run_fair_scoring_tests.sh` runs the full suite on the cluster. S3PL's tests
run from `baselines/s3pl` with `python -m unittest discover tests`.

## Tables and figures → script → result files

| Report item | Script | Result files (under `results/`) |
|---|---|---|
| Table: dataset overview | `scripts/export_mz_axes.py`, `scripts/export_section_images.py` | `diagnostics/mz_axis_20261030/mz_axis.json`, `diagnostics/dataset_contact_20261031/summary.json` |
| Figure: dataset overview | `report_figures/dataset_overview.py` | `diagnostics/dataset_contact_20261031/`, `diagnostics/dataset_basepeak_gbm_20261031/` |
| Figure: pipeline | `report_figures/pipeline.tex` | (no data) |
| Table: main results (three seeds) | `scripts/summarise_three_seed_main_table.py` | inputs: `diagnostics/fair_scoring_baselines/{test_r/decisions_20261030_ig_steps_local, bin_level_only/summary_66097, rcc/decisions_20261030_ig_steps_p1_local}`, the seed-2/3 summaries under `diagnostics/ig_steps_20261030/composite_root/`; output: `diagnostics/three_seed_main_table_20261030_local/` |
| Table: main, RCC msiPL; text: msiPL budget stability | `scripts/summarise_msipl_retune.py` | `diagnostics/fair_scoring_baselines/msipl_retune_20261030/` (`decisions_20261031_local/`) |
| Table: IG minus posterior correlation, three seeds | `scripts/summarise_test_r.py`, `scripts/compute_statistics_6_6.py` | `diagnostics/fair_scoring_baselines/test_r/decisions_20261030_ig_steps_local/`, `diagnostics/statistics_6_6_ig_steps_20261030/` (inputs `diagnostics/ig_steps_20261030/composite_root_6_6/`) |
| Figure: IG minus correlation per section | `report_figures/seed_averaged_figures.py` | `…/test_r/decisions_20261030_ig_steps_local/section_table.csv` |
| Figure: neighbourhood variants | `report_figures/seed_averaged_figures.py` | the Test R table and `…/extra_arms/decisions_20261016_local/` |
| Figure: VAE vs PCA | `report_figures/seed_averaged_figures.py` | `diagnostics/segmentation_control_V/decisions_20261030_with_test_r_ig_steps_local/` |
| Figure: S3PL seed variation | `scripts/plot_s3pl_seed_distributions.py` (`--root results/diagnostics/s3pl_seed_investigation_21`) | `diagnostics/s3pl_seed_investigation_21/{part_a_released,part_b}/` |
| Figure: runtime (whole workflow, CAC 160TopL, three repeats) | `report_figures/runtime_figure.py` | `comparisons/s3pl_gbm_stability_runtime/runtime_repeats.csv` |
| Text: runtime (ranking stage, hardware) | `scripts/summarise_runtime_hardware.py` | `diagnostics/ranking_stage_runtime*/`, `publication/current_evidence/runtime_all_sections_v2.csv`, `diagnostics/runtime_hardware_20261030_local/` |
| Text: VAE training length | `scripts/summarise_training_length.py` | `diagnostics/fair_scoring_baselines/training_length_20261030/decisions_20261031_local/` |
| Table: label-free K (Table IV); Section V-H | `scripts/summarise_label_free_k.py` | inputs: `experiments/label_free_k_20261104/`, `diagnostics/fair_scoring_baselines/label_free_k_20261104/bin_level_only/`, the seed-1 production summaries under `diagnostics/ig_steps_20261030/composite_root/`, `diagnostics/gate_d_bic*/`; output: `diagnostics/fair_scoring_baselines/label_free_k_20261104/decisions_20261104_local/` |
| Figure: qualitative example (GBM39_2) | `report_figures/qualitative_example.py` | `diagnostics/dataset_contact_20261031/GBM39_2.npz`, the K = 2 and K = 6 `coordinates_and_gmm.npz`, `visualisations/qualitative_example/`, the label-free K `per_section.csv` |

## Label-free K analysis (added in v1.1)

The GMM's K normally equals the number of annotated classes, so the segmentation is
label-free in training and ranking but class-informed in its component count. This
analysis repeats the ranking comparison with K chosen without labels: BIC on the saved
seed-1 latent means (candidates K = 1–6), GMM refitted at that K, IG and posterior
correlation recomputed from the same trained models, and everything scored by the
unchanged fair evaluator at the same K_bin (bin level, all classes). BIC chose K = 6, the
largest value tested, in all 48 section-arms. The predeclared rule asks whether
correlation still beats IG in at least 7 of 8 sections; the rankings that do not depend
on K (mean intensity, variance, Moran's I, the oracle and legacy msiPL) must reproduce
their earlier scores exactly, and did. The rule held on CAC and RCC in both arms but not
on GBM (2/8 and 5/8 sections), where correlation and IG became about equal. The decision
table is
`results/diagnostics/fair_scoring_baselines/label_free_k_20261104/decisions_20261104_local/`
(`decisions.json`, `per_section.csv`); Table IV of the report is built from it.

Code: `scripts/resolve_label_free_k.py` (reads K from the BIC record), the opt-in
`--no-component-mapping` of `scripts/evaluate_spatial_msipl_attributed_peaks.py` (ARI and
NMI only when K differs from the class count; the default path is unchanged, tested
against the v1.0 copy), a figure palette in `scripts/run_spatial_msipl_gmm_integrated_gradients.py`
that covers K = 6, `scripts/summarise_label_free_k.py`, the `*label_free_k*.sh` jobs and
`src/spatial_msipl/tests/test_label_free_k.py`.

**New figures in v1.1.** `report_figures/qualitative_example.py` draws the expert mask and
the K = 2 and K = 6 segmentations of GBM39_2, the section a rule fixed before plotting
selects (the fourth of the eight GBM sections ordered by IG minus correlation at class K);
it recomputes that order and refuses any other section. `report_figures/runtime_figure.py`
now draws the whole-workflow comparison (VAE training, GMM fit and IG, peak scoring
against S3PL) instead of the v1.0 ranking-time and training-cache panels.

`docs/whitelist.tsv` lists every file in this release with its source and its purpose.

**Regeneration check.** `python tools/check_regeneration.py` reruns these scripts on the
files in `results/` and compares the outputs with the saved summaries (numbers to 1e-12)
and with the report's figures (PNG byte-identical; PDF identical apart from creation dates,
document IDs and byte offsets). It also checks the values the report prints from the
label-free K table and the two new figures. It needs `pdflatex` for the runtime figure.
Figure digests are those of the environment in `environment/spatial_msipl.yml`
(matplotlib 3.11.2) with MiKTeX pdfTeX 1.40.29; another matplotlib or TeX version draws the
same figure with different bytes. All 17 checks pass for this release. Numerical result
fields are copied unchanged; private provenance paths, node names and internal process
notes are replaced by documented placeholders (`<project-root>`, `<data-root>`,
`<checkpoint-root>`, `<compute-node>`). The label-free K check therefore compares
recorded paths with `/` separators and skips `production_reference_sha256`, which hashes
the private copy of each production summary before its paths were replaced.

## Licences

- **Our code** (everything outside `baselines/`): MIT, see `LICENSE`.
- **`baselines/s3pl/`**: a modified copy of S3PL v1.0.0 plus the files that import it,
  under the **GNU Affero General Public License v3.0** (`baselines/s3pl/LICENSE`, unchanged
  from upstream). Each modified file starts with a notice; `CHANGES.md` and
  `changes_from_660e3d9.diff` list every change.
- **msiPL** is not redistributed. Its licence is the 3D Slicer Software License; Part B is
  included as `baselines/msipl/LICENSE-3DSlicer-PartB.txt`. Our only change to msiPL, three
  Keras-compatibility edits, is given as `baselines/msipl/computational_model_legacy.patch`
  and applied to your clone by `make_legacy_model.py`.
- Each dataset keeps the terms of its original repository.

## Citation

If you use this code, please cite the report and this release (see `CITATION.cff`), and the
msiPL and S3PL papers:

```bibtex
@thesis{suliman2026spatialmsipl,
  author = {Suliman, Zayd},
  title  = {Spatially Aware Peak Ranking in Mass Spectrometry Imaging},
  school = {University of the Witwatersrand},
  type   = {Honours research report},
  year   = {2026},
  note   = {Code: https://github.com/2653934/Spatial-msiPL, release v1.1}
}
```
