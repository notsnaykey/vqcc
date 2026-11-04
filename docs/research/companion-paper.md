# Companion paper: "Leveraging verifiable structure in quantum circuits to find more efficient compilations with agentic AI"

**arXiv:2610.23832** (v1 16 Oct 2026, v2 21 Oct 2026; this report is based on v2, which is what the PDF, HTML and e-print serve today).
Authors: Tanuj Khattar, Nicholas C. Rubin, Craig Gidney, Michael Broughton, Guang Hao Low, Ryan Babbush (Google Quantum AI, Santa Barbara). 30 pages, revtex one-column.

Local copies (untrusted downloads, read-only):
`/tmp/claude-0/-home-user/af1e8b3b-1af8-51dd-9e8d-ec3f80eabc0b/scratchpad/papers/2610.23832/paper.pdf`, `.../paper.txt` (pdftotext), `.../src/main.tex` + `.../src/GH_notes/*.tex` (v2 LaTeX), `.../src_v1/` (v1 LaTeX), `.../all.bib`.

Page references below are PDF page numbers of v2; section numbers follow the PDF table of contents (Sec. II = kickmix, Sec. III = Kaggle competition with III.A/B/C = Benchmarks I/II/III, Sec. IV = Outlook, App. A = DFTHC circuits, App. B = 1/sqrt(x) baseline circuits). Equation labels are the LaTeX labels from the source where the PDF number is not load-bearing.

> **Important scoping note.** The paper is a *benchmark-definition / reference-implementation* paper. It contains **no description of the authors' agentic method** (no model names, prompts, loops, branching policy, compute budget, attempt counts, verified fraction), **no quantitative results** of their internal AI runs, and **no list of discovered tricks**: it only commits to their best internal runs via SHA-256 hashes and says "significant improvements over the previously published baselines" were found. Every item below marked **"not in paper"** is genuinely absent from v1 and v2. The closest thing to "what agents found" is the authors' pointer to Gu et al. arXiv:2610.22367 (Sec. "Acknowledgments", p. 22), which independently optimised the same benchmarks with LLMs and which we should read next.

---

## 0. One-page summary

| | Benchmark I: 1/sqrt(x) phasing | Benchmark II: RS syndrome decoder (DQI) | Benchmark III: FeMoCo DFTHC angle oracles |
|---|---|---|---|
| Target map | `|x>|0> -> exp(2 pi i beta/sqrt(x)) |x>|0>`, x in [1, 3,133,452], 22-bit register `"x"`, beta = 1 | `U_c |s>|0>_W = (-1)^{c . bin(e(s))} |s>|0>_W` for RS dual code [4095,4025,71] over F_{2^12}, l = 35 | K kickmix circuits `Angles_k`: `|a>|z> -> |a>|z xor Delta-theta_a^[k]>`, J angle words of beta bits, selection register ceil(log2(N+RB)) qubits |
| Reference cost | Q = 260 qubits, 7,735 Toffoli, 1 T, 37 non-Clifford Z_POW; C = 7,988 Tof-eq; **score 2.08e6** | Q = 1,893 qubits, T = 5,725,461 Toffoli; eps+ ~ 8.7e-4 (k=0), R ~ 1.19; **score ~ 2.44e13** (derived) | **not in paper** (no baseline T_tot, Q_tot, lambda_eff, R/B/C, b_rot, J for FeMoCo given) |
| Score | S = Q x C, C = Toffolis + T/4; rotations priced 0.56 log2(1/eps) + 5.3 T each | S = R(eps+) Q^2 T, R = ln2 / (-ln(1/2 + 2 sqrt(eps))) | S = lambda_eff x T_tot x Q_tot, lambda_eff = sqrt(E_gap (2 Lambda - E_gap)) |
| Pass criterion | all x in [1,xmax], 64 shots each (200,540,928 shots), **k = 0 failures**, phase within tol(x) = 2^-24 beta/sqrt(x) turns | N = 102,400 shots, k >= 0 allowed, eps+ from Clopper-Pearson at 1 - 2^-128; eps+ >= 1/16 -> no finite score | every address, forward and reverse, 64 shots/address; eps_1, eps_2 <= 20 mHa; Lambda > 49.0 Ha; E_gap > 3.914898 Ha; <= 128 qubits per Angles_k; no Z_POW |
| Explicitly "improvable" per authors | polynomial choice/range, QROM coefficient precision, "completely different route" of direct polynomial on input domain | "Every part of this baseline ... can be improved": explicit remainder storage, pointer-driven EEA, polynomial-basis F_{2^12} arithmetic, per-position Itoh-Tsujii inversion; 51-Toffoli multiplier exists | ranks (R,B,C), vectors, weights, angle precision b_rot, batch size J, tree, angle-loading circuits |

---

## 1. The kickmix circuit model (Sec. II, pp. 3-6)

### 1.1 Gate set (Sec. II.A, p. 3)

"Every instruction in this family maps any computational basis state to a single computational basis state up to a scalar phase", so a classical simulator stores one bit per qubit wire, one bit per classical wire, and one scalar phase. Four instruction classes (verbatim list from p. 3):

1. **Reversible classical gates**: `X, CX, CCX, SWAP` (permute basis states).
2. **Diagonal phase gates**: `Z, CZ, CCZ, Z_POW, NEG` (update the tracked phase when all controls are 1).
3. **Measurement and reset**: `HMR` ("hammer": Hadamard, Z-measure, reset to |0>) and `R` (reset).
4. **Classical bit ops**: `BIT_STORE0, BIT_STORE1, BIT_INVERT`.

Every instruction can be controlled per gate (`if b`) or across blocks via a condition stack (`PUSH_CONDITION`/`POP_CONDITION`); it runs only when all active classical conditions hold 1.

### 1.2 HMR / measurement-based uncomputation (Eq. `hmr_kickback`, p. 3)

`|x>|f(x)> --HMR--> (-1)^{b f(x)} |x>|0>`, b uniformly random. When b = 1 a classically controlled diagonal gate (`Z, CZ, CCZ, NEG`) fixes the phase. Example: uncomputing a temporary AND `|x1 ^ x2>` costs one HMR plus a classically controlled CZ, saving a Toffoli (Gidney 2018). **Simulator semantics that matter for us:** HMR on a qubit holding 1 samples b, flips the phase if `q_t . b = 1`, resets. Without a matching fixup the shot fails with probability 1/2 whenever q_t = 1. `R` on a qubit in |1> also applies a random sign flip: "preventing circuits from silently discarding uncleaned junk qubits". So junk can never be thrown away for free; dirty resets are caught with prob 1/2 per shot (64 shots per input in Benchmarks I and III make this ~2^-64 to slip through).

### 1.3 Simulator engineering (Sec. II.B, p. 4) and speed

- C++20 with Python bindings inside Qualtran. Struct-of-arrays storage grouped by operand count; 1-byte opcodes with bit flags selecting operand arrays; binary `.kmb` serialization that dumps arrays as contiguous blocks.
- Simulation bit-packs **64-512 trajectories across SIMD registers**; every instruction updates a whole batch of shots, **except `Z_POW`**, which keeps a 128-bit fixed-point phase accumulator per trajectory and loops over active shots sequentially. (So Z_POW-heavy circuits simulate slower; relevant only for Benchmark I.)
- Speed numbers (p. 3): builds at **2 x 10^7 instructions/s**, simulates at **6.0 x 10^10 instructions/s** on one CPU core; builds the 86M-gate DQI circuit in < 5 s; checks 102,400 syndrome-decoder shots in 150 s.
- Builder API: automatic downgrading (quantum/classical/constant operands interchangeable, no-ops on False controls dropped), NumPy-style broadcasting over `km.array` registers, dynamic workspace allocation within a configurable qubit budget (freed qubits are reused), library of subroutines: temporary-AND, QROM lookups, adders, comparators, finite-field arithmetic, context-managed unary iteration, each with paired compute / measurement-based-uncompute variants. Inspection utilities: circuit diagrams and **interactive SVG flame charts of Toffolis and qubits per nested subroutine** (use these to find hotspots).

