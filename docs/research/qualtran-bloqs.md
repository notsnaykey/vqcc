# Qualtran building blocks and literature behind the three VQCC benchmarks

Reference document for the Kaggle competition "Google Quantum AI – Verifiable Quantum Circuit
Compilation" (benchmarks `invsqrt`, `dqi`, `dfthcsos`). It maps each benchmark to (a) the Qualtran
bloqs that implement the same subroutines, with the resource formulas those bloqs encode, and
(b) the papers the bloqs and the competition cite, with short summaries and concrete numbers.

Sources used:

* Qualtran `main`, shallow clone taken 2026-11-04 (`qualtran/_version.py` = `0.8.0.dev0`), local copy at
  `/tmp/claude-0/-home-user/af1e8b3b-1af8-51dd-9e8d-ec3f80eabc0b/scratchpad/upstream/qualtran-full`.
  GitHub links below use `https://github.com/quantumlib/Qualtran/blob/main/<path>`.
* The competition companion paper, Khattar, Rubin, Gidney, Broughton, Low, Babbush,
  "Leveraging verifiable structure in quantum circuits to find more efficient compilations with
  agentic AI", arXiv:2610.23832 (v2, 21 Oct 2026). Read in full (HTML version). This is the single
  most important source: it states the exact benchmark contracts, baseline numbers and score formulas.
* The papers cited by the relevant bloqs and by the companion paper (arXiv full texts, see §7).

Everything marked "(inferred)" is my reading, not a statement from the code or papers.
The kickmix library (`kickmix/` in the Qualtran repo) was analysed separately and is only cross-referenced here.

---

## 0. Executive summary

| Benchmark | Score (lower is better) | Baseline from companion paper (arXiv:2610.23832) | Best published number I found |
|---|---|---|---|
| `invsqrt` | `Q × C`, `C = Toffoli + T/4`, non-Clifford `Z_POW` priced at `0.56·log2(1/ε)+5.3` T each; zero failures over all 3,133,452 inputs × 64 shots | Q = 260 qubits, 7,735 Toffoli + 1 T + 37 rotations → C = 7,988, **score 2.08e6**, worst rel. error 2^-25.07 | Gu et al. arXiv:2610.22367 (different spec: 8-bit coords, 25-bit accumulator, abs. error 2e-6): 1,140 Toffoli, 142 qubits — shows table-of-lines + MBU-erased lookup beats cubic + Newton |
| `dqi` | `R(ε⁺) × Q² × T`, `R(ε) = ln2 / −ln(1/2 + 2√ε)`, ε⁺ = Clopper–Pearson bound from 102,400 shots; 0 failures still gives R = 1.19 | Q = 1,893, T = 5,725,461 (EEA decoder, 63-Toffoli GF(2^12) Karatsuba multiplier, 315-Toffoli Itoh–Tsujii inversion per position) → **score ≈ 2.4e13** | Gu et al. arXiv:2610.22367: Berlekamp–Massey + phase-only Forney, 440,000 Toffoli, 1,837 qubits, failure 1.4e-4 → score ≈ 1.6e12 (≈15× better) (inferred from their numbers) |
| `dfthcsos` | `λ_eff × T_tot × Q_tot`, `λ_eff = sqrt(E_gap(2Λ − E_gap))`, floors Λ > 49.0 Ha, E_gap > 3.914898 Ha, Frobenius errors ≤ 20 mHa, each `Angle_k` circuit ≤ 128 qubits | FeMoCo-76 (N = 76, η = 113); baseline = QROM angle oracles + fixed tree; numbers not printed in the paper (the Kaggle page has them) | Low et al. arXiv:2502.15882 Table 1: FeMoCo-76 full QPE 9.99e8 Toffoli, 1,459 qubits (DFTHC + BLISS + spectrum amplification); FeMoCo-54 block-encoding breakdown in their Table 3 (9,997 Toffoli, 1,131 qubits) |

Floors imply `λ_eff ≥ sqrt(3.914898 × (98 − 3.914898)) ≈ 19.2 Ha` for `dfthcsos`.

---

## 1. What in the Qualtran repo is competition-related

Grep over the whole clone for `kickmix|kmx|kmb|invsqrt|dqi|dfthcsos|femoco|sos|reed|syndrome|spectrum amplification|SOSSA|BLISS`:

| Hit | What it is | Competition-specific? |
|---|---|---|
| `kickmix/` (C++20 + Python, `pyproject.toml` adds `pythonpath = ["kickmix"]`), `docs/kickmix/*.md` (`kickmix_instructions.md`, `kickmix_format.md`, `kickmix_binary_format.md`, `conventions.md`, `api_reference.md`, `dev.md`), `dev_tools/kickmix/` | The competition simulator / builder library and its docs | Yes (analysed by the other agent) |
| `kickmix/src/kickmix/py/circuit/subs/gf_arithmetic_test.py` | kickmix's own GF(2^m) subroutines (tests) | Yes |
| `qualtran/bloqs/chemistry/trotter/grid_ham/{inverse_sqrt,potential,kinetic,qvr}.py`, `trotter_costs.ipynb` (author Fionn Malone, 2023) | Trotter step for the grid Coulomb Hamiltonian incl. variable-spaced QROM + cubic polynomial + one Newton–Raphson step for 1/sqrt(x). Cites arXiv:2308.12352 pp.12–13 and Jones et al. 2012 | Predates the competition; same algorithm as the `invsqrt` baseline |
| `qualtran/bloqs/gf_arithmetic/*` (GF2Addition, GF2AddK, GF2Multiplication, GF2MulViaKaratsuba, GF2MulMBUC, GF2MulK, GF2Square, GF2Inverse, GF2ShiftLeft/Right, BinaryPolynomialMultiplication, MultiplyPolyByOnePlusXk, SynthesizeLRCircuit) and `qualtran/bloqs/gf_poly_arithmetic/*` (GF2PolyAdd, GF2PolyAddK, GFPolySplit/Join) | GF(2^m) and GF(2^m)[x] arithmetic; cites van Hoof arXiv:1910.02849, Amento 2012, Itoh–Tsujii 1989, Banegas et al. 2020 | Written 2024–25 in the run-up to the DQI circuits paper (inferred). `GF2MulViaKaratsuba(12)` costs exactly 63 Toffolis = the companion paper's baseline multiplier; `GF2Inverse(12)` = 5 multiplications = 315 Toffolis = the companion paper's per-position inversion cost |
| `qualtran/bloqs/chemistry/{df,thc,sf,sparse}`, `qualtran/bloqs/chemistry/quad_fermion/givens_bloq.py`, `qualtran/bloqs/rotations/programmable_rotation_gate_array.py`, `qualtran/bloqs/data_loading/{qrom,select_swap_qrom,qroam_clean}.py`, `qualtran/bloqs/chemistry/black_boxes.py` (QROAM placeholder), `qualtran/bloqs/chemistry/resource_estimation.ipynb` (FeMoCo THC/DF numbers), `qualtran/surface_code/thc_compilation.ipynb` | Second-quantised block encodings, Givens rotations by phase gradient, QROM/QROAM | Predates the competition. No spectrum-amplification / SOS / DFTHC bloq exists in Qualtran |
| "sos" hits | `SumOfSquares` arithmetic bloq (`qualtran/bloqs/arithmetic/multiplication.py`) used by the grid Hamiltonian — *not* sum-of-squares Hamiltonians | — |
| `qualtran/qlt_ir`, `docs/qcall.md`, `qualtran/l1` | New textual IR / `qcall` composition sugar | New infra, not benchmark-specific |

No file in `qualtran/` mentions DQI, Reed–Solomon, syndrome decoding, spectrum amplification or FeMoCo-SOS; the RS decoder itself was released with arXiv:2510.10967 (Appendix F "Reference Python implementation", ref. [35] in Gu et al.), not in Qualtran.

---

## 2. Cost model and the primitive cost tables (as implemented in Qualtran)

Qualtran's default cost key `QECGatesCost` counts `And` (compute) as 1 Toffoli-equivalent and `And†` (uncompute) as a measurement + Clifford (0 Toffoli). This is exactly the kickmix accounting (`CCX` = Toffoli, `HMR` + classically controlled `CZ` = free uncompute). `TwoBitCSwap` = 1 Toffoli (or 7 T via Gosset). Arbitrary `ZPowGate`/`Rz` are counted as "rotations" and must be priced separately (the competition prices each non-Clifford `Z_POW` at `0.56·log2(1/ε)+5.3` T, Kliuchnikov et al. arXiv:2203.10064, then divides T by 4).

Below, `n` = register width in bits; "Tof" = Toffoli(-equivalent) count on the compute direction; uncompute via measurement is free unless stated.

### 2.1 Addition / subtraction / comparison

| Bloq (file under `qualtran/bloqs/arithmetic/`) | Operation | Tof | Ancilla / notes | Reference |
|---|---|---|---|---|
| `Add(a_dtype, b_dtype)` (`addition.py`) | `b += a` in place | `n − 1` And | `n−1` temporary; CNOT `6(n−2)+3` | Gidney 1709.06648 |
| `OutOfPlaceAdder(n)` | `c = a + b` into fresh `n+1` reg | `n` And (`out_bitsize − 1`), uncompute 0 | CNOT `5(n−1)+2(+3)` | Gidney 1709.06648 |
| `AddK(dtype, k)` | `x += k` (classical k) | `n − 1` (load k with X gates, then `Add`) | `n` aux; controlled version controls only the load (Clifford) | Häner et al. 2001.09580 §3, Fig 2a |
| `CAdd` (`controlled_addition.py`) | controlled `b += a` | `2n − 1` | `n` And on the control + `Add` | Gidney 1709.06648 |
| `Subtract` (`subtraction.py`) | `b = a − b` via `~(~a + b)` | same as `Add` + `3n` X | | Sanders 2007.07391 p.9 |
| `Negate` (`negate.py`) | `−x = ~x + 1` | `AddK(1)` | cheap controlled version | |
| `LessThanConstant(n, a)` (`comparison.py`) | `z ^= (x < a)` | `n` And | | Babbush 1805.03662 |
| `LessThanEqual(n, n)` | `z ^= (x ≤ y)` | `2n − 1` And (BiQubitsMixer tree `n−1` × 2 And + SingleQubitCompare 1 And), "8n − 4 T" | differing widths add `MultiAnd(d)` | Berry 1711.10460 App. B; Babbush 1805.03662 |
| `GreaterThan(n)` | `a > b` | `LessThanEqual` + X | | |
| `LinearDepthGreaterThan(n, signed)` | `t ^= (a > b)` via half-adder trick | `n` And (unsigned), `n − 1` (signed) | | Gidney 1709.06648; Häner 2306.08585 |
| `LinearDepthHalfGreaterThan` family | keeps `b − a` so the uncompute is free | `n` And | `n+1` ancilla retained | Gidney 1709.06648 |
| `CLinearDepthGreaterThan` | controlled `a > b` | `n + 2` Toffoli | | Häner 2306.08585 p.7 |
| `Equals(n)` / `EqualsAConstant` | `t ^= (x == y)` | `n − 1` Toffoli (MultiControlX) | | |
| `HammingWeightCompute(n)` (`hamming_weight.py`) | `|x⟩|0⟩ → |x⟩|HW(x)⟩` | `n − HW(n)` And | same number of junk qubits; free uncompute | Gidney 1709.06648 p.4 |
| `ToContiguousIndex(n, s)` (`conversions/contiguous_index.py`) | `s = ν(ν+1)/2 + μ` | `n² + n − 1` | | Lee 2011.03494 Eq. 29 |

