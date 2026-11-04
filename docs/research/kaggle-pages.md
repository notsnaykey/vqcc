# Kaggle pages digest — Google Quantum AI: Verifiable Quantum Circuit Compilation

Competition: <https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation>
Compiled 2026-11-04. Raw material and provenance: `docs/research/kaggle-raw/` (read its `README.md` first).

> **How this was obtained.** kaggle.com could not be rendered from this session: the HTML shell loads but every
> internal API call is answered with a reCAPTCHA Enterprise challenge, so each page shows "Something went wrong and
> this page crashed!" (see `kaggle-raw/kaggle-*.CRASHED-recaptcha.txt`). WebFetch cannot resolve kaggle.com here.
> Everything below therefore comes from public mirrors that quote the Kaggle pages (chiefly `nasir26/vqcc-kaggle`
> `docs/RULES.md`, which carries **verbatim quotes fetched from Kaggle on 2026-10-27**, and the official
> `verifiers/dfthcsos/SCORING_README.md` shipped in the competition data), cross-checked against six other
> participant repositories and search-engine snippets of the live pages. **Blocks marked VERBATIM are quoted from
> those mirrors of the Kaggle text; everything else is my summary. Re-verify against Kaggle before relying on
> dates, limits or rule wording.**

---

## 1. Overview

### 1.1 Description (summary; the Kaggle description text itself was not retrievable verbatim)

- Hosted by Google Quantum AI and Kaggle; launched 2026-10-22 (Google Open Source Blog announcement by Tanuj Khattar
  and Ryan Babbush, 2026-10-21). Tagline on the page: "Reducing the resources required for quantum applications"
  (from the page `<meta name="description">`, which did load). Kaggle listing flags: *Medal: True, Kernel Only: False*.
- Task: find smaller/faster compilations of three "kickmix" subroutines, each a bottleneck of a fault-tolerant algorithm:
  1. **invsqrt** (fusion energy / stopping power in inertial-confinement fusion): phase |x⟩ by 1/√x for every x in a
     22-qubit register (Trotter simulation of electrons on a grid; Rubin et al., PNAS 2024).
  2. **dqi** (combinatorial optimisation, Decoded Quantum Interferometry / Optimal Polynomial Intersection): a reversible
     Reed–Solomon RS(4095, 4025) syndrome decoder over GF(2^12) (Jordan et al., Nature 2025; Khattar et al., arXiv:2510.10967).
  3. **dfthcsos** (quantum chemistry, FeMoCo nitrogenase cluster): QROM circuits loading the Givens-rotation angle words
     of a DF-THC/SOS block encoding of the FeMoCo76o113e Hamiltonian, plus the factorisation itself.
- Why verification is cheap: kickmix circuits contain only reversible classical gates, diagonal phase gates and
  Hadamard-measure-reset (measurement-based uncomputation), so a classical simulator checks them input-by-input
  (64–512 shots per CPU instruction, >100 M gates on one core). Linearity extends basis-state correctness to superpositions.
- Verifier design: fuzz testing on every valid input (invsqrt, dfthcsos addresses) or weighted random inputs (dqi);
  inputs and measurement outcomes are seeded from a salted cryptographic hash of the submission (Fiat–Shamir), so
  **there is no hidden test set** and any byte change gives fresh draws.
- Companion paper: Khattar et al., *Leveraging verifiable structure in quantum circuits to find more efficient
  compilations with agentic AI*, arXiv:2610.23832. Library: kickmix (C++20 + Python, in Qualtran; kickmix 1.0.0 on PyPI
  since ~2026-10-28 with Linux/macOS/Windows wheels).

### 1.2 Evaluation — VERBATIM (Evaluation page, as quoted by nasir26 RULES.md, fetched 2026-10-27)

> Score = ( ∏_{b=1}^{3} cost_b^ref / cost_b )^{1/3}
>
> The reference submission (`sample_submission/`) "scores 1.0".
> Official metric notebook: https://www.kaggle.com/code/metric/google-quantum-ai-metric
> "Scoring takes roughly 45 minutes."

Per-task cost table (Evaluation page, verbatim):

| Task | Cost |
|:---|:---|
| `invsqrt` | Q × C, where C = Toffolis + T gates / 4 |
| `dqi` | R(ε₊) × Q² × T, where R(ε) = ln 2 / ( −ln( ½ + 2√ε ) ) |
| `dfthcsos` | λ_eff × T × Q, where λ_eff = √( E_gap ( 2Λ − E_gap ) ) |

