# Deep read: the primary papers behind the `dqi` benchmark

Scope: depth, not breadth (the broad bibliography is in `papers.md`). This file reads the papers that
define the `dqi` benchmark (Benchmark II of the Kaggle competition "Google Quantum AI – Verifiable
Quantum Circuit Compilation"), the DQI algorithm itself, the published reversible Reed–Solomon (RS)
decoders, and the GF(2^m) arithmetic literature, and ends with a design-space synthesis for the
`R(ε⁺)·Q²·T` metric.

Tags used below: **[PAPER]** = stated in the cited paper; **[NUM]** = recomputed here (script
`/tmp/claude-0/-home-user/af1e8b3b-1af8-51dd-9e8d-ec3f80eabc0b/scratchpad/scripts/dqi_numbers.py`);
**[SIBLING]** = taken from `participants.md` / `kaggle-pages.md` (verifier source and leaderboard
reconstructions by other agents); **[INFERENCE]** = my own estimate or reasoning.

Local copies (PDF + LaTeX source where available) are in
`/tmp/claude-0/-home-user/af1e8b3b-1af8-51dd-9e8d-ec3f80eabc0b/scratchpad/papers/<id>/`
(`paper.pdf`, `src/main.tex` or `src/DQI_arxiv_v5.tex`, `assets/code/*.py` for 2510.10967).

---

## 0. TL;DR

* **Benchmark contract** (companion paper arXiv:2610.23832 §"Benchmark II"): given the classical
  syndrome `s = Bᵀe` in 70 twelve-qubit registers `S0..S69` and a classical 49,140-bit record
  `c` (`E0..E4094`, 12 bits each), apply the phase `(−1)^{c·bin(e(s))}` where `e(s)` is the unique
  error of weight ≤ 35 with syndrome `s`, restore `s`, return all workspace to |0⟩. Field
  `F_{2^12} = F_2[α]/(α^12+α^6+α^4+α+1)`, little-endian polynomial basis, evaluation points
  `α_j = α^j`, `s_i = Σ_j e_j α^{(i+1)j}`, `i = 0..69`. Dual code `[4095, 4025, 71]`, `ℓ = 35`.
* **Score** `S = R(ε⁺)·Q²·T`, `R(ε) = ln 2 / (−ln(½ + 2√ε))`, `Q` = total qubits (syndrome +
  workspace, peak), `T` = mean executed Toffoli count per shot. `ε⁺` is the one-sided
  Clopper–Pearson upper bound at confidence `1 − 2^{−128}` from `k` failures in `N = 102,400` shots.
  `ε⁺ ≥ 1/16` → no score.
* **Origin of `R`**: the companion paper's own derivation (not the Nature paper). Fuzz-test failure
  rate `ε` → purified-state Euclidean error ≤ `2√ε` (Eq. "branch_robustness", because failing
  branches of the measurement record add in quadrature) → trace distance ≤ `2√ε` → total-variation
  distance of the sampled candidate distribution ≤ `2√ε` → per-run success probability
  `p ≥ p₀ − 2√ε` with `p₀ = ½` ("acceptable" = at least the median of ideal DQI) → number of
  repetitions to reach any fixed overall failure `δ'` scales as `ln δ'/ln(1−p)`, so the repetition
  overhead is `R(ε) = ln(1−p₀)/ln(1−(p₀−2√ε)) = ln 2 / (−ln(½+2√ε))`. The Nature paper's own
  imperfect-decoding theorem (Thm. "imperfect_decoding", objective loss `2ε(m+1)`) is a different,
  weaker-for-this-purpose statement and is *not* what the benchmark uses.
* **Numbers that matter** [NUM]: `k = 0 → ε⁺ = 8.66×10⁻⁴, R = 1.1913` (the floor every exact
  submission pays). Each extra failing shot costs ≈ +0.46 % at first; `k = 10 → +3.2 %`,
  `k = 50 → +10 %`, `k = 100 → +16.6 %`, `k = 500 → +52 %`. DQI's error-weight distribution
  (principal eigenvector of the tridiagonal `A`) has `E[w] = 31.05`, `P(w = 35) = 2.77 %`,
  `P(w ≤ 20) = 5.5×10⁻⁵`, `P(w ≤ 16) = 1.6×10⁻⁷`. Therefore: correcting fewer than 35 errors is
  catastrophic (`ℓ' = 34` → `ε ≈ 0.028 → R ≈ 3.9`), but being *wrong on low weights* (≤ 18) is free.
* **Published designs**: Google reference (synchronized EEA + Chien/Forney, 1,893 q, 5.73 M T,
  score 2.44×10¹³); Khattar et al. 2510.10967 (same with a 51-Toffoli multiplier: 1,885 q, ≈5.2 M T
  decoder); Gu et al. 2610.22367 (LLM-discovered Berlekamp–Massey with rescaled updates, in-place
  evaluator, phase-only trace scan with a precomputed reciprocal polynomial: 1,837 q, 442 k T,
  ≈13× better) [PAPER]. The public leaderboard lineage (in-place continued-fraction/Schur solve in the
  syndrome register, 883–900 q, 400–520 k T, ≈64×) [SIBLING] goes further on `Q`.
* **Most promising directions** (synthesis, §10): (i) work in place in the 840 syndrome qubits
  (`Q ≈ 850–900`), (ii) phase-only recovery `Tr(ν_j ω(β_j) Ψ(β_j))` with 23 Toffolis/position and a
  single precomputed reciprocal `Ψ ≡ 1/σ' (mod σ)` via a half-degree EEA on `σ = E² + zO²`,
  (iii) classical mask projection to skip 70–71 positions, (iv) spend the ε budget only on
  `≤ 10⁻⁴`-probability events (history-stack overflow, coefficient cut-offs, low-weight behaviour),
  (v) cheaper `F_{2^12}` products (rank-42 evaluation/interpolation over `F_8`, 51-Toffoli
  Karatsuba) and MBUC (X-measure + CZ) for every product whose factors survive.

---

## 1. The benchmark definition (arXiv:2610.23832, Benchmark II and §"Fuzz testing") [PAPER]

Citation: T. Khattar, N. C. Rubin, C. Gidney, M. Broughton, G. H. Low, R. Babbush, *Leveraging
verifiable structure in quantum circuits to find more efficient compilations with agentic AI*,
arXiv:2610.23832 (Oct 2026). Only its DQI section/appendix is read here.

### 1.1 Problem and why RS decoding appears

* OPI instance: allowed sets `F_i ⊆ F_q` at the `m = q−1` nonzero points `α_i`; find
  `Q_x(z) = Σ_{j<n} x_j z^j` maximizing `f(x) = |{i : Q_x(α_i) ∈ F_i}|`. `|F_i| = r` for all `i`.
* `B_{ij} = α_i^j` (m×n Vandermonde); `C = {Bx}` is an RS code; DQI needs a **syndrome decoder of
  the dual** `C^⊥ = ker Bᵀ`, parameters `[m, m−n, n+1]`, distance `d = n+1`.
* Fourier identity (their Eq. "dqi_fourier_syndrome"): for `q = 2^b`, `χ(z) = (−1)^{Tr z}`, QFT =
  Walsh–Hadamard, and
  `Σ_x P(f(x))|x⟩ = √(qⁿ)·QFT( Σ_{wt(e)≤ℓ} a_e |Bᵀe⟩ )`.
  The degree of the enhancing polynomial `P` equals the number of correctable errors `ℓ`.
* Uniqueness: for `2ℓ ≤ n` two errors with the same syndrome differ by a codeword of weight ≤ n <
  d, so the map `s ↦ e(s)` is well defined on the support.

### 1.2 Why the task is a *phase* and not an erasure

The improved construction of Khattar et al. (2510.10967) generates error symbols one at a time into a
single `b`-qubit register, adds `e_i b_i` to the syndrome, and erases the register by X-basis
measurement (MBUC), picking up `(−1)^{c_i·bin(e_i)}` per position. After all `m` positions the state
is `|ψ_c⟩ = Σ a_e (−1)^{c·bin(e)} |Bᵀe⟩`. The decoder's only job is to cancel that sign:

```
U_c |s⟩|0⟩_W = (−1)^{c·bin(e(s))} |s⟩|0⟩_W ,   s = Bᵀe(s),  wt(e(s)) ≤ ℓ .      (benchmark contract)
```

"Implementations may recover error symbols one at a time or compute the required parity directly."
`c` is a per-shot classical input (bits `E0..E4094`), so all phase application is classically
controlled `Z` (Clifford, zero Toffolis).

### 1.3 Instance and reference implementation

* `(m, n, b, r) = (4095, 70, 12, 2016)`, `r = (2^b − 2^{b/2})/2` = bent-function target size.
  Dual RS code `[4095, 4025, 71]` over `F_{2^12}`, decoder corrects `ℓ = n/2 = 35` errors.
* Syndrome: 70×12 = 840 qubits; record: 4095×12 = 49,140 classical bits.
* Field `F_2[α]/(α^12+α^6+α^4+α+1)` (integer 4179 in the verifier [SIBLING]), little-endian
  polynomial basis `(1, α, …, α^11)`, points `α_j = α^j`, `s_i = Σ_j e_j α^{(i+1)j}`.
* Reference (3 stages):
  1. **Key equation** `σ(z)S(z) ≡ Ω(z) (mod z^{2ℓ})` by the EEA on `(z^{2ℓ}, S(z))`, stopping when
     `deg r < ℓ`. Zero syndrome → `σ = 1, Ω = 0`. Uses an optimized Proos–Zalka synchronized EEA
     (register sharing between shrinking remainders and growing Bézout coefficients, quotients
     stored in free register space). `3(n+1)+9 = 222` synchronized cycles with unary iteration over
     five `O(log n)`-qubit degree pointers.
  2. **Chien search + Forney**: evaluate `σ(α_i^{-1})` at all `m` positions (in-place coefficient
     scaling by constants = CNOTs); on a zero, `e_i = Ω(α_i^{-1})/σ'(α_i^{-1})` with one Itoh–Tsujii
     inversion (315 Toffolis, 48 scaffold qubits); apply `Z` on recovered bits selected by `c_i`;
     clear temporaries. 351 Toffolis per position.
  3. **Uncompute the EEA** (reverse of stage 1).
* Storage: two arrays of `n+3` registers of `b` qubits (syndrome registers reused in the first array).
  Arithmetic: addition/squaring/multiplication-by-constant are `F_2`-linear → CNOT only;
  quantum–quantum product = 63-Toffoli Karatsuba; products whose factors stay in memory are erased by
  X-measurement + classically controlled CZ.
* Totals: **1,893 qubits** (`2(n+3)b + O(log n)` + inversion scaffold), **5,725,461 Toffolis**
  (static; mean executed 5,725,108 [SIBLING]). "Slightly higher than the 5.2×10⁶ of Khattar et al.,
  which used a hand-tuned 51-Toffoli multiplier instead of our 63-Toffoli circuit." Every part
  "can be improved".
  Qubit anatomy [SIBLING, nasir26]: 840 S + 876 `reg_b` + 36 pad + 40 pointers + 11 control + 90 peak
  temporaries. Toffoli anatomy: EEA sweep 50 %, Chien/Forney 25 % (inversions 22.5 %), `shift_b`
  8.3 %, `swap_a_and_b` 6.9 %.

### 1.4 Verification and the ε → R chain

* Test distribution: `e ~ |a_e|²` for the optimal degree-ℓ `P` (Lemma 9.2 of the Nature paper):
  `Pr[wt(e) = w] = v_w²`, `v` = unit principal eigenvector of the `(ℓ+1)×(ℓ+1)` tridiagonal
  `A_{w,w} = w(q−2r)/√(r(q−r))`, `A_{w−1,w} = A_{w,w−1} = √(w(m−w+1))`. Given `w`: positions uniform
  without replacement, values uniform in `F_q^*`, record `c` uniform. (`E[w] ≈ 31.05`,
  `P(w=35) ≈ 2.8 %` [PAPER, reproduced NUM].)
* Per shot the verifier checks (1) `S` unchanged, (2) all ancillas |0⟩, (3) phase = `(−1)^{c·bin(e)}`.
* Robustness lemma (§"Fuzz testing"): fix the record `r` of all HMR/R outcomes; each `V_r` maps
  basis states to basis states (up to phase) and is norm-preserving on the support when every
  measured qubit is a function of the others (MBUC). Failing inputs `B_r` carry weight `ε_r`;
  `ε = E_r[ε_r]` is exactly the fuzz-test failure probability. Then
  `‖W|ψ⟩ − U|ψ⟩⊗|+⟩^m‖² = E_r‖(V_r−U)Σ_{x∈B_r}α_x|x⟩‖² ≤ 4ε`, fidelity ≥ `(1−2ε)²`, trace distance
  ≤ `2√ε`, which upper-bounds the TV distance of any later measurement. (Footnote: a phase
  tolerance `τ` turns adds ≤ `2πτ`; negligible here. Also note: inputs that fail only through an
  `R`/uncorrected `HMR` on a |1⟩ qubit contribute *half* their weight to ε.)
* "Acceptable candidate" = satisfies ≥ the median of an ideal run, so `p₀ ≥ ½`; with failure rate ε,
  `p ≥ ½ − 2√ε`. Repetitions for overall failure `δ'`: `t(p) = ln δ'/ln(1−p)`, ratio independent of
  `δ'`: **`R(ε) = ln(1−p₀)/ln(1−(p₀−2√ε)) = ln 2/(−ln(½+2√ε))`**.
* `ε⁺`: smallest `ε` with `Σ_{j≤k} C(N,j) ε^j (1−ε)^{N−j} ≤ 2^{−128}` (one-sided Clopper–Pearson);
  for `k = 0`, `ε⁺ = 1 − 2^{−128/N} ≈ 88.7/N`. Verifier: `−expm1(ln δ / N)` for `k = 0`, 64-step
  bisection otherwise [SIBLING].
* Score `S = R(ε⁺)·Q²·T`: "a 1 % reduction in qubits improves the score as much as a 2 % reduction in
  Toffoli gates." `R(10⁻⁵, 10⁻⁴, 10⁻³, 10⁻²) = 1.02, 1.06, 1.21, 1.94`. `ε⁺ ≥ 1/16` → no finite
  score. Zero failures → `ε⁺ ≈ 8.7×10⁻⁴`, `R ≈ 1.19` floor.
* Scoring detail [SIBLING]: `T` is the *mean executed* Toffoli count (classically controlled gates
  that do not fire are not counted), `Q` = largest referenced qubit id + 1 (no lifetime tracking),
  `toffolis = toffoli_count + t_count/4`, `Z_POW` is forbidden in Benchmark II.

### 1.5 Recomputed tables [NUM]

| failures k (of 102,400) | ε⁺ | R(ε⁺) | penalty vs k=0 |
|---:|---:|---:|---:|
| 0 | 8.661×10⁻⁴ | 1.1913 | — |
| 1 | 9.104×10⁻⁴ | 1.1967 | +0.46 % |
| 2 | 9.488×10⁻⁴ | 1.2014 | +0.85 % |
| 5 | 1.048×10⁻³ | 1.2131 | +1.83 % |
| 10 | 1.188×10⁻³ | 1.2290 | +3.17 % |
| 20 | 1.427×10⁻³ | 1.2548 | +5.33 % |
| 50 | 2.022×10⁻³ | 1.3134 | +10.3 % |
| 100 | 2.865×10⁻³ | 1.3887 | +16.6 % |
| 200 | 4.353×10⁻³ | 1.5103 | +26.8 % |
| 500 | 8.308×10⁻³ | 1.8131 | +52.2 % |

Rule of thumb: a shortcut with true failure probability `ε_s` produces `≈ 102,400·ε_s` failing
shots; it pays off only if it reduces `Q²T` by more than the penalty above
(`ε_s = 10⁻⁴` → ≈10 shots → must save > 3.2 %; `ε_s = 10⁻³` → ≈100 shots → must save > 16.6 %).

Weight distribution (`m=4095, n=70, b=12, r=2016`): `λ_max/m = 0.168`, `E[w] = 31.05`;
`P(w) for w = 28..35 = 0.062, 0.099, 0.142, 0.176, 0.184, 0.154, 0.092, 0.028`;
`P(w ≥ 34) = 0.120`; `P(w ≤ 24) = 5.1×10⁻³`, `P(w ≤ 22) = 6.2×10⁻⁴`, `P(w ≤ 20) = 5.5×10⁻⁵`,
`P(w ≤ 18) = 3.5×10⁻⁶`, `P(w ≤ 16) = 1.6×10⁻⁷`. Expected shots with `w ≤ 20`: 5.6; with `w ≤ 18`: 0.36.
Semicircle expectation `⟨s⟩/m` (Thm. below) for `ℓ = 35, 34, 33, 30`: 0.5844, 0.5831, 0.5817,
0.5776 — the *optimization* loss from a smaller ℓ is tiny, but the verifier does not measure that:
it measures ε, and `ε(ℓ'=34) = P(w=35) = 2.8 %` → `R ≈ 3.9`.

---

## 2. Jordan, Shutty, Wootters, Zalcman, Schmidhuber, Isakov, Neven — *Optimization by Decoded Quantum Interferometry*, arXiv:2408.08292 (Nature 2025) [PAPER]

Source read: `src/DQI_arxiv_v5.tex` (v5, Oct 2025, 2,333 lines).

### 2.1 Contribution
Introduces DQI for max-LINSAT over `F_p` (and extension fields, §"Folded codes"): prepare
`|P(f)⟩ = Σ_x P(f(x))|x⟩` by (1) a weight-superposition `Σ_k w_k|k⟩`, (2) a Dicke/sparse-error
superposition, (3) the constraint-encoding isometries `G_i|1⟩ = Σ_{y≠0} g̃_i(y)|y⟩` (Fourier
coefficients of the shifted/rescaled constraint indicator `g_i = (f_i − f̄)/φ`, `f̄ = 2r/p − 1`,
`φ = √(4r(1−r/p))`), (4) computing `Bᵀy` into the syndrome register, (5) **uncomputing the error
register by bounded-distance decoding of `C^⊥`**, (6) inverse QFT and measurement.

### 2.2 Performance: the semicircle law
Theorem (semicircle): if `C^⊥` is decodable to `ℓ` errors (`2ℓ+1 < d^⊥`) and `|F_i| = r`,
`⟨s⟩/m → (√(ℓ/m·(1−r/q)) + √((1−ℓ/m)·r/q))²` (for `r/q ≤ 1 − ℓ/m`). The optimal `w` is the
principal eigenvector of the `(ℓ+1)×(ℓ+1)` tridiagonal `A^{(m,ℓ,d)}` (Lemma 9.2 / Eq. "A_def";
exactly the matrix the verifier samples from). For OPI with RS/Berlekamp–Massey (`ℓ = n/2`,
`m = p`): `⟨s⟩/p = ½ + √(n/2p·(1−n/2p))` vs Prange's `½ + n/2p`; e.g. `n/p = 1/2` gives 0.933 vs
0.75; `n/p = 1/10` gives 0.718 vs 0.55.

### 2.3 OPI → Reed–Solomon (§"Optimal Polynomial Intersection")
With `B_{ij} = γ^{ij}` (γ primitive), `C^⊥` is RS with alphabet `F_p`, length `p−1`, dimension
`p−n−1`, distance `n+1`; ML syndrome decoding to half distance is polynomial (Berlekamp–Massey), so
`ℓ = ⌊(n+1)/2⌋`. Balanced case `|F_i| = ⌊p/2⌋`. Classical attacks surveyed (Prange, list recovery,
lattice/Bleichenbacher–Nguyen, simulated annealing) do not reach DQI's fraction in the regime
`n/p ≈ r/p ≈ ½`.

### 2.4 What the decoder must do, and what failures cost (in this paper)
* Figure caption of Alg. 1: "If `2ℓ+1 < d^⊥`, the postselection succeeds with probability
  `≥ 1 − ε_ℓ`, where `ε_ℓ` is the decoding failure rate on random weight-ℓ errors."
* §"Imperfect decoding": a deterministic decoder partitions errors into correctly decoded `D_k` and
  misidentified `F_k` per Hamming shell; `ε_k = |F_k|/C(m,k)`, `ε = max_k ε_k`. After uncomputation
  the failed branches leave `|y ⊕ y'⟩ ≠ |0⟩` in the error register; postselecting on |0⟩ leaves the
  state `|P̃_D(f)⟩ = Σ_k w_k/√C(m,k) Σ_{y∈D_k} (−1)^{v·y}|Bᵀy⟩`.
* **Theorem (imperfect_decoding, F_2, average-case v):**
  `E_v⟨f⟩ ≥ wᵀ[A − 2ε(m+1)]w / Σ_k w_k²(1−ε_k) ≥ wᵀAw/wᵀw − 2ε(m+1)`, and asymptotically
  `⟨f⟩/m ≥ 2(√(ℓ/m(1−ℓ/m)) − ε)`. Remark: empirically the failure probability rises with weight, so
  the failure rate on uniform weight-ℓ errors upper-bounds ε. Proved only for `F_2`; the authors
  expect it to generalize.
* **This is not the benchmark's `R(ε)`.** The competition instead bounds the TV distance of the
  output distribution (`2√ε`) and converts it into a repetition factor (§1.4). Note the different
  scaling: objective loss linear in ε (this theorem) vs. success-probability loss `2√ε` (benchmark).
  The benchmark's ε is also weighted by `|a_e|²` rather than a max over shells (cf. Gao et al.
  2604.15025, who derive weighted bounds for the Nature-paper setting).
