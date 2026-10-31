#!/usr/bin/env python3
"""Regenerate every table summary and figure of the paper from the summary files in
results/, with the scripts in this repository, and compare them with the saved outputs.

Tables: the regenerated CSV/JSON must equal the saved ones (numbers to 1e-12, everything
else exactly). Figures: PNG files must be byte-identical to the expected SHA-256 values in
tools/expected_figures.json; PDF files are compared after removing their creation dates and
document IDs (PDF writers embed the time of writing). Writes nothing outside a temporary
folder (or --keep DIR, which must not exist).

Usage: python tools/check_regeneration.py [--figures-only | --tables-only] [--keep DIR]
"""

import argparse
import csv
import hashlib
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIAG = ROOT / "results" / "diagnostics"
TOLERANCE = 1e-12


def same(a, b, where):
    """Recursive comparison: numbers to 1e-12, everything else exactly."""
    if isinstance(a, bool) or isinstance(b, bool) or a is None or b is None:
        return [] if a == b else [f"{where}: {a!r} != {b!r}"]
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if math.isnan(a) and math.isnan(b):
            return []
        return [] if abs(a - b) <= TOLERANCE else [f"{where}: {a!r} != {b!r}"]
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b):
            return [f"{where}: keys differ {sorted(set(a) ^ set(b))[:5]}"]
        return [x for k in a for x in same(a[k], b[k], f"{where}.{k}")]
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [f"{where}: length {len(a)} != {len(b)}"]
        return [x for i, (p, q) in enumerate(zip(a, b)) for x in same(p, q, f"{where}[{i}]")]
    return [] if a == b else [f"{where}: {str(a)[:60]!r} != {str(b)[:60]!r}"]


def as_number(text):
    try:
        return float(text)
    except ValueError:
        return text


def read_table(path):
    with open(path, newline="", encoding="utf-8") as stream:
        return [{k: as_number(v) for k, v in row.items()} for row in csv.DictReader(stream)]


def compare_folder(regenerated, saved, names):
    problems = []
    for name in names:
        new, old = regenerated / name, saved / name
        if name.endswith(".json"):
            problems += same(json.loads(new.read_text(encoding="utf-8")),
                             json.loads(old.read_text(encoding="utf-8")), name)
        else:
            problems += same(read_table(new), read_table(old), name)
    return problems


def run(arguments, environment=None):
    python_path = [str(ROOT / "src"), str(ROOT / "scripts")]
    if os.environ.get("PYTHONPATH"):
        python_path.append(os.environ["PYTHONPATH"])
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(python_path), MPLBACKEND="Agg",
               **(environment or {}))
    result = subprocess.run([sys.executable, *arguments], cwd=ROOT, env=env,
                            capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f"failed: {' '.join(map(str, arguments))}\n{result.stderr[-2000:]}")
    return result


def tables(work):
    checks = {}
    out = work / "three_seed"
    run(["scripts/summarise_three_seed_main_table.py", "--project-root", str(ROOT), "--output", str(out)])
    checks["tab:main + F2 (summarise_three_seed_main_table.py)"] = compare_folder(
        out, DIAG / "three_seed_main_table_20261030_local",
        ["main_table.csv", "f2_seed_averaged.csv", "summary.json"])
    out = work / "msipl_retune"
    run(["scripts/summarise_msipl_retune.py", "--project-root", str(ROOT), "--output", str(out)])
    checks["tab:main RCC msiPL, RQ1 budget clause (summarise_msipl_retune.py)"] = compare_folder(
        out, DIAG / "fair_scoring_baselines" / "msipl_retune_20261030" / "decisions_20261031_local",
        ["decisions.json", "rcc_count_matched.csv"])
    out = work / "statistics"
    run(["scripts/compute_statistics_6_6.py", "--root",
         str(DIAG / "ig_steps_20261030" / "composite_root_6_6"), "--output", str(out)])
    saved = DIAG / "statistics_6_6_ig_steps_20261030"
    names = ["tests.csv", "mann_whitney.csv", "mixed_models.csv"]
    checks["tab:seeds HL, r, Holm (compute_statistics_6_6.py)"] = compare_folder(out, saved, names)
    out = work / "hardware"
    run(["scripts/summarise_runtime_hardware.py", "--project-root", str(ROOT), "--output", str(out)])
    checks["tab:runtime hardware (summarise_runtime_hardware.py)"] = compare_folder(
        out, DIAG / "runtime_hardware_20261030_local", ["runtime_hardware.csv"])
    checks["tab:seeds mean +- SD (recomputed from the Test R section table)"] = seed_sd_check()
    return checks