> where Q is the qubit count and T the Toffoli count, both per shot. For `dqi`, ε₊ is an upper confidence bound on
> the decoder's failure rate. For `dfthcsos`, T and Q cover the whole block encoding, not just the submitted ANGLE
> circuits, and any ANGLE circuit wider than 128 qubits is rejected.

Submission format (Evaluation page, verbatim):

> You must submit a zip archive containing the following files:
>  - `invsqrt.kmb` or `invsqrt.kmx`
>  - `dqi.kmb` or `dqi.kmx`
>  - a folder named `dfthcsos` containing the circuits `angle_k_0`, `angle_k_1`, … `angle_k_<n-1>`, numbered from 0
>    with no gaps, each as `.kmb` or `.kmx`, plus `submission.npz` holding the factorization (`U`, `W`, `H2_I`, `H1_I`,
>    `Hsym_lower`) and the Givens tree (`tree_edges`).

Upload dialog: "Your submission should be named submission.zip." (several repos confirm the CLI returns HTTP 400 otherwise).

Independent corroboration of the same formulas: clduab11 field guide (re-read from the Evaluation page 2026-11-02),
zjukop3 ("read from the shipped verifiers"), ai4science README, wahyurahmaniar, harshulchess77-arch, the Gluzdov public
notebook. All agree. Note the Evaluation page states formulas **without constants**; the constants below come from the
verifier source and metric notebook.

### 1.3 What the Evaluation page omits (confirmed from verifier source / metric notebook — summary)

- **Q** = `circuit.num_qubits` (all declared qubits, not peak-live) for invsqrt and dqi; `Q_total` formula for dfthcsos.
- **T** = *mean* Toffoli-like gates (CCX, CCZ, CSWAP) executed per simulated shot; a gate conditioned on a measured
  bit counts only on shots where that bit is set (so measurement-based-uncompute fixups cost ~50%). Static count is only
  an upper bound (dqi reference executes 5,725,108.4 of a static 5,725,461).
- **invsqrt rotations**: Z_POW angles that are multiples of ½ half-turn are Clifford (free); multiples of ¼ cost 1 T;
  any other rotation costs `0.56·log2(1/ε) + 5.3` T, where ε is a *single circuit-wide* synthesis error
  `ε = π·min_margin/n_rot` (min over all shots of tol(x) − |error(x)|). Reference: 37 rotations at ε = 1.53e-12 → 27.3 T each.
  Tolerance 2^-24/√x turns; phase compared in units of 2^-64 turns. Unused precision margin buys cheaper rotations.
- **dqi ε₊**: one-sided Clopper–Pearson upper bound at δ = 2^-128 over N = 102,400 shots; k = 0 failures ⇒
  ε₊ = −expm1(ln δ / N) ≈ 8.66e-4 ⇒ **R = 1.19126 floor** that nobody can optimise away. Reject if ε₊ ≥ 1/16.
  Exchange rate (nasir26, matches forum): k=1 +0.46%, k=2 +0.85%, k=5 +1.83%, k=10 +3.17%, k=20 +5.33%, k=50 +10.25% of dqi cost.
  Error weight k ∈ {0..35} drawn ∝ w_k² (DQI principal eigenvector), mean weight ≈ 31 — not uniform.
  dqi forbids Z_POW. Registers exactly S0..S69 (12 qubits each) and E0..E4094 (12 classical bits each).
- **dfthcsos** (see §4 and `kaggle-raw/mirrors/official_verifiers_dfthcsos_SCORING_README.md`):
  `T_total = ANGLES Toffolis (forward + reverse, simulated) + outer_state_prep + inner_state_prep (heuristic
  SpinFreeData_V1, χ = 10) + 2(N−1)(2·brot−1)`; `Q_total = outer_persistent + inner_persistent + J·brot +
  max(outer_temp, inner_temp, angles_temp)`. Rejections: any ANGLE_k > 128 qubits; error_1 or error_2 > 20 mHa;
  not 0 < E_gap < 2Λ; Λ ≤ 49.0; E_gap ≤ 3.914898 Ha (both strict). E_upper = −22140.27335 Ha fixed. S, β₁ fixed to
  the baseline's (`fixed_shifts.npz`); submitted H1_I and Hsym_lower are ignored. No Z_POW. 64 shots per address.
