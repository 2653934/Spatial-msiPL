"""Configurable locations: paths.py and slurm_jobs/paths.sh defaults and overrides, every
job script sources paths.sh first, and no cluster-specific location is left in the code."""

import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from spatial_msipl import paths

ROOT = Path(__file__).resolve().parents[3]
JOBS = ROOT / "slurm_jobs"
BASH = shutil.which("bash")
VARIABLES = ("SPATIAL_MSIPL_ROOT", "SPATIAL_MSIPL_DATA", "SPATIAL_MSIPL_CHECKPOINTS", "MSIPL_REPO")
FORBIDDEN_TERMS = tuple(left + right for left, right in (
    ("Cl", "aude"), ("Cod", "ex"), ("Open", "AI"), ("Anth", "ropic"),
    ("super", "visor"), ("ch", "at"), ("zsu", "liman"), ("mscl", "uster"),
    ("/home-ms", "cluster"),
))
PRIVATE_LOCATION = re.compile("|".join((
    re.escape("/data" + "sets/"),
    re.escape("/ho" + "me-") + r"[^/\s]+/[^/\s]+/",
    re.escape("146" + ".141."),
    re.escape("ms" + ".wits.ac.za"),
)), re.IGNORECASE)
# Outside the tests (which build a temporary $HOME/msi tree), no script may hard-code $HOME/msi/.
HOME_MSI = re.compile(r"\$HOME/msi/(?!slurm_jobs/paths\.sh)")


def clean_environment():
    return {k: v for k, v in os.environ.items() if k not in VARIABLES}


class PythonPathsTests(unittest.TestCase):
    def setUp(self):
        self.saved = {k: os.environ.pop(k) for k in VARIABLES if k in os.environ}
        self.addCleanup(os.environ.update, self.saved)

    def test_defaults_are_inside_the_repository(self):
        self.assertEqual(paths.project_root(), ROOT)
        self.assertEqual(paths.data_root(), ROOT / "data")
        self.assertEqual(paths.checkpoint_root(), ROOT / "checkpoints")
        self.assertEqual(paths.msipl_repo(), ROOT / "baselines" / "msipl" / "msiPL")

    def test_overrides(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["SPATIAL_MSIPL_ROOT"] = tmp
            self.assertEqual(paths.data_root(), Path(tmp) / "data")
            os.environ["SPATIAL_MSIPL_DATA"] = str(Path(tmp) / "d")
            os.environ["SPATIAL_MSIPL_CHECKPOINTS"] = str(Path(tmp) / "c")
            os.environ["MSIPL_REPO"] = str(Path(tmp) / "m")
            self.assertEqual(paths.data_root(), Path(tmp) / "d")
            self.assertEqual(paths.checkpoint_root(), Path(tmp) / "c")
            self.assertEqual(paths.msipl_repo(), Path(tmp) / "m")
        for name in VARIABLES:
            os.environ.pop(name, None)


@unittest.skipUnless(BASH, "bash not available")
class ShellPathsTests(unittest.TestCase):
    def evaluate(self, **environment):
        script = ('source slurm_jobs/paths.sh; printf "%s\\n" "$PROJECT_ROOT" "$DATA_ROOT" '
                  '"$CHECKPOINT_ROOT" "$SPATIAL_MSIPL_PYTHON" "$MSIPL_REPO"')
        result = subprocess.run([BASH, "-c", script], cwd=ROOT, capture_output=True, text=True,
                                env=dict(clean_environment(), **environment))
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.split("\n")[:5]

    def test_defaults(self):
        self.assertEqual(self.evaluate(HOME="/h"), [
            "/h/msi", "/h/msi/data", "/h/msi/checkpoints", "python3",
            "/h/msi/baselines/msipl/msiPL"])

    def test_overrides(self):
        self.assertEqual(self.evaluate(HOME="/h", SPATIAL_MSIPL_ROOT="/r", SPATIAL_MSIPL_DATA="/d",
                                       SPATIAL_MSIPL_CHECKPOINTS="/c", SPATIAL_MSIPL_PYTHON="py",
                                       MSIPL_REPO="/m"),
                         ["/r", "/d", "/c", "py", "/m"])
        self.assertEqual(self.evaluate(HOME="/h", SPATIAL_MSIPL_ROOT="/r")[1], "/r/data")


class JobScriptRootTests(unittest.TestCase):
    def scripts(self):
        found = sorted(JOBS.glob("*.sh")) + sorted((ROOT / "baselines" / "s3pl" / "slurm_jobs").glob("*.sh"))
        self.assertGreater(len(found), 40)
        return [p for p in found if p.name != "paths.sh"]

    def test_every_job_script_sources_paths_before_its_first_command(self):
        for script in self.scripts():
            lines = [l for l in script.read_text(encoding="utf-8").split("\n")
                     if l.strip() and not l.lstrip().startswith("#")]
            self.assertTrue(lines and lines[0].startswith('_paths="$(dirname "${BASH_SOURCE[0]}")/paths.sh"'),
                            script.name)
            self.assertIn('source "$_paths"', lines[0], script.name)

    def test_no_hard_coded_node_exclusions(self):
        for script in self.scripts():
            self.assertNotRegex(script.read_text(encoding="utf-8"), r"#SBATCH --exclude=", script.name)


class PublicTreeHygieneTests(unittest.TestCase):
    def test_tree_has_no_internal_terms_paths_users_or_hosts(self):
        offenders = []
        for path in sorted(ROOT.rglob("*")):
            if (not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts
                    or path.suffix == ".pyc"):
                continue
            rel = path.relative_to(ROOT).as_posix()
            text = path.read_text(encoding="utf-8", errors="replace")
            for number, line in enumerate(text.split("\n"), 1):
                home = HOME_MSI.search(line) and "/tests/" not in rel
                internal = any(term.lower() in line.lower() for term in FORBIDDEN_TERMS)
                if PRIVATE_LOCATION.search(line) or home or internal:
                    offenders.append(f"{rel}:{number}: {line.strip()[:80]}")
        self.assertEqual(offenders, [])

    def test_figure_scripts_read_and_write_configurable_locations(self):
        for name in ("seed_averaged_figures.py", "dataset_overview.py", "runtime_figure.py",
                     "qualitative_example.py"):
            text = (ROOT / "report_figures" / name).read_text(encoding="utf-8")
            self.assertIn('os.environ.get("SPATIAL_MSIPL_RESULTS"', text, name)
            self.assertIn('os.environ.get("SPATIAL_MSIPL_FIGURE_OUTPUT"', text, name)
            self.assertNotIn('"code" / "msi"', text, name)


if __name__ == "__main__":
    unittest.main()