* Follow-up noted in the paper: Chailloux & Tillich [CT24] observe that for `p > 2` the per-symbol
  error distribution in DQI's decoding problem is non-uniform and exploitable by soft decoders
  (Koetter–Vardy); [PBH25] = Patamawisut et al. 2504.18334 (ISD/Gauss–Jordan reversible decoder,
  no RS-specific circuits).

### 2.5 Resource estimates (§"Resource Estimation for OPI")
Berlekamp–Massey syndrome decoder over prime fields `F_p`, `n ≃ p/2`, `ℓ = n/2`:
* Alg. "bkm_decoding": (1) BM-LFSR for `σ` (`O(N²)` mults, `O(N)` inversions), (2) `Ω = σS mod
  z^{n+1}` by NTT, (3) Chien by NTT, (4) Forney with `O(N)` divisions.
* Alg. "bkm_lfsr" (reversible BM, generalizing Chevignard–Fouque–Schrottenloher): per round `i`:
  discrepancy `d_i = Σ_j s_{i−j} c_j` (≤ ℓ+1 QQ mults), comparator `v_i = (2L ≤ i)`, `b ← b·r`
  (in-place, `r = d_i` or 1), conditional `c ← c − b`, conditional `L ← i+1−L; b ← b + c`,
  `b ← b·r⁻¹`. Garbage: `L`, `B(X)`, all `d_i`, all `v_i`. **Qubits `2(n+ℓ)⌈log₂q⌉ + n + log₂ℓ`**
  (for our instance that would be 2·105·12 + 70 + 6 ≈ 2,600 — the "history storage" problem that
  Gu et al. later solve).
