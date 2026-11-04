"""Run the official Kaggle metric locally on a submission archive.

    uv run python -m vqcc.verify.metric submission.zip [--salt SALT] [--shot-divisor N]
                                        [--dqi-workers N] [--baseline NAME=COST ...] [--json OUT]

The metric (``third_party/kaggle_metric/google_quantum_ai_metric.py``, vendored verbatim)
reads its solution and hyperparameters from ``/kaggle/input/competition_evaluation`` and
writes ``submission.csv`` to the working directory. This wrapper builds a one-split solution
with your salt in a scratch directory, points the metric's ``EVAL_INPUTS_DIR`` at it, runs
``generate_standard_submission`` on the extracted archive and then ``score``. Nothing in the
vendored file is edited; the metric's own docstring says local installs of kickmix and the
verifiers take precedence over the competition-data paths, which is what happens here.

The leaderboard salts are secret, so ``--salt`` is any string of 32+ characters; the
reference costs under that salt are unknown (dqi's depends on the salt in the 7th digit),
so ``baseline_cost`` defaults to the public empty-salt baselines and the reported score is
approximate to that extent. ``--shot-divisor`` is the metric's testing-only
``verification_shot_divisor`` (weakens dqi and dfthcsos; Kaggle uses 1).
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import sys
import tempfile
import time
import zipfile
from typing import Any

from vqcc.verify._vendor import load_dqi, load_metric

DEFAULT_SALT = "vqcc-local-development-salt-0123456789abcdef"  # 44 chars; metric requires >= 32.

# Reference-submission costs with no salt (invsqrt and dfthcsos are salt-independent in
# practice; dqi varies in the 7th significant digit). Sources: docs/research/participants.md
# item 3 and docs/verification.md (our own runs).
DEFAULT_BASELINES = {
    "invsqrt": 2076774.233715282,
    "dqi": 24439463583672.93,
    "dfthcsos": 3355599588.3155365,
}


def _extract(archive: pathlib.Path, dest: pathlib.Path) -> pathlib.Path:
    if archive.is_dir():
        return archive
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            target = (dest / info.filename).resolve()
            if not target.is_relative_to(dest.resolve()):
                raise ValueError(f"archive member escapes extraction root: {info.filename}")
        zf.extractall(dest)
    return dest


def run_metric(
    submission: str | os.PathLike[str],
    *,
    salt: str = DEFAULT_SALT,
    baselines: dict[str, float] | None = None,
    shot_divisor: int = 1,
    dqi_workers: int | None = 2,
    workdir: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Score ``submission`` (zip or directory) exactly as the Kaggle metric would, under ``salt``."""
    import pandas as pd

    if len(salt) < 32:
        raise ValueError("salt must be at least 32 characters (the metric refuses shorter ones)")
    baselines = {**DEFAULT_BASELINES, **(baselines or {})}
    metric = load_metric()
    if dqi_workers is not None:
        # The metric calls the dqi verifier without max_workers, which then uses
        # min(cpu_count, DEFAULT_MAX_WORKERS) = 4 workers of ~6 GB each on the reference.
        load_dqi().DEFAULT_MAX_WORKERS = int(dqi_workers)

    own_tmp = workdir is None
    work = pathlib.Path(tempfile.mkdtemp(prefix="vqcc-metric-") if own_tmp else workdir)
    work.mkdir(parents=True, exist_ok=True)
    eval_inputs = work / "competition_evaluation"
    eval_inputs.mkdir(exist_ok=True)
    rows = [
        {"row_id": i, "benchmark": name, "seed_salt": salt, "baseline_cost": baselines[name], "Usage": "Private"}
        for i, name in enumerate(("invsqrt", "dqi", "dfthcsos"))
    ]
    solution = pd.DataFrame(rows)
    solution.to_csv(eval_inputs / "solution.csv", index=False)
    (eval_inputs / "metadata.json").write_text(
        json.dumps({"Hyperparameters": {"verification_shot_divisor": int(shot_divisor)}})
    )
    extracted = _extract(pathlib.Path(submission), work / "submission")

    saved_eval, saved_cwd = metric.EVAL_INPUTS_DIR, os.getcwd()
    metric.EVAL_INPUTS_DIR = eval_inputs
    run_dir = work / "run"
    run_dir.mkdir(exist_ok=True)
    os.chdir(run_dir)
    start = time.monotonic()
    try:
        metric.generate_standard_submission(str(extracted))
        produced = pd.read_csv(run_dir / "submission.csv")
        score, details = metric.score(solution, produced, "row_id", verification_shot_divisor=int(shot_divisor))
    finally:
        os.chdir(saved_cwd)
        metric.EVAL_INPUTS_DIR = saved_eval
        if own_tmp:
            shutil.rmtree(work, ignore_errors=True)
    return {
        "score": score,
        "salt": salt,
        "verification_shot_divisor": int(shot_divisor),
        "baseline_costs": baselines,
        "details": details,
        "seconds_total": time.monotonic() - start,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("submission", help="submission.zip (or an already extracted directory)")
    parser.add_argument("--salt", default=DEFAULT_SALT, help="seed salt, >= 32 characters (default: a fixed dev salt)")
    parser.add_argument("--shot-divisor", type=int, default=1, help="metric's verification_shot_divisor (testing only)")
    parser.add_argument("--dqi-workers", type=int, default=2, help="worker processes for the dqi verifier (default 2; Kaggle uses 4)")
    parser.add_argument("--baseline", action="append", default=[], metavar="NAME=COST",
                        help="override a baseline cost, e.g. dqi=2.4439465632206816e13")
    parser.add_argument("--workdir", help="keep the metric's scratch files (solution.csv, submission.csv) here")
    parser.add_argument("--json", help="also write the result JSON to this path")
    args = parser.parse_args(argv)
    baselines = {}
    for item in args.baseline:
        name, _, cost = item.partition("=")
        if name not in DEFAULT_BASELINES or not cost:
            parser.error(f"--baseline expects NAME=COST with NAME in {sorted(DEFAULT_BASELINES)}, got {item!r}")
        baselines[name] = float(cost)
    metric = load_metric()
    try:
        result = run_metric(
            args.submission, salt=args.salt, baselines=baselines, shot_divisor=args.shot_divisor,
            dqi_workers=args.dqi_workers, workdir=args.workdir,
        )
    except metric.ParticipantVisibleError as err:
        print(json.dumps({"status": "FAIL", "error": str(err)}, indent=2))
        sys.exit(1)
    text = json.dumps(result, indent=2)
    if args.json:
        pathlib.Path(args.json).write_text(text)
    print(text)


if __name__ == "__main__":
    main()