def seed_sd_check():
    """IG - posterior per collection x arm: seed-level collection means, mean +- SD (ddof 1),
    recomputed from section_table.csv against decisions.json."""
    import statistics
    folder = DIAG / "fair_scoring_baselines" / "test_r" / "decisions_20261030_ig_steps_local"
    rows = [r for r in read_table(folder / "section_table.csv") if r["scale"] == "bin"]
    decisions = json.loads((folder / "decisions.json").read_text(encoding="utf-8"))
    problems, checked = [], 0
    for key, record in decisions["decision_1"]["per_collection_arm_seed"].items():
        collection, arm, seed = key.split("/")
        values = [r["ig_mSCF1"] - r["posterior_mSCF1"] for r in rows
                  if r["collection"] == collection and r["arm"] == arm and int(r["seed"]) == int(seed[4:])]
        saved = record["IG_minus_posterior"]["bin"]["per_section"]
        problems += same(sorted(values), sorted(saved), key)
        checked += 1
    if checked != 18:
        problems.append(f"expected 18 collection-arm-seed records, found {checked}")
    return problems


def normalise_pdf(data):
    data = re.sub(rb"/(CreationDate|ModDate) *\(D:[^)]*\)", b"", data)
    data = re.sub(rb"/ID *\[<[0-9A-Fa-f]+> *<[0-9A-Fa-f]+>\]", b"", data)
    data = re.sub(rb"/PTEX\.FullBanner *\([^)]*\)", b"", data)
    # Byte offsets (cross-reference table, startxref) shift with the date strings' length.
    data = re.sub(rb"(?m)^\d{10} \d{5} [nf] *\r?$", b"", data)
    data = re.sub(rb"startxref\s+\d+", b"startxref", data)
    return hashlib.sha256(data).hexdigest()


def figure_digest(path):
    data = path.read_bytes()
    return normalise_pdf(data) if path.suffix == ".pdf" else hashlib.sha256(data).hexdigest()


def figures(work):
    out = work / "figures"
    environment = {"SPATIAL_MSIPL_FIGURE_OUTPUT": str(out), "SPATIAL_MSIPL_ALLOW_UNTRACKED": "1",
                   "SOURCE_DATE_EPOCH": "0"}
    run(["report_figures/seed_averaged_figures.py"], environment)
    run(["report_figures/dataset_overview.py"], environment)
    run(["scripts/plot_s3pl_seed_distributions.py", "--root",
         str(DIAG / "s3pl_seed_investigation_21"), "--out", str(out / "s3pl_released_seed_distributions")],
        environment)
    if shutil.which("pdflatex"):
        run(["report_figures/runtime_figure.py"], environment)
    expected = json.loads((ROOT / "tools" / "expected_figures.json").read_text(encoding="utf-8"))
    checks = {}
    for name, digest in expected.items():
        path = out / name
        if not path.exists():
            checks[f"{name}"] = ["not produced" + ("" if shutil.which("pdflatex") else
                                                    " (pdflatex not found)")]
            continue
        actual = figure_digest(path)
        checks[name] = [] if actual == digest else [f"digest {actual[:16]} != expected {digest[:16]}"]
    return checks


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tables-only", action="store_true")
    parser.add_argument("--figures-only", action="store_true")
    parser.add_argument("--keep", type=Path, help="keep the regenerated files here (must not exist)")
    args = parser.parse_args(argv)
    if args.keep is not None and args.keep.exists():
        raise SystemExit(f"exists: {args.keep}")
    work = Path(tempfile.mkdtemp(prefix="regeneration_")) if args.keep is None else args.keep
    work.mkdir(parents=True, exist_ok=True)
    checks = {}
    if not args.figures_only:
        checks.update(tables(work))
    if not args.tables_only:
        checks.update(figures(work))
    failed = 0
    for name, problems in checks.items():
        print(("PASS  " if not problems else "FAIL  ") + name)
        for problem in problems[:5]:
            print("      " + problem)
        failed += bool(problems)
    print(f"{len(checks) - failed}/{len(checks)} checks passed; regenerated files in {work}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