* Table "arithmetic_costs" (prime fields): modular QQ multiplication `3n² + 2n − 1` Toffolis,
  modular inverse `26n² + 2n` (Litinski), etc. Table "lfsr_resource_estimates": `RS_521(520,264)`,
  i.e. `(n, ℓ, b) = (256, 128, 10)`: `1.01×10⁸` Toffolis, 8,850 qubits; `RS_67`: `10⁶`, 907 qubits;
  `RS_2153`: `2.2×10⁹`, 41,132 qubits. (These are prime-field numbers; the binary-field redesign in
  2510.10967 is ≈20× cheaper per multiplication.)
* Classical comparison: repeat-until-success Prange at `p = 521` needs ~10³⁵ trials.

---

## 3. Khattar, Shutty, Gidney, Zalcman, Yosri, Maslov, Babbush, Jordan — *Verifiable Quantum Advantage via Optimized DQI Circuits*, arXiv:2510.10967 (Oct 2025) [PAPER]

Source read: `src/main.tex` (2,561 lines) + `assets/code/{poly_eea_zalka_gcd, rs_syndrome_decoder_eea_zalka, divstep_dialog_inplace, rs_syndrome_decoder_eea_dialogs}.py`.
Data/code: Zenodo 17301475. This is the direct ancestor of the competition reference.

### 3.1 Contributions
1. OPI over `GF(2^b)` ("Twisted Bent Target OPI", Maiorana–McFarland sets so each `G_i` costs
   `O(log q)`), with classical hardness re-analysed (Prange, "Extended Prange" XP via LP/knapsack).
2. Qubit-efficient DQI circuit: sparse Dicke state in `ℓ·⌈log₂m⌉` qubits, sequential syndrome
   accumulation with one `b`-qubit error register erased by MBUC, phase fix-ups during decoding →
   total `2nb + O(log n)` qubits (was `(m+n)b` + decoder ancilla in the Nature paper).
3. Two EEA compilations at the `2nb + O(log n)` space floor: **explicit** Bézout (improved
   Proos–Zalka synchronized Euclid, `6n²` QQ multiplications, deterministic in-register quotient
   storage, unified cycle) and **implicit** Bézout (the "Dialog" = recorded Bernstein–Yang divstep
   transition matrices, `2n²` QQ multiplications).
4. End-to-end reversible RS decoders (EEA + Chien + Forney) with Qualtran resource estimates and a
   physical estimate (≈800 k physical qubits, ~1 h, for `(4095,70,12)`).
Headline theorem: OPI via DQI is the first verifiable-advantage candidate with `Õ(N)` quantum gates
for `2^N` classical hardness.

