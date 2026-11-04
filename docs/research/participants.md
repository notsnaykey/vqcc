# Participant repositories: what they reveal about the VQCC competition

Digest compiled 2026-11-04 from public GitHub repositories of participants in the Kaggle competition
"Google Quantum AI – Verifiable Quantum Circuit Compilation" (`google-verifiable-quantum-circuit-compilation`),
plus the official files those repos redistribute and two public Kaggle API endpoints that turned out to be
reachable without credentials (the metric notebook and the dfthc-sos starter-kit dataset).

Every fact below is tagged by provenance:

- **[OFFICIAL]** verbatim from an official file (verifier source, SCORING_README, metric notebook, starter kit,
  companion paper arXiv:2610.23832v2) found inside a repo or downloaded from a public Kaggle endpoint.
- **[CLAIM]** a participant's own statement or measurement (local verifier run, leaderboard reading).
- **[INFERENCE]** my own deduction.

Local copies (all cloned shallow, read-only, never executed):
`/tmp/claude-0/-home-user/af1e8b3b-1af8-51dd-9e8d-ec3f80eabc0b/scratchpad/participants/<owner>__<repo>/`
and official downloads under
`/tmp/claude-0/-home-user/af1e8b3b-1af8-51dd-9e8d-ec3f80eabc0b/scratchpad/official_downloads/`
(`google-quantum-ai-metric.py`, `starter_kit/`).

---

## 0. Twenty-line executive summary

1. **Official verifier sources are redistributed verbatim** in three repos (Inzainos, parth33320, harshulchess77-arch);
   their SHA-256s agree with the hashes pinned in clduab11's ledger (`verify_submission_invsqrt.py` `ddef520d…`,
   `verify_submission_dqi.py` `f14274bc…`, `dfthcsos/verify.py` `0775be7a…`). The companion paper PDF (1,092,999 B,
   sha `1aa5e545…`) and `kickmix.so` (3,220,392 B, sha `c66b3216…`, CPython 3.13 x86-64, needs glibc ≥ 2.34) are also in repos.
2. **Official metric notebook** (v10, sha `e7c5bfaf…`) is downloadable anonymously from
   `https://www.kaggle.com/api/v1/kernels/pull/metric/google-quantum-ai-metric` (verified today, HTTP 200). It fixes the
   zip layout, an instruction allow-list, id cap 699,050, register caps, npz array specs, per-split secret salts (≥32 chars),
   `baseline_cost` per split = reference cost under that salt, random task order, and "any failure voids the submission".
3. **Baselines (measured by ≥3 repos with the official verifiers):** invsqrt Q 260, 7,735 Toffoli, 37 rotations, C 7,987.59,
   cost **2,076,774.2337**; dqi Q 1,893, mean T 5,725,108.4 (static 5,725,461), R 1.19126, cost **≈2.4439×10¹³** (salt-dependent
   in the 7th digit); dfthcsos λ_eff 49.301369, T 93,237, Q 730, cost **3,355,599,588.3155**.
4. **invsqrt verifier internals:** exhaustive 64 shots × every x ∈ [1, 3,133,452]; phase compared in uint64 units of 2⁻⁶⁴ turn
   against `isqrt(2^130/x)`; tol(x) = r >> 25; zero failures allowed; rotation ε = π·min_margin/2⁶⁴/n_rot; cost = Q·(Toffoli + T/4),
   T per rotation = 0.56·log₂(1/ε)+5.3; Q = `circuit.num_qubits` (max id + 1).
5. **dqi verifier internals:** 102,400 shots (400 batches of 256); weights from the DQI tridiagonal principal eigenvector (r = 2016,
   mean weight 31.05, P(w=35)≈2.8 %); value error = syndrome not restored OR dirty ancilla, phase error otherwise; ε⁺ = one-sided
   Clopper–Pearson at δ = 2⁻¹²⁸ (k = 0 → 8.6606×10⁻⁴, R = 1.19126; k = 1 → R = 1.19673, +0.459 %); Z_POW forbidden; cost R·Q²·T.
6. **dfthcsos verifier internals:** `selection` must be exactly ⌈log₂(76+R·B)⌉ qubits; `word_j` registers declare brot; 64 shots/address,
   forward then reverse; words must agree across shots; `lambda_eff = sqrt(E_gap(2Λ−E_gap))` with E_upper = −22140.27335 Ha;
   floors Λ > 49.0, E_gap > 3.914898 (strict), error_1, error_2 ≤ 20 mHa; ANGLE circuits ≤ 128 qubits; Q_total shares temp workspace (max).
7. **Best public invsqrt (early Nov):** 62 qubits, 1,325.48 mean Toffoli, 41 rotations, cost 100,568.5 (**20.65×**); lineage
   mrmeows 63q → busyaprime → yoyobar 62q → Özer patch → Ehan Mallick AND merges. Architecture: signed-digit centered quadratic
   per 256 (e,a) segments, QROM coefficients, derivative split, virtual low bit, exact-domain affine rewrites, LP-calibrated angles.
8. **Best public dqi:** 892 qubits, ~403.6k–407k mean Toffoli (**63–64×**): SomeJoint "q18" confluent/Hankel-Schur decoder lineage
   (jday96314 → alexchilton 883q → SomeJoint 897/889 → yoyobar/ahoirg 893 → wahyurahmaniar/manwithacat 892). Rank-42 GF(2¹²) multiplier,
   in-place continued-fraction of S(z), classical mask projection, rare-branch approximations traded against R(ε⁺).
9. **Best public dfthcsos:** marculera's (R,B,C) = (9,143,40) table, 1,363 rows, 8-bit words, J = 5 (15 circuits), λ_eff ≈ 47.04–47.10,
   T ≈ 15.7k–16.2k, Q 428, cost ≈ 3.17–3.27×10⁸ (**10.3–10.6×**); all gates bind (error_2 = 19.999 mHa, E_gap at floor). Loaders are
   ANF/paired-product XOR oracles, 294–318 Toffolis per circuit at 128 qubits.
10. **Public leaderboard:** top 26.14 (10-28) → 26.76 (10-30) → 27.996 (11-02, "Breaking1800"); 6th place 26.80 on 11-02; 2,052 teams.
    Portfolio assemblers of public parts sit at 23.0–24.0.
11. **Pitfalls that cost people submissions:** wrong register names (dqi needs exactly S0..S69 / E0..E4094), `.kmx` text saved as `.kmb`,
    npz with wrong shapes, same file for every angle_k, non-contiguous angle_k numbering, resetting dirty qubits (R dephases → random phase),
    measuring local invsqrt score on a subrange of x, Q counted as max-id+1 (freed high ids still count), ~6 GB RAM per dqi worker,
    `reaction_depth()` OOM on 7 GB hosts, upload must be named `submission.zip`, Kaggle metric rejects hard links.
12. **No repo found that beats the public frontier by original work** except marginal patches (wahyurahmaniar −1 dqi qubit and −245 ANGLE
    Toffolis/pass; manwithacat HW-06 −12 Toffoli-uncomputes). The genuine frontier lives in Kaggle notebooks/datasets (SomeJoint, mrmeows,
    busyaprime, yoyobar, heliosli, marculera, Özer, Gluzdov, kirilltym, alexchilton), not on GitHub.

---

## 1. Repository inventory