### 1.4 Verification: fuzz testing + Fiat-Shamir (Sec. II.C, pp. 5-6)

- Simulate on basis inputs with `km.Simulator`; exhaustive when the domain is small (Benchmark I enumerates all 3.1M inputs; Benchmark III enumerates all addresses), sampled otherwise (Benchmark II). Sampling certifies a bound on the per-input failure probability eps, which "naturally accommodates approximations ... such as dropping low-weight carry bits, truncating intermediate registers, or bounding iteration counts to save Toffolis".
- **State-distance bound** (Eq. `branch_robustness`, p. 5): fix the m HMR/R outcomes r; the circuit is a map V_r; Kraus operators 2^{-m/2} V_r; eps = E_r[eps_r] with eps_r the |alpha_x|^2-weight of failing inputs. Under the assumption that each V_r is injective on the support (true when every HMR/R acts on a qubit that is a function of the others), `||W|psi> - U|psi> (x) |+>^m||^2 <= 4 eps`, fidelity >= (1 - 2 eps)^2, **trace distance <= 2 sqrt(eps)**, which also bounds total-variation distance of any later measurement. The verifier must sample inputs from |alpha_x|^2, so each benchmark fixes its input distribution. Footnote: accepting phases within tau turns adds <= 2 pi tau to the bound (negligible at benchmark tolerances).
- **Fiat-Shamir**: SHA-256 of the raw `.kmb` bytes seeds a deterministic PRNG; in competition the digest is **combined with a private salt** to defeat seed grinding by appending no-ops. Verification is non-interactive and reproducible once the salt is published.
- **Per-shot checks (p. 6, verbatim)**: "1. Input and output registers hold their expected classical bitstrings. 2. Every scratch qubit returns cleanly to |0>. 3. The accumulated output phase matches the target phase within the benchmark tolerance."
- **Confidence bound** (Eq. `binomial_tail`): with k failures in N shots, one-sided Clopper-Pearson eps+ at delta = 2^-128: `sum_{j<=k} C(N,j) eps+^j (1-eps+)^{N-j} = delta`. For k = 0, eps+ ~ ln(1/delta)/N ~ **88.7/N**: N = 10,240 -> eps+ = 1%; N = 102,400 -> 0.1% (precisely 8.66e-4). "Depending on the benchmark, the verifier either requires k = 0 ... or allows k >= 0 failures and uses the certified upper bound eps+ to compute the repetition overhead."

### 1.5 The "verifiable structure" argument (Sec. I, p. 2)

Checking equivalence of general circuits is coNP-complete classically / QMA-complete quantumly (Janzing et al.), intractable above ~40 qubits; but the cost-dominating subroutines of fault-tolerant algorithms (integer arithmetic, lookup tables, syndrome decoders) "do not use arbitrary quantum interference internally". Precedent: the secp256k1 ECC paper (arXiv:2603.28846) withheld circuits but released simulator + harness + ZK proof; the `ecdsa.fail` challenge then had >100 participants, "most without a quantum computing background", use AI coding agents to **roughly halve Toffoli counts** (Long et al. arXiv:2609.28882, record-and-replay arithmetic). Non-kickmix parts (state preparation in Benchmark III) are priced with analytic formulas so the score still reflects the whole algorithm.

---

## 2. Benchmark I: 1/sqrt(x) phasing for first-quantised Coulomb simulation (Sec. III.A, pp. 6-10; App. B, pp. 26-30)

### 2.1 Problem statement and provenance

- Context: Trotterised first-quantised dynamics for stopping power / inertial confinement fusion (Rubin et al. PNAS 2024). The e-e term V = sum_{i != j} 1/|r_i - r_j| is applied pairwise: compute V(r_i, r_j) into a register, phase by e^{-i delta V}, uncompute (Jones et al. 2012 Eqs. 15-17). C(eta, 2) pairs make it the dominant Trotter-step cost.
- Input to the benchmark subroutine is w = (x_i - x_j)^2 + (y_i - y_j)^2 + (z_i - z_j)^2 already computed upstream (costs 3 n_p^2 - n_p - 1 Toffolis, Su et al. Lemma 8; not part of the benchmark). Coordinates are n_p-bit sign-magnitude; w occupies 2 n_p + 2 bits.
- **Benchmark size**: n_p = 10 (eta = 218 electrons), **22-bit input x in [1, 3(2^10 - 2)^2] = [1, 3,133,452]**. Range starts at 1 because the state is antisymmetrised (two electrons never share a lattice site). (The fusion paper used n_p = 6, 14-bit w in [1, 11532].)
- **Precision**: "24-bits of relative error" on 1/sqrt(x) (from the total time-evolution error analysis of Rubin et al.). 1/sqrt(x) at x_max ~ 5.6e-4 needs ~11 leading fractional zeros at n_p = 10, so naive fixed point would need 35 fractional bits.
- The Quake III `Q_rsqrt` (one Newton-Raphson step from a bit-hacked initial guess; max rel. error 0.00175228 over 32-bit floats) is the inspiration; the quantum version is fixed point.

### 2.2 Verification contract (Sec. III.A.3, p. 10; quoted definitions)

- Submission: a single `.kmb` file implementing `|x>|0> -> exp(2 pi i beta/sqrt(x)) |x>|0>` for every x in [1, max x]; defaults n_p = 10, **beta = 1**, register width 2 n_p + 2 = 22, max x = 3,133,452.
- "The circuit must declare exactly one named quantum register `"x"` of 22 distinct qubits; all remaining qubits are unnamed scratch that must return to |0>, and `"x"` must be restored to |x>."
- "Every input x in [1, max x] is simulated `shots_per_x = 64` times (200,540,928 shots in total)" with PRNG seeded from SHA-256(canonical .kmb) + competition salt.
- Phase check: tracked phase theta(x) in turns mod 1, 64-bit fixed point (uint64 units of 2^-64 turns), compared to exact integer arithmetic `floor(2^65 beta/sqrt(x)) = isqrt(floor(2^130 beta^2 / x))`.
- **"Every shot must pass (k = 0 failures) within tolerance tol(x) = 2^-24 beta/sqrt(x) turns."** (absolute tolerance in turns = relative tolerance 2^-24 on the value). Note tol(1) = 2^-24 turns while tol(x_max) = 3.37e-11 turns = 2^-34.8.
- **Score**: `S = Q x C`, Q = total qubit count, `C = Toffolis + T/4` = mean Toffoli-equivalent cost per shot. "Clifford Z_POW angles are free, T-angles cost 1 T, and each of the n_rot finer Z_POW rotations is priced analytically via mixed fallback synthesis at 0.56 log2(1/eps) + 5.3 T-gates [Kliuchnikov et al. 2023], where eps = pi min_x(tol(x) - |error(x)|)/n_rot splits the remaining phase-error margin evenly across all rotations." So the rotation price depends on the *worst-case leftover margin* across all x: arithmetic error eats into rotation budget.

### 2.3 Reference construction (Sec. III.A.2, pp. 8-10; App. B)

Pipeline: `|x> --shift by 2s--> x_norm --QROM + cubic Horner--> y_0 --NR--> p = y_0 (3 - x_norm y_0^2)/2 --<< s--> y_1 = p 2^s --Z_POW + uncompute--> e^{2 pi i/sqrt(x)} |x>`.

