# vqcc — Verifiable Quantum Circuit Compilation

Working repo for the Kaggle competition
[Google Quantum AI – Verifiable Quantum Circuit Compilation](https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation).

The task: hand in three [kickmix](https://github.com/quantumlib/Qualtran/tree/main/kickmix)
circuits (reversible logic + diagonal phases + X-basis measurement) that pass a
classical fuzz verifier while using fewer qubits and Toffoli/T gates than
Google's reference. Score = geometric mean over the three benchmarks of
`baseline_cost / your_cost`; the reference scores 1.0.

See `docs/competition-notes.md` for everything gathered about the benchmarks,
cost models, verifier behaviour and submission format.

## Layout

```
src/vqcc/        helpers: fuzz harness, cost models, submission zip builder
tasks/<name>/    per-benchmark generators and notes (invsqrt, dqi, dfthcsos)
tests/           pytest smoke tests
scripts/         fetch_data.sh (Kaggle download)
data/            competition bundle (git-ignored)
submissions/     built zips (git-ignored)
docs/            notes
```

## Setup

```bash
uv sync --extra dev
uv run pytest
```

Then download the competition bundle (needs a Kaggle API token and accepted rules):

```bash
uv sync --extra kaggle
./scripts/fetch_data.sh
```

## Workflow

1. Write a generator in `tasks/<name>/` using `km.CircuitBuilder`, save as `.kmb`.
2. Fuzz it locally with `vqcc.fuzz_circuit` against a Python reference function
   (fast; seconds for most circuits).
3. Run the **official verifier** from `data/` on the exact file.
4. Check resources with `vqcc.resources` and the cost helpers in `vqcc.cost`.
5. Assemble with `uv run python -m vqcc.submission <dir>` and upload
   `submissions/submission.zip` (5 uploads/day, ~45 min scoring each).

## Quick example

```python
import kickmix as km
from vqcc import fuzz_circuit, resources

b = km.CircuitBuilder()
a = b.create_quantum_register(8, "a")
t = b.create_quantum_register(8, "t")
b.iadd(a, target=t)
c = b.finish_circuit()

print(resources(c))
print(fuzz_circuit(c, lambda i: ({"t": (i["a"] + i["t"]) % 256}, 0.0),
                   input_registers={"a": None, "t": None}, output_registers=["t"]))
```