| Repo (GitHub) | Last commit | Approach | Own score / status [CLAIM] | Most valuable contents |
|---|---|---|---|---|
| [Inzainos/quantum-circuit-compilation](https://github.com/Inzainos/quantum-circuit-compilation) | 2026-11-03 | hand-designed + AI agents (Spanish docs) | invsqrt 570,323 (3.63×) verified; dqi 7-bit counters (−0.8 %); dfthcsos sample only | **verbatim official `verifiers/`** (all three + reference generators + SCORING_README), honest CHANGELOG of a broken zip |
| [somfieao/kickmix-compiler](https://github.com/somfieao/kickmix-compiler) | 2026-10-24 | Dream-RSI evolutionary agent loop (Claude Code CLI on DeepSeek V4.1 Flash) | invsqrt 562,141 (3.694×); LB 1.54586 (rank ≈260/365 on 10-23) | `scripts/fetch_data.sh` (full official data file list + Kaggle API URLs), evaluator/protocol, agent proposal with simulator findings |
| [clduab11/quantum-hackathon](https://github.com/clduab11/quantum-hackathon) ("Praxen") | 2026-11-03 | multi-agent engineering org (ledger, gates G0–G5, provenance audits); ports of public notebooks | LB 19.20572 (rank 1,404/2,052 on 11-02): invsqrt 13.24× (Q84), dqi 54.73× (Q889), chem 9.78× (Q430) | field guide, per-task anatomy, exhaustive provenance maps of public notebooks, decision/negative-result register, baseline JSONs |
| [acco-cyber/Quantum-Circuit](https://github.com/acco-cyber/Quantum-Circuit) | 2026-11-02 | portfolio assembler of public Kaggle outputs, hourly scheduled agent | LB 23.17173 (v16, 10-30) | STATUS/RUNLOG with per-version member costs, local verifier JSONs, rotation-angle LP study, chemistry XOR audit, Gluzdov notebook copy |
| [nasir26/vqcc-kaggle](https://github.com/nasir26/vqcc-kaggle) | 2026-10-29 | metric-identical harness + anatomy studies + public-member portfolio | LB 22.78536 (v2) | **best written anatomy docs** (invsqrt/dqi/dfthcsos cost breakdowns), RULES digest, flip-graph GF(2¹²) multiplier search |
| [wahyurahmaniar/Verifiable-Quantum-Circuit-Compilation](https://github.com/wahyurahmaniar/Verifiable-Quantum-Circuit-Compilation) | 2026-11-02 | own ANGLE loader planner + dqi 893→892 patch on public parts | LB 23.97677 (893q) / 23.93 (892q, 2 failing shots on Kaggle) | paired-product loader algebra, dqi pole-flag structure, CREDITS lineage map, results JSONs |
| [manwithacat/kickmix-engine](https://github.com/manwithacat/kickmix-engine) | 2026-11-03 | Rust re-implementation of kickmix semantics + official-logic `verify`/`diff` | tooling; author's HW-06 portfolio local GM 23.838 | performance numbers, `qrom-plan` crate for chemistry loaders, DQI failing-shot fixtures |
| [manwithacat/kickmix-macos](https://github.com/manwithacat/kickmix-macos) | 2026-10-31 | patched kickmix fork (NEON, memory) + browser circuit viewer | tooling | stage-level description of the 62/63-qubit invsqrt frontier circuits |
| [zjukop3/google-quantum-circuit-compilation-2026-support](https://github.com/zjukop3/google-quantum-circuit-compilation-2026-support) | 2026-10-25 | hand-designed incremental edits of the reference (Chinese notes E1–E8) | LB 1.11751 (rank 710) | exact scoring-model confirmation; invsqrt Q231/T6852 via binary `s`; dqi "register freeze" |
| [harshulchess77-arch/…](https://github.com/harshulchess77-arch/Google-Quantum-AI-Verifiable-Quantum-Circuit-Compilation) | 2026-10-28 | agent harness scaffold | baseline only | verbatim `third_party/` official bundle incl. `kickmix.so`, paper PDF, ground-truth notes |
| [parth33320/…](https://github.com/parth33320/Google-Quantum-AI---Verifiable-Quantum-Circuit-Compilation) | 2026-10-26 | agent SDLC scaffold | none | verbatim `verifiers/` (dqi ref has a `compute_only` edit), `kickmix.so`, LFS placeholders for `.kmb` and FCIDUMP, dqi analysis doc |
| [ccjjllt/quantum](https://github.com/ccjjllt/quantum) | 2026-11-01 | audits of public portfolios (Chinese) | LB 23.00037 (10-30), HW-06 submitted 11-01 | fixed-weight dqi diagnostic (low-weight errors), chemistry cost ladder |
| [Arnabs-ops/Quantum-Circuit-](https://github.com/Arnabs-ops/Quantum-Circuit-) | 2026-10-26 | Kaggle notebook portfolio + chemistry shape search | 10.88057 | `dfthcsos_estimator.py`, notes on (R,B,C) shape transitions |
| [blucca/quantum-circuit-research](https://github.com/blucca/quantum-circuit-research) | 2026-10-29 | hand/AI-designed direct polynomial invsqrt | 3.04× (150q, 4,226 T) not officially verified | arithmetic-only studies, Walsh-phase negative result |
| [andigu/uncompute](https://github.com/andigu/uncompute) (Gu et al., not a participant) | 2026-10-15 | LLM-discovered circuits, arXiv:2610.22367 | dqi: 442,397 T, 1,837 peak qubits (12× TQ) | BM+Forney decoder design, test distribution, differs from competition (field poly 4331 vs 4179, fixed mask) |
| [tatra-labs/kickmix-arena](https://github.com/tatra-labs/kickmix-arena) | 2026-10-26 | open evaluator for Gu et al. tasks | n/a | arithmetic baselines (Gidney adder T=31 Q=95 for add32) |
| [Adithyaphani/Verifiable-Quantum-Circuit](https://github.com/Adithyaphani/Verifiable-Quantum-Circuit), [timothywheelspro/verifiable-circuit-compilation-](https://github.com/timothywheelspro/verifiable-circuit-compilation-), [rampluto/vqca](https://github.com/rampluto/vqca), [dailycodepython/*](https://github.com/dailycodepython/Leveraging-verifiable-structure-in-quantum-circuits-to-find-efficient-compilations-with-agentic-AI) | Oct 24–30 | environment/plan scaffolds, explainer figures | none | nothing beyond README plans |

Not reachable: `jday96314/QuantumAI` (origin of the Schur dqi decoder; clone returned auth prompt → private/removed; referenced by
clduab11 as "no licence") and `gbhanuteja23/Verifiable-Quantum-Circuit` (PR #8 claimed "22.79549 LB, rank 137"; also unreachable).

---

## 2. The official data bundle [OFFICIAL unless noted]

### 2.1 File list and download URLs

From [somfieao `scripts/fetch_data.sh`](https://github.com/somfieao/kickmix-compiler/blob/main/scripts/fetch_data.sh) (needs a `KGAT_` token;
base `https://www.kaggle.com/api/v1/competitions/data/download/google-verifiable-quantum-circuit-compilation/<path with %2F>`):

```
kickmix/kickmix.so, kickmix/LICENSE.txt
verifiers/LICENSE.txt
verifiable_circuit_compilation.pdf
verifiers/invsqrt/{__init__.py, verify_submission_invsqrt.py, nr_reference_circuit.py}
verifiers/dqi/{__init__.py, dqi_reference_circuit.py, verify_submission_dqi.py}
verifiers/dfthcsos/{__init__.py, SCORING_README.md, verify.py, example_submission/angle_k_reference_circuit.py,
                    scoreinfra/{__init__,circuits,costs_prepare,dfthc_math,reference}.py,
                    FeMoCo76o113e.fcidump, FeMoCo76o113e.fixed_shifts.npz}
sample_submission/invsqrt.kmb, sample_submission/dqi.kmb
sample_submission/dfthcsos/submission.npz, sample_submission/dfthcsos/angle_k_0..9.kmb
```

Sizes/hashes seen: `kickmix.so` 3,220,392 B sha `c66b3216c4029e0cdfd09054306aa0feadf53ab2f50c1164e37f752874e5005e`, ELF BuildID
`c801b8df…`, version `0.1` [CLAIM clduab11]; FCIDUMP 128,128,348 B sha `e5a48af7…`; `fixed_shifts.npz` 61,028 B sha `7b7facf6…`;
`sample_submission/invsqrt.kmb` sha `e2bf8eb6…` (~0.58 MB); `sample_submission/dqi.kmb` sha `959471d0…` (~845 MiB, 86 M ops, 49,154
classical bits); `submission.npz` 4,537,436 B sha `14d5cc25…`; angle_k ≈1.7–2.0 MB each [CLAIM nasir26/clduab11]. Whole download ≈128 MB
compressed / 1.04 GB unpacked [CLAIM clduab11]. The competition data endpoint returns 401 without a token (checked today); the
**starter kit dataset and the metric notebook are anonymous-downloadable** (see §2.3, §3).

Paper pin: starter `pyproject.toml` pins `qualtran @ git+…@c58703d00b01c346d3e77d3913cf2d6e9e556be3`; somfieao built kickmix from Qualtran
tree `638777fac4379bc62e2a1e4a52cf1a1753895d48`; the metric says kickmix will move to PyPI (ccjjllt/manwithacat already use `kickmix 1.0.0`).

### 2.2 Verbatim copies in repos (identical to the bundle)

- Inzainos: [`verifiers/`](https://github.com/Inzainos/quantum-circuit-compilation/tree/main/verifiers) (no FCIDUMP/fixed_shifts).
- harshulchess77-arch: [`third_party/google-verifiable-quantum-circuit-compilation/`](https://github.com/harshulchess77-arch/Google-Quantum-AI-Verifiable-Quantum-Circuit-Compilation/tree/main/third_party/google-verifiable-quantum-circuit-compilation)
  includes `kickmix.so`, the paper PDF, `fixed_shifts.npz`, sample `.kmb`s.
- parth33320: [`verifiers/`](https://github.com/parth33320/Google-Quantum-AI---Verifiable-Quantum-Circuit-Compilation/tree/main/verifiers) + `kickmix/kickmix.so`;
  **its `dqi_reference_circuit.py` is modified** (adds a `compute_only` flag that skips the reverse EEA) — do not treat it as official.
  Its `.kmb` and `.fcidump` are Git-LFS pointers (134 bytes).
- somfieao: [`docs/benchmark-paper.pdf`](https://github.com/somfieao/kickmix-compiler/blob/main/docs/benchmark-paper.pdf) (same sha as the bundle PDF).

### 2.3 dfthc-sos starter kit (public dataset `sohier/verifiable-circuit-compilation-starter-kit`, version 4)

Downloaded today without credentials via `https://www.kaggle.com/api/v1/datasets/download/sohier/verifiable-circuit-compilation-starter-kit/<path>?datasetVersionNumber=4`
into `official_downloads/starter_kit/`. Contents: `starter_kit/verifier/{verify,score,reference,dfthc_math,costs,circuits}.py` (the
multi-system "Qaggle" verifier the competition one was reduced from), `starter_kit/starter/task1_factorization/{train_df_thc_qaggle.py,
solution_io.py, check_factorization.py, FeMoco76_65_60_60.npz (2,150,130 B)}`, `task2_angles/{trees.py, encode.py}`,
`task3_circuits/{build_circuits.py, angle_k_kickmix.py}`, `starter_kit/dfthc/*.py` (JAX/Optax trainer `df_thc_sga.py`,
`spin_free_block_encoding_costs.py`, `build_angle_k.py`, `verify_angle_k.py`, `dfthc_u_to_tei.py`, `load_integrals.py`),
`FeMoCo76o113e.fixed_shifts.npz`, `FeMoCo76o113e.fcidump` (128 MB, not fetched), and `starter_kit/baselines/` with research NPZs
(Fe2S2-20o30e_15_20_20, Fe4S4-36o54e_32_22_22, FeMoCo54o54e_40_40_40, FeMoCo76o113e_65_60_60, XVIII100o100e_70_70_70, …).

Key starter facts: trees are `path` ((0,1),(1,2),…) or `log_depth` (arXiv:2605.30455 binary tree, BFS order); words `m` mean
`theta/pi = m/2^(brot-1)` in [0,2); rounding is `nearest` or `floor`; the encoder recomputes one-body rows as eigenvectors of `h1'` built
from the *rounded* two-body vectors (rounding-aware); the trainer uses ReLU penalties with `FEMOCO_TRAINING = {rho: 1e-4, epsilon_dfthc: 0.010}`
and freezes `(S, beta_1)`; `pyproject` requires Python ≥ 3.13, numpy, h5py, jax, optax; author Guang Hao Low.

---

## 3. Official metric notebook (`metric/google-quantum-ai-metric`, v10, last run 2026-11-01) [OFFICIAL]

Source extracted to `official_downloads/google-quantum-ai-metric.py` (278 lines, sha `e7c5bfafa13cb54e138c70a281ca08ecece3e9203b514f6616fa19bf33475c8f`,
the same hash clduab11 pins). Exact rules:

- Archive must contain exactly one `invsqrt.km[xb]`, one `dqi.km[xb]`, one directory `dfthcsos` (found by `rglob`, so nesting is tolerated but
  duplicates are fatal; `__MACOSX` ignored) holding `angle_k_0..angle_k_<n-1>` each once (a stem present as both `.kmb` and `.kmx` fails) and
  exactly one `submission.npz`.
- Files must be regular files, `st_nlink == 1` (no hard links), inside the extraction root.
- `ALLOWED_INSTRUCTIONS = {X, CX, CCX, Z, CZ, CCZ, Z_POW, NEG, SWAP, CSWAP, R, HMR, BIT_INVERT, BIT_STORE0, BIT_STORE1, PUSH_CONDITION,
  POP_CONDITION, INFO_TAG, DEBUG_PRINT}`; any other op → rejected. `DEBUG_PRINT` ids still count toward Q.
- `MAX_QUBIT_OR_BIT_ID = 2**30 // 1536 = 699,050` (ids must be below); max registers: invsqrt 1, dqi n+m = 4,165, each ANGLE_k ≤ 128;
  every register must be named.
- `submission.npz`: format-1.0 `.npy` members only, plain little-endian number dtypes, shapes `U (R,B,76) f`, `W (R,B,C) f`, `H2_I (R,C) f`,
  `H1_I () f`, `Hsym_lower (2926,) f`, `tree_edges (75,2) int/uint`; decoded array bytes ≤ 2²⁶ (64 MiB).
- Each leaderboard split row has `seed_salt` (≥ 32 chars, secret) and `baseline_cost` (the reference's cost under that salt). All split
  verifications run in random order before `score()`; "neither a failure's timing nor its message shows which split it failed on";
  any verifier exception → `ParticipantVisibleError` → whole submission fails. Score = geometric mean of `baseline_cost/cost`.
- Verifier calls: `verify_submission_invsqrt.verify(circuit, ProblemSpecInvSqrt.for_n_p(10), salt=salt)`,
  `verify_submission_dqi.verify(circuit, benchmark_instance(num_shots=102400), salt=salt)`,
  `dfthcsos.verify(angle_circuits, npz, tree_edges, salt=salt, shots_per_address=64)`. A `verification_shot_divisor` hyperparameter exists
  "for testing only, must stay 1 on Kaggle".
- Kaggle image `gcr.io/kaggle-images/python@sha256:81b1e7c4…`; data mounted at `/kaggle/input/competitions/google-verifiable-quantum-circuit-compilation/`.
- Memory note in the source: "Verifier memory grew by ~1.5 KB per bit (dqi) and ~1.1 KB per qubit (invsqrt) with the verifiers at c636a96…;
  at 03027f8, dqi's grows by only ~0.2 KB per qubit or bit". The baselines use ids below 50,000.

Scoring time ≈ 45 min per submission; 5 submissions/day; 2 final submissions [CLAIM, Kaggle pages quoted by nasir26 and Inzainos].

---

## 4. invsqrt verifier and reference — exact logic [OFFICIAL]

Source: [Inzainos `verifiers/invsqrt/verify_submission_invsqrt.py`](https://github.com/Inzainos/quantum-circuit-compilation/blob/main/verifiers/invsqrt/verify_submission_invsqrt.py) (402 lines).

- Instance: `n_p = 10`, `width = 2n_p+2 = 22`, `max_x = 3(2^n_p − 2)^2 = 3,133,452`, `beta = 1`, `precision_bits = 24`, `shots_per_x = 64`
  → `num_shots = 200,540,928`; `ETA = 218` only feeds an unused `system_qubits = 3·eta·n_p` field.
- Registers: `register_data` must be exactly `['x']`, 22 distinct `km.q` qubits; every other qubit index `< circuit.num_qubits` is scratch.
- Reference values: `r = isqrt((p²<<130) // (q²·x))`, `target = (r+1)>>1 & MASK64` (nearest multiple of 2⁻⁶⁴ turn),
  `tol = min(r >> (precision_bits+1), 2^63)`; rejects if `tol(max_x) < 2^16` units.
- Shots: shot `i` has `x = i mod max_x + 1`; batches of 256 shots, chunks of 64 batches (16,384 shots); chunk seeds from
  `np.random.SeedSequence(base_seed, pool_size=8)`; `base_seed = int(sha256(kmb bytes),16)` or `int(sha256(f"{hash}{salt}"),16)` with salt;
  `--seed` overrides. Parallel via `fork` ProcessPool, all CPUs by default (`--max-workers`).
- Per batch: `write_across_shots(x_reg, bits)`, `sim.do(circuit)`, assert `x` restored (else "x was not restored."), assert no scratch bit set
  (names the first dirty qubit), `theta = half_turns_to_units(read_shot_phase(i))` per shot, `error = (theta − target).view(int64)`,
  fail if `|error| > tol` ("x=…: phase error … exceeds tolerance …"). Tracks `min_margin = min(tol − |error|)` and the worst ratio/x.
- Cost after all chunks: `toffoli_count = Σ num_toffoli_like / num_shots` (mean executed CCX/CCZ/CSWAP; **conditioned gates count only on
  shots whose bit is set**), `t_base = mean num_t_like`, `n_rot = mean num_z_pow(min_clifford_hierarchy_level=4)`,
  `eps = π·min_margin/2^64/n_rot` (fail if not > 0), `t_count = t_base + n_rot·(0.56·log2(1/eps)+5.3)`,
  `toffolis = toffoli_count + t_count/4`, **`score = circuit.num_qubits · toffolis`**.
- Z_POW classes: `half_turns % 1/2 == 0` → Clifford (free), `% 1/4 == 0` → T (1 T), else rotation.
- Output JSON keys: status, score, toffoli_equivalent, toffoli_count, max_toffoli_count (static), t_count, rotation_count, rotation_eps,
  num_qubits, reaction_depth, num_ops, verified_shots, worst_error_over_tolerance, worst_x, circuit_sha256.
- CLI: `python invsqrt/verify_submission_invsqrt.py submission.kmb [--format auto|kmb|kmx] [--n-p 10] [--beta 1] [--precision-bits 24]
  [--shots-per-x 64] [--eta 218] [--width] [--max-x] [--salt STR] [--seed N] [--batch-size 256] [--max-workers N]`. Prints
  `{"status":"FAIL","error":…}` and exits 1 on failure.
- Runtime [CLAIM]: reference ≈ 726 s on a Kaggle 4-vCPU notebook (nasir26), 400–620 s for 63-qubit circuits with 4 workers (acco-cyber),
  71 s on a 256-core host (clduab11), 20–30 min on a loaded 56-core box (somfieao).

Reference circuit ([`nr_reference_circuit.py`](https://github.com/Inzainos/quantum-circuit-compilation/blob/main/verifiers/invsqrt/nr_reference_circuit.py)):
normalize by counting leading zero *pairs* into 10 unary flags with CSWAP lane rotations (120 Toffoli forward, 110 back), select one of
4 cubic pieces by 3 AND bits (`[1,1.5)`, `[1.5,2)`, `[2,3)`, `[3,4)` with coefficients A/B of arXiv:2308.12352 scaled by `2^j·√2`),
Clifford coefficient load, Horner with column-truncated multipliers (`Precision(delta_bits=14, coef_bits=17, square_bits=28,
product_bits=28, result_bits=29)`), one Newton step `p = T(y0(3 − T(M·T(y0²))))`, unary-controlled denormalize `y1 = p·2^s`
(F = 29+10+1 = 40 fractional bits), `phase_by_bits` = 40 Z_POW (2 Clifford, 1 T, 37 rotations), then exact mirror uncompute.
Model worst relative error 2.84×10⁻⁸ = 2⁻²⁵·⁰⁷ at x = 2,588,411 (0.477 of tolerance). Measured: Q 260 (231 named + 29 adder ancillas),
7,735 Toffoli (3,874 compute + 3,861 uncompute), reaction depth 4,005, 62,160 ops, `rotation_eps` 1.5289×10⁻¹² → 27.3 T/rotation,
C = 7,987.593, cost 2,076,774.233715282 [OFFICIAL numbers measured by clduab11, nasir26, somfieao, Inzainos].

Toffoli anatomy of the reference [CLAIM nasir26 `docs/invsqrt_anatomy.md`]: horner 2,142 (27.7 %), multiply_m 2,086 (27 %), multiply_y0 1,734
(22.4 %), square 884 (11.4 %), denormalize 600 (7.8 %), normalize 230, correct 56, select 3; multiplications = 88.5 % of Toffolis; rotations
= 3.2 % of C; 231/260 qubits are registers live for the whole circuit (c0..c3 68 qubits dead after Horner).

Paper §III.A [OFFICIAL]: internal Google run hash for Benchmark I `4b98f38a52a01fc125da7fc2847f9698abe192519dccf894fd758eccc8f37cea` (circuit withheld).

---

## 5. dqi verifier and reference — exact logic [OFFICIAL]

Source: [Inzainos `verifiers/dqi/verify_submission_dqi.py`](https://github.com/Inzainos/quantum-circuit-compilation/blob/main/verifiers/dqi/verify_submission_dqi.py) (501 lines).

- Instance: `m=4095, n=70, degree=12, r=2016` (= `(2^12 − isqrt(2^12))//2`), `l = n//2 = 35`, `num_shots = 400·256 = 102,400`,
  `batch_size 256`, `log2_delta = −128`, `DEFAULT_MAX_WORKERS = 4` ("matching 4-core / 30 GB Kaggle notebooks; each worker needs ~6 GB of RAM
  for the reference decoder").
- Field: `km.GF2Field(12)` — modulus **4179** (= x¹²+x⁶+x⁴+x+1), primitive element 2 [paper + clduab11 reading the binary]. (Gu et al.'s
  repo uses 4331; constants are not transferable.)
- Registers: exactly `S0..S69` (12 `km.q` each, pairwise disjoint) and `E0..E4094` (12 `km.b` classical bits each); any other qubit is ancilla.
  `'Z_POW' in circuit.operation_statistics()` → `ValueError('Z_POW gates are not allowed in Benchmark II.')`.
- Shot sampling (`sample_shots`): weight `k ~ w_k²` where `w` is the principal eigenvector of the (l+1)×(l+1) tridiagonal
  `A[k,k] = k(q−2r)/sqrt(r(q−r))`, `A[k−1,k] = sqrt(k(m−k+1))` (arXiv:2408.08292 Lemma 9.2); `k` distinct positions uniform in `0..m−1`;
  values uniform in `1..4095`; `M_j` uniform in `0..4095` for all 4095 positions; syndrome `S_i = XOR_j antilog[(log v_j + (i+1)·pos_j) mod 4095]`,
  `i = 0..69`; expected phase `= parity of Σ popcount(v_j & M_j)`. Verifier reports `mean_error_weight = 31.0467`; P(w=35) ≈ 2.8 % [paper].
- RNG: per batch `(rng_seed, sim_seed)` from `SeedSequence(base_seed).generate_state(8·batches)`; `base_seed = int(sha256(kmb),16)` merged with
  salt as for invsqrt; `np.random.default_rng(rng_seed)` draws inputs; `km.Simulator(seed=sim_seed, counting_operations=True)`.
- Per batch: `use_same_registers_as(circuit)`, write S and E, `do`, then `phase_flipped = read_phase_flipped_across_shots()`,
  `val_err = (S changed) | (any ancilla ≠ 0)`, `phase_err = (phase_flipped ^ expected) & ~val_err`.
- `eps_hat = k/N`; `eps_plus = clopper_pearson_upper_bound(k, N, −128)`: for k = 0 `−expm1(ln δ/N)`; else bisection (64 iters) on the log
  binomial tail. Reject if `eps_plus ≥ 1/16`. `R(eps) = ln2 / −ln(1/2 + 2·sqrt(eps))` (R(0) = 1).
  **`score = R · num_qubits² · mean_toffoli`**.
- Numbers: k=0 → ε⁺ = 8.660587301657926×10⁻⁴, R = 1.1912604648115832; k=1 → 9.1042×10⁻⁴, R = 1.1967314991687559 (+0.459 %);
  k=2 → 1.223 ×; k=3 → R 1.2056; k=4 → 1.2095; k=7 → 1.2199; k=8 → 1.2230 [OFFICIAL formula, values from clduab11/acco-cyber runs].
- Output JSON adds `shot_operation_counts` (every instruction summed over all shots — useful to see e.g. 5×10¹² CX in a 897-qubit decoder),
  `num_bits`, `max_toffoli_count` (static), `reaction_depth`.
- CLI: `python dqi/verify_submission_dqi.py submission.kmb [--m 4095] [--n 70] [--degree 12] [--r 2016] [--num-shots 102400]
  [--batch-size 256] [--log2-delta -128] [--salt STR] [--seed N] [--max-workers 4]`.
- Runtime [CLAIM]: reference 184 s on Kaggle 4 vCPU (nasir26), 150 s on one core per the paper; 889–897-qubit decoders 84–124 s with 4 workers
  (acco-cyber); build of the reference circuit 28 s / 1.76 GB RSS (nasir26); `reaction_depth()` of a 55 M-op circuit peaks ~7.8 GiB upstream
  (manwithacat), `std::bad_alloc` on a 7 GB machine (Inzainos).

Reference decoder ([`dqi_reference_circuit.py`](https://github.com/Inzainos/quantum-circuit-compilation/blob/main/verifiers/dqi/dqi_reference_circuit.py),
class `ProosAndZalkaDecoder`): `m_eea = n+3 = 73` slots; `reg_a` = 3 fresh 12-qubit slots + the 70 syndrome registers, `reg_b` = 73 fresh slots
(876 qubits); degree pointers `n_A, n_B, n_a, n_b, n_q` each `logm = (73).bit_length()+1 = 8` qubits; `flag`, 2-bit `counter`, 8-bit
`halting_counter`; `n_iters = 3(n+1)+9 = 222` synchronized EEA iterations each executing all sub-steps (update_flag, multiply_and_add_or_sub,
shift_b_array_right, update_metadata, swap_a_and_b) under one-hot controls; Chien search + Forney over 4,095 positions with Itoh–Tsujii
inversion (315 Toffoli, 48 scaffold qubits [paper]), phase via `gf2_phase_by_product` (Clifford), each position conditioned on `E_j ≠ 0`;
reverse EEA. Static 5,725,461 Toffoli-like, Q 1,893 (840 S + 876 reg_b + 36 pad + 40 pointers + 11 control + 90 peak temp), mean executed
≈5,725,108 (one Forney step skipped per shot on average because P(E_j=0)=1/4096) [OFFICIAL build, anatomy by nasir26]. Unit costs
[CLAIM nasir26]: `ixor_gf2_mul` 63 Toffoli (Karatsuba), controlled 75, div scaffold 378, inverse scaffold 315, CSWAP 12-bit 12.

Baseline cost: 24,439,463,583,672.93 at empty salt (nasir26, harshulchess77), 24,439,465,632,206.816 at clduab11's fixed salt,
24,439,473,914,136.668 in wahyurahmaniar's run — i.e. the mean executed Toffoli varies in the 7th significant digit with the salt
[INFERENCE: because the number of skipped Forney steps depends on sampled M_j]. Paper hash for Google's internal Benchmark II run:
`0701f553a9ac4e8af100f66acfccf2fc82cf5a44c2e5aa765b1d4ace01cbaadb`.

---

## 6. dfthcsos verifier — exact logic [OFFICIAL]

Sources: [`verifiers/dfthcsos/SCORING_README.md`](https://github.com/Inzainos/quantum-circuit-compilation/blob/main/verifiers/dfthcsos/SCORING_README.md),
[`verify.py`](https://github.com/Inzainos/quantum-circuit-compilation/blob/main/verifiers/dfthcsos/verify.py),
[`scoreinfra/circuits.py`](https://github.com/Inzainos/quantum-circuit-compilation/blob/main/verifiers/dfthcsos/scoreinfra/circuits.py),
[`scoreinfra/dfthc_math.py`](https://github.com/Inzainos/quantum-circuit-compilation/blob/main/verifiers/dfthcsos/scoreinfra/dfthc_math.py),
[`scoreinfra/costs_prepare.py`](https://github.com/Inzainos/quantum-circuit-compilation/blob/main/verifiers/dfthcsos/scoreinfra/costs_prepare.py),
[`scoreinfra/reference.py`](https://github.com/Inzainos/quantum-circuit-compilation/blob/main/verifiers/dfthcsos/scoreinfra/reference.py).

System constants: FeMoCo76o113e, N = 76, η = 113, `E_upper = −22140.27335` Ha, baseline shape (R,B,C) = (65,60,60), `KEEP_BITS χ = 10`,
`QUBIT_CAP = 128`, `ERROR_1_THRESHOLD = ERROR_2_THRESHOLD = 0.020` Ha, `LAMBDA_FLOOR = 49.0`, `E_GAP_FLOOR = 3.914898` ("difference between the
supplied active-space DMRG and SOS-SDP energies"), `SHOTS_PER_ADDRESS = 64`. FCIDUMP sha `e5a48af7…` is checked every call (~10 s parse;
two-electron integrals stored as **float32**, `S` rounded to float32 — "the score depends on this rounding").

Submission: directory with `angle_k_0..K−1` (`.kmx` or `.kmb`, contiguous, not both formats) and `submission.npz` (`U,W,H2_I,H1_I,Hsym_lower,
tree_edges`; pickles refused; `H1_I`/`Hsym_lower` **ignored** — the shift `(S, β₁)` is always the baseline's from `fixed_shifts.npz`).
`w = W`, `W_offsets = H2_I − Σ_b w`, `S = symmetric_from_lower(Hsym_lower)` (float32), `β₁ = H1_I − tr(S)/2`.

Register contract: `selection` exactly `(num_vectors−1).bit_length()` qubits where `num_vectors = 76 + R·B` ("Extra selection bits are rejected
so workspace cannot be hidden in this register"); `word_0..word_{J−1}` all the same width = brot; all public registers are `km.q`, disjoint,
identical across every circuit; other word_* names rejected; any line starting with `Z_POW` in `str(circuit)` rejected (rotations are not
counted as Toffolis and "the phase check only tells a half turn from no turn").

Simulation (`recover_words_from_circuits`): one simulator with `batch_size = num_vectors·64`, shots `a + r·num_vectors` hold address `a`, words
start at 0; after each circuit `k`: phase must be unflipped on every shot, selection unchanged, workspace zero, and the J words must be
identical across the 64 shots of an address ("a word that depends on a measurement outcome is random rather than a function of the address");
then `clear_for_shot` and rewrite selection + batch `k` words; after K circuits, padding words beyond 75 must be zero; then circuits are applied
in reverse order, each must restore batch `k−1` (or clear to zero for k = 0). Toffoli = `num_toffoli_like/(num_vectors·64)` over **both passes**.
Seed = `initial_seed(submission_sha256, salt)`; `submission_sha256` = sha256 of canonical `.kmb` bytes of all circuits in order then the
`.npy` entries `U,W,H2_I,H1_I,Hsym_lower,tree_edges` (shell recipe given in the README).

Metrics (`evaluate_dfthc_angle_words`): decode `theta/pi = word/2^(brot−1)` on `tree_edges` (must be a tree rooted at 0, parent-before-child)
to unit vectors; rows 0..75 one-body, then R·B two-body in (ρ,b) order; `X^(ρc) = Σ_b w_b u_b u_bᵀ` (symmetrized from lower triangle);
`H1_THC = oei − ½Σ_r (pr|rq)`; `h1' = H1_THC − (η/2)S + β₁I − Σ W X`; `error_1 = ‖Σ_j λ_j v_j v_jᵀ − h1'‖_F` after one-to-one assignment of
submitted one-body rows to eigenvectors by |overlap| (`linear_sum_assignment`); `error_2 = ‖Σ X⊗X − tei − (S⊗I + I⊗S)/2‖_F` over N⁴;
`Λ = Σ|λ_j| + ¼Σ_{ρc}(|w_B| + Σ_b|w_b|)²` with `w_B = W + Σ_b w_b`; `E_SOS = ecore − ηβ₁ − (Σ|λ| − Σλ) − ½ΣW²`; `E_gap = E_upper − E_SOS`;
`λ_eff = sqrt(E_gap(2Λ − E_gap))` only if `0 < E_gap ≤ 2Λ` and a 100-digit `Decimal` recomputation agrees to 1e-6 rel (else NaN → reject).

Cost: `T_total = angles_toffoli (both passes) + outer_state_prep() + inner_state_prep() + 2(N−1)(2·brot−1)`;
`Q_total = outer_persistent + inner_persistent + J·brot + max(outer_temp, inner_temp, angles_temp)` where `angles_temp = max_k num_qubits −
selection − J·brot`. `SpinFreeData_V1(R,B,C,N=76,chi=10,beta=brot, optimize_qubits=True)` gives the heuristic (QROM/QROAM alias-sampling
formulas; three documented deviations from the original dfthc model). Score `= λ_eff·T_total·Q_total`; `inf`/raise if any gate fails.
Output JSON includes a full `resources` and `metrics` breakdown (see examples in §8.3).

Baseline worked example (SCORING_README, confirmed by clduab11/nasir26 runs): log-depth tree, brot 12, J 8, K 10 ordinary QROMs of 119 qubits and
3,974 Toffoli each → angles 79,480; heuristic 846 + 9,461 + 3,450 = 13,757; T 93,237; Q = 186 persistent (90 + 96) + 544 temp = 730; Λ 308.456,
E_gap 3.965477, λ_eff 49.301369 (49.254686 unrounded); error_1 3.19 mHa, error_2 18.64 mHa; shots 3,976·64 = 254,464; cost 3,355,599,588.3155365;
≈25 s. At brot 16 the heuristic is 846 + 9,461 + 4,650 = 14,957 Toffoli with 1,087 temporary qubits. Threshold pair
`sqrt(3.914898·(98 − 3.914898)) = 19.192` is "not a lower bound on λ_eff".

Reference ANGLE builder ([`angle_k_reference_circuit.py`](https://github.com/Inzainos/quantum-circuit-compilation/blob/main/verifiers/dfthcsos/example_submission/angle_k_reference_circuit.py)):
`delta[0]=batch[0]`, `delta[k]=batch[k]^batch[k−1]`; Qualtran-style segment-tree unary iteration over `selection` with `n−1` ancillas computed by
`init_and`/`del_and` (HMR + conditioned CZ), `_break_early` when a subtree's rows are identical; ≤ `A−2` Toffoli. CLI
`angle_k_reference_circuit.py submission.npz OUT --brot 12 --batch-size 8 [--format kmb]`.

Paper §III.C [OFFICIAL]: optimization scope = factorization (R,B,C,u,w,W), tree, brot, J, ANGLE circuits; Outer/Inner never opened; "this cap
keeps the interesting part of optimizing Inner dominant, and in our previous resource estimates gives a balanced physical cost, e.g. 200k physical
qubits and < 1 day"; internal run hash `9b8d070f41dd3b6e10a69dbbae9b047847646d1540de30c7b75799f15692f644`.

---

## 7. What the public frontier looks like, per task

### 7.1 invsqrt (fusion) — frontier 20.65× at 62 qubits

Timeline of public circuits (all [CLAIM], official-verifier numbers quoted by acco-cyber/nasir26/manwithacat/wahyurahmaniar):

| Circuit (sha prefix) | Author lineage | Q | mean Toffoli (static) | rotations | cost | ratio |
|---|---|---:|---:|---:|---:|---:|
| reference `e2bf8eb6` | Google | 260 | 7,735 | 37 | 2,076,774 | 1.00 |
| zjukop3 E5 `0687a7b2` | hand edit of reference | 231 | 6,852 | 37 | 1,641,977 | 1.265 |
| somfieao b0_a1 `38d90b45` | DeepSeek agent | 166 | 3,141 | 36 | 562,142 | 3.694 |
| Inzainos halfsplit `47c56f52` | hand | 183 | 2,867 | — | 570,323 | 3.64 |
| Gluzdov 84q / clduab11 port `17fc223d` | signed-digit quadratic | 84 | 1,553 (1,564) | 44 | 156,883 | 13.24 |
| Gluzdov v7 notebook | busyaprime 7 edits of Phuc Thai EXP222 | 78 | — | 44 | ≈1,696 C | ≈16 |
| mrmeows `0766a111` | mrmeows (team selenium) | 63 | 1,348.5 (1,416) | 41 | 103,546 | 20.06 |
| busyaprime v2 `07314803` | lookup re-synthesis | 63 | 1,334.5 (1,402) | 41 | 102,664 | 20.23 |
| busyaprime `9a8627` / kirilltym `e623b659` | window S1 re-synth | 63 | 1,329.5 (1,397) | 41 | 102,349 | 20.29 |
| yoyobar `67482db6` (+Özer patch) | first 62-qubit | 62 | 1,327.48 (1,497 static) | 41 | 100,693 | 20.63 |
| Özer `6dbb98b3` | patch removing one CSWAP AND | 62 | — | — | 100,940 | 20.57 |
| Ehan Mallick `bce2948f` | two 3-to-2 AND merges | 62 | 1,325.48 | 41 | **100,568.5** | **20.65** |

Architecture of the 63/62-qubit family (from clduab11 `tasks/invsqrt/PROVENANCE.md`, `docs/research/PRA-249…`, `staged/README.md`, Gluzdov
notebook markdown in acco-cyber `reference/public_notebooks/`, and manwithacat's viewer notes) [CLAIM]:

- Normalize x to mantissa `M ∈ [1,2)` with a ladder of one-bit shift stages; shift flags give `e` (parity) and `s`; `1/√x = 2^(s−10)·y`,
  `y = 2^((e−1)/2)/√M ∈ (0.5,1]`.
- **256-entry coefficient QROM** addressed by `(e, a)` (a = 7 high mantissa bits) holding a *centered quadratic* `y = K0 − R·δ`, `R = K1 − C2·δ`
  with **signed-digit offset** `δ = Σ(2d_i − 1)2^(i−22)` so every Horner row is a plain add/subtract (no controlled multiply)
  (Sumit Chongder's idea). Widths `f2=8, f1=19, fyr=27, gy=1, drop2=(5,)` (kozykappa); clduab11's regenerated fit: 256 `[K2,K1,K0]` triples,
  Lawson minimax, "groups of eight, three fractional slope bits, config (9,19,26,2,drop2=(5,))", curvature 8 bits with a 4-bit step register.
- Derivative split into residual + coarse bits (Rudra Bhaskar); high part of the result phased early and its register erased by HMR with one merged
  ANF phase repair; virtual lowest accumulator bit (zongaobian); carry-save rows and parity refit (Phuc Thai); fused output phase using
  controlled swaps; exact-domain affine Toffoli/CSWAP rewrites and "peephole" involution pass (kozykappa/anazemcev) — gates whose outcome is
  fixed on every legal input become Cliffords, eligible erasing Toffolis become HMR + conditioned CZ; rotation angles calibrated by LP over the
  whole domain (lightningv08/Mizero/acco-cyber).
- Budget per stage of the 84-qubit port (clduab11 `staged/README.md`): normalize 104 T, lookups ~247 ANDs each, inner MAC 87, outer MAC 280,
  phase kernels 66+154 with 15+29 rotations, merged repair 22, unnormalize 89; binding width = x22 + flags4 + res12 + coarse7 + low20 + carry18 + 1.
- acco-cyber `research/invsqrt-angle-lp/NOTES.md`: on busyaprime 63q the 41 rotations cost 295 of C=1,629.6 (ε 2.43e-13 → 28.77 T each);
  published angles are **already LP-optimal** and **no rotation can be dropped** (margin goes negative); worst error 0.99932 of tolerance at x = 161,
  min margin 3.18e-12 turns at x = 52,229. Doubling the margin would save only ~10 Toffoli-eq.
- manwithacat viewer: 62q circuit has 47,248 ops, 1,497 Toffoli-class gates of which only 1,327.5 run per input on average (many in
  measurement-conditioned blocks); at most 34 of the 40 non-x qubits hold a 1 at any instant.
- clduab11's source audit (PRA-320): mrmeows' published "generators" replay **frozen circuit checkpoints** and synthesis certificates (e.g. a
  32-stage pipeline starting from `round5_phase/l6_exact.logical.kmx`); no closed source-to-circuit build exists publicly for the 63q design.

Other invsqrt approaches on GitHub [CLAIM]:
- somfieao (agent proposal `results/vqcc_invsqrt/b0_a1/proposal.md`): QROM-indexed Taylor degree-3 over 512 cells (k=9), all-positive Horner,
  barrel shifts, Fp=29 → 166 q / 3,141 T. Observed that `init_lookup` costs `2^k − 2` Toffoli independent of target width, `del_lookup` ~10 %,
  and that **a compute-only circuit that `R`-resets scratch fails with random ±0.5-turn phases** ("`R` dephases: phase ^= qubit & rng").
  A finer grid (k ≥ 10) with quadratic was strictly worse. Agent cost ≈$13–15 per attempt.
- Inzainos `src/invsqrt_piecewise.py` / `invsqrt_halfsplit.py`: piecewise polynomial deg 2 on 2^j-wide segments, Chebyshev-node fit, coefficients
  via `init_lookup`, "half-split" table folds `M ∈ [2,4)` into `[1,2)` with 1/√2 baked in (2^(j+1) entries instead of 3·2^j); best verified
  deg=2, j=8, wc=28, dd=13: Q 183, T 2,867, worst error 0.893, score 570,323. Their earlier precision sweep: `result_bits=28` fails at x = 917,115.
- zjukop3 E5: replacing the 10-qubit unary thermometer by a 4-bit binary `s` (pure CX conversion) gave Q 237→231 and T 7,334→6,852 at once.
- blucca: 1024-cell linear interpolant with bias, 150 q, 4,226 T (3.04×, not officially verified); 32-interval cubic 284 q / 9,252 T;
  Walsh-phase approach needs 76,640 fine rotations (dead end).
- nasir26: LUT-seeded Newton generator reached only 1.744× (3 salts).

### 7.2 dqi (combinatorial optimization) — frontier ≈63–64× at 892 qubits

| Circuit (sha prefix) | Lineage | Q | mean T | failures (102,400) | cost | ratio |
|---|---|---:|---:|---|---:|---:|
| reference `959471d0` | Google EEA | 1,893 | 5,725,108 | 0 | 2.444e13 | 1.00 |
| zjukop3 E8 (CSWAP freeze) | hand | 1,893 | 5,164,841 | 1 | — | 1.103 |
| clduab11 BM+Forney port `529b0750` | Gu et al. via anazemcev/kozykappa notebooks | 1,789 | 445,229 | 3–8 phase | — | 14.0–14.2 |
| Gluzdov v7 881q | in-place continued fraction | 881 | ~0.96 M | — | — | ~10.6 (early) |
| clduab11 Hankel port `17df1828` | SomeJoint v7 | 883 | 996,048 | 0–1 | 9.29e11 | 26.3 |
| Özer v8 Bézout-Schur `569863ae` | jday96314 decoder, Chilton synthesis | 883 | 519,152 | 6 val + 2 ph | 4.950e11 | 49.4 |
| clduab11 fused `7beea291` | SomeJoint kernel v12 | 889 | 474,308 (static 487,331) | 0 | 4.466e11 | 54.7 |
| SomeJoint 883 + 658-T jet `ef334fee` | "GPT-6 Astra Pro" | 883 | 467,790 | 1 ph | 4.365e11 | 56.0 |
| SomeJoint 897 `b3354f60` | same | 897 | 440,633 | 0 | 4.2235e11 | 57.9 |
| alexchilton 889 `4ee7a17b` | — | 889 | 440,564 | 0 | 4.1478e11 | 58.9 |
| 889 `7a378f47` (hengck23/kirilltym/SomeJoint) | — | 889 | — | — | 4.084e11 | 59.8 |
| yoyobar 889 `73e1b187` | — | 889 | 427,475 | 0 (1 in 1 of 12 salts) | 4.0246e11 | 60.7 |
| ahoirg/yoyobar 893 `fb2da4f2` | SomeJoint q18 + yoyobar one-carry pole history | 893 | 407,444 | 0 (1 ph at salt s3) | 3.8706e11 | 63.1 |
| wahyurahmaniar 892 `c453c7ac` | P6 flag measured + recomputed | 892 | 407,005 | 0 locally, **2 on Kaggle** | 3.8578e11 | 63.35 |
| manwithacat HW-06 892 `c2531119` | 12 borrowed-wire 3-AND uncomputes → HMR + CCZ | 892 | 403,587 | 0 | 3.8254e11 | **63.9** |
| SomeJoint "900-qubit" v23 | newest, cost not recorded | 900 | — | — | — | — |

Design facts of the SomeJoint "q18"/Schur lineage [CLAIM, from Gluzdov notebook markdown, clduab11 `tasks/dqi/*/PROVENANCE.md`, nasir26 NOTES,
ccjjllt audit, wahyurahmaniar `dqi/README.md`]:
- The 70 syndrome words are rewritten **in place** as partial quotients of the continued fraction of `S(z)` ("the decoder needs almost no
  workspace beyond its 840 input qubits"); consecutive levels share one power-series reciprocal; conversion in place to σ, Ω; Chien/Forney
  sweep under the record bits; everything reversed. Stage names in the fused build: mask_projection, initial, extract (87,040 T), synthesis
  (44,654), convert_lookahead (69,220), scan (44,275), unconvert (70,342), unsynthesis (53,803), unextract (117,997), uninitial, restore_masks.
- **Classical mask projection** (manwithacat): 70 classical field words λ_i solved from a Vandermonde system absorb the record at positions 0–69
  into a known syndrome phase `Tr(Σ λ_i s_i)`, so the sweep skips those positions.
- GF(2¹²) multiplier: evaluation/interpolation over GF(8) (degree 4, 7 points incl. ∞, 6-AND GF(8) products): **rank 42** symmetric; tower
  norm trick (norm of inverse = inverse of norm); a 99-rank GF(2²⁴) product is also used; ccjjllt's audit says 53.4 M of 60 M ops are CX.
- Approximations: missing leading coefficient repaired by a paired 3+1 step; histories with ≤2 gaps exact; rarer patterns unhandled;
  ccjjllt fixed-weight probe: w = 0 gives 131/256 phase errors, w = 2, 8, 16 give 256/256 value errors, w = 17–20, 35 give 0 — i.e. the decoder is
  deliberately wrong at low weights that the DQI distribution almost never samples (P(w ≤ 16) ≈ 1.6e-7 per shot).
- Pole-flag structure (wahyurahmaniar): `P_g = 1` iff weight w is odd and `w ≤ 2g−1`; width peak 893 occurs only in `unextract`; measuring P6 and
  recomputing it (23 T + CZ) gives 892; dropping pole branches of groups 7–8 and zero flags of folds 18–20 saves 439 T/shot at ~3e-8 failure.
- Trade-offs quantified: at 889 q each qubit is −0.23 % cost; one failing shot +0.459 %; `R0 = 1.19126` even at zero failures; "retaining the norm
  cache −12,100 T, +12 Q" is roughly neutral.
- Gu et al. (`andigu/uncompute`, not directly portable): BM recurrence on one shared arithmetic path, no stored discrepancies, half-degree Euclid
  pass for Ψ = 1/σ′, 23 Toffoli per swept position over 4,024 positions; 442,397 T, 1,837 peak qubits, 7 wrong signs in 100,000.
- Negative result (nasir26): a *reversible* Berlekamp–Massey rewrite of the reference needs ≈2,600 qubits (history storage), worse than EEA's
  1,893; the EEA layout's floor is 2nb = 1,680 so only ≈1.27× is available from Q at that floor.
- nasir26 attributions of the reference: EEA sweep 50 % of T, Chien/Forney 25 % (inversions 22.5 %), shift_b 8.3 %, swap_a_and_b 6.9 %; polynomial
  storage 92.5 % of Q.

### 7.3 dfthcsos (chemistry) — frontier ≈10.3–10.6× at Q 428

| Factor / loader [CLAIM] | (R,B,C), rows | brot, J, K | λ_eff | T | Q | cost | ratio |
|---|---|---|---:|---:|---:|---:|---:|
| reference | (65,60,60), 3,976 | 12, 8, 10 | 49.301 | 93,237 | 730 | 3.356e9 | 1.00 |
| Signed-Digit-Memory v3 lineage (k256.dev factor) | — | — | 47.559 | 71,958 | 681 | 2.33e9 | 1.44 |
| Gluzdov v8 `809a9929` (clduab11 J=10) | (1,496,384), 572 | 11, 10, 8 | 47.856 | 20,286 | 833 | 8.087e8 | 4.15 |
| rustad R10 (clduab11 J=3 port) | (10,129,60), 1,366 | 8, 3, 25 | 48.031 | 21,922 | 415 | 4.370e8 | 7.68 |
| Özer R4/B255/C128 + lightningv08 J=5 (kirilltym gauge) | (4,255,128) | 8, 5, 15 | — | — | 429 | 4.270e8 | 7.86 |
| mrmeows C59 (clduab11 J=4) | (10,129,59) | 8, 4, 19 | — | 274 T/circuit | 128/ckt | — | 8.9 |
| Özer V9 + busyaprime refit | — | 8, 5, 15 | 47.537 | 17,330 | 431 | 3.551e8 | 9.45 |
| heliosli J5 on Özer C46 table `ab4d2288` | — | 8, 5, 15 | 47.494 | 17,066 | 431 | 3.493e8 | 9.61 |
| SomeJoint R8/B143 C62 `377c0080` | (8,143,62), 1,220 | 8, 5, 15 | 48.271 | 16,752 | 430 | 3.477e8 | 9.65 |
| SomeJoint R8/B143 C60 full-XOR `07dfbd32` | (8,143,60), 1,220 | 8, 5, 15 | 48.561 | 16,528 | 430 | 3.451e8 | 9.72 |
| clduab11 B143 port (submission-011) | (8,143,60) | 8, 5, 15 | 48.764 | 16,366 | 430 | 3.432e8 | 9.78 |
| nasir26 v2 (`open_circuits_v33` + Gluzdov weights) | — | 8, 5, 15 | 48.614 | 16,296 | 430 | 3.407e8 | 9.85 |
| heliosli 10-30 `6503daab` | — | 8, 5, 15 | 48.324 | 16,266 | 430 | 3.380e8 | 9.93 |
| Özer weights via manwithacat Real-150K `47427ee0` | — | 8, 5, 15 | 48.296 | — | 430 | 3.378e8 | 9.93 |
| marculera C40 + public tensorqrom loaders | (9,143,40), 1,363 | 8, 5, 15 | 47.097 | 16,237 | 428 | 3.273e8 | 10.25 |
| C40 + heliosli v36 weights, Dmitrii v44 loaders (HW v5) | (9,143,40) | 8, 5, 15 | 47.040 | 16,233 | 428 | 3.268e8 | 10.27 |
| C40 + wahyurahmaniar loaders | (9,143,40) | 8, 5, 15 | 47.097 | 15,747 | 428 | 3.174e8 | **10.57** |

What moves the score [CLAIM + INFERENCE]:
- With `J=5, brot=8` the heuristic part is fixed at 369 + 5,311 + 2,250 = 7,930 T, 86 persistent + 304 temp qubits; `Q_total = 86 + 40 + 304 = 430`
  regardless of ANGLE workspace (ANGLE temp ≤ 77 < 304), so **ANGLE workspace up to the 128 cap is free** and all effort is in λ_eff and the
  ANGLE Toffolis (≈4,200–4,750 per pass, i.e. 52–58 % of T).
- Every top factor pins all gates: error_1 ≈ error_2 ≈ 19.999 mHa, E_gap = 3.914899–3.914902 (floor 3.914898), Λ ≈ 290–306. Since
  λ_eff ≈ sqrt(2Λ·E_gap) at the floor, the only remaining classical lever is **Λ** (the two-body one-norm, 96 % of Λ in the reference).
  nasir26: replacing Σ|w_b| by the nuclear norm of each X_rc would save only 4.2 %; real gains need a new factorization.
- Rounding: naive 11-bit re-rounding of the reference words explodes error_1 (3 → 221 mHa); the shipped words are rounding-aware; nasir26 models
  `error_2² = e0² + r²·4^(12−brot)` with e0 ≈ 16.0 mHa, r ≈ 9.7 mHa, and found coordinate-descent/AdaRound-style re-rounding gives no gain.
- Loader construction (wahyurahmaniar `chemistry/README.md`, clduab11 `B143.md`/`C59.md`): each output bit is an ANF polynomial of the 11 address
  bits; split 7 high / 4 low bits; keep high monomials cached (78 Toffoli), low monomials in a small slot cache (11 Toffoli) erased by HMR+CZ;
  mixed terms paired so **one Toffoli covers two products** via `(h1⊕l2)(h2⊕l1) = h1l1 ⊕ h2l2 ⊕ h1h2 ⊕ l1l2`; GF(2) kernel relations reduce the
  product count ("plan" files); LSB of each word in batches 4–14 is affine in the low bits so two products per word suffice; bit 7 = bit 6 on
  the C40 table so only 35 of 40 bits are loaded. Result 294–318 T per circuit at exactly 128 qubits.
- Alternative "reference-style" builders (clduab11 `circuit.py`): bank-bits ANF lookup, prefix pebbling, `J=10, brot 11` ordinary QROM at
  exactly 128 qubits.
- Warning (muchat007 via acco-cyber RUNLOG; acco-cyber `research/chem_xor_audit.py`): the shared public loaders **fail an arbitrary-target XOR
  audit** (uncorrected phase on random incoming word states) yet pass the official verifier, which only drives the contract input sequence;
  kirilltym's loaders need bit7 = bit6 on the target. [INFERENCE: a private-split salt changes only HMR branches, so this is not an LB risk,
  but such circuits are not true XOR oracles.]
- Shape sweeps on the reference words (Inzainos): brot 10/8 cannot be produced from 12-bit words by `angle_k_reference_circuit.py`
  (words out of range); brot 12 J 12 → 167-qubit circuits rejected; brot 14 → errors 474/202 mHa; J 4 → 682 q, 5.54e9 (worse).

---

## 8. Per-repository digest

### 8.1 Inzainos/quantum-circuit-compilation (Spanish; "DBHEXA" agents)

- Approach: hand-designed circuits assisted by AI agents (`AGENTS.md`), Qualtran-bloq wrappers, unit tests. README documents prizes/timeline
  (start 2026-10-22; milestone 11-20; longest leader 2027-01-04; entry/merger 01-13; final 01-20; $150k pool: 50/25/10/5/5/5k + 10k milestone +
  10k longest leader + 3×10k single-task + 50k additional).
- invsqrt: precision tweaks of the reference (28/28/29 → 27/27/27: Q 254, T 7,405, −6.5 %); then `invsqrt_piecewise.py` (deg 2, j 7, wc 28,
  dd 13: Q 185, T 2,993, 599,866) and `invsqrt_halfsplit.py` (deg 2, j 8: Q 183, T 2,867, 570,323; worst error 0.893; full-domain 1 shot/x PASS,
  64-shot run not yet done).
- dqi: `dqi_optimized_v10.py` = reference with 7-bit degree counters (max 127 > 73) → Q 1,888, T 5,708,480 (−0.82 %); honest note that the file
  imports `galois_iqft` but never uses it. Listed but unrealized ideas: share reg_a/reg_b (−438 q), active-length reg_b, scaffold reuse, ancilla pool.
- dfthcsos: only sample-data sweeps; no FCIDUMP in repo so no local verification.
- **Incident (CHANGELOG 2026-11-03):** an AI-generated "submission_final" zip replaced the valid one; official verifiers rejected all three parts:
  invsqrt (Q184/T2,279) failed at x = 2 with phase error 0.293 turns; dqi (Q138/T4,408, "245,000×") failed "Registers must be exactly S0..S{n-1}
  and E0..E{m-1}" (it declared `addr_high/addr_low/result`); dfthcsos npz had 54×54 matrices instead of (R,B,N)/(R,B,C) tensors and all five
  `angle_k` were the same file; `.kmb` files were `.kmx` text; files were nested under `submission/`. `SUBMISSION_DOCUMENTATION.md` still carries
  those unverified claims — treat as fiction.
- Useful: `results/README.md`, `benchmarks/fusion_energy/baseline/BASELINE.md` (score they compute as Q × toffoli_equivalent).

### 8.2 somfieao/kickmix-compiler

- Approach: Google's Dream-RSI engine (pinned `8ec35bd`) with Claude Code CLI driven by DeepSeek-V4.1-Flash; exploration agents have file tools
  only, no shell, cannot run circuits; evaluator = official verifier with a fresh random salt; `combined_score = 2076774.2337/score`.
- Result: one attempt (b0_a1) reached 3.694×, LB 1.54586 with reference dqi/dfthcsos; verification 20–30 min CPU; ≈$13–15 per attempt; a later
  attempt failed verification at x = 2 (0.5-turn phase error).
- Files worth reading: `tasks/vqcc_invsqrt/vqcc_invsqrt.txt` (the agent problem statement — concise correct contract),
  `results/vqcc_invsqrt/b0_a1/proposal.md` (simulator cost measurements), `scripts/kaggle_submit_lowlevel.py` + README §8 (upload through
  `storage.googleapis.com` when `www.googleapis.com` is blocked; archive must be `submission.zip`), `docs/kickmix-api.md`.

### 8.3 clduab11/quantum-hackathon ("Praxen")

- Approach: an elaborate agent organisation (Paperclip tickets PRA-1xx–3xx, roles "john-wick", "the-adjudicator", gates G0–G5, append-only
  decision register with hundreds of rows, provenance maps with per-file SHA-256). All shipped circuits are **ports of Apache-2.0 public
  notebooks**, regenerated byte-for-byte (G5). Rule R10 forbids shipping k256.dev or jday96314 artifacts.
- Standing: submission-011 (10-29) LB 19.20572; invsqrt 84q 13.24× (Gluzdov v7 recipe, CUDA refit), dqi SomeJoint fused 889q 54.73×, chemistry
  SomeJoint (8,143,60) full-XOR 9.78×; PRA-325 later vendors mrmeows' 63q `0766a111` (20.06×) under a licence ruling.
- Highest-value documents: [`docs/field-guide.md`](https://github.com/clduab11/quantum-hackathon/blob/main/docs/field-guide.md),
  [`tasks/invsqrt/PROVENANCE.md`](https://github.com/clduab11/quantum-hackathon/blob/main/tasks/invsqrt/PROVENANCE.md) (who invented what in the
  invsqrt lineage, with Kaggle scriptVersionIds), [`tasks/invsqrt/staged/README.md`](https://github.com/clduab11/quantum-hackathon/blob/main/tasks/invsqrt/staged/README.md)
  (why their 84q design cannot reach 63q: payload alone is 61 wires), [`docs/research/PRA-320-invsqrt-source-audit.md`](https://github.com/clduab11/quantum-hackathon/blob/main/docs/research/PRA-320-invsqrt-source-audit.md),
  [`docs/dqi-bm-forney-design.md`](https://github.com/clduab11/quantum-hackathon/blob/main/docs/dqi-bm-forney-design.md) (Gu vs competition table),
  [`tasks/dqi/PROVENANCE.md`](https://github.com/clduab11/quantum-hackathon/blob/main/tasks/dqi/PROVENANCE.md), `tasks/dqi/fused/PROVENANCE.md`,
  `tasks/dqi/hankel/PROVENANCE.md`, `tasks/dfthcsos/{B143,C59,RUSTAD,FIT_V3,FACTOR_PIPELINE}.md`, `docs/reports/pra2{32,37,47,50,80}*.md`,
  `docs/handoffs/p0-4-kickmix-build.md` (metric snapshot recipe, reference calibration), `ledger/examples/reference/logs/*.json` (baseline JSON).
- Measured facts: Q for invsqrt/dqi is "largest referenced qubit id + 1 (register declarations included, no lifetime tracking)" per Qualtran
  `circuit.cc:1008–1029` at `c58703d`; conditioned fixups pay only when they run; mean dqi Toffoli differs from static (5,725,108.86 vs 5,725,461).
- Negative results worth not repeating: Gluzdov-recipe port tops at 13.24× (unrefined groups fail; dropping any rotation fails); chemistry refits
  of the 65/60/60 baseline repeatedly violate 20 mHa; `paired_qrom` J=3 on C59 gives 7.78×; J=4 lift gives 132 qubits (> cap).

### 8.4 acco-cyber/Quantum-Circuit ("gwey1025")

- Approach: an hourly scheduled agent ("Koushik-one way") that downloads the newest public Kaggle notebook outputs, hash-checks members, re-runs
  the official verifiers locally with its own salts, assembles the best-of portfolio and submits (5 quantum slots/day). Versions v1 (12.13,
  10-26) → v16 (23.17173, 10-30); rank 92/1171 at 19.58 (10-27), ~275/1703 at 23.0 (10-30).
- Leaderboard readings: 10-27 00:32 UTC top 23.352/22.886/22.805; 10-28 25.629/25.052/24.159; 10-29 26.141/25.531/25.341; 10-30 22:30
  26.764/26.314/26.263. "About 25 teams share the public plateau 19.5790 exactly" (kirilltym's QROM+Tower42 output).
- Every portfolio version is documented in `notebooks/v*/NOTES.md` with member hashes and verifier JSONs; `summary.json` files contain complete
  official outputs including `resources` breakdowns and `shot_operation_counts`.
- Research: rotation-angle LP (angles LP-optimal, no droppable rotation); chemistry XOR audit; observation that DQI cost is salt dependent
  (one value error in 12 salts of yoyobar's 889q); each qubit at 883 is −0.23 % dqi cost; "every public > 21.8 portfolio shares the same invsqrt
  and chemistry blocks, they differ only in DQI".
- `reference/public_notebooks/quantum-circuit-compilation-from-source.ipynb` is a copy of Gluzdov's public notebook (markdown cells summarize the
  78q invsqrt, 881q dqi, (1,496,384) chemistry designs and a full credit chain).

### 8.5 nasir26/vqcc-kaggle

- Approach: metric-identical harness (`harness/score.py` vendors the metric), Kaggle kernels for dqi verification (laptop had 7.9 GB), later a
  256-core host with a user-level glibc 2.39 runtime (`tools/host_runtime.sh`) to load the official `.so`. Portfolio of public members:
  v1 22.77459, v2 22.78536 (10-29). Submissions zip attached to GitHub release `submissions-2026-10-29`.
- `docs/RULES.md`: verbatim Kaggle page quotes (cost table, submission format, data-security clause: competition data must not be redistributed
  — several repos above violate this), confirmed verifier facts.
- `docs/{invsqrt,dqi,dfthcsos}_anatomy.md`: the best quantitative breakdowns of the three references (quoted in §4–6).
- Studies: tower-field GF(((2³)²)²) arithmetic (mul 54, inv 77 — superseded by the public rank-42 multiplier), flip-graph search for GF(2¹²)
  multipliers (`tasks/dqi/flipgraph.c`, `scheme42.py`), chemistry rounding/shape sweeps, GPU refit failure of the 65/60/60 baseline.
- Note: "The metric rejects hardlinked files, so stage real copies"; "Kaggle CLI returned HTTP 400 for file names other than submission.zip".

### 8.6 wahyurahmaniar/Verifiable-Quantum-Circuit-Compilation

- Own contributions: `chemistry/plan.py` + `loader.py` (paired-product ANGLE loaders, 4,503 T/pass vs 4,748 public on the C40 table → chemistry
  10.57×) and a dqi 893→892 patch set on ahoirg's hash-pinned build of SomeJoint's q18 decoder. LB 23.97677 (893q) and 23.93 (892q: two failing
  shots in Kaggle's draw although 0 in 307,200 local shots).
- `CREDITS.md` is the most complete lineage map of the public frontier (marculera, Özer, SomeJoint, mrmeows, heliosli, lightningv08, kozykappa,
  Sumit Chongder, anazemcev, Phuc Thai, Michael Rustad, k256net, Gluzdov; yoyobar, ahoirg; Ehan Mallick).
- Inputs pinned: ahoirg `qcc-reproducible-circuit-assets` (`build_dqi.py` sha `80c39449…`, `dqi-source-bundle.json`), Özer `vqcc-v18-portfolio`
  invsqrt `bce2948f…`, marculera C40 `submission.npz` sha `89357442…`.

### 8.7 manwithacat (kickmix-engine, kickmix-macos)

- `kickmix-engine`: Rust simulator, bit-identical to kickmix; `verify` reproduces all official summary fields; DQI sampler reproduces NumPy PCG64
  draws; `diff`/`profile` predict a candidate's expected DQI cost from 16 paired batches in ~5 s; chemistry verify 4.9× faster on Kaggle
  (FCIDUMP parsing is 66 % of the official verifier's 7.6 s). `qrom-plan` crate ports the chemistry kernel-relation planner (90 µs per word flip).
- `kickmix-macos`: 8 patches (NEON, PopCounter fast path, streaming `reaction_depth`, bulk shot IO); full DQI verification peaks 2.0 GiB instead of
  7.8 GiB; wheels on Kaggle datasets `manwithacat/kickmix-fork-wheels`; public quickstart notebook; browser viewer with stage descriptions of
  the 62q/63q invsqrt circuits.
- The author's "Hedge Wizardry" notebook v5 (HW-06 dqi 892q 403,587 T; Ehan 62q invsqrt; C40 mixed loaders 16,233 T) verified locally at GM 23.838
  [CLAIM via ccjjllt].

### 8.8 zjukop3/google-quantum-circuit-compilation-2026-support

- Six submissions 10-24/25: 1.00000 (reference reproduction, byte-identical 73,803,082 B zip; 64 of 662 teams scored within [0.99,1.01], median
  5.85) → 1.04644 → 1.04905 → 1.08145 (invsqrt E5) → 1.09489 (dqi E7) → 1.11751 (dqi E8). Predictions matched LB to 5 decimals, confirming
  `score = (Π ratio)^(1/3)` and that the dqi "salt lottery" (one extra failing shot) explains a −0.0017 residual.
- Notes E1–E8 (Chinese): reference qubit anatomy, "register freeze" of dqi multiply/CSWAP registers (T 5,725,110 → 5,164,841 at Q 1,893).

### 8.9 Other repos (brief)

- **harshulchess77-arch**: harness scaffold with baseline scores only; `notes/repo_ground_truth.md` restates the contracts; its `.backup/`
  manifests hold sha256 of the sample files.
- **parth33320**: scaffold using "Jules & Pocock" agent SDLC; `docs/plans/dqi/01-analysis.md` has a correct register table of the reference
  decoder (1,803 persistent qubits).
- **ccjjllt/quantum**: audits of the public HW-06/heliosli portfolios; per-stage static Toffoli shares of the 889q decoder (unextract 28 %,
  convert+unconvert 30 %, extract 15 %, synthesis 17 %, scan 10 %); priorities list ("recover exact generator first; Q 840 floor would give at
  most +3.85 % GM").
- **Arnabs-ops**: Kaggle-notebook pipeline reaching 10.88; `tools/dfthcsos_estimator.py` reproduces the heuristic model; explored (R,B,C)
  transitions (R26/B60/C30 four-address, R19/B49/C24, R12/B36/C20).
- **blucca**: arithmetic-first invsqrt designs (see §7.1), Walsh negative result.
- **tatra-labs/kickmix-arena**: open T×Q evaluator for Gu-style tasks; not competition-specific.
- **andigu/uncompute**: Gu et al. tasks; `tasks/dqi-reed-solomon/README.md` documents their RS(4095,4025,71) instance (field 4331, SHA-256 mask,
  100,000 shots, ≤100 failures) and the khattar-eea baseline (5,125,070 T, 1,938 q).

---

## 9. Pitfalls and gotchas (collected)

Verifier/metric mechanics [OFFICIAL]:
1. Q = `circuit.num_qubits` = max qubit id + 1; freeing a high id does not lower Q unless ids are reused (clduab11 reading Qualtran source).
2. Toffoli cost is the **mean executed** count; `CCX/CCZ/CSWAP` under `PUSH_CONDITION`/`if b` count only when the condition holds → measurement-
   based uncomputation with conditioned fixups is ~half price; `del_and`/`del_lookup` cost ~0 Toffoli.
3. `R` on a dirty qubit applies a random sign flip; HMR on a qubit that holds a function of others kicks `(−1)^{b·f}` which must be repaired by a
   classically conditioned Z/CZ/CCZ. "Compute then reset" designs fail with random ±½-turn phases (somfieao agent, paper §II.A).
4. invsqrt allows zero failures across 200,540,928 shots; rotation ε is set by the single worst shot's margin (`min_margin`), so one tight x
   makes every rotation expensive; the metric's secret salt re-rolls HMR outcomes only.
5. dqi: Z_POW forbidden; one failing shot = +0.459 % cost; two salts can differ by one failure; ε⁺ ≥ 1/16 (≈6,000 failures) voids the task.
6. dfthcsos: `selection` width fixed; `word_j` width declares brot; no Z_POW; words must be deterministic across the 64 shots; reverse pass must
   restore previous batch; `H1_I`/`Hsym_lower` ignored; pickles refused; strict floors Λ > 49.0, E_gap > 3.914898; errors ≤ 20 mHa; any ANGLE
   circuit > 128 qubits rejected (128 allowed).
7. Zip: exactly one of each entry anywhere in the tree; no hard links/symlinks/special files; allow-listed instructions only; ids < 699,050;
   npz arrays format 1.0, ≤ 64 MiB decoded; `tree_edges` integer (75,2).

Practical [CLAIM]:
8. Upload must be named `submission.zip` (Kaggle UI and CLI); ~45 min scoring; 5/day.
9. `kickmix.so` is CPython 3.13 / x86-64 / glibc ≥ 2.34 (GLIBCXX_3.4.32); Ubuntu 20.04 needs a patched runtime (nasir26) or a source build
   (somfieao conda g++ 13; zjukop3 Homebrew LLVM 20 on macOS).
10. dqi verification needs ~6 GB per worker (4 workers default); `reaction_depth()` of large circuits can OOM (`std::bad_alloc`) — use
    manwithacat's fork or `kickmix-engine`.
11. Local invsqrt scores on a subrange of x are not comparable (mean Toffoli and min margin depend on the range) — Inzainos reported 593,733 on
    x ≤ 9,984 vs 599,866 on the full domain.
12. Public "generators" often replay frozen `.kmx` checkpoints and certificates; byte-for-byte rebuilds from numeric inputs are rare (clduab11
    PRA-320). Licences: many notebooks are Apache-2.0, jday96314's repo states none, kozykappa's dataset "Other".
13. Resubmitting identical bytes gives the identical score (same salt → same seed).
14. Kaggle data-security clause forbids redistributing competition data; several repos nevertheless commit `verifiers/`, `kickmix.so`, the PDF.

---

## 10. Inferences and recommendations [INFERENCE]

- The leaderboard leaders (26–28) are ≈3× the product of the public frontier (20.65 × 63.9 × 10.57 → GM 23.8); matching the public parts gets
  ≈23.8–24.0; the single-task prizes will likely go to circuits beyond: invsqrt < 100k, dqi < 3.8×10¹¹, chemistry < 3.2×10⁸.
- invsqrt levers left: structural (fewer Toffoli in lookup/MAC stages, 1–2 fewer qubits — each qubit at Q 62 ≈ 21 Toffoli-eq), not rotation tuning.
  All published 62/63q circuits are hand/agent-edited binaries, so a from-source re-implementation of the signed-digit quadratic schedule is itself
  valuable (and required for prizes).
- dqi: cost ∝ Q²·T with 840 syndrome qubits mandatory; at 892 q only 52 private qubits remain (ideal 840 q would give +3.85 % GM); the
  Toffoli side (≈400k, 99-rank GF(2²⁴) products, conversion stages ≈30 %) and the approximation/R trade are where the public lineage still moves.
- chemistry: the ANGLE-loader side is near an algebraic floor for the C40 table (~294–318 T per 5-word circuit); the classical lever is a
  factorization with lower Λ (two-body one-norm) at error_2 = 20 mHa and E_gap pinned at the floor; fewer addressed rows (R·B) cut both T and the
  loader count. The starter-kit trainer (JAX) plus `fixed_shifts.npz` are enough to attempt this; GPU refits of the 65/60/60 baseline failed for
  nasir26, the public (9,143,40) table came from marculera's "compact groups from the Hamiltonian" + augmented-Lagrangian refit.
- Tooling: use the official verifiers with a fixed public salt for development, `kickmix-engine diff` for fast dqi A/B, and keep a 7-salt sweep
  before uploading dqi circuits with rare-branch approximations.

---

## 11. Appendix — local paths

- Repos: `/tmp/claude-0/-home-user/af1e8b3b-1af8-51dd-9e8d-ec3f80eabc0b/scratchpad/participants/` (21 clones, see §1).
- Official verifiers (verbatim): `…/participants/Inzainos_quantum-circuit-compilation/verifiers/` and
  `…/participants/harshulchess77-arch_Google-Quantum-AI-Verifiable-Quantum-Circuit-Compilation/third_party/google-verifiable-quantum-circuit-compilation/`
  (includes `kickmix/kickmix.so`, `verifiable_circuit_compilation.pdf`, `verifiers/dfthcsos/FeMoCo76o113e.fixed_shifts.npz`, sample `.kmb`s).
- Metric: `…/scratchpad/official_downloads/google-quantum-ai-metric.py` (+ `metric_kernel_pull.json`).
- Starter kit: `…/scratchpad/official_downloads/starter_kit/starter_kit/` (+ `FeMoCo76o113e.fixed_shifts.npz`, `starter_kit_list.json`).
- Baseline verifier outputs: `…/participants/clduab11_quantum-hackathon/ledger/examples/reference/logs/{invsqrt,dfthcsos}.json`;
  frontier outputs: `…/participants/acco-cyber_Quantum-Circuit/notebooks/v*/summary.json`, `…/participants/wahyurahmaniar_*/results/*.json`,
  `…/participants/nasir26_vqcc-kaggle/ledger/runs/*.json`.
