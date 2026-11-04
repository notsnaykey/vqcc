# Literature review: Verifiable Quantum Circuit Compilation (kickmix benchmarks)

Annotated bibliography for the Kaggle competition *Google Quantum AI – Verifiable
Quantum Circuit Compilation* (companion paper arXiv:2610.23832). Compiled 2026-11-04.

**How to read the confidence tags.** Every entry ends with a *Confidence* line:

| Tag | Meaning |
|---|---|
| **FULL** | PDF downloaded from arXiv and the relevant sections read in full; numbers quoted directly. |
| **PARTIAL** | PDF downloaded; only the abstract and grep-located passages read. |
| **ABSTRACT** | Only the abstract (arXiv listing / PDF first page) read. |
| **SNIPPET** | Only web-search snippets, blog posts or secondary coverage; treat numbers as provisional. |
| **COMMUNITY** | Public participant GitHub repos / notebooks (unverified third-party claims). |

The companion paper arXiv:2610.23832 is being read in depth by a separate agent; it gets a
short entry here (Section A.1), but its baseline numbers are repeated wherever they are needed
to judge the relevance of another paper.

---

## 0. Benchmark cheat-sheet (numbers from the companion paper, FULL)

| | invsqrt (Benchmark I) | dqi (Benchmark II) | dfthcsos (Benchmark III) |
|---|---|---|---|
| Task | `|x>|0> -> exp(2πiβ/√x)|x>|0>`, x ∈ [1, 3,133,452] (22-bit), β = 1, n_p = 10 | `|s>|0> -> (-1)^{c·bin(e(s))}|s>|0>`: RS syndrome decoding over F_{2^12}, (m,n,b,r) = (4095,70,12,2016), ℓ = 35 | K angle oracles `Angle_k` (QROM of Givens angles) + factorization `.npz` for FeMoCo (N = 76, η = 113) |
| Cost | S = Q × C, C = Toffoli + T/4; fine Z_POW priced 0.56·log2(1/ε)+5.3 T | S = R(ε⁺)·Q²·T, R(ε) = ln 2 / (−ln(½ + 2√ε)); no finite score if ε⁺ ≥ 1/16 | S = λ_eff·T_tot·Q_tot, λ_eff = √(E_gap(2Λ − E_gap)) |
| Verification | exhaustive: every x, 64 shots each = 200,540,928 shots, zero failures, tol(x) = 2⁻²⁴·β/√x turns | 102,400 shots from the DQI weight distribution; Clopper–Pearson ε⁺ at 1−2⁻¹²⁸ (ε⁺ ≈ 88.72/N → 8.7e-4 with 0 failures → R ≈ 1.19) | all N+RB addresses × 64 shots, forward + reverse; ε₁, ε₂ ≤ 20 mHa; Λ > 49 Ha; E_gap > 3.914898 Ha; each Angle_k ≤ 128 qubits; no Z_POW |
| Baseline | Q = 260, 7,735 Toffoli, 1 T, 37 Z_POW → C = 7,988, S ≈ 2.08e6 (2,076,774.23); worst rel. err 2.84e-8 = 2⁻²⁵·⁰⁷ | Q = 1,893, T = 5,725,461 → S ≈ 2.44e13 | (community) R/B/C = 65/60/60, b_rot = 12, J = 8 (K = 10); Q_tot = 730, T_tot = 93,237, Λ ≈ 308, E_gap ≈ 3.9655 → S ≈ 3.3556e9 |
| Public best (COMMUNITY, early Nov 2026) | Q = 62, cost ≈ 100,700 (≈ 20.6×) | Q = 889–897, ≈ 4.4e5 Toffoli, cost ≈ 4.0e11 (≈ 60×) | cost ≈ 3.38e8 (≈ 9.9×); LB top ≈ 26.1–26.8 geomean |

Scaling intuition: invsqrt is linear in Q and in C; dqi is *quadratic* in Q (1 % fewer qubits ≈ 2 % fewer
Toffolis); dfthcsos is linear in each of λ_eff, T_tot, Q_tot and the angle circuits are ~85 % of T_tot.

---

## A. Verification-driven / agentic circuit compilation

### A.1 Leveraging verifiable structure in quantum circuits to find more efficient compilations with agentic AI
*T. Khattar, N. C. Rubin, C. Gidney, M. Broughton, G. H. Low, R. Babbush (Google Quantum AI), Oct 2026, arXiv:2610.23832 (v2 21 Oct 2026).*

**Method (short entry; another agent is doing the deep read).** Defines *kickmix* circuits (reversible
classical gates X/CX/CCX/SWAP/CSWAP, diagonal phases Z/CZ/CCZ/Z_POW, and HMR = Hadamard–measure–reset
for measurement-based uncomputation). Such circuits map a basis input to a single basis output with a
tracked phase, so a SIMD bit-sliced simulator (64–512 shots per CPU instruction, >1e8 gates/core) can
fuzz-test them; failure probability ε bounds trace distance by 2√ε and phase error τ adds ≤ 2πτ. Shots are
seeded by Fiat–Shamir (SHA-256 of the circuit + salt). The paper sets up the three benchmarks, gives
reference circuits in Qualtran/kickmix, and reports that internal Gemini-driven agent loops beat all three
baselines (hashes of the improved circuits are published: I: 4b98f38a…, II: 0701f553…, III: 9b8d070f…).
What worked for the agents: modular decomposition with local checks, measurement-based uncomputation
(~50 % fewer Toffolis on cleanups), bit-precision/carry pruning, register reuse. What did not: black-box
unitary optimisers (>40 qubits), seed grinding (salted), over-approximation (R blows up / rejection).

**Key numbers.** See the cheat-sheet (Section 0). Additional baseline anatomy (Appendix B):
invsqrt normalisation costs n_p(n_p+2) = 120 Toffoli-eq forward (n_p AND flags + n_p(n_p+1) = 110 CSWAPs),
in-place Horner 1,071 Toffolis, squaring 442, mantissa multiply 1,043, negation 28, final NR multiply 867,
denormalise 30·n_p = 300 CSWAPs; widths: 14-bit Δx, 17-bit coefficients, 28-bit y₀², 30-bit z and p,
40-bit y₁; one Z_POW per bit of y₁. dqi baseline: 222 synchronised EEA cycles, 63-Toffoli Karatsuba
F_{2^12} multiplier (vs hand-tuned 51 in arXiv:2510.10967), Itoh–Tsujii inversion 315 Toffoli + 48 scaffold
qubits, Chien/Forney 351 Toffolis per position × 4095 positions, polynomials in 2(n+3) = 146 registers of
12 qubits. dfthcsos: Givens rotation t = b_t-bit controlled adder assumed 2b_t − 1 Toffolis; Outer/Inner
state preparation priced by heuristic formulas ("Inner Prep"/"Outer Prep" rows of Table 3 of
arXiv:2502.15882); symmetry shift (S, β₁) fixed to the baseline's; E_upper = −22140.27335 Ha.

**Relevance.** All three. Confidence: **FULL** (benchmark sections III A–C and Appendices A, B read).

### A.2 Discovering state-of-the-art quantum circuits with large language models  *(the "simultaneous independent work" named by the Google announcement)*
*A. Gu, A. H. Kemeny, S. F. Yelin, M. D. Lukin (Harvard / Anthropic / QuEra), 15 Oct 2026, arXiv:2610.22367. Code + exact evaluator: github.com/andigu/uncompute.*
Identification: the companion paper's Acknowledgments say "While we were finalizing this manuscript … Ref. [32]
appeared on the arXiv. That work also builds on the kickmix model of Ref. [13] to optimize fault-tolerant quantum
subroutines with AI agents, and studies many of the same benchmark problems, including Reed-Solomon syndrome decoding
for DQI, Coulomb-potential evaluation, and quantum lookup tables for electronic structure" — Ref. [32] is exactly
arXiv:2610.22367 (confirmed from the reference list, FULL). Ref. [33] is R. Babbush's recorded KITP talk
"Accelerating the field of quantum algorithms with AI" (KITP conference *Artificial Intelligence at the Quantum
Frontier*, 2026), given two weeks before. Press coverage (QuEra blog, Quantum Computing Report, Quantum Zeitgeist)
attributes the LLM to Anthropic's Claude Mythos 5 (SNIPPET).

**Method.** An LLM (Claude Mythos 5 per press coverage) writes Python circuit-generator programs inside an
evolutionary loop; a frozen kickmix-style evaluator (exact bit-sliced simulation, hash-seeded tests, optional
*failure budget*) rejects incorrect circuits and scores survivors by TQ-cost = Toffoli × peak qubits. An
"ideation" stage first proposes several algorithm families (e.g. for RS decoding: extended Euclid,
Berlekamp–Massey, Peterson–Gorenstein–Zierler), each optimised in parallel with periodic cross-pollination.
Three recurring design principles: (1) **conditional routing** – replace branch-specific controlled
arithmetic by cheap CSWAP routing around one shared uncontrolled kernel (e.g. two controlled
multiply-adds → one MADD: 3n²+17n−2 → (3n²+17n−2)/2 Toffolis); (2) **decode branch decisions from state**
during uncomputation instead of storing a history stack (e.g. g_{j+1} = g_j + b_j 2^j reveals b_j);
(3) **spend the failure budget** on rare costly inputs (drop stack entries / lanes that only atypical inputs
need). MBU (Gidney) of temporary ANDs and of whole QROM lookups is used throughout; coefficient tables are
fitted *to the exact quantised integer computation* rather than rounded from a real-valued fit.

**Key numbers (Table I).** RS DQI decoder (baseline = Khattar et al. 2510.10967 released code):
(5.1e6 T, 1,938 Q) → (4.4e5 T, 1,837 Q), 12× TQ; Hermitian DQI decoder (1.0e8, 1.9e5) → (9.3e5, 2,395);
HHL arcsin angle (1.6e4, 300) → (1,348, 115), 32×; **Coulomb potential 1/√(Σ(Δr)²) (6,355, 252) →
(1,140, 142), 9.9×**; fixed-point Gaussian (2.4e4, 362) → (1,583, 139), 39×; Fe₂S₂ sparse-qubitization
Select/QROM (5.5e4, 139) → (1.5e4, 126), 4.1×; lattice-gauge plaquette (1.3e6, 1,927) → (1.7e5, 1,859), 7.7×;
prime-field modular inversion/point add (4.0e6, 935).