1. **Normalisation** (App. B.2, pp. 27-28): count leading zero *pairs* s (stored in **unary/thermometer** in an n_p-qubit register f_0..f_{n_p-1}); x_norm = x 2^{2s} in [1,4) so 1/sqrt(x_norm) in (0.5,1]. Implementation: for k = 0..n_p-1, test whether the top two bits are 00 (X gates + clean AND into f_k), then controlled left shift by 2 realised as controlled **cyclic rotation by 1 of the even and odd bit lanes** (L-1 CSWAPs per lane of L qubits; the wrapped-around zero cleans the vacated low bits without ancillas). Truncated loop: lane length n_p + 1 - k at step k. Cost **n_p(n_p+1) CSWAP = 110 + n_p AND = 10 -> 120 Toffoli-eq forward** at n_p = 10; reverse uses 110 CSWAPs, the flag ANDs uncompute free by measurement.
2. **Initial guess y_0** by cubic polynomials: on [1,1.5] `P_a(x) = a0 - a1(x-1) + a2(x-1)^2 - a3(x-1)^3`, on [1.5,2] `P_b(x) = b0 - b1(x-1.5) + ...` with
   a = (0.99994132489119882162, 0.49609891915903542303, 0.33261112772430493331, 0.14876762006038398086),
   b = (0.81648515205385221995, 0.27136515484240234115, 0.12756148214815175348, 0.044753028579153842218).
   [2,4) is handled by u = x_norm/2 and rescaled coefficients a_i -> a_i/2^{(2i+1)/2}, offsets (x-2) and (x-3) (App. B.1). Fig. 1 (p. 9): the cubic guess has abs. error ~1e-5 to 6e-5 on range 1 and ~1e-5 on range 2; after one NR step ~1e-9 (range 1) and ~1e-10 (range 2), "within double precision one step of Newton-Raphson is sufficient for 2^-24 relative error".
   **QROM**: 4 entries addressed by the three MSBs of x_norm (b13 b12 b11 at n_p=6): cost **2 Toffolis** (two ANDs decode t_a = !b13 ^ b11, t_b = b13 ^ b12, then CNOT fan-out controlled on {1, b13, t_a, t_b} into |c0>..|c3>). Delta x needs no separate register: only its 0.5s-place bit `b13 ^ b11` (1 AND); other fractional bits are read from x_norm.
3. **Horner in place**: c2 -= T(c3 Dx); c1 -= T(c2 Dx); c0 -= T(c1 Dx) -> y_0 in |c0> (T(.) drops partial-product bits below the target LSB). Each Dx bit controls a row: AND multiplicand slice into a shared scratch register, subtract in place, uncompute row ANDs by measurement. **1,071 Toffolis** at n_p = 10 (954 at n_p = 6).
4. **NR step** rewritten in normalised variables (Eq. `last_nr_mult_xnorm`): y_1 = (1/2)(y_0 2^s)(3 - x_norm y_0^2). Squaring T(y_0^2) into 28 bits: **442 Toffolis** (diagonal bits copied by CNOT, doubled cross terms added row by row). z = T(x_norm T(y_0^2)) into 30 qubits: **1,043 Toffolis** (719 at n_p=6); 3 - z in two's complement via X gates + add (3<<28)+1: **28 Toffolis**. p = T(y_0 z) ~ 2/sqrt(x_norm) into the bottom 30 bits of y_1: **867 Toffolis**. Shift y_1 = p << s in place by controlled cyclic left shifts on 31-qubit slices controlled on f_k: **30 n_p CSWAP = 300**. "Shifting after the multiplication keeps the final multiplier width independent of n_p, saving 30 n_p AND gates per direction."
5. **Phasing**: one Z_POW of 2^{j-F} turns on each bit j of y_1, F = 30 + n_p = 40. Then run everything in reverse.

Bit widths (App. B.3, p. 29): 14 bits of Dx (all 12 fractional bits at n_p=6; 14 of the 20 at n_p=10), 17 fractional bits for QROM coefficients and Horner intermediates, 28 fractional bits for y_0^2, 28 + 2 integer = 30 qubits for z and 3 - z, 29 + 1 = 30 qubits for p, 30 + n_p = 40 qubits for y_1; one shared 30-qubit scratch register for partial products.

**Reference totals (p. 10)**: Q = 260, 7,735 Toffolis, 1 T, 37 non-Clifford Z_POW (the 40 bits of y_1 give 2 Clifford + 1 T + 37 priced rotations), **C = 7,988**, **S = 2.08 x 10^6**, worst-case relative error 2.84e-8 = 2^-25.07 at x = 2,588,411.

Derived breakdown (my arithmetic from the stage counts above):

| Stage (forward) | Toffoli-eq |
|---|---|
| normalise (ANDs + CSWAPs) | 120 |
| QROM + Dx bit | 3 |
| Horner (3 truncated multiplies, 14 x 17 bit) | 1,071 |
| square y_0^2 (28 bit) | 442 |
| z = x_norm y_0^2 (22 x 28 -> 30 bit) | 1,043 |
| 3 - z | 28 |
| p = y_0 z (17 x 30 -> 30 bit) | 867 |
| shift << s | 300 |
| **forward sum** | **3,874** |
| reverse (implied: 7,735 - 3,874) | 3,861 |
| rotations: 37 x ~27.3 T + 1 T -> /4 | ~253 |

The implied synthesis cost 27.3 T per rotation corresponds to eps ~ 1.5e-12 per rotation, i.e. the leftover margin min_x(tol - |err|) is ~1.7e-11 turns. Multiplications are ~88% of the Toffolis; the uncompute is a full second copy.

### 2.4 Authors' own list of what is improvable (p. 8, verbatim-ish)

"Our baseline implementation is merely a starting point ... For example, not using a cubic polynomial over a small rescaled range but a simpler polynomial over a larger range may reduce cost further. Also the accuracy of coefficients output by QROM can be further optimized. One could imagine going a completely different route and simply finding a good polynomial approximation over the input domain."

---

## 3. Benchmark II: Reed-Solomon syndrome decoding for DQI / OPI (Sec. III.B, pp. 10-14)

### 3.1 Problem statement

- **OPI**: given allowed sets F_i subset F_q at the m = q - 1 nonzero points alpha_i, find degree < n polynomial Q_x maximising f(x) = |{i : Q_x(alpha_i) in F_i}|; |F_i| = r. Classically verifiable advantage candidate (Jordan et al. Nature 2025; Khattar et al. arXiv:2510.10967). Related to RS list recovery and noisy polynomial interpolation.
- B_ij = alpha_i^j (m x n); Bx is an RS code; DQI needs a **syndrome decoder for the dual code C^perp = ker(B^T), parameters [m, m-n, n+1]**, correcting up to l errors, unique when 2l <= n. Eqs. `dqi_qft_def` - `dqi_fourier_syndrome` (pp. 11-12) derive why degree-l P(f(x)) corresponds to decoding l errors: before the final QFT the basis states are syndromes s = B^T e of weight <= l errors.
- **MBUC construction** (Khattar et al.): error symbols e_i are prepared one at a time in a single b-qubit register, added to the syndrome, then X-measured and reset, leaving sign (-1)^{c . bin(e)} with c the 49,140-bit classical measurement record. The decoder's job in this benchmark is to **undo that sign** (Eq. `dqi_measurement_phase`).
- **Contract (Eq. `dqi_benchmark_contract`, p. 12)**: `U_c |s>|0>_W = (-1)^{c . bin(e(s))} |s>|0>_W` with s = B^T e(s), wt(e(s)) <= l. Each test supplies s (quantum register) and c (classical bits); e is withheld. "Implementations may recover error symbols one at a time or compute the required parity directly."

### 3.2 Instance parameters (Sec. III.B.2, p. 12)

- **(m, n, b, r) = (4095, 70, 12, 2016)**, r = (2^b - 2^{b/2})/2 (bent-function constraint size). Dual code **[4095, 4025, 71] over F_{2^12}**, **l = n/2 = 35**.
- Syndrome: **70 x 12 = 840 qubits**; record c: 4095 x 12 = **49,140 classical bits**.
- Field: F_{2^12} = F_2[alpha]/(alpha^12 + alpha^6 + alpha^4 + alpha + 1), **little-endian polynomial basis** (1, alpha, ..., alpha^11); evaluation points alpha_j = alpha^j, j = 0..m-1; syndromes **s_i = sum_j e_j alpha^{(i+1) j}, i = 0..n-1** (i.e. b_0 = 1 convention: first syndrome uses alpha^{1 j}).