### 3.2 The DQI circuit (§"The DQI Quantum Circuit")
Registers: error-locator `ℓb`, error-value `b`, syndrome `nb`. Stage 1 sparse Dicke
(`2k log₂m` qubits, `O(mk + k²b²)` gates); Stage 2 for `i = 1..m`: (2a) unary-iteration membership
test `y_i` (`mℓ` gates total), (2b) `G_i` on `y_i` → `|e_i⟩_b`, (2c) `s += b_i e_i` (CNOT-only for
`GF(2^b)` since `b_i` is classical), (2d) MBUC of `|e_i⟩` → sign `(−1)^{c_i·e_i}`; Stage 3 reversible
decoding of `|s⟩` with sequential phase fix-ups; Stage 4 IQFT. The Stage-3 contract is exactly the
benchmark's `U_c`.

### 3.3 EEA compilation (§"Efficient Quantum Circuits for EEA")
Prior-art table (two degree-n polynomials over `F_q`, `b = ⌈log₂q⌉`):

| source | technique | qubits | dominant cost (QQ mults) |
|---|---|---|---|
| Kaye/Proos–Zalka 2004 | Euclid GCD | `3nb + O(log n)` | `12n²` |
| Roetteler et al. 2017 | binary GCD | `4nb + 2n + O(log n)` | `4n²` |
| Banegas–Bernstein–van Hoof–Lange 2020 | Bernstein–Yang | `4nb + n + O(log n)` | `4n²` |
| Kim–Hong 2023 | Bernstein–Yang | `4nb + 0.5n + O(log n)` | `4n²` |
| **this work, explicit** | Euclid | `2nb + O(log n)` | `6n²` |
| **this work, implicit (Dialog)** | Bernstein–Yang | `2nb + O(log n)` | `2n²` |

Modular division (`A/B mod P`): invert-then-multiply `7n²` at `4nb` vs direct division via Dialog
`4n²` at `4nb`.

**Explicit (synchronized) EEA.** Invariants (Fig. "zalka_eea_improved_flow"): (a)
`deg u_i + deg r_i ≤ n`, (b) `deg r_i < deg r_{i−1}`, `deg u_i > deg u_{i−1}`, (c)
`deg u_i + deg r_{i−1} = n`; so `(u_i, r_i)` share one `(n+1)`-slot register, two such registers =
`2(n+1)b`. Quotient `q_{i+1}` (degree `deg r_{i−1} − deg r_i`) is stored in the guaranteed-free
padding of the shared register. Five steps per logical iteration (compute quotient term-by-term;
right-shift remainder until leading coefficient nonzero; align `u_{i−1}`; `u_{i+1} = u_{i−1} −
q u_i` term-by-term; swap). Four-stage synchronized cycle driven by a `counter` and `flag`
(Python `poly_eea_zalka_gcd_impl`: per cycle `update_flag`, `multiply_and_add_or_sub` (one loop over
all `m = deg B + 3` slots doing `q_i·a[i]` products with CSWAP-based in-register quotient access),
`shift_b_array_right`, `update_metadata`, `swap_a_and_b`, `check_stop`; a `halting_counter` absorbs
early-finishing branches — the Proos–Zalka "quantum halting problem"). Per cycle cost
`T_i = 2d_i + s_i + d_{i−1} + 2` (d = quotient degree, s = remainder degree drop); total
`T = 3D_k + S_k − d_k + 2k`. **Worst case: full PEEA `6n − 1` cycles; half PEEA (RS) `6⌊n/2⌋ + 5`
= 215 cycles for n = 70** (the reference uses 222 = `3(n+1)+9`; the Python uses `3.75·(n+3)`).
[INFERENCE] For an error of weight `w` the typical cycle count is `≈ 4w + 70` (quotients of degree
1, one big remainder drop of `70 − 2w + 1` at step `w`), so `w = 35 → 210`, `w = 31 → 194`; there
is only ≈3–8 % to gain by trimming the cycle count, and the "all quotients have degree 1" shortcut
fails with probability ≈ `35/4096 ≈ 0.85 %` (→ `R ≈ 1.8`), so it is not usable.

**Implicit (Dialog) EEA.** Bernstein–Yang polynomial divstep: with `δ`, `(f, g)`: if `δ > 0` and
`g_0 ≠ 0` swap and negate `δ`; `c = g_0/f_0`; `g ← (g − c f)/z`; `δ ← δ + 1`. The Dialog is the list
of `(c, swap)` for `2n` steps; each step frees one `b`-qubit slot of the shrinking `(f, g)` pair
which immediately stores `c`: invariant `len(poly) + len(dialog) = 2n` (+3 slots). Playback on
`[0, C]ᵀ` gives `C·B⁻¹ mod P` (direct division); evaluating the Bézout polynomial at a point is a
product of constant 2×2 matrices. Python `construct_dialog` / `rs_syndrome_decoder_eea_dialog_inplace`
(evaluates `σ(β)` and `σ'(β)` by playing back the Dialog with derivative tracking:
`2n` QQ mults + `n/2` QC mults per evaluation).

### 3.4 RS decoding with the EEA (§"Decoding Reed Solomon Codes…")
`A = z^{2ℓ}`, `B = S(z)`; `A u_i + B v_i = r_i` ⇒ `S v_i ≡ r_i (mod z^{2ℓ})`; stop at the first `i`
with `deg r_i < ℓ`; `σ ∝ v_i`, `Ω ∝ r_i`. Chien: roots of `σ` at `γ_j⁻¹`; Forney
`e_j = −Ω(γ_j⁻¹)/σ'(γ_j⁻¹)` (the reference includes the position-dependent constant
`c^{−(len−1+n_b−n_B−1)}`; in characteristic 2, `σ'` = sum of odd-index terms).
Leading-order costs (Table "decoder_costs"):

| stage | explicit: QQ / QC / inv | implicit: QQ / QC / inv |
|---|---|---|
| EEA | `3n²` / – / `6n` | `n²` / – / `n` |
| Chien + Forney | – / `mn` / `m` | `2mn` / `mn/2` / `m` |
| total | `3n²` / `mn` / `m + 6n` | `2mn + n²` / `mn/2` / `m + n` |

Over `GF(2^b)` QC multiplications are CNOT-only, so **explicit access wins** for `n ≪ m`
(`2mn ≈ 573 k` QQ products would cost ≈ 30 M Toffolis in the implicit model).

### 3.5 `GF(2^m)` arithmetic (§"Improved arithmetic circuits")
* Multiplication (Toffoli/CNOT; PCTOF/CNOT): `m=10`: 39/738 (39); `m=11`: 47/1278 (46);
  **`m=12`: 51/1506 (51)**. Built from Maslov–Yosri–Gavinsky (2511.20618) modified Karatsuba over a
  chosen irreducible polynomial, optimised for `∞:1` Toffoli:CNOT, then rank-reduced in the
  `m²`-dimensional space of degree-2 Boolean forms (any set of PCTOFs = `k × m²` matrix; rank =
  minimum PCTOF count).
* PCTOF = multi-target Toffoli whose two controls are parities of disjoint sets (one lattice-surgery
  cycle each with enough ancilla).
* **MBUC of a product** `|x⟩|y⟩|xy⟩ → |x⟩|y⟩`: X-measure the product register (outcome `c`), then
  the phase `(−1)^{c·bin(xy)}` is a bilinear form in `(x, y)` → fixed by CZ gates between `x_i` and
  `y_j` for pairs where `x^{i+j} mod p(x)` has a `1` at a position where `c_t = 1`; depth
  `⌊m/2 + 0.5 log² m + 3 log m − 11⌋`, `≤ m²/4 + O(m log² m)` Cliffords. Qualtran `GF2MulMBUC`.
  **Zero Toffolis** — this is why "both factors stay in memory" matters so much in the design space.
* Inversion: Itoh–Tsujii, `O(log b)` multiplications (chain for `2^11 − 1`: 5 products →
  `5 × 63 = 315` in the reference, `5 × 51 = 255` with the tuned multiplier), intermediate products
  kept in scaffold registers (4 × 12 = 48 qubits) so the chain can be uncomputed with MBUC.
* Physical layout (for context): `GF2Mul` for `b = 12` fits a `3 × (2.5b+9) = 3×39` lattice-surgery
  region; 1,885 logical qubits → 40×48 yoked cold storage + 3×40 hot; ≈800 k physical qubits.

### 3.6 Resource table (Table "resource_estimates", Qualtran, whole DQI circuit)

