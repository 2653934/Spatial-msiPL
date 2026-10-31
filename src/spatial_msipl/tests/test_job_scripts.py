"""Static checks on Slurm job scripts (no data or GPU needed).

Added 16 October 2026 after the RCC campaign was first specified with the
streaming HDF5 loader.
"""
import unittest
from pathlib import Path

JOBS = Path(__file__).resolve().parents[3] / "slurm_jobs"

# Historical scripts that must keep the streaming loader because they reproduce
# frozen pre-October baselines (the cached loader was validated on 28 September,
# investigation 10). Reason given per entry. Do not add new campaigns here.
STREAMING_ALLOWLIST = {
    "run_spatial_msipl_production.sh": "frozen GBM production baseline (Sept)",
    "run_spatial_msipl_central_only.sh": "frozen GBM centre-only baseline (Sept)",
    "run_spatial_msipl_cac_validation_training.sh": "frozen CAC production arms (Sept)",
    "run_spatial_msipl_gbm_validation_training.sh": "frozen GBM validation arms (Sept)",
}


class TrainingJobLoaderTests(unittest.TestCase):
    def test_training_jobs_use_cached_loader(self):
        scripts = sorted(JOBS.glob("*.sh"))
        self.assertTrue(scripts, f"no job scripts found under {JOBS}")
        missing = []
        for script in scripts:
            text = script.read_text()
            if "train_spatial_msipl_production.py" not in text:
                continue
            if script.name in STREAMING_ALLOWLIST:
                continue
            if "--cache-spectra" not in text:
                missing.append(script.name)
        self.assertEqual(missing, [], "training job scripts without --cache-spectra "
                         "(add the flag; the allowlist is for frozen historical baselines only)")

    def test_allowlist_entries_exist_and_stay_streaming(self):
        for name in STREAMING_ALLOWLIST:
            path = JOBS / name
            self.assertTrue(path.exists(), f"allowlisted script missing: {name}")
            self.assertIn("train_spatial_msipl_production.py", path.read_text())

    def test_rcc_campaign_is_cached(self):
        self.assertIn("--cache-spectra", (JOBS / "run_rcc_campaign.sh").read_text())


if __name__ == "__main__":
    unittest.main()