- **Metric notebook** (`metric/google-quantum-ai-metric`, confirmed by nasir26): each leaderboard split has its own
  secret `seed_salt` (≥ 32 chars) and `baseline_cost` = the reference's cost *under that salt*; score per split =
  geomean of baseline_cost/cost; tasks verified in random order; **any failure on any split errors the whole
  submission**. Allowed instructions: X, CX, CCX, Z, CZ, CCZ, Z_POW, NEG, SWAP, CSWAP, R, HMR, BIT_INVERT, BIT_STORE0,
  BIT_STORE1, PUSH_CONDITION, POP_CONDITION, INFO_TAG, DEBUG_PRINT (DEBUG_PRINT ids still count toward num_qubits).
  Qubit/bit ids < 2^30/1536 = 699,050. Max registers: invsqrt 1; dqi 4,165; each ANGLE_k ≤ 128 qubits; every register named.
  `submission.npz`: format-1.0 .npy members, plain numeric little-endian dtypes, shapes U (R,B,76), W (R,B,C),
  H2_I (R,C), H1_I (), Hsym_lower (2926,), tree_edges (75,2) int; total ≤ 2^26 bytes. No links/special files in the zip
  (hard-linked files are rejected). File-level checks: exactly one `invsqrt.km[xb]`, one `dqi.km[xb]`, one `dfthcsos/`
  dir found by recursive search; shipping both .kmb and .kmx rejects the archive. Kaggle mount
  `/kaggle/input/competitions/<slug>/`; image `gcr.io/kaggle-images/python@sha256:81b1e7c4…`.
- **Reference (baseline) costs measured with the shipped verifiers at empty salt** (identical in nasir26, manwithacat
  hosted run, zjukop3, ai4science):

| Task | Q | Toffolis / shot | Other | Reference cost |
|---|---:|---:|---|---:|
| invsqrt | 260 | 7,735 | 1 T + 37 rotations → C = 7,987.59 | 2,076,774.233715282 |
| dqi | 1,893 | 5,725,108.38 mean (static 5,725,461) | ε₊ = 8.66e-4, R = 1.19126 | 24,439,463,583,672.93 |
| dfthcsos | 730 | 93,237 | λ_eff = 49.301369 (Λ = 308.456, E_gap = 3.96548) | 3,355,599,588.3155365 |

### 1.4 Timeline (consistent across Inzainos, harshul, clduab11, ai4science; all 23:59 UTC)

| Date | Event |
|---|---|
| 2026-10-22 | Start |
| 2026-11-20 | Mid-Competition Milestone Prize snapshot (highest public-LB score at that instant; **public notebook required**, kept public to the end). Kaggle page: "You must accept the competition rules before this date in order to compete." |
| 2027-01-04 | Longest Leader Prize window closes; qualifying notebooks and datasets must be public by then |
| 2027-01-13 | Entry deadline (accept rules) and team-merger deadline |
| 2027-01-20 | Final submission deadline |

