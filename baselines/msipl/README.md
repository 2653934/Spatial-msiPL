# msiPL (not redistributed)

The legacy msiPL baseline (Abdelmoula et al., *Nature Communications*, 2021) is used from
your own clone of <https://github.com/wabdelmoula/msiPL> at commit `1e8d5cf`. msiPL is
distributed under the 3D Slicer Software License; Part B, which applies to downloads and
redistribution, is included here as `LICENSE-3DSlicer-PartB.txt`.

```bash
git clone https://github.com/wabdelmoula/msiPL.git baselines/msipl/msiPL
git -C baselines/msipl/msiPL checkout 1e8d5cf
python baselines/msipl/make_legacy_model.py   # or: python make_legacy_model.py /path/to/clone
```

`make_legacy_model.py` writes `Computational_Model_legacy.py` into the clone: upstream
`Computational_Model.py` with the three Keras-compatibility edits in
`computational_model_legacy.patch` (`ReLU()` → `Activation("relu")`), checked against the
SHA-256 of the file used for the report. `LearnPeaks.py` is used unchanged.

Our scripts (`scripts/run_msipl_legacy_gbm.py`, `tune_msipl_massnet_beta.py`,
`retune_msipl_beta.py`) import the clone from `$MSIPL_REPO` (default
`baselines/msipl/msiPL`) and run in the `msipl_legacy` environment
(`environment/msipl_legacy.yml`).
