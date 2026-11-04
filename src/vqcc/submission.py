"""Build and sanity-check a submission.zip in the competition layout.

Expected layout (files at the zip root, no wrapper folder):
    invsqrt.kmb | invsqrt.kmx
    dqi.kmb     | dqi.kmx
    dfthcsos/angle_k_0.kmb ... dfthcsos/angle_k_{n-1}.kmb   (contiguous from 0)
    dfthcsos/submission.npz   (U, W, H2_I, H1_I, Hsym_lower, tree_edges)

Always run the official verifiers from data/ on the exact files before uploading.
"""

from __future__ import annotations

import hashlib
import re
import zipfile
from pathlib import Path

import kickmix as km

from vqcc.cost import resources

DFTHCSOS_MAX_QUBITS = 128
_ANGLE_RE = re.compile(r"^angle_k_(\d+)\.(kmb|kmx)$")


def _pick(dir_: Path, stem: str) -> Path:
    for ext in ("kmb", "kmx"):
        p = dir_ / f"{stem}.{ext}"
        if p.exists():
            return p
    raise FileNotFoundError(f"{stem}.kmb or {stem}.kmx not found in {dir_}")


def check_layout(src: Path) -> list[str]:
    """Return a list of problems with a candidate submission directory (empty if fine)."""
    problems: list[str] = []
    for stem in ("invsqrt", "dqi"):
        try:
            _pick(src, stem)
        except FileNotFoundError as e:
            problems.append(str(e))
    d = src / "dfthcsos"
    if not d.is_dir():
        problems.append("missing dfthcsos/ directory")
        return problems
    if not (d / "submission.npz").exists():
        problems.append("missing dfthcsos/submission.npz")
    idx = sorted(int(m.group(1)) for p in d.iterdir() if (m := _ANGLE_RE.match(p.name)))
    if not idx:
        problems.append("no dfthcsos/angle_k_*.kmb files")
    elif idx != list(range(len(idx))):
        problems.append(f"angle_k indices not contiguous from 0: {idx}")
    for p in d.iterdir():
        if _ANGLE_RE.match(p.name):
            c = km.Circuit.from_file(p)
            if c.num_qubits > DFTHCSOS_MAX_QUBITS:
                problems.append(f"{p.name} uses {c.num_qubits} qubits > {DFTHCSOS_MAX_QUBITS}")
    return problems


def summarize(src: Path) -> str:
    lines = []
    for p in sorted(src.rglob("*")):
        if p.suffix in (".kmb", ".kmx"):
            r = resources(km.Circuit.from_file(p))
            lines.append(
                f"{p.relative_to(src)}: Q={r.qubits} Toffoli={r.toffoli} "
                f"T={r.t_like} instr={r.instructions}"
            )
    return "\n".join(lines)


def build_zip(src: Path, out: Path) -> str:
    """Zip `src` into `out` with files at the root. Returns the sha256 of the zip."""
    problems = check_layout(src)
    if problems:
        raise ValueError("submission layout problems:\n  " + "\n  ".join(problems))
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(src.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(src).as_posix())
    return hashlib.sha256(out.read_bytes()).hexdigest()


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", type=Path, help="directory laid out like the submission root")
    ap.add_argument("--out", type=Path, default=Path("submissions/submission.zip"))
    args = ap.parse_args()
    print(summarize(args.src))
    digest = build_zip(args.src, args.out)
    print(f"wrote {args.out} sha256={digest}")
