# Local verification pipeline

How to run the three **official** competition verifiers and the **official Kaggle
metric** on a candidate submission without Kaggle, and what they produced on the
reference submission on this machine (4 cores, 15 GB RAM, Python 3.13.18,
`kickmix` wheel 1.0.0 reporting `0.1`, numpy 2.5.4, scipy 1.18.1, pandas 3.1.0;
measured 2026-11-04).

The official code is vendored **unmodified** under `third_party/`
(provenance and SHA-256 of every file in `third_party/README.md`). Our code only
wraps it (`src/vqcc/verify/`). Competition data lives under `data/` (git-ignored,
see `data/README.md`); the two dfthcsos data files download anonymously from the
public starter-kit dataset, and all three reference circuits can be regenerated
with the vendored Apache-2.0 generators (hash-identical to the bundle, see below).

## Commands

```bash
uv sync --extra dev                        # numpy, scipy, pandas, kickmix, pytest

# Benchmark I (invsqrt). All flags are the official verifier's. 200,540,928 shots, ~13 min on 4 cores.
uv run python -m vqcc.verify.invsqrt path/to/invsqrt.kmb --salt "<32+ chars>"
#   quick smoke test (NOT a verification): --max-x 1000 runs 64,000 shots in seconds

# Benchmark II (dqi). 102,400 shots, ~3.4-9 GB per process: use 2 workers on 15 GB.
uv run python -m vqcc.verify.dqi path/to/dqi.kmb --salt "<32+ chars>" --max-workers 2
#   reduced run: --num-shots 2560 is the smallest multiple of 256 that can pass
#   (Clopper-Pearson at delta = 2^-128 with 0 failures gives eps+ = 0.034 < 1/16)

# Benchmark III (dfthcsos). Needs data/dfthcsos/FeMoCo76o113e.{fcidump,fixed_shifts.npz}.
uv run python -m vqcc.verify.dfthcsos path/to/dfthcsos_dir/ --salt "<32+ chars>"
#   dir holds angle_k_0..K-1.km[xb] + submission.npz; ~2 min; --shots-per-address 1 for a ~25 s check

# The official Kaggle metric on a submission archive (what the leaderboard runs, one split, your salt):
uv run python -m vqcc.verify.metric submissions/submission.zip --salt "<32+ chars>" [--dqi-workers 2]
#   --shot-divisor N (testing only) divides the dqi and dfthcsos shots; invsqrt always runs all shots.
#   Baseline costs for the improvement ratio default to the public empty-salt baselines
#   (override with --baseline dqi=...). The leaderboard salts are secret, so the dqi ratio
#   is approximate in its 7th significant digit.

uv run python scripts/timed_run.py -- python -m vqcc.verify.invsqrt x.kmb   # wall/CPU/peak-RSS report
uv run pytest tests/test_verify.py                                           # harness tests, ~28 s
```

Python API: `vqcc.verify.invsqrt.verify(path, salt=...)`, `vqcc.verify.dqi.verify(path,
instance={...}, max_workers=2, ...)`, `vqcc.verify.dfthcsos.verify(dir, ...)`,
`vqcc.verify.metric.run_metric(zip, salt=...)`; each returns the official JSON dict.