(The "January 13" seen in Kaggle's social post is the *entry* deadline; the final deadline is 2027-01-20.)

### 1.5 Prizes (Inzainos table; totals corroborated by clduab11/landscape as "$150,000")

| Prize | Amount |
|---|---|
| 1st / 2nd / 3rd | $50,000 / $25,000 / $10,000 |
| 4th / 5th / 6th | $5,000 each |
| Mid-Competition Milestone (2026-11-20) | $10,000 |
| Longest Leader (window to 2027-01-04) | $10,000 |
| Single Task Performance (invsqrt, dqi, dfthcsos) | $10,000 each ($30,000) |
| "Additional Prizes" line in the Inzainos table | $50,000 (the leaderboard + milestone + longest-leader + single-task prizes sum to $150,000; treat this extra line as unverified) |

Rules attached to the extra prizes (Kaggle page wording via search snippet): "the winning notebooks or submissions
need to adhere to the same requirements and restrictions regarding licensing, reproducibility, and documentation as
the winning submission"; participants are encouraged to make notebooks public. Single-task prizes go to the best task
score among *selected* submissions, so the other two tasks must still pass (one failing task rejects the zip).

### 1.6 Code requirements / citation

- Not a code (kernel-only) competition (*Kernel Only: False*); upload `submission.zip` directly or from a notebook.
- Citation (VERBATIM, via Inzainos): "Tanuj Khattar, Nicholas Rubin, Craig Gidney, Michael Broughton, Guang Hao Low,
  Ryan Babbush, Sohier Dane, Brandon Horton, and María Cruz. Google Quantum AI - Verifiable Quantum Circuit Compilation.
  https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation, 2026. Kaggle."

---

## 2. Rules highlights (summary of nasir26 RULES.md §5–6, zjukop3 §6.4 citation, clduab11 §6)

- **Submissions: 5 per day**; up to **2 final submissions** selected.
- **Team size ≤ 5**; mergers allowed by the team leader subject to the combined submission-count cap; merger deadline 2027-01-13.
- **Winner licence: Apache 2.0** for the submission *and* the generating source code; winners must deliver reproducible
  code plus documentation of the compute environment (zjukop3 cites "Rules §6.4 (Open Source and Prize Obligations,
  B.5 / B.7 / C.6.b)").
- **Competition data**: licensed Apache 2.0 for use, but a "Data Security" clause: "You agree not to transmit, duplicate,
  publish, redistribute or otherwise provide or make available the Competition Data to any party not participating in
  the Competition." Several repos therefore gitignore the verifiers/kickmix.so/FeMoCo data.
- **No private sharing** of code/data outside your team; public forum/notebook sharing is fine.
- **External data/tools**: allowed if publicly available at no cost ("Reasonableness Standard"); AutoML/agents allowed
  with a valid licence. Public Kaggle notebooks default to Apache-2.0, and reuse of other participants' Apache-2.0
  circuits with attribution is widespread (and the subject of several discussion threads, see §5).
- Public vs private leaderboard: the metric notebook has per-split secret salts; the usual Kaggle banner "calculated
  with approximately 50% of the test data" appears on the leaderboard but is boilerplate — final scoring re-draws the
  verifier samples with a different secret salt.

---

## 3. Data page (summary; file list reconstructed from nasir26 and other repos — the Kaggle listing itself did not load)

Task contracts — VERBATIM (Data page, via nasir26):

> **invsqrt** — "Map |x⟩|0⟩ ↦ e^{2πi/√x}|x⟩|0⟩ for every x from 1 to 3,133,452, held in a 22-qubit register named `x`.
> Each input is tested 64 times, and every phase must be within 2^{-24}/√x turns. Cost: qubits × Toffoli-equivalents
> (Toffolis plus T gates / 4, with rotations priced in T gates)."
>
> **dqi** — "A reversible decoder for the Reed–Solomon code RS(4095, 4025) over GF(2^12). Given error syndromes in
> registers `S0` to `S69` and a classical record M in `E0` to `E4094`, it restores the syndromes and applies the phase
> (−1)^{Σ_j popcount(e_j ∧ M_j)} for the error e. It is tested on 102,400 shots; failures are allowed but raise the cost.
> Cost: R(ε₊) × Q² × T, with R a repetition factor that grows with the failure rate (paper Eq. (43))."
>
> **dfthcsos** — "Circuits that load the Givens-rotation angles of a factorized FeMoCo Hamiltonian, one batch of J angles
> per circuit, plus the factorization and rotation tree in `submission.npz`. A submission is rejected if any circuit
> uses more than 128 qubits, if the encoded Hamiltonian is more than 20 mHa from the reference, or if the LCU
> normalization Λ ≤ 49.0 or E_gap ≤ 3.914898 Ha. Cost: λ_eff × T_total × Q_total over the whole block encoding
> (paper Eq. (44)). The full contract is in verifiers/dfthcsos/SCORING_README.md."
>
> General: "A verifier simulates your circuit with kickmix on many inputs and checks every shot: inputs restored,
> scratch qubits back to |0⟩, and the right phase. Measurement-based uncomputation is allowed. Tests are seeded from
> your submission's hash plus a secret salt, so any change to a circuit gets fresh tests (paper §II.C)." The verifiers
> in `verifiers/` "are the authoritative specification".

Files (sizes from nasir26 NOTES and zjukop3; download needs login + accepted rules; total ≈ 3.7 GB incl. starter kit):

| Path | Description / size |
|---|---|
| `kickmix/kickmix.so` (+ Python package) | "The kickmix circuit simulator, kickmix.so, built for the Kaggle notebook image" — x86-64 Linux, CPython 3.13, glibc ≥ 2.34. (Now also `pip install kickmix==1.0.0`.) |
| `verifiers/invsqrt/verify_submission_invsqrt.py` (+ `nr_reference_circuit.py`) | invsqrt verifier and generator of the reference circuit |
| `verifiers/dqi/verify_submission_dqi.py` (+ `dqi_reference_circuit.py`) | dqi verifier; default 4 workers at ~6 GB RAM each for the reference (use `--max-workers 2` on 16 GB) |
| `verifiers/dfthcsos/verify.py`, `scoreinfra/`, `SCORING_README.md`, `example_submission/angle_k_reference_circuit.py`, `FeMoCo76o113e.fcidump` (128,128,348 B, SHA-256 e5a48af7…), `FeMoCo76o113e.fixed_shifts.npz` | dfthcsos verifier package (self-contained: numpy, scipy, kickmix) |
| `sample_submission/invsqrt.kmb` | ≈ 0.58 MB; reference circuit, Q = 260 |
| `sample_submission/dqi.kmb` | ≈ 886 MB (845 MiB, ~86 M operations); reference decoder, Q = 1,893 |
| `sample_submission/dfthcsos/angle_k_0..9.kmb` + `submission.npz` | 10 circuits ≈ 1.7–2.0 MB each (119 qubits, 3,974 Toffolis each); npz ≈ 4.5 MB; baseline (R,B,C) = (65,60,60), brot = 12, J = 8 |
| `README` (competition data) | declares the FCIDUMP SHA-256 |
| Separate dataset: `sohier/verifiable-circuit-compilation-starter-kit` ("Flash-THC"/dfthc-sos starter kit) | dfthc trainer, `build_circuits.py`, eight research example factorizations as NPZ |

Reference submission zip is 73,803,082 bytes (zjukop3). Maximum upload size is not stated on any page.

---

## 4. dfthcsos SCORING_README (official, Apache-2.0; full text in `kaggle-raw/mirrors/official_verifiers_dfthcsos_SCORING_README.md`)

Key VERBATIM lines:

> score = lambda_eff * T_total * Q_total                      (lower is better)
> lambda_eff = sqrt(E_gap * (2 Lambda - E_gap))               of the words the circuits load
> T_total    = ANGLES Toffolis                                Toffoli-like gates run per shot in kickmix (U_T and U_T^dagger)
>            + outer_state_prep() + inner_state_prep()        heuristic: SpinFreeData_V1 (incl. _dag)
>            + 2 * (N - 1) * (2 * brot - 1)                   heuristic: Givens rotations (U_T and U_T^dagger)
> Q_total    = outer_persistent + inner_persistent            persistent state-prep qubits (SpinFreeData_V1)
>            + J * brot                                       persistent angle-word registers
>            + max(outer_temp, inner_temp, angles_temp)       shared temporary workspace

Other points: `selection` register must be exactly ⌈log2(76 + R·B)⌉ qubits; one `word_j` register per word of width
`brot` ("this is how the circuits state their precision"); K = ⌈75/J⌉ circuits; ANGLE_k XORs batch_k ⊕ batch_{k−1};
pickles rejected; `submission_sha256` is over canonical .kmb bytes + npz arrays; grader salt is secret; the 128-qubit
cap applies to ANGLE circuits only. Baseline breakdown: ANGLES 79,480 Toffolis (85% of T_total), heuristic
846 + 9,461 + 3,450 = 13,757; Q = 186 persistent + 544 shared temp.

---

## 5. Leaderboard snapshots (public LB; Kaggle publishes no per-task scores)

| Read at (UTC) | Teams | Top scores | Source |
|---|---|---|---|
| 2026-10-26 | — | 21.10 / 20.18 / 19.55 | acco-cyber STATUS |
| 2026-10-27 00:32 | 1,171 | 23.352 / 22.886 / 22.805 / 22.698 / 21.755 | acco-cyber STATUS |
| 2026-10-28/29 | 1,501 (10-29) | top 26.14113 (Breaking1800, unchanged since 10-28 04:40); 25.53, 25.34; ranks 3–7 at 24.56–24.92; prize line (6th) 24.74 | nasir26 NOTES, clduab11 |
| 2026-10-30 | 1,696–1,729 | 26.76409 (Breaking1800); gold line (rank 13) 24.74; silver line (rank 84) 23.137; median 22.486 | manwithacat briefing 754174 via ai4science |
| **2026-10-31 06:45** | **1,756** | **26.76409, 26.56195, 26.26331, 26.07341, 25.94669, 25.31734, 25.27389, 25.06945, 25.00467, 24.96177** (top 10); 9 teams > 25; median 22.659; 75th pct 7.93; 90th pct 1.06; ~81 teams tied at 1.00000 (reference) | `kaggle-raw/mirrors/charleneleong-ai_ai4science_leaderboard-2026-10-31.json` — **all 1,756 scores**, names omitted |
| 2026-11-02 17:47 | 2,052 | leader 27.99617 (Breaking1800); 6th (last paid) 26.80320 | clduab11 field guide |
| undated, after 11-02 (search-engine cache) | 2,233 (one snippet) | 1 James & Geremie & Tony 28.82853 (57 entries); 2 Schrödinger's cat lived 28.07608 (47); 3 Breaking1800 27.99617 (20); … Thinking... 26.81091; Bingran You 26.80320; 7 田村さんを囲む会 26.67001 | Google/Bing snippets of the Kaggle leaderboard page |

Observations (ai4science, 2026-10-31): the field is **bimodal** — about half of all teams sit in a 0.6-wide band near
22.9–23.2 (assemblies of the best public Apache-2.0 circuits; the "public frontier" 23.14 is only rank ~374), then it
falls off a cliff; the leaders hold ~55% more total cost reduction than the public frontier (26.76/23.14 = 1.157 ⇒
1.157³ on the product of ratios). Public per-task frontier on 2026-10-30: invsqrt 62 qubits, cost 100,941 (20.57×);
dqi 888 qubits, 4.0334e11 (60.59×); dfthcsos 430 qubits, 3.3780e8 (9.93×) ⇒ blend 23.136. By 2026-11-03
wahyurahmaniar reports invsqrt 20.65×, dqi 63.35× (892 q), dfthcsos 10.57× ⇒ 24.0.

---

## 6. Discussion forum (titles from search-engine snapshots of the listing; thread bodies could not be opened)

Host announcements / pinned:
- **"How to get started + Competition's Official Discord"** — María Cruz (Kaggle host), pinned. Last comment ~12 days
  before the snapshot (Kishore Badyakar). Links the official Discord (invite not captured).
- **"[Update] kickmix is now on PyPI (Windows, Linux, and macOS wheels)"** — Tanuj Khattar (Google host), ~2026-10-28,
  15 votes. nasir26 notes: "kickmix will move to PyPI; metric will migrate to that copy. Watch for version skew between
  dataset `.so` and PyPI." PyPI confirms kickmix 1.0.0 (plus 0.1.dev0), homepage quantumlib/Qualtran.

Verifier / scoring clarifications and bugs (participant-authored; no host reply text captured):
- **"Final evaluation scope: published verifier or additional correctness checks?"** — Pizzaboi, ~2026-11-03/04,
  11 votes. Asks whether final scoring is exactly the published verifier. No answer visible in snippets. (zjukop3
  documents that the *metric notebook* adds file-level checks absent from the standalone verifiers — see §1.3.)
- **Topic 753230** — manwithacat: measurements showing `Circuit.reaction_depth()` materialises every op (≈135–170 B/op)
  and `_circuit_sha256` buffers the whole circuit (+1.4 GiB on a 55 M-op circuit), limiting verifiable circuit size
  on 16 GB machines; mirrored as Qualtran issues #1993 (open PR #1994) and #1987 (odinfree: a 3.31 GB / 363 M-op dqi
  circuit that passed locally was rejected by Kaggle with "Out of memory", burning one of five daily slots; no
  documented op-count/file-size limit; no maintainer reply as of 2026-11-04). Practical limit: Kaggle scoring ran a
  1.14 GiB / 130 M-op circuit fine.
