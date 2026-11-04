"""Run the official Benchmark II (DQI) verifier from our venv.

    uv run python -m vqcc.verify.dqi circuit.kmb [--salt STR] [--num-shots N] [--max-workers N] ...

All flags are the official verifier's. Memory: each worker simulates a batch of 256 shots
of the whole circuit (the 845 MiB reference circuit needs ~6 GB per worker); the official
default is 4 workers, so on a 15 GB machine pass ``--max-workers 2``. ``--num-shots`` must
be a multiple of 256; the competition uses 102,400.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from vqcc.verify._vendor import load_dqi, run_official_main


def verify(circuit_path: str | Path, *, instance: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    """Python API: ``verify_submission_dqi.verify`` on a .kmb/.kmx file.

    ``instance`` holds overrides for ``ProblemSpecDQI.benchmark_instance`` (``m``, ``n``,
    ``degree``, ``r``, ``num_shots``); ``kwargs`` go to the official ``verify`` (``salt``,
    ``seed``, ``batch_size``, ``log2_delta``, ``max_workers``).
    """
    import kickmix as km

    mod = load_dqi()
    circuit = km.Circuit.from_file(str(circuit_path), format=Path(circuit_path).suffix.removeprefix("."))
    return mod.verify(circuit, mod.ProblemSpecDQI.benchmark_instance(**(instance or {})), **kwargs)


def main(argv: list[str] | None = None) -> None:
    run_official_main(load_dqi(), sys.argv[1:] if argv is None else argv, "verify_submission_dqi.py")


if __name__ == "__main__":
    main()
