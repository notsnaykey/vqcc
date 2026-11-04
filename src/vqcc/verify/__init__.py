"""Thin wrappers around the official competition verifiers and the Kaggle metric.

The official code is vendored verbatim under ``third_party/`` (see
``third_party/README.md`` for provenance and hashes) and is never modified: these
modules only put it on ``sys.path``, point the dfthcsos verifier at the data files
under ``data/`` and expose command-line entry points:

    uv run python -m vqcc.verify.invsqrt  path/to/invsqrt.kmb [official flags...]
    uv run python -m vqcc.verify.dqi      path/to/dqi.kmb     [official flags...]
    uv run python -m vqcc.verify.dfthcsos path/to/dfthcsos/   [official flags...]
    uv run python -m vqcc.verify.metric   submission.zip --salt SALT

See docs/verification.md for measured runtimes and the baseline numbers.
"""

from vqcc.verify._vendor import (
    DATA_DIR,
    THIRD_PARTY_DIR,
    VERIFIERS_DIR,
    load_dfthcsos,
    load_dqi,
    load_invsqrt,
)

__all__ = [
    "DATA_DIR",
    "THIRD_PARTY_DIR",
    "VERIFIERS_DIR",
    "load_dfthcsos",
    "load_dqi",
    "load_invsqrt",
]