- **Topic 753633** — chemistry bound: with the verifier's fixed S, β₁, **λ_eff ≥ 46.79 for any factorization**
  (public best ≈ 48.3–48.7), so chemistry gains must come from T × Q.
- **Topic 753185** (+ manwithacat) — Eckart–Young floor R·C ≥ 290 at 20 mHa; brot 7 and naive re-rounding fail;
  72.3% of a Berlekamp–Massey decoder's Toffolis are 42-AND GF(2^12) multiplies; invsqrt is precision-saturated
  (rotations cannot be cheapened); 63 → 62 qubit invsqrt step closed by manwithacat.
- **Topic 754174** — manwithacat's daily "briefings": leaderboard and per-task public-frontier snapshots (a
  Claude-driven research-ops agent). ai4science checked its implied reference costs: within 0.02%/0.006%/0.04% of the
  verifiers. Best public intel in the competition.
- dqi salt variance is widely discussed: one failing shot in 102,400 moves ε₊ from 8.6606e-4 to 9.1042e-4 and R
  from 1.19126 to 1.19673 (+0.459% dqi cost ≈ −0.035 overall points); the leaderboard re-draws, so local
  zero-failure runs are optimistic by ~0.46% on dqi.

Licensing / reuse of public circuits (hot topic):
- **Topics 753660 and 753740** — reuse of public Apache-2.0 circuits with attribution ("live threads on exactly this").
- **"Winner source-delivery requirements for public compiled inputs"** — Adem Vessell, 9 comments.
- **"Generator requirement: does a generator that transforms a pinned public Apache-2.0 circuit qualify?"** —
  Toluwalase Olufemi (~2026-11-04). clduab11's board concluded "the host's generator rule applies at prize time".
