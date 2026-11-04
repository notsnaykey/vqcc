"""Run the official Benchmark III (DFTHC-SOS) verifier from our venv.

    uv run python -m vqcc.verify.dfthcsos submission_dir/ [--salt STR] [--shots-per-address N] ...

``submission_dir`` holds ``angle_k_0..K-1.km[xb]`` and ``submission.npz``; the other official
input forms (``factorization.npz dir/``, circuit files + ``--tree-edges``) work too. Needs
``data/dfthcsos/FeMoCo76o113e.fcidump`` and ``FeMoCo76o113e.fixed_shifts.npz`` (see
data/README.md); the official SHA-256 checks on them still apply.
"""

from __future__ import annotations

import sys
from typing import Any

from vqcc.verify._vendor import load_dfthcsos, run_official_main


def verify(circuits: Any, factorization: Any = None, tree_edges: Any = None, **kwargs: Any) -> dict[str, Any]:
    """Python API: the official ``dfthcsos.verify.verify`` with our data paths bound."""
    return load_dfthcsos().verify(circuits, factorization, tree_edges, **kwargs)


def main(argv: list[str] | None = None) -> None:
    run_official_main(load_dfthcsos(), sys.argv[1:] if argv is None else argv, "verify.py")


if __name__ == "__main__":
    main()
