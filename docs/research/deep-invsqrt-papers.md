# Deep read: the arithmetic behind the `invsqrt` benchmark

Scope: the primary literature behind Benchmark I ("1/√x phasing for Coulomb
simulations") of the Google Quantum AI "Verifiable Quantum Circuit Compilation"
competition. This note goes deep on the *arithmetic*: the exact recurrences,
bit widths, iteration counts, initial-guess construction, error control, and
Toffoli/qubit formulas in each paper, followed by a quantitative design space
for a kickmix circuit under the `Q × (Toffoli + T/4)` metric. The broad
bibliography lives in `papers.md`; this file overlaps it only where needed.

All PDFs/sources were downloaded to
`/tmp/claude-0/-home-user/af1e8b3b-1af8-51dd-9e8d-ec3f80eabc0b/scratchpad/papers/<arxivid>/`
and read in full for the sections cited. Statements tagged **[inference]** are
my own derivations/estimates, not claims made by the papers. Numbers tagged
**[computed]** come from
`/tmp/claude-0/-home-user/af1e8b3b-1af8-51dd-9e8d-ec3f80eabc0b/scratchpad/scripts/invsqrt_numerics.py`
(Remez minimax fits, Newton error maps, a truncated-multiplier cost model).

---

## 0. The benchmark contract (what "exact" actually means)

Source: Khattar, Rubin, Gidney, Broughton, Low, Babbush, *Leveraging verifiable
structure in quantum circuits to find more efficient compilations with agentic
AI*, arXiv:2610.23832 (Sec. III.A and App. B). This is the authoritative spec.

* Map: `|x⟩|0⟩ ↦ exp(2πi β/√x) |x⟩|0⟩`, β = 1, for every integer
  `x ∈ [1, 3(2^10 − 2)^2] = [1, 3 133 452]`; one named register `x` of
  `2n_p + 2 = 22` qubits; all other qubits are scratch and must return to |0⟩.
* The check is **not** bit-exactness of a register; it is a *phase tolerance*:
  the tracked phase θ(x) (turns, mod 1, 64-bit fixed point) must satisfy
  `|θ(x) − β/√x| ≤ tol(x) = 2^-24 · β/√x` turns, i.e. **2^-24 relative error in
  the phase**, on every one of 3 133 452 inputs × 64 shots (200 540 928 shots,
  PRNG seeded from the circuit hash) with **zero failures**. The randomness is
  only in HMR/R measurement outcomes, so a circuit whose measurement-based
  uncomputation is correctly fixed up is deterministic in θ.
* Because `1/√x_max = 5.65×10^-4`, the *absolute* phase tolerance ranges from
  `2^-24` turns (x = 1) down to `2^-24/√3 133 452 = 3.37×10^-11 = 2^-34.8` turns
  (x = x_max). **[computed]**
* Score `S = Q × C`, `C = Toffolis + T/4` (mean per shot). CSWAP = 1 Toffoli.
  Z_POW with Clifford angle is free; T-angle costs 1 T; each of the `n_rot`
  finer Z_POW rotations is priced analytically at `0.56 log2(1/ε) + 5.3` T
  (Kliuchnikov et al. mixed fallback synthesis), with
  `ε = π (min_x tol(x) − |error(x)|) / n_rot` — i.e. the arithmetic error
  *eats the rotation budget*. For n_rot ≈ 24–37 this is ≈ 27 T ≈ 6.8
  Toffoli-equivalents per rotation **[computed]**: 24 rotations ≈ 162, 30 ≈ 204,
  37 ≈ 253 Toffoli-eq. The baseline's `C − Toffolis = 7988 − 7735 = 253`
  matches 37 rotations exactly.

### Baseline (reference) circuit, n_p = 10: Q = 260, 7 735 Toffoli, 1 T, 37 rotations, C = 7 988, S = 2.08×10^6, worst relative error 2.84×10^-8 = 2^-25.07 (at x = 2 588 411)

Stage-by-stage Toffoli counts, all from App. B of 2610.23832 (forward pass):

| stage | what | Toffolis (n_p = 10) |
|---|---|---|
| normalize | strip leading zero *pairs*: n_p clean ANDs into unary flags f_k + controlled cyclic lane rotations, `n_p(n_p+1)` CSWAPs; total `n_p(n_p+2)` | 120 (reverse: 110, flags erased by measurement) |
| QROM | 4 cubic polynomials selected by top 3 bits of x_norm; 2 ANDs + CNOT fan-out of 4×17-bit coefficients | 2 |
| Δx bit | `Δx_11 = b13 ∧ b11`, other Δx bits read straight from x_norm | 1 |
| Horner | in place: `c2 −= T(c3Δx)`, `c1 −= T(c2Δx)`, `c0 −= T(c1Δx)`; 14-bit Δx × 17-bit coefficient, truncated | 1 071 (≈ 357 each) |
| square | `T(y0²)` into 28 bits (diagonal bits by CNOT, cross terms row by row) | 442 |
| mantissa mult | `z = T(x_norm · T(y0²))`, 22 × 28 → 30 bits | 1 043 |
| 3 − z | X gates + add `(3≪28)+1` | 28 |
| final NR mult | `p = T(y0 · z)` 17 × 30 → 30 bits | 867 |
| denormalize | `y1 = p ≪ s`, unary-controlled cyclic shifts, `30 n_p` CSWAPs | 300 |
| phase | one Z_POW per bit of y1, `F = 30 + n_p = 40` bits → 3 Clifford/T + 37 rotations | 0 Toffoli (≈253 Toffoli-eq) |
| uncompute | everything in reverse, row ANDs and flag ANDs erased by measurement | ≈ 3 861 |

Register widths used: 14 bits of Δx, 17 fractional bits for coefficients and
Horner intermediates, 28 fractional bits for y0², 30 qubits for z and 3−z, 30
for p, 30 + n_p = 40 for y1, one shared 30-qubit scratch register for multiplier
rows. **Multiplications are ≈ 88 % of all Toffolis; the Newton step alone
(square + 2 multiplies + subtract = 2 380 forward) is 61 % of the forward
arithmetic.** [computed from the table]

---

## 1. Rubin, Berry, Malone, White, Khattar, DePrince, Sicolo, Kühn, Kaicher, Lee, Babbush — *Quantum computation of stopping power for inertial fusion target design*, arXiv:2308.12352, PNAS 121, e2317772121 (2024)

**Contribution.** End-to-end resource estimate for stopping power of a
projectile (α, proton) in warm dense hydrogen/deuterium via first-quantized
dynamics. Two propagators are costed: qubitization/QSP (plane waves, builds on
Su et al.) and a real-space-grid product formula (Sec. II.D, "Time evolution
costs using product formulas"). The latter is where the inverse square root
lives. Headline: 10^15–10^17 Toffolis, ~10^3 logical qubits for converged
systems; the Trotter route is cheaper in Toffolis for the systems studied
(Table "total costs": QSP ~10^17 vs 8th-order product formula substantially
less, at the price of more qubits).

**Where the cost is.** One Trotter step = (i) phase by the potential in the
position basis, (ii) phase by kinetic energy in the momentum basis, (iii) QFTs.
Step (i) requires the pairwise Coulomb term for `η(η−1)/2` electron pairs; the
paper explicitly phases *each pair separately* (compute → phase → uncompute),
which it notes costs ancilla-time but avoids summing. Each exponential
`e^{−iδV}` costs "on the order of `2395 η(η−1)/2`" Toffolis (n_p = 6), and the
bespoke 8th-order product formula uses 17 exponentials per step. So the
inverse-square-root subroutine is *the* multiplicative constant of the whole
Trotter algorithm, which is why it became Benchmark I.

**The algorithm (Sec. II.D), with their numbers (n = n_p bits per coordinate).**

1. Squared distance: `x = Σ_c (r_{i,c} − r_{j,c})²` via Lemma 8 of Su et al.
   (sum of three n-bit squares): `3n² − n − 1` Toffolis (101 at n = 6; 289 at
   n = 10). x has ≤ 2n + 2 bits. *(Upstream of the benchmark.)*
2. Normalization: strip pairs of leading zeros, cost `n(n+1)` Toffolis
   ("the number of bits moved": 12+10+8+6+4+2 = 42 at n = 6). All-zero x is
   impossible (antisymmetry).
3. QROM-selected interpolation (Sanders et al. 2020 *variable-spacing QROM*,
   cost `4n + 2` Toffolis, 26 at n = 6): intervals are dyadic,
   `[2^m, (3/2)2^m]` and `[(3/2)2^m, 2^{m+1}]`, i.e. **two cubic polynomials per
   octave**, with coefficients rescaled per octave as
   `a0 → a0/2^{m/2}, a1 → a1/2^{3m/2}, a2 → a2/2^{5m/2}, a3 → a3/2^{7m/2}` and
   `(x−1) → (x−2^m)`.
   * On [1, 3/2]: `1/√x ≈ a0 − a1(x−1) + a2(x−1)² − a3(x−1)³` with
     `a0 = 0.99994132489119882162, a1 = 0.49609891915903542303,
      a2 = 0.33261112772430493331, a3 = 0.14876762006038398086`.
   * On [3/2, 2]: same form in `(x − 3/2)` with
     `0.81648515205385221995, 0.27136515484240234115,
      0.12756148214815175348, 0.044753028579153842218`.
   * Evaluated by Horner: `a0 − (x−1){a1 − (x−1)[a2 − a3(x−1)]}` → 3 multiplies,
     3 subtractions; `x − 1` / `x − 3/2` is a CNOT (drop the leading 1).
   * The coefficients were found by *numerically minimising the maximum
     relative error after the Newton step*, not of the polynomial itself.
4. One Newton–Raphson step with a tuned constant:
   `y ↦ ½ y (3 + δ − y² x)`, `δ = 5.1642030908180720584×10^-9` on [1, 3/2]
   (max relative error 2.5821×10^-9 after the step) and
   `δ = 3.6279794522852781448×10^-10` on [3/2, 2] (1.8140×10^-10). δ shifts the
   one-sided NR error (NR from a good guess always undershoots: error
   `−(3/2)ε²`) to be two-sided, halving it. (Confirmed numerically: without δ
   the post-NR error is 5.16×10^-9 / 3.63×10^-10, with δ exactly half.
   **[computed]**)
   Reported: "using two points within each factor of 2 of the argument gives
   relative error within about one part in 4×10^8" ≈ 2^-28.6 in double
   precision.
5. Bit widths: "the initial polynomial interpolation may be given to only 15
   bits of precision, and the resulting accuracy after the step of NR is still
   about one part in 10^8". Cost model: a real multiplication ≈ (bits)²
   Toffolis ("less significant bits can be omitted", citing Sanders 2020).
   Three Horner multiplies at 15 bits: `3 × 15² = 675`; subtractions ≈ 45;
   NR: square `15²`, two multiplies at 24 bits `2 × 24²`, subtract 24 →
   **2 136** Toffolis for interpolation + NR excluding x and QROM; with sum of
   squares and QROM **2 263** (n = 6); plus un-normalization of the result
   (`≤ 15n` = 90) and normalization (42) → **≈ 2 395**. General:
   `2136 + (3n² − n − 1) + (4n + 2) + n(n+1) + 15n = 2137 + 4n² + 19n`.
   (At n = 10 this formula gives 2 727; the actual reference implementation
   needs 7 735 because the 2 136 estimate ignores the truncation-aware widths
   and the ×2 for uncomputation. **[inference]**)
6. Absorbing the Trotter coefficient: to get `b/√x` (needed for high-order
   product formulas with irrational step ratios), multiply the QROM constants
   by b and replace 3 by `2 + b²` in the NR step — same Toffoli count. The
   benchmark fixes β = 1.
7. Uncomputation: they would phase pair-by-pair and uncompute "with Clifford
   gates by retaining about 2000 qubits used in the calculation"
   (i.e. keep the AND ancillas and erase them by measurement, Gidney-style),
   noting that summing all pairs first then uncomputing is infeasible in
   Toffolis.
8. Why not Jones et al. 2012 alone: Jones claimed 32-bit accuracy in 5 NR
   iterations; Rubin et al. tested this and found it holds only over a range
   of < 5× in the argument unless the seed is good — hence lookup + NR.

**Precision requirement origin.** "Due to the accuracy requirements of the
total time evolution Ref. [9] determined that 24-bits of relative error would
be needed" (quoted in 2610.23832). The benchmark's `2^-24` relative tolerance
is inherited from here.

---

## 2. Su, Berry, Wiebe, Rubin, Babbush — *Fault-tolerant quantum simulations of chemistry in first quantization*, arXiv:2105.12767, PRX Quantum 2, 040332 (2021)

**Contribution to this problem.** Not an inverse-sqrt paper: the main text is
plane-wave qubitization/interaction-picture simulation, where the Coulomb
kernel `1/‖ν‖²` is handled by *inequality tests* in state preparation, never
by arithmetic. Its relevance is (a) the arithmetic lemmas everyone cites for
squaring/multiplying, (b) App. K on real-space grids, and (c) the phase-gradient
appendix.

**Arithmetic lemmas (App. G "Complexity of binary squaring").**
* Lemma (binary squaring, simple): `n² − 2` Toffolis by repeated addition with
  Gidney adders.
* Lemma (binary squaring improved): **`n(n−1)` Toffolis** using the
  Hamming-weight/carry-save technique of Kivlichan et al. 2020 ("bits are
  grouped by level; three (or two) bits can be summed with a single Toffoli,
  giving a carry at the next level; the number of carry bits equals the number
  of Toffolis").
* Lemma 8 (summing triple squares): sum of three n-bit squares in
  **`3n² − n − 1`** Toffolis (this is the Coulomb `x` computation).
* Lemma (binary sums of squares): k squares of n bits ≤ `kn²`; numerically
  `kn² − n`, and `kn² − n − 1` when 3 | k.
* Lemma (binary products): **n-bit × m-bit product in `2nm − n` Toffolis
  (n ≥ m)**: `nm` Toffolis for the bit products + the carry-save summation.
  This is the "full-width schoolbook" reference cost; truncation to the top
  bits roughly halves it (see §13 cost model).

**App. K (real-space grids).** Block-encodes `V` by decomposing
`1/(2‖r_p − r_q‖)` into M equal-weight indicator terms
`v(m, r_p, r_q) = [m v_max/M < 1/(2‖r_p − r_q‖)]`, evaluated as
`4 m² v_max² ‖r_p − r_q‖² < M²` — "we can much more efficiently compute [this]
by multiplying the norm through to the other side and squaring it … whereas
the reciprocal square root can be a costly function to evaluate directly
[Häner 2018]". Cost O(log² M) per test via Lemma 8. **This trick (never form
1/√x, only compare x against thresholds) is available to LCU/qubitization but
not to Trotter phasing, where the phase must be `e^{−iδ/√x}` exactly.**
[inference: in kickmix one could emulate it only by a sum of
`e^{−iδ v_max/M · [...]}` phases over M comparators, i.e. M comparisons each
~2·22 Toffolis; reaching 2^-24 relative precision would need M ≈ 2^24 — hopeless.]

**App. F (modified phase gradient state).** Phasing by a register via addition
into a phase-gradient state costs `b_grad − 2` Toffolis and *no rotations*; the
multiplying factor is absorbed by choosing `b_grad`, `b_T` with effective-λ
penalty ≤ `1 + 1/2^{2b_T+1}`. **Not available in kickmix** (no H to prepare the
resource state and no gate to consume it), so the benchmark forces one Z_POW
per output bit. This is the single biggest structural difference between the
literature costings and the competition metric.

**Qubit costings (App. C)** give the general pattern "`n_p` bits per coordinate,
`2n_p + 2` after summing squares", used verbatim by the benchmark.

---

## 3. Kivlichan, Wiebe, Babbush, Aspuru-Guzik — *Bounding the costs of quantum simulation of many-body physics in real space*, arXiv:1608.05696, J. Phys. A 50, 305301 (2017)

**What it actually contains.** Despite being cited for the real-space approach,
the paper contains **no Newton–Raphson, no lookup, no inverse-sqrt circuit**
(grep over the full LaTeX source: zero hits for "Newton", "Toffoli", "lookup",
"reciprocal"). It works in an *oracle query model*: cost = number of unitary
adders + queries to a potential-energy oracle. Relevant facts:
* The Coulomb potential is softened to
  `V = Σ_{i<j} q_i q_j / √(‖x_i − x_j‖² + Δ²)` to bound `V_max ≤ η² q² √3/(9Δ²)`;
  this is the first place in this lineage where `1/√(x + Δ²)` appears — note
  the benchmark instead relies on antisymmetry (x ≥ 1) and has no Δ.
* The potential is decomposed into `V_max` signature matrices applied as
  phases (BCCKS Taylor-series simulation, not Trotter).
* Theorem "Discrete simulation": query count `Õ(η D (k_max + V_max t) ...)`
  adders and oracle queries; Fig. `log_cswaps.pdf` concerns controlled swaps
  for antisymmetrization, not arithmetic.
So for *circuit* purposes this paper contributes only the problem framing;
the arithmetic lineage is Jones 2012 → Häner 2018 → Rubin 2023.

---

## 4. Häner, Roetteler, Svore — *Optimizing quantum circuits for arithmetic*, arXiv:1805.12445 (2018)

**Contribution.** (a) A parallel piecewise-polynomial evaluation scheme (Remez
minimax per subinterval, label register from comparators, coefficients loaded
in superposition); (b) a reversible fixed-point "fast inverse square root"
(Quake-style seed + Newton), with an initial-guess tweak that saves one
iteration; (c) explicit Toffoli formulas and tables; all implemented and tested
in LIQUi|⟩.

**Fixed-point multiply cost (App. A/B).** Shift-and-add with *pre-truncation*
(additions act only on the bits inside the n-bit result, error ≤ `n/2^{n−p}`),
Takahashi controlled adders at `3n + 3` Toffolis:
`T_mul(n,p) = (3/2)n² + 3np + (3/2)n − 3p² + 3p`,
`T_fma(n,p) = (3/2)n² + 3np + (7/2)n − 3p² + 3p − 1`,
degree-d polynomial `T_poly = d·T_fma`;
M parallel polynomials add `2M(4⌈log2 M⌉ − 8)` per FMA plus label computation
`T_label = 4Mn` (one CARRY comparator per boundary); qubits
`(d+1)n + ⌈log2 M⌉ + 1`. These are *general-boundary* intervals and
*full-width* n × n multiplies — exactly the two overheads later removed by
dyadic leaves and narrow local coordinates (§12).

**Inverse square root (App. C).** Iteration `x_{n+1} = x_n (1.5 − a x_n²/2)`.
Seed: `x̃0 = 2^{−⌊log2 a⌋/2}` from the position of the leading 1 (flag scan,
`2n` Toffolis), then one *cheap* first round
`x0 = 2^k(1.5 − a 2^{2k}/2)` done with n controlled additions
(`T_init = 3n² + 5n`). Tuning the constant 1.5 to `C(k) ∈ {1.613 (k<0), 1.5,
1.62 (k>0)}` removes the error spikes at powers of two and "saves an entire
Newton iteration" (Fig. 3). Each iteration: square, multiply by shifted a,
subtract from 1.5, multiply by x_n, uncompute three intermediates → 5
multiplies + 2 adds: `T_iter = (15/2)n² + 15np + (23/2)n − 15p² + 15p − 2`;
`T_invsqrt(n,m,p) = T_init + m T_iter`, qubits `n(m+4)`. They needed m = 2–4
iterations with n = 25/35/55 bits for the error curves in Fig. 3 (absolute
error 10^-5 … 10^-14 on [1/2000, 5]) and remark that widths should grow with
the iteration because of quadratic convergence. Table I gives optimal pebbling
step counts for m registers × r iterations.

**Numbers to calibrate against.** Table II (compute-only, ×2 for uncompute):
tanh at 10^-9 needs degree 5 / 30 intervals / 281 qubits / 35 460 Toffolis;
exp(−x) at 10^-9 degree 5 / 19 intervals / 25 721 Toffolis; i.e. tens of
thousands of Toffolis for ~30-bit accuracy with this general scheme. The
reference costs in Gu et al. (§12) for the same scheme tuned to 1/√x are
6 355 Toffolis / 252 qubits at a much looser 2×10^-6 absolute target.

---

## 5. Bhaskar, Hadfield, Papageorgiou, Petras — *Quantum algorithms and circuits for scientific computing*, arXiv:1511.08253, QIC 16, 197 (2016)

**Contribution.** Fixed-precision Newton schemes for `1/w`, `√w`, `w^{1/2^k}`,
`ln w` with *rigorous* error theorems; circuits built only from adders and
multipliers; explicit qubit/op counts for n = 2m = b = 32.

**INV(w, n, m, b)** (w ≥ 1, n bits of which m integer; b ≥ m fractional bits):
seed `x̂0 = 2^{−p}` with `2^p > w ≥ 2^{p−1}` (leading-one detector, Fig. 4),
`s = ⌈log2 b⌉` iterations of `x_i = −w x̂²_{i−1} + 2 x̂_{i−1}`, each result
truncated to b fractional bits; error `|x̂_s − 1/w| ≤ (2 + log2 b)/2^b`
(Corollary 0). The iteration converges from below and truncation is shown not
to break monotone convergence.

**SQRT(w, n, m, b)** (b ≥ max{2m, 4}): first INV, then
`y_j = ½(3 ŷ_{j−1} − x̂_s ŷ³_{j−1})`, i.e. **Newton on `f(y) = 1/y² − 1/w`,
which is the inverse-square-root iteration applied to `1/w`**, seeded with
`ŷ0 = 2^{⌊(q−1)/2⌋}` where `2^{1−q} > x̂_s ≥ 2^{−q}` (Fig. 5); error bound
(Theorem 1, Eq. 5): `|ŷ_s − √w| ≤ (3/4)^{b−2m} (2 + b + log2 b)` — loose, and
the reason they require `b ≥ 2m` fractional bits. They
deliberately avoid `x ↦ x − (x² − w)/(2x)` because it needs a division with a
floating binary point.

**Costs.** Per iteration ≤ 3 multiplier modules; they keep all iterates
(reversibility by storage), so for n = 2m = b = 32: INV = 20 multiplications,
10 additions, ~370 qubits; SQRT = 60 multiplications, 20 additions, ~790 qubits
(Table 6); uncomputing everything "at most doubles" the arithmetic. **Lesson
for us:** the power-of-two seed costs `⌈log2 b⌉ = 5` full-width iterations to
reach 32 bits; every extra bit of seed accuracy removes work quadratically,
which is why lookup seeds (Rubin) or finer tables with no Newton at all (Gu)
dominate.

---

## 6. Jones, Whitfield, McMahon, Yung, Van Meter, Aspuru-Guzik, Yamamoto — *Faster quantum chemistry simulation on fault-tolerant quantum computers*, arXiv:1204.0567, NJP 14, 115023 (2012)

The origin of the lineage. App. B: `r_ij² = Σ (Δx)²` by adders; then
`a_{n+1} = ½ a_n (3 − a_n² r_ij²)`, "with suitably chosen initial value a0 …
converges within 5 iterations at 32-bit arithmetic". The result feeds a
**quantum variable rotation (QVR)**, Eq. (18): `Σ c_j |φ_j⟩ ↦ Σ e^{2πi ξ φ_j}
c_j |φ_j⟩`, realised either (Fig. 14) as one single-qubit rotation per bit of
|θ⟩ (each needs accuracy ε/t for t bits — exactly the benchmark's Z_POW-per-bit
pricing) or (Fig. 15) by phase kickback: add |θ⟩ into a pre-programmed
phase-kickback register `γ(k_[ξ])`, with the constant ξ absorbed into the
resource state and a bit-shift; Fig. 16 shows this is linear in log(1/ε) vs
super-quadratic for bitwise rotations. Again: kickback is not available in
kickmix, so Fig. 14 is our regime. Scaling constants for V and T
(`ξ = q_i q_j δt/(8π²ε0ħ)`, `ħδt/(4πm_j)`) are folded into the QVR, the
ancestor of Rubin's "compute b/√x directly".

---

## 7. Gidney — *Halving the cost of quantum addition*, arXiv:1709.06648, Quantum 2, 74 (2018)

* **Temporary logical AND**: 4 T (= 1 Toffoli-equivalent) to compute
  `|a,b,0⟩ → |a,b,ab⟩` into a fresh ancilla; **0 T to erase** by X-basis
  measurement + classically-controlled CZ(a,b). This is exactly kickmix's
  `HMR` + classically-controlled `CZ` (2610.23832 Sec. II.A: "saving a Toffoli
  gate"); the competition's simulator samples the measurement outcome and
  checks that the fix-up is applied, hence the 64 shots per input.
* n-bit adder: `4n − 4` T = **n − 1 Toffolis**, measurement depth `2n − 2`,
  n − 1 ancillae (vs 8n T for Cuccaro). Discusses the "opportunity cost" of
  ancillae (480 |T⟩/measurement-depth) — the Q × C metric is a crude version of
  this.
* Consequence for arithmetic: a row of a schoolbook multiplier (AND the
  multiplier bit into m partial-product bits, add, erase) costs `m + (m−1)`
  ≈ 2m Toffolis forward, and the *same again* in reverse because the ANDs
  have to be recomputed to undo the addition. Only the ANDs' erasure is free.
  This is why baseline forward (3 874) ≈ reverse (3 861). **[inference from
  the baseline table]**

## 8. Gidney — *Windowed quantum arithmetic*, arXiv:1905.07682 (2019)

* Table lookup (QROM, Fig. 2 from Babbush 2018): `L − 1` Toffolis (+ L·W CNOTs)
  for L entries of W bits, `⌈log2 L⌉` ancillae.
* **Uncomputing a lookup (Fig. 3)**: measure all W output qubits in X basis;
  the residual phase `(−1)^{Σ r_k T[a]_k}` is fixed by a lookup *of a 1-bit
  table addressed by the high half of a* targeting a unary register over the
  low half: Toffoli count **≈ 2√L** instead of L. "Uncomputing the lookup has
  negligible cost."
* Windowed product-addition `x += k·y` (k classical): iterate y in windows of
  w bits, look up `(y_window · k) ≪ i` and add: `O((n/w)(n + 2^w))`; w = lg n
  gives `O(n²/lg n)`; lower Toffoli count than schoolbook at ≥ ~100 bits in
  their Q# tracing. Windowed `x *= k` similar. Fig. 5 generalises to k being
  "a function of a small number of qubits" by including those qubits in the
  lookup address — **this is the bridge to our case**: the polynomial
  coefficient `c_i(leaf)` is a function of the 8-ish leaf-address bits, so
  `c_i(leaf) · Δx_window` can be looked up jointly. **[inference]** With 8 leaf
  bits and a 3-bit window that is 2^11 entries per window — more expensive
  than a narrow multiply (§14), so windowing only pays with very few leaves
  (2–3 address bits), i.e. in the *Newton* regime, not the fine-table regime.

## 9. Babbush, Gidney, Berry, Wiebe, McClean, Paler, Fowler, Neven — *Encoding electronic spectra in quantum circuits with linear T complexity*, arXiv:1805.03662, PRX 8, 041015 (2018)

Unary iteration (Sec. III.A): walks a binary tree over the index register with
`⌈log2 L⌉` ancillae, T-count `4L − 4` (= `L − 1` Toffolis), parallelisable;
QROM = unary iteration with CNOT fan-outs at the leaves. Also the "controlled
by one extra qubit for +1 Toffoli" convention used in the baseline's "QROM
cost 2 Toffolis because it is not controlled".

## 10. Low, Kliuchnikov, Schaeffer — *Trading T-gates for dirty qubits in state preparation and unitary synthesis*, arXiv:1812.00954 (2018)

SelectSwap QROM: for N entries of b bits with parameter λ, T-count
`4⌈N/λ⌉ + 8bλ` (= `⌈N/λ⌉ + 2bλ` Toffolis in the original accounting) using
`bλ + 2⌈log2 N⌉` qubits of which `b(λ−1)` may be dirty; optimum
`λ ≈ √(N/b)` gives `O(√(Nb))`. Berry et al. (next) tightened the swap count.

## 11. Berry, Gidney, Motta, McClean, Babbush — *Qubitization of arbitrary basis quantum chemistry leveraging sparsity and low rank factorization*, arXiv:1902.02134, Quantum 3, 208 (2019)

App. A–C: with clean ancillas, **QROM compute `⌈d/k⌉ + M(k − 1)` Toffolis**
(d entries, M output bits, k a power of two, `Mk` ancilla qubits);
**uncompute `⌈d/k⌉ + k`** by the measurement trick ("X measurements on the
output qubits … a phase fix-up by a lookup over a much smaller table"), with k
chosen independently for the two directions; with dirty ancillas
`2⌈d/k⌉ + 4M(k−1)` and `2⌈d/k⌉ + 4k`. Optimum `k ≈ √(d/M)` → compute
`≈ 2√(dM)`, uncompute `≈ 2√d`. **Worked for us [computed]:** a 256-entry,
51-bit table: plain 255 Toffolis, k = 2: 179 (+51 qubits), uncompute k = 16:
32. A 4 096-entry 43-bit table: k = 8: 813 Toffolis (+344 qubits), k = 4:
1 153 (+172), uncompute k = 64: 128.

## 12. Sanders, Berry, Costa, Tessler, Khattar, Reiher, Babbush — *Compilation of fault-tolerant quantum heuristics for combinatorial optimization*, arXiv:2007.07391, PRX Quantum 1, 020312 (2020)

Sec. II.E / Fig. 3: **variable-spacing QROM** — unary iteration with steps
`ℓ ↦ ℓ+1, ℓ+2, ℓ+4, …`, so that regions that *ignore low address bits* (dyadic
blocks `{4,5}, {8..11}, {12..15}`, or powers of two `0,1,2–3,4–7,8–15`) cost
**`g − 2` Toffolis for g distinct regions** (+1 if controlled). Regions must be
power-of-two sized and aligned ("{4,5} but not {3,4}"). Used for piecewise
*linear* interpolation of `exp` and `arcsin(exp)` with points spaced by powers
of two; interpolation error `≈ (δz)² f''(z)/8`. This is the `4n + 2` QROM in
Rubin et al. (2 regions per octave × (2n+2) bits → `2(2n+2) − 2 = 4n + 2`) and
the pruned lookup in Gu et al.'s Gaussian circuit (1 022 → 495 Toffolis).

---

## 13. Gu, Kemeny, Yelin, Lukin — *Discovering state-of-the-art quantum circuits with large language models*, arXiv:2610.22367 (Oct 2026) — directly relevant prior art

(Not on the original list; it was already in the scratchpad and contains an
LLM-discovered **Coulomb 1/‖r‖ kickmix circuit** evaluated with the same
verification style.) SI III.2: inputs `r_i, r_j ∈ {0..255}³` (8-bit coords,
≤ 18-bit d²), output `F = round(2^24/√d²)` added to a 25-bit accumulator with
**absolute** error ≤ 2×10^-6 (≈ 2^-19; a *far looser* target than the
competition's 2^-24 *relative*). Tuned HRS (Häner) baseline: quadratics on 16
intervals, 6 355 Toffolis, 252 qubits. Discovered circuit: **1 140 Toffolis,
142 qubits** (TQ 9.9× better), via:
* squared distance accumulated directly (partial products of all three
  squares into one accumulator; no product registers);
* `d² = 2^e u`, `1 ≤ u < 2`, `1/√d² = 2^{−e/2}/√u`; flag qubits hold the scale;
* **parity of e + six leading mantissa bits select one of 128 *lines***; the
  next six bits are the local coordinate → "at most six controlled additions
  rather than a general multiplication"; remaining low bits are dropped;
* coefficients fitted offline *to the exact integer/truncated computation*
  (not rounded from a real-valued fit), so widths, omitted columns and
  rounding share one error budget;
* the lookup is erased by **MBU with 17 Toffolis instead of the 126 that
  reversing it would take** (≈ 2√128);
* worst-case error 1.91×10^-6.
Same paper, HHL `arcsin` circuit (SI III.1, 10^-7 rad): 345 *dyadic leaves*
selected by leading input bits (no comparators), an in-place **cyclic shift of
the input bits into a shared local coordinate** (`d = 2^{15−b} δ + c_L`, the
leaf constant `c_L` absorbed into the fitted coefficients), quadratics instead
of cubics, Horner "in place over the loaded slope, accumulate the outer product
directly into the output", multiplications 15 × 16 bits instead of 44 × 44;
1 348 Toffolis / 115 qubits vs 16 000 / 300. Gaussian: after MBU the freed
coefficient qubits are reused as carry ancillas (peak 139 qubits vs 362).
**These are precisely the levers available for Benchmark I; the competition
baseline already uses the normalization shift and in-place Horner, but keeps
the Newton step and a coarse 4-piece cubic table.**

## 14. Babbush, Huggins, Berry, Ung, Zhao, Reichman, Neven, Baczewski, Lee — *Quantum simulation of exact electron dynamics can be more efficient than classical mean-field methods*, arXiv:2301.01203, Nat. Commun. 14, 4058 (2023)

Read in full (LaTeX). It is a plane-wave, first-quantized *qubitization*
costing (block encodings of T, U, V with inequality tests; state preparation
of Slater determinants with unary iteration, Toffoli cost `η n_η + …`). **There
is no Coulomb-phasing arithmetic and no inverse square root in it** (grep:
no hits). Its relevance is only that it motivates real-space/first-quantized
dynamics and reuses the Su et al. machinery; nothing from it changes the
arithmetic design.

## 15. Other square-root circuit literature (for completeness)

* Muñoz-Coreas & Thapliyal, arXiv:1712.08254: garbageless *non-restoring
  integer square root*, T-count `(7/2)n² + 21n − 28`, `2n + 1` qubits
  (with a `14n − 7` T adder; their multiplier is `21n² − 14` T, i.e. ~5n²
  Toffolis — much worse than the Su/Gidney `2nm − n`). **[inference]** An
  exact-integer route (`isqrt(x·2^{2k})` to get 25 significant bits needs a
  ~50-bit radicand → ≈ 8 750 T ≈ 2 200 Toffolis, then a reciprocal of
  comparable cost, then ×2 for uncompute) is not competitive with the
  polynomial route and is not pursued below.
* Häner, Soeken, Roetteler, Svore, *Quantum circuits for floating-point
  arithmetic* (arXiv:1807.02023) and Cao et al. (Poisson solver, NJP 2013;
  Wang et al. 2020 follow-up) use Newton reciprocal/inverse-sqrt with 5+
  iterations at fixed width; they predate and are dominated by the above.
* An arXiv full-text search for "inverse square root" quantum circuit returns
  essentially only Häner 2018 among circuit papers.

---

## 16. Cost primitives (kickmix accounting: CSWAP = CCX = 1; HMR free)

| primitive | Toffolis | qubits | source |
|---|---|---|---|
| temporary AND compute / erase | 1 / 0 | +1 | Gidney 2018 |
| n-bit in-place add (quantum + quantum) | n − 1 | n − 1 ancilla | Gidney 2018 |
| controlled add / multiplier row of m bits (AND row, add, erase) | ≈ 2m − 1 fwd, same in reverse | m scratch | baseline App. B |
| n × m full product | 2nm − n | — | Su Lemma |
| n-bit square | n(n − 1) | — | Su Lemma |
| sum of three n-bit squares | 3n² − n − 1 | — | Su Lemma 8 |
| truncated n × m → k top bits, G guard bits | ≈ 2 × (#partial products of weight ≥ 2^{−(k+G)}) (calibrates to baseline within ~10–15 % at G = 3) | | **[computed]** |
| QROM, L entries, W bits | L − 1 (unary iteration) | ⌈log L⌉ + W | Babbush 2018 |
| variable-spacing QROM, g dyadic regions | g − 2 | | Sanders 2020 |
| SelectSwap QROM | ⌈L/k⌉ + W(k − 1) | + Wk | Berry 2019 |
| uncompute QROM by measurement | ⌈L/k⌉ + k ≈ 2√L | | Berry 2019 / Gidney 2019 |
| leading-zero-pair normalization of 2n_p + 2 bits (unary flags) | n_p(n_p + 2) fwd, n_p(n_p + 1) rev | n_p flags | baseline |
| controlled cyclic shift of an m-bit register by one position | m − 1 CSWAPs | 0 | baseline |
| barrel shift by binary s (⌈log2 n_p⌉ stages) | ≈ Σ_stages (width) ≈ 4 × 30 = 120 for 27-bit p, s ≤ 9 **[inference]** | 0 (thermometer→binary is CNOT-only: `s_0 = ⊕_k f_k`, `s_1 = ⊕_k f_{2k+1}`, …) | |
| Z_POW rotation (non-Clifford, non-T) | 0.56 log2(1/ε) + 5.3 T ≈ 27 T ≈ 6.8 Toffoli-eq at ε ≈ 2×10^-12 | | benchmark pricing **[computed]** |
| phase-gradient addition | n − 2 Toffolis, 0 rotations | **not available in kickmix** | Su App. F / Jones 2012 |

---

## 17. Numerics: how much approximation power is needed **[computed]**

Minimax (Remez, relative-error weighted) piecewise polynomials for `1/√u`,
`u ∈ [1, 2)`, on `2^k` equal dyadic intervals per octave (for `[1, 4)` the
same table is reused with the octave parity as one more address bit; errors
are identical by the `2^{−m/2}` rescaling):

| degree | intervals/octave | max relative error | log2(1/err) |
|---|---|---|---|
| 1 | 512 | 1.79e-7 | 22.4 |
| 1 | 1024 | 4.47e-8 | 24.4 |
| 1 | 2048 | 1.12e-8 | 26.4 |
| 2 | 16 | 2.18e-6 | 18.8 |
| 2 | 32 | 2.85e-7 | 21.7 |
| 2 | 64 | 3.64e-8 | 24.7 |
| 2 | 128 | 4.60e-9 | 27.7 |
| 2 | 256 | 5.79e-10 | 30.7 |
| 3 | 4 | 5.28e-6 | 17.5 |
| 3 | 8 | 4.11e-7 | 21.2 |
| 3 | 16 | 2.89e-8 | 25.1 |
| 3 | 32 | 1.92e-9 | 29.0 |
| 4 | 4 | 2.65e-7 | 21.9 |
| 4 | 8 | 1.09e-8 | 26.5 |

Each halving of the interval gains `d + 1` bits (2 / 3 / 4 / 5 bits for
d = 1/2/3/4), as expected from `err ∝ h^{d+1}`.

Newton step `y1 = ½ y0 (3 − x y0²)`: relative error map
`ε1 = −(3/2)ε0² − ε0³/2` (exact), so

| ε0 | ε1 (one step) | ε2 (two steps) |
|---|---|---|
| 2^-8 | 2^-15.4 | 2^-30.2 |
| 2^-10 | 2^-19.4 | 2^-38.2 |
| 2^-12 | 2^-23.4 | — |
| 2^-13 | 2^-25.4 | — |
| 2^-14 | 2^-27.4 | — |

Baseline seed quality: the Rubin cubic on [1, 3/2] has ε0 = 5.87×10^-5
(2^-14.1) → 2^-27.5 after one step (2^-28.5 with δ); on [3/2, 2]
ε0 = 1.56×10^-5 (2^-16.0) → 2^-31.4 (2^-32.4 with δ). The reference circuit's
realised 2^-25.07 is therefore dominated by fixed-point truncation (14-bit Δx,
17-bit coefficients, 28/30-bit products), not by the approximation.

Tolerance: `min_x tol(x) = 2^-24/√3 133 452 = 3.37×10^-11 = 2^-34.8` turns;
rotations priced at ≈ 27 T each when ~half the margin is left for them.

---

## 18. Design space for an exact-to-tolerance `exp(2πi/√x)` kickmix circuit (n_p = 10)

Fixed structural facts that every design shares:

* **Normalize**: `x = x_norm · 2^{−2s}`, `x_norm ∈ [1, 4)`, 22 bits (2 integer),
  s ∈ {0..9} as a thermometer code. Cost 120 fwd + 110 rev (baseline); a
  priority-encoder + 4-stage barrel shifter is ≈ 90 fwd **[inference]**, a
  marginal gain. Keep the baseline's lane-rotation trick (zero-cost vacated
  bits).
* **Phase**: `1/√x = 2^{−s} · g(x_norm)`, `g ∈ (0.5, 1]`. 2^-24 relative ⇒ g
  needs ≈ 26–27 significant bits (p = 1 integer + 26 fractional) **plus** the
  truncation budget; a 27-bit p shifted by s ≤ 9 occupies up to 36 bit
  positions ⇒ ≈ 33 non-Clifford rotations ≈ 225 Toffoli-eq. The rotation count
  cannot be reduced by phasing before the shift (the angle must depend on s)
  nor by controlled rotations per s value (10 × 27 AND + rotation pairs ≈ 1 900
  Toffoli-eq) **[inference]**. Shift cost: 300 CSWAPs each way (unary) or
  ≈ 120 each way with a binary barrel shifter (thermometer→binary is free).
* **Uncompute**: everything non-AND must be reversed (same Toffoli count as
  forward), except table lookups (MBU, ≈ 2√L) and AND ancillas (free). So
  `total ≈ 2 × (arithmetic) + lookup + 2√L + normalize + 2 × shift + rotations`.
* **Error budgeting**: arithmetic error at the worst x must leave margin for
  the rotations (`ε = π(tol − |error|)/n_rot`); fit the integer coefficients to
  the exact truncated computation (Gu et al.) so that approximation +
  truncation ≤ ~½ tol. The verifier compares against exact
  `isqrt(⌊2^130/x⌋)`, so there is no "exact register" requirement at all —
  *any* function whose phase is within tolerance passes.

### Option A — baseline family (4 cubic pieces + one Newton step)
As shipped: 7 735 Toffoli, 37 rot, Q = 260, S = 2.08×10^6. Incremental fixes
**[inference]**: binary barrel shift (−350), drop guard bits via exact-integer
fitting (−10 % on multiplies ≈ −650), reuse of coefficient qubits after MBU
(Q ≈ 220). Floor ≈ 6 500 × 220 ≈ 1.4×10^6. **Still dominated by the Newton
step's two wide quantum × quantum multiplies (1 043 + 867 + 442 each way).**

### Option B — no Newton: fine dyadic table + quadratic (recommended first target)
Address = octave parity + top 7 fractional bits of x_norm (8 bits, 256 leaves);
local coordinate Δx = remaining 14 bits (only the top ~9 matter for the
quadratic term, all 14 for the linear term). Approximation error 2^-27.7
(table above), leaving ≈ 90 % of the 2^-24 budget for truncation and rotations.

| stage | Toffolis (model, ±15 %) |
|---|---|
| normalize | 120 fwd / 110 rev |
| QROM 256 × (c0 27 b + c1 16 b + c2 9 b ≈ 52 b) | 255 fwd; MBU rev ≈ 32 (k = 16) |
| `t = c1 − T(c2·Δx_hi)` 9 × 9 → 15 b, in place over c1 | ≈ 160–200 fwd, same rev |
| `y = c0 − T(Δx·t)` 14 × 16 → 27 b, in place over c0 | ≈ 420–550 fwd, same rev |
| barrel shift ≪ s | ≈ 120 fwd / 120 rev |
| rotations: ~33 | ≈ 225 Toffoli-eq |
| **total** | **≈ 2 300–2 600 Toffoli-eq** |

Qubits: x 22 + flags 10 + c0/c1/c2 52 + shift extension 9 + multiplier scratch
≤ 16 (rows are narrow) + QROM ancilla 8 ≈ **115–130**. Score ≈ 2.7–3.4×10^5,
i.e. **6–8× below the baseline**, consistent with the 9.9× Gu et al. obtained
on their looser Coulomb task. Variants: 64 leaves/octave (2^-24.7) is too
tight once truncation is added; 256/octave (2^-30.7) costs +256 QROM Toffolis
but lets Δx shrink to 13 bits and c2 to 7 bits — roughly cost-neutral, more
margin.

### Option C — no Newton: 64 leaves + cubic
32 leaves/octave × 2 = 64 entries (2^-29.0), QROM 63 fwd / 16 rev, Δx 15 bits,
three narrowing multiplies ≈ 136 + 348 + 604 ≈ 1 100 fwd (model) ⇒
≈ 2 × 1 100 + 230 + 240 + 80 + 225 ≈ **3 000 Toffoli-eq**, Q ≈ 110–120.
Score ≈ 3.3–3.6×10^5. Slightly worse than B in C, slightly better in Q; a
coin flip until implemented. Quartic (16 entries, 2^-26.5) adds a fourth
multiply (≈ 1 400 fwd) and loses.

### Option D — windowed/pure lookup + linear correction
2048 leaves/octave (4 096 entries, 2^-26.4), Δx 9 bits × 16-bit slope ≈ 290
Toffolis fwd. Table dominates: plain QROM 4 095 (no), SelectSwap k = 8: 813 fwd
+ 344 qubits, k = 4: 1 153 + 172 qubits; MBU rev 128. Total ≈ 1 150 + 290 +
128 + 290 + 230 + 240 + 225 ≈ 2 550 Toffoli-eq but Q ≈ 250–420 ⇒ score
6–10×10^5. **Loses on Q × C**; pure lookup of the phase (3·2^20 entries) is
out of the question. Windowed multiplication (Gidney 2019) helps only when the
coefficient depends on ≤ 2–3 address bits, i.e. in the Newton regime, and even
there a 2^(2+3)-entry lookup per 3-bit window ≈ 31 + adder per window ≈ 60 vs
≈ 3 × (2 × 17) ≈ 100 for three plain rows — a 30–40 % saving on the Horner
stage only, not on the Newton multiplies. **[inference]**

### Option E — cheap seed + Newton
Quadratic on 16 leaves/octave (32 entries, ε0 = 2^-18.8, two tiny multiplies
≈ 250 fwd) + one NR step at 28 bits (≈ 2 400 fwd as in the baseline) ⇒
≈ 5 500 Toffoli-eq. Two NR steps from an 8-bit seed (first at 12 bits ≈ 700,
second at 28 bits ≈ 2 400) ⇒ ≈ 6 500. **Newton is never competitive here
because its multiplies are quantum × quantum at full output width, whereas
Horner's are narrow-Δx × coefficient with shrinking widths** (this is Gu et
al.'s "15 × 16 vs 44 × 44" observation applied to the Rubin circuit).

### Option F — fixed-point vs floating representation
Floating (mantissa + exponent) is already what the normalize/denormalize pair
implements; keeping s in a thermometer code is cheapest for the shift logic.
No further gain from a true floating-point format (Häner et al. 2018b add
exponent handling to every op).

### Option G — exploit "only the phase matters"
* Phasing by a product `e^{2πi Δx·t}` without forming the product costs one
  AND + one rotation per partial-product pair (≈ 7.8 Toffoli-eq each,
  14 × 16 = 224 pairs ≈ 1 750) — worse than multiply + 27 rotations. **[inference]**
* Phasing table values directly (one rotation per leaf under unary iteration)
  costs ≈ 7 Toffoli-eq per entry — worse than loading bits and rotating 27
  times once L ≳ 4.
* Measurement-based erasure of an *arithmetic* output register would need a
  parity fix-up `(−1)^{r·y(x)}` that is as hard as recomputing y; no free
  lunch beyond ANDs and lookups.
So the phase-only structure buys exactly two things: no need to materialise a
correct register (any within-tolerance y is fine, so truncation can be
aggressive), and the ability to absorb β and any constant into the table.

### Open questions worth testing in kickmix
1. Exact Toffoli counts of truncated 9 × 9 → 15 and 14 × 16 → 27 in-place
   row multipliers with exact-integer-fitted coefficients (the model is ±15 %).
2. Whether 256 leaves (2^-30.7) + narrower Δx beats 128 leaves (2^-27.7).
3. Barrel vs unary denormalization in practice (300 vs ≈ 120 CSWAPs per
   direction); whether the shift can be fused into the final row-accumulation.
4. Reusing freed coefficient/lookup qubits as adder carries to push Q toward
   ≈ 100.
5. Rotation budget: with ≈ 2^-27 arithmetic error, ε ≈ 2×10^-12 per rotation;
   check the benchmark's exact `ε = π(min tol − |error|)/n_rot` so that
   n_rot × 27 T is not underestimated.
