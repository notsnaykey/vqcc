# third_party — vendored official competition code

Verbatim copies of the open-source parts of the Google Quantum AI
"Verifiable Quantum Circuit Compilation" Kaggle competition
(`google-verifiable-quantum-circuit-compilation`, Kaggle id 161954). Nothing in
this directory is modified; our wrappers live in `src/vqcc/verify/`. Do not
edit these files — re-vendor and update the hashes below instead.

Competition **data** (the FeMoCo FCIDUMP, `fixed_shifts.npz`, the reference
`.kmb` circuits, `submission.npz`, `kickmix.so`, the paper PDF) is deliberately
**not** here: the competition rules forbid redistributing it. It goes under
`data/` (git-ignored); see `data/README.md`.

## Contents

| Path | What | License |
| --- | --- | --- |
| `verifiers/LICENSE.txt` | Apache License 2.0 text shipped with the verifiers (none of the `.py` files carry a per-file header; the bundle's `LICENSE.txt` covers them) | Apache-2.0 |
| `verifiers/invsqrt/` | Benchmark I verifier `verify_submission_invsqrt.py` + reference generator `nr_reference_circuit.py` | Apache-2.0 |
| `verifiers/dqi/` | Benchmark II verifier `verify_submission_dqi.py` + reference generator `dqi_reference_circuit.py` | Apache-2.0 |
| `verifiers/dfthcsos/` | Benchmark III verifier `verify.py`, `scoreinfra/`, `example_submission/angle_k_reference_circuit.py`, `SCORING_README.md` | Apache-2.0 |
| `kaggle_metric/google_quantum_ai_metric.py` | The official Kaggle metric notebook (`metric/google-quantum-ai-metric`, version 10, last run 2026-11-01), source cell extracted to a `.py` | Kaggle notebook by "Kaggle Competition Metrics"; the kernel metadata carries no license field. It is downloadable anonymously from `https://www.kaggle.com/api/v1/kernels/pull/metric/google-quantum-ai-metric` and references the competition data only by path |

The verifiers import only `numpy`, `scipy` (dfthcsos: `scipy.optimize.linear_sum_assignment`)
and `kickmix`; the metric also needs `pandas`. All are in `pyproject.toml`.

## Provenance

The competition data endpoint needs a Kaggle token and accepted rules, so the
verifiers were taken from public GitHub repositories that redistribute the
`verifiers/` folder of the official bundle verbatim, and cross-checked byte for
byte between independent clones (cloned 2026-11-04):

| Repo (commit) | Path | Agreement |
| --- | --- | --- |
| `Inzainos/quantum-circuit-compilation` @ `ca8b3bcfdab79acfde68e3f65b1328438b445eba` | `verifiers/` | **source of the copy here**; all 16 files |
| `harshulchess77-arch/Google-Quantum-AI-Verifiable-Quantum-Circuit-Compilation` @ `f080a41d464abe7c0d2420b22b9106c91f5201ac` | `third_party/google-verifiable-quantum-circuit-compilation/verifiers/` | all 16 files identical (`cmp`) |
| `parth33320/Google-Quantum-AI---Verifiable-Quantum-Circuit-Compilation` @ `c32131cacf05b764e9ef4c31f2f6b0f220bee169` | `verifiers/` | 15 of 16 identical; its `dqi/dqi_reference_circuit.py` (`281a433f…`) is **modified** (adds a `compute_only` flag) and was not used |
| `clduab11/quantum-hackathon` ledger | pinned hashes | invsqrt `ddef520d…`, dqi `f14274bc…`, dfthcsos `verify.py` `0775be7a…` match |

The metric was downloaded directly from Kaggle (anonymous `kernels/pull`,
HTTP 200, 2026-11-04); its sha256 matches the hash pinned by clduab11.

## SHA-256 of every vendored file

```
e7c5bfafa13cb54e138c70a281ca08ecece3e9203b514f6616fa19bf33475c8f  kaggle_metric/google_quantum_ai_metric.py
cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30  verifiers/LICENSE.txt
c2228569f96e58e118419bc32be2be9e33d6abffb8117cb0b91e1fc25b2a0230  verifiers/dfthcsos/SCORING_README.md
81915e324cc0cade67f52a54b7a51991fd96abaea94d1f8a4d423dae20e57348  verifiers/dfthcsos/__init__.py
8daccdca69f2d718b0176cd9281803df84a988ea5ac6c167fbb02e461ac2b371  verifiers/dfthcsos/example_submission/angle_k_reference_circuit.py
be90e0d503d5c20dcac0102af638b9a4ccad0341daa5baa5d49216a259e4516f  verifiers/dfthcsos/scoreinfra/__init__.py
fc027b52fdcebe14404f403a089122485d097ed65d03e6d989623d620b1ab68c  verifiers/dfthcsos/scoreinfra/circuits.py
7f1e190c42fc5325f3e6689fbbef51f95b0cb12f1c828cda92b6c088e72206da  verifiers/dfthcsos/scoreinfra/costs_prepare.py
ae82898d47a7a86b96378fb906e0f8a9f46003065cf19c7c09952a123b5b5af8  verifiers/dfthcsos/scoreinfra/dfthc_math.py
a2d5a63191d655729e29f0fde1e85fe4630bf896a91a63bb894d8d7daf71ed39  verifiers/dfthcsos/scoreinfra/reference.py
0775be7a528922367caebe9e4d051d6199811f1aefeaa4b793eaaa4621b8ec9d  verifiers/dfthcsos/verify.py
01c870aa9763f4e4357fc6654bff1d3296cec995bd0943f87b4a48946ada5b40  verifiers/dqi/__init__.py
2b8e1b80a806157c333a7e308eaf2499ee09de499efbc05875202c327959959e  verifiers/dqi/dqi_reference_circuit.py
f14274bc0943fb9769ddb01131be6063191a15009fe1caf1d4bdd9fd25194e65  verifiers/dqi/verify_submission_dqi.py
e9a6ecf253c343528578be5fa92eb820ccade63333aebb784552fb4ae75dbc0b  verifiers/invsqrt/__init__.py
bb90330dcf774f7b502de471293facba67f27952cc8808fe4a9970a9b1322e23  verifiers/invsqrt/nr_reference_circuit.py
ddef520dec6b68d1cf0a6f328ddd36d79eb84570b9192cf3f7acaf073f06733a  verifiers/invsqrt/verify_submission_invsqrt.py
```

Re-check with `cd third_party && sha256sum -c <(sed -n '/^```$/,/^```$/p' README.md | grep '  ')`.

## How the wrappers use this

* `vqcc.verify._vendor.ensure_verifiers_on_path()` prepends `third_party/verifiers`
  to `sys.path`, so `import invsqrt`, `import dqi`, `import dfthcsos` resolve
  exactly as on Kaggle (where `VERIFIERS_DIR` is appended after local installs).
* `dfthcsos/scoreinfra/reference.py` expects the FCIDUMP and `fixed_shifts.npz`
  beside the package (`PACKAGED_FCIDUMP`). `vqcc.verify._vendor.load_dfthcsos()`
  rebinds `dfthcsos.verify.check_fcidump` / `load_fixed_shifts` to partials that
  pass `data/dfthcsos/...` instead; the official sha256 checks still run.
* The metric's `EVAL_INPUTS_DIR` is reassigned by `vqcc.verify.metric` to a
  scratch directory holding a one-split `solution.csv` + `metadata.json`.

## kickmix

The verifiers run against the `kickmix` wheel in `.venv` (`kickmix>=1.0.0` from
PyPI, reports `__version__ == '0.1'`). The competition bundle's `kickmix.so`
(3,220,392 B, sha256 `c66b3216c4029e0cdfd09054306aa0feadf53ab2f50c1164e37f752874e5005e`,
also version 0.1) is kept under `data/kickmix/` for reference only.
