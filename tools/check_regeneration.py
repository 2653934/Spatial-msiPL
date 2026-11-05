#!/usr/bin/env python3
"""Regenerate every table summary and figure of the paper from the summary files in
results/, with the scripts in this repository, and compare them with the saved outputs.

Tables: the regenerated CSV/JSON must equal the saved ones (numbers to 1e-12, everything
else exactly). Figures: PNG files must be byte-identical to the expected SHA-256 values in
tools/expected_figures.json; PDF files are compared after removing their creation dates and
document IDs (PDF writers embed the time of writing). The values the report prints from
the label-free K table (Table IV, Section V-H) and the two figures that print numbers (the
ARI of the qualitative example, the workflow totals of the runtime figure) are also
checked. Writes nothing outside a temporary folder (or --keep DIR, which must not exist).

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
import statistics
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
    out = work / "label_free_k"
    run(["scripts/summarise_label_free_k.py", "--results-root", "results", "--composite-root",
         "results/diagnostics/ig_steps_20261030/composite_root", "--output", str(out)])
    checks["tab:lfk + Sec. V-H (summarise_label_free_k.py)"] = label_free_k_check(out)
    checks["tab:lfk cells and Sec. V-H values as printed in the report"] = label_free_k_values(out)
    return checks


LABEL_FREE_K = DIAG / "fair_scoring_baselines" / "label_free_k_20261104" / "decisions_20261104_local"


def portable(value, key=None):
    """Path strings with '/' (the summariser records paths with the OS separator), and
    production_reference_sha256 dropped: it hashes the private copy of each production
    summary, whose provenance paths were replaced by placeholders in this release."""
    if isinstance(value, dict):
        return {k: portable(v, k) for k, v in value.items() if k != "production_reference_sha256"}
    if isinstance(value, list):
        return [portable(v) for v in value]
    if isinstance(value, str) and key in ("production_reference", "fair_summary", "source"):
        return value.replace("\\", "/")
    return value


def label_free_k_check(out):
    new = json.loads((out / "decisions.json").read_text(encoding="utf-8"))
    old = json.loads((LABEL_FREE_K / "decisions.json").read_text(encoding="utf-8"))
    problems = same(portable(new), portable(old), "decisions.json")
    return problems + same(read_table(out / "per_section.csv"),
                           read_table(LABEL_FREE_K / "per_section.csv"), "per_section.csv")


# Table IV of the report (correlation minus IG at class K and at K = 6, sections where
# correlation is higher, and the strongest unsupervised ranking at K = 6), as printed.
TABLE_IV = {
    ("GBM", "central_only"): ("+0.225", "-0.019", 2, "morans_i", "0.684"),
    ("GBM", "uniform_mean"): ("+0.233", "+0.006", 5, "morans_i", "0.684"),
    ("CAC", "central_only"): ("+0.078", "+0.045", 8, "mean_intensity", "0.612"),
    ("CAC", "uniform_mean"): ("+0.047", "+0.025", 7, "mean_intensity", "0.612"),
    ("RCC", "central_only"): ("+0.156", "+0.073", 8, "morans_i", "0.631"),
    ("RCC", "uniform_mean"): ("+0.169", "+0.054", 7, "morans_i", "0.631"),
}


def label_free_k_values(out):
    decisions = json.loads((out / "decisions.json").read_text(encoding="utf-8"))
    problems = []
    for cell in decisions["cells"]:
        key = (cell["collection"], cell["arm"])
        means = {m: v for m, v in cell["descriptive_means_label_free_k"].items()
                 if isinstance(v, float)}
        best = max(means, key=means.get)
        printed = (f"{cell['production_mean_correlation_minus_ig']:+.3f}",
                   f"{cell['mean_correlation_minus_ig']:+.3f}", cell["correlation_beats_ig"],
                   best, f"{means[best]:.3f}")
        if printed != TABLE_IV[key]:
            problems.append(f"{key}: {printed} != report {TABLE_IV[key]}")
    if len(decisions["cells"]) != 6 or not all(r["label_free_k"] == 6 for r in decisions["sections"]):
        problems.append("expected six cells and K = 6 in 48/48 section-arms")
    # Sec. V-H text: correlation fell by 0.25-0.28 (GBM), 0.06-0.10 (RCC), 0.02-0.03 (CAC);
    # IG changed by at most 0.04; GBM mean ARI 0.19; IG > legacy msiPL in 8/8 (GBM, CAC).
    ranges = {"GBM": (0.25, 0.28), "RCC": (0.06, 0.10), "CAC": (0.02, 0.03)}
    for collection, (low, high) in ranges.items():
        for cell in (c for c in decisions["cells"] if c["collection"] == collection):
            k6, production = (cell["descriptive_means_label_free_k"],
                              cell["descriptive_means_production_k"])
            drop = round(production["posterior_abs_pcc_balanced"] - k6["posterior_abs_pcc_balanced"], 2)
            if not low <= drop <= high:
                problems.append(f"{collection} {cell['arm']}: correlation drop {drop}")
            change = abs(k6["integrated_gradients"] - production["integrated_gradients"])
            if round(change, 2) > 0.04:
                problems.append(f"{collection} {cell['arm']}: IG change {change:.3f}")
    gbm = [c for c in decisions["cells"] if c["collection"] == "GBM"]
    ari = statistics.fmean(c["mean_ari"] for c in gbm)
    if f"{ari:.2f}" != "0.19":
        problems.append(f"GBM mean ARI {ari:.3f} != 0.19")
    for collection in ("GBM", "CAC"):
        for arm in ("central_only", "uniform_mean"):
            wins = sum(r["label_free"]["integrated_gradients"] > r["label_free"]["legacy_msipl"]
                       for r in decisions["sections"]
                       if r["collection"] == collection and r["arm"] == arm)
            if wins != 8:
                problems.append(f"{collection} {arm}: IG > legacy in {wins}/8")
    return problems


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


def qualitative_values(stdout):
    """The section the predeclared rule selects and the ARI values the figure prints."""
    problems = []
    if "  4. GBM39_2:" not in stdout:
        problems.append("rule does not place GBM39_2 4th")
    match = re.search(r"Section (\S+): ARI K=2 ([0-9.]+), K=6 ([0-9.]+)", stdout)
    if match is None:
        return problems + ["no ARI line printed"]
    shown = (match.group(1), f"{float(match.group(2)):.2f}", f"{float(match.group(3)):.2f}")
    if shown != ("GBM39_2", "0.35", "0.21"):
        problems.append(f"{shown} != ('GBM39_2', '0.35', '0.21')")
    return problems


def runtime_values():
    """Workflow totals per repeat (VAE training + GMM fit and IG + peak scoring; S3PL), from
    the timing table the runtime figure draws, against the report's 122-135 s and 151-174 s."""
    path = ROOT / "results" / "comparisons" / "s3pl_gbm_stability_runtime" / "runtime_repeats.csv"
    rows = read_table(path)
    jobs = sorted({row["job_id"] for row in rows})
    stage = {(row["job_id"], row["stage"]): row["wall_seconds"] for row in rows}
    vae = sorted(round(sum(stage[(job, s)] for s in ("vae_train", "vae_attribution",
                                                      "vae_peak_evaluation"))) for job in jobs)
    s3pl = sorted(round(stage[(job, "s3pl_full")]) for job in jobs)
    problems = [] if len(jobs) == 3 else [f"{len(jobs)} repeats, expected 3"]
    if (vae[0], vae[-1], s3pl[0], s3pl[-1]) != (122, 135, 151, 174):
        problems.append(f"workflow {vae}, S3PL {s3pl}")
    return problems


def figures(work):
    out = work / "figures"
    environment = {"SPATIAL_MSIPL_FIGURE_OUTPUT": str(out), "SPATIAL_MSIPL_ALLOW_UNTRACKED": "1",
                   "SOURCE_DATE_EPOCH": "0"}
    run(["report_figures/seed_averaged_figures.py"], environment)
    run(["report_figures/dataset_overview.py"], environment)
    run(["scripts/plot_s3pl_seed_distributions.py", "--root",
         str(DIAG / "s3pl_seed_investigation_21"), "--out", str(out / "s3pl_released_seed_distributions")],
        environment)
    qualitative = run(["report_figures/qualitative_example.py"], environment).stdout
    if shutil.which("pdflatex"):
        run(["report_figures/runtime_figure.py"], environment)
    expected = json.loads((ROOT / "tools" / "expected_figures.json").read_text(encoding="utf-8"))
    checks = {"fig:qual values (section GBM39_2, ARI 0.35 and 0.21)": qualitative_values(qualitative),
              "fig:runtime values (workflow 122-135 s, S3PL 151-174 s)": runtime_values()}
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