### 3.3 Reference decoder (pp. 12-13)

1. **Key equation via EEA** on z^{2l} and S(z) = sum s_j z^j, stop when remainder degree < l: sigma(z) S(z) = Omega(z) mod z^{2l}; sigma proportional to prod(1 - alpha_i z); zero syndrome -> sigma = 1, Omega = 0. Uses an optimised variant of **Proos-Zalka synchronised EEA** sharing registers between shrinking remainders and growing Bezout coefficients, temporary quotients in free register space.
2. **Chien search + Forney**: evaluate sigma(alpha_i^{-1}) at all m positions (in-place CNOT updates of sigma, sigma', Omega); at a zero, Forney gives e_i from Omega and sigma'; apply Z gates to recovered symbol bits selected by c_i; clear workspace.
3. **Uncompute EEA**, restoring s and W.

Data layout: polynomials in two arrays of n + 3 registers of b qubits (the n syndrome registers are reused in the first array); five O(log n)-qubit degree pointers; **3(n+1) + 9 = 222 synchronised EEA steps**, each using unary iteration over pointers to address/shift active slices. Field ops: addition, squaring, multiplication by fixed powers of alpha are F_2-linear -> CNOTs (free). Quantum x quantum multiply: **63-Toffoli Karatsuba**; inversion: **Itoh-Tsujii addition chain, 315 Toffolis, 48 scaffold qubits**. "When both factors of a temporary field product stay in memory, the circuit erases that product by X-basis measurement and classically controlled CZ gates" (free uncompute of bilinear products). Step 2: **one Itoh-Tsujii inversion of sigma'(alpha_i^{-1}) per position, 351 Toffolis per position** x 4095 = 1,437,345 Toffolis = **25% of total**.

**Reference totals**: **Q = 1,893** (2(n+3)b + O(log n) + inversion scaffold = 876 workspace + 840 syndrome + pointers/scaffold), **T = 5,725,461 Toffolis** (v1 said 5,730,597; corrected in v2). Khattar et al. reported 5.2e6 with a hand-tuned **51-Toffoli F_{2^12} multiplier** instead of 63. "Every part of this baseline---explicit remainder storage, pointer-driven EEA steps, polynomial-basis F_{2^12} arithmetic, and per-position Itoh-Tsujii inversion---can be improved."

### 3.4 Verification and score (Sec. III.B.3, pp. 13-14)

- Failures are allowed: a decoding failure only lowers the probability of sampling a good candidate (candidates are classically checked). Trace distance 2 sqrt(eps) -> single-run success p >= 1/2 - 2 sqrt(eps) (Eq. `dqi_success_bound`, with p_0 = 1/2 defined via "at least as many constraints as the median output of an ideal DQI run").
- **Test distribution**: e ~ |a_e|^2 with weight distribution Pr[wt = w] = v_w^2, v the principal eigenvector of the (l+1)x(l+1) tridiagonal matrix `A_{w,w} = w(q - 2r)/sqrt(r(q-r))`, `A_{w-1,w} = sqrt(w(m-w+1))` (Eq. `dqi_weight_matrix`, Lemma 9.2 of Jordan et al.). Positions uniform without replacement, nonzero symbols uniform in F_q \ {0}. **E[wt(e)] ~ 31.05, Pr[wt = 35] ~ 2.8%.** Note q - 2r = 4096 - 4032 = 64 so the diagonal is small and the weight distribution is concentrated near l. c is uniform. Target phase (-1)^{c . bin(e)}.
- **N = 102,400 shots**, eps+ from Eq. `binomial_tail` at 1 - 2^-128.
- **Score (Eq. `dqi_score`)**: `S = R(eps+) Q^2 T`, `R(eps) = ln(1 - p_0)/ln(1 - (p_0 - 2 sqrt(eps))) = ln 2 / (-ln(1/2 + 2 sqrt(eps)))`. Q = total qubits (syndrome + workspace), T = single-run Toffolis including cleanup. "a 1% reduction in qubits improves the score as much as a 2% reduction in Toffoli gates." R values quoted: eps+ = 1e-5, 1e-4, 1e-3, 1e-2 -> 1.02, 1.06, 1.21, 1.94. **eps+ >= 1/16 -> no finite score.** Zero failures -> eps+ ~ 8.7e-4 -> floor **R ~ 1.19 for every exact submission**.

Derived table (Clopper-Pearson at delta = 2^-128, N = 102,400; my computation):

| failures k | eps+ | R(eps+) | score penalty vs k=0 |
|---|---|---|---|
| 0 | 8.66e-4 | 1.191 | 0 |
| 1 | 9.10e-4 | 1.197 | +0.5% |
| 5 | 1.05e-3 | 1.213 | +1.8% |
| 10 | 1.19e-3 | 1.229 | +3.2% |
| 20 | 1.43e-3 | 1.255 | +5.3% |
| 50 | 2.02e-3 | 1.313 | +10% |
| 100 | 2.87e-3 | 1.389 | +17% |
| 200 | 4.35e-3 | 1.510 | +27% |
| 500 | 8.31e-3 | 1.813 | +52% |
| 1000 | 1.43e-2 | 2.297 | +93% |

**Baseline score (derived)**: Q^2 T = 1893^2 x 5,725,461 = 2.05e13; x R(8.66e-4) = 1.191 -> **S ~ 2.44e13**.

Takeaway: a heuristic that fails on ~1e-4 of inputs (~10 failures) costs only ~3% in score, so approximations that save > 3% of Q^2 T are net wins; failing on all weight-35 inputs (2.8%) would cost ~4x and is not an option.

---

## 4. Benchmark III: QROM angle oracles + Majorana rotations for FeMoCo DFTHC-SOS block encoding (Sec. III.C, pp. 14-22; App. A, pp. 24-26)

### 4.1 Framing (Sec. III.C.1-2, p. 14)

- Spectrum-amplification / DFTHC (double-factorised THC) sum-of-squares block encoding of Low et al. PRX 2025 (doi 10.1103/pb2g-j9cw). The tensor network is fixed; the participant chooses its dimensions (R, B, C), the vectors, the weights, the angle precision, the batching of angle loads, and the kickmix circuits that load angles. State preparation (Outer, Inner) and the Givens rotations are **black boxes with heuristic costs** ("too many possible implementations, and most of them would be difficult to verify").
- **Molecule: FeMo-co, N = 76 orbitals, eta = 113 electrons** (Sec. III.C.7, p. 20). Symmetry shift (S, beta_1) fixed to the provided baseline's (v2 change: "any submitted shift is ignored").
- Provided: variational upper bound on ground-state energy, raw one- and two-electron integrals, a reference factorisation "that does not necessarily satisfy the accuracy requirements", a reference QROM-based compilation of the Boolean oracles, a reference address->bitstring map, a reference tree.

### 4.2 DFTHC factorisation (Sec. III.C.3, pp. 15-17; file `GH_notes/dfthc_integrals_optimization_target.tex`)

- Hamiltonian Eq. `chem_ham`: H = sum h^(1)_pq E_pq + 1/2 sum h^(2)_pqrs E_pq E_rs. Spectrally-equivalent shifted form in the eta-particle manifold with symmetric S and scalar beta_1.
- Inputs: (h^(1), h^(2), R, B, C, H_sym, eps_DFTHC = 20 mHa = 2.0e-2 Ha).
- For rho in [R], b in [B]: unit vectors u_b^(rho) in R^N; for (rho, c): weights w_b^(rho c), identity offset W^(rho c). `X^(rho c)_pq = sum_b w_b^(rho c) u_b,p u_b,q`; `h~^(2)_pqrs = sum_{rho,c} X^(rho c)_pq X^(rho c)_rs`. L = RC "squares"; the B vectors are shared within each group of C copies.
- H_DFTHC (Eq. `dfthc-hamiltonian`) = sum h^(1)'_pq E_pq + 1/2 sum_{rho c}(W I + sum X E)^2 - (eta beta_1 + 1/2 sum |W|^2) I, with **exact one-body absorption** h^(1)' = h^(1) - (eta/2) S + beta_1 delta - sum W^(rho c) X^(rho c) (Eq. `exact-one-body-absorption`): only the two-body tensor is approximated. Error eps_fro = ||h^(2) - h~^(2) + (S (x) I + I (x) S)/2||_F.
- **LCU one-norm** (Eq. `dfthc-normalization`): `Lambda = ||h^(1)'||_* + 1/4 sum_{rho c} (|w_B^(rho c)| + sum_b |w_b^(rho c)|)^2`, w_B = W + sum_b w_b, ||.||_* Schatten-1.
- **SOS shift**: `E_SOS = -eta beta_1 - (||h^(1)'||_* - Tr h^(1)') - 1/2 sum |W|^2`, so H_DFTHC - E_SOS I >= 0. E_gap = E_gs - E_SOS in [0, 2 Lambda]; delta_gap = E_gap/Lambda; g_amp = sqrt(delta_gap(2 - delta_gap)); **lambda_eff = Lambda g_amp = sqrt(E_gap (2 Lambda - E_gap))** (Eq. `effective-normalization`).
- Optimisation target (boxed Eq. `dfthc-optimization`): min lambda_eff s.t. eps_fro < 20 mHa, ||u|| = 1. Implementation-aware outer objective C_BE(R,B,C) x lambda_eff.
- Efficient Frobenius evaluation (Eq. `fro-contraction`): eps_fro^2 = ||h2||^2 - 2 sum_l x_l^T H2 x_l + sum_{l,m} (x_l^T x_m)^2, cost O(N^4 + LBN^2 + LN^4 + L^2 N^2); dominant O(RCN^4).

### 4.3 Boolean angle oracles (Sec. III.C.4, p. 17; III.C.6 pp. 19-20)

- K = ceil((N-1)/J) kickmix circuits `Angles_k`, k in [K]. Registers: `selection` of **ceil(log2(N + RB))** qubits taking a < N + RB (first N addresses = one-body eigenvectors, last RB = two-body vectors u_b^(rho)); `word_0 ... word_{J-1}`, each **beta qubits**, a fixed-point angle in [0, 2) (1 integer bit, beta - 1 mantissa bits; theta/pi encoded as vartheta in {0,1}^{b_rot}); the verifier reads beta and J from the registers. All other qubits workspace, start and end |0>. **No Z_POW allowed** (phases multiples of pi only).
- Action (Eq. `angle`): `Angles_k |a>|z> -> |a>|z xor Delta-vartheta_a^[k]>`, where Delta-vartheta^[0] = vartheta^[0] and Delta-vartheta^[k] = vartheta^[k] xor vartheta^[k-1] for k > 0 (angles with index t >= N - 1 are zero). Batch label is hard-wired (no coherent k register). "for k > 0, a register holding vartheta^[k-1] is changed directly into vartheta^[k], eliminating a separate inter-batch uncomputation." Forward traversal costs C_ang^pass(J) = sum_k C_ang,k(J); the reverse traversal walks backwards and ends with Angles_0 clearing z. Each oracle is self-inverse. J = 1 streams one angle; J = N - 1 loads all at once; J "changes ancillas, latency, and cost, but not the represented Hamiltonian".
- Verification: "The family of oracles is simulated for every input in the `selection` register, once forward and once in reverse, with 64 shots per address", checking consistent angle words, unchanged addresses, clean workspace, corrected phases. **Each Angles_k circuit may use at most 128 qubits in total.**

### 4.4 Tree Majorana rotations (Sec. III.C.5, pp. 17-19; App. A.1, p. 24)

- Rooted child-ordered tree T on N vertices (root 0), edges e_k = (p_k -> q_k) in parent-before-child order; sibling order matters. Givens rotation G_vw(theta) = exp[(theta/2)(gamma_v0 gamma_w0 + gamma_v1 gamma_w1)] with convention (gamma_v, gamma_w) -> (cos theta gamma_v + sin theta gamma_w, -sin theta gamma_v + cos theta gamma_w). U_T(theta) = prod_k G (left to right increasing k). Then U^dagger gamma_{0,x} U = sum_v u_v gamma_{v,x} with the unit vector u computed classically (Eq. `tree_planar_alg`): start u = e_0, for each edge (u_p, u_q) <- (c u_p - s u_q, s u_p + c u_q); since u_q = 0 when its parent edge is processed, u_q <- u_p sin theta_k, u_p <- u_p cos theta_k (Eq. `tree_simplified_update`); product form Eq. `tree_child_product`: A_{w_j} = A_v (prod_{l<j} cos theta_{v w_l}) sin theta_{v w_j}, u_v = A_v prod_l cos theta_{v w_l}. For the path 0->1->...->N-1 this is the usual sequential line construction.
- **Givens cost heuristic (App. A.1)**: "The quantum circuit implementing the t-th Givens rotation is a b_t-bit controlled adder. The Toffoli count of each adder is assumed to be 2 b_t - 1." The N - 1 rotations appear forward and inverse per block encoding (pipeline Eq. `pipeline`).

### 4.5 Block-encoding structure and cost accounting (App. A.2-A.4, pp. 24-26)

- SOS generators: O_{D1,j} = sqrt(w_+j)(gamma_u0 + i gamma_u1)/2 and O_{Q1,j} = sqrt(w_-j)(gamma_u0 - i gamma_u1)/2 for positive/negative eigenpairs of h^(1)', and O_{SF,rc} = (1/sqrt2)(w_B I + (i/2) sum_{b,sigma} w_b gamma_{u_b sigma 0} gamma_{u_b sigma 1}); H_DFTHC - E_SOS = sum O^dagger O; E_SOS = -2 sum w_-j - 1/2 sum |W|^2; Lambda = half the sum of squared generator norms over both spins.
- Outer address x_o in [N + RC]: r for D1 (r < N_+), N_+ + r for Q1, N + rC + c for SF. Inner selects b < B (rotated Majorana) or b = B (identity). **Vector address mu in [N + RB]** = the `a` of the angle oracle.
- Pipeline (Eq. `pipeline`): Outer -> [decode -> Inner -> spin select] -> {Angles_k -> Givens batch k}_k -> Majorana select -> {inverse Givens batch k -> Angles_k}_{k reversed} -> [Inner^dagger -> reflect and square] -> Outer^dagger.
- Cost accounting (Eq. `cost-accounting`): C_BE = nu_out C_out + nu_in C_in + sum_k nu_ang,k C_ang,k(J) + C_fixed(T, N, J, b_rot); in the standard schedule every Angles_k is called once per direction -> angle contribution 2 C_ang^pass(J).
- Heuristic black-box costs: Inner Prep and Outer Prep rows of **Table 3 of Low et al. (pb2g-j9cw)** - values **not reproduced in the paper**.

### 4.6 Verification and score (Sec. III.C.2 p. 14-15 and III.C.7 p. 20)

- **Score**: `S = lambda_eff x T_tot x Q_tot`, lambda_eff = sqrt(E_gap (2 Lambda - E_gap)). "T_tot is the simulated Toffoli count of the Angles_k circuits over one forward and one reverse traversal plus the heuristic Toffoli costs of Outer, Inner, and the N - 1 Givens rotations, and Q_tot is the number of persistent qubits (the state-preparation registers and the J b_rot angle-word registers) plus the largest temporary workspace among Outer, Inner, and the Angles_k circuits, which run sequentially and share it." Q_tot is **not capped at 128**; the 128 cap applies per Angles_k circuit ("keeps the interesting part of optimizing Inner dominant, and in our previous resource estimates gives a balanced physical cost, e.g. 200k physical qubits and < 1 day").
- Verifier recomputes vectors from decoded words via TreeMajoranaCoefficients, builds X^(rho c) and h^(1)', matches decoded one-body vectors to eigenvectors of h^(1)' and reconstructs h~^(1)' with the ideal eigenvalues. Acceptance: **eps_1 = ||h~^(1)' - h^(1)'||_F <= 0.020 Ha** and **eps_2 = ||sum X (x) X - h^(2) - T(S_0)||_F <= 0.020 Ha**, T(S_0) = (S_0 (x) I + I (x) S_0)/2.
- E_gap = **E_upper - E_SOS with fixed core-inclusive E_upper = -22140.27335 Ha**; lambda_eff from that. Floors: **0 < E_gap < 2 Lambda, E_gap > 3.914898 Ha, Lambda > 49.0 Ha**; "these floors rule out degenerate factorizations that shrink the normalization or the gap to game lambda_eff, which itself has no separate floor"; "values are not clamped to the floors"; failed checks -> infinite score. "The original baseline passes with unchanged score. These checks constrain coefficient errors and resource costs; they do not certify a 20 mHa many-electron energy error."
- Derived: lambda_eff is increasing in both Lambda and E_gap (for E_gap < Lambda), so the floors imply **lambda_eff >= sqrt(3.914898 x (98 - 3.914898)) = 19.19 Ha**. The specificity of 3.914898 suggests the floors sit at (or just below) the baseline factorisation's own values, i.e. the lambda_eff lever may already be near-exhausted and the score must come from T_tot x Q_tot (verify against the Kaggle data).
- v1 -> v2 change: v1 scored `sqrt(E_gap(2 Lambda - E_gap)) x [Toffolis(Angles + heuristics)] x min{qubits, 128}` with qubits counting only the Angles width; v2 replaced this with the T_tot x Q_tot definition above, added the floors, added the explicit named `word_j` registers (v1 had a single `target` register of beta J qubits), the no-Z_POW rule, forward+reverse simulation with 64 shots, and the fixed (S, beta_1).

**Not in paper**: baseline (R, B, C), b_rot, J, tree shape, Lambda_0, E_gap_0, lambda_eff_0, T_tot_0, Q_tot_0, C_out, C_in formulas, the address->bitstring map. All must come from the Kaggle data / Table 3 of Low et al.

---

## 5. The agentic-AI method

**Not in paper.** The paper contains no description of models, agents, prompts, loop structure, branching/exploration policy, compute budget, attempt counts, or verified fractions. What it does say:

- Sec. I: "AI coding agents [AlphaEvolve] can automate this search if a fast test harness checks each candidate circuit and scores its resource cost in a closed loop."
- Sec. II.B: kickmix is designed so "humans and AI agents iterate on 10^8-gate circuits in seconds"; flame charts of Toffolis/qubits per subroutine are provided.
- Sec. III (p. 6): "In our own runs with AI coding agents, we have found significant improvements over the previously published baselines, and we expect further improvements remain to be discovered. For each benchmark, we commit to our best internal run via its SHA-256 hash ... and will release our full solutions at the end of the competition." Hashes: I `4b98f38a52a01fc125da7fc2847f9698abe192519dccf894fd758eccc8f37cea`, II `0701f553a9ac4e8af100f66acfccf2fc82cf5a44c2e5aa765b1d4ace01cbaadb`, III `9b8d070f41dd3b6e10a69dbbae9b047847646d1540de30c7b75799f15692f644`. **$150,000 prize pool.**
- Acknowledgments (p. 22): "Our internal results show that all three benchmarks can be further improved beyond the circuits reported to date [i.e. beyond Gu et al. 2610.22367], so the competition remains open and interesting."
- Precedent numbers: ecdsa.fail participants halved Toffoli counts with AI coding agents (Long et al. 2609.28882).

## 6. Results, discovered tricks, failure modes

**Not in paper** (no per-benchmark improvement numbers, no trick list, no failure-mode analysis). The only "tricks" documented are those baked into the *reference* implementations (Sec. 2.3, 3.3, 4.3 above), the general approximation licence ("dropping low-weight carry bits, truncating intermediate registers, or bounding iteration counts"), and the simulator's junk-detection behaviour (Sec. 1.2). For actual AI-discovered improvements on these exact benchmarks, read **Gu, Kemeny, Yelin, Lukin et al., arXiv:2610.22367 "Discovering state-of-the-art quantum circuits with large language models"** (RS decoding for DQI, Coulomb-potential evaluation, QROM for electronic structure) and Long et al. arXiv:2609.28882 (record-and-replay arithmetic from ecdsa.fail).

## 7. Outlook / open problems stated by the authors (Sec. IV, p. 22)

1. Compile to a target QEC architecture: logical qubit/Toffoli counts are coarse; future benchmarks keep kickmix for correctness but score with a QEC cost model (magic-state distillation, routing, reaction time), letting agents co-optimise arithmetic, layout and schedule.
2. Machine-checkable proofs (Lean) so that non-kickmix subroutines (state preparation, QSP, fermionic rotations) and parameterised constructions for all n can be certified.

## 8. Related work and references useful for the benchmarks

| Key | Reference | Why useful |
|---|---|---|
| babbush2026securing... | Babbush, Zalcman, Gidney, Broughton et al., "Securing Elliptic Curve Cryptocurrencies against Quantum Vulnerabilities", **arXiv:2603.28846** | Origin of kickmix, Fiat-Shamir verification, measurement-based uncomputation of products, approximation-by-failure-rate; tricks for finite-field and integer arithmetic |
| long2026recordreplay | Long, Pender, Huang, Santos et al., "Efficient Record-and-Replay Arithmetic for Quantum Elliptic-Curve Point Addition", **arXiv:2609.28882** | ecdsa.fail winners' techniques (halved Toffolis); record-and-replay uncomputation pattern directly applicable to Benchmarks I/II |
| gu2026discovering | Gu, Kemeny, Yelin, Lukin et al., "Discovering state-of-the-art quantum circuits with large language models", **arXiv:2610.22367** | Parallel LLM study on the same three benchmark problems; "strong results" per the authors |
| khattar2025optimizeddqi | Khattar, Shutty, Gidney, Zalcman et al., "Verifiable Quantum Advantage via Optimized DQI Circuits", **arXiv:2510.10967** | Baseline decoder: synchronised EEA, 51-Toffoli F_{2^12} multiplier, measurement-based erasure of field products, 5.2e6 decoder count |
| jordan2025dqi | Jordan, Shutty, Wootters et al., "Optimization by decoded quantum interferometry", **arXiv:2408.08292**, Nature 2025 | DQI, OPI, Lemma 9.2 weight distribution |
| proos2004 | Proos & Zalka, "Shor's discrete logarithm quantum algorithm for elliptic curves" (quant-ph/0301141) | Synchronised EEA register sharing |
| rubin2024quantum | Rubin, Berry, Kononov, Malone, Khattar et al., "Quantum computation of stopping power for inertial fusion target design", PNAS 121 e2317772121 (2024) (arXiv:2308.12352) | Origin of the 24-bit requirement, the cubic coefficients, n_p = 6 estimates |
| Haner2018 | Haener, Roetteler, Svore, "Optimizing Quantum Circuits for Arithmetic", **arXiv:1805.12445** | Fixed-point polynomial/NR arithmetic, truncated multipliers, piecewise polynomial evaluation |
| Su2021 | Su, Berry, Wiebe, Rubin, Babbush, "Fault-tolerant quantum simulations of chemistry in first quantization", PRX Quantum 2021 (arXiv:2105.12767) | Lemma 8 (sum-of-squares cost), first-quantised arithmetic |
| cody2012faster | Jones, Whitfield, McMahon et al., NJP 2012 | Phase-by-potential algorithm (Eqs. 15-17) |
| GidneyAdder | Gidney, "Halving the cost of quantum addition", Quantum 2018 (arXiv:1709.06648) | Temporary AND + measurement uncompute, n-1 Toffoli adders |
| Gidney2019b | Gidney & Ekeraa, "How to factor 2048 bit RSA integers in 8 hours...", Quantum 2021 (arXiv:1905.09749) | Approximate arithmetic by dropping carries, windowed arithmetic |
| gidney2025factor2048 | Gidney, "How to factor 2048 bit RSA integers with less than a million noisy qubits", **arXiv:2505.15917** | Approximate residue arithmetic, yoked surface codes, qubit-lean compilation |
| kliuchnikov2023shorter | Kliuchnikov, Lauter, Minko, Paetznick, Petit, Quantum 2023, **arXiv:2203.10064** | Rotation synthesis cost 0.56 log2(1/eps) + 5.3 used in Benchmark I scoring |
| BabbushSpectra | Babbush, Gidney, Berry, Wiebe et al., PRX 2018 (arXiv:1805.03662) | Unary-iteration QROM used in Benchmark III reference |
| Lee2020 | Lee, Berry, Gidney, Huggins et al., PRX Quantum 2021 (arXiv:2011.03494) | THC block encodings, FeMoCo resource estimates |
| pb2g-j9cw | Low, King, Berry, Han et al., "Fast Quantum Simulation of Electronic Structure by Spectrum Amplification", PRX 2025 (arXiv:2502.15882) | DFTHC-SOS construction; **Table 3 Inner/Outer Prep rows = heuristic costs in Benchmark III** |
| harrigan2024qualtran | Harrigan, Khattar et al., **arXiv:2409.04643** | Qualtran (hosts kickmix) |
| gidney2021stim | Gidney, Stim, Quantum 2021 (arXiv:2103.02202) | Simulator design inspiration |
| novikov2025alphaevolve | Novikov et al., AlphaEvolve, **arXiv:2506.13131** | Agentic search loop reference |
| kissinger2020reducing, xu2022quartz, ruiz2025alphatensor | ZX T-count reduction; Quartz superoptimiser; AlphaTensor-Quantum (Nat. Mach. Intell. 2025) | Cited as local-only optimisers |
| janzing2005nonidentity | Janzing, Wocjan, Beth, IJQI 2005 | QMA-completeness of non-identity check |
| fiat1986prove | Fiat & Shamir, CRYPTO 86 | Fiat-Shamir heuristic |
| zhou2025neutralatom, cain2026shor | arXiv:2505.15907; arXiv:2603.28627 | QEC-architecture cost models (outlook) |
| guruswami2000concatenated, naor1999oblivious, bleichenbacher2000noisy | List recovery; noisy polynomial interpolation | OPI context |
| quake3_invsqrt | id Software q_math.c | Fast inverse sqrt |
| deMoura2015 | Lean theorem prover | Outlook |
| babbush2026kitp | Babbush, KITP recorded talk 2026 "Accelerating the field of quantum algorithms with AI" | May contain hints about internal runs (not in paper) |

Note: arXiv IDs not present in the .bib (rubin2024quantum, Su2021, GidneyAdder, Gidney2019b, BabbushSpectra, Lee2020, pb2g-j9cw, gidney2021stim, proos2004) are supplied from memory and should be double-checked before citing.

---

## 9. Implications for our strategy

General, from the scoring rules:

- **Benchmark I rewards Q x C equally**, Benchmark II rewards **qubits twice as much as Toffolis** (Q^2 T), Benchmark III multiplies lambda_eff x T_tot x Q_tot where Q_tot has a large fixed part (state-prep registers) so Toffolis in the angle oracles matter most.
- Benchmark I is exhaustive with k = 0: no approximation that fails on *any* of 3.1M inputs x 64 shots is allowed; but the tolerance is per-x and relative, so approximations that stay within 2^-24 everywhere are fine. Benchmark II allows ~10 failures in 102,400 for ~3% score cost (table in Sec. 3.4). Benchmark III is exhaustive over addresses with 64 shots and no Z_POW.
- Use kickmix flame charts to attribute cost; keep a local verifier identical to the contract (salted seed irrelevant locally).

### 9.1 Benchmark I (1/sqrt(x)) - prioritised ideas

1. **Direct piecewise polynomial on x_norm, no Newton step** (the authors' own "completely different route"). Rough estimate: a minimax cubic reaches 2^-25 on intervals of width ~0.06, i.e. 16 intervals on [1,2) reused for [2,4) by the 1/sqrt(2) rescaling -> ~32 QROM entries (~31 Toffolis by unary iteration, CNOT fan-out of 4 x ~28-bit coefficients) + 3 Horner multiplies at ~26-28 bits (~400-500 Toffolis each) -> ~1.5k forward vs 3.9k now; and drops the y_0^2, z, p registers (~90 qubits). Degree 4 (7 intervals x 2, 4 multiplies) and degree 2 (~700 intervals, 2 multiplies) are alternatives to scan; pick by Q x C.
2. **Right-size every bit width using the 2^-24 budget**: the baseline has 1 bit of slack (2^-25.07 worst case). Run an exact error model over all 3.1M inputs (cheap classically) and shave bits from Dx, coefficients, intermediates until the worst-case error is just under tol(x) minus a small rotation margin. Each dropped bit saves ~30-60 Toffolis per multiplier in both directions.
3. **Taper widths per Horner step**: the c3 Dx product tolerates far more error than c1 Dx (errors scale by Dx^2, Dx^3); use narrower multipliers for the inner steps.
4. **Exploit the relative tolerance by output-width tapering**: for small s (large x) the low bits of y_1 are below tol(x); for large s the high bits are zero. Consider phasing from p with s folded into the angle set differently, or verify the 40-bit y_1 is not wider than needed (tol(x_max) = 2^-34.8 turns suggests ~36 fractional bits suffice at the top end).
5. **Cheaper denormalisation**: thermometer-code s -> binary is F_2-linear (CNOTs only), then a 4-stage barrel shifter (shifts 1,2,4,8) costs ~4 x 35 = 140 CSWAPs instead of 300, both directions. Or fold 2^s into the Z_POW angles via address-dependent coefficient tables if a direct-polynomial design makes s part of the QROM address.
6. **Reduce the rotation bill (~253 Tof-eq)**: the per-rotation synthesis price depends on min_x(tol - |err|)/n_rot; leaving a slightly larger arithmetic margin at the worst x (x = 2,588,411 in the baseline) is cheap and lowers all 37 rotations' cost; also fewer output bits -> fewer rotations.
7. **Qubit reuse / eager uncompute**: coefficient registers c1..c3 (51 qubits) stay live until the reverse pass; uncomputing them right after use (re-doing a cheap truncated multiply + measurement-based QROM uncompute) trades ~+10% Toffolis for ~-20% qubits (net ~8% on Q x C). The direct-polynomial design makes this natural.
8. **Measurement-based uncomputation of the whole second half**: the reverse pass costs 3,861 Toffolis. Record-and-replay / "uncompute by HMR + phase fixup" (Long et al., ECC paper) can turn parts of the uncompute into parity computations; worth testing on the multiply outputs (parity of selected product bits may be cheaper than the full product when few record bits are 1 - on average half).
9. **Cheaper multipliers**: Karatsuba / Toom for 28-bit truncated multiplies, Gidney-style adders with measurement-based uncompute of carries, and sharing partial-product scratch; also compute y_0^2 (442) via the identity y_0^2 = (c0 - T(c1 Dx))^2 expansions only if cheaper (probably not).
10. **Normalisation alternatives**: the 230 Toffoli normalise/denormalise could shrink by indexing the QROM directly with (s, top bits) and avoiding the physical shift of x (keep x in place, read Dx bits through a multiplexer controlled by unary s); evaluate against the CSWAP cost.
11. **Remember k = 0 is strict**: any approximation must be validated on all 3,133,452 inputs with the exact isqrt check, and HMR/R on dirty qubits fails with probability 1/2 per shot, so every scratch qubit must be provably clean.

### 9.2 Benchmark II (RS decoder) - prioritised ideas

1. **Kill the per-position inversion** (1.44M Toffolis = 25%). Forney division is only needed at the <= 35 error positions, but kickmix cost is paid uniformly; options: (a) compute only a cheap zero-flag per position (OR of 12 bits ~ 11 Toffolis -> ~45k total) and move the division to a compact per-error structure; (b) rewrite the needed phase (-1)^{c_i . bin(e_i)} = (-1)^{Tr(lambda_{c_i} e_i)} (every F_2-linear functional is a trace) and search for a formulation of Tr(lambda Omega_i / sigma'_i) that avoids a full inversion; (c) batch inversions with Montgomery's trick across positions (one inversion per block of positions plus 3 multiplies each).
2. **Tower-field representation** of F_{2^12} (e.g. F_{(2^6)^2} or F_{((2^2)^2)^3}): basis change is F_2-linear (free CNOTs on the syndrome registers), multiplication via Karatsuba over the tower (~27-40 Toffolis vs 63; the paper itself cites a 51-Toffoli hand-tuned multiplier), inversion via the tower norm trick (one F_{2^6} inversion + a few F_{2^6} multiplies, far below 315). This hits every EEA step and every Forney evaluation.
3. **Qubit diet (Q counts squared)**: 840 syndrome qubits are fixed; the 1,053 workspace qubits are the lever. Replace the two full (n+3) x b polynomial arrays (876 qubits) with an in-place / Berlekamp-Massey style key-equation solver that keeps the syndrome read-only and stores only sigma and B (2(l+1) b = 864 at most, likely less with register sharing), and shrink the 48-qubit inversion scaffold with the tower-field inverter. A 20% qubit cut is worth a 36% Toffoli cut.
4. **Accept a small failure rate**: by the table in Sec. 3.4, up to ~10 failures (eps ~ 1e-4) costs ~3%. Candidates: bounded-iteration EEA that fails on rare degree patterns, truncated carry/overflow handling in degree pointers, skipping defensive checks for the zero syndrome. Do not drop high-weight (w = 35) handling: that is 2.8% of inputs and would cost ~4x.
5. **Exploit the weight distribution**: E[wt] = 31, concentrated near 35; design the EEA step count / pointer ranges for weights 25-35 and fail (rarely) outside; verify the tail mass against the eigenvector distribution before committing.
6. **Direct-parity computation** (authors' hint): the contract only needs the parity c . bin(e(s)); think about computing the parity sum over error positions as a running phase without ever materialising e_i in a register (e.g. phase kickback via CZ gates between c-selected bits as each e_i is produced and erased by measurement, as in the MBUC construction itself).
7. **Cheaper Chien search**: sigma(alpha_i^{-1}) updates are CNOT-only (free); make sure the zero test, the Omega/sigma' evaluation and the symbol-bit Z gates are the only Toffoli consumers per position; consider an additive-FFT evaluation of sigma at all 4095 points (linear -> CNOT) if the register budget allows.
8. **EEA control overhead**: 222 synchronised steps with unary iteration over five pointers; replace pointer-driven addressing with a fixed schedule where the degree sequence is data-independent (standard trick: run exactly 2l "systolic" steps with swap-controlled updates, as in Berlekamp-Massey hardware), eliminating unary iteration Toffolis.
9. **Measurement-based erasure of every bilinear product** (already used in baseline for products whose factors stay in memory): extend to quotient x divisor products in the EEA by keeping factors alive slightly longer.
10. **Reuse the 51-Toffoli multiplier** from Khattar et al. immediately as a zero-risk 19% cut on multiplication cost; then go further with tower fields.
11. **Local verifier fidelity**: generate test syndromes exactly per Sec. 3.4 (tridiagonal eigenvector weights, uniform positions/symbols, uniform c), use 102,400 shots, and compute R(eps+) with the Clopper-Pearson bound so local scores match Kaggle.

### 9.3 Benchmark III (FeMoCo angle oracles) - prioritised ideas

1. **First establish the lambda_eff headroom**: compute the baseline factorisation's Lambda and E_gap; if they sit at the floors (49.0 Ha, 3.914898 Ha), lambda_eff is already ~19.2 Ha and essentially all score must come from T_tot x Q_tot. If not, re-optimise (R, B, C, u, w, W) to push lambda_eff toward 19.2 Ha while keeping eps_1, eps_2 <= 20 mHa.
2. **Minimise b_rot (angle precision)**: it multiplies both the Givens heuristic (2(N-1)(2 b_rot - 1) Toffolis per block encoding: 2,250 at 8 bits vs 3,450 at 12) and the persistent J b_rot angle registers in Q_tot. Do **quantisation-aware factorisation**: optimise the angles directly in their b_rot-bit grid (or at least re-optimise weights w after quantising vectors) so that the full 20 mHa budget absorbs both factorisation and rounding error.
3. **Minimise the number of addresses N + RB**: with unary-iteration QROM, Toffolis per lookup ~ N + RB - 1 per Angles_k; fewer two-body vectors (smaller R x B, compensated by larger C which is free for the QROM) directly cut T_tot. Explore the (R, B, C) Pareto front under the 20 mHa constraint.
4. **Choose J (batch size) by the real objective**: T_tot ~ 2 K (N + RB - 1) + ... with K = ceil(75/J), while Q_tot grows by J b_rot. Sweep J; the 128-qubit cap on each Angles_k (selection ~ 10-12 qubits + J b_rot words + workspace) bounds J b_rot at roughly 100.
5. **Use the shared workspace for free**: Q_tot adds only the *largest* temporary workspace among Outer, Inner and Angles_k. Any Angles_k workspace up to max(C_out, C_in workspace) (and within 128 total) is free, so SelectSwap / clean-ancilla QROM variants that trade Toffolis for ancillas can be used up to that size at zero Q_tot cost.
6. **Exploit the XOR-difference interface**: the oracle outputs vartheta^[k] xor vartheta^[k-1]; choose the tree and the angle ordering so consecutive batches share bits (many zero XORs -> fewer CNOT fan-outs; not Toffolis, but shorter circuits) and, more importantly, so that **many angles are exactly 0 or pi** (sparse vectors u) - zero words need no data at all.
7. **Tree design**: the tree T is a free choice; a path tree needs N - 1 nontrivial angles for a dense vector, but a star or balanced tree can realise sparse vectors with few nonzero angles; also sibling-order affects which angles are zero. Pair tree choice with a sparsity-promoting factorisation (e.g. localised orbitals).
8. **QROM compression**: the selection space is N + RB addresses but the one-body block (N addresses) and the two-body block (RB) have different structure; use variable-spaced / multi-level unary iteration, and share the two-body vectors across the C copies (the spec already shares B vectors within each rho group - make sure the address map does not duplicate them).
9. **Data-dependent QROM tricks**: since the verifier only checks the words, you can permute/relabel addresses arbitrarily (the address map is yours), and sort addresses so lookups are prefix-structured. Phase-based tricks are *not* available (no Z_POW allowed), but measurement-based uncompute of the unary-iteration ancillas (HMR + classically controlled CZ) is.
10. **Forward/reverse symmetry**: the reverse traversal ends with Angles_0 clearing z; design Angles_k so forward and reverse share the same circuit (self-inverse by construction, as required) and so the reverse pass can use measurement-based uncomputation of the unary iteration tree.
11. **Validate the black-box costs early**: implement C_out, C_in from Table 3 of Low et al. exactly as the Kaggle scorer does; otherwise Pareto decisions on (R,B,C,J,b_rot) will be wrong.
12. **Read Gu et al. 2610.22367** for the QROM-for-electronic-structure results before spending effort on QROM micro-optimisation.

### 9.4 Cross-cutting

- Build a shared library: tower-field F_{2^12} arithmetic (II), truncated/tapered multipliers with measurement-based uncompute (I), unary-iteration QROM with free uncompute (III), and a scorer per benchmark that reproduces Sec. 2.2 / 3.4 / 4.6 exactly.
- The simulator checks dirty resets with probability 1/2 per shot; always run >= 64 shots per input locally to catch junk.
- Watch the v1 -> v2 drift (Benchmark II Toffoli count, Benchmark III scoring) - the Kaggle rules may drift again; keep the contract parameters in one config file.