- **"Permission request: reuse of the QuantumAI DQI decoder"** — jday96314, 3 comments (the QuantumAI GitHub Schur
  decoder, rebuilt publicly by alexchilton, runs on a 42-AND GF(2^12) multiplier).

Strategy / community:
- **"Free introductory guide to FTQC circuit optimization for this competition"** — snuffkin (Hidemasa Tsukano's
  Japanese primer v1.0, 2026-11-02; CC BY 4.0 English adaptation), 12 comments.
- **"what to learn from this competition"** — hengck23, 17 comments ("learn to control AI better than others").
- **"How do you plan to win this game?"** — yoyobar, 16 comments (last by Jack).
- **"Grid search vs. exact trigonometry"** — Pablo Diego Pereira (~2026-11-04).
- A thread on AI-agent use; "The dataset is public now" style release threads accompany the public portfolios.

---

## 7. Code tab — public notebooks (titles/scores from search snapshots and repo provenance; two full texts captured)

| Notebook | Author | Public score / note |
|---|---|---|
| `heliosli/the-dataset-is-public-now-enjoy` ("The dataset is public now. Enjoy!") | heliosli | 24.54647 (V4); dataset "QCC circuits live"; earlier v10/v12/v28 portfolios 22.70–22.79 |
| "QCC \| Reproducible Circuit Portfolio" | — | 24.49359 |
| `ahmedberatozer/quantum-ai-df-thc-group-compression` | Ahmed Berat Özer | 23.91013 ("VQCC v20: verified three-task portfolio"; builds on heliosli's 2 Nov portfolio); also dataset `df-thc-group-compression-factorization` |
| `dmitriigluzdov/quantum-circuit-compilation-from-source` | Dmitrii Gluzdov | 23.87253, silver medal; **full text in `kaggle-raw/notebooks/`**: builds all three from source — invsqrt Q 78 / 1,696 Toffoli-eq; dqi Q 881 / 0.96 M Toffolis (in-place continued-fraction decoder); FeMoCo single-group (R,B,C) = (1,496,384), 572 addresses, Q 833, λ_eff 47.86; dataset `vqcc-femoco-public-factorization` (194 MB) |
| `manwithacat/kickmix-quickstart` | manwithacat (James Barlow) | utility: runs official verifiers with three simulators (official, kickmix-macos fork, Rust kickmix-engine) and checks bit-identical results; **full text captured**; plus `manwithacat/kickmix-tools`, datasets `kickmix-fork-wheels`, `kickmix-engine-wheels`, `vqcc-apache-public-circuits` (142 circuits with author manifests) |
| `manwithacat/vqcc-hedge-wizardry-notebook` | manwithacat | 888-qubit dqi (yoyobar's 889 → 888), cost 4.0199e11 |
| `manwithacat/dqi-classical-mask-projection-9-13909` | manwithacat | dqi classical-mask projection |
| `leotang09/vqcc-t7421-submission` | Leo Tang | 62-qubit invsqrt (yoyobar design + Özer patch), cost 100,692.6 |
| `isabe11am00re/qcc-v47-submission` | Isabe11aM00re | dfthcsos weights-only refit, λ_eff 48.2932, (8,143,60), brot 8, T 16,266, Q 430, cost 3.3778e8 |
| `somejoint/quantum-circuits-22-75-local-gm-897-qubit-dqi`, `somejoint/quantum-circuits-22-67-local-gm-full-xor-chem`, `somejoint/quantum-circuits-8-95-lb-cost-breakdown` | SomeJoint (Agniv Banerjee) | 897-qubit BM+Forney dqi decoder generator (Apache-2.0, embedded source); full-XOR chemistry (8,143,60) |
| `kirilltym/quantum-circuits-exact-gauge-5-word-qrom` | kirilltym | dfthcsos exact-gauge 5-word QROM (9.8366×); V22 portfolio 22.78244 |
| `marculera/df-thc-10x-compact-groups-from-the-hamiltonian` | marculera | C40 table (R,B,C) = (9,143,40), 1,363 rows → chemistry 10.25–10.57× |
| `busyaprime/...` ("LB 21.88210"), dataset `33-qcc-v8-members` | busyaprime | 63-qubit invsqrt lineage (20.23×) |
| `alexchilton/...` (v53 ≈ 22.78) | alexchilton | 889-qubit dqi 4.1478e11; rebuilt QuantumAI Schur decoder |
| `phucthaiv02/qcc-verified-portfolio-df-thc-retraining-study`, dataset `qcc-best-invsqrt-circuit` | Phuc Thai | invsqrt EXP-222/226a line, paired dqi extraction |
| `sumitchongder/notebook2f196e646b`, `rudrabhaskar/...`, `lightningv08` (Bezout–Schur) | — | signed-digit invsqrt, direct polynomial phasing, Bezout–Schur dqi |
| `dedquoc/quantum-circuit-synthesis-loop` | dedquoc | synthesis loop (no score in snippet) |
| `metric/google-quantum-ai-metric` | Kaggle (official) | **the official metric notebook** |

Lineage notes: public invsqrt progress is single-Toffoli surgery on one shared line (mrmeows/team selenium →
busyaprime → yoyobar 62-qubit → Özer −1 Toffoli); dqi public line is SomeJoint's decoder (897 → 889 → 888 → 892/893
variants); chemistry public line is the shared (8,143,60) word table with weight refits (λ_eff 48.29–48.76), which
sits at 99.999% of the 20 mHa cap and 1e-6 Ha above the E_gap floor — "tuning this shape is finished".

---

## 8. Facts that confirm, contradict or extend the caller's notes

- **Cost formulas confirmed exactly**: invsqrt = Q·(Toffoli + T/4); dqi = R(ε₊)·Q²·Toffoli with
  R(ε) = ln 2/(−ln(½ + 2√ε)); dfthcsos = λ_eff·Toffoli·Q with λ_eff = √(E_gap(2Λ − E_gap)). Final score = geometric
  mean of baseline/cost (reference = 1.0). **Additions**: Toffoli = simulated *mean* per shot (MBU-conditioned gates
  ~half price); invsqrt rotations priced 0.56·log2(1/ε) + 5.3 T with one circuit-wide ε (reference 27.3 T each);
  dqi R floor 1.19126 at zero failures (Clopper–Pearson, δ = 2^-128); dfthcsos T/Q include heuristic state-prep costs.
- **5 submissions/day confirmed** (metric `maxDailySubmissions`; also HTTP 400 unless named `submission.zip`);
  up to 2 final submissions; team size ≤ 5.
- **Deadline 2027-01-20 confirmed** (final); entry/merger 2027-01-13; **milestone 2026-11-20 confirmed** ($10k,
  needs a public notebook); longest-leader window ends 2027-01-04.
- **Prizes**: $150k = 50/25/10/5/5/5k + 10k milestone + 10k longest leader + 3 × 10k single-task.
- **Hard walls**: invsqrt zero failures over 200,540,928 shots; dqi ε₊ < 1/16; dfthcsos error ≤ 20 mHa, Λ > 49.0,
  E_gap > 3.914898 Ha (strict floors), ANGLE ≤ 128 qubits; any failing task (on any split) errors the whole submission.
- **Undocumented limits**: no stated op-count/file-size cap, but a 3.31 GB / 363 M-op dqi circuit failed with
  "Out of memory" on Kaggle (Qualtran #1987); qubit/bit ids < 699,050; npz ≤ 64 MiB; hard links rejected.
- **Leaderboard**: top 26.76 (10-31, 1,756 teams) → 27.996 (11-02, 2,052 teams) → 28.83 (latest cached, James &
  Geremie & Tony; 2,233 teams in one snippet); 6th place ≈ 26.8; public-assembly plateau ≈ 23–24.5.