### 2.2 Multiplication, squaring, inverse

| Bloq (`qualtran/bloqs/arithmetic/multiplication.py`) | Operation | Tof | Reference |
|---|---|---|---|
| `Product(n, m)` | `|a⟩|b⟩|0⟩ → |a⟩|b⟩|ab⟩` (2·max bits out) | `2nm − max(n, m)` | Su et al. 2105.12767 p.81 (Lemma 10) |
| `Square(n)` | `|a⟩|0⟩ → |a⟩|a²⟩` | `n(n − 1)` | Su et al. 2105.12767 p.76 (Lemma 7) |
| `SumOfSquares(n, k)` | `Σ_i a_i²` into `2n + ⌈log k⌉` bits | `k n² − n` (−1 if `k % 3 == 0`) → `3n² − n − 1` for k = 3 | Su et al. 2105.12767 p.80 (Lemma 8) |
| `PlusEqualProduct(a, b, r)` | `r += a·b` | ≈ `8·max(a,b)²` T (approximate placeholder) | — |
| `ScaleIntByReal(r_bits, i_bits)` | real × integer, truncated | `r(2i − 1) − i²` | Sanders 2007.07391 App. D Eq. D8 (p.70) |
| `MultiplyTwoReals(d)` | real × real, truncated to d bits | `d² − d − 1` | Sanders 2007.07391 App. D §5 Eq. D13 (p.71) |
| `SquareRealNumber(d)` | real², truncated | `d²/2 − 4` | Sanders 2007.07391 App. D §6 (p.74) |
| `InvertRealNumber(n, f)` | `1/a` by Newton–Raphson `x' = 2x − a x²` | `⌈log2 n⌉` iterations × (`SquareReal + MultiplyTwoReals + ScaleIntByReal + Subtract`) + `n_int − 1` Toffoli initial guess | Bhaskar et al. 1511.08253 §2.1 |

These truncated-multiplication formulas (Sanders et al. App. D) are the ones used by the `invsqrt` baseline reasoning ("multiplying two real numbers costs about the square of the number of bits because less significant bits can be omitted").

### 2.3 Data loading (QROM family) and unary iteration

