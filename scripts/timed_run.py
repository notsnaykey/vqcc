#!/usr/bin/env python3
"""Run a command, then print wall time, CPU time and peak RSS of its process tree to stderr.

    uv run python scripts/timed_run.py -- python -m vqcc.verify.invsqrt data/sample_submission/invsqrt.kmb

Peak RSS is ``ru_maxrss`` over the children, i.e. the largest single process (the verifiers
fork workers, so multiply by the worker count for a memory budget). GNU time is not
installed on every machine, hence this script.
"""

import resource
import subprocess
import sys
import time


def main() -> None:
    argv = sys.argv[1:]
    if argv and argv[0] == "--":
        argv = argv[1:]
    if not argv:
        sys.exit(__doc__)
    start = time.monotonic()
    code = subprocess.call(argv)
    wall = time.monotonic() - start
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    print(
        f"[timed_run] exit={code} wall={wall:.1f}s user={usage.ru_utime:.1f}s sys={usage.ru_stime:.1f}s "
        f"max_rss_largest_process={usage.ru_maxrss / 1024:.0f} MiB",
        file=sys.stderr,
    )
    sys.exit(code)


if __name__ == "__main__":
    main()