Development salt: the leaderboard salts are secret and at least 32 characters. Use one
fixed public salt (the metric wrapper's default `vqcc-local-development-salt-0123456789abcdef`)
for A/B work and a sweep of several salts before submitting, since one dqi failing shot
costs +0.46 % and whether a marginal circuit fails depends on the salt.

## Results on the reference submission

All runs with the empty salt (the official CLI default), which is how the public baseline
numbers were measured. Timings from `scripts/timed_run.py` (peak RSS = largest single process).

### invsqrt — `uv run python -m vqcc.verify.invsqrt data/sample_submission/invsqrt.kmb`

| quantity | measured | public baseline (docs/research/participants.md §1 item 3) |
| --- | ---: | ---: |
| score (cost) | **2,076,774.233715282** | 2,076,774.2337 (identical) |
| toffoli_equivalent C | 7,987.593206597238 | 7,987.59 |
| toffoli_count (mean) | 7,735.0 | 7,735 |
| t_count / rotation_count | 1.0 / 37.0 | — / 37 |
| rotation_eps | 1.5289e-12 | — |
| num_qubits Q | 260 | 260 |
| reaction_depth / num_ops | 4,005 / 62,160 | — |
| verified_shots | 200,540,928 (= 64 × 3,133,452) | — |
| worst_error_over_tolerance (at x) | 0.4769 (x = 2,588,411) | — |
| circuit_sha256 | `e2bf8eb6…321e1` | `e2bf8eb6…` |
| **wall / CPU / peak RSS** | **796 s (13.3 min) / 3,068 s user / 511 MiB** | — |

4 worker processes (one per core, ~130 MiB each during simulation; the 511 MiB peak is
the parent). Regenerating the circuit with the vendored official generator
(`third_party/verifiers/invsqrt/nr_reference_circuit.py OUT.kmb`, 18 s) gives a
byte-identical file (same sha256).

### dqi — `uv run python -m vqcc.verify.dqi data/sample_submission/dqi.kmb --max-workers 2`

The reference circuit was regenerated with the vendored official generator
(`third_party/verifiers/dqi/dqi_reference_circuit.py data/sample_submission/dqi.kmb`:
28.6 s, 1.7 GiB, 886,118,180 B, 5,725,461 Toffolis, 1,893 qubits) and its sha256
`959471d05a26373b4f14ca0cae2d8639ea25f18170d9f6532139aa51ccc04995` matches the
bundle's `sample_submission/dqi.kmb` hash recorded in docs/research/participants.md.

| run | shots | failures | ε⁺ | R | mean Toffoli | score | wall | peak RSS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| probe, 1 worker | 512 | 0 | 0.1591 | — | — | FAIL (ε⁺ ≥ 1/16: too few shots, as designed) | 42.6 s | 3,415 MiB |
| reduced, 2 workers | 2,560 | 0 | 0.034064 | 4.941658 | 5,725,094.37 | 1.0138e14 (R inflated by the small N) | 126 s | 9,085 MiB |
| **full, 2 workers** | 102,400 | **0** | 8.6606e-4 | **1.1912604648** | **5,725,108.382109375** | **24,439,463,583,672.93** | **566 s (9.4 min)** | 9,091 MiB |

Public baseline (participants.md item 3/§5): Q 1,893, mean T 5,725,108.4 (static
5,725,461), R(k=0) = 1.19126, mean_error_weight 31.0467, cost
24,439,463,583,672.93 at the empty salt. **All match exactly** (score identical to the
last digit, mean Toffoli 5,725,108.38, mean_error_weight 31.046737, 0/102,400 failures,
reaction_depth 170,757, num_ops 86,051,014, num_bits 49,154). The 2,560-shot mean
5,725,094 differs only through per-shot noise (one Forney step is skipped per shot with
probability 1/4096).

Timeline of the full run (memory watchdog, 1-minute samples): file load + 400 batches
on 2 workers took ~8 min at ~0.9 GB RSS per worker (about 2.4 s per 256-shot batch per
worker, i.e. ~1.2 GB simulator state, not the 6 GB quoted in the research notes); the
last ~1.5 min is the parent computing `reaction_depth()`/`operation_statistics()` on the
86 M-op circuit, which is the 9 GB peak. With this profile 4 workers would also fit in
15 GB, but keep 2 to leave headroom for that final step.

Memory: the official default is 4 workers (`DEFAULT_MAX_WORKERS`); the metric wrapper
sets it to `--dqi-workers` (default 2). Budget ~1 GB per worker during simulation plus
~9 GB for the parent's final `reaction_depth()` (the 3.4 GB "largest process" in the
512-shot probe was the single-worker run's parent during loading).

### dfthcsos — `uv run python -m vqcc.verify.dfthcsos data/sample_submission/dfthcsos`

| quantity | measured | SCORING_README baseline |
| --- | ---: | ---: |
| score | **3,355,599,588.3155375** | 3,355,599,588.3155365 (differs by 1 ulp, 3e-16 relative) |
| lambda_eff | 49.30136925057439 | 49.301369 |
| toffoli_count T_total | 93,237.0 | 93,237 |
| num_qubits Q_total | 730 (186 persistent + 544 temporary) | 730 |
| angles / outer / inner / givens Toffoli | 79,480 / 846 / 9,461 / 3,450 | same |
| angles qubits per circuit | 119 (selection 12, words 96, temp 11) | 119 |
| error_1 / error_2 | 3.185 mHa / 18.640 mHa | 3.19 / 18.64 |
| Lambda / E_SOS / E_gap | 308.4559 / −22144.2388 / 3.965477 | 308.456 / — / 3.965477 |
| brot / J / K | 12 / 8 / 10 | same |
| verified_shots | 254,464 (= 3,976 × 64) | 254,464 |
| reaction_depth / num_ops | 110 / 2,060,743 | — |
| submission_sha256 | `276d464f…2695` | — |
| **wall / CPU / peak RSS** | **118 s / 109 s user / 1,093 MiB** | "about 25 s" (faster host) |

Single process. `--shots-per-address 1` (what the pytest uses) gives the same metrics
and score in ~25 s (the metrics depend only on the recovered words). Regenerating the ten
ANGLE circuits from the sample `submission.npz` with the vendored official builder
(`angle_k_reference_circuit.py submission.npz OUT --brot 12 --batch-size 8 --format kmb`,
4.7 s) gives byte-identical files (same sha256 as the bundle's `angle_k_0..9.kmb`).

The starter kit's own `build_circuits.py` route (factorization NPZ → words → Qualtran
QROMs) needs `qualtran`, `cirq`, `jax`, `optax`; it was not used, since the official
`angle_k_reference_circuit.py` rebuilds the identical circuits from `submission.npz`
with kickmix alone.

### Official metric end to end — `uv run python -m vqcc.verify.metric reference_submission.zip`

The zip held `invsqrt.kmb`, `dqi.kmb` and `dfthcsos/{angle_k_0..9.kmb, submission.npz}`
(stored, 909,634,446 B). Default development salt
`vqcc-local-development-salt-0123456789abcdef`, `verification_shot_divisor = 1`,
`--dqi-workers 2`, `--workdir` kept. The metric's own `generate_standard_submission`
read and validated every file, ran the three verifications in random order and wrote
`submission.csv`; then its `score()` produced:

| benchmark | cost under the dev salt | baseline (empty salt) | ratio | seconds |
| --- | ---: | ---: | ---: | ---: |
| invsqrt | 2,076,774.233715282 | 2,076,774.233715282 | 1.0 | 788.7 |
| dqi | 24,439,472,524,060.105 | 24,439,463,583,672.93 | 0.99999963 | 608.5 |
| dfthcsos | 3,355,599,588.3155375 | 3,355,599,588.3155365 | 1.0 (−3e-16) | 123.2 |
| **geometric mean** | | | **0.9999998781** | **1,535 s wall total, 9.2 GB peak** |

The dqi cost moved by +3.7e-7 relative under the salt (mean Toffoli 5,725,110.5 vs
5,725,108.4: which Forney steps get skipped depends on the seeded HMR outcomes), the
same 7th-digit salt dependence the research notes report; invsqrt and dfthcsos costs are
salt-independent for these circuits. An empty `--salt` is refused by the metric
(`< 32 characters`), exactly as on Kaggle.

## Discrepancies and caveats

* dfthcsos score differs from the README's value in the 17th significant digit
  (`…3155375` vs `…3155365`): floating-point summation order in numpy/scipy versions;
  irrelevant for ranking but worth knowing when comparing JSONs across machines.
* dfthcsos takes 118 s here vs the README's ~25 s: the FCIDUMP parse (sha256 + 128 MB
  text, ~10 s) plus a 2 M-op simulation at batch 254,464 on a slow 4-core VM.