*RS decoder details (SI I.1, highly relevant to dqi).* Replaces the 222-cycle synchronised EEA (≈1.9 M
Toffolis for the locator solve, 3.8 M with reversal) by a **70-round Berlekamp–Massey** recurrence
(≈140 k Toffolis forward). Tricks: rescaled BM update so both branches (retain/replace) share one MADD path
under a CSWAP-routed flag; invariant σ₀δ = 1 so the discrepancy δ is never stored (read as σ₀⁻¹); adaptive
per-round coefficient cutoffs chosen from classical simulation of the DQI input distribution (locator degree
L ≈ r/2 typically); history stack reduced from 35 entries (665 qubits) to **one entry (19 qubits)** because a
second retain-round discrepancy is needed with probability only 1.0e-4; combined failure modes 1.4e-4.
Evaluator ω built *in place* over the first 35 syndrome words (ω_i = S_{i+1} + Σ σ_j S_{i−j+1}, reversible),
the last 35 words become zero workspace. **Phase-only error recovery**: DQI needs only the parity ⟨c,e⟩₂,
expressed as a field trace Tr(µ_j e_j); the linear-in-syndrome part is applied with Clifford Z gates, cancelling
the mask at 71 positions; the remaining 4,024 positions use a precomputed reciprocal polynomial Ψ ≡ 1/σ′ (mod σ)
so no division happens in the scan: each position costs a 12-bit zero test (11 Toffolis) + 12 bilinear
products (12 Toffolis) = 23 Toffolis → 93 k Toffolis for the scan vs 1.3 M in the baseline. Ψ is found by an
EEA on half-degree operands (char-2 trick σ = E² + zO², σ′ = O²; EEA on (E, O) of degree ≤ 17 → 44 k Toffolis
each direction), stored in the zeroed syndrome words. Result: **440,000 Toffolis, 1,837 qubits, TQ = 8.1e8**;
7 wrong signs in 100,000 tests. Under the competition's DQI metric this circuit is *not* obviously better than the
community's ≈890-qubit decoders because Q is squared (see Section F).

*Function-evaluation details (SI III, relevant to invsqrt).* Baselines are tuned Häner–Roetteler–Svore
piecewise polynomials. Discovered circuits: choose **power-of-two-aligned ("dyadic") intervals selected
directly by input bits** (no comparators), use *finer tables with lower-degree polynomials* (Coulomb: 16
quadratics → **128 lines**; HHL: 35 cubics → 345 dyadic quadratics; Gaussian: 32 cubics → 1,024 intervals
with 455 quadratics / 59 constants / 510 zeros pruned via Sanders et al. variable-spaced QROM, 1,022 → 495
Toffolis), map every interval onto one **shared local coordinate by cyclic bit shifts** (no subtraction, one
15×16-bit kernel instead of 44×44), **accumulate directly into the destination** (t ← g₁ − g₂d stored over
g₁; k ← k + g₀ − d·t, no product/function registers), truncate partial-product columns inside a single
end-to-end error budget, and clear loaded coefficients with **MBU of the lookup (17 Toffolis instead of 126
for the 128-entry table)**, then reuse the freed coefficient qubits as carry ancillas. Coulomb circuit:
d² = 2^e u, 1 ≤ u < 2, 1/√(d²) = 2^{−e/2}/√u; parity of e + six mantissa bits select the line; next six bits
are the local coordinate; the line is at most six controlled additions; error 1.91e-6 vs 2e-6 budget.

**Relevance.** dqi (directly: a 12× cheaper RS decoder with full design rationale and released code);
invsqrt (the Coulomb/HHL/Gaussian circuits are the closest published analogue of the 1/√x task and explain
how the community reached ~60 qubits); dfthcsos (Fe₂S₂ Select/QROM section: frame-block Select, merged alias
words, structured QROM tables). Also the best description of an agentic search loop that works.
Confidence: **FULL** (main text, Methods, SI I.1 and SI III read; SI IV skimmed).