| `(m, n, b, r)` | Toffoli | Clifford | qubits |
|---|---:|---:|---:|
| (1023, 60, 10, 496) | 2,764,580 | 38.9 M | 1,364 |
| (1023, 70, 10, 496) | 3,593,114 | 49.1 M | 1,569 |
| (1023, 100, 10, 496) | 6,710,658 | 86.8 M | 2,170 |
| (4095, 60, 12, 2016) | 4,640,644 | 127 M | 1,640 |
| **(4095, 70, 12, 2016)** | **5,717,729** | 152 M | **1,885** |
| (4095, 80, 12, 2016) | 6,922,158 | 179 M | 2,125 |
| (4095, 100, 12, 2016) | 9,745,253 | 241 M | 2,606 |

Qubits scale as `2nb + O(log n)`: `(1885 − 1640)/10 = 24.5 ≈ 2b` per unit of `n` ✓. Gu et al.
re-ran the released code and attribute ≈5.0–5.1 M Toffolis to the decoder, of which the forward +
reverse EEA is ≈3.8 M and the locator solve alone ≈1.9 M.

---

## 4. Gu, Kemeny, Yelin, Lukin — *Discovering state-of-the-art quantum circuits with large language models*, arXiv:2610.22367 (Oct 2026), SI §"Reed–Solomon decoding for OPI" [PAPER]

Code/evaluator: github.com/andigu/uncompute (different field polynomial 4331 and a fixed mask —
constants not transferable [SIBLING]). Result: **442,397 Toffolis, 1,837 peak qubits**, 7 wrong
signs in 100,000 on the DQI distribution (vs. their baseline run of Khattar's code: 5.1 M / 1,938
peak). This is the most detailed published description of a sub-million-Toffoli decoder and the
conceptual source of several leaderboard techniques.

Their acceptance rule is different from Kaggle's (≤ 100 wrong signs in 100,000 → `ε ≤ 2.4×10⁻³` at
97.5 %, objective loss `≤ 4ε⟨f⟩`), so their circuit targets a looser ε than the competition rewards.

Techniques, in order:
1. **Berlekamp–Massey instead of EEA** for the key equation: `≈140 k` Toffolis vs `≈1.9 M` for
   the locator solve. Round `r = 1..70`: `τ̃ = zτ`, `Δ = Σ_{i≤min(deg σ, r−1)} σ_i S_{r−i}`, then
   (`Δ = 0`): `(σ, τ̃, δ, d+1)`; (`Δ ≠ 0, d ≥ 0`, replace): `(σ − (Δ/δ)τ̃, σ, Δ, −d)`;
   (`Δ ≠ 0, d < 0`, retain): `(σ − (Δ/δ)τ̃, τ̃, δ, d+1)`. Ties (`d = 0`) are resolved as *replace*
   (textbook retains) to shrink history.
2. **Rescaled shared update**: replace branch computes `τ − α⁻¹σ = −α⁻¹(σ − ατ)` (same roots), so
   both branches are one multiply-add on swapped registers with multiplier `α` or `α⁻¹`; the
   displaced template is never stored. Invariant **`σ_0 δ = 1`** → `δ` is never stored; each round
   forms `Δσ_0 = α` and inverts it; a controlled select picks `α` or `α⁻¹`.
3. **History reconstruction**: replace rounds are reversible from `σ_0 = Δ⁻¹`; retain rounds must
   push `Δ` on a stack (worst case 35 entries = 665 qubits). Retain rounds are rare on the DQI
   distribution; **one stack entry (19 qubits)**; overflow probability `1.0×10⁻⁴`. Temporary
   discrepancy registers are erased by MBU and recomputed on the reverse pass.
4. **Adaptive coefficient ranges**: classical simulation picks a per-round cutoff `k`; only
   `σ_0..σ_k` are updated (locator degree ≈ `r/2` typically). Combined failure probability of 3+4
   over 4×10⁸ samples: **`1.4×10⁻⁴`** (≈14 expected failing shots on Kaggle → `R` penalty ≈ 4 %).
5. **In-place evaluator**: normalize `σ_0 = 1`; `ω_i = S_{i+1} + Σ_{j=1}^{i} σ_j S_{i−j+1}` equals
   the overwritten syndrome symbol plus a function of earlier ones → overwrite `S_1..S_35` with
   `ω_{<35}` reversibly (saves 420 qubits); extending the map to all 70 symbols zeroes `S_36..S_70`
   whenever the decode is correct, giving **free workspace inside the syndrome register**.