* dqi memory: the research notes' "~6 GB per worker" was not observed (workers ~0.9 GB);
  the real peak is the parent's `reaction_depth()` on the 86 M-op circuit (9.1 GB). Never
  run it next to another verifier on this machine.
* `kickmix` wheel reports `__version__ == '0.1'` although PyPI calls it 1.0.0; the
  bundle's `kickmix.so` is also 0.1, and the three regenerated reference circuits are
  byte-identical to the bundle's, so the simulator semantics match.
* The metric reads `pandas`; the verifiers need `scipy` (`linear_sum_assignment`) —
  both added to `pyproject.toml`.
* The vendored `.py` files carry no per-file Apache header; the bundle's `LICENSE.txt`
  (Apache-2.0) is vendored next to them. The metric notebook has no license field in its
  Kaggle metadata.

## Harness tests (`tests/test_verify.py`, 28 s)

* `test_invsqrt_official_verifier_tiny_instance`: a 24-qubit hand-made circuit
  (`x` + 2 unnamed scratch qubits, two Toffolis, one S gate) at `max_x = 1, beta = 1/4`
  passes the official `verify()` with score 24 × 2; the same circuit with a T gate fails
  with the official "phase error" assertion.
* `test_dqi_official_verifier_tiny_instance`: RS(15, 11) over GF(2⁴) built by the official
  generator, 2,560 shots, 0 failures, through both the module API and the file wrapper.
* `test_dfthcsos_official_verifier_reduced_shots` (skipped without `data/`): the reference
  submission at 1 shot per address reproduces Q 730, T 93,237, λ_eff 49.301369 and the score.