### A.3 Securing Elliptic Curve Cryptocurrencies against Quantum Vulnerabilities: Resource Estimates and Mitigations  *(primary source: where kickmix circuits were introduced)*
*R. Babbush, A. Zalcman, C. Gidney, M. Broughton, T. Khattar, H. Neven, T. Bergamaschi, J. Drake, D. Boneh, arXiv:2603.28846 (30 Mar 2026, v2 15 Apr 2026); published as a Perspective in **PRX Quantum 7, 031001 (21 Aug 2026), DOI 10.1103/j3xf-bw18**; also IACR ePrint 2026/625.*
Named by the Google announcement blog as the paper that introduced kickmix circuits and the salted fuzz-testing
verification style (the companion paper cites it as Ref. [13]: "used this method in March 2026 to estimate the cost
of breaking 256-bit elliptic curve cryptography").

**Method.** Resource estimate for Shor's ECDLP on secp256k1: ≤ 1,200 logical qubits & ≤ 90 M Toffolis, or
≤ 1,450 qubits & ≤ 70 M Toffolis (vs Litinski's 50 M Toffolis / larger qubit count). The point-addition circuit
is not disclosed; instead a zero-knowledge proof (SP1 zkVM) attests the counts. Appendix sections "Measurement
Based Uncomputation and Kickmix Circuits" and "Verifiable Fuzz Testing via the Fiat–Shamir Heuristic" are the
*origin of the kickmix model and the salted fuzz-testing protocol* reused by the competition.

**Relevance.** Background for the verifier; cryptographic field arithmetic ideas (windowed/record-and-replay
GCD) overlap with dqi. Confidence: **PARTIAL** (abstract + grep; kickmix appendix not read).

### A.4 ECDSA.Fail: Open Autoresearch for Optimizing Elliptic-Curve Point Addition in Shor's Algorithm
*J. Long et al. (Theta Labs, Starknet, Eigen Labs, Ethereum Foundation, …), Sep 2026, arXiv:2609.09582.* And
companion **Efficient Record-and-Replay Arithmetic for Quantum Elliptic-Curve Point Addition**, arXiv:2609.28882.

**Method.** >100 human+AI-agent participants optimised a reversible secp256k1 point-addition circuit against a
public evaluator with score S = Q × T (peak qubits × mean executed Toffolis). Score fell from 10.75 B
(Q = 2,715, T = 3,960,753) to 1.496 B (−86.1 %); best low-width circuit 813 qubits. Companion paper: compressed
*record-and-replay* GCD (Jump-2 base-5 encoding of binary-GCD decisions: 609 transcript qubits; "ping-pong"
comparison-free schedule; fused doubling+signed-addition replay cell 393 vs 446 Toffolis), operating point
1,151 qubits / 1,299,453 mean Toffolis. The companion paper cited by the competition says this community
halved Toffoli counts using AI coding agents.

**Relevance.** Methodological precedent for the competition (same Q×T objective, same agent loop); the
record-and-replay/transcript-compression ideas are exactly the "history" problem in dqi's EEA/BM decoders.
Confidence: **PARTIAL** (abstracts + result lists).

### A.5 Optimized Point Addition Circuits for Elliptic Curve Discrete Logarithms
*A. Schrottenloher (Inria), Jun 2026, arXiv:2606.02235.* Reconstructs a logical architecture matching
Babbush et al. 2603.28846 (≈1.5 % more qubits, slightly fewer Toffolis; qubits ≈ 4.355n + O(√n)); uses
window size w = 16 (3·2^w extra Toffolis). **Relevance:** low (prime-field arithmetic), but a worked example of
windowed modular arithmetic at competition-relevant scale. Confidence: **ABSTRACT**.

### A.6 Automating quantum circuit optimization with AI agents
*M. Crichigno, S. Flammia, 22 Oct 2026, arXiv:2610.31352.* Autoresearch loop with a *frozen, exact verifier*
co-built by agent + researcher and checked against solved cases; Claude-based coding agents with shell/file
access; tasks: fermion-to-qubit encodings, Hamiltonian layout, unitary synthesis; up to 73 % cost reduction at the
largest sizes; every submission carries the agent's notes. **Relevance:** process design for our own search loop
(keep the verifier frozen; log rationale). Confidence: **SNIPPET**.

### A.7 AlphaEvolve: a coding agent for scientific and algorithmic discovery
*A. Novikov et al. (Google DeepMind), Jun 2025, arXiv:2506.13131.* Evolutionary coding agent: program database →
prompt sampler (parent + inspirations + evaluator feedback) → LLM ensemble proposes diffs → evaluator pool scores →
database update (`parent, inspirations = database.sample(); diff = llm.generate(prompt); …`). Successor to
FunSearch (2023), with richer context and multi-objective evaluation. **Relevance:** template for an invsqrt/dqi
generator-evolution loop; the competition explicitly rewards "search and AI methods". Confidence: **PARTIAL**.

### A.8 Gemini 4 Argon quantum-research results (Google blog post, no paper)
*Google, "Gemini 4 Argon: Built to solve your hardest problems", blog.google (launch ≈ 30 Sep – 13 Oct 2026); echoed in
the competition announcement ("Argon is already helping accelerate progress across both quantum error correction and
algorithm design").* Claims: an Argon-written implementation of an **arcsin subroutine used in quantum simulation
algorithms, formally verified in Lean, cuts spacetime cost by >100× versus a published quantum CORDIC baseline**
(described as a step toward a standard library of optimised quantum circuits); Argon also rewrote an internal
AlphaQubit decoder into one hardware kernel (~2× inference throughput). No circuit, arXiv id or technical write-up was
found; a secondary report of "40 % over a published baseline in minutes" is unreliable. The companion paper's hashed
internal circuits for the three benchmarks are the related Google-internal evidence. **Relevance:** invsqrt — arcsin is
the same "fixed-point elementary function via lookup + polynomial" family as 1/√x (compare Gu et al.'s HHL arcsin task,
16 k → 1,348 Toffolis), and Lean-verified circuits are the companion paper's stated future direction.
Confidence: **SNIPPET** (company blog + press).

---

## B. invsqrt — fusion / stopping power, first-quantised grids, and fixed-point arithmetic

### B.1 Quantum computation of stopping power for inertial fusion target design
*N. C. Rubin, D. W. Berry, A. Kononov, F. D. Malone, T. Khattar, A. White, J. Lee, H. Neven, R. Babbush, A. D. Baczewski, Aug 2023, arXiv:2308.12352 (PNAS 2024).*

**Method.** First-quantised grid simulation of electrons + projectile (non-Born–Oppenheimer, finite T) to
estimate stopping power; compares QSP/qubitised time evolution with a high-order Trotter grid approach. For
the Trotter route the dominant cost is the pairwise Coulomb phase e^{−iδ/|r_i − r_j|} for η(η−1)/2 pairs, i.e.
computing 1/√w with w = Σ(Δx)² to 24-bit *relative* precision. The paper's design is the competition baseline:
(i) strip pairs of leading zeros (n(n+1) Toffolis; "12+10+8+6+4+2 = 42" at n = 6), (ii) variable-spacing QROM
(Sanders et al.) outputs cubic interpolation coefficients for [1, 3/2] and [3/2, 2] (a₀ = 0.99994132…,
a₁ = 0.49609892…, a₂ = 0.33261113…, a₃ = 0.14876762…; b₀ = 0.81648515…, b₁ = 0.27136515…, b₂ = 0.12756148…,
b₃ = 0.04475303…; scaled per octave by 2^{−m/2}, 2^{−3m/2}, 2^{−5m/2}, 2^{−7m/2}), evaluated by Horner (three
multiplications), (iii) one Newton–Raphson step y ← ½y(3 + δ − y²x) with tuned δ = 5.164e-9 / 3.628e-10 giving
relative error ≤ 2.58e-9 / 1.81e-10 on the two ranges (they state 15-bit interpolation precision is enough for
~1e-8 after Newton), (iv) optional b/√x via scaled constants and 3 → 2 + b². Toffoli estimate per pair
≈ 2137 + 4n² + 19n (Eq. 50; 2,395 at n = 6), dominated by three 15-bit multiplies (3×15² = 675) and two 24-bit
multiplies (2×24²). They note Kivlichan et al.'s pure-Newton approach needs a good seed (32-bit accuracy only
over a <5× range). Overall: stopping power needs ~1e15–1e17 Toffolis, ~1e3 logical qubits.

**Relevance.** invsqrt (origin of the baseline and of the 24-bit requirement). Note the paper itself says only
one Newton step after a cubic seed is needed, and that bit widths can be truncated aggressively — the community
has since shown that a *pure table + linear interpolation* with no Newton step suffices at ~60 qubits.
Confidence: **FULL** for the arithmetic section (lines ~815–940); rest PARTIAL.

### B.2 Fault-tolerant quantum simulations of chemistry in first quantization
*Y. Su, D. W. Berry, N. Wiebe, N. Rubin, R. Babbush, May 2021, arXiv:2105.12767 (PRX Quantum 2021).*

**Method.** Compiles the two first-quantised plane-wave algorithms of Babbush et al. 2019 (qubitisation and
interaction picture) with explicit constant factors; O(η^{8/3}N^{1/3}) Toffoli scaling; heavy use of QROM, unary
iteration, inequality-test state preparation (e.g. "3n + 2b_r − 9" style costs, b_r ≈ 8 bits for amplitude
rotations), and Toffoli-counted arithmetic (bit products as single Toffolis). The Coulomb term is handled in
momentum space (1/|ν|² via inequality tests), so no inverse square root is computed — this is the *alternative*
to the Trotter/grid route that needs 1/√x.

**Relevance.** invsqrt (context; shows why Trotter-on-grid incurs the 1/√x primitive); its QROM/unary-iteration
cost bookkeeping is reused in dfthcsos. Confidence: **PARTIAL**.

### B.3 Low-depth quantum simulation of materials
*R. Babbush, N. Wiebe, J. McClean, J. McClain, H. Neven, G. K.-L. Chan, Jun 2017, arXiv:1706.00023 (PRX 8, 011044, 2018).*
Plane-wave dual basis diagonalises the potential (O(N²) terms), enabling linear-depth Trotter steps and the
grid-based viewpoint later used for stopping power. **Relevance:** invsqrt background only. Confidence: **ABSTRACT**.

### B.4 Bounding the costs of quantum simulation of many-body physics in real space
*I. D. Kivlichan, N. Wiebe, R. Babbush, A. Aspuru-Guzik, Aug 2016, arXiv:1608.05696 (J. Phys. A 50, 305301, 2017).*
Truncated-Taylor-series real-space simulation with Õ(η²) pairwise-interaction evaluations; evaluates the Coulomb
kernel by Newton–Raphson iterations for 1/√x (Rubin et al. report 32-bit accuracy in 5 iterations only when the seed
is within a ~5× range). **Relevance:** invsqrt history (pure-Newton approach, superseded). Confidence: **ABSTRACT**
(the PDF text did not grep cleanly for the Newton passage; the characterisation comes from Rubin et al.).

### B.5 Quantum simulation of exact electron dynamics can be more efficient than classical mean-field methods
*R. Babbush, W. J. Huggins, D. W. Berry, S. F. Ung, A. Zhao, D. R. Reichman, H. Neven, A. D. Baczewski, J. Lee, Jan 2023, arXiv:2301.01203 (Nat. Commun. 2023).*
Tightened bounds for first-quantised grid Trotter dynamics: Õ(N^{1/3}η^{7/3}t + N^{2/3}η^{4/3}t) gates with O(η log N)
qubits; Appendix G gives Toffoli complexities; discusses smoothing the Coulomb cusp. **Relevance:** justifies the
"η² pairwise phasings per Trotter step" framing of invsqrt. Confidence: **ABSTRACT/PARTIAL**.

### B.6 Improved fault-tolerant quantum simulation of condensed-phase correlated electrons via Trotterization
*I. D. Kivlichan, C. Gidney, D. W. Berry, N. Wiebe, J. McClean, W. Sun, Z. Jiang, N. Rubin, A. Fowler, A. Aspuru-Guzik, H. Neven, R. Babbush, Feb 2019, arXiv:1902.10673 (Quantum 4, 296, 2020).*
Low-order Trotter + phase estimation for Hubbard / plane-wave models; **Hamming-weight phasing** (Appendix A) to
apply many equal-angle rotations with few synthesised rotations plus Toffolis; converts Toffoli → 2 T for
accounting. **Relevance:** invsqrt phasing stage (one Z_POW per bit of y₁ is already cheap, but Hamming-weight
phasing is the standard trick if many rotations must share angles). Confidence: **PARTIAL**.

### B.7 Optimizing quantum circuits for arithmetic
*T. Häner, M. Roetteler, K. M. Svore (Microsoft), May 2018, arXiv:1805.12445.*

**Method.** Piecewise-polynomial evaluation in fixed point: label register from M comparators (T_label = 4Mn),
coefficients loaded per interval, Horner with fused multiply-accumulate. Costs (Appendix A/B, Takahashi adders):
T_mul(n,p) = (3/2)n² + 3np + (3/2)n − 3p² + 3p; T_fma = T_mul + n − 1; degree-d polynomial
T_poly = d·T_fma; parallel evaluation of M polynomials adds 2Md(4⌈log₂M⌉ − 8) Toffolis and n + ⌈log₂M⌉ qubits;
total qubits (d+1)n + ⌈log₂M⌉ + 1. Pebbling tables trade registers for recomputation. Inverse square root
(Appendix C): seed x₀ = 2^k(1.5 − a2^{2k}/2) from the leading-one position, Newton x_{n+1} = x_n(1.5 − a x_n²/2),
each iteration = SQR, MUL, SET1.5/SUB, MUL, and uncompute; m iterations need m + 3 n-qubit registers without
pebbling; tuning C(k) ∈ {1.613, 1.5, 1.62} saves an entire Newton iteration. Multiplications use truncation
("pre-truncation": skip partial-product bits below the result LSB) and conditional negation of the multiplicand.

**Relevance.** invsqrt — the generic baseline family and the formulas for pricing any Horner/Newton design;
Gu et al. show that dyadic interval selection + shared coordinate + MBU unlookup beats HRS by 10–39×.
Confidence: **FULL** (appendices A–C read).

### B.8 Quantum algorithms and circuits for scientific computing
*M. K. Bhaskar, S. Hadfield, A. Papageorgiou, I. Petras, Nov 2015, arXiv:1511.08253 (QIC 2016).*
Reversible fixed-precision modules: INV (reciprocal by Newton, error ≤ (2 + log₂ b)/2^b), SQRT (two Newton stages,
reciprocal then y ↦ ½y(3 − wy²)), LN, fractional powers; each Newton step keeps ~6 fixed-precision numbers.
**Relevance:** invsqrt (classic reference for Newton-based 1/√w with error analysis; costlier than table methods).
Confidence: **PARTIAL**.

### B.9 Efficient quantum circuits for square-root and inverse square-root
*S. Dutta, Y. Tavva, D. Bhattacharjee, A. Chattopadhyay, VLSID 2020 (not on arXiv).* Clifford+T realisations of
√x and 1/√x across number formats (the "Wang et al. 2020" item in the brief could not be identified; the closest
matches are this paper and Wang et al.'s function-value binary-expansion circuits for transcendental functions).
**Relevance:** invsqrt, low (NISQ-style T-count designs, no measurement-based tricks). Confidence: **SNIPPET**.

### B.10 Halving the cost of quantum addition
*C. Gidney, Sep 2017, arXiv:1709.06648 (Quantum 2, 74, 2018).*
**Temporary logical-AND**: compute a∧b into an ancilla with 4 T (one Toffoli-equivalent), *erase it with zero T*
by X-basis measurement + classically-controlled CZ (this is exactly kickmix's HMR / `init_and`/`del_and`). n-bit
adder from 8n to 4n T (n − 1 Toffolis + measurement uncompute). **Relevance:** all three — every carry chain,
multiplier row, comparator and QROM in the baselines should be built from computed-once/measured-away ANDs; the
companion paper reports ~50 % savings on cleanups from this alone. Confidence: **FULL** (short paper).

### B.11 Windowed quantum arithmetic
*C. Gidney, May 2019, arXiv:1905.07682.*
Replace k successive controlled operations by one small QROM lookup addressed by the k control bits ("windowing"),
e.g. windowed multiplication/exponentiation; table lookup (Babbush et al. 2018 unary iteration) costs L − 1
Toffolis for L entries regardless of output width; **uncomputing a lookup costs only ~2√L Toffolis** via MBU +
a fix-up lookup over √L entries (Fig. 3). **Relevance:** invsqrt (large coefficient tables are cheap to compute
and almost free to erase; windowed multipliers for the remaining products), dfthcsos (angle QROMs), dqi (windowed
field-constant multiplications are Clifford anyway). Confidence: **PARTIAL** (key sections read).

### B.12 Asymptotically efficient quantum Karatsuba multiplication
*C. Gidney, Apr 2019, arXiv:1904.07356.* O(n^{lg 3}) Toffolis with O(n) space by adding recursive outputs directly
into sub-sections of the target. **Relevance:** invsqrt only marginally (cross-over above competition widths);
the binary-field Karatsuba variants (B.13/C.6) matter for dqi. Confidence: **ABSTRACT**.

### B.13 T-count optimized design of quantum integer multiplication
*E. Muñoz-Coreas, H. Thapliyal, Jun 2017, arXiv:1706.05113.* Garbage-free 4n + 1 qubit schoolbook multiplier with a
conditional adder (Toffoli instead of controlled add when the multiplier bit is 0); T-count savings ~47–75 % vs
prior. **Relevance:** invsqrt (reference point for ancilla-free multipliers; Gidney-style measured ANDs supersede
its T-count accounting). Confidence: **ABSTRACT**.

### B.14 Trading T gates for dirty qubits in state preparation and unitary synthesis
*G. H. Low, V. Kliuchnikov, L. Schaeffer, Dec 2018, arXiv:1812.00954 (Quantum 2024).*
**SelectSwap / QROAM**: a table of N words of b bits costs ⌈N/λ⌉ + b(λ − 1) Toffolis (λ clean or dirty qubit
blocks; T-count 4⌈N/λ⌉ + 8bλ in T units), optimum λ ≈ √(N/b) giving O(√(Nb)); dirty-qubit variants
(Fig. 1d: 8⌈N/λ⌉ + 32bλ T) let idle data qubits host the swap network. **Relevance:** dfthcsos (the angle QROMs
and Inner/Outer preps are exactly QROAMs; companion paper's Inner-prep heuristic rows come from 2502.15882 which
uses these formulas), invsqrt (space–time trade for coefficient tables). Confidence: **PARTIAL**.

### B.15 Encoding electronic spectra in quantum circuits with linear T complexity
*R. Babbush, C. Gidney, D. W. Berry, N. Wiebe, J. McClean, A. Paler, A. Fowler, H. Neven, May 2018, arXiv:1805.03662 (PRX 8, 041015).*
Introduces **unary iteration** (L − 1 Toffolis to iterate over L indices with ⌈log L⌉ ancillas) and QROM (L − 1
Toffolis for L entries independent of word width), qubitisation walk operator, coherent alias sampling for
state preparation. **Relevance:** dfthcsos (the reference angle oracle is literally "QROM via unary iteration with
MBU"); invsqrt (coefficient lookup). Confidence: **PARTIAL**.

### B.16 Qubitization of arbitrary basis quantum chemistry leveraging sparsity and low rank factorization
*D. W. Berry, C. Gidney, M. Motta, J. R. McClean, R. Babbush, Feb 2019, arXiv:1902.02134 (Quantum 3, 208).*
Sparse and single-factorised LCUs; QROAM cost ⌈d/k⌉ + M(k − 1) Toffolis to compute and **⌈d/k⌉ + k to
uncompute** (Appendix C: measure outputs in X basis, fix phases with a lookup over d/k entries), different k for
compute vs uncompute; with dirty qubits 2⌈d/k⌉ + 4M(k−1). FeMoCo (Reiher): ~700× less spacetime volume than
prior. **Relevance:** dfthcsos (QROAM uncompute formula used by all later chemistry papers and by the heuristic
Inner/Outer costs), invsqrt. Confidence: **PARTIAL** (QROAM sections read).

### B.17 Compilation of fault-tolerant quantum heuristics for combinatorial optimization
*Y. R. Sanders, D. W. Berry, P. C. S. Costa, L. W. Tessler, N. Wiebe, C. Gidney, H. Neven, R. Babbush, Jul 2020, arXiv:2007.07391 (PRX Quantum 1, 020312).*
Phase/energy oracles for Ising-type cost functions; **QROM-based function evaluation** (Sec. II E): piecewise-linear
f̃(z) = αf(z_ℓ) + (1−α)f(z_{ℓ+1}) with slope/intercept from a lookup; **variable-spacing QROM** (Fig. 3) that outputs
one word per power-of-two (or arbitrary) sub-range with Toffoli count = number of distinct ranges − 1, independent
of word width. **Relevance:** invsqrt (the baseline's "4n + 2" QROM comes from here; dyadic tables of lines are the
natural design), dfthcsos (pruned QROMs). Confidence: **PARTIAL** (Sec. II E read).

### B.18 Improved quantum circuits for division
*P. Mukhopadhyay, A. Gheorghiu, H. Krovi (IBM), Mar 2026, arXiv:2603.18110.* COMP-N-SUB primitive (compare and
conditionally subtract at ≈ one addition's cost); division T-count O(nm). **Relevance:** invsqrt (only if a design
needs division; mostly not), dqi (no). Confidence: **ABSTRACT**.

### B.19 Approximate encoded permutations and piecewise quantum adders
*C. Gidney, 2019, arXiv:1905.08488 (cited by Gu et al. as ref. [18]).* Piecewise adders that are exact except on a
small fraction of inputs — the fixed-point analogue of "spend the failure budget". Not downloaded.
**Relevance:** invsqrt has *zero* failure budget, so only usable where exactness is provable. Confidence: **SNIPPET**.

---

## C. dqi — Decoded Quantum Interferometry and reversible Reed–Solomon decoding

### C.1 Optimization by Decoded Quantum Interferometry
*S. P. Jordan, N. Shutty, M. Wootters, A. Zalcman, A. Schmidhuber, R. King, S. V. Isakov, R. Babbush, Aug 2024, arXiv:2408.08292 (Nature 646, 2025).*

**Method.** DQI prepares |P(f)⟩ = Σ_x P(f(x))|x⟩ for max-LINSAT by (1) a superposition over sparse error vectors
e weighted by the optimal degree-ℓ polynomial's coefficients w_k (principal eigenvector of a tridiagonal
matrix — the competition's test distribution, E[wt(e)] ≈ 31.05, Pr[wt = 35] ≈ 2.8 %), (2) syndrome computation
s = Bᵀe, (3) *reversible decoding* to uncompute e, (4) inverse QFT. **Semicircle law**: expected satisfied fraction
(√(ℓ/m·(1−r/q)) + √((1−ℓ/m)·r/q))² when the dual code is decodable to ℓ errors. OPI (fit a degree < n polynomial
through prescribed value-sets at all m = q − 1 points) has a Vandermonde B so the dual code is Reed–Solomon,
decodable to half distance by Berlekamp–Massey; at n/p = 1/2, OPI reaches ⟨s⟩/m ≈ 0.933 vs Prange 0.75. The paper
gives an optimised **reversible Berlekamp–Massey** (shortest-LFSR) circuit: p = 521 prime field needs ≈1e8
Toffolis and 9e3 qubits. Decoding failures only reduce the probability of good samples (candidates are classically
checked), which is why the competition prices ε via a repetition factor.

**Relevance.** dqi — defines the task, the input distribution, why approximate decoding is acceptable, and
Berlekamp–Massey as the alternative to EEA. Confidence: **PARTIAL** (abstract, Sec. 8 structure and RS/OPI
passages via grep; the reversible BM appendix not read in detail).

### C.2 Verifiable Quantum Advantage via Optimized DQI Circuits
*T. Khattar, N. Shutty, C. Gidney, A. Zalcman, N. Yosri, D. Maslov, R. Babbush, S. P. Jordan (Google Quantum AI), Oct 2025, arXiv:2510.10967. Data/code: Zenodo 17301475.*

**Method.** The source of the competition baseline. (a) **Space-efficient DQI circuit**: sparse Dicke states
(ℓ·⌈log₂m⌉ qubits instead of m), sequential error-symbol generation with immediate X-basis measurement (MBU) of
each symbol e_i (phase (−1)^{c_i·e_i} fixed later during decoding), so the whole algorithm needs 2nb + O(log n)
qubits; this is why the benchmark's input is "syndrome + classical record c". (b) **Two EEA compilations**:
*explicit Bézout* — improved Proos–Zalka synchronised Euclid with in-register quotient storage (deterministic
2nb + O(log n) space, 6n² quantum–quantum multiplications, unified cycle architecture; worst case 6n iterations,
Appendix D), and *implicit Bézout* — the **"Dialog" representation** (record the constant-time Bernstein–Yang
divstep transition matrices in the space freed as polynomials shrink: len(poly) + len(dialog) = 2n; 2n² QQ
multiplications; direct modular division 4n² vs 7n² for invert-then-multiply). (c) Full RS decoder: key equation
σS ≡ Ω (mod z^{2ℓ}) by EEA on (z^{2ℓ}, S), Chien search, Forney e_j = −Ω(γ_j⁻¹)/σ′(γ_j⁻¹); Table V leading-order
costs — explicit: 3n² QQ mults + mn QC mults + m + 6n inversions; implicit: 2mn + n² QQ + mn/2 QC + m + n
inversions. Over GF(2^b) QC multiplication, squaring and addition are **CNOT-only**, so the explicit model wins
(Chien evaluation is Clifford). (d) **GF(2^m) arithmetic** (Appendix C): Karatsuba-style multipliers from
van Hoof's construction tuned to a ∞:1 Toffoli:CNOT weight — **m = 10: 39 Toffoli / 738 CNOT; m = 11: 47/1278;
m = 12: 51/1506** (Table VII); "parity-control Toffoli" (PCTOF) abstraction with a rank-based minimisation
(k PCTOFs ≙ k × m² Boolean matrix → rank lower bound); **MBU of GF2 multiplication** (measure the product
register in X basis, fix phase with a CZ circuit of depth ≈ m/2 + O(log m); implemented as `GF2MulMBUC` in
Qualtran); Itoh–Tsujii inversion with O(log b) multiplications. (e) Classical hardness: Prange and "extended
Prange" (XP) over extension fields; Maiorana–McFarland bent target sets (r = (2^b − 2^{b/2})/2 = 2016 at b = 12);
instances needing > 1e23 trials deemed intractable.

**Key numbers (Table VI).** (4095, 70, 12, 2016): **5.72e6 Toffoli, 1.52e8 Clifford, 1,885 logical qubits**,
4.75e26 Prange / 1.97e23 XP trials; (4095, 60, 12): 4.64e6 / 1,640; (1023, 70, 10): 3.59e6 / 1,569. Physical:
≈800 k physical qubits, ~1 h (d = 21 hot patches, yoked cold storage, magic-state cultivation; 58,215 GF2Mul and
687,564 SynthesizeLR calls; 1.5·51 ≈ 77d rounds per multiplication).

**Relevance.** dqi — this *is* the baseline design; its Table V/VII and Appendix C are the cost model for any
EEA-based redesign; its own suggestions (51-Toffoli multiplier, PCTOF rank optimisation, Dialog representation,
MBU of products) are the first things to try. Confidence: **FULL** (Secs. I–II, V, Appendix C read).

### C.3 Discovering state-of-the-art quantum circuits with LLMs — RS decoder (see A.2)
Berlekamp–Massey replacement: 4.4e5 Toffoli, 1,837 qubits (≈12× TQ). Under the competition metric
R·Q²·T this is ≈ 1.19 × 1,837² × 4.4e5 ≈ 1.77e12 (≈ 14× better than baseline) — far behind the community's
≈890-qubit decoders (≈ 4.0e11), because Q enters squared and 1,837 is still 2.2× the 840-qubit floor.
The *ideas* (phase-only recovery via traces, precomputed reciprocal, in-place evaluator, classical Z-gate
cancellation of the mask at n+1 positions, failure-budgeted stack) transfer directly. Confidence: **FULL**.

### C.4 The quantum decoding problem
*A. Chailloux, J.-P. Tillich (Inria), Oct 2023, arXiv:2310.20651 (TQC 2024).*
Studies decoding when the noisy codeword is given in superposition (the quantum analogue of Regev's SIS→LWE
reduction); shows quantum-polynomial-time decoding for random linear codes at low noise (via unambiguous state
discrimination of the error register), and relates it to DQI-style reductions. **Relevance:** dqi, conceptual
only (why decoding-in-superposition is the hard step; no circuits). Confidence: **ABSTRACT**.

### C.5 On the design and optimization of a quantum polynomial-time attack on elliptic curve cryptography
*D. Maslov, J. Mathew, D. Cheung, D. K. Pradhan, Oct 2007, arXiv:0710.1093 (QIC 2009).*
First optimised reversible GF(2^m) multiplier (polynomial-basis Mastrovito-style, O(m²) Toffolis, no ancilla)
and ECDLP circuit over binary curves. **Relevance:** dqi (historical baseline for field multiplication;
superseded by Karatsuba variants). Confidence: **ABSTRACT**.

### C.6 Space-efficient quantum multiplication of polynomials for binary finite fields with sub-quadratic Toffoli gate count
*I. van Hoof (TU Eindhoven), Oct 2019, arXiv:1910.02849.*
In-place Karatsuba multiplication modulo an irreducible polynomial with 2n input + n output qubits, **no
ancillas**, O(n^{log₂3}) Toffolis (CNOTs up to O(n²) but much lower in practice). This is the construction the
baseline's 63-Toffoli F_{2^12} multiplier and Khattar et al.'s 51-Toffoli tuned version descend from.
**Relevance:** dqi (multiplier design space; the community's best uses a **42-AND** scheme found by flip-graph
search — see F.2 — which is the bilinear-rank route rather than Karatsuba). Confidence: **ABSTRACT**.

### C.7 Asymptotic yet practical optimization of quantum circuits implementing GF(2^m) multiplication and division
*N. Yosri, D. Gavinsky, D. Maslov (Google Quantum AI / CAS), Nov 2025 (v3 Mar 2026), arXiv:2511.20618.*
Ancilla-free multiplication with O(m^{log₂3}) *CNOT* count (by choosing irreducible polynomials that make
multiplication by 1 + x^{⌈m/2⌉} O(m)), 100+× CNOT reductions at practical m; division via addition chains with
O(m² log log m / log m) gates; objective 10·Toffoli + CNOT; reports up to 28 % reductions in both Toffoli and CNOT
for cryptographic sizes; defines PCTOF gates. **Relevance:** dqi — CNOTs are free in the metric, but the paper's
choice of irreducible polynomial/addition chains for *inversion* (the 315-Toffoli Itoh–Tsujii in the baseline)
is directly reusable; note the field polynomial is fixed by the benchmark (α¹² + α⁶ + α⁴ + α + 1), so gains must
come from isomorphic tower-field representations (community: GF((2^6)²) "mul99"/"Tower42"). Confidence: **PARTIAL**.

### C.8 Concrete quantum cryptanalysis of binary elliptic curves
*G. Banegas, D. J. Bernstein, I. van Hoof, T. Lange, 2020, IACR ePrint 2020/1296 (TCHES 2021).* 7n + ⌊log₂n⌋ + 9
qubits; Toffoli count 48n³ + 8n^{log₂3+1} + 352n² log₂n + 512n² + …; GF(2^n) inversion by Bernstein–Yang-style
constant-time GCD (4nb + n + O(log n) qubits, 4n² multiplications per Khattar et al. Table III) and FLT/Itoh–Tsujii
alternatives (Taguchi–Takayasu 2023 improve the addition chains). **Relevance:** dqi (inversion costs; shows the
qubit overhead of division-free EEAs that the Dialog representation removes). Confidence: **SNIPPET**.

### C.9 Itoh–Tsujii inversion
*T. Itoh, S. Tsujii, Inf. Comput. 83 (1989).* a⁻¹ = (a^{2^m−1−1}) computed with ⌊log₂(m−1)⌋ + HW(m−1) − 1
multiplications plus Frobenius squarings (CNOT-only in GF(2^m)); for m = 12 the baseline spends 315 Toffolis
(≈ 6 × 51 + overhead) and 48 scaffold qubits. **Relevance:** dqi (the per-position inversion in Chien/Forney is
22.5 % of baseline Toffolis; Gu et al. eliminate it entirely with a precomputed reciprocal polynomial).
Confidence: classic result, cited via C.2.

### C.10 A provable quantum advantage for approximate optimization via DQI
*(2026), arXiv:2610.02145.* Proves a strict approximation-ratio gap between DQI and polynomial-time classical
algorithms for an OPI-like family, still relying on conventional unique decoding of RS codes via Berlekamp–Massey.
**Relevance:** dqi motivation only. Confidence: **SNIPPET**.

---

## D. dfthcsos — FeMoCo phase estimation, tensor factorisations, SOS/spectrum amplification, Givens trees

### D.1 Fast quantum simulation of electronic structure by spectrum amplification  *(primary source for the chemistry benchmark)*
*G. H. Low, R. King, D. W. Berry, Q. Han, A. E. DePrince III, A. White, R. Babbush, R. D. Somma, N. C. Rubin, arXiv:2502.15882 (Feb 2025); published as "Fast Quantum Simulation of Electronic Structure by Spectral Amplification", **Phys. Rev. X (Oct 2025), DOI 10.1103/pb2g-j9cw**.*
Named by the Google announcement as the basis of Benchmark III (sum of squares, spectral amplification, the
λ_eff = √(E_gap(2Λ − E_gap)) formula, DF-THC factorisation, Inner/Outer prep cost tables).

**Method.** Write H − E_SOS·I = Σ_α O_α†O_α (sum of squares) and block-encode the *square root* H_sqrt = [O_α]
with normalisation Λ (= ½Σλ_α²); qubitising the SOS form amplifies the low-energy spectrum so that phase-estimation
queries scale as πλ_eff/(2σ) with **λ_eff = √(E_gap(2Λ − E_gap))** (Eq. 11), E_gap = E_gs − E_SOS. For chemistry the
SOS algebra is spin-free degree-2: generators O_D (positive one-body eigenspace), O_Q (negative), and O_SF,rc =
(w_B I + i/2 Σ_b Σ_σ w_b γ_{u_b σ0}γ_{u_b σ1})/√2 (Eqs. 28–30, A6–A8). The two-electron tensor is approximated by
**DF-THC**: h⁽²⁾_pqrs ≈ Σ_{ρ,c} X⁽ρc⁾_pq X⁽ρc⁾_rs with X⁽ρc⁾ = Σ_b w⁽ρc⁾_b u⁽ρ⁾_b u⁽ρ⁾_bᵀ (R rank components, B unit
vectors per component, C coefficient copies) — DF is (R, N, 1), THC is (1, R_THC, R_THC). Block encoding
(Fig. 2, Table III, Appendix B): Outer prep over N + RC addresses (alias sampling), Inner prep over b ∈ [B+1]
(QROAM), **Rot = QROM of (N−1)·b_rot angle bits addressed by N + RB vectors** (cost ≈ N + RB per call, output
(N−1)b_rot qubits), Givens rotations 2(N−1)b_rot Toffolis per basis change via phase-gradient additions, Sel ≈
4(N−1)b_rot, reflection, and the whole thing applied twice (square). Rot/Qroam/Sel ≈ 90 % of Toffolis, Sel ≈ 60 %.
Heuristics: C = Θ(N), B = Θ(N), R = Θ̃(1); b_rot ∈ [11, 18], b_coeff ∈ [6, 14]; randomised rounding converts bit
truncation into a variance term (Appendix D). Factorisation found by Adam gradient descent on
‖h^S − h⁽²⁾‖_fro with ReLU regularisers on Λ and E_gap (Table IV: FeMoCo-76 (76,15,57,19), λ_reg = 100 mHa).
E_gap bounded by variational energies (DMRG M = 6000 for FeMoCo-76: E_upper −1119.05933, lower bound −1123.300,
E_gap = 4.240 Ha, λ_eff lower bound 21.69 Ha). BLISS symmetry shift (S, β₁) applied before factorisation.

**Key numbers (Table V).** FeMoCo [113e,76o]: (R,B,C) = (15,57,19), ε_fro = 0.0825 Ha, **Λ = 179.73 Ha,
E_gap = 5.382 Ha, λ_eff = 43.65 Ha, C_BE = 14,563 Toffolis, 1,459 qubits, total 9.99e8 Toffolis** (4.3× vs
THC+BLISS 198.9 Ha / 13,763; 37× vs DF 584.5 Ha / 40,442). FeMoCo-54: (10,27,27), Λ 58.34, E_gap 4.05,
λ_eff 21.37, C_BE 10,169, 1,137 qubits, 3.41e8 Toffolis (Table III breakdown: Rot QROM 324, ROT 3,180 = 4·15·53,
Inner QROAM 860 + 254, Outer 310; 795 persistent angle qubits; total walk 9,997 Toffolis, 1,131 qubits). Scaling:
Toffolis ∝ N^{2.09}, Λ ∝ N^{1.46}, λ_eff ∝ N^{1.14}, E_gap ∝ N^{0.88}. Physical: 4.5 M qubits, 8.6 h (FeMoCo-76).

**Relevance.** dfthcsos — this is the algorithm being benchmarked ("DF-THC-SOS"); the score's λ_eff, the Λ and
E_gap floors, the 20 mHa Frobenius gates, the angle QROM contract (N + RB addresses × (N−1) words of β bits),
the Inner/Outer heuristic costs, and the J-batched angle streaming all come from here. Important caveat found by
the community (F.3): the paper's FeMoCo-76 factorisation has ε_fro = 82.5 mHa, so it *fails* the competition's
20 mHa gate even though its λ_eff (43.65) is lower than the public best (48.76); with the verifier's fixed
symmetry shift the community estimates λ_eff ≥ 46.79 is a floor. Confidence: **FULL** (Secs. II–V, Tables
II–V, Appendix A/B skimmed).

### D.2 Quantum simulation with sum-of-squares spectral amplification
*R. King, G. H. Low, R. Babbush, R. D. Somma, N. C. Rubin, May 2025, arXiv:2505.01528.*
General SOSSA framework (energy/phase estimation, Gibbs sampling) with a √N asymptotic speedup for the SYK model;
formalises the E_gap/Λ trade-off used in D.1. **Relevance:** dfthcsos theory (why lowering Λ and E_gap both reduce
λ_eff; λ_eff ≈ √(2ΛE_gap) when E_gap ≪ Λ). Confidence: **ABSTRACT**.

### D.3 Elucidating reaction mechanisms on quantum computers
*M. Reiher, N. Wiebe, K. M. Svore, D. Wecker, M. Troyer, May 2016, arXiv:1605.03590 (PNAS 2017).*
Origin of the FeMoCo benchmark (54-orbital active space, ~1e14 T gates, ~111 logical qubits in the original
Trotter estimate). **Relevance:** historical context only. Confidence: **ABSTRACT**.

### D.4 Qubitization of arbitrary basis quantum chemistry (see B.16)
Sparse/single-factorised LCU, QROAM uncompute ⌈d/k⌉ + k; FeMoCo (Reiher) ≈ 700× less spacetime volume than
Reiher et al. Confidence: **PARTIAL**.

### D.5 Quantum computing enhanced computational catalysis
*V. von Burg, G. H. Low, T. Häner, D. S. Steiger, M. Reiher, M. Roetteler, M. Troyer, Jul 2020, arXiv:2007.14460 (Phys. Rev. Research 2021).*
**Double factorisation (DF)** of the Coulomb tensor (eigen-decompose h⁽²⁾ into rank-R one-body squares, then
eigen-decompose each one-body operator; truncate by eigenvalue thresholds), block-encoded with programmable
Givens rotations loaded by QROM; ~1.2e10 Toffolis / ~4,000 qubits for the 54-orbital FeMoCo (vs 2.3e11 Berry 2019);
1-norm λ_DF; Toffoli cost ≈ "cW ≤ … + 2λNβ + 8Nβ + 4N" with rotation precision β. **Relevance:** dfthcsos — the
(R, N, 1) corner of DF-THC and the first use of QROM-loaded Givens rotations for a basis change per leaf.
Confidence: **PARTIAL**.

### D.6 Even more efficient quantum computations of chemistry through tensor hypercontraction
*J. Lee, D. W. Berry, C. Gidney, W. J. Huggins, J. R. McClean, N. Wiebe, R. Babbush, Nov 2020, arXiv:2011.03494 (PRX Quantum 2, 030305, 2021).*
**THC** block encoding with Õ(N) Toffolis: h⁽²⁾ ≈ Σ_{µν} χ_p^µ χ_q^µ ζ_{µν} χ_r^ν χ_s^ν; the basis rotation to
χ^µ uses N/2 Givens rotations whose angles are QROM-loaded (Sec. "rotation angles loaded from QROM", cost
N(i − 2) Toffolis to apply rotations with i angle bits via **phase-gradient additions**; each b_r-bit rotation =
b_r − 3 Toffolis), QROAM for coefficients, coherent alias sampling. FeMoCo: Reiher 2,142 qubits / 5.3e9 Toffolis;
Li 2,196 / 3.2e10; ~4 M physical qubits, < 4 days. **Relevance:** dfthcsos — the (1, R_THC, R_THC) corner; the
"QROM of rotation angles + phase-gradient Givens" pattern is the angle-oracle/Givens pipeline the benchmark isolates.
Confidence: **PARTIAL**.

### D.7 Reducing the runtime of fault-tolerant quantum simulations in chemistry through symmetry-compressed double factorization
*D. Rocca, C. L. Cortes, J. Gonthier, P. J. Ollitrault, R. M. Parrish, G.-L. Anselmetti, M. Degroote, N. Moll, R. Santagati, M. Streif (QC Ware / Boehringer Ingelheim), Mar 2024, arXiv:2403.03502 (JCTC 2024).*
**SCDF** = compressed DF (optimise the factors directly against the integrals with a cost function penalising
large W_t components) + symmetry shift (Loaiza–Izmaylov). FeMoCo-54 (Table 2): XDF λ = 293.9 Ha (9.6e9 Toffoli,
3,722 qubits); XDF + sym. shift 182.9 Ha (62 %); THC 306.3 Ha (5.3e9, 2,142); **SCDF 5N: λ = 78.0 Ha, 2.4e9
Toffolis, 3,722 qubits (k_r = 2 variant: 2.6e9, 1,994 qubits)** — 1-norm about ¼ of XDF/THC, < half THC's
Toffolis. **Relevance:** dfthcsos — direct evidence that *optimising the factors* (rather than truncating an
eigendecomposition) and symmetry shifting are the big levers on Λ; and that qubit count can be traded via the
rotation-batching parameter k_r (≙ J here). Confidence: **PARTIAL** (results tables read).

### D.8 Block-invariant symmetry shift (BLISS)
*I. Loaiza, A. F. Izmaylov, Apr 2023, arXiv:2304.13772 (JCTC 2023).* Subtract T̂ = (N̂ − η)(…) built from symmetry
operators so H − T̂ has the same spectrum on the η-electron sector but a smaller LCU 1-norm (≈2× on small
molecules). The competition's Hamiltonian already includes a fixed shift (S, β₁) of this type ("Hsym" in the
npz, Eq. 46 of the companion paper: H = Σ(h⁽¹⁾ − η/2 S + β₁δ)E + ½Σ(h⁽²⁾ + (S⊗I + I⊗S)/2)EE − ηβ₁I), and the
verifier *ignores* any submitted shift. **Relevance:** dfthcsos — understand what is fixed; the remaining freedom
is the factorisation of the shifted tensor. Confidence: **ABSTRACT + companion paper**.

### D.9 Global minimization of electronic Hamiltonian 1-norm via linear programming in BLISS (LP-BLISS)
*S. Patel, A. S. Brahmachari, J. T. Cantin, L. Wang, A. F. Izmaylov, Sep 2024, arXiv:2409.18277.* Recasts the BLISS
optimisation as an LP with guaranteed optimality; FeMoCo-Lg (76o): Pauli 1-norm 1174 → 487.5 Ha (59 % reduction);
FeMoCo-Sm: 296.9 → 169.4 (and DF/THC variants 78.0/57.9 Ha after fermionic shifts). **Relevance:** dfthcsos
(magnitude of symmetry-shift gains; but the shift is frozen in the benchmark). Confidence: **PARTIAL**.

### D.10 Simultaneously optimizing symmetry shifts and tensor factorizations
*K. Deka, E. Zak (BEIT), Dec 2024, arXiv:2412.01338 (JCTC 2025).* Joint optimisation of DF factors and BLISS
parameters; ≥25 % reduction of λ_DF for FeMoCo and P450 vs prior. **Relevance:** dfthcsos (joint optimisation is
the right mindset even with the shift frozen: optimise factors against the *shifted* tensor under the 20 mHa
constraint while regularising Λ). Confidence: **ABSTRACT**.

### D.11 Assessing the query complexity limits of quantum phase estimation using symmetry-aware spectral bounds
*C. L. Cortes, D. Rocca, J. F. Gonthier, P. J. Ollitrault, R. M. Parrish, G.-L. Anselmetti, M. Degroote, N. Moll, R. Santagati, M. Streif, Mar 2024, arXiv:2403.04737 (PRA 110, 022420).*
Hierarchy of lower bounds on the LCU 1-norm: Δ/2 (spectral range) ≥ Δ_s/2 (symmetry-shifted) ≥ Δ_µ/2 (block-invariant
sector); variational orbital-optimised estimates; FeMoCo bound ≈ 108.9 Ha (BLISS-THC within 2×). **Relevance:**
dfthcsos — explains why Λ cannot be pushed arbitrarily low and why the organisers impose Λ > 49 and
E_gap > 3.9149 floors (λ_eff floor ≈ 46.8 per community analysis). Confidence: **PARTIAL**.

### D.12 Majorana tensor decomposition (MTD)
*I. Loaiza, A. S. Brahmachari, A. F. Izmaylov, Jul 2024, arXiv:2407.06571 (QST 2025).* Unifies DF, THC, CSA, etc.
as tensor decompositions over Majorana operators; lowest possible 1-norm is half the spectral range. **Relevance:**
dfthcsos (framework; DF-THC is an MTD instance). Confidence: **ABSTRACT**.

### D.13 Accelerating quantum computations of chemistry through regularized compressed double factorization
*O. Oumarou, M. Scheurer, R. M. Parrish, E. G. Hohenstein, C. Gogolin, Dec 2022, arXiv:2212.07957 (Quantum 2024).*
RC-DF: fit compressed DF factors with an L1-style regulariser that directly lowers λ; 3× fewer measurement bases
(NISQ) and lower λ for FT. **Relevance:** dfthcsos — regularised gradient fitting of (u, w) with a Λ penalty is the
same recipe as D.1's Table IV optimiser. Confidence: **ABSTRACT**.

### D.14 Faster quantum chemistry simulations with improved tensor factorization and active volume compilation
*A. Caesura, C. L. Cortes, W. Pol, S. Sim, M. Steudtner, G.-L. Anselmetti, M. Degroote, N. Moll, R. Santagati, M. Streif, C. S. Tautermann (PsiQuantum / BI), Jan 2025, arXiv:2501.06165 (PRX Quantum 2026).*
**BLISS-THC** (joint THC fit + block-invariant shift) + active-volume compilation. FeMoCo (113e,76o), Table VII:
Sparse λ 1547.3 / 4.4e10 Toffoli; DF* 582.4 / 3.2e10 / 6,402 qubits; THC 1201.5 / 3.2e10; THC* 781.8 / 2.1e10;
**BLISS-THC λ = 198.9 Ha, 4.3e9 Toffolis, 1,512 qubits, THC rank M = 290** (CCSD(T) error < 0.3 mHa). Givens
rotations ≈ 4Nℶ Toffolis with ℶ = 18 angle bits; dataloaders 2M + N Toffolis. **Relevance:** dfthcsos — best
pure-THC numbers for the same active space (the DF-THC+SA paper beats it 4×); shows the rank/accuracy frontier.
Confidence: **PARTIAL**.

### D.15 Quantum simulation of electronic structure with linear depth and connectivity
*I. D. Kivlichan, J. McClean, N. Wiebe, C. Gidney, A. Aspuru-Guzik, G. K.-L. Chan, R. Babbush, Nov 2017, arXiv:1711.04789 (PRL 120, 110501, 2018).*
Fermionic swap networks; any Slater determinant / single-particle basis rotation via a **network of N(N−1)/2
Givens rotations in depth N** (N/2 for a single determinant), nearest-neighbour only. **Relevance:** dfthcsos — a
*rank-1* rotation (one vector u) needs only N − 1 Givens rotations along a tree/path; the companion paper's
`TreeMajoranaCoefficients` (u_{q_k} ← u_{p_k} sin θ_k, u_{p_k} ← u_{p_k} cos θ_k in parent-before-child order) is
the tree generalisation, and the tree shape changes the angle statistics (hence QROM compressibility) and
the adder widths. Confidence: **ABSTRACT/PARTIAL**.

### D.16 Universal quantum circuits for quantum chemistry
*J. M. Arrazola, O. Di Matteo, N. Quesada, S. Jahangiri, A. Delgado, N. Killoran (Xanadu), Jun 2021, arXiv:2106.13839 (Quantum 2022).*
Controlled single-excitation Givens rotations are universal for particle-conserving unitaries; gradient formulas.
**Relevance:** dfthcsos, low (conceptual background on Givens networks). Confidence: **ABSTRACT**.

### D.17 Fault-tolerant quantum simulation of materials using Bloch orbitals
*N. C. Rubin, D. W. Berry, F. D. Malone, A. F. White, T. Khattar, A. E. DePrince III, S. Sicolo, M. Kühn, M. Kaicher, J. Lee, R. Babbush, Feb 2023, arXiv:2302.05531 (PRX Quantum 2023).*
Sparse/SF/DF/THC LCUs for periodic systems; QROAM cost ⌈L/k⌉ + m(k−1) with k ≈ √(L/m) → O(√(Lm)); exploits
translational symmetry to shrink QROM output by N_k. **Relevance:** dfthcsos (QROAM bookkeeping; symmetry-based
table compression analogous to Gu et al.'s frame blocks). Confidence: **PARTIAL**.

### D.18 Gu et al. SI IV: Fe₂S₂ sparse-qubitisation Select/QROM (see A.2)
Baseline 55 k Toffolis / 139 qubits (QROM of 34-bit alias words 13 k, Select traversal 41 k) → 15 k / 126 by
**frame-block Select** (group Pauli terms related by fixed Clifford "frames" from spin and spatial symmetries,
select a representative + controlled frames) and **repeated-pattern alias tables** (exploit the freedom to
permute terms and choose alias tables). **Relevance:** dfthcsos — the angle table (N + RB addresses × 75 words)
has analogous structure (equal/near-equal angles, tree-induced zeros); choose the Givens tree and vector
ordering to make the QROM compressible. Confidence: **FULL**.

---

## E. Generic fault-tolerant compilation and cost models

### E.1 Efficient magic state factories with a catalyzed |CCZ⟩ → 2|T⟩ transformation
*C. Gidney, A. G. Fowler, Dec 2018, arXiv:1812.01238 (Quantum 3, 135, 2019).* CCZ factory 12d × 6d footprint, one
|CCZ⟩ per 5.5d cycles; one CCZ state converts exactly to two |T⟩ states with a catalyst. Hence the accounting
"1 Toffoli ≈ 2 T" used by Kivlichan et al. and the competition's C = Toffoli + T/4 (T priced at a quarter Toffoli,
i.e. the organisers weight T cheaper than factory parity). **Relevance:** invsqrt pricing of rotations (each fine
Z_POW ≈ 0.56 log₂(1/ε) + 5.3 T ≈ 19–25 T ≈ 5–6 Toffoli-eq; 37 rotations ≈ 3 % of baseline cost). Confidence: **ABSTRACT**.

### E.2 Novel constructions for the fault-tolerant Toffoli gate
*C. Jones, Dec 2012, arXiv:1212.5069 (PRA 87, 022328, 2013).* Toffoli with 4 T (+ measurement), n extra controls cost
4n T; error-detecting Toffoli. Gidney's temporary AND (B.10) is the same idea framed for reuse. Confidence: **ABSTRACT**.

### E.3 On the advantages of using relative phase Toffolis
*D. Maslov, Aug 2015, arXiv:1508.03273 (PRA 93, 022311, 2016).* Circuit identities letting relative-phase Toffolis
(cheaper T-count/CNOT) replace true Toffolis inside multi-controlled gates and compute/uncompute pairs.
**Relevance:** in kickmix only exact permutations + diagonal phases are allowed, so relative-phase gates are
usable only where the stray phase is later cancelled (compute/uncompute pairs); measured-AND already captures
most of the gain. Confidence: **ABSTRACT**.

### E.4 Assessing requirements to scale to practical quantum advantage
*M. E. Beverland et al. (Microsoft), Nov 2022, arXiv:2211.07629.* Resource-estimation framework across the stack
(Azure QRE); rotation synthesis costs ≈ 0.53 log₂(1/ε) + 5.3 T (the "mixed fallback" formula quoted by the
competition as 0.56 log₂(1/ε) + 5.3 comes from this line of work / ref. [24] of the companion paper). Confidence: **ABSTRACT**.

### E.5 How to compute a 256-bit elliptic curve private key with only 50 million Toffoli gates
*D. Litinski (PsiQuantum), Jun 2023, arXiv:2306.08585.* Active-volume architecture; 50 M Toffolis for ECDLP-256 at
the cost of more qubits — the Toffoli-vs-qubit trade that Babbush et al. (A.3) and the dqi metric penalise.
Confidence: **ABSTRACT**.

### E.6 A comprehensive review of quantum circuit optimization (2024)
*K. Karuppasamy et al., arXiv:2408.08941.* Survey of analytical, heuristic, ML and hybrid optimisers. Largely
NISQ-oriented; the companion paper notes black-box unitary optimisers are useless beyond ~40 qubits for kickmix
circuits. Confidence: **ABSTRACT**.

---

## F. Community state of the art (public repos/notebooks; COMMUNITY, unverified)

Sources: github.com/nasir26/vqcc-kaggle (`docs/NOTES.md`), github.com/acco-cyber/Quantum-Circuit (`STATUS.md`),
github.com/Inzainos/quantum-circuit-compilation, github.com/zjukop3/…-support,
github.com/harshulchess77-arch/… (`notes/`), github.com/blucca/quantum-circuit-research, github.com/tatra-labs/kickmix-arena.
Leaderboard top ≈ 26.1–26.8 (late Oct / early Nov 2026); best public portfolio ≈ 22.8–23.2.

### F.1 invsqrt
* Baseline anatomy (nasir26): rotations ≈ 3 % of cost; 88.5 % of Toffolis are multiplications; half of all Toffolis
  are the mirror uncompute; 231 of 260 qubits are named registers live for the whole circuit; worst error is only
  0.477 of tolerance.
* Public best: **62–63-qubit table-based circuits** (busyaprime v8: 63 q, score 20.23, worst error 0.9993 of
  tolerance; yoyobar 62 q: cost 100,693 ≈ 20.6×; "mrmeows" 76 q earlier). Mean ≈ 1,400 Toffolis at 63 q.
  Reported techniques: no Newton step; piecewise interpolation with lookup tables fitted to the exact integer
  computation (same recipe as Gu et al. A.2 SI III.2), measured uncompute of conditioned Toffolis (≈ halves their
  price), "flags" register re-encoding (unary → binary leading-zero count: 260 → 231 qubits, 7,735 → 6,852 Toffolis),
  Inzainos' "piecewise half-split" (fold M ∈ [2,4) onto M/2 with 1/√2 absorbed into coefficients so the table has
  2^{j+1} instead of 3·2^j entries; degree-2, j = 8, 183 q / 2,867 T → 570 k), "signed-digit Horner, shared lookup"
  (78 q / ≈1,700 Toffoli-eq). blucca: biased linear interpolant over 1,024 cells with joint 29-bit intercept +
  19-bit delta QROM and one 40-bit product → 150 q / 4,226 T (3.04×); degree-3 over 32 intervals failed to beat
  the baseline.
* Closed directions (nasir26): precision "saturated" — rotations cannot be made cheaper; 63 → 62 qubits achieved by a
  forum participant; further gains need fewer ancillas or cheaper phasing.

### F.2 dqi
* Baseline anatomy: EEA sweep 50 % of T, Chien inversions 22.5 %, polynomial storage 92.5 % of Q; constant
  multiplies and phase-by-product are Clifford. Qubit floor = 840 (syndrome); each qubit removed ≈ −0.23 % cost,
  each 1 % Toffoli cut ≈ −1 %. Tolerated failures cost ≈ +0.46 % per failure at k = 1, +5.33 % at k = 20.
* Public best: **"SomeJoint"/somejoint 897-qubit decoder** (mean 440,564 Toffolis, ratio ≈ 58.9–59.2), then
  889-qubit variants (alexchilton 4.1478e11; Ozer 4.084e11; yoyobar **4.0246e11 ≈ 60.7×**); R18 877 q and 883 q
  + "658-Toffoli jet" variants also reported. Design (from attribution): a "Schur"-type decoder with stages
  *extract / synthesis / convert / scan / unextract*; **rank-42 GF(2^12) multiplier** (42 ANDs; found by
  flip-graph search, ≈ 40 % of Toffolis), **GF(2^24) "mul99"** (≈ 25 %) and tower-field inverse, `zero_hold` 9 %,
  `phase_classical_parity` 6 %. Flip-graph search found no GF(2^12) scheme below rank 42 (rank 41 would save ~1 %).
  Replaying D (rather than holding it) during convert/unconvert is the better trade; additive-FFT root search is
  worse. zjukop3 "register freezes" on the baseline: 5.725 M → 5.165 M Toffolis at Q = 1,893.
* Note: Gu et al.'s 1,837-qubit BM decoder is *worse* under the Q² metric than these ≈890-qubit designs
  (nasir26 explicitly checked). Only ≈ 57 workspace qubits remain above the 840 floor, so future gains are Toffolis.

### F.3 dfthcsos
* Baseline (community reconstruction): R/B/C = 65/60/60 (3,900 + 76 = 3,976 addresses), b_rot = 12, J = 8 (K = 10),
  linear unary-iteration QROM with MBU; Q_tot = 730, T_tot = 93,237 (angle circuits ≈ 78–79 k ≈ 85 %; inner-prep
  temporary space 544 qubits ≈ 75 % of Q), Λ ≈ 308 (Λ_h2 ≈ 96 % of Λ), E_gap ≈ 3.9655 (1.3 % above floor),
  error₂ 18.64 mHa, error₁ 3.19 mHa, angle circuits 119 qubits. λ_eff ≈ √(2ΛE_gap) so **Λ is the lever**.
* Public best: **R8/B143/C60 factor, 8-bit angle words, 15 five-word lookups (J = 5), 16,366 Toffolis, λ_eff
  48.764**, cost ≈ 3.378e8 (≈ 9.93×; kirilltym "exact gauge" QROM, heliosli/Gluzdov circuit sets v33/v34, "Bro8
  tensor-lookup compiler"). Both error terms sit at 19.998 mHa, E_gap at its floor, Λ ≈ 304: "all gates bind".
* Closed/measured-null directions: GPU refit of 65/60/60 (λ_eff 49.0–50.9, no rounding room); nuclear-norm
  re-representation saves 4.2 %; copy pruning below C = 60 infeasible (ε₂ min 19.767 mHa); b_rot = 7 fails; naive
  11-bit re-rounding gives ε₁ = 221 mHa (rounding-aware 12-bit words work); Eckart–Young floor R·C ≥ 290 at 20 mHa;
  λ_eff ≥ 46.79 for any factorisation with the verifier's fixed (S, β₁); tree reordering, "chemistry QAT" and Λ
  regularisation measured null by one team; arXiv:2502.15882's own factorisation (λ_eff 43.65) fails the 20 mHa gate.
  A 10 % cut in λ_eff ≈ 3.2 % score; the remaining structural lever is *new angle circuits* exploiting structure in
  the 76 + R·B rows (structured/compressible angle tables, trimming "chemistry slots 0–3" ≈ 1 %).

---

## G. Techniques ranked by expected impact

Ranking combines (i) what the literature above demonstrates, (ii) the competition cost model, and (iii) what the
community has already banked (so that remaining headroom, not raw gain, drives the order).

### G.1 invsqrt (cost = Q × (Toffoli + T/4); community at ≈ 62 q / ≈ 1.4 k Toffoli-eq ≈ 20.6×; baseline 260 q / 7,988)

1. **Drop Newton entirely: dyadic piecewise-linear (or quadratic) table + shared local coordinate**
   (Gu et al. A.2 SI III.2; Sanders B.17; Häner B.7 for pricing). Select the interval from the leading mantissa bits
   and the parity of the exponent (no comparators, no Δx subtraction), fit integer coefficients to the *exact
   truncated integer arithmetic* over all 3.1 M inputs, size the table so a line (≤ 6–8 controlled additions)
   meets 2⁻²⁴·β/√x. Expected: this is what took the field from 7,988 to ~1,400 Toffoli-eq and 260 → 62 qubits.
2. **Measurement-based uncomputation everywhere** (Gidney B.10, B.11, Berry B.16): erase the coefficient lookup
   with ~2√L Toffolis instead of L; measure away every partial-product AND; mirror-uncompute only the parts that
   cannot be measured (half of the baseline's Toffolis were the mirror pass). Expected 1.5–2× on the arithmetic.
3. **Direct accumulation and register reuse** (A.2): never materialise y₀², z, p; accumulate the polynomial directly
   into the phase register / use a phase-gradient-style accumulation; reuse freed coefficient qubits as carries.
   This is the qubit lever (62 q ≈ 22 input + 40 phase/working).
4. **Phase register design**: phase directly from the table output bits (one Z_POW per bit, Clifford for the top
   bits), price only the ≤ 40 fine rotations (≈ 3 % of cost); consider Hamming-weight phasing (B.6) only if several
   equal-angle rotations appear.
5. **Normalisation cheaply**: binary (not unary) leading-zero-pair count (zjukop3: −29 qubits, −480 Toffolis);
   lane-wise cyclic CSWAP shifts n_p(n_p+1) = 110 CSWAPs (companion paper App. B) — or avoid the shift by folding
   the exponent into the table address (Gu et al.'s "few flag qubits record the scale 2^{−e/2}").
6. **Exploit the unused error budget** (baseline uses 48 % of tolerance; community circuits run at 99.9 %):
   truncate partial-product columns and coefficient widths with an end-to-end integer error model; but the
   verifier is exhaustive with zero failure budget, so every design must be validated over all 3,133,452 inputs
   offline (cheap classically).
7. Lower-impact / closed: windowed multipliers (B.11), Karatsuba (B.12), relative-phase Toffolis (E.3), seed-grinding
   (impossible), reducing rotation cost (saturated per community).

### G.2 dqi (cost = R(ε⁺)·Q²·T; floor Q = 840; community at ≈ 889 q / ≈ 4.4e5 T ≈ 60×; baseline 1,893 q / 5.73e6 T)

1. **Qubit count first — stay within ~50 qubits of the 840 syndrome floor** (metric: 1 % Q ≈ 2 % T). Every
   polynomial/evaluator/history register must live *inside* the syndrome words: in-place evaluator ω over the first
   35 syndrome words, workspace in the 35 words that become zero on a correct decode (A.2 SI I.1); Dialog-style
   "freed space absorbs the transcript" invariants (C.2); no separate 420-qubit ω/Ψ registers.
2. **Replace the synchronised EEA by Berlekamp–Massey with conditional routing** (A.2, C.1): ~140 k vs 1.9 M Toffolis
   for the locator; share one MADD path between retain/replace via CSWAP routing; σ₀δ = 1 invariant (no δ register);
   adaptive coefficient cutoffs from simulated DQI inputs; decode branch decisions from state instead of a stack.
3. **Phase-only error recovery** (A.2): compute Σ_j Tr(µ_j e_j) directly — cancel the mask at n + 1 positions with
   Clifford Z gates, precompute Ψ ≡ 1/σ′ (mod σ) with a half-degree EEA (char-2 even/odd split), then 23 Toffolis per
   scanned position (11-Toffoli zero test + 12 bilinear products): 93 k vs 1.3 M for Chien+Forney with 4,095
   Itoh–Tsujii inversions.
4. **Cheapest GF(2^12) quantum–quantum multiplier** (C.2 App. C, C.6, C.7, community F.2): baseline 63 → 51
   (Karatsuba/PCTOF rank) → **42 ANDs** (bilinear-rank / flip-graph search; apparently the floor for this field at
   rank 42); tower-field GF((2^6)²) representations for inversion; MBU of every out-of-place product
   (`GF2MulMBUC`); keep all quantum–classical multiplications, squarings, Frobenius maps and polynomial evaluations
   at fixed points as CNOT-only.
5. **Spend the failure budget deliberately** (A.2, companion paper): each tolerated failure costs ≈ +0.46 % (k = 1)
   to +5.3 % (k = 20) through R(ε⁺); drop stack entries/lanes/iterations only when the saved Q²T exceeds that
   (e.g. a one-entry discrepancy stack fails at 1e-4 — essentially free). Bound iteration counts (BM: 70 rounds
   fixed; EEA worst case 6n) and prune coefficient ranges per round.
6. **Record-and-replay / transcript compression** for whatever control flow remains (A.4, C.2 Dialog): record
   branch bits in the space freed by shrinking polynomials; replay on uncompute rather than holding full values
   (community confirms "replay beats hold").
7. Lower-impact: PCTOF rank optimisation beyond 42 (community found nothing), additive-FFT root finding (worse),
   Dicke-state/syndrome-generation stages (outside the benchmark), CNOT/depth optimisation (free in metric).

### G.3 dfthcsos (cost = λ_eff·T_tot·Q_tot; community ≈ 9.9×; baseline Q 730 / T 93 k / λ_eff ≈ 49.4)

1. **Factorisation that minimises C_BE·λ_eff under the 20 mHa gates** (D.1, D.7, D.13, D.10): optimise (u, w, W)
   by regularised gradient descent (Frobenius loss + ReLU penalties on Λ and E_gap) against the *shifted* tensor
   with the verifier's fixed (S, β₁); push R·B (angle-table rows) and C (coefficient copies) down to the Eckart–Young
   floor (R·C ≥ 290; community best R8/B143/C60 ≈ 1,220 rows vs 3,976) while keeping ε₁, ε₂ ≤ 20 mHa and Λ > 49,
   E_gap > 3.9149. Both λ_eff (floor ≈ 46.8) and the row count enter multiplicatively; the community says the gates
   all bind now, so remaining gains are in T_tot and Q_tot.
2. **Angle-oracle (QROM) compression** (B.15, B.17, D.18, B.11): the Angle_k circuits are ≈ 85 % of T_tot. Use
   variable-spaced/pruned QROM where words repeat (tree-induced zeros, equal angles from symmetric vectors), exploit
   the freedom to permute addresses and choose the Givens tree so adjacent addresses share words (XOR-difference
   loading between batches is already in the baseline), frame-block style grouping of related vectors; windowed /
   SelectSwap (QROAM) layouts within the 128-qubit cap; MBU unlookup (~2√L). Rounding-aware low-precision words
   (8-bit words pass; naive re-rounding does not).
3. **Batch size J and qubit accounting** (companion paper Sec. III C, D.1 Table III): Q_tot = persistent prep
   qubits + J·b_rot + max temporary workspace (Inner prep temporaries were 544 of 730 baseline qubits). Choose J and
   the angle-circuit workspace so the Angle_k temporary space never exceeds the Inner-prep temporary space (shared),
   and so J·b_rot persistent qubits are small (community: J = 5, 8-bit words).
4. **Givens tree choice** (D.15, companion App. A): the N − 1 = 75 rotations cost Σ(2b_t − 1) Toffolis and the tree
   fixes the angle statistics; a tree matched to the vectors' sparsity makes many angles 0/π/2 (free) and the table
   compressible. One team measured reordering as null on their factor — expect gains only jointly with (1)–(2).
5. **Rank/precision co-design**: b_rot = 8 verified by the community (7 fails); lower b_rot reduces both QROM width
   and Givens adder cost (2b_t − 1), but rounding must be absorbed into the fit (randomised rounding, D.1 App. D).
6. Out of scope / fixed: symmetry shift (ignored by verifier), Inner/Outer prep (heuristic black boxes — but their
   heuristic cost depends on (R, B, C), so they are indirectly optimised by (1)), Majorana select logic.

### G.4 Cross-cutting (search methodology)
* Keep the official verifier frozen as ground truth (A.6); fuzz with few shots during search, full shots before
  accepting (harshul notes; A.2 Methods: ε ≲ ln(1/δ)/k).
* Evolve *generator programs* with parameterised sweeps (bit widths, table sizes, J, ranks) plus LLM-proposed
  structural rewrites (A.2, A.7); keep per-candidate notes and a failure log.
* Score deltas to watch: invsqrt is linear in Q and C; dqi rewards Q twice; dfthcsos is dominated by angle QROMs
  × λ_eff, and the leaderboard geomean punishes neglecting any one task.

---

## H. Gaps and items not found
* No standalone "Wang et al. 2020 inverse square root" arXiv paper was identified (closest: Dutta et al. VLSID 2020;
  Wang et al.'s transcendental-function circuits); Kepley–Steinwandt (GF(2^n) multiplication) exists only as a
  journal paper and was not fetched.
* Kaggle discussion threads (public notebooks by busyaprime, kirilltym, yoyobar, Ozer, heliosli, Gluzdov,
  "SomeJoint") were not fetchable from this environment; their numbers above come from participant repos that
  re-scored them locally.
* The companion paper's hashed internal (Gemini) circuits are unpublished until the competition ends; the Gemini 4
  Argon arcsin/CORDIC result (A.8) has no public write-up beyond the launch blog.
* Kivlichan 2017's Newton-based 1/√x passage could not be located in the PDF text layer; its characterisation
  relies on Rubin et al.'s description.

