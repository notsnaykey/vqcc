"""Run the official Benchmark I (invsqrt) verifier from our venv.

    uv run python -m vqcc.verify.invsqrt circuit.kmb [--salt STR] [--shots-per-x N] [--max-x N] ...

All flags are the official verifier's (``--help`` lists them). Prints the official JSON
summary; exit status 1 on a failed verification, as the official CLI does.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from vqcc.verify._vendor import load_invsqrt, run_official_main


def verify(circuit_path: str | Path, *, n_p: int = 10, **kwargs: Any) -> dict[str, Any]:
    """Python API: ``verify_submission_invsqrt.verify`` on a .kmb/.kmx file at the benchmark instance.

    ``kwargs`` go to the official ``verify`` (``salt``, ``seed``, ``batch_size``, ``max_workers``).
    """
    import kickmix as km

    mod = load_invsqrt()
    circuit = km.Circuit.from_file(str(circuit_path), format=Path(circuit_path).suffix.removeprefix("."))
    return mod.verify(circuit, mod.ProblemSpecInvSqrt.for_n_p(n_p), **kwargs)


def main(argv: list[str] | None = None) -> None:
    run_official_main(load_invsqrt(), sys.argv[1:] if argv is None else argv, "verify_submission_invsqrt.py")


if __name__ == "__main__":
    main()