6. **Phase-only recovery**: `⟨c_j, e_j⟩_2 = Tr(μ_j e_j)` for a unique `μ_j ∈ F_{2^12}`; the part of
   the phase linear in the syndromes is applied offline with Clifford `Z` ("cancels the mask at 71
   positions"), leaving residual constants `μ̃_j` at 4,024 positions. At a root,
   `Tr(μ̃_j e_j) = Tr(ν_j ω(β_j)/σ'(β_j))` with `ν_j = μ̃_j κ_j` — no `e_j` is materialized.
7. **Precomputed reciprocal**: one polynomial `Ψ` with `Ψσ' ≡ 1 (mod σ)` evaluates to `1/σ'` at all
   roots, so the phase bit is `Tr(ν_j ω(β_j) Ψ(β_j))`, bilinear → 12 Toffolis (each a product of two
   CNOT-computed parities), plus an 11-Toffoli zero test: **23 Toffolis per position, 4,024
   positions ≈ 92.6 k**. `Ψ` by a *half-degree* EEA: in characteristic 2, `σ = E² + zO²` with
   `E_i = √σ_{2i}`, `O_i = √σ_{2i+1}` (`deg ≤ 17`), `σ' = O²`; `AE + BO = 1` ⇒ `Ψ = B² + zA²`;
   squares/square roots are CNOT-only. `A, B` are stored in the zeroed `S_36..S_70` words.
8. Everything is reversed after the scan (reverse Euclid, reverse product, reverse BM).

[INFERENCE] Peak 1,837 qubits comes from the BM stage (`σ`, `τ`: 2 × 36 words = 864 qubits beside the
840 syndrome qubits, plus temporaries); the leaderboard's 883–900-qubit designs [SIBLING] remove that
by solving the key equation **in place in the syndrome register** (continued-fraction partial
quotients of `S(z)` overwrite the syndrome words; "consecutive levels share one power-series
reciprocal"), which the Gu design does not do.

---

## 5. Babbush, Zalcman, Gidney, Broughton, Khattar, Neven, Bergamaschi, Drake, Boneh — *Securing Elliptic Curve Cryptocurrencies against Quantum Vulnerabilities*, arXiv:2603.28846 (PRX Quantum 7, 031001, 2026) [PAPER]

Where kickmix circuits were introduced (Appendix "Zero-Knowledge Proof of Resource Costs"). Only the
circuit-technique content is relevant here:
* **Kickmix** = classical reversible gates + measurement-based uncomputation via X-basis
  measurements + diagonal phase gates for the fix-ups; classically simulable; name from phase
  *kick*back and *mix*ing of classical states.
* **MBUC**: ancilla `q` holding `f(k)`; X-measure: `|+⟩` → erased, `|−⟩` → erased with
  `(−1)^{f(k)}` kickback; the correction is a function of the surviving data; "usually slightly
  smaller, sometimes much smaller" than computing `f` (cites Gidney 2018 halving, Berry et al. 2019
  lookup uncompute).
* **Approximate correctness is enough**: "a superposition with 1 % of points in the wrong place
  will cause the algorithm to fail at most 1 % of the time" (Proos–Zalka/Zalka). Fiat–Shamir fuzz
  testing: 9,024 pseudo-random inputs from SHAKE256(circuit bytes) certify `ε < 1 %` at `2^{−130}`;
  the Kaggle verifier is the same construction with a private salt and `N = 102,400`.
* Point-addition circuits: windowed (`w = 16`) in-place additions with three table lookups each,
  `3·2^w` Toffolis per window, lookups uncomputed by MBUC, qubit-recycled QFT; low-qubit variant
  ≤ 2.7 M non-Clifford / 1,175 qubits, low-gate variant ≤ 2.1 M / 1,425. Toffoli counts are
  **averages over executed test cases** because classically-conditioned instructions may not run —
  the same convention the dqi verifier uses (`T` = mean executed).
* Techniques that carry over to `GF(2^12)`: MBUC of lookups/products, windowing (QROM-style lookup
  of `2^w`-entry tables costs `≈2^w` Toffolis — for 12-bit inversion that is 4,095, worse than
  Itoh–Tsujii's 255–315, so windowing is *not* attractive for field inversion here [INFERENCE]), and
  the practice of accepting input-dependent failures that are rare under the test distribution.

---

## 6. Other DQI follow-ups that touch the decoder or ε (read at abstract/section level)

| paper | relevance |
|---|---|
| Chailloux & Tillich, *The quantum decoding problem*, 2310.20651 (read: abstract/intro) | Quantum decoding with errors in superposition; polynomial-time for small noise, information-theoretic regime beyond classical. Background for the Regev-reduction view of DQI; no circuits. |
| Chailloux & Tillich, *Quantum advantage from soft decoders*, 2411.12553 | Koetter–Vardy soft decoding improves DQI/OPI for `ISIS_∞`; generic syndrome-decoding → coset-sampling reduction. Shows the decoder may exploit the non-uniform per-symbol error prior; not used by the benchmark (uniform nonzero values). |
| Patamawisut et al., *Quantum circuit design for DQI*, 2504.18334 | Reversible Gauss–Jordan (ISD) decoder, ≤ 30-qubit simulations. Not competitive for RS. |
| Rosmanis, *A nearly linear-time DQI algorithm for OPI*, 2601.15171 | Sidesteps quadratic Dicke-state preparation; concurrent with Khattar et al.; algorithmic, not a decoder circuit. |
| Gu & Jordan, *Algebraic geometry codes and DQI*, 2510.06603 | Hermitian codes: block length `q³` over `F_{q²}` → ≈1/3 fewer qubits per symbol; Gu et al. 2610.22367 also optimise a Hermitian decoder. Different benchmark. |
| Gao et al., *Weighted performance bounds for DQI with imperfect decoding*, 2604.15025 | Tightens the Nature paper's `max_k ε_k` bound by weighting with `w_k²`; conceptually the same weighting the Kaggle ε already uses. |
| Jo 2607.16541; Horinaga–Yamakawa 2607.14650; Sun–Wootters 2604.09533 | Worst-case / Sun–Wootters-distribution samplers via list decoding; beyond the benchmark's contract. |
| Bollmann–Hess, *Benchmarking techniques for DQI*, 2603.24441 | Greedy LDPC decoder circuits for max-2-XORSAT; not RS. |
| Kramer et al. 2610.02145, 2603.04540, 2606.13570; Marwaha et al. 2509.14443; Anschuetz et al. 2509.14509 | Complexity/approximability of DQI; no circuit content. |

---

## 7. Classical RS decoding algorithms, judged for reversible implementation

Setting: `2t = 70` syndromes, `t = 35`, `q = 2^12`, `m = 4095` positions, uniqueness guaranteed.

| algorithm | arithmetic (classical) | reversibility issues | status in the literature |
|---|---|---|---|
| **Sugiyama / EEA** on `(z^{70}, S)` | ≈`3t²` ≈ 3.7 k mults; variable quotient degrees and iteration count | Proos–Zalka synchronized architecture: `6t+5 = 215` cycles each touching all `n+3` slots ⇒ `3n²` QQ mults (`×4` over the classical count) plus CSWAP/controlled-add overhead; `2nb` space | Reference and Khattar explicit model (§3) |
| **Berlekamp–Massey** | `2t` rounds, ≈`t` mults each (discrepancy) + ≈`t` for the update ⇒ ≈`2·70·36 ≈ 5 k` mults; one inversion per nonzero-discrepancy round | Overwrites template/discrepancy → naive history of 35 polynomials; Jordan et al. reversible BM needs `2(n+ℓ)b + n + log ℓ ≈ 2.6 k` qubits [SIBLING confirms ≈2,600]; Gu et al. fix it with rescaling (`σ_0δ = 1`), tie → replace, 1-entry stack, cutoffs (≈140 k Toffolis for the solve) | Gu et al. (§4) |
| **Inversionless BM / Sarwate–Yan modified EEA** (0906.3778) | exactly `2t` fixed iterations, cross-multiplication `V ← U_{2t} zV − V_{2t−1} U`, `X ← U_{2t} zX − V_{2t−1} W`, swap when `V_{2t−1} ≠ 0 ∧ δ < 0`; outputs `z^{2t−ν}Λ`, `z^{2t−ν}Ω` (scalars cancel in Forney) | No degree tracking, no inversions — ideal control structure; but in-place scaling of a register by a *quantum* scalar is not cheaply reversible (needs the inverse to undo), which is why Khattar's Dialog keeps a division (`c = g_0/f_0`) per step instead | Hardware literature; structurally identical to Bernstein–Yang divsteps |
| **Bernstein–Yang divstep / Dialog** | `2n = 140` constant-time steps, ≈`n/2`–`n` mults each ⇒ `n²` QQ mults; one inversion per step | Reversible by construction (each freed slot stores the step's coefficient); but `σ` is only implicit → Chien needs `2mn` QQ mults, or `+432` qubits to materialize `σ` [INFERENCE] | Khattar implicit model (§3.3) |
| **Peterson–Gorenstein–Zierler** (solve the `t×t` Hankel system directly) | `O(t³)` ≈ 43 k mults with pivoting | Pivoting in superposition is hopeless; Gu et al.'s LLM search also tried a PGZ family and did not win with it | not competitive |
| **Gao / Welch–Berlekamp (syndrome-less)** | needs the received word of length `m` | Not applicable: the circuit only receives the 70-symbol syndrome | — |
| **Hankel/Schur, continued fraction of `S(z)`** | the Euclidean remainder sequence = partial quotients of the continued fraction of `S(z)/z^{70}`; `t` levels of degree-1 steps in the generic case | Can be organised to overwrite the syndrome words with the partial quotients **in place** ("the decoder needs almost no workspace beyond its 840 input qubits"), then converted in place to `(σ, Ω)` [SIBLING, leaderboard lineage; no paper] | leaderboard frontier (883–900 q) |
| **Chien search** | `m` evaluations; in-place constant scaling `σ_k ← σ_k α^{−k}` = CNOTs; zero test 11 Toffolis | fully reversible, cheap | all designs |
| **Forney** `e_j = κ_j ω(β_j)/σ'(β_j)` | 1 inversion + 1 mult per *error*; in superposition: per *position* | 315–351 Toffolis/position in the reference (1.44 M total). Avoid via **phase-only trace** + **precomputed reciprocal `Ψ`** (23/position) | Gu et al. |

Important structural facts for any design:
* The forward solve must be undone (stage 3): the EEA/BM state is a bijective image of `s`, so it
  cannot be erased by MBUC without recomputing it; you pay the solve twice (or once forward + once
  backward with the same count). Only *out-of-place products whose factors remain* and
  *recomputable temporaries* (Gu's discrepancies) are MBUC-free.
* In characteristic 2: `σ'` = odd-index coefficients shifted (`σ' = O²`), squaring/square root/
  Frobenius/multiplication by constants/trace are `F_2`-linear → CNOT only. Trace functionals turn
  any parity `c·bin(e)` into `Tr(μ e)` with `μ` computable classically from `c` (dual basis).
* Normalization freedom: `σ` is needed only up to scale (roots), and `ω/σ'` is scale-invariant if
  both are scaled together.

---

## 8. `GF(2^m)` arithmetic circuits, with `m = 12` numbers

### 8.1 Multiplication (`|x⟩|y⟩|0⟩ → |x⟩|y⟩|xy⟩`, no ancilla)

| construction | Toffolis for `m = 12` | source |
|---|---:|---|
| schoolbook (Cheung–Maslov–Mathew–Pradhan 0710.1093): `m²` Toffolis, ≤ `2m²−1` gates, `m²+m−1` for trinomials/all-one polynomials, LNN depth `O(m)` | 144 | [PAPER] |
| van Hoof 1910.02849 space-efficient Karatsuba: `3^k` Toffolis for `m = 2^k`, `O(m²)` CNOTs; table: m=2:3, 4:9, 8:27, 16:81, 127:2185, 256:6561 | ≈54–63 (12 = 3·4 or 2·6 splits; the reference's 63 is such a variant) | [PAPER]; 63 = reference |
| Maslov–Yosri–Gavinsky 2511.20618 (modified Karatsuba, chosen irreducible, templates, rank optimisation) | **51** (Khattar Table: m=10: 39, m=11: 47, m=12: 51; PCTOF 51) | [PAPER] |
| evaluation/interpolation over `F_8` (degree-4 polynomials over `F_8`, 7 points incl. ∞, 6-AND `F_8` products): symmetric bilinear rank **42**; a 99-rank `F_{2^24}` product also used | 42 | [SIBLING, leaderboard claim; consistent with the bilinear-rank view: the minimal number of PCTOFs equals the rank of the bilinear map `F_{2^12} × F_{2^12} → F_{2^12}` over `F_2`, for which `M(12)` via CRT/eval-interp is known classically to be ≤ 42–45] |
| CRT-based multipliers (Kepley–Steinwandt / Parent–Roetteler–Mosca lineage), `O(m 2^{log m})` | similar order; CNOT-heavy | cited in 2511.20618 |

Squaring, Frobenius `x ↦ x^{2^i}`, multiplication by a known constant, trace, basis change: all
`F_2`-linear → CNOT only (`≤ m² − 1` CNOTs, or `≤ m²/log m` with optimal linear synthesis). The
benchmark fixes the I/O basis (polynomial basis of 4179), but any internal basis (normal, tower
`F_{(2^6)^2}`, `F_{(2^4)^3}`, `F_{(2^3)^4}`) is reachable by free linear maps.

### 8.2 Inversion / division

| method | Toffolis (`m = 12`) | ancilla | notes |
|---|---:|---:|---|
| Itoh–Tsujii / FLT, addition chain for `2^{11}−1` (`l(11) = 5` products), Frobenius free | `5 × 63 = 315` (reference), `5 × 51 = 255`, `5 × 42 = 210` | 48 (4 × 12 intermediates, needed for MBUC uncompute) | Amento–Steinwandt–Roetteler 1209.6348 give `2(⌊log₂(m−1)⌋ + hw(m−1) − 2) m²` Toffolis with schoolbook products including cleanup; Banegas et al. (via 2511.20618 Table II "division [3]"): m=8: 243 T, m=16: 1,053 → 891 (Maslov et al.) with 6 ancilla registers |
| Euclid/Bernstein–Yang GCD division (Banegas et al. 2020/1296 "GCD_DIV", Kim–Hong 2303.06570) | m=8: 2,954 T / 67 q; m=16: 7,594 T / 123 q (Kim–Hong: 3,726 / 64 and 10,190 / 116) → ≈5 k for m=12 | ≈90 | far worse than FLT at this size [PAPER tables] |
| QROM lookup of `x⁻¹` | ≈4,095 (unary iteration) or SelectSwap `≈2^{12}/λ + λ·12` ≈ 400 | `λ·12` | worse than FLT [INFERENCE] |
| subfield/tower `F_{(2^6)^2}`: `a⁻¹ = a^{64}·N(a)⁻¹`, `N(a) = a^{65} ∈ F_{2^6}` (6 quadratic forms, ≲ 30–36 Toffolis), `N⁻¹` in `F_{2^6}` by Itoh–Tsujii (chain for 31: 3 products × `M(6) ≈ 15–18`) or 64-entry lookup, then `a^{64}·N⁻¹` (2 `F_{2^6}` products) | **≈ 110–150** | ≈ 24–36 | [INFERENCE]; the leaderboard's "tower norm trick (norm of inverse = inverse of norm)" [SIBLING] is this idea |
| Taguchi–Takayasu 2023 (addition-chain ITA with fewer ancillas; later with CRT multipliers) | not retrievable (IACR behind bot-check); described in 2511.20618 as "reduce the space required for inversion at the cost of slightly increasing the Toffoli count" | | |

Multiplication-by-inverse vs. direct division: Khattar's Dialog gives direct division at `4n²`
polynomial-level cost; at the *field-element* level, FLT inversion then multiply is the practical
choice (Maslov et al. Table II is exactly "FLT-based division").

### 8.3 Cost accounting idioms (from 2510.10967 / 2603.28846 / verifier)
* Out-of-place product: `M` Toffolis to compute, **0** to uncompute if both factors survive (X-measure
  + CZ fix-up; the fix-up is conditioned on the measurement record and *executes* only for the
  outcome bits that are 1, so its Clifford cost is halved on average — Toffoli cost is zero
  regardless).
* Controlled product / controlled add: a 12-bit controlled XOR costs 12 Toffolis; controlled
  multiplier ≈ `M + 12` (reference: 75 for the controlled multiply [SIBLING]).
* Zero test of 12 bits: 11 Toffolis (AND ladder), uncompute by MBUC for free.
* 12-bit CSWAP: 12 Toffolis.
* Executed-count semantics: Toffolis inside classically-controlled blocks (controlled on `c` bits or
  on measurement outcomes) count only when they run; the reference's one skipped Forney step per
  shot (`P(e_j = 0) = 1/4096` at a flagged position) is why its mean `T` is 353 below the static
  count [SIBLING].

---

## 9. Where the reference spends its budget (reconstruction) [INFERENCE unless marked]

* Chien/Forney: `4095 × 351 = 1,437,345` Toffolis (25 %) — of which inversions
  `4095 × 315 = 1.29 M` (22.5 % [SIBLING]). The remaining 36/position ≈ zero test (11) + controlled
  copies/products.
* EEA forward + reverse: `5,725,461 − 1,437,345 = 4,288,116` → 2.14 M per direction → ≈9,660 per
  cycle over 222 cycles. Of that, products `73 × 63 = 4,599`, leading-coefficient inversion + quotient
  product ≈ 378 (`div scaffold 378` [SIBLING]), controlled adds/subs ≈ 876, `shift_b` CSWAPs ≈ 876
  (8.3 % of total [SIBLING]), `swap_a_and_b` ≈ 876 (6.9 % [SIBLING]), unary-iteration/pointer logic
  for the rest.
* Qubits: 840 (input) + 876 (`reg_b`) + 36 (pad: `3 × 12` in `reg_a`) + 40 (five 8-bit pointers) +
  11 (flag, counter, halting counter) + 90 peak temporaries (48 inversion scaffold + product
  registers) = 1,893 [SIBLING anatomy].
* Score: `1.1913 × 1893² × 5,725,108 = 2.444×10¹³` [NUM; matches the verifier's reported baseline].

---

## 10. Design space for the reversible RS decoder under `R(ε⁺)·Q²·T`

### 10.1 What the metric rewards
* `Q` is squared and has a hard floor of 840 (the input). The reference sits at 2.25× the floor;
  the leaderboard at 1.05–1.07×. Going from 1,893 to 892 qubits alone is a **4.5× score factor**,
  larger than any arithmetic trick. Every qubit at `Q ≈ 890` is worth ≈0.22 % of score; a 12-qubit
  word ≈ 2.7 %; one failing shot ≈ 0.46 % ⇒ **a 12-qubit register is worth ≈ 6 failing shots** or
  ≈ 2.7 % of `T`.
* `T` is a *mean*: conditional branches that rarely execute are nearly free; measurement-conditioned
  fix-ups are half price on Cliffords and free on Toffolis when MBUC applies.
* `R` has a floor of 1.1913 and is flat: `ε_s ≤ 10⁻⁵` (≈1 shot) costs 0.5 %, `10⁻⁴` costs 3 %,
  `10⁻³` costs 17 %, `10⁻²` costs 60 %+. Spend ε only on `≤ 10⁻⁴` events.

### 10.2 Axis 1 — how many errors to correct: do not trade ℓ
`ε(ℓ') = P(w > ℓ')`: `ℓ' = 34 → 2.8 %` (`R ≈ 3.9`), `ℓ' = 33 → 12 %` (no score). Not viable. The
converse is free: the distribution never samples `w ≤ 18` (`3.5×10⁻⁶` → 0.36 expected shots), so a
decoder may assume `deg σ ≥ 19`, use per-round coefficient cut-offs (Gu: locator degree ≈ `r/2`
after `r` rounds), and skip "zero syndrome"/trivial branches entirely [INFERENCE; the leaderboard
decoder is reported to be wrong at `w ≤ 16` and exact at 17–35 [SIBLING]].

### 10.3 Axis 2 — key-equation solver
| option | Toffolis (solve + unsolve) | qubits beyond 840 | ε cost |
|---|---:|---:|---|
| synchronized EEA (reference) | ≈4.3 M (63-T mult) / ≈3.5 M (51-T) | ≈1,050 | 0 |
| Dialog divsteps + materialize `σ` | ≈ `2 × (n² + n²) × 51 ≈ 1.0 M` + overhead | `2nb + 432 ≈ 1,300` | 0 |
| rescaled BM (Gu) | ≈ `2 × 140 k = 280 k` + evaluator/`Ψ` passes | ≈ 1,000 (peak 1,837 total) | `1.4×10⁻⁴` |
| in-place continued fraction / Hankel–Schur (leaderboard) | `extract 87 k + synthesis 45 k + convert 69 k` and mirror ≈ 440 k total incl. scan [SIBLING] | **≈ 40–60** | ≈ 0–10⁻⁵ (“histories with ≤ 2 gaps exact; rarer patterns unhandled”) |

[INFERENCE] The in-place solve is possible because the generic Euclidean path on a random-looking
`S(z)` has all quotient degrees 1 (probability `1 − 1/q` per step), so the remainder sequence is
a continued fraction with `≈w` degree-1 partial quotients, each determined by two leading
coefficients; writing the partial quotients over the consumed syndrome words is a bijection and
therefore reversible with `O(1)` extra words. Non-generic steps (a vanishing leading coefficient,
probability `≈ 1/4096` per step, `≈ 35/4096 ≈ 0.85 %` per shot) must be handled explicitly — the
leaderboard note "missing leading coefficient repaired by a paired 3+1 step; histories with ≤2 gaps
exact" [SIBLING] is exactly that; leaving two or more gaps unhandled costs `≈ C(35,2)/4096² ≈
3.5×10⁻⁵`, i.e. ≈ 4 shots — acceptable.

### 10.4 Axis 3 — error-value recovery
| option | per position | total (4,024–4,095 positions) | qubits |
|---|---:|---:|---:|
| Forney with Itoh–Tsujii inversion (reference) | 351 | 1.44 M | 48 scaffold + 12–24 |
| Forney with tower inversion | ≈ 150–170 | ≈ 0.65 M | ≈ 36 |
| lazy buffer (process ≤ K flagged positions per chunk, fail on overflow) | 351 only `35K` times | e.g. 35 chunks × K=7: 245 inversions (77 k), `ε = 1.8×10⁻⁴` | +168 (buffer) → net ≈ neutral vs. tower inversion [NUM] |
| **phase-only trace with precomputed `Ψ`** (Gu) | **23** (11 zero-test + 12 bilinear) | **≈ 92.6 k** | 0 extra (A, B live in zeroed syndrome words) + 2 words |
| + classical mask projection (skip 70–71 positions) | — | −1.6 k | 0 |

The `Ψ` approach also removes the 48-qubit scaffold and all 4,095 inversions; its cost is one
half-degree EEA (degree ≤ 17 operands, ≈ `3·17²·51 ≈ 44 k` forward + same reverse [INFERENCE],
consistent with the leaderboard's `synthesis 44.7 k / unsynthesis 53.8 k` stage sizes [SIBLING]).
Scan floor: the 11-Toffoli zero test per position is hard to beat (a 12-input OR needs ≥ 11
two-input ANDs); the 12 bilinear Toffolis could shrink by choosing the basis so that `Tr(ν_j x y)`
has lower rank, but the rank of a nondegenerate trace form over `F_2` is 12, so 23 is essentially
tight for a per-position Toffoli test [INFERENCE]. Reducing the number of scanned positions below
4,024 requires knowing something about the error support, which the syndrome alone gives only via
`σ`; no cheaper global root-finding (e.g. factoring `σ` over `F_{2^12}` by Berlekamp/Cantor–
Zassenhaus) is reversible-cheap at degree 35 [INFERENCE].

### 10.5 Axis 4 — field arithmetic
Products: 63 → 51 (published) → 42 (eval/interp over `F_8`, leaderboard claim). Inversions: avoid
them (one per BM round/divstep is unavoidable in the solve: ≈35–70 per direction; use the cheapest
tower/ITA variant, ≈ 150–255 each). Keep every product's factors alive until it is MBUC-erased.
Use PCTOF-style circuits (parities computed by CNOT, one Toffoli per rank-one term). Squares/roots/
Frobenius/trace/basis changes are free.

### 10.6 Axis 5 — qubit budget (the dominant term)
* Floor: 840 input + ≥ 1 word of scratch for a product/zero-test + flags. Realistic in-place
  designs: 883–900 [SIBLING]; the frontier claims each removed qubit is worth 0.23 %.
* Techniques: (1) overwrite syndrome words with the partial quotients / `ω` / `A,B` (Gu's in-place
  evaluator + "zeros become workspace"); (2) borrow wires: 3-input ANDs via HMR + CCZ on borrowed
  qubits (manwithacat's 892) [SIBLING]; (3) measure-and-recompute a flag instead of storing it
  (wahyurahmaniar's P6 flag: 23 T + CZ for −1 qubit) [SIBLING]; (4) classical pre-/post-processing of
  anything linear in `s` (mask projection); (5) never materialize `e_j`.
* Negative results: explicit `(σ, Ω)` copies (+852), Dialog materialization (+432), lazy-Forney
  buffers (+168), reversible BM with history (+700–800) all lose to the in-place approach because of
  the square.

### 10.7 Design points and estimated scores [NUM for the arithmetic; the (Q, T) pairs are PAPER/SIBLING where marked, else INFERENCE]

| design | Q | T (mean) | k (expected) | score | vs baseline |
|---|---:|---:|---:|---:|---:|
| A. reference (EEA + Forney/ITA) [PAPER/SIBLING] | 1,893 | 5,725,108 | 0 | 2.44×10¹³ | 1.0× |
| B. A + 51-Toffoli multiplier (Khattar) | 1,893 | ≈5.2 M | 0 | 2.22×10¹³ | 1.1× |
| C. B + tower inversion + MBUC-clean EEA | ≈1,870 | ≈4.4 M | 0 | 1.83×10¹³ | 1.3× |
| D. C + EEA trimmed to the `2nb` floor (1,680 + pointers) | ≈1,740 | ≈3.8 M | 0 | 1.37×10¹³ | 1.8× |
| E. Dialog EEA + materialized σ (Clifford Chien) | ≈2,170 | ≈2.2 M | 0 | 1.23×10¹³ | 2.0× |
| F. Gu et al. rescaled BM + Ψ scan [PAPER] | 1,837 | 442,397 | ≈7–14 | 1.8×10¹² | 13× |
| G. leaderboard in-place Schur + Ψ scan [SIBLING] | 892 | 403,587 | 0 | 3.83×10¹¹ | 64× |
| H. G with further in-place compaction and rank-42 products | ≈870 | ≈350 k | 0 | 3.2×10¹¹ | 77× |
| I. hypothetical near-floor (`Q = 852`, `T = 250 k`, 10 failing shots) | 852 | 250 k | 10 | 2.2×10¹¹ | 110× |

Reading of the table: the arithmetic-only improvements (B–D) are worth at most ≈2×; the qualitative
changes — BM/continued-fraction solve, phase-only trace recovery with a precomputed reciprocal, and
working inside the syndrome register — are worth 13–64×. Beyond G the remaining levers are
≈5 % of `Q` (toward 840–860) and ≈1.5× of `T` (toward the ≈93 k scan floor plus a ≈150 k solve
and its reversal), i.e. perhaps another 1.5–2×, with any ε spent only on `≤ 10⁻⁵`-probability
events.

### 10.8 Suggested path (ordered by expected value)
1. Implement the solve **in place** on `S0..S69` (continued-fraction/EEA with degree-1 generic
   steps; explicit handling of one or two "gap" steps; everything else fails on a `≲ 10⁻⁵` set).
2. Convert in place to `(σ, ω)` with `σ_0 = 1` (Gu's triangular map), leaving the upper 35 words
   zeroed as workspace.
3. Compute `Ψ ≡ 1/σ' (mod σ)` by the half-degree EEA on `(E, O)`; store `A, B` in the zeroed words.
4. Scan 4,024 positions with CNOT-only updates, an 11-Toffoli zero test, and the 12-Toffoli bilinear
   trace `Tr(ν_j ω(β_j) Ψ(β_j))` applied only under the flag; absorb 70–71 positions classically.
5. Reverse 3, 2, 1. Use 42–51-Toffoli products, MBUC for every surviving-factor product, tower-field
   inversions where unavoidable, borrowed-wire ANDs, measured-and-recomputed flags.
6. Verify locally with the official verifier at 102,400 shots and several salts; target `k ≤ 2`.

---

## 11. Flags and open questions
* [INFERENCE] The per-cycle Toffoli decomposition of the reference EEA (§9) is reconstructed from
  totals and the sibling anatomy, not from the paper.
* [INFERENCE] Tower-field inversion cost (≈110–150) and the eval/interp rank-42 multiplier are not
  in any paper read here; the latter is a leaderboard claim consistent with known bilinear-rank
  bounds for `M(12)`.
* [INFERENCE] The in-place continued-fraction solve is reconstructed from leaderboard notes; no
  paper describes it. Its exact failure set (which "gap" patterns are handled) determines `k`.
* Not retrieved: Banegas–Bernstein–van Hoof–Lange (IACR 2020/1296) and Taguchi–Takayasu (IACR
  behind a bot-check); their `m = 12`-relevant numbers were taken from Kim–Hong's and Maslov et al.'s
  comparison tables and from Khattar's prior-art table.
* Open: can the per-position zero test be amortized (e.g. testing `σ` at several points with a
  shared multi-output linear map and a single multi-bit OR tree) to go below 23 Toffolis/position?
  Can the solve's `≈35` field inversions be replaced by a single inversion via the
  `σ_0 δ = 1`-type invariants plus cross-multiplication while staying reversible?
