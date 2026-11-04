# FACTS — consolidated fact sheet for the VQCC competition

Google Quantum AI – Verifiable Quantum Circuit Compilation (Kaggle, `google-verifiable-quantum-circuit-compilation`).
Consolidated 2026-11-04 from the ten reports in this directory. Every fact carries its source report and section,
e.g. [kaggle-pages §1.3]. Source authority, highest first: **official verifier / metric source** (quoted in
[participants], [kaggle-pages]) > **companion paper** arXiv:2610.23832 v2 ([companion]) > **Kaggle rules mirror**
([kaggle-pages]) > **participant claims** > **inference** by a report author. Section 6 lists every disagreement found.

Report short names: [kaggle-pages], [companion], [kickmix], [qualtran], [participants], [papers], [ai-tricks]
(= ai-found-tricks.md), [deep-invsqrt], [deep-dqi], [deep-chem].

---

## 1. Competition rules and logistics

| Item | Fact | Source |
|---|---|---|
| Launch | 2026-10-22 (blog announcement 10-21). Hosts: Google Quantum AI + Kaggle; not kernel-only; medals awarded | [kaggle-pages §1.1] |
| Mid-competition milestone | 2026-11-20 23:59 UTC, $10,000 to the highest public-LB score at that instant; **public notebook required**, kept public to the end; rules must be accepted before this date | [kaggle-pages §1.4–1.5] |
| Longest-leader window | closes 2027-01-04; $10,000; qualifying notebooks/datasets public by then | [kaggle-pages §1.4] |
| Entry + team-merger deadline | 2027-01-13 (the "January 13" in Kaggle's social post) | [kaggle-pages §1.4] |
| **Final submission deadline** | **2027-01-20 23:59 UTC** | [kaggle-pages §1.4] |
| Prizes | 1st/2nd/3rd $50k/$25k/$10k; 4th–6th $5k each; milestone $10k; longest leader $10k; single-task (invsqrt, dqi, dfthcsos) $10k each. Total **$150,000** (companion paper); an extra "$50,000 additional" line in one mirror is unverified | [kaggle-pages §1.5], [companion §5] |
| Single-task prizes | best task score among *selected* submissions — the other two tasks must still pass (one failing task voids the zip) | [kaggle-pages §1.5] |
| Submissions | **5 per day**; up to **2 final** selections; team size ≤ 5; mergers subject to combined-count cap | [kaggle-pages §2] |
| Upload name | must be `submission.zip` (CLI returns HTTP 400 otherwise); scoring ≈ 45 min; identical bytes ⇒ identical score | [kaggle-pages §1.2], [participants §9] |
| Winner licence | Apache 2.0 for the submission **and** the generating source; reproducible code + compute-environment documentation; milestone/longest-leader/single-task winners have the same obligations. A "generator that transforms a pinned public circuit" is debated; "the host's generator rule applies at prize time" | [kaggle-pages §1.5, §2, §6] |
| Data redistribution | "You agree not to transmit, duplicate, publish, redistribute or otherwise provide or make available the Competition Data to any party not participating" — do not commit verifiers, `kickmix.so`, FCIDUMP, sample `.kmb` to public repos (several participants violate this) | [kaggle-pages §2], [participants §9.14] |
| External data/tools | allowed if publicly available at no cost; AutoML/agents allowed; public Kaggle notebooks default to Apache-2.0 and reuse with attribution is widespread | [kaggle-pages §2] |
| Zip layout | exactly one `invsqrt.km[xb]`, one `dqi.km[xb]`, one directory `dfthcsos/` (found by `rglob`, nesting tolerated, duplicates fatal, `__MACOSX` ignored) containing `angle_k_0 … angle_k_<K-1>` (contiguous from 0, each once, a stem present as both `.kmb` and `.kmx` fails) and exactly one `submission.npz` | [participants §3] |
| File checks | regular files only, `st_nlink == 1` (hard links rejected), no symlinks/special files, inside the extraction root; `.kmb` must really be binary (text saved as `.kmb` fails) | [participants §3, §9] |
| Instruction allow-list | `X, CX, CCX, Z, CZ, CCZ, Z_POW, NEG, SWAP, CSWAP, R, HMR, BIT_INVERT, BIT_STORE0, BIT_STORE1, PUSH_CONDITION, POP_CONDITION, INFO_TAG, DEBUG_PRINT`; anything else rejects. (`Z_POW` is additionally rejected by the dqi and dfthcsos verifiers — §3.) `DEBUG_PRINT` ids count toward Q | [participants §3], [kaggle-pages §1.3] |
| Id cap | every qubit/bit id `< 2**30 // 1536 = 699,050` | [participants §3] |
| Register caps | invsqrt: 1 register; dqi: n + m = 4,165; each ANGLE_k ≤ 128 qubits; **every register must be named** | [participants §3] |
| `submission.npz` | format-1.0 `.npy` members, plain little-endian numeric dtypes, no pickles; shapes `U (R,B,76)`, `W (R,B,C)`, `H2_I (R,C)`, `H1_I ()`, `Hsym_lower (2926,)`, `tree_edges (75,2)` int; decoded bytes ≤ 2^26 (64 MiB) | [participants §3] |
| Splits / salts | each leaderboard split (public, private) has a secret `seed_salt` (≥ 32 chars) and its own `baseline_cost` = reference cost under that salt; tasks verified in random order; **any verifier exception on any split voids the whole submission** and the message does not say which split | [participants §3] |
| Seeding | PRNG seed = SHA-256(canonical `.kmb` bytes) combined with the salt (Fiat–Shamir); any byte change re-rolls inputs/outcomes; no hidden test set | [companion §1.4], [participants §4–6] |
| Undocumented limits | no stated op-count/file-size cap, but a 3.31 GB / 363 M-op dqi circuit failed with "Out of memory" on Kaggle; a 1.14 GiB / 130 M-op circuit scored fine | [kaggle-pages §6, §8] |
| Environment | Kaggle image `gcr.io/kaggle-images/python@sha256:81b1e7c4…`; data at `/kaggle/input/competitions/<slug>/`; `kickmix.so` is CPython 3.13 / x86-64 / glibc ≥ 2.34 (dataset version "0.1"); `pip install kickmix==1.0.0` now exists and the metric will migrate to PyPI — watch version skew | [participants §2–3], [kaggle-pages §6] |
| Verifier resources | dqi: 4 workers × ~6 GB RAM for the reference (`--max-workers 2` on 16 GB); `reaction_depth()` can OOM; invsqrt reference ≈ 726 s on 4 vCPU | [participants §4–5, §9] |

Key official file hashes (to confirm you hold the real thing): `verify_submission_invsqrt.py` `ddef520d…`,
`verify_submission_dqi.py` `f14274bc…`, `dfthcsos/verify.py` `0775be7a…`, metric notebook v10 `e7c5bfaf…`,
FCIDUMP `e5a48af7…`, `kickmix.so` `c66b3216…` [participants §0, §2].

---

## 2. Scoring, exactly

### 2.1 Overall metric

`Score = (∏_{b∈{invsqrt,dqi,dfthcsos}} baseline_cost_b / cost_b)^{1/3}` per split; reference submission scores 1.0
[kaggle-pages §1.2], [participants §3]. The baseline costs below are measured with the shipped verifiers at empty
salt; on Kaggle each split uses the reference's cost under its own salt (dqi differs in the 7th significant digit).

| Task | Q | Toffolis / shot (mean) | Other | **Reference cost** |
|---|---:|---:|---|---:|
| invsqrt | 260 | 7,735 (3,874 fwd + 3,861 rev) | 1 T + 37 rotations at 27.28 T → C = 7,987.593 | **2,076,774.233715282** |
| dqi | 1,893 | 5,725,108.4 (static 5,725,461) | k = 0, ε⁺ = 8.6606e-4, R = 1.1912605 | **24,439,463,583,672.93** (empty salt) |
| dfthcsos | 730 | 93,237 | λ_eff = 49.301369 (Λ = 308.456, E_gap = 3.965477) | **3,355,599,588.3155365** |

Sources: [kaggle-pages §1.3], [participants §0, §4–6].

### 2.2 How Toffolis and qubits are counted (all three tasks)

* **T = mean executed Toffoli-like gates per shot**: `CCX`, `CCZ`, `CSWAP` and their `if b` variants, counted by
  `km.Simulator(counting_operations=True)` only on shots where the condition holds. Measurement-conditioned fix-ups
  (`CCZ … if b` after an `HMR`) therefore cost ≈ ½ on average; `del_and`/`del_lookup` cost 0 Toffolis. Static
  `operation_statistics()` is only an upper bound [participants §4–6, §9], [kaggle-pages §1.3].
* **Q = `circuit.num_qubits` = max qubit id + 1** — no liveness analysis; freed high ids still count; ids used only in
  `APPEND_TO_REGISTER` or `DEBUG_PRINT` count [kickmix §3, §6], [participants §9.1].
* A `Z_POW` never counts as a Toffoli; CSWAP under a *classical* bit (`SWAP a b if b`) is free [kickmix §3].

### 2.3 invsqrt: `cost = Q × C`, `C = T_tof + T_T / 4`

From the verifier source [participants §4] and [companion §2.2]:

* Instance: `n_p = 10`, register `x` of 22 qubits, `x ∈ [1, 3(2^10−2)^2] = [1, 3,133,452]`, β = 1, `precision_bits = 24`,
  64 shots per x ⇒ **200,540,928 shots**, **zero failures allowed**.
* Target phase: `r = isqrt(2^130 / x)`, `target = (r+1)>>1` in units of 2^-64 turn (= 1/√x turns);
  `tol(x) = min(r >> 25, 2^63)` units = **2^-24/√x turns** (relative 2^-24). tol(1) = 2^-24 turns, tol(x_max) = 3.37e-11 = 2^-34.8 turns.
* Per shot: `x` restored, every other qubit `< num_qubits` is |0⟩, `|θ − target| ≤ tol`. Tracks `min_margin = min(tol − |error|)`.
* `T_tof` = mean executed Toffoli-like; `t_base` = mean count of T-angle `Z_POW` (odd multiple of ¼ half-turn, hierarchy level 3);
  `n_rot` = mean count of `Z_POW` with level ≥ 4; Clifford angles (multiples of ½ half-turn) are free.
* **Rotation price**: `ε = π · min_margin(turns) / n_rot` (fail if ≤ 0); each rotation costs `0.56·log2(1/ε) + 5.3` T
  (Kliuchnikov et al. 2203.10064 mixed-fallback synthesis). `T_T = t_base + n_rot·(0.56·log2(1/ε)+5.3)`; `C = T_tof + T_T/4`;
  `cost = num_qubits × C`. One circuit-wide ε: the single worst shot sets the price of every rotation.
* Reference: ε = 1.5289e-12 → 27.28 T per rotation; 37 rotations ⇒ 252.6 Toffoli-eq (3.2 % of C); min margin ≈ 1.8e-11 turns;
  worst error 0.477 of tolerance at x = 2,588,411 (2^-25.07 relative) [participants §4], [deep-invsqrt §0].

### 2.4 dqi: `cost = R(ε⁺) × Q² × T`

From the verifier source [participants §5] and [companion §3.4], [deep-dqi §1]:

* Instance `(m, n, b, r) = (4095, 70, 12, 2016)`, `r = (2^12 − isqrt(2^12))//2`, ℓ = 35; field `GF2Field(12)` with modulus
  **4179** (x¹²+x⁶+x⁴+x+1), little-endian polynomial basis, primitive element 2; `s_i = Σ_j e_j α^{(i+1)j}`, i = 0..69.
* Registers **exactly** `S0..S69` (12 `km.q` each, disjoint) and `E0..E4094` (12 classical bits each); any other qubit is
  ancilla that must end at |0⟩. **`Z_POW` anywhere ⇒ `ValueError`** .
* Shots: `N = 102,400` (400 batches × 256). Error weight `w ~ v_w²`, v = principal eigenvector of the (ℓ+1)×(ℓ+1) tridiagonal
  `A[k,k] = k(q−2r)/√(r(q−r))`, `A[k−1,k] = √(k(m−k+1))` (Jordan et al. Lemma 9.2): **E[w] = 31.05**, P(w=35) = 2.8 %,
  P(w ≤ 20) = 5.5e-5, P(w ≤ 16) = 1.6e-7 [deep-dqi §1.5]. Positions uniform without replacement, values uniform in F_q*,
  mask `M_j` uniform over all 4,095 positions. Expected phase = parity of Σ_j popcount(v_j ∧ M_j).
* Failure = `S` changed OR any ancilla ≠ 0 (value error) OR wrong phase. k failures ⇒ **ε⁺ = one-sided Clopper–Pearson
  upper bound at δ = 2^-128** (k = 0: `−expm1(ln δ / N)`; else 64-step bisection on the log binomial tail). Reject if ε⁺ ≥ 1/16.
* `R(ε) = ln 2 / (−ln(½ + 2√ε))` (R(0) = 1; origin: companion-paper derivation — trace distance ≤ 2√ε ⇒ single-run success
  ≥ ½ − 2√ε ⇒ repetition overhead; **not** the Nature paper's imperfect-decoding theorem) [deep-dqi §0, §1.4].
* `cost = R · num_qubits² · mean_toffoli`. Quoted: R(1e-5, 1e-4, 1e-3, 1e-2) = 1.02, 1.06, 1.21, 1.94.

| k failures | ε⁺ | R | penalty |
|---:|---:|---:|---:|
| 0 | 8.6606e-4 | **1.19126** (floor for every submission) | — |
| 1 | 9.1042e-4 | 1.19673 | +0.46 % |
| 2 | 9.488e-4 | 1.2014 | +0.85 % |
| 5 | 1.048e-3 | 1.2131 | +1.83 % |
| 10 | 1.188e-3 | 1.2290 | +3.17 % |
| 20 | 1.427e-3 | 1.2548 | +5.33 % |
| 50 | 2.022e-3 | 1.3134 | +10.3 % |
| 100 | 2.865e-3 | 1.3887 | +16.6 % |
| ≈6,400 | ≥ 1/16 | ∞ | rejected |

[deep-dqi §1.5], [companion §3.4] (recomputed, all agree). Rule of thumb: a shortcut with failure probability ε_s costs
≈ 102,400·ε_s shots; 1e-4 must save > 3.2 % of Q²T, 1e-3 must save > 16.6 %. One failing shot ≈ −0.15 % overall score
≈ −0.037 points at 24; the public-LB salt re-draws, so a locally zero-failure circuit is optimistic by ~0.46 % on dqi.

### 2.5 dfthcsos: `cost = λ_eff × T_total × Q_total`

From `SCORING_README.md` and `verify.py` [kaggle-pages §4], [participants §6], [deep-chem §1]:

```
λ_eff   = sqrt( E_gap · (2Λ − E_gap) )                       computed from the DECODED angle words
Λ       = Σ_j |λ_j(h1')|  +  ¼ Σ_{ρc} ( |w_B^{ρc}| + Σ_b |w_b^{ρc}| )²,   w_B = W + Σ_b w_b
E_SOS   = ecore − η·β₁ − (Σ|λ_j| − Σλ_j) − ½ Σ_{ρc} W²       (verifier form)
E_gap   = E_upper − E_SOS,   E_upper = −22140.27335 Ha (fixed)
T_total = ANGLES Toffolis (mean over shots, forward + reverse passes, all K circuits)
        + outer_state_prep() + inner_state_prep()            heuristic SpinFreeData_V1(R,B,C,N=76,χ=10,β=brot)
        + 2·(N−1)·(2·brot − 1)                               Givens rotations, N−1 = 75 edges, both directions
Q_total = outer_persistent + inner_persistent + J·brot + max(outer_temp, inner_temp, angles_temp)
angles_temp = max_k num_qubits(ANGLE_k) − selection_width − J·brot
```

* Gates (strict): `error_1 = ‖h̃1' − h1'‖_F ≤ 0.020 Ha`, `error_2 = ‖Σ X⊗X − h2 − (S⊗I + I⊗S)/2‖_F ≤ 0.020 Ha`,
  `Λ > 49.0`, `E_gap > 3.914898` (difference between supplied DMRG and SOS-SDP energies), `0 < E_gap ≤ 2Λ`, any
  ANGLE_k > 128 qubits rejected (128 allowed); values are not clamped; failure ⇒ infinite score.
* `S` and `β₁` are **fixed to the baseline's** (`FeMoCo76o113e.fixed_shifts.npz`); submitted `H1_I`, `Hsym_lower` are
  ignored; `U` is used only for its shape (vectors are re-decoded from the circuits). Two-electron integrals are stored
  as float32 ("the score depends on this rounding").
* Baseline worked example: (R,B,C) = (65,60,60), L = 76 + 3,900 = 3,976 addresses, brot = 12, J = 8, K = 10 plain
  unary-iteration QROMs of 119 qubits / 3,974 Toffolis ⇒ ANGLES 79,480 (85 %); outer 846 + inner 9,461 + Givens 3,450 = 13,757;
  Q = 186 persistent (90 + 96) + 544 shared temp = 730; error_1 3.19 mHa, error_2 18.64 mHa; λ_eff 49.301369 (unrounded
  words 49.254686); 254,464 shots; ≈ 25 s.
* At brot = 16 the heuristic is 846 + 9,461 + 4,650 with 1,087 temp qubits (the inner temp scales with brot).
* Sensitivities at the baseline: dλ_eff/dE_gap = 6.2 per Ha, dλ_eff/dΛ = 0.08 per Ha; with E_gap pinned at the floor,
  **λ_eff ≈ 2.8·√Λ** (Λ 300 → 48.3, 200 → 39.3, 120 → 30.3, 49 → 19.19) [deep-chem §0].

---

## 3. Per-benchmark contracts, references, frontiers, levers

### 3.1 Benchmark I — invsqrt

**Contract** [companion §2.2], [participants §4]

| Item | Value |
|---|---|
| Map | `|x⟩|0⟩ → e^{2πi/√x} |x⟩|0⟩` for every integer x ∈ [1, 3,133,452] |
| Registers | exactly one named quantum register `x`, 22 distinct qubits; everything else unnamed scratch returned to |0⟩ |
| Tolerance | 2^-24/√x turns, per x; phase compared in 2^-64-turn units against exact `isqrt(2^130/x)` |
| Shots | 64 per x, 200,540,928 total; k = 0 (one failing shot fails the task) |
| Allowed | `Z_POW` yes (it is the only way to phase); every HMR must be fixed up |
| Cost | Q × (T_tof + T_T/4), rotation price §2.3 |

**Reference construction** (QROM-seeded cubic + one Newton step) [companion §2.3], [participants §4], [deep-invsqrt §0]

| Stage (forward) | Toffoli | Note |
|---|---:|---|
| normalise (count leading zero *pairs* into 10 unary flags, CSWAP lane rotations) | 120 (110 rev) | x_norm ∈ [1,4) |
| QROM 4 cubic pieces + Δx bit | 3 | coefficients a/b of Rubin et al., 17 bits |
| Horner (3 truncated 14×17-bit multiplies) | 1,071 | in place over coefficient registers |
| y₀² (28 bit) | 442 | |
| z = x_norm·y₀² (22×28→30) | 1,043 | |
| 3 − z | 28 | |
| p = y₀·z (17×30→30) | 867 | |
| denormalise p ≪ s (30·n_p CSWAP) | 300 | |
| phase: 40 Z_POW on y₁ (2 Clifford, 1 T, 37 rotations) | 0 (≈253 Tof-eq) | F = 40 fractional bits |
| **forward / reverse / total** | **3,874 / 3,861 / 7,735** | Q = 260 (231 named + 29 adder ancillas) |

Multiplications are 88.5 % of Toffolis; the mirror uncompute is a full second copy; worst error 0.477 of tolerance.

**Public frontier** (official-verifier numbers) [participants §7.1], [kaggle-pages §7]

| Circuit | Q | mean T (static) | rot | cost | × |
|---|---:|---:|---:|---:|---:|
| Gluzdov 84 q (signed-digit quadratic) | 84 | 1,553 | 44 | 156,883 | 13.24 |
| mrmeows 63 q | 63 | 1,348.5 (1,416) | 41 | 103,546 | 20.06 |
| busyaprime 63 q | 63 | 1,329.5 (1,397) | 41 | 102,349 | 20.29 |
| yoyobar 62 q (+Özer patch) | 62 | 1,327.48 (1,497) | 41 | 100,693 | 20.63 |
| **Ehan Mallick 62 q (two 3-to-2 AND merges)** | **62** | **1,325.48** | 41 | **100,568.5** | **20.65** |

Architecture: normalise to mantissa M ∈ [1,2) with one-bit shift stages (flags give exponent parity e and shift s);
**256-entry coefficient QROM addressed by (e, 7 high mantissa bits)** holding a *centred quadratic* `y = K0 − R·δ`,
`R = K1 − C2·δ` with **signed-digit offset δ** so every Horner row is a plain add/subtract; derivative split
(residual + coarse bits), high part phased early and erased by HMR with one merged ANF phase repair, virtual lowest
accumulator bit, exact-domain affine Toffoli/CSWAP rewrites (gates with fixed outcome on every legal input become
Clifford), LP-calibrated rotation angles. 62 q = 22 (x) + 40 working; at most 34 of the 40 hold a 1 at any instant.
Rotations: 41 × 28.77 T ≈ 295 of C ≈ 1,620 (ε ≈ 2.4e-13); **angles are LP-optimal, no rotation can be dropped**, worst
error 0.99932 of tolerance (x = 161) — "precision-saturated". No closed source-to-circuit build exists publicly for the
63/62 q line (frozen checkpoints); a from-source generator is itself valuable and required for prizes [participants §7.1, §10].

**Best published research design**: Gu et al. 2610.22367 Coulomb 1/√d² (different spec: 8-bit coords, 25-bit accumulator,
2e-6 *absolute* error): 128 dyadic *lines*, ≤ 6 controlled additions, MBU unlookup 17 Toffolis instead of 126, direct
accumulation, backward-fitted integer coefficients: **1,140 T / 142 Q** vs HRS baseline 6,355 / 252 [ai-tricks §1.4.3],
[papers §A.2]. HHL arcsin (21-bit in / 33-bit out, closer to our widths): 345 dyadic quadratic leaves, 1,348 T / 115 Q.

**Levers and estimated gains** [deep-invsqrt §18], [ai-tricks §5.1], [companion §9.1]

| Lever | Status / estimate |
|---|---|
| Drop Newton; fine dyadic table + quadratic (256 leaves: 2^-27.7 approx. error) | **done by the public frontier** (260/7,988 → 62/1,620); design model ≈ 2,300–2,600 Tof-eq at 115–130 q from scratch |
| Backward fitting of integer coefficients through the exact truncated pipeline + exhaustive 3.1 M-input check | the right method for k = 0; frontier's "LP-calibrated angles" is the same idea |
| Booth radix-4 rows, per-row truncation schedule, carry-mode dial under a live-qubit cap | transferable from Gu; ~45 % fewer rows per multiply |
| Binary (not unary) leading-zero count; barrel shift ≈ 120 vs 300 CSWAP per direction | zjukop3: 260 → 231 q, 7,735 → 6,852 T on the reference; ~90 T saving per direction on the frontier design |
| Qubit cuts (each qubit at Q = 62 ≈ 21–31 Tof-eq) | remaining lever; payload alone is ~61 wires in the 84 q port |
| Rotation cost | **closed**: doubling the margin saves ~10 Tof-eq; no rotation can be removed |
| Phase gradient, Hamming-weight phasing, windowed multipliers, Karatsuba | net negative or irrelevant at these widths |

### 3.2 Benchmark II — dqi

**Contract** [companion §3.1–3.2], [participants §5], [deep-dqi §1]

| Item | Value |
|---|---|
| Map | `U_c |s⟩|0⟩_W = (−1)^{c·bin(e(s))} |s⟩|0⟩_W`, s = Bᵀe(s), wt(e) ≤ 35; "may recover symbols one at a time or compute the parity directly" |
| Registers | `S0..S69` (12 qubits each = 840) quantum; `E0..E4094` (12 bits each = 49,140) classical, per-shot input; all other qubits ancilla → |0⟩ |
| Code | dual RS [4095, 4025, 71] over GF(2^12), ℓ = 35; field poly 4179; points α^j |
| Shots | 102,400 from the DQI weight law (§2.4); failures allowed, priced by R(ε⁺) |
| Allowed | **no `Z_POW`**; conditioned Z/CZ/CCZ on classical bits free |
| Cost | R(ε⁺)·Q²·T; **Q enters squared** (1 % fewer qubits ≈ 2 % fewer Toffolis); hard floor Q ≥ 840 |

**Reference decoder** (Proos–Zalka synchronised EEA + Chien/Forney) [companion §3.3], [participants §5], [deep-dqi §9]

| Component | Value |
|---|---|
| Key equation | EEA on (z^70, S(z)) until deg r < 35; `3(n+1)+9 = 222` synchronised cycles, each running every sub-step under one-hot controls; five 8-qubit degree pointers |
| Storage | two arrays of 73 slots × 12 qubits (syndrome reused in the first): Q = 840 S + 876 reg_b + 36 pad + 40 pointers + 11 control + 90 peak temp = **1,893** |
| Field ops | add/square/const-multiply/Frobenius = CNOT (free); quantum×quantum product = **63-Toffoli Karatsuba** (`init_gf2_mul`); controlled product 75; inversion = Itoh–Tsujii **315 T + 48 scaffold qubits**; products whose factors survive erased by X-measure + conditioned CZ (0 T) |
| Chien/Forney | all 4,095 positions, 351 T each (inversion 315 + zero test/copies 36) = 1,437,345 T = 25 % (inversions 22.5 %); one Forney step skipped per shot on average (P(E_j = 0) = 1/4096) ⇒ mean 5,725,108 vs static 5,725,461 |
| Anatomy | EEA sweep 50 % of T, Chien/Forney 25 %, shift_b 8.3 %, swap_a_and_b 6.9 %; polynomial storage 92.5 % of Q |
| Score | 1.19126 × 1893² × 5,725,108 = 2.444e13 |

Khattar et al. 2510.10967 Table VI: whole DQI circuit (4095,70,12,2016) = 5,717,729 T / 1,885 q with a 51-Toffoli
multiplier; the decoder part ≈ 5.1–5.2 M. Gu's re-run of that code: 5,125,070 T / 1,938 peak q [deep-dqi §3.6], [ai-tricks §1.4.1].

**Public frontier** [participants §7.2]

| Circuit | Q | mean T | failures | cost | × |
|---|---:|---:|---|---:|---:|
| clduab11 BM+Forney port (Gu design) | 1,789 | 445,229 | 3–8 | — | 14.0–14.2 |
| Özer v8 Bézout–Schur | 883 | 519,152 | 8 | 4.950e11 | 49.4 |
| SomeJoint 897 | 897 | 440,633 | 0 | 4.2235e11 | 57.9 |
| yoyobar 889 | 889 | 427,475 | 0 (1 in 1 of 12 salts) | 4.0246e11 | 60.7 |
| ahoirg/yoyobar 893 | 893 | 407,444 | 0 (1 at one salt) | 3.8706e11 | 63.1 |
| wahyurahmaniar 892 | 892 | 407,005 | 0 local, **2 on Kaggle** | 3.8578e11 | 63.35 |
| **manwithacat HW-06 892** | **892** | **403,587** | 0 | **3.8254e11** | **63.9** |

Design (SomeJoint "q18"/Schur lineage, [participants §7.2], [deep-dqi §10.3]): the 70 syndrome words are rewritten
**in place** as partial quotients of the continued fraction of S(z) ("almost no workspace beyond its 840 input qubits"),
converted in place to (σ, Ω), Chien/Forney sweep under the record bits, everything reversed. Stages: mask_projection,
initial, extract (87,040 T), synthesis (44,654), convert_lookahead (69,220), scan (44,275), unconvert (70,342),
unsynthesis (53,803), unextract (117,997). **Classical mask projection**: 70 classical field words solved from a
Vandermonde system absorb the record at positions 0–69 into a syndrome-linear phase so the sweep skips them.
**Rank-42 GF(2^12) multiplier** (evaluation/interpolation over GF(8), 7 points incl. ∞; flip-graph search found no
rank-41) plus a 99-rank GF(2^24) product and a tower-norm inverse; 53.4 M of 60 M ops are CX. Approximations: missing
leading coefficient repaired by a paired 3+1 step; histories with ≤ 2 gaps exact; deliberately wrong at w ≤ 16
(P ≈ 1.6e-7 per shot). Pole flags `P_g = 1` iff w odd and w ≤ 2g−1; width peak only in `unextract`; measuring P6 and
recomputing (23 T + CZ) gave 893 → 892. Each qubit at 892 ≈ 0.22 % of cost ≈ 6 failing shots ≈ 2.7 % of T.

**Best published research design**: Gu et al. [ai-tricks §1.4.1], [deep-dqi §4]: **442,397 T / 1,837 Q**, 7 wrong signs
in 1e5 (aggregate failure 1.4e-4). Phase table: BM 141,071 (31.9 %), monicize 2×1,583, ω in place 2×15,246, half-degree
Euclid for Ψ 2×44,470, sweep 4,024 × 23 = 92,552, reverse 86,176. Tricks: Berlekamp–Massey on one shared path via
rescaling (replace/retain), invariant σ₀δ = 1 (no discrepancy register), one-entry 19-qubit stack (overflow 1e-4),
per-round coefficient windows (3.8e-5), tie → replace, in-place evaluator ω over S₁..S₃₅ (zeroes S₃₆..S₇₀ as workspace),
phase-only Forney via trace `Tr(ν_j ω(β_j) Ψ(β_j))` with **Ψ ≡ 1/σ' mod σ precomputed once** by a half-degree EEA
(σ = E² + zO², σ' = O²), syndrome-linear mask part applied with free Z gates (71 positions dropped), 42-T multiplier,
66-T tower-norm inversion. Under the competition metric this circuit scores ≈ 1.8e12 (≈ 13–14×) because Q = 1,837 is
2.2× the floor and Q is squared — **transfer components, not the architecture**.

**Levers** [deep-dqi §10], [ai-tricks §5.2]

| Lever | Estimate |
|---|---|
| Work in place in the 840 syndrome qubits (Q 1,893 → ~890) | ×4.5 alone; the frontier is at 892; remaining room ≈ 5 % of Q (→ 850–870), each qubit 0.22 % |
| Key-equation solve: synchronised EEA (≈4.3 M incl. reverse) → BM/continued fraction (≈280–440 k incl. reverse) | ×10 on the stage; done by the frontier |
| Phase-only recovery with precomputed Ψ: 351 → 23 T/position (11 zero-test + 12 bilinear) | 1.44 M → 93 k + 2 × 44 k; 23/position is essentially tight |
| Multiplier 63 → 51 → 42; inversion 315 → 255 → 66 (tower) | −33 % on every quantum×quantum product; frontier has rank 42 |
| Failure budget only on ≤ 1e-4 events (stack depth, windows, 2+ gap patterns ≈ 3.5e-5); never reduce ℓ (ℓ = 34 ⇒ ε = 2.8 %, R ≈ 3.9) | ≤ 3 % cost |
| Borrowed-wire 3-ANDs via HMR + CCZ; measure-and-recompute flags | −12 T uncomputes, −1 q each (done in HW-06) |
| Hypothetical near-floor design Q = 852, T = 250 k, 10 failures | ≈ 2.2e11 ⇒ ≈ 110× |

### 3.3 Benchmark III — dfthcsos

**Contract** [companion §4.3–4.6], [participants §6], [deep-chem §1.4]

| Item | Value |
|---|---|
| Submission | `K = ⌈75/J⌉` circuits `angle_k_0..K−1` + `submission.npz` (U, W, H2_I, H1_I, Hsym_lower, tree_edges) |
| Registers (identical in every circuit) | `selection` of **exactly** `(76 + R·B − 1).bit_length()` qubits (extra bits rejected); `word_0..word_{J−1}` all of width `brot` (this declares brot); all other qubits workspace starting/ending at |0⟩; other `word_*` names rejected |
| Action | `ANGLE_k: |a⟩|z⟩ → |a⟩|z ⊕ Δ[k,a]⟩`, Δ[0] = batch[0], Δ[k] = batch[k] ⊕ batch[k−1]; batch label hard-wired; words beyond index 74 must be zero |
| Word encoding | `θ/π = word / 2^(brot−1)` ∈ [0, 2); vectors rebuilt on `tree_edges` (rooted at 0, parent before child): `u_c ← u_p sin θ`, `u_p ← u_p cos θ`; rows 0..75 = one-body eigenvectors of h1', rows 76.. = u_b^(ρ) in (ρ,b) order |
| Verification | one simulator, batch = L·64 shots; forward through k = 0..K−1 (phase unflipped, selection unchanged, workspace zero, J words **identical across the 64 shots of an address**), then reverse (each must restore batch k−1, k = 0 clears) |
| Allowed | **no `Z_POW`** (any line starting with `Z_POW` rejected); HMR + conditioned CZ fine; each circuit ≤ 128 qubits |
| Cost | λ_eff · T_total · Q_total (§2.5); Q_total uncapped |
| Fixed | S, β₁ (baseline's), E_upper, χ = 10, N = 76, η = 113; Outer/Inner/Givens are black-box heuristics |

Because the same gate list runs forward and backward and must map batch_{k−1} → batch_k and back, ANGLE_k must be a
genuine XOR oracle; Berry-style measurement-based *unlookup* cannot replace the reverse pass (MBU is fine for internal
ancillae) [deep-chem §1.4]. Warning: the shared public loaders fail an arbitrary-target XOR audit yet pass the official
verifier (which only drives the contract sequence); a private salt changes only HMR branches so this is not a LB risk,
but they are not true XOR oracles [participants §7.3].

**Reference**: log-depth tree, (65,60,60), brot 12, J 8, K 10 ordinary segment-tree unary-iteration QROMs
(`_break_early` on identical subtrees, ≤ L−2 Toffolis), 119 qubits / 3,974 T each; totals in §2.5 [participants §6].

**Public frontier** [participants §7.3], [kaggle-pages §5, §7]

| Factor / loaders | (R,B,C), rows L | brot, J, K | λ_eff | T | Q | cost | × |
|---|---|---|---:|---:|---:|---:|---:|
| reference | (65,60,60), 3,976 | 12, 8, 10 | 49.301 | 93,237 | 730 | 3.356e9 | 1.00 |
| Gluzdov v8 (THC-like) | (1,496,384), 572 | 11, 10, 8 | 47.856 | 20,286 | 833 | 8.087e8 | 4.15 |
| SomeJoint full-XOR | (8,143,60), 1,220 | 8, 5, 15 | 48.561 | 16,528 | 430 | 3.451e8 | 9.72 |
| heliosli 10-30 | (8,143,60) | 8, 5, 15 | 48.324 | 16,266 | 430 | 3.380e8 | 9.93 |
| marculera C40 + public loaders | (9,143,40), 1,363 | 8, 5, 15 | 47.097 | 16,237 | 428 | 3.273e8 | 10.25 |
| **C40 + wahyurahmaniar paired-product loaders** | (9,143,40) | 8, 5, 15 | **47.097** | **15,747** | **428** | **3.174e8** | **10.57** |

At J = 5, brot = 8, (8,143,60): heuristic = 369 + 5,311 + 2,250 = 7,930 T; 86 persistent + 304 temp qubits;
Q = 86 + 40 + 304 = 430 regardless of ANGLE workspace (ANGLE temp ≤ 77 < 304) ⇒ **ANGLE workspace up to the 128 cap is
free**; ANGLE Toffolis ≈ 4,200–4,750 per pass (52–58 % of T). Every top factor pins all gates: error_1 ≈ error_2 ≈
19.999 mHa, E_gap = 3.914899–3.914902, Λ ≈ 290–306. Loaders: each output bit an ANF polynomial of the 11 address bits,
7 high / 4 low split, cached high monomials (78 T), low monomials in a slot cache (11 T) erased by HMR+CZ, mixed terms
paired so one Toffoli covers two products via `(h1⊕l2)(h2⊕l1)`; 294–318 T per circuit at exactly 128 qubits.
Rounding: naive 11-bit re-rounding of the reference words gives error_1 = 221 mHa; shipped words are rounding-aware;
brot 7 fails; nasir26 model `error_2² = e0² + r²·4^(12−brot)`, e0 ≈ 16.0, r ≈ 9.7 mHa. Eckart–Young floor R·C ≥ 290 at
20 mHa. Nuclear-norm re-representation saves only 4.2 %; GPU refits of 65/60/60 failed; weights-only refits stay at Λ ≈ 300.

**Best published research design**: Low et al. 2502.15882 FeMoCo-76 (R,B,C) = (15,57,19): Λ = 179.73, E_gap = 5.382,
λ_eff = 43.65, C_BE = 14,563 T, 1,459 q, total 9.99e8 T — but ε_fro = 82.5 mHa, so it **fails the 20 mHa gate**; its
scan spans Λ 140–206 with a *free* shift [deep-chem §2.1], [papers §D.1]. FeMoCo-54 (10,27,27), b_rot 15: Outer 310,
Inner 1,154, RPREP 361, SEL 3,295, REF 67 ⇒ 9,997 T / 1,131 q. Gu et al. Fe₂S₂ alias+SELECT: 55 k → 15 k T by
repeated-span pruning (41,050 → 10,271), melt scheduling of the address map, hold-budget DP [ai-tricks §1.4.4].

**Levers** [deep-chem §3], [ai-tricks §5.3], [participants §10]

| Lever | Estimate |
|---|---|
| Fewer addresses × fewer bits (ANGLES ∝ L·brot under the cap) | L 1,220 → 700–900 and brot 8 → 7: ×1.3–1.7 on ANGLES **if** the gates allow (training problem with fixed S, β₁) |
| Λ at the E_gap floor: full re-optimisation with Λ penalty, W^(ρc) offsets and h1' negative mass as explicit variables | Λ 300 → 200–250 ⇒ λ_eff 39–44: ×1.1–1.25; feasibility under the fixed shift unproven (community claims λ_eff ≥ 46.79) |
| ANGLE engineering: select-swap k = 2–4 with J·brot·k ≲ 105, address ordering/repeated-span pruning, hold-budget DP, half-priced conditioned Toffolis | ×1.2–1.5 on ANGLES (loader side is near an algebraic floor for the C40 table) |
| (R,B,C) co-design with inner heuristic (RC and B+1 terms) and shared temp | ×1.1–1.3 on Q |
| Tree/gauge (multi-valued θ ∈ f⁻¹(u)) to make brot 7 pass and to shape zero/repeated words | ×1.1–1.15 |
| Not levers | E_gap below floor, Λ < 49, tree depth, per-row precision, MBU unlookup as reverse pass, Z_POW |

---

## 4. kickmix cost cheat-sheet

Source: [kickmix §1–9] (measured against the wheel) unless noted. Units: Tof = Toffoli-like count; "free" = 0 Tof.

### 4.1 Instruction costs

| Instruction | Cost | Semantics |
|---|---|---|
| `X, CX, Z, CZ, SWAP, NEG, BIT_*` | free | reversible / phase / classical |
| `CCX, CCZ, CSWAP` (incl. `if b`) | **1 each**, counted per shot only when the condition holds | |
| `SWAP a b if b` (bit-controlled swap) | free | `cswap(km.b, …)` free, `cswap(km.q, …)` 1 per pair |
| `Z_POW q t` (t in half-turns, 2^-127 grid, canonical [0,2)) | level ≤ 2 (multiples of ½) free; level 3 (odd/4) = 1 T; level ≥ 4 = rotation priced 0.56·log2(1/ε)+5.3 T (invsqrt only; forbidden in dqi/dfthcsos) | not bit-parallel in the simulator (~35× slower when the qubit is 1) |
| `HMR q b` | free | `b = random; phase ^= q & b; q = 0` — must be fixed by `NEG/Z/CZ/CCZ … if b` |
| `R q` | free | `phase ^= q & random; q = 0` — **unfixable** on a |1⟩ qubit (fails 50 % of shots) |
| `PUSH_CONDITION if b` / `POP_CONDITION` | free | snapshot of b at push time; everything but PUSH/POP/REGISTER/INFO_TAG skipped while false |
| `INFO_TAG "@enter:NAME"` / `"@exit:NAME"` | free | flame-chart attribution |

### 4.2 Primitive costs (Python builder, `max_qubits = inf`)

| Primitive | Tof | Ancilla | Note |
|---|---:|---|---|
| `init_and` / `del_and` | 1 / **0** | +1 | `R t; CCX` / `HMR t b; CZ c1 c2 if b` |
| `multi_controlled_x` k controls | k−1 | k−2 | AND ladder with MBU; C++ `cccx` with no clean qubit silently uses a dirty helper at 4 Tof |
| `iadd` quantum offset, n bits | n−1 | n−2 | Gidney adder; qubit-controlled 2n+3; with fewer spare qubits 8-bit cost rises 7 → 13 |
| `iadd` classical constant | n−2 | n−1 | needs ≥ 2 clean; qubit-controlled n+1; `btol` skips carries into leading runs |
| `flip_if_less_than` const / quantum | n−1 / n | n−1 | controlled n+2; `==` n |
| `init_lookup` N = 2^a entries, w output bits | **N−2** (N−1 controlled) | a | unary iteration; table must have exactly 2^a entries, a ≤ 32; all-zero table still costs N−2; width free |
| `del_lookup` (MBU unlookup) | ≈ 2^(a−⌊a/2⌋) + 2^⌊a/2⌋ (N=8/16/32/64/128/256/512 at w=8: 2/3/7/10/18/25/41) | 2^a classical bits | **raises** when 2^(a//2) > 2·(a//2)+w (w=1 fails for a ≥ 6, w=8 for a ≥ 10) — pad `target` with fresh |0⟩ qubits |
| `unary_iteration` a bits | 2^a−2 (2^a−1 controlled) | a | entering ≤ a, moving x→y costs bit_width(x^y)−1, closing 0 |
| `left_rotate` constant shift | 0 (SWAPs) | 0 | quantum shift of log2 n bits: 4/13/36/91 CSWAP for n = 4/8/16/32 |
| `init_gf2_mul` m = 12 | **63** (controlled 75) | 0 | Karatsuba; `del_gf2_mul` **0** (m HMR + m² conditioned CZ) |
| `gf2_phase_by_product` | 0 | | phase kickback without the product |
| `init_gf2_inverse` m = 12 | **315** (with scaffold: 72 qubits, `del_…_with_scaffold` 0) | | Itoh–Tsujii; without scaffold the delete costs 315 again |
| `init_gf2_div` m = 12 | 378 | | |
| `gf2_imul/idiv(const)`, `gf2_iadd`, Frobenius, squaring | 0 | | CNOT linear maps |
| phase gradient | n/a | | **not available** in kickmix |

Literature formulas (Qualtran, same accounting) [qualtran §2]: `Add` n−1; `Product(n,m)` 2nm−max; `Square` n(n−1);
truncated real×real `d²−d−1`; QROAM clean `⌈N/K⌉ + b(K−1)` (+ (K−1)b qubits), MBU adjoint `⌈N/K⌉ + K ≈ 2√N`;
variable-spaced QROM = (#aligned constant segments) − 1; `QROM` with repeated rows priced by `_break_early`.

### 4.3 Uncomputation tricks that are free or cheap

* Temporary AND: compute 1 Tof, erase 0 (HMR + `CZ if b`). Every adder/multiplier row AND, comparator carry, unary-iteration
  ladder node and QROM ancilla should be erased this way; the reverse pass should cost well below the forward pass
  [companion §1.2], [qualtran §6].
* Out-of-place product whose factors survive: erase for 0 Tof (`del_gf2_mul`, Qualtran `GF2MulMBUC`).
* Lookup erasure: `del_lookup` / Berry unlookup ≈ 2√N instead of N; Gu's batched one-hot + Reed–Muller repair: 17 for
  128 entries, 50 for 514 live words, 212 for 345 leaves [ai-tricks §1.4.3 N8]; ecdsa split-address cleanup
  `C(w) = 2(2^⌊w/2⌋ + 2^⌈w/2⌉) − 4` [ai-tricks §2.2 L8].
* Measured carries (1 Tof + 1 live qubit) vs in-place Cuccaro carries (2 Tof, 0 qubits): choose per position under a
  live-qubit cap [ai-tricks N11].
* Conditioned fix-ups execute only on shots where the outcome bit is 1 ⇒ the Toffoli *mean* is halved for conditioned
  `CCZ`/`CCX` (borrowed-wire 3-AND uncomputes in dqi HW-06).
* Everything that is a bijective image of the input (EEA/BM state, arithmetic outputs) cannot be measured away; it must
  be reversed or recomputed [deep-dqi §7].

### 4.4 Allocator behaviour

* LIFO free list: `alloc_qubits` pops the most recently freed id, else `next_qubit_id++`; `create_quantum_register`
  bypasses the free list (fresh ids). Freed qubits are not cleaned. **Q = max id + 1**, so reuse *ids*, keep allocations
  LIFO and tight; ancilla ids left over from early allocations count forever.
* `set_max_qubits` bounds live allocations and silently switches generators to lower-workspace variants (Toffoli count
  rises) or makes them raise ("tried to take N clean qubits"). Subroutines take `min(num_free_qubits, n)` workspace.
* `del_lookup` allocates 2^a classical bits (bits are free in every metric but `num_bits` explodes; verifier memory
  ~1.5 KB per bit for dqi at some versions).

### 4.5 Pitfalls that cause verifier failures

1. `R` on a dirty qubit ⇒ random sign, cannot be fixed ("compute then reset" designs fail at x = 2 with 0.5-turn errors).
2. `HMR` on a qubit that is not a Z-basis function of the others, or an unfixed kickback ⇒ 50 % of shots fail; 64 shots per input catch it with probability 1 − 2^-64.
3. Wrong register names/widths: invsqrt exactly `x` (22 q); dqi exactly `S0..S69`/`E0..E4094`; dfthcsos exactly `selection` of the prescribed width and `word_0..word_{J−1}` of equal width; every register named.
4. `.kmx` text saved as `.kmb`; both formats for one stem; non-contiguous `angle_k`; same file for every `angle_k`; npz with wrong shapes or pickles; hard links; nested duplicates.
5. dfthcsos words that depend on a measurement outcome (differ across the 64 shots) are rejected; reverse pass must restore batch k−1.
6. invsqrt: one tight x sets ε for every rotation; a negative margin fails; measuring a subrange of x locally gives non-comparable costs.
7. dqi: `Z_POW` anywhere; dirty ancilla counts as a value error; local zero failures can become 1–2 on Kaggle's salt.
8. Static `operation_statistics()` double-counts mutually exclusive conditional branches — use `Simulator(counting_operations=True)` or the official verifier for costs.
9. Text-format traps: `Z_POW q0 1` / `.5` are parse errors (need `1.0`/`0.5`); `X q0 if b0 if b1` silently drops the second condition; a qubit may not appear twice in one instruction.
10. GF generators do not check register disjointness (silently wrong); `init_lookup` needs exactly 2^a entries; `target` is keyword-only in arithmetic subs.
11. `count_operations --magic` and `estimate_ccz_state_weight` are not the competition metric (they count Clifford `Z_POW`).

---

## 5. Leaderboard state and what each improvement buys

**Public LB history** [kaggle-pages §5], [participants §0]: 10-28 top 26.14; 10-30 26.76 (1,696–1,729 teams); 10-31 top-10
26.76 … 24.96, 9 teams > 25, median 22.66, ~81 teams at 1.000; 11-02 27.996 (Breaking1800), 6th place 26.80, 2,052 teams;
latest cached: **28.83** (James & Geremie & Tony), 28.08, 28.00, 6th ≈ 26.8, 2,233 teams. The field is bimodal: about half
of all teams sit at 22.9–23.2 (assemblies of public Apache-2.0 circuits); the public frontier is rank ~374.

**Geomean arithmetic.** `Score = (r_I · r_II · r_III)^{1/3}`; a factor f on one task multiplies the score by f^{1/3};
+1 % on one task ≈ +0.33 % overall.

| Assembly | r_I | r_II | r_III | Score |
|---|---:|---:|---:|---:|
| public frontier 2026-10-30 | 20.57 | 60.59 | 9.93 | 23.13 |
| rounded "20.6 / 63 / 10.5" | 20.6 | 63 | 10.5 | 23.89 |
| manwithacat HW-06 (verified locally) | 20.65 | 63.9 | 10.27 | 23.84 |
| **best public parts, 2026-11-03** | **20.65** | **63.9** | **10.57** | **24.07** |
| leader 28.83 (product 23,963 = 1.72× the public product) | e.g. 25 / 80 / 12 | | | 28.8 |

What reaching X on one task buys, holding the other two at the public frontier (20.65 / 63.9 / 10.57):

| invsqrt → | score | dqi → | score | dfthcsos → | score |
|---:|---:|---:|---:|---:|---:|
| 25 (cost 83 k) | 25.65 | 80 (3.05e11) | 25.94 | 15 (2.24e8) | 27.05 |
| 30 (69 k) | 27.26 | 100 (2.44e11) | 27.95 | 20 (1.68e8) | 29.77 |
| 40 (52 k) | 30.01 | 150 (1.63e11) | 31.99 | 30 (1.12e8) | 34.08 |

Marginal values at the frontier: one dqi qubit at 892 = 0.22 % dqi = 0.075 % overall (≈ 0.018 pts); one dqi failing shot
= −0.46 % dqi ≈ −0.037 pts; one invsqrt qubit at 62 = 1.6 % invsqrt ≈ 0.54 % overall (≈ 0.13 pts); 100 invsqrt Toffoli-eq
= 6.2 % ≈ 2.1 % overall; Q = 840 (the dqi floor) would give at most +3.85 % overall. Overtaking 28.83 from the public
assembly needs ×1.72 on the product, e.g. ×1.2 on each task (→ 28.9) or ×1.5 on dqi plus ×1.15 elsewhere. The single-task
prizes will likely need invsqrt < 100 k, dqi < 3.8e11, chemistry < 3.2e8 [participants §10].

---

## 6. CONTRADICTIONS AND OPEN QUESTIONS

Authority order: official verifier/metric source > companion paper > Kaggle rules mirror > participant claims > inference.

| # | Topic | Disagreement | Resolution |
|---|---|---|---|
| 1 | **Static vs mean Toffoli count** | [kickmix §3, §10.4] says the competition uses the *static* `num_toffoli_like` (+T/4) and that `CCX … if b` "still counts 1"; [kaggle-pages §1.3], [participants §4–6], [companion §2.2 "mean per shot"] say mean *executed* per shot | **Resolved: mean executed** (verifier source: `Σ num_toffoli_like / num_shots` with `counting_operations=True`). kickmix's statement describes `Circuit.operation_statistics()`, not the verifier |
| 2 | **Z_POW in dqi** | [kickmix App. B] "Benchmark II counts Toffolis only" (implies allowed but uncounted); [participants §5], [kaggle-pages §1.3]: verifier raises `ValueError` | **Resolved: forbidden** in dqi and dfthcsos; allowed only in invsqrt (and it passes the metric's global allow-list) |
| 3 | **dqi baseline Toffolis** | companion v1 5,730,597; v2 5,725,461 (static); verifier mean 5,725,108.38 (empty salt) / 5,725,108.86 (clduab11 salt) / zjukop3 5,725,110 | **Resolved**: static 5,725,461; mean varies with salt in the 7th digit (one Forney step skipped per shot on average). Baseline cost 24,439,463,583,672.93 (empty salt), 24,439,465,632,206.816 and 24,439,473,914,136.668 at other salts; Kaggle uses the per-split value |
| 4 | **dqi baseline qubits / Khattar numbers** | companion 1,893 q; Khattar Table VI 1,885 q & 5,717,729 T; [companion §3.3] "Khattar reported 5.2e6 with a 51-T multiplier"; [papers §4.1] "Khattar's own count … 5.72e6"; Gu's re-run 5,125,070 T / 1,938 q | **Resolved**: three different implementations. 5.72e6/1,885 = Khattar's *whole* DQI circuit; ≈5.1–5.2e6 = its decoder part; 1,893/5,725,461 = the kickmix reference (63-T multiplier) |
| 5 | **Inversion cost per position** | 315 (Itoh–Tsujii) vs 351 per position; [papers §C.9] "≈ 6 × 51 + overhead" | 351 = 315 inversion + 36 (zero test, copies); chain is 5 products × 63 = 315 (5 × 51 = 255, 5 × 42 = 210) |
| 6 | **R at k = 2** | [participants §5] "k=2 → 1.223×"; [companion §3.4], [deep-dqi §1.5] R(2) = 1.2014 (+0.85 %) | **Resolved: 1.2014** (participants' value is non-monotone with its own k=3 → 1.2056; typo) |
| 7 | **Gu's RS decoder under the competition metric** | [qualtran §0] ≈1.6e12 (15×, used R ≈ 1.1); [papers §C.3] 1.77e12 (14×, k = 0); [ai-tricks §4] ≈1.85e12 (13×, ≈14 failures) | **Resolved**: 1.78e12 at k = 0, 1.85e12 at k = 14 ⇒ 13–14×; qualtran's R was too low. All agree it is far below the 63.9× frontier |
| 8 | **dfthcsos public-best numbers** | [papers §F.3] pairs "16,366 T, λ_eff 48.764" with cost 3.378e8 / 9.93×; [participants §7.3]: 16,366 T + 48.764 is clduab11's port (3.432e8, 9.78×); 3.380e8 (9.93×) is heliosli's 16,266 T at λ_eff 48.324 | **Resolved** per the participants table (arithmetic check: 48.764 × 16,366 × 430 = 3.432e8) |
| 9 | **dqi "SomeJoint 897" Toffolis** | [papers §F.2] 440,564 T for the 897-q decoder; [participants §7.2] 897 q = 440,633 T, 440,564 belongs to alexchilton's 889 q | **Resolved** per participants (hash-pinned verifier JSONs) |
| 10 | **Rotation price per rotation** | [papers §E.1] "≈19–25 T ≈ 5–6 Tof-eq"; verifier/companion: 27.28 T ≈ 6.8 Tof-eq for the reference (ε = 1.53e-12), 28.77 T on the 63-q frontier | **Resolved: 27–29 T** at competition margins; papers' range assumed a looser ε |
| 11 | **Origin of the 0.56·log2(1/ε)+5.3 constant** | [papers §E.4] attributes it to Beverland et al. (0.53·log2); [companion §2.2], [qualtran §2] Kliuchnikov et al. 2203.10064 | Verifier uses 0.56; cite Kliuchnikov et al. (companion ref.) |
| 12 | **R(ε) origin** | Kaggle Data page "paper Eq. (43)"; [deep-dqi §0] companion's own TV-distance derivation vs Nature paper's imperfect-decoding theorem (loss linear in ε) | **Resolved**: companion derivation (p₀ = ½, trace distance ≤ 2√ε); the Nature theorem is not used |
| 13 | **λ_eff floor** | [companion §4.6], [qualtran §0] derive λ_eff ≥ 19.19 from the floors and speculate the baseline sits at the floors; README says the floor pair "is not a lower bound on λ_eff"; participants: baseline Λ = 308 (far above 49), E_gap 3.9655 (1.3 % above floor); forum claim λ_eff ≥ 46.79 for any factorisation with the fixed shift; Cortes sector bound Λ ≥ 57.6 (coherent) / 109 (incoherent) ⇒ λ_eff ≥ 20.9 / 29.0 at the E_gap floor | Formal floor 19.19 is loose; physical bound ≈ 21–29; empirical community floor 46.79 is a **participant claim, unverified**. **Open**: how far Λ can fall under the fixed (S, β₁) |
| 14 | **Givens adder widths** | [companion App. A.1] "b_t-bit controlled adder, 2b_t − 1" (per-edge b_t); [qualtran §5.4] suggests narrow words per edge; README/verifier: `2(N−1)(2·brot−1)` with one `brot` for all words | **Resolved: single brot** (verifier); no per-row precision exists |
| 15 | **Q cap for dfthcsos** | companion v1 scored `min{qubits,128}` with qubits = ANGLE width; v2/verifier: 128-qubit cap per ANGLE_k, Q_total uncapped | **Resolved: v2** (inclusive: 128 allowed, 132 and 167 rejected) |
| 16 | **Prize total** | Inzainos table lists "$50,000 additional prizes" beyond the itemised $150k | Companion paper and itemised sum say **$150,000**; extra line unverified |
| 17 | **Final deadline** | Kaggle social post "January 13" vs 2027-01-20 | 01-13 = entry/merger deadline; **final = 2027-01-20** |
| 18 | **Data volume** | [kaggle-pages §3] "≈ 3.7 GB incl. starter kit"; [participants §2.1] "≈128 MB compressed / 1.04 GB unpacked" (clduab11) | Not reconciled; dqi.kmb alone is 886 MB, so 1.04 GB unpacked for the competition data is plausible and 3.7 GB includes the starter kit. Minor |
| 19 | **zjukop3 E5 deltas** | [papers §F.1] attributes 260 → 231 q and 7,735 → 6,852 T wholly to the binary-s rewrite; [participants §7.1, §8.8] the E5 step itself was 237 → 231 q and 7,334 → 6,852 T on top of earlier edits | Participants (primary notes) |
| 20 | **`init_lookup` cost** | [qualtran §2.3] "N − 2 + n_ctrl And (≈ N − 1)"; [kickmix §4.3] measured N − 2 uncontrolled, N − 1 controlled; README reference ANGLE ≤ L − 2 | **Resolved: N − 2** uncontrolled |
| 21 | **Invsqrt rotation lever** | [companion §9.1.6], [papers §3.4 idea 6] propose cheaper rotations via larger margin; [participants §7.1] acco-cyber LP: angles already optimal, doubling margin saves ~10 Tof-eq, no rotation droppable | **Closed at the frontier** (participant measurement); still ~3 % of C on a fresh design |
| 22 | **dqi frontier snapshots** | [kaggle-pages §5] 10-30: 888 q 4.0334e11 (60.59×), manwithacat 888 q 4.0199e11; [participants §7.2] table has no 888-q row (889 q 4.0246e11, then 893/892) | Different snapshot dates; 892 q / 3.8254e11 (63.9×) is the latest verified |
| 23 | **kickmix throughput** | paper 6e10 instr/s (native AVX-512 build); measured 1.16e10 shot-instr/s with the `-mno-avx` pip wheel | Both true; build with `-march=native` for speed |
| 24 | **ε⁺ ≥ 1/16 shot count** | "≈6,000 failures" [participants §9.5] vs 1/16 × 102,400 = 6,400 | Approximation; irrelevant in practice |
| 25 | **Gu's "no human intervention"** | [ai-tricks §1.2] notes `gen_constants.py` (100–200 CPU-h), Lean proofs and custom bilinear synthesis are human-curated | Inference; read as "the agent chose algorithm and structure" |
| 26 | **Open: metric vs standalone verifiers** | forum thread "Final evaluation scope" (11 votes) unanswered; the metric notebook adds file-level checks (§1) absent from standalone verifiers | Treat the metric notebook as authoritative |
| 27 | **Open: inner heuristic formula** | [deep-chem §1.5] reproduces outer 846 exactly from Low et al. Table "outer_prepare_costs" (χ = 10, k₁ = 4, k₅ = 6) but **cannot** reproduce inner 9,461 or the 544 shared temp from naive k choices | Read `scoreinfra/costs_prepare.py` (`SpinFreeData_V1`, three documented deviations) before any (R,B,C) sweep |
| 28 | **Open: `del_lookup` repair cost vs Gu's one-hot + Reed–Muller rail** | kickmix measured table (§4.2) vs Gu 17/128, 50/514 | Measure on our table shapes |
| 29 | **Open: per-test classical mask in dqi** | Gu's fixed mask lets the syndrome-linear part be baked in; ours is per-shot classical bits. [ai-tricks §5.2] sketches an F₂-linear classical projection (Vandermonde solve offline) — the public "classical mask projection" does this, but the per-point ν_j folding is uncosted | Derive and cost; the frontier's `scan` stage (44,275 T ≈ 11/position) suggests it is cheap |
| 30 | **Open: public loaders are not true XOR oracles** | pass the verifier, fail an arbitrary-target XOR audit [participants §7.3] | No LB risk under salted HMR re-draws; a host-side scope change could matter (see #26) |

---

## 7. Reading order for a new team member

1. **This file**, then [kaggle-pages] §1–4 (rules, formulas, file contract) — 30 min.
2. [companion] §1–4 (kickmix model, the three contracts, reference constructions, verification math) — the authoritative spec; skip §5–6 (nothing about the agents is in the paper).
3. [participants] §3–6 (metric notebook and the three verifiers line by line, with exact numbers) and §9 (pitfalls) — read before writing any file; §7 for the public frontier with hashes.
4. [kickmix] §1–4, §9 — the builder API, costs and gotchas; keep §4.3 open while coding.
5. Per benchmark, in this order: [deep-invsqrt] §0, §16–18 (contract, cost primitives, design space); [deep-dqi] §0–1, §7–10 (contract, algorithms, arithmetic, design points); [deep-chem] §0–1, §3 (score anatomy, levers).
6. [ai-tricks] §1.3–1.4 and §5 — the concrete trick catalogue (Gu et al.) and its transfer table; §6 for the search-loop design.
7. [qualtran] §2 and the per-benchmark bloq tables when you need a literature cost formula or a Qualtran reference implementation.
8. [papers] as the annotated bibliography (confidence-tagged); §G for the ranked technique list; [deep-*] supersede it where they overlap.

Raw material: `kaggle-raw/` (verbatim mirrors incl. the official `SCORING_README.md` and the 2026-10-31 full leaderboard JSON).