| Bloq | Tof (compute) | Tof (uncompute) | Ancilla | Reference |
|---|---|---|---|---|
| `QROM` (`data_loading/qrom.py`, unary iteration) with `N` addresses, total output `b` bits | `N − 2 + n_ctrl` And (≈ `N − 1`, "4(L−1) T") | free (And†) | `Σ selection_bits − 1 + n_ctrl` clean; CNOT ≈ `b·N` | Babbush 1805.03662 Fig. 1/7, §III.A |
| Variable-spaced `QROM` (same class; `_break_early` prunes segment-tree nodes whose data is constant) | ≈ (#maximal aligned constant segments) − 1, e.g. `4n + 2` for the 1/√x tables with `2n+2`-bit index (26 for a 14-bit index) | free | same | Babbush 2007.07391 Fig. 3; Rubin 2308.12352 p.12 |
| `SelectSwapQROM` (`select_swap_qrom.py`), block `K = 2^k` | clean: `N/K + b(K−1)`; dirty: `2(N/K − 1) + 4b(K−1)` (Qualtran charges toggles ×2 for dirty) | same again unless replaced by MBU | `(K−1)b` extra target copies (+ `k` for SwapWithZero) | Low–Kliuchnikov–Schaeffer 1812.00954; Berry 1902.02134 App. A/B |
| `QROAMClean` (`qroam_clean.py`) | `N/K + (K−1)b`, optimal `K ≈ sqrt(N/b)` → ≈ `2·sqrt(N b)` | `QROAMCleanAdjoint`: `⌈N/K⌉ + K − 4 + n_ctrl` (MBU; Berry Thm 3: `⌈d/k⌉ + k`, min ≈ `2 sqrt(N)`), or dirty `2⌈d/k⌉ + 4k` | `(K−1)b` junk registers kept until the adjoint | Berry 1902.02134 App. A, B, C |
| `QROAM` placeholder (`chemistry/black_boxes.py`) | `N/x + b(x − 1)`, adjoint `N/x + x`, optimal `x` chosen | | | Berry 1902.02134 App. B |
| `QROAMTwoRegs` (`black_boxes.py`) | `⌈N_a/k_a⌉⌈N_b/k_b⌉ + b(k_a k_b − 1)`, adjoint `… + k_a k_b` | | | Lee 2011.03494 App. G Eq. G3/G6 |
| `UnaryIterationGate` (`multiplexers/unary_iteration_bloq.py`) | `L − 1` And for an `L`-range loop (`4L − 4` T) | free | `log L` | Babbush 1805.03662 §III.A |
| `SwapWithZero` (`swap_network/swap_with_zero.py`) | `(M − 1)` `CSwap(b)` = `(M−1)·b` Toffoli | | | Low 1812.00954 |
| `CSwapApprox` | `4n` T (relative-phase, OK inside garbage) | | | Low 1812.00954 App. B.2.c |
| `PrepareUniformSuperposition(n)` | `10 log L + 2K` T target (Qualtran currently `12 log L` T + `2(K + log L)` rotations) | | | Babbush 1805.03662 Fig. 12 |
| `StatePreparationAliasSampling` | `PrepareUniform + QROM(L, log L + μ) + LessThanEqual(μ) + CSwap(log L)`; qubits `2 log L + 2μ + 1 + log L` | | | Babbush 1805.03662 §III.D |

### 2.4 Rotations and phasing

| Bloq (`qualtran/bloqs/rotations/`) | Operation | Tof | Reference |
|---|---|---|---|
| `PhaseGradientState(b)` | prepare `Σ_k e^{−2πik/2^b}|k⟩` | `b` rotations (one-off resource) | Sanders 2007.07391 App. A |
| `AddIntoPhaseGrad(x_bits, b_phase)` | `|x⟩|φ⟩ → e^{2πi x/2^b}|x⟩|φ⟩` by in-place add | `b_phase − 2` (controlled: `2(b_phase − 2)`) | Sanders 2007.07391 App. A; Gidney 1709.06648 |
| `AddScaledValIntoPhaseReg(γ)` | phase by `γ·x` via repeated shifted additions | `≤ (γ_bits + 2)/2` additions × `(b_grad − 2)` (only the 1-bits of γ) | Sanders 2007.07391 App. A |
| `ZPowConstViaPhaseGradient(t, b)` | single-qubit `Z^t` | `b_grad − 2` (+ two Clifford controlled loads) | Sanders App. A; Häner 2001.09580 |
| `RzViaPhaseGradient` | `Rz(4πx)` with quantum angle register | one `ControlledAddOrSubtract` | Sanders 2007.07391 §II-C, App. A |
| `QvrZPow` / `QvrPhaseGradient` (`quantum_variable_rotation.py`) | phase by cost register `e^{2πiγf(x)}` | `n` rotations vs `O(log²(1/ε))` Toffoli | Sanders 2007.07391 App. C |
| `HammingWeightPhasing(n)` | `Z^t` on every qubit with `log n` rotations | `n − HW(n)` Toffoli + `⌈log n⌉` rotations | Gidney 1709.06648 p.4 |
| `QuantumVariableRotation(b)` (`chemistry/trotter/grid_ham/qvr.py`) | the grid-Hamiltonian phasing used by `PairPotential` | `b` `Rz` rotations (naive Fig. 14 of Jones 2012) | Jones 1204.0567 Fig. 14 |
| `ZPowUsingProgrammedAncilla` (`programmable_ancilla_rotation.py`) | repeat-until-success rotation from `Z^{2^k t}|+⟩` resource states | T cost of the ancilla states | Jones 1204.0567 Fig. 4 |
| `ProgrammableRotationGateArray` | `M` multiplexed rotations with `B`-bit angles via `⌈MB/κ⌉ + 1` QROM reads + `MB` controlled rotations | | von Burg 2007.14460 §VII.B.1 p.45 |
| `RealGivensRotationByPhaseGradient(b)` (`chemistry/quad_fermion/givens_bloq.py`) | fermionic Givens rotation `exp(θ(a_i†a_j − h.c.))` between two JW-adjacent modes, angle in a `b`-bit register | `2(b − 2)` Toffoli (two `RzViaPhaseGradient`) + Cliffords | von Burg 2007.14460 Eq. 57/73; Sanders App. A |
| `ComplexGivensRotationByPhaseGradient` | adds `e^{iφ n_j}` | `3(b − 2)` | von Burg 2007.14460 |
| `THCRotations(M, N, β, block_size)` (`chemistry/thc/select_bloq.py`) | QROAM of `N/2 − 1` angles + phase-gradient state + `N/2 − 1` real Givens rotations + uncompute | `QROAM + 2·(N/2−1)(β−2)` | Lee 2011.03494 Fig. 7; von Burg 2007.14460 Eq. 73 |
| `ProgRotGateArray` (`chemistry/df/select_bloq.py`) | DF basis rotation | `(n_{LΞ} − 1) + N(β − 2)` Toffoli + `QROAM(LΞ + N/2, N β/2)` | Lee 2011.03494 App. C step 4 p.53 |

### 2.5 GF(2^m) arithmetic (`qualtran/bloqs/gf_arithmetic/`)

| Bloq | Operation | Tof | CNOT / ancilla | Reference |
|---|---|---|---|---|
| `GF2Addition(m)` | `y += x` | 0 | `m` CNOT | — |
| `GF2AddK(m, k)` | `x += k` | 0 | `popcount(k)` X | — |
| `GF2Square(m, k)` | `x → x^{2^k}` in place | 0 | linear reversible circuit (`SynthesizeLRCircuit`, ≤ `m² − m` CNOT) | — |
| `GF2MulK(const)` | `x → c·x mod P` | 0 | CNOT (LR synthesis) | van Hoof 1910.02849 Alg. 1 |
| `GF2ShiftRight/Left(k)` | `x → x^{±k} f mod m(x)` | 0 | `(w−2)k` CNOT, `w` = # terms of the irreducible | van Hoof 1910.02849 §3.1 |
| `GF2Multiplication(m)` (schoolbook) | out-of-place `x·y` (or `z += x·y`) | `m²` | reduction by CNOTs | Maslov et al. 0710.1093; Reyhani-Masoleh 2004 |
| `GF2MulViaKaratsuba(m)` | out-of-place `x·y mod m(x)` | `≈ m^{log2 3}`; exact recursion gives **9 (m=4), 27 (8), 51 (10), 59 (11), 63 (12), 81 (16)** | `O(m²)` CNOT, no ancilla | van Hoof 1910.02849 Alg. 4 |
| `BinaryPolynomialMultiplication(n)` | `h ^= f·g` (no reduction) | `n^{log2 3}` | ≤ `(10+1/3) n^{log2 3}` CNOT | van Hoof 1910.02849 Alg. 3 |
| `GF2MulMBUC(m)` | measurement-based uncompute of a product when both factors remain | 0 Toffoli, `m²` classically-controlled CZ | — | Khattar 2510.10967 App. C.3 (inferred link) |
| `GF2Inverse(m)` (Itoh–Tsujii / Fermat `a^{2^m−2}`) | out-of-place `a⁻¹` | `k1 + t − 1` multiplications with `k1 = bitlen(m−1) − 1`, `t = popcount(m−1)` → **5 mults for m = 12 → 315 Toffoli with the 63-Toffoli multiplier (255 with a 51-Toffoli one)** plus free squarings | `m(m − 2)` junk qubits (120 for m = 12) kept until uncompute | Amento 1209.6348 §2.3; Itoh–Tsujii 1989; Banegas et al. TCHES 2021 Alg. 2 |

Khattar et al. 2510.10967 Table 7 report hand-optimised multipliers of **39/47/51 Toffolis for m = 10/11/12** (Maslov–Yosri–Gavinsky 2025, "modified Karatsuba over a carefully selected irreducible polynomial + template optimisation"), i.e. 19% below Qualtran's Karatsuba at m = 12.

---

## 3. Benchmark I — `invsqrt` (phasing by `e^{2πiβ/√x}`)

### 3.1 Contract and baseline (companion paper §III.1, App. B)

* Input: one named 22-qubit register `x` holding `w = Σ_c (r_{i,c} − r_{j,c})²` for `n_p = 10`-bit sign-magnitude coordinates; `x ∈ [1, 3(2^{10}−2)²] = [1, 3,133,452]`. All other qubits are scratch and must return to `|0⟩`.
* Target: `|x⟩ → exp(2πi β/√x)|x⟩`, `β = 1`; phase checked in `2^-64`-turn fixed point against `isqrt(⌊2^130 β²/x⌋)`; tolerance `2^-24 β/√x` turns; **every input tested 64 times, zero failures allowed** (so no probabilistic slack, but the test is exhaustive and reproducible offline).
* Score `S = Q × C`, `C = Toffoli + T/4`, `Z_POW` with Clifford angle free, T angle = 1 T, finer angles priced `0.56·log2(1/ε) + 5.3` T with `ε = π·min_x(tol(x) − |err(x)|)/n_rot` — i.e. the *leftover* error margin is shared among the rotations, so a more accurate arithmetic makes the rotations cheaper.
* Upstream (not part of the benchmark): computing `w` costs `3n_p² − n_p − 1` Toffolis (Su et al. Lemma 8 = Qualtran `SumOfSquares(n_p, 3)`).
* Baseline pipeline (`|x⟩ →shift 2s→ x_norm →QROM+cubic→ y0 →NR→ p = ½y0(3 − x_norm y0²) →≪s→ y1 →Z_POW + uncompute`):
  1. Normalisation: count leading zero *pairs* `s` (unary, `n_p` flags) and shift so `x_norm ∈ [1,4)`; cyclic lane rotations cost `n_p(n_p+1)` CSWAP + `n_p` AND = `n_p(n_p+2)` = 120 Toffoli at `n_p = 10` (reverse: 110).
  2. QROM: 4 entries (2 polynomial ranges × 2 scalings), 2 Toffolis, outputs four 17-bit coefficients; `Δx` needs only one extra AND (`b13 ∧ b11`).
  3. Horner, in place on the coefficient registers with truncated products `T(·)`: 14-bit `Δx`, 17-bit coefficients → 1,071 Toffoli.
  4. Newton–Raphson: `T(y0²)` 28 bits (442 Tof), `z = T(x_norm·T(y0²))` 30 bits (1,043 Tof), `3 − z` (28 Tof), `p = T(y0·z)` (867 Tof), denormalise `p ≪ s` (`30 n_p` = 300 CSWAP), 40-bit `y1`.
  5. Phasing: one `Z_POW` per bit of `y1` (`F = 30 + n_p = 40` bits; 37 non-Clifford) then reverse everything.
  Totals: Q = 260, 7,735 Toffoli, 1 T, 37 rotations → C = 7,988, S = 2.08e6; worst error 2.84e-8 = 2^-25.07 at x = 2,588,411.

### 3.2 Qualtran bloqs for this benchmark

| Path | What it does | Costs / parameters |
|---|---|---|
| [`qualtran/bloqs/chemistry/trotter/grid_ham/inverse_sqrt.py`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/chemistry/trotter/grid_ham/inverse_sqrt.py) | `get_inverse_square_root_poly_coeffs()` = the exact `a_i`, `b_i` cubic coefficients of Rubin et al. (same as companion Eqs. 17–24); `build_qrom_data_for_poly_fit(sel_bits, target_bits, coeffs)` builds the *variable-spaced* QROM table (ranges `[2^k, 1.5·2^k)`, `[1.5·2^k, 2^{k+1})`, coefficients scaled by `2^{-k/2}`); `PolynmomialEvaluationInverseSquareRoot` (3 `MultiplyTwoReals` + 3 `Add`); `NewtonRaphsonApproxInverseSquareRoot` (`SquareRealNumber(poly_bits) + ScaleIntByReal(poly_bits, x_sq_bits) + 2 MultiplyTwoReals(target_bits) + Add`) | Call-graph-only (no decomposition). Example sizes 7/8/12 bits. References: Rubin 2308.12352 pp. 12–13; Jones 1204.0567 |
| [`.../grid_ham/potential.py`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/chemistry/trotter/grid_ham/potential.py) | `PairPotential(bitsize, qrom_data, poly_bitsize=15, inv_sqrt_bitsize=24)`: `OutOfPlaceAdder` ×3 for `r_i − r_j`, `SumOfSquares(n+1, 3)`, `QROM` with `2n+2`-bit selection on `r_ij²`, polynomial, NR step, `QuantumVariableRotation(24)`; `PotentialEnergy(η, N_grid)` loops over all pairs | Uses `QROM` (unary iteration) with the repeated data so Qualtran's `_break_early` gives the variable-spaced cost (`4n + 2`, 26 Toffolis for a 14-bit index) |
| [`.../grid_ham/kinetic.py`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/chemistry/trotter/grid_ham/kinetic.py), [`qvr.py`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/chemistry/trotter/grid_ham/qvr.py) | `KineticEnergy` = `SumOfSquares` + `QuantumVariableRotation(2n+2)`; `QuantumVariableRotation(b)` = `b` `Rz` rotations (Jones Fig. 14) | The phasing is costed as rotations, not Toffolis — the competition does the same (`Z_POW`) |
| [`.../grid_ham/trotter_costs.ipynb`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/chemistry/trotter/grid_ham/trotter_costs.ipynb) | Narrative derivation: NR iteration `a_{n+1} = ½a_n(3 − a_n² r²)`, the `δ` shift (`δ_a = 5.164e-9`, `δ_b = 3.628e-10`, halves the error), the binning `0,1,2,3,[4,5],[6,7],[8,11],...` and the segment-tree argument for variable-spaced QROM ("g − 2 Toffolis = 26 for 14-bit `r_ij²`"); "15 bits of precision" for coefficients | Worked comparison against the paper's rough estimate (2,136 Toffoli for arithmetic, 2,395 incl. shifts) |
| [`qualtran/bloqs/arithmetic/multiplication.py`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/arithmetic/multiplication.py) | `Square`, `SumOfSquares`, `Product`, `ScaleIntByReal`, `MultiplyTwoReals`, `SquareRealNumber`, `InvertRealNumber` | see §2.2 |
| [`qualtran/bloqs/arithmetic/error_analysis_for_fxp_arithmetic.ipynb`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/arithmetic/error_analysis_for_fxp_arithmetic.ipynb) | Fixed-point truncation error bookkeeping (QFxp) | useful for choosing register widths |
| [`qualtran/bloqs/rotations/phase_gradient.py`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/rotations/phase_gradient.py), [`quantum_variable_rotation.py`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/rotations/quantum_variable_rotation.py), [`hamming_weight_phasing.py`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/rotations/hamming_weight_phasing.py) | Alternatives to `b` separate `Z_POW`s: `AddIntoPhaseGrad` (`b_grad − 2` Toffoli), `QvrPhaseGradient`, Hamming-weight phasing | see §3.4 idea 8 |
| [`qualtran/bloqs/data_loading/qrom.py`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/data_loading/qrom.py), [`qroam_clean.py`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/data_loading/qroam_clean.py) | QROM / QROAMClean with MBU adjoint | a 128–256 entry coefficient table costs ≤ 255 Toffoli to load and ≈ `2·sqrt(N)` ≈ 20–32 to erase |

### 3.3 Papers

**Rubin, Berry, Kononov, Malone, Khattar, White, Lee, Neven, Babbush, Baczewski, "Quantum computation of stopping power for inertial fusion target design", arXiv:2308.12352 (PNAS 2024).** First-quantised, grid-based Trotter and QSP simulation of a projectile stopping in warm dense matter. The Coulomb pair term is the bottleneck; they replace Jones et al.'s ≥5 Newton–Raphson iterations with a hybrid: variable-spaced QROM (cost `4n + 2` Toffoli for a `2n+2`-bit `r²`) loads cubic interpolation coefficients fitted on `[1, 3/2]` and `[3/2, 2]` (coefficients in §3.1), one NR step `y ↦ ½y(3 + δ − y²x)` with a tuned `δ` gives relative error ≤ 2.58e-9 / 1.81e-10 per range; coefficients only need 15 bits; Horner form needs 3 multiplications (≈ `3·15²`); the NR step ≈ `15²` square + multiplications; their rough total is 2,136 Toffoli for arithmetic, 2,395 with normalisation shifts (`12+10+…+2 = 42` CSWAP at `n = 6`) and de-shifting (≤ `15n`). They also fold the Trotter coefficient `b` into the table (`b/√x` by replacing 3 with `2 + b²`). 24-bit relative precision was the accuracy requirement derived for the whole time evolution.

**Jones, Whitfield, McMahon, Yung, Van Meter, Aspuru-Guzik, Yamamoto, "Faster quantum chemistry simulation on fault-tolerant quantum computers", arXiv:1204.0567 (NJP 2012).** Introduces the first-quantised grid Trotter algorithm (compute `1/|r_i − r_j|` into an ancilla, phase, uncompute), Newton–Raphson for `1/√x` ("5 or more iterations"), the *quantum variable rotation* (QVR) `Σ_j c_j|φ_j⟩ → Σ_j e^{iξφ_j}c_j|φ_j⟩` implemented either as `t` bitwise rotations (Fig. 14, each to accuracy `ε/t`) or by phase kickback with an addition into a programmed ancilla register (Fig. 15), and programmable ancilla rotations (PAR). Qualtran's `QuantumVariableRotation` is the Fig. 14 version; `ZPowUsingProgrammedAncilla` is Fig. 4.

**Su, Berry, Wiebe, Rubin, Babbush, "Fault-tolerant quantum simulations of chemistry in first quantization", arXiv:2105.12767 (PRX Quantum 2021).** Appendix G gives the arithmetic lemmas Qualtran cites: Lemma 6/7 squaring `n² − 2` → `n(n − 1)` Toffoli, Lemma 8 sum of three squares `3n² − n − 1`, Lemma 10 product `2nm − n`. (The companion paper uses Lemma 8 for the upstream `w` computation.)

**Sanders, Berry, Costa, Tessler, Wiebe, Gidney, Neven, Babbush, "Compilation of fault-tolerant quantum heuristics for combinatorial optimization", arXiv:2007.07391 (PRX Quantum 2020).** Appendix A: phase gradient trick, addition into the gradient register costs `b_grad − 2`, multiplication by a classical constant by repeated shifted additions. Appendix C: phasing by a cost function via `O_direct` and `O_phase`. Appendix D: fixed-point arithmetic with truncation — real × integer `d_B² + (2d_B − 1)⌈log(d_B/ε)⌉ − d_B` (Eq. D8/D9), real × real `d_A(2d_B − 3) − (d_B − 1)²` → `d² − d − 1` for equal widths (Eq. D13), squaring `d²/2 − 4`. Also Figure 3 of this paper is the variable-spaced QROM reference.

**Häner, Roetteler, Svore, "Optimizing quantum circuits for arithmetic", arXiv:1805.12445 (2018).** (Not fetched; cited by the companion as the origin of the normalise-then-piecewise-polynomial approach, "HRS".) Piecewise polynomial approximation of smooth functions (inverse square root, Gaussian, arcsin, …) with a classical fit, table lookup of coefficients, Horner evaluation with truncated fixed-point multipliers, plus NR refinement; gives the error-vs-interval-count trade-off used by Gu et al.'s "tuned HRS baseline" (16 quadratic intervals, 6,355 Toffoli, 252 qubits for their Coulomb spec).

**Gu, Kemeny, Yelin, Lukin, "Discovering state-of-the-art quantum circuits with large language models", arXiv:2610.22367 (Oct 2026).** LLM-evolutionary search over kickmix-style reversible circuits scored by `T × Q`. §III.2 "Coulomb potential" (spec: 8-bit coordinates, add `round(2^24/d)` into a 25-bit accumulator, abs. error < 2e-6): accumulate the three squares directly into one register; write `d² = 2^e u`; parity of `e` + 6 leading mantissa bits select one of **128 lines**, next 6 bits are the local coordinate (≤ 6 controlled additions, no general multiplier); **MBU erases the 128-entry lookup with 17 Toffolis instead of 126**; 1,140 Toffoli, 142 qubits (5.6× fewer Toffoli, 1.8× fewer qubits than HRS). Their point: "spend more lookup entries to use a lower-degree polynomial — the larger lookup is cheaper than the extra reversible multiplication". (Their §I.1 and §IV are summarised under the other benchmarks.)

**Kliuchnikov, Lauter, Minko, Paetznick, Petit, "Shorter quantum circuits via single-qubit gate approximation", arXiv:2203.10064 (Quantum 2023).** Source of the `0.56·log2(1/ε) + 5.3` T-count-per-rotation pricing used by the verifier (mixed fallback synthesis).

### 3.4 Ideas to cut `Q × C` (with provenance and rough impact)

1. **Trade polynomial degree for table size** (Gu et al. 2610.22367 §III.2; HRS 1805.12445). The QROM is almost free (`N − 1` Toffoli to load, `≈2√N` to erase by MBU per Berry 1902.02134 App. C / Qualtran `QROAMCleanAdjoint`), while each truncated multiply costs `d² − d − 1`. A 128–256-entry table of (intercept, slope) with a 6–7-bit local coordinate replaces the 3 Horner multiplies (1,071 Tof) by ≤ 7 controlled additions (≈ 7 × 30 ≈ 200 Tof) *and* removes 2 of the 4 coefficient registers (−34 qubits). Expected: −800 Tof, −30 qubits. (Whether a line + one NR step reaches 2^-25 must be checked: linear interpolation error on `[1,2)` with 128 intervals is ≈ 2^-17, and NR squares the relative error, so ≈ 2^-33 — comfortable (inferred).)
2. **Skip Newton–Raphson entirely with a higher-degree local polynomial** (the companion paper explicitly suggests "simply finding a good polynomial approximation over the input domain"). A cubic on 32–64 mantissa intervals has interpolation error ≈ `h⁴·max|f''''|/384 ≈ 2^-26` at 64 intervals (inferred), so three ~26-bit truncated multiplies (`3 × (26² − 26 − 1) ≈ 1,950` Tof) replace Horner + square + two 30-bit multiplies (≈ 3,400 Tof) and the 28-bit `y0²`/30-bit `z` registers disappear. Expected: ≈ −1,400 Tof and −60 qubits.
3. **Newton step on the residual** (inferred from the companion's own remark that `x_norm y0²` is "very close to 1"): compute `r = x_norm·y0² − 1` (|r| ≲ 2^-15 after a 15-bit initial guess) and `y1 = y0 − ½·y0·r`; the last multiply then only needs ~12 significant bits of `r` instead of 30 → ≈ −500 Tof and a 30-qubit register shrinks to ~12.
4. **Fuse `y0²` and `x_norm·y0²`** into a single accumulation `z = Σ_k x_k·2^k·(y0²)` without materialising `y0²` (Gu et al.'s "direct accumulation" trick for `d²`): saves the 28-qubit `y0²` register (≈ −10% Q) at a modest Toffoli cost increase; only pays off because Q enters linearly.
5. **Avoid the explicit normalisation shifts** by using variable-spaced QROM on the raw `x` (Qualtran `build_qrom_data_for_poly_fit` / Rubin 2308.12352: cost `4n + 2 = 42` Tof at `n = 10`) with pre-scaled coefficients, instead of `n_p(n_p+2) + n_p(n_p+1) + 30n_p = 530` CSWAP/AND for normalise + denormalise. Caveat: the unnormalised multiplications are wider; a hybrid (QROM-selected exponent flags + barrel shift only of the *output*) is probably best (inferred).
6. **Bit-width search with the exhaustive verifier**: the baseline leaves margin (2^-25.07 vs 2^-24 required). Every register width, truncation point and polynomial coefficient can be tuned by exhaustive classical evaluation over the 3.1M inputs (kickmix simulates 6e10 instr/s), e.g. the 17-bit coefficients, 28-bit square, 30-bit `z` are all candidates for 1–3 fewer bits (each bit of a 30-wide multiplier saves ≈ 60 Tof). Also widen the error margin so the rotation pricing `ε = π·min(tol − err)/n_rot` becomes cheaper (each rotation costs ≈ `0.56·log2(1/ε) + 5.3` T ≈ 22 T ≈ 5.5 Tof-eq; 37 of them ≈ 200 Tof-eq ≈ 2.5% of C).
7. **Fewer rotations / no output barrel shift**: the tolerance is relative (`2^-24/√x` turns), so only the ≈ 26 most significant bits of `p ≈ 2/√x_norm` matter; the `30 n_p = 300` CSWAPs that shift `p ≪ s` can be avoided by phasing `p` directly with angles scaled by `2^{k}` under control of the unary flag `f_k` (controlled `Z_POW` = `CZ_POW`, priced like a rotation but applied only to the ~`n_p` distinct scales — i.e. `n_p × 26` controlled phases, worth it only if the harness prices `CZ_POW` as one rotation). Simpler: keep the shift but drop the 3–4 least-significant bits of `p` and the corresponding multiplier rows (inferred, needs checking against the exhaustive verifier).
8. **Phase gradient instead of 37 `Z_POW`s** (Sanders 2007.07391 App. A; Qualtran `AddIntoPhaseGrad`): `b_grad − 2 ≈ 38` Tof instead of ≈ 200 Tof-eq of rotations, but needs a ~40-qubit resource register (+15% Q) — *net negative* for this score unless Q is cut elsewhere; HammingWeightPhasing does not apply (different angles per bit).
9. **Measurement-based uncomputation everywhere** (Gidney 1709.06648; Berry 1902.02134 App. C): the baseline already uncomputes row ANDs by measurement; make sure every temporary product register is erased by `HMR` + phase fix-up when its inputs are still available (the reverse pass should cost well below the forward pass, as in Gu et al.'s decoder where the reverse walk is 52k Toffolis cheaper). Qualtran pattern: `LinearDepthHalfGreaterThan`/`OutOfPlaceAdder(is_adjoint)` keep the carry register so the adjoint is free.
10. **Reuse scratch across stages and recompute instead of store** (score is `Q × C`, so a 10% Q cut is worth a 10% C increase): the baseline's single shared 30-qubit scratch is the right direction; the four 17-bit coefficient registers can be loaded one at a time (QROM twice) if that removes 34–51 live qubits.

---

## 4. Benchmark II — `dqi` (Reed–Solomon syndrome decoding sign-fix for DQI/OPI)

### 4.1 Contract and baseline (companion paper §III.2)

* Instance `(m, n, b, r) = (4095, 70, 12, 2016)`: OPI over `F_{2^12} = F_2[α]/(α^12 + α^6 + α^4 + α + 1)` (little-endian polynomial basis), evaluation points `α_j = α^j`, dual code `[4095, 4025, 71]`, decoder corrects up to `ℓ = n/2 = 35` symbol errors. Syndromes `s_i = Σ_j e_j α^{(i+1)j}`, `i = 0..69`, stored in `70 × 12 = 840` qubits; classical measurement record `c` has `4095 × 12 = 49,140` bits.
* Required map (Eq. 38): `U_c|s⟩|0⟩_W = (−1)^{c·bin(e(s))}|s⟩|0⟩_W` — the circuit must *only* apply the parity sign, restore `s`, and clean workspace. It may recover symbols one at a time or compute the parity directly.
* Test distribution: `e ~ |a_e|²` with weight distribution from the principal eigenvector of the tridiagonal matrix of Eq. 42 (`E[wt] ≈ 31.05`, `P[wt = 35] ≈ 2.8%`), positions uniform, nonzero symbols uniform, `c` uniform; `N = 102,400` shots; `ε⁺` = Clopper–Pearson upper bound at confidence `1 − 2^-128` (`ε⁺ ≈ 88.7/N ≈ 8.7e-4` with zero failures).
* Score `S = R(ε⁺)·Q²·T`, `R(ε) = ln 2 / −ln(½ + 2√ε)`; `R = 1.02, 1.06, 1.21, 1.94` at `ε⁺ = 1e-5, 1e-4, 1e-3, 1e-2`; `R(8.7e-4) ≈ 1.19` is the floor; `ε⁺ ≥ 1/16` → no score. **Qubits count squared**: 1% fewer qubits = 2% fewer Toffolis. The 840 syndrome qubits are fixed, so only workspace (1,053 in the baseline) can shrink.
* Baseline (Khattar et al. 2510.10967 EEA decoder, re-implemented in kickmix): (1) synchronised reversible EEA on `z^{2ℓ}` and `S(z)` (Proos–Zalka style register sharing, 5 `O(log n)` degree pointers, `3(n+1)+9 = 222` synchronised steps, unary iteration over pointers), (2) Chien search over all `m = 4095` positions with in-place CNOT updates of `σ, σ', Ω`, Forney's formula with one Itoh–Tsujii inversion of `σ'(α_i^{-1})` per position (351 Toffolis per position), `Z` gates on recovered symbol bits selected by `c_i`, (3) uncompute the EEA. Field multiply = 63-Toffoli Karatsuba (= Qualtran `GF2MulViaKaratsuba(12)`), inversion = Itoh–Tsujii addition chain (315 Toffoli + 48 scaffold qubits), temporary products erased by X-measurement + classically controlled CZ when both factors remain (= Qualtran `GF2MulMBUC`). Polynomials in two arrays of `n + 3` registers of `b` qubits, the input syndrome registers reused. **Q = 1,893 (`2(n+3)b + O(log n)` + scaffold), T = 5,725,461.** Khattar et al.'s own count with a 51-Toffoli multiplier: 5.72e6 Toffoli, 1,885 qubits (Table 6, row `(4095,70,12,2016)`), 1.5e8 Cliffords.

### 4.2 Qualtran bloqs for this benchmark

| Path | Relevance |
|---|---|
| [`qualtran/bloqs/gf_arithmetic/gf2_multiplication.py`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/gf_arithmetic/gf2_multiplication.py) | `GF2Multiplication` (schoolbook `m²`), `GF2MulViaKaratsuba` (`n^{log2 3}`; 63 Tof at m = 12), `BinaryPolynomialMultiplication`, `MultiplyPolyByOnePlusXk`, `GF2MulK` (constant multiply = CNOT only, used for the Chien-search updates by `α^{-r}`), `GF2ShiftRight/Left`, `GF2MulMBUC` (free uncompute), `SynthesizeLRCircuit` (CNOT synthesis via LU, Patel–Markov–Hayes quant-ph/0302002) |
| [`gf2_inverse.py`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/gf_arithmetic/gf2_inverse.py) | `GF2Inverse` Itoh–Tsujii: for m = 12, `k1 = 3`, `t = 3` → 5 multiplications (315 Tof), `2k1 = 6` additions, free Frobenius squarings; junk `m(m−2) = 120` qubits |
| [`gf2_square.py`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/gf_arithmetic/gf2_square.py), [`gf2_addition.py`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/gf_arithmetic/gf2_addition.py), [`gf2_add_k.py`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/gf_arithmetic/gf2_add_k.py) | Clifford-only field ops (squaring/square-root are linear in char 2 — exploited heavily by Gu et al.) |
| [`qualtran/bloqs/gf_poly_arithmetic/`](https://github.com/quantumlib/Qualtran/tree/main/qualtran/bloqs/gf_poly_arithmetic) | Polynomial registers over GF(2^m) (`QGFPoly` dtype, add, add-constant, split/join) — the data layout of the syndrome/locator polynomials |
| [`qualtran/bloqs/multiplexers/unary_iteration_bloq.py`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/multiplexers/unary_iteration_bloq.py), [`qualtran/bloqs/swap_network/`](https://github.com/quantumlib/Qualtran/tree/main/qualtran/bloqs/swap_network) | Pointer-addressed access to polynomial slices (`L − 1` And per loop), `SwapWithZero` for shifting registers by a quantum amount |
| [`qualtran/bloqs/arithmetic/comparison.py`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/arithmetic/comparison.py) (`Equals`, `EqualsAConstant`, `LessThan*`) | zero-tests (root test `σ(β_j) = 0` costs `11` Toffoli on 12 bits = `MultiControlX`/`Equals`), degree comparisons |
| [`qualtran/bloqs/mod_arithmetic/`](https://github.com/quantumlib/Qualtran/tree/main/qualtran/bloqs/mod_arithmetic), [`qualtran/bloqs/cryptography/ecc/`](https://github.com/quantumlib/Qualtran/tree/main/qualtran/bloqs/cryptography/ecc) | Prime-field analogues (Montgomery multiply, `ModInv` via Bernstein–Yang / Kaliski) — the reversible-EEA/ "divsteps" bookkeeping tricks there (history stacks, step-dependent register reuse) are the same ones Gu et al. apply to modular inversion |

### 4.3 Papers

**Jordan, Shutty, Wootters, Zalcman, Schmidhuber, King, Isakov, Khattar, Babbush, "Optimization by decoded quantum interferometry", arXiv:2408.08292 (Nature 646, 831 (2025)).** DQI: for `max f(x) = Σ_i h_i(b_i·x)`, build `Σ_e a_e |e⟩|Bᵀe⟩` over sparse errors, erase `|e⟩` with a syndrome decoder of the dual code, QFT to get `Σ_x P(f(x))|x⟩` with `deg P` = number of correctable errors `ℓ`. For OPI (`m = q − 1` evaluation points, degree-`n` polynomials over `F_q`) the dual code is Reed–Solomon with distance `n + 1`, decodable to `ℓ = n/2` by Berlekamp–Massey; the paper identifies the reversible implementation of the BM shortest-LFSR subroutine as the dominant cost and gives Lemma 9.2 for the optimal degree-`ℓ` polynomial (the tridiagonal matrix used by the verifier to sample error weights).

**Khattar, Shutty, Gidney, Zalcman, Yosri, Maslov, Babbush, Jordan, "Verifiable quantum advantage via optimized DQI circuits", arXiv:2510.10967 (Oct 2025).** End-to-end compilation of DQI for OPI over `GF(2^b)`: qubit-efficient DQI circuit with one reusable `b`-qubit error-value register erased by X-measurement (hence the `(−1)^{c·bin(e)}` sign that this benchmark must cancel); two reversible EEA constructions — *explicit* Bézout coefficients via an optimised Proos–Zalka synchronised EEA (quantum–classical multiplications are CNOT-only over binary fields, so this wins here) and *implicit* access via a linear "dialog representation" of division-free EEA (4n² quantum multiplications, `4nb + O(log² n)` qubits, direct modular division without materialising inverses, Table 4); RS decoding = key equation `σS ≡ Ω mod z^{2ℓ}` via half-EEA (worst case `6⌊n/2⌋ + 5` cycles, App. D.2), Chien search, Forney; sparse Dicke-state preparation by unranking (App. B); GF(2^m) multipliers of 39/47/51 Toffolis for m = 10/11/12 expressed as Parity-Control-Toffolis for lattice surgery (App. C, Table 7) and MBU of GF2 multiplication (App. C.3). Resource table (Table 6): `(4095,70,12,2016)` needs 5.72e6 Toffoli, 1,885 logical qubits, beyond 1e23 classical Extended-Prange trials; physical estimate uses magic-state cultivation, no factories.

**Gu, Kemeny, Yelin, Lukin, arXiv:2610.22367, SI §I.1 "Reed–Solomon decoding for OPI".** Same instance and baseline (their reconstruction: 5.1e6 Toffoli, 1,938 qubits; EEA forward+reverse = 3.8e6). Discovered circuit, 440,000 Toffoli, 1,837 qubits, `TQ` 12× better, 7 wrong signs in 100,000 tests:
  * Berlekamp–Massey instead of EEA (≈140k Toffoli for the locator), with (i) *adaptive coefficient ranges* (classically simulated per-round cutoffs on `deg σ`, failing on rare inputs), (ii) *shared BM updates* — a flag swaps `σ` with the shifted template so both BM cases use one multiply-subtract with multiplier `α` or `α^{-1}`; invariant `σ_0·δ = 1` means no discrepancy register is stored, (iii) *reconstructing BM history* — replace rounds leave `σ_0 = Δ^{-1}` so the discrepancy is recomputed on the reverse pass; only rare retain rounds push to a 1-entry (19-qubit) stack; combined failure 1.4e-4 over 4e8 samples.
  * *In-place evaluator*: `ω = σS mod z^35` overwrites the first 35 syndrome words reversibly (`ω_i = S_{i+1} + Σ_j σ_j S_{i−j+1}`), the last 35 words become zeros usable as workspace — saves a 420-qubit register.
  * *Phase-only error recovery*: `⟨c_j, e_j⟩ = Tr(μ_j e_j)`; the part linear in the syndromes is applied with Clifford Z gates (cancels 71 positions); at the remaining 4,024 positions the phase bit is `Tr(ν_j ω(β_j) Ψ(β_j))`, bilinear → 12 parity-products = 12 Toffolis + 11-Toffoli root test = **23 Toffolis per position** (93k total) versus a 351-Toffoli inversion per position (1.3M) in the baseline.
  * *Precomputed reciprocal*: `Ψ ≡ 1/σ' mod σ` computed once by EEA on half-degree operands using `σ = E² + zO²`, `σ' = O²` in characteristic 2 (square/sqrt are CNOT-only), 17 fixed elimination blocks with quotients parked in cleared words (44k Toffoli each direction), stored in the zeroed syndrome words — no extra qubits.

**Seiler? et al., "A nearly linear-time Decoded Quantum Interferometry algorithm for the Optimal Polynomial Intersection problem", arXiv:2601.15171 (Jan 2026).** Asymptotic improvements: sidesteps quadratic-time Dicke preparation, fast EEA over formal series (App. C: fast RS decoding, parallel remainder–quotient sequences), NTT-based transforms; concurrent with Khattar et al. Relevant mostly as a source of asymptotically faster (half-GCD style) key-equation solvers; constant factors not analysed.

**Gu, Jordan, "Algebraic geometry codes and decoded quantum interferometry", arXiv:2510.06603.** Hermitian codes (block length `q³` over `F_{q²}`) as an alternative to RS, ~1/3 fewer qubits per field element; not directly applicable (the benchmark fixes the RS instance) but their Lanczos-type decoder in Gu et al. 2610.22367 §I.2 shows another division-free decoding style.

**van Hoof, "Space-efficient quantum multiplication of polynomials for binary finite fields with sub-quadratic Toffoli gate count", arXiv:1910.02849.** Karatsuba with `n^{log2 3}` Toffolis, no ancilla, `(10+1/3)n^{log2 3}` CNOT bound; Algorithms 1–4 are implemented 1:1 in Qualtran (`GF2MulK`, `MultiplyPolyByOnePlusXk`, `BinaryPolynomialMultiplication`, `GF2MulViaKaratsuba`).

**Amento, Rötteler, Steinwandt, arXiv:1209.6348; Itoh–Tsujii 1989; Banegas, Bernstein, van Hoof, Lange, "Concrete quantum cryptanalysis of binary elliptic curves" (TCHES 2021, Alg. 2).** Itoh–Tsujii inversion `a^{-1} = a^{2^m − 2}` by an addition chain of `⌊log2(m−1)⌋ + HW(m−1) − 1` multiplications and free Frobenius maps; Qualtran `GF2Inverse` follows these.

**Proos, Zalka, quant-ph/0301141; Häner, Jaques, Naehrig, Roetteler, Soeken, arXiv:2001.09580.** Synchronised reversible EEA with shared shrinking/growing registers; the companion's baseline EEA is an optimised variant.

### 4.4 Ideas to cut `R(ε⁺)·Q²·T`

1. **Switch the key-equation solver from EEA to Berlekamp–Massey** (Jordan et al. 2408.08292 flags BM as the natural choice; Gu et al. 2610.22367 realise it at ≈140k Toffoli vs 1.9M for the EEA locator solve). 70 rounds × (one discrepancy = `≤36` multiply-accumulates + one inversion + one scaled subtraction of `≤36` words). Impact: ×10 on the dominant stage.
2. **Phase-only Forney / trace trick** (Gu et al.): never build `e_j`; compute `Tr(ν_j ω(β_j) Ψ(β_j))` with 12 parity-products per position; precompute `Ψ = (σ')^{-1} mod σ` once via half-degree EEA using `σ' = O²`. Removes 4,095 inversions (1.3–1.4M Toffoli) → 93k. The benchmark contract explicitly allows "computing the required parity directly".
3. **Apply the syndrome-linear part of the mask with Clifford Z gates** (Gu et al.): choose the affine part of `c·bin(e)` offline so 71 positions need no scanning.
4. **Store `ω` in place of the first 35 syndrome words** (reversible overwrite, Gu et al.) and park EEA quotients/`Ψ` in the zeroed upper 35 words: −420 qubits of workspace ⇒ since `Q` is squared this alone is ≈ −35% score relative to a design that allocates them.
5. **Exploit the input distribution with a failure budget**: `R(ε⁺)` is flat near zero — `ε⁺ = 2e-3` costs only `R = 1.31` vs the floor 1.19 — so per-round degree cutoffs, a 1-entry discrepancy stack (19 qubits instead of 665), bounded iteration counts and truncated loops (Gu et al.; same philosophy as Gidney–Ekerå's "allow rare failures") are cheap. Tune cutoffs by classical BM simulation on the exact verifier distribution (Eq. 42 weights, `E[wt] ≈ 31`, worst-case 35 only 2.8%).
6. **Cheaper field multiplier**: Qualtran/van Hoof Karatsuba costs 63 Toffoli at m = 12; Khattar et al. Table 7 give 51 (Maslov–Yosri–Gavinsky modified Karatsuba with a chosen irreducible — note the benchmark fixes `α^12 + α^6 + α^4 + α + 1`, so check which irreducible their 51 assumes; if a different one is needed, a basis change is CNOT-only). Expected −19% on every quantum–quantum multiply; combined with MBU erasure (`GF2MulMBUC`, 0 Toffoli) when both factors survive.
7. **Make quantum–classical multiplications Clifford** (Khattar et al. §II.2.1): multiplication by fixed constants (`α^{-r}` in the Chien search, evaluation of `ω, Ψ` at fixed points, Frobenius powers) is a linear map over `F_2` → `GF2MulK`/`SynthesizeLRCircuit`, 0 Toffoli. Design the scan so that *only* the root test and the 12 bilinear products are non-Clifford (23 Toffoli/position).
8. **Fewer Chien positions**: the root test is needed only at positions where the error can be nonzero — all 4,095 here — but the 71 positions handled by the Clifford mask trick drop out; also note the scan cost "barely depends on `c`" so no per-instance tuning is possible beyond this.
9. **Implicit (dialog) EEA for the `Ψ` solve** (Khattar et al. §II.2.3): division-free, fixed schedule, `4nb + O(log² n)` qubits — good when the operand degree is small (17 after the `E/O` split) and when history must not be stored.
10. **Qubit accounting**: reuse the EEA/BM degree pointers and scaffold; avoid Itoh–Tsujii's `m(m−2) = 120` junk qubits per inversion (Qualtran `GF2Inverse` keeps them; the baseline already trims to 48) by inverting via a 4-register addition chain and MBU of intermediate products; keep the whole workspace below ~1,000 qubits so that `Q ≈ 1,840` (Gu et al. reached 1,837).

Rough target (inferred from Gu et al.): `T ≈ 4.4e5`, `Q ≈ 1,837`, `ε⁺ ≈ 2e-4` → `S ≈ 1.1 × 1,837² × 4.4e5 ≈ 1.6e12` vs baseline `1.19 × 1,893² × 5.73e6 ≈ 2.4e13`.

---

## 5. Benchmark III — `dfthcsos` (angle oracles for the DFTHC sum-of-squares block encoding of FeMoCo)

### 5.1 Contract and score (companion paper §III.3, App. A)

* Hamiltonian: spin-free electronic structure `H = Σ h¹_{pq}E_{pq} + ½Σ h²_{pqrs}E_{pq}E_{rs}`, FeMoCo-76 (`N = 76` spatial orbitals, `η = 113`), symmetry shift `(S, β₁)` fixed to the baseline (BLISS-style, Eq. 46), reference upper bound `E_upper = −22140.27335 Ha`.
* DFTHC factorisation (Eqs. 48–53): ranks `(R, B, C)`; unit vectors `u_b^{(ρ)}` (`ρ ∈ [R]`, `b ∈ [B]`), weights `w_b^{(ρc)}`, identity offsets `W^{(ρc)}`; `X^{(ρc)} = Σ_b w_b u_b u_bᵀ`, `h̃² = Σ_{ρc} X^{(ρc)} ⊗ X^{(ρc)}`; one-body part absorbed exactly (Eq. 52). Sum-of-squares form `H − E_SOS·I = Σ O†O` with generators `D₁, Q₁` (one-body ± eigenspaces) and `SF` (Eqs. 93–96).
* Cost quantities: `Λ = ‖h¹′‖_* + ¼Σ_{ρc}(|w_B| + Σ_b|w_b|)²` (Eq. 56/87), `E_SOS` (Eq. 57), `E_gap = E_upper − E_SOS` (Eq. 76), `λ_eff = sqrt(E_gap(2Λ − E_gap))` (Eq. 61/77).
* Constraints: `ε₁ = ‖h̃¹′ − h¹′‖_F ≤ 20 mHa`, `ε₂ = ‖Σ X⊗X − h² − 𝒯(S₀)‖_F ≤ 20 mHa` (Eqs. 74–75); `Λ > 49.0 Ha`, `E_gap > 3.914898 Ha`, `0 < E_gap < 2Λ`; each `Angle_k` circuit ≤ 128 qubits, no `Z_POW` allowed in it.
* Submission artefacts: `K = ⌈(N−1)/J⌉` kickmix circuits `Angle_k` with named registers `selection` (`⌈log2(N + RB)⌉` qubits; addresses `a < N` = one-body eigenvectors, `a ≥ N` = the `RB` vectors `u_b^{(ρ)}`) and `word_0..word_{J−1}` (`β` qubits each, fixed point in `[0, 2)`, 1 integer bit); the verifier reads `β` and `J` from the registers. `Angle_0` loads batch 0; `Angle_k` XORs batch `k` over batch `k−1` in place; the reverse traversal re-applies them backwards and ends with `Angle_0` clearing the register. Plus an `.npz` with `(U, W, H2_I, H1_I, Hsym_lower, tree_edges)` — (inferred) `U` = the `N + RB` unit vectors, `W` = `w_b^{(ρc)}, W^{(ρc)}`, `H2_I/H1_I` = integrals, `Hsym_lower` = the fixed symmetry shift `S₀` (lower triangle) / `β₁`, `tree_edges` = the rooted child-ordered Givens tree `(p_t → q_t)`.
* Verification of angles: every address simulated forward and backward, 64 shots; `u_a = TreeMajoranaCoefficients(𝒯, θ_a)` (Eq. 66–68: `u_q ← u_p sin θ`, `u_p ← u_p cos θ` along parent-before-child edges, 2(N−1) multiplications) rebuilds the vectors from the decoded `β`-bit angle words, from which `X^{(ρc)}`, `h¹′`, `Λ`, `E_SOS` are recomputed.
* Score `𝒮 = λ_eff × T_tot × Q_tot` (Eq. 44/78): `T_tot` = simulated Toffolis of all `Angle_k` (one forward + one reverse traversal) + heuristic Toffolis of `Outer`, `Inner` ("Inner/Outer Prep" rows of Low et al. Table 3) + `N − 1` Givens rotations priced as `b_t`-bit controlled adders at `2b_t − 1` Toffoli each (App. A.1 — note per-edge widths `b_t`); `Q_tot` = persistent qubits (state-prep registers + `J·b_rot` angle words) + the largest temporary workspace among `Outer`, `Inner`, `Angle_k` (they run sequentially and share it); `Q_tot` is not capped at 128. Block-encoding order (Eq. 100): `Outer → [decode → Inner → spin select] → {Angle_k → Givens batch k}_k → Majorana select → {inverse Givens → Angle_k}_k → [Inner† → reflect, square] → Outer†`; cost `C_BE = ν_out C_out + ν_in C_in + Σ_k ν_ang,k C_ang,k(J) + C_fixed(𝒯, N, J, b_rot)` (Eq. 101).

### 5.2 Qualtran bloqs for this benchmark

| Path | What it provides |
|---|---|
| [`qualtran/bloqs/chemistry/thc/select_bloq.py`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/chemistry/thc/select_bloq.py) | `THCRotations(num_mu, num_spin_orb, num_bits_theta, block_size, two_body_only, angles_data)` — the closest existing analogue of an `Angle` oracle + Givens batch: QROAM (`block_size` = `kr1/kr2` of Lee et al. Eq. 34/35) loads `N/2 − 1` angles of `β` bits selected by `μ` (plus the `nu_eq_mp1` flag for one-body terms), prepares a phase gradient, applies `RealGivensRotationByPhaseGradient` on JW-adjacent pairs (a *path* tree), uncomputes; `_leaf_tensor_to_givens_rotations(eta, num_bits_theta)` computes the integer angle words from THC leaf vectors (von Burg Eq. 57). `SelectTHC` wires it with `CSwap` spin swaps and `ApplyControlledZs` (CCZ/CCCZ on the "root" orbital) |
| [`qualtran/bloqs/chemistry/df/select_bloq.py`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/chemistry/df/select_bloq.py), [`df/prepare.py`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/chemistry/df/prepare.py), [`df/double_factorization.py`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/chemistry/df/double_factorization.py) | DF block encoding (Lee et al. Fig. 15–16, App. C): `OuterPrepareDoubleFactorization` (uniform + `QROAM(L+1, n_L + ℵ)` + ineq + swaps), `OutputIndexedData` (`QROAM(L+1, n_Ξ + n_{LΞ} + b_r + 1)`), `InnerPrepareDoubleFactorization` (`7n_Ξ + 2b_r − 6` + `Add` + `QROAM(LΞ + N/2, n_Ξ + ℵ + 2)` + `ℵ + n_Ξ`), `ProgRotGateArray` (`QROAM(LΞ + N/2, N β/2) + (n_{LΞ} − 1) + N(β − 2)`), reflection `n_N + 1` bits. Reproduces 21,753 − (reflection) Toffolis for FeMoCo (`N = 108`, `L = 360`, `Ξ_tot = 13,031`, `ℵ = 10`, `β = 16`) in `resource_estimation.ipynb` |
| [`qualtran/bloqs/chemistry/quad_fermion/givens_bloq.py`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/chemistry/quad_fermion/givens_bloq.py) | `RealGivensRotationByPhaseGradient(b)`: explicit Clifford frame (`X, S, CNOT, H`) + two `RzViaPhaseGradient` = `2(b − 2)` Toffoli; `ComplexGivensRotationByPhaseGradient` adds an `Rz(φ)`. Module docstring states the von Burg decomposition `V_{Q_q} = Π V_{n−1,n−2}…V_{1,0}` with one rotation per edge of a *line* |
| [`qualtran/bloqs/rotations/programmable_rotation_gate_array.py`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/rotations/programmable_rotation_gate_array.py) | von Burg's batched angle loading: `κ`-qubit ancilla, `⌈MB/κ⌉ + 1` QROM reads, `MB` controlled rotations — the same "stream angles in batches of `J` words" structure as the competition's `Angle_k` family |
| [`qualtran/bloqs/data_loading/qrom.py`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/data_loading/qrom.py), [`select_swap_qrom.py`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/data_loading/select_swap_qrom.py), [`qroam_clean.py`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/data_loading/qroam_clean.py) | The lookup itself: `QROM` (unary iteration, `N_addr − 1` Toffoli, `log N_addr` ancilla, variable spacing for repeated words), `SelectSwapQROM`/`QROAMClean` (`N/K + (K−1)b`, `(K−1)b` extra qubits), `QROAMCleanAdjoint` (MBU erase `N/K + K − 4`) |
| [`qualtran/bloqs/chemistry/black_boxes.py`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/chemistry/black_boxes.py) | `QROAM`, `QROAMTwoRegs`, `get_qroam_cost_clean_ancilla` — literature-matching placeholder costs (OpenFermion-compatible), handy for reproducing the competition's heuristic Inner/Outer costs |
| [`qualtran/bloqs/state_preparation/state_preparation_alias_sampling.py`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/state_preparation/state_preparation_alias_sampling.py), [`prepare_uniform_superposition.py`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/state_preparation/prepare_uniform_superposition.py), [`qualtran/bloqs/chemistry/thc/prepare.py`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/chemistry/thc/prepare.py) | The "Outer"/"Inner" state preparations (coherent alias sampling: uniform + QROM(alt, keep) + `LessThanEqual(μ)` + `CSwap`; `UniformSuperpositionTHC` `10 log(M+1) + 2b_r − 9` target) |
| [`qualtran/bloqs/chemistry/resource_estimation.ipynb`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/chemistry/resource_estimation.ipynb), [`qualtran/surface_code/thc_compilation.ipynb`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/surface_code/thc_compilation.ipynb) | FeMoCo-108 THC walk ≈ 10,880 Toffoli (SELECT dominant, 94% of PREPARE is QROM; rotations `108 × 14` vs QROM 402); Lee et al. physical costing (6.67e9 Toffoli, 696 qubits, 4 CCZ factories) |
| [`qualtran/bloqs/rotations/phase_gradient.py`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/rotations/phase_gradient.py), [`rz_via_phase_gradient.py`](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/rotations/rz_via_phase_gradient.py) | `AddIntoPhaseGrad` (`b − 2`), `ControlledAddOrSubtract` — the competition's "`b_t`-bit controlled adder, `2b_t − 1` Toffoli" per Givens rotation is Qualtran's `CAdd` cost |

### 5.3 Papers

**Low, King, Berry, Han, DePrince, White, Babbush, Somma, Rubin, "Fast quantum simulation of electronic structure by spectrum amplification", arXiv:2502.15882 (PRX 15, 041016 (2025)).** If `H − E_SOS = Σ_α O_α†O_α` (sum of squares) and the ground state lies `E_gap` above `E_SOS`, a block encoding of the rectangular matrix `(O_α)` gives a walk whose effective normalisation is `λ_eff = sqrt(E_gap(2Λ − E_gap)) ≈ sqrt(2ΛE_gap) ≪ Λ`, so phase estimation needs `π λ_eff/(2ε)` steps instead of `π Λ/(2ε)`. SOS representations come from level-2 (quadratic) spin-free SOS algebras found by SDP/optimisation that lower-bound the energy; combined with the new **DFTHC** factorisation (`h² ≈ Σ_{ρc} X^{(ρc)}⊗X^{(ρc)}`, `X^{(ρc)} = Σ_b w_b^{(ρc)} u_b^{(ρ)}u_b^{(ρ)ᵀ}` — DF when `B = N`, THC when `C = 1`) and BLISS. Block-encoding components (App. B): `Rot` ≈ `N + RB` Toffoli per call (QROM over `x_o`/`b` of `(N−1)b_rot` angle bits, erased for `R + B`), `Qroam` ≈ `RBC/(λ+1) + λ b_Q`, `Sel` ≈ `4(N−1)b_rot` (two `U_Rot`, each `2(N−1)b_rot`), `4N` controlled swaps for spin, 7 Toffolis for the Majorana on a single qubit, reflections `⌈log(B+1)⌉ + b_k2 + 1` and `⌈log(N+RC)⌉ + ⌈log(B+1)⌉ + b_k1 + b_k2 + 2`. **FeMoCo-54 (`N = 54`, `(R,B,C) = (10,27,27)`, `b_rot = 15`): 9,997 Toffoli per walk step, 1,131 qubits; Outer PREP 310 Tof (50 persistent / 110 temp), Inner PREP 1,154 Tof (53 / 313), RPREP (angle QROM) 361 Tof with 795 persistent angle qubits, SEL 3,295 Tof (ROT `4·15·53 = 3,180`), REF 67.** Headline: FeMoCo-54 3.41e8 Toffoli / 1,137 qubits, FeMoCo-76 9.99e8 / 1,459 (4.3× fewer Toffolis than symmetry-compressed THC), `b_rot ≈ 10–15` suffices (App. D randomised rounding), Toffoli cost of block encodings scales ∼`N^0.96`, `E_gap ∼ N^0.88`.

**King, Low, Babbush, Somma, Rubin, "Quantum simulation with sum-of-squares spectral amplification", arXiv:2505.01528.** General SOSSA framework: energy/phase estimation with query complexity ∝ `sqrt(Λ·E_gap)`, optimality proof, SOS optimisation by SDP, worked SYK example (`√N` speedup). Conceptual background for why `λ_eff` is the right multiplier in the score.

**Lee, Berry, Gidney, Huggins, McClean, Wiebe, Babbush, "Even more efficient quantum computations of chemistry through tensor hypercontraction", arXiv:2011.03494 (PRX Quantum 2021).** THC block encoding with `Õ(N)` Toffolis per step: contiguous index `s = ν(ν+1)/2 + μ` (Eq. 29), coherent alias sampling over `M(M+1)/2 + N/2` entries with QROAM blocks `k_r1, k_r2` (Eqs. 34–35), SELECT = QROM of `N/2` Givens angles indexed by `μ` + rotations by addition into a phase gradient (`N(i − 2)` Toffoli for `i`-bit angles, Fig. 7), CCZ on the rotated orbital, `i`-qubit phase-gradient register kept in the operating area. Also the DF (App. C, Fig. 15–16; listings 1–4 pages 51–54) and SF/sparse costings Qualtran implements, and the FeMoCo surface-code compilation (`6.67e9` Toffoli, 696 qubits, 3 days, 4M physical qubits).

**von Burg, Low, Häner, Steiger, Reiher, Roetteler, Troyer, "Quantum computing enhanced computational catalysis", arXiv:2007.14460 (PRR 2021).** Double factorisation `V = Σ_r (Σ_k f_k^{(r)} U^{(r)} n_k U^{(r)†})²` block encodings with Toffoli ∼`N^{3/2}`; basis changes implemented by fermionic Givens rotations whose angles are loaded by a *programmable rotation gate array* (§VII.B.1 p.45: angles as `β`-bit words, loaded `κ` at a time, each bit controls a rotation by `2^{-j}π`); Eq. 57 gives the Givens angles for a unit vector, Eq. 73 the controlled rotation; QROM-with-dirty-qubits variants (`d/(1+λ) + λb + O(log d)`); FeMoCo-type catalysts at `∼10^10` Toffolis / 4,000 qubits.

**Berry, Gidney, Motta, McClean, Babbush, "Qubitization of arbitrary basis quantum chemistry leveraging sparsity and low rank factorization", arXiv:1902.02134 (Quantum 2019).** Appendix A/B: QROAM with dirty (`2⌈d/k⌉ + 4bk`) and clean (`⌈d/k⌉ + b(k−1)`, `(k−1)b` ancilla) qubits; Appendix C Theorem 3: *measurement-based uncomputation* of a lookup in `⌈d/k⌉ + k` Toffolis with `k + ⌈log(d/k)⌉` clean ancilla (or `2⌈d/k⌉ + 4k` with dirty), optimum `≈ 2√d` — the basis of Qualtran's `QROAMCleanAdjoint` and of the competition's reverse-traversal savings; also sparse-state alias sampling (Eqs. 43–44).

**Babbush, Gidney, Berry, Wiebe, McClean, Paler, Fowler, Neven, "Encoding electronic spectra in quantum circuits with linear T complexity", arXiv:1805.03662 (PRX 2018).** Unary iteration (`4L − 4` T, `log L` ancilla), QROM Fig. 1/7, the `And` gate with free uncompute (Fig. 4), uniform superposition (Fig. 12, `10 log L + 2K` T), coherent alias sampling (§III.D), `SELECT` via Majorana accumulators (Fig. 9/14), qubitization walk and Heisenberg-limited QPE (Fig. 2).

**Jiang, Sung, Kechedzhi, Smelyanskiy, Boixo, arXiv:1711.05395; Kivlichan, McClean, Wiebe, Gidney, Aspuru-Guzik, Chan, Babbush, "Quantum simulation of electronic structure with linear depth and connectivity", arXiv:1711.04789 (PRL 2018).** (1711.05395 fetched; 1711.04789 not fetched, cited from memory.) Givens-rotation networks: any single-particle basis rotation `U(Q)` is a product of `O(N²)` Givens rotations on JW-adjacent modes in `O(N)` depth; a *single* column/vector (Slater determinant with one orbital, or the rotated Majorana `γ_u = Σ u_p γ_p`) needs only `N − 1` rotations along a path (`N/2` per spin in Lee et al. Eq. 51). The competition generalises the path to an arbitrary rooted tree 𝒯 (companion App. A.1) — `u_q ← u_p sin θ`, `u_p ← u_p cos θ`.

**Loaiza, Izmaylov, "Block-invariant symmetry shift (BLISS)", arXiv:2304.13772; Rocca et al., "Reducing the runtime of fault-tolerant quantum simulations in chemistry through symmetry-compressed double factorization", arXiv:2403.03502 (symmetry compression of DF, FeMoCo-54 2.6e9 Toffoli); Caesura et al., arXiv:2501.06165 (symmetry-compressed THC, FeMoCo-76 4.3e9 Toffoli, 1,512 qubits).** (Not fetched; cited via Low et al. Table 1.) Shifting `H → H − Σ(N̂ − η)·S`-type symmetry operators lowers `Λ` without changing the η-particle spectrum; the companion fixes this shift `(S₀, β₁)` so it is not a lever here, but the "Hsym" term in the `.npz` is exactly this object (inferred).

**Gu et al. 2610.22367 §IV "Quantum chemistry simulation".** For a *sparse* Fe₂S₂ block encoding (41,052 Pauli terms) they cut the data-dependent part from 55,000 to 15,000 Toffolis (126 qubits): *frame-block Select* (group Pauli terms related by fixed Clifford frames, pay once per block + controlled frames) and *alias tables with repeated rows* (choose among the many alias tables realising the same distribution the one with repeated 34-bit words so the QROM can merge rows). The second trick transfers directly to `Angle_k` tables (choose angle words/tree to maximise repeats; Qualtran's `QROM._break_early` costs exactly the merged-segment count).

### 5.4 Ideas to cut `λ_eff × T_tot × Q_tot`

1. **Minimise `λ_eff` first** — it multiplies everything, and the floors (`Λ > 49`, `E_gap > 3.9149`) put the best attainable value at ≈ 19.2 Ha. Follow Low et al. §IV: optimise `(u, w, W)` for `λ_eff` subject to `ε_fro < 20 mHa` (a loose tolerance compared with the 0.3–1.6 mHa they use), increase the SOS gap via the `W^{(ρc)}` identity offsets and the one-body `D₁/Q₁` split, select `(R, B, C)` by the "Amdahl/linear-scaling" heuristic (`C = Θ(N)`, `B` moderate, `R` small), randomised rounding to `β` bits (App. D).
2. **Shrink the address space `N + RB`** of the angle oracles (dominant simulated cost: a plain QROM costs ≈ `N + RB − 1` Toffoli per call and each `Angle_k` is called twice per block encoding, `K = ⌈(N−1)/J⌉` oracles) — prefer small `R·B` and large `C` since `C` only enters the heuristic Inner cost `RC⌈(B+1)/2^k⌉ + 2^k b₂` (Low et al. Table 8).
3. **Reduce angle precision `β` / use per-edge widths `b_t`**: the Givens heuristic is `2b_t − 1` per edge and traversal, so `β: 15 → 10` cuts the rotation term by a third and the persistent `J·β` word qubits proportionally; the verifier only checks 20 mHa Frobenius errors (Low et al. App. D show `b_rot ≈ 10–12` keeps energy errors ≪ 1 mHa). Edges whose angles are tiny for *all* addresses can get narrow words (inferred from App. A.1 "`b_t`-bit controlled adder").
4. **Choose the tree 𝒯 so vectors are sparse in tree coordinates**: with parent-before-child ordering only edges on the path from the root to the support of `u` carry nonzero angles; a star/bushy tree rooted at a high-weight orbital makes most angles zero for most addresses → repeated words → variable-spaced QROM merges (Babbush 2007.07391 Fig. 3; Gu et al. "repeated rows") and narrow `b_t`. Caveat: Givens rotations on a tree still cost `N − 1` adders unless the verifier lets zero-width words drop edges (check the harness) (inferred).
5. **Batch size `J` vs the 128-qubit cap**: `Q_tot` includes `J·β` persistent angle words, `T_tot` includes `2K` oracle calls; with `β = 15`, `J ≤ 7` fits the cap (selection ≈ 9 + words 105 + unary-iteration ancilla ≈ 9); with `β = 10`, `J ≈ 11`. Sweep `J` with the exact score formula; also consider non-uniform batches (e.g. last batch smaller).
6. **XOR-difference loading and address ordering** (companion App. A.1): since `Angle_k` XORs batch `k` over batch `k−1`, QROM CNOT counts (not Toffolis) depend on Hamming distances — irrelevant for the score but ordering addresses/batches so that many *words* repeat across addresses reduces the unary-iteration tree (Toffolis) through segment merging.
7. **SelectSwap/QROAM inside the cap** (Low–Kliuchnikov–Schaeffer 1812.00954; Berry 1902.02134; Qualtran `SelectSwapQROM`, `QROAMClean`): with `K = 2`, cost `(N+RB)/2 + J·β` and `J·β` extra ancilla — e.g. `β = 10, J = 5`: 50 words + 50 swap ancilla + 9 selection + ~10 ≈ 120 qubits, cost `≈ 0.5(N+RB) + 50` instead of `N + RB` (−40% at `N + RB ≈ 450`). The reverse traversal of a QROAM can use the MBU adjoint (`N/K + K`) *if* the harness accepts a different circuit for the reverse pass; otherwise keep `K` where forward = reverse.
8. **Exploit the two-level structure of the `RB` vectors**: vectors are indexed by `(ρ, b)`; a QROM over `ρ` of "which sub-table" plus a QROM over `b` (nested unary iteration, Qualtran multi-dimensional `QROM` with `selection_shape = (R, B)`) costs `R·B` Toffoli like a flat table but allows per-`ρ` trees/precisions; alternatively make the `B` vectors of one `ρ` share a common prefix of rotations (e.g. `u_b^{(ρ)}` all inside a low-dimensional subspace) so the first few batches are address-independent on `ρ` (inferred).
9. **One-body addresses**: the `N` one-body vectors are eigenvectors of `h¹′` (orthonormal); they can be ordered so that successive eigenvectors differ in few tree angles, or the one-body term can be absorbed differently (e.g. smaller `N₊/N₋` split) — only the verifier's `ε₁ ≤ 20 mHa` matters, so low-weight eigenvectors can be truncated to very few bits (inferred).
10. **Reuse Qualtran to reproduce the heuristic costs** before optimising: `QROAM`/`QROAMTwoRegs` placeholders (`black_boxes.py`), `PrepareUniformSuperposition`, `StatePreparationAliasSampling`, `THCRotations.from_hamiltonian_coeffs` (angle quantisation) and `RealGivensRotationByPhaseGradient` give the same formulas as Low et al. Tables 7–9, so the full `𝒮` can be evaluated offline for any `(R, B, C, β, J, 𝒯)` without running the verifier.

---

## 6. Cross-cutting techniques (apply to all three)

* **Temporary AND + measurement-based uncompute** (Gidney 1709.06648; Babbush 1805.03662 Fig. 4): compute `AND` with 1 Toffoli, erase with `HMR` + classically-controlled `CZ`. Qualtran: `And`/`And†`, `MultiAnd`, `OutOfPlaceAdder(is_adjoint=True)`, `LinearDepthHalf*`; kickmix: `CCX` + `HMR` + `CZ if b`. Budget rule: every forward Toffoli whose inputs still exist at uncompute time should cost 0 on the way back.
* **Lookup erasure by MBU** (Berry 1902.02134 App. C; Qualtran `QROAMCleanAdjoint`): erase an `N`-entry lookup for `≈ 2√N` Toffolis instead of `N`; Gu et al. use it for the 128-line table (17 vs 126) and for the DQI products.
* **Truncated fixed-point multiplication** (Sanders 2007.07391 App. D): `d² − d − 1` instead of `2d² − d`; choose `d_A = d_B`; justify bit widths by exhaustive simulation.
* **Phase gradient vs rotations** (Sanders App. A; Gidney 1709.06648): `b − 2` Toffoli per phase but a persistent `b`-qubit resource; good when many rotations share the register (chemistry Givens), bad when `Q` is scored and only ~40 rotations are needed (`invsqrt`).
* **Variable-spaced / merged-row QROM** (Babbush 2007.07391 Fig. 3; Qualtran `QROM._break_early`): cost = number of maximal constant aligned segments − 1; design tables (coefficients, alias words, angle words) to have repeats.
* **Failure budgets** (Gidney–Ekerå 2021; Gu et al. 2026): where the score tolerates `ε⁺ > 0` (`dqi`), size stacks/loops/degree bounds for the typical case; where it does not (`invsqrt`, `dfthcsos` angle checks), exploit exhaustive classical verification to tune bit widths to the edge.
* **Cost accounting**: Toffoli-equivalents `C = Toffoli + T/4`; `CSWAP` = 1 Toffoli in kickmix (not 7 T); `Z_POW` of Clifford/T angle free/1 T; `R` (reset) on a `|1⟩` qubit randomises the phase and will be caught by the verifier.

---

## 7. Paper index (arXiv ids) and where they were used

| arXiv | Authors / title (short) | Used for |
|---|---|---|
| 2610.23832 | Khattar, Rubin, Gidney, Broughton, Low, Babbush — competition companion | §3–5 contracts, baselines, score formulas |
| 2308.12352 | Rubin et al. — stopping power for ICF | `invsqrt` algorithm, coefficients, costs |
| 1204.0567 | Jones et al. — faster chemistry simulation on FT computers | Newton–Raphson, QVR, phase kickback |
| 2105.12767 | Su et al. — first-quantised chemistry | squaring/sum-of-squares/product lemmas |
| 2007.07391 | Sanders et al. — compilation of FT heuristics | fixed-point multiply costs, phase gradient, variable-spaced QROM |
| 1805.12445 | Häner, Roetteler, Svore — optimizing circuits for arithmetic | piecewise polynomial (HRS) baseline (not fetched) |
| 2203.10064 | Kliuchnikov et al. — shorter circuits via 1-qubit approximation | rotation pricing |
| 2610.22367 | Gu, Kemeny, Yelin, Lukin — LLM-discovered circuits | best-known numbers for Coulomb, RS decoder, sparse chemistry |
| 2408.08292 | Jordan et al. — DQI (Nature 2025) | DQI/OPI, error-weight distribution |
| 2510.10967 | Khattar et al. — optimized DQI circuits | RS decoder baseline, GF(2^m) multipliers (39/47/51), dialog EEA, Table 6 |
| 2601.15171 | nearly linear-time DQI for OPI | fast RS decoding over formal series |
| 2510.06603 | Gu, Jordan — AG codes and DQI | Hermitian alternative |
| 1910.02849 | van Hoof — space-efficient GF(2^m) Karatsuba | Qualtran GF2 multipliers |
| 1209.6348 | Amento, Rötteler, Steinwandt — binary EC arithmetic | Itoh–Tsujii inversion |
| quant-ph/0301141, 2001.09580, 2306.08585 | Proos–Zalka; Häner et al. — EC discrete log circuits | synchronised EEA, AddK, comparators |
| 2502.15882 | Low et al. — spectrum amplification + DFTHC | `λ_eff`, DFTHC block-encoding cost tables |
| 2505.01528 | King et al. — SOSSA | SOS framework |
| 2011.03494 | Lee et al. — THC | THC/DF/SF/sparse block encodings, Givens by phase gradient |
| 2007.14460 | von Burg et al. — computational catalysis | DF, programmable rotation gate array |
| 1902.02134 | Berry et al. — sparsity and low rank | QROAM, MBU lookup erasure |
| 1805.03662 | Babbush et al. — linear T complexity | unary iteration, QROM, And, alias sampling |
| 1812.00954 | Low, Kliuchnikov, Schaeffer — dirty qubits | SelectSwapQROM, CSwapApprox |
| 1711.05395 / 1711.04789 | Jiang et al. / Kivlichan et al. — Givens networks | basis rotations by Givens rotations |
| 1709.06648 | Gidney — halving the cost of addition | adders, And, Hamming-weight phasing |
| 2304.13772, 2403.03502, 2501.06165 | Loaiza–Izmaylov (BLISS); Rocca et al.; Caesura et al. | symmetry shifts / compressed DF & THC (not fetched) |
| 2409.04643 | Harrigan et al. — Qualtran | the library itself |

Local copies of all fetched papers (text extracted) are in
`/tmp/claude-0/-home-user/af1e8b3b-1af8-51dd-9e8d-ec3f80eabc0b/scratchpad/papers/` (`<id>.txt`, plus `.html`/`.pdf`).

## 8. Qualtran file index (clone paths)

Prefix `/tmp/claude-0/-home-user/af1e8b3b-1af8-51dd-9e8d-ec3f80eabc0b/scratchpad/upstream/qualtran-full/`:

* `qualtran/bloqs/chemistry/trotter/grid_ham/{inverse_sqrt.py, potential.py, kinetic.py, qvr.py, trotter_costs.ipynb, trotter.ipynb}`
* `qualtran/bloqs/arithmetic/{multiplication.py, addition.py, subtraction.py, controlled_addition.py, comparison.py, negate.py, bitwise.py, hamming_weight.py, conversions/contiguous_index.py, error_analysis_for_fxp_arithmetic.ipynb, t_complexity_of_comparison_gates.ipynb}`
* `qualtran/bloqs/data_loading/{qrom.py, qrom_base.py, select_swap_qrom.py, qroam_clean.py}`
* `qualtran/bloqs/multiplexers/unary_iteration_bloq.py`, `qualtran/bloqs/swap_network/{swap_with_zero.py, cswap_approx.py}`
* `qualtran/bloqs/rotations/{phase_gradient.py, zpow_via_phase_gradient.py, rz_via_phase_gradient.py, quantum_variable_rotation.py, hamming_weight_phasing.py, phasing_via_cost_function.py, programmable_rotation_gate_array.py, programmable_ancilla_rotation.py}`
* `qualtran/bloqs/mcmt/{and_bloq.py, multi_control_pauli.py, controlled_via_and.py}`; `qualtran/resource_counting/_bloq_counts.py` (And = 1 Toffoli, And† = measurement)
* `qualtran/bloqs/gf_arithmetic/{gf2_addition.py, gf2_add_k.py, gf2_multiplication.py, gf2_square.py, gf2_inverse.py, gf_utils.py}`, `qualtran/bloqs/gf_poly_arithmetic/*`
* `qualtran/bloqs/chemistry/{df, thc, sf, sparse}/*.py`, `qualtran/bloqs/chemistry/quad_fermion/givens_bloq.py`, `qualtran/bloqs/chemistry/black_boxes.py`, `qualtran/bloqs/chemistry/resource_estimation.ipynb`, `qualtran/surface_code/thc_compilation.ipynb`
* `qualtran/bloqs/state_preparation/{state_preparation_alias_sampling.py, prepare_uniform_superposition.py}`
* `kickmix/`, `docs/kickmix/*.md`, `dev_tools/kickmix/`, `kickmix/src/kickmix/py/circuit/subs/gf_arithmetic_test.py`
