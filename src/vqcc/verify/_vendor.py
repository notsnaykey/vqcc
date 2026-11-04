"""Locate the vendored official code and the (git-ignored) competition data.

Nothing here edits the vendored files. The dfthcsos verifier expects
``FeMoCo76o113e.fcidump`` and ``FeMoCo76o113e.fixed_shifts.npz`` next to its package
(``dfthcsos/scoreinfra/reference.py``: ``PACKAGED_FCIDUMP``), but those are competition
data that must not be redistributed, so they live under ``data/dfthcsos/`` and
``load_dfthcsos`` rebinds the two loader names in ``dfthcsos.verify`` to read them from
there. The SHA-256 checks of the official code still run on the files we supply.

Environment overrides:
    VQCC_THIRD_PARTY   directory holding ``verifiers/`` and ``kaggle_metric/``
    VQCC_DATA_DIR      directory holding ``dfthcsos/FeMoCo76o113e.fcidump`` etc.
"""

from __future__ import annotations

import functools
import importlib
import os
import sys
from pathlib import Path
from types import ModuleType

_REPO_ROOT = Path(__file__).resolve().parents[3]
THIRD_PARTY_DIR = Path(os.environ.get("VQCC_THIRD_PARTY", _REPO_ROOT / "third_party"))
VERIFIERS_DIR = THIRD_PARTY_DIR / "verifiers"
KAGGLE_METRIC_DIR = THIRD_PARTY_DIR / "kaggle_metric"
DATA_DIR = Path(os.environ.get("VQCC_DATA_DIR", _REPO_ROOT / "data"))

FCIDUMP_PATH = DATA_DIR / "dfthcsos" / "FeMoCo76o113e.fcidump"
FIXED_SHIFTS_PATH = DATA_DIR / "dfthcsos" / "FeMoCo76o113e.fixed_shifts.npz"

# Starter-kit dataset (anonymous download, no Kaggle token needed) that carries both data files.
STARTER_KIT_URL = (
    "https://www.kaggle.com/api/v1/datasets/download/sohier/"
    "verifiable-circuit-compilation-starter-kit/{name}?datasetVersionNumber=4"
)


def ensure_verifiers_on_path() -> Path:
    """Prepend ``third_party/verifiers`` to ``sys.path`` so ``import invsqrt`` etc. resolve.

    Prepending (rather than appending) is what the Kaggle metric relies on: it appends the
    competition-data paths after the local ones so "local installs take precedence".
    """
    if not VERIFIERS_DIR.is_dir():
        raise FileNotFoundError(f"vendored verifiers not found at {VERIFIERS_DIR}")
    path = str(VERIFIERS_DIR)
    if path not in sys.path:
        sys.path.insert(0, path)
    return VERIFIERS_DIR


def load_invsqrt() -> ModuleType:
    """The official ``invsqrt.verify_submission_invsqrt`` module."""
    ensure_verifiers_on_path()
    return importlib.import_module("invsqrt.verify_submission_invsqrt")


def load_dqi() -> ModuleType:
    """The official ``dqi.verify_submission_dqi`` module."""
    ensure_verifiers_on_path()
    return importlib.import_module("dqi.verify_submission_dqi")


def require_dfthcsos_data() -> tuple[Path, Path]:
    missing = [p for p in (FCIDUMP_PATH, FIXED_SHIFTS_PATH) if not p.is_file()]
    if missing:
        names = ", ".join(p.name for p in missing)
        raise FileNotFoundError(
            f"dfthcsos data missing: {names}. Download into {DATA_DIR / 'dfthcsos'} with\n"
            + "\n".join(
                f"  curl -L -o {DATA_DIR / 'dfthcsos' / p.name} '{STARTER_KIT_URL.format(name=p.name)}'"
                for p in missing
            )
            + "\n(see data/README.md)"
        )
    return FCIDUMP_PATH, FIXED_SHIFTS_PATH


def load_dfthcsos() -> ModuleType:
    """The official ``dfthcsos.verify`` module, reading the FCIDUMP and fixed shifts from ``data/``.

    ``dfthcsos.verify.load_inputs`` calls the names ``check_fcidump()`` and
    ``load_fixed_shifts()`` with no arguments, defaulting to files beside the package. We
    rebind those two names in the ``dfthcsos.verify`` namespace to partials that pass our
    paths. The official functions still enforce the official SHA-256s.
    """
    ensure_verifiers_on_path()
    verify_mod = importlib.import_module("dfthcsos.verify")
    reference = importlib.import_module("dfthcsos.scoreinfra.reference")
    fcidump, fixed_shifts = require_dfthcsos_data()
    verify_mod.check_fcidump = functools.partial(reference.check_fcidump, fcidump)
    verify_mod.load_fixed_shifts = functools.partial(reference.load_fixed_shifts, fixed_shifts)
    return verify_mod


def load_metric() -> ModuleType:
    """The official Kaggle metric module (``third_party/kaggle_metric/google_quantum_ai_metric.py``)."""
    ensure_verifiers_on_path()
    # Load the dfthcsos verifier first so the metric's own ``from dfthcsos import verify``
    # gets the module whose data paths are already rebound (sys.modules caches it).
    load_dfthcsos()
    path = str(KAGGLE_METRIC_DIR)
    if path not in sys.path:
        sys.path.insert(0, path)
    return importlib.import_module("google_quantum_ai_metric")


def run_official_main(module: ModuleType, argv: list[str], prog: str) -> None:
    """Run the vendored module's ``main()`` with ``argv`` as its command line."""
    saved = sys.argv
    sys.argv = [prog, *argv]
    try:
        module.main()
    finally:
        sys.argv = saved
