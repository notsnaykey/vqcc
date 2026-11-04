# Deep read: the papers behind the `dfthcsos` (FeMoCo) benchmark

Written 2026-11-04 from the arXiv LaTeX sources / PDFs (downloaded into the session scratchpad under
`papers/<arxivid>/src/`), the companion paper's Benchmark III section and Appendix A, and the official
`SCORING_README.md` mirrored in `docs/research/kaggle-raw/mirrors/`. The companion paper as a whole is covered in
`companion-paper.md`; this file goes deep on the cost model, the factorisation, lambda machinery and the circuit
structure. Everything tagged **[inference]** or **[derived]** is mine, not the papers'. Everything else is quoted or
paraphrased from the sources with the equation/table it comes from.

Notation used throughout: N = 76 spatial orbitals, eta = 113 electrons, (R, B, C) = DFTHC ranks, L = N + R·B = number of
QROM addresses (vectors), J = angle words per ANGLE circuit, K = ceil((N-1)/J) circuits, b_rot = `brot` = bits per
angle word, chi = keep-register bits of coherent alias sampling (fixed to 10 by the verifier).

---

## 0. TL;DR

* The benchmark is the **DFTHC-SOS + spectrum-amplification** block encoding of Low, King, Berry, Han, DePrince,
  White, Babbush, Somma, Rubin, *Fast quantum simulation of electronic structure by spectrum amplification*,
  PRX 15, 041016 (2025), arXiv:2502.15882 (DOI 10.1103/pb2g-j9cw). That paper defines every symbol in the score:
  the SOS generators, Lambda = (1/2) lambda_sqrt^2, E_SOS, E_gap, lambda_eff = sqrt(E_gap (2 Lambda - E_gap)), the
  BLISS set H_eta that "Hsym"/beta_1 parametrise, the (R,B,C) ansatz, the optimisation program, the bit-precision
  study and the full Toffoli/qubit cost tables (its Table "Outer PREP / Inner PREP / RPREP / SEL / REF" is the
  "Table 3" the competition's heuristic cost functions come from).
* `lambda_eff` is the first-order error-propagation constant of the qubitised walk whose eigenphases are
  arccos(E/Lambda - 1): PEA queries = pi·lambda_eff/(2 sigma_E). It is the Hamiltonian's cost-relevant norm after
  spectrum amplification, and it is quadratically more sensitive to E_gap than to Lambda:
  d lambda_eff/d E_gap = (Lambda - E_gap)/lambda_eff ~ 6.2 per Ha at the baseline versus
  d lambda_eff/d Lambda = E_gap/lambda_eff ~ 0.08 per Ha. **[derived]** That is why the verifier floors E_gap
  (> 3.914898 Ha) and Lambda (> 49.0 Ha); public submissions sit 1e-6 Ha above the E_gap floor, so in practice
  **lambda_eff ~ sqrt(2·3.9149·Lambda) ~ 2.8·sqrt(Lambda)** and Lambda is the only remaining lambda lever
  (Lambda 300 -> 48.3, 200 -> 39.3, 120 -> 30.3, 57.6 (the symmetry-sector lower bound of Cortes et al.) -> 20.8,
  49 -> 19.19). **[derived]**
* The score is lambda_eff x T_tot x Q_tot where the *only simulated* part is the family of ANGLE_k XOR oracles
  (forward + reverse, i.e. 2·K circuits per block-encoding query); OUTER/INNER state preparation and the N-1 Givens
  rotations are priced with heuristics (Givens: 2·(N-1)·(2 b_rot - 1) Toffolis). Baseline: (R,B,C) = (65,60,60),
  L = 3976, b_rot = 12, J = 8, K = 10 plain unary-iteration QROMs of 3974 Toffolis / 119 qubits each ->
  ANGLES 79,480 (85% of T_tot = 93,237), outer 846, inner 9,461, Givens 3,450; Q_tot = 730 = 90 (state prep) + 96
  (J·b_rot) + 544 (shared temp); Lambda = 308.456, E_gap = 3.9655, lambda_eff = 49.3014; score 3.3556e9.
* Levers, in order of expected impact (Section 3): (i) shrink L = N + R·B and b_rot under the two 20 mHa
  Frobenius gates (public frontier: (8,143,60), b_rot = 8, T = 16,266, Q = 430, ~9.9x); (ii) lower Lambda at the
  E_gap floor by re-optimising the factorisation with the *fixed* baseline shift (S0, beta_1) and exploiting the
  identity offsets W^(rho c) (Lambda 300 -> 200 would be a further 1.23x); (iii) cheaper ANGLE oracles inside the
  128-qubit cap (select-swap with k = 2..4, address ordering, half-priced measurement-conditioned Toffolis);
  (iv) choose (R,B,C) jointly with the INNER heuristic (RC and B+1 terms) and the shared temporary workspace;
  (v) tree shape and angle gauge to make b_rot = 7..8 pass the 20 mHa gates.

---

## 1. The benchmark contract (companion paper arXiv:2610.23832, Sec. III.C + App. A; SCORING_README)

### 1.1 Hamiltonian, symmetry shift and the DFTHC form

Spin-free Hamiltonian (Eq. `chem_ham`): H = sum_pq h1_pq E_pq + 1/2 sum_pqrs h2_pqrs E_pq E_rs,
E_pq = sum_sigma a^dag_{p sigma} a_{q sigma}. The verifier reads h1, h2 from `FeMoCo76o113e.fcidump` (SHA-256
e5a48af7...), and stores the two-electron integrals as **float32** (the README says this is deliberate).

Symmetry-shifted (spectrally equivalent in the eta-particle sector) family, Eq. after `chem_ham`:

```
H = sum_pq (h1_pq - (eta/2) S_pq + beta_1 delta_pq) E_pq
  + 1/2 sum_pqrs (h2_pqrs + 1/2 (S (x) I + I (x) S)_pqrs) E_pq E_rs  - eta beta_1 I
```

for a real symmetric S and scalar beta_1. **This is exactly the BLISS set H_eta of Low et al. Eq. (DFTHC_program
context)**: h2 -> h2 + (h_sym (x) I + I (x) h_sym)/2, h1 -> h1 - (eta/2) h_sym + beta_1 I, h0 -> h0 - eta beta_1,
with h_sym = S. In BLISS language (Loaiza-Izmaylov) the added operator is (1/2) S_op (N_hat - eta) + beta_1 (N_hat - eta),
i.e. the xi-term and the kappa_1 term; a multiple of the identity inside S reproduces the kappa_2 N_hat^2 term.
**[derived]** In the competition S = S0 and beta_1 = beta_{1,0} are **fixed to the provided baseline**
(`FeMoCo76o113e.fixed_shifts.npz`); the submitted `H1_I` and `Hsym_lower` are ignored. `Hsym_lower` has shape
(2926,) = 76·77/2 = the lower triangle of S; `H1_I` is a scalar (beta_1). **[inference from shapes]**

DFTHC ansatz (Eq. `dfthc-hamiltonian`), the fixed "tensor network" of Low et al.:

```
u_b^(rho) in R^N, ||u_b^(rho)||_2 = 1            rho in [R], b in [B]      (U array: (R, B, 76))
w_b^(rho c) in R, W^(rho c) in R                 c in [C]                  (W array: (R, B, C); H2_I array: (R, C) = W)
X^(rho c)_pq = sum_b w_b^(rho c) u^(rho)_{b,p} u^(rho)_{b,q}
h2~_pqrs    = sum_{rho,c} X^(rho c)_pq X^(rho c)_rs
H_DFTHC = sum_pq h1'_pq E_pq + 1/2 sum_{rho c} ( W^(rho c) I + sum_pq X^(rho c)_pq E_pq )^2
          - ( eta beta_1 + 1/2 sum_{rho c} |W^(rho c)|^2 ) I
h1'_pq  = h1_pq - (eta/2) S_pq + beta_1 delta_pq - sum_{rho c} W^(rho c) X^(rho c)_pq      (exact one-body absorption)
```

So the one-body part is represented exactly for any Theta; only h2 is approximated, with
eps_fro = || h2 - h2~ + 1/2 (S (x) I + I (x) S) ||_F. Note the sign convention: the shifted target is h2 + T(S0) with
T(S0) = (S0 (x) I + I (x) S0)/2, and the verifier's `error_2 = || sum X (x) X - h2 - T(S0) ||_F <= 0.020 Ha`.

`DF` is the special case B = N, w_B = 0, C = 1 with orthonormal u's; `THC` is (R,B,C) = (1, R_THC, R_THC)
(Low et al. after Eq. DFTHC_representation). The B vectors are shared by the C "copies" of a rank component, which is
why only N + R·B vectors (addresses) are loaded while N + R·C·(B+1) coefficients exist.

### 1.2 Lambda, E_SOS, E_gap, lambda_eff (Eqs. `dfthc-normalization`, `effective-normalization`, `lambda-main`)

```
w_B^(rho c) = W^(rho c) + sum_b w_b^(rho c)
Lambda      = ||h1'||_*  +  1/4 sum_{rho c} ( |w_B^(rho c)| + sum_b |w_b^(rho c)| )^2       (||.||_* = Schatten-1)
E_SOS       = -eta beta_1 - ( ||h1'||_* - Tr h1' ) - 1/2 sum_{rho c} |W^(rho c)|^2
            = -eta beta_1 - 2 sum_j w_{-,j} - 1/2 sum |W|^2    (w_{-,j} = |negative eigenvalues of h1'|)
E_gap       = E_gs - E_SOS,   0 <= E_gap <= 2 Lambda           (paper);
E_gap       = E_upper - E_SOS, E_upper = -22140.27335 Ha fixed  (verifier)
lambda_eff  = Lambda·sqrt(delta(2-delta)), delta = E_gap/Lambda  = sqrt( E_gap (2 Lambda - E_gap) )
```

Where these come from (Low et al. Sec. II-III, App. "DFTHC block-encoding cost"): the SOS generators are

```
O_{D1^sigma,j} = sqrt(w_{+,j}) (gamma_{u+_j sigma 0} + i gamma_{u+_j sigma 1})/2        (positive eigenpairs of h1')
O_{Q1^sigma,j} = sqrt(w_{-,j}) (gamma_{u-_j sigma 0} - i gamma_{u-_j sigma 1})/2        (negative eigenpairs)
O_{SF,rc}      = (1/sqrt2) ( w_B^(rc) I + (i/2) sum_{b,sigma} w_b^(rc) gamma_{u_b^(r) sigma 0} gamma_{u_b^(r) sigma 1} )
H_DFTHC - E_SOS I = sum_{j,sigma} (O_D1^dag O_D1 + O_Q1^dag O_Q1) + sum_{rc} O_SF^dag O_SF
lambda_{D1,j} = sqrt(w_+j), lambda_{Q1,j} = sqrt(w_-j), lambda_{SF,rc} = (1/sqrt2)(|w_B| + sum_b |w_b|)
lambda_sqrt^2 = sum_alpha lambda_alpha^2,   Lambda = (1/2) lambda_sqrt^2
```

(gamma_{u sigma x} = sum_p u_p gamma_{p sigma x} is a rotated Majorana; the sum over both spins gives the factor 2 that
cancels the 1/2 in Lambda for the one-body part). E_SOS is optimal for the one-body part (it is the normal-ordering
shift of Eq. H1normalorder) but not for the two-body part, where the identity offsets W are free parameters.

**Derivation of lambda_eff [derived, consistent with Low et al. Eq. lambda_eff]**: the rectangular block encoding
U = SEL·PREP of H_sqrt/lambda_sqrt is turned into a walk W = Ref·U^dag·Ref·U with eigenphases
phi = arccos(E_k/Lambda - 1), Lambda = lambda_sqrt^2/2 (Eq. two_walk_phases). Phase estimation to phase precision
sigma_phi costs pi/(2 sigma_phi) queries; dphi/dE = -1/sqrt(E(2Lambda - E)), so sigma_E = sigma_phi·sqrt(E_gap(2Lambda-E_gap))
and queries = pi·lambda_eff/(2 sigma_E). Because the walk encodes H_SA/Lambda - 1 (one qubitisation step, Eq. after
two_walk_phases), the ground state sits at E_gap above the bottom of the walk's window; the amplification is the
divergent derivative of arccos(x-1) at x -> 0 (King et al. Fig. 1). Low et al. App. "Correction for divergent
derivative" checks that the first-order formula is accurate for their parameters.

Sensitivities at the baseline (Lambda = 308.456, E_gap = 3.9655, lambda_eff = 49.30) **[derived]**:
d lambda_eff/dE_gap = 6.18 /Ha, d lambda_eff/dLambda = 0.0804 /Ha; 1 Ha of E_gap is worth ~77 Ha of Lambda.
At the floor E_gap = 3.914898 the same Lambda gives 48.99; lambda_eff at the (Lambda, E_gap) floor pair is 19.192
(README). The public-frontier lambda_eff 48.29 corresponds to Lambda ~ 299.8 at the floor. **[derived]**

### 1.3 What the npz arrays mean and how the verifier uses them

| array | shape | used? | meaning |
|---|---|---|---|
| `U` | (R, B, 76) | only its **shape** (R, B) | the unit vectors u_b^(rho); the verifier *re-decodes* them from the circuits' angle words |
| `W` | (R, B, C) | yes | w_b^(rho c) |
| `H2_I` | (R, C) | yes | W^(rho c), the identity offsets |
| `H1_I` | () | ignored | beta_1 (baseline's is used) |
| `Hsym_lower` | (2926,) | ignored | lower triangle of S (baseline's is used) |
| `tree_edges` | (75, 2) int | yes | the Givens tree: (parent, child) pairs in parent-before-child order, rooted at 0 |

Verifier pipeline (README "Steps", paper Sec. III.C.5): check register contract -> simulate every address a < L with 64
shots forward and in reverse through ANGLE_0..ANGLE_{K-1} -> recover the (L, 75) integer word table
(word in [0, 2^brot), theta = pi·word/2^(brot-1), i.e. theta/pi in [0,2) with one integer bit) -> decode each row on the
tree -> rows 0..75 are the one-body eigenvectors, rows 76.. are u_b^(rho) in (rho, b) order -> rebuild X^(rho c) and h1' ->
`error_1`: eigendecompose h1', match the decoded one-body vectors to its eigenvectors, rebuild h1~' with the exact
eigenvalues and quantised vectors, undo the shift (h1~ = h1~' + (eta/2) S - beta_1 I + sum W X~) and require
||h1~ - h1||_F <= 0.020 Ha; `error_2` as above <= 0.020 Ha -> Lambda, E_SOS, E_gap, lambda_eff from the quantised vectors
-> cost -> score. Failed checks give infinite score; floors are strict and values are not clamped.

Tree decode (Eq. `tree-coefficient-recursion` / README): v = e_0; for t, (p, c) in enumerate(tree_edges):
(v_p, v_c) <- (cos th_t v_p - sin th_t v_c, sin th_t v_p + cos th_t v_c). Because children are untouched before their
parent edge, this is u_c <- u_p sin th, u_p <- u_p cos th (Eq. tree_simplified_update): the coefficient at vertex v is
A_v·prod_{children} cos, where A_v arrives through the chain of sines/cosines from the root
(Eq. tree_child_product). The path tree 0->1->...->75 is von Burg's sequential chain
u_p = cos(2 theta_p) prod_{j<p} sin(2 theta_j) (their Lemma, with their theta = half-angle convention).
The tree shape does **not** change the Givens Toffoli heuristic (always N-1 rotations) — it changes the angle values,
their quantisation-error propagation (depth-many multiplications vs log-depth) and the structure of the word table.
**[inference]** "Givens tree" has no hits on arXiv; it is competition-specific terminology, generalising the
chain of von Burg Lemma "Sum of Majorana operators by Majorana rotations".

### 1.4 What the ANGLE circuits must do (Eq. `angle`, README "What a submission must do")

Split the 75 words of every row into K = ceil(75/J) batches of J words (zero padded). Circuit k is the reversible XOR
oracle ANGLE_k: |a>|z> -> |a>|z XOR delta[k,a]> with delta[0,a] = batch[0,a], delta[k,a] = batch[k,a] XOR batch[k-1,a]
(the batch label is hard-wired, no coherent k register). Streaming the family forward on z = 0 produces the batches of
row a in turn; the reverse traversal clears them — "eliminating a separate inter-batch uncomputation". This is exactly
von Burg's *programmable rotation gate array* (SI Sec. "New quantum circuit primitives"): with kappa data qubits you
need ceil(Mb/kappa)+1 lookups and "the middle pair of data-lookup oracles ... can be merged into one that writes the
bits theta_{k,[j kappa..]} XOR theta_{k,[(j+1)kappa..]}". Register contract: `selection` = exactly ceil(log2(76 + RB))
qubits; `word_0..word_{J-1}` of `brot` qubits each (this is how b_rot is declared); all other qubits are workspace that
starts and ends in |0>; no Z_POW (every phase a multiple of pi); the phase check only distinguishes a half turn.

**[inference]** Because the same gate list is run in both directions and must map batch_{k-1} -> batch_k *and*
batch_k -> batch_{k-1}, the circuit has to be a genuine XOR-of-a-function oracle: the cheap Berry-et-al.
measurement-based *unlookup* (X-measure the data, phase-fix with a lookup of size ~L/k + k) cannot replace it, because
"reset-and-write batch_k" would give batch_k in the reverse pass instead of batch_{k-1}. Measurement-based
uncomputation is still usable for *internal* ancillae (unary-iteration ladder, select-swap temporaries), and the
verifier counts a Toffoli conditioned on a measured bit only on the shots where the bit is set (mean over shots).

### 1.5 Score and Toffoli accounting of the whole block encoding

```
score   = lambda_eff * T_total * Q_total                                   (lower is better)
T_total = ANGLES Toffolis (simulated, forward U_T and reverse U_T^dag; mean over shots)
        + outer_state_prep() + inner_state_prep()        heuristic SpinFreeData_V1 (incl. inverses)
        + 2 * (N - 1) * (2 * brot - 1)                   heuristic Givens rotations (U_T and U_T^dag)
Q_total = outer_persistent + inner_persistent            (90 for the baseline shape)
        + J * brot                                       persistent angle-word registers
        + max(outer_temp, inner_temp, angles_temp)       shared temporary workspace (sequential subroutines)
```

Paper Eq. `cost-accounting`: C_BE = nu_out C_out + nu_in C_in + sum_k nu_ang,k C_ang,k(J) + C_fixed(T, N, J, b_rot),
with every ANGLE_k called once per direction, so the angle contribution is 2·C_ang^pass(J). The pipeline
(Eq. `pipeline`) is OUTER -> [decode -> INNER -> spin select] -> {ANGLE_k -> Givens batch k}_k -> Majorana select ->
{inverse Givens batch k -> ANGLE_k}_{k reversed} -> [INNER^dag -> reflect and square] -> OUTER^dag. Note the score
prices **one** such pass (one generator O_x applied, not the full T_2 = reflect-and-repeat walk step of Low et al.,
which would double the inner part); the reflection costs are omitted. The Givens heuristic "each of the N-1 rotations
is a b_t-bit controlled adder costing 2 b_t - 1 Toffolis" (App. A.1) is the fused-adder Givens of Caesura et al.
(Sec. "Givens rotations"), cheaper than Lee et al.'s two separate adders (2 b_rot per edge in Low et al. Table
"rotation_qrom": 2(N-1)b_rot for forward+reverse). ANGLE_k circuits are capped at 128 qubits; Q_total is not capped.

Baseline numbers (README "Worked example"): L = 3976 addresses, selection 12 qubits, 10 circuits of 119 qubits and
3974 Toffolis each (= L - 2, a plain unary-iteration QROM over all addresses, matching kickmix's `init_lookup`),
ANGLES = 79,480; outer 846, inner 9,461, Givens 3,450; T_total 93,237; Q_total 730 = 186 persistent (90 + 96) + 544 temp.
At brot = 16: 846 + 9461 + 4650 and 1,087 temp qubits. 12-bit words give lambda_eff = 49.301369 (unrounded 49.254686).

**Check of the heuristic against Low et al.'s tables [derived]**: Outer PREP for N + RC = 3976 (12 bits), chi = 10:
uniform 4·12 = 48 (x2 for inverse) + alias sampling ceil(3976/2^k1) + 2^k1·b1 with b1 = 12 + 10 = 22, k1 = 4:
249 + 352 = 601 + inverse b1 + ceil(3976/2^k5) + 2^k5 with k5 = 6: 22 + 63 + 64 = 149 -> **846 exactly**. So
`SpinFreeData_V1` = Low et al. Table "outer_prepare_costs" with b_k1 = chi = 10 and k's optimised. I could not
reproduce the inner 9,461 from Table "b_weight_prep_via_unary_qrom" with the obvious choices (2 calls of
RC·ceil((B+1)/2^k2) + 2^k2 b2, b2 = 6 + 10 = 16, give >= 9,848 before inverses), so the inner model has its own
k-choices/sharing — read `scoreinfra/costs_prepare.py` before optimising (R,B,C). The 544 shared-temp figure is also
not the naive (2^k2 - 1) b2; it moves with b_rot (544 -> 1,087 for 12 -> 16 bits), so the model probably lets the inner
QROAM borrow angle-register space the way Low et al. do (their footnote: 313 temp qubits of inner PREP reuse the 795
persistent rotation qubits). **[inference]**

---

## 2. Paper-by-paper deep reads

### 2.1 Low, King, Berry, Han, DePrince III, White, Babbush, Somma, Rubin — *Fast quantum simulation of electronic structure by spectrum amplification*, PRX 15, 041016 (2025); arXiv:2502.15882 (the source of everything above)

**Contribution.** (1) Practical circuits for spectrum amplification (SA) of a Hamiltonian in sum-of-squares (SOS) form
H = sum_alpha O_alpha^dag O_alpha + E_SOS, via a *rectangular* block encoding of H_sqrt = sum_alpha |chi_alpha> (x) O_alpha
(cheaper than Hermitian dilations) and a walk whose two steps restore standard PEA; (2) the spin-free level-2 SOS
algebra {I, a, a^dag, sum_sigma a^dag_i a_j} whose SDP (cuLoRADS) gives E_SOS lower bounds with gaps of a few Ha;
(3) the DFTHC ansatz that spans that algebra, is optimised directly for Lambda and E_gap by Adam/JAX, and balances the
two dominant lookup oracles. Headline: FeMoCo-76 (Li) 1459 qubits, 9.99e8 Toffolis, a 4.3x improvement over
BLISS-THC (Caesura et al.) and 37x over DF; FeMoCo-54 (Reiher) 1137 qubits, 3.41e8 Toffolis.

**Key definitions** (Sec. II): block encoding Be[O/lambda]; SEL = sum |alpha><alpha| (x) Be[O_alpha/lambda_alpha],
PREP|0> = (1/lambda_sqrt) sum lambda_alpha |alpha>|garb_alpha>, lambda_sqrt^2 = sum lambda_alpha^2; U = SEL·PREP =
Be[H_sqrt/lambda_sqrt]; W = Ref_aBe U^dag Ref_Be U has spectrum exp(+-i arccos(E_k/Lambda - 1)), Lambda = lambda_sqrt^2/2;
U^dag Ref U = Be[H_SA/Lambda - 1] which is the LCU of T_2 Chebyshev polynomials of the O_alpha (Fig. "single step
qubitization") — the generalisation of the oblivious-amplitude-amplification factor-of-2 trick of von Burg et al.
Queries = pi·lambda_eff/(2 sigma_{E_gap}), lambda_eff = sqrt(E_gap(2Lambda - E_gap)) (Eq. lambda_eff).

**SOS / SDP** (Sec. III): max E_SOS s.t. H - E_SOS = o^dag G o, G >= 0 over the generator vector o; dual of the
pseudomoment (2-RDM, DQG) lower-bound program. Variational table (Table var_energies, no core energy):
FeMoCo[113e,76o] DMRG M=6000 upper -1119.05933 Ha, SDP lower -1123.300, E_gap* = 4.240 Ha, lambda_eff lower bound
21.691 Ha (= sqrt(E_gap(Delta_mu - E_gap)) with the Cortes et al. S = 3/2 sector bound Delta_mu/2 = 57.6 Ha);
FeMoCo[54e,54o]: gap 3.464, bound 16.025. **[inference]** The competition's E_upper = -22140.27335 Ha minus
-1119.05933 Ha = -21021.21402 Ha is the frozen-core/nuclear constant ("core-inclusive"); E_gap is unaffected only if
E_SOS is computed with the same constant, which the verifier's E_SOS formula (no core term) implies is folded into
E_upper. The floor 3.914898 Ha is below the SDP-optimal gap 4.240 (different S0, beta_1 and float32 integrals), i.e.
the floor is close to the best achievable gap for this algebra; do not expect to beat it.

**DFTHC optimisation program** (Eq. DFTHC_program):
argmin over u, w, (h2_S, h1_S, h0_S) in H_eta of ||h2_S - h2'||_F/eps_reg + Lambda/lambda_reg + Relu((E_gap - E_reg)/E_reg),
with E_gap computed through Eq. Egap_corrected (E_gap = E_gs + ||h1'||_1 - Tr h1 - 1/2 sum_pq h2'_ppqq + 1/2 sum |w_B|^2,
using the exact h2 in the trace replacement). Random initial conditions suffice (u random unit, w, h_sym ~ N(0.01),
beta_1 ~ N(0.05)); FeMoCo-76 hyperparameters: lambda_reg 100 mHa, eps_reg 10 mHa, E_reg in [4,8] Ha, 4.4 ms/step on
an L4 GPU, 1e5-1e6 Adam steps, cost dominated by the O(RCN^4) contraction. Heuristic for (R,B,C): C = Theta(N)
(Amdahl: Rot and Qroam comparable), B = Theta(N), R = O~(1); scan B in {N, 3N/4, N/4}, C in {N/2, N/4}, R.

**Selection and error budget** (Sec. IV.B, App. Robust selection, App. bits of precision): chemical accuracy
1.6 mHa split as sigma_PEA = 1.0 mHa + |eps_corr| <= 0.6 mHa (threshold 0.3 mHa on the high-spin CCSD(T) correlation
energy change, S_z = 35/2 for FeMoCo-76), or statistically sigma_E <= sqrt(sigma_PEA^2 + sigma_corr^2 + sigma_trunc^2)
with sigma_PEA = 1.4, sigma_corr <= 0.7, sigma_trunc <= 0.331 mHa using *randomised rounding* of angles (first
b_rot - 1 bits floor, last bit Bernoulli; expected vector error O(N 4^-b_rot) instead of O(N 2^-b_rot)) and of
alias-sampling bins, rounded once per PEA run. Chemical precision needs b_rot in [11,18], b_coeff in [6,14]; FeMoCo-76
used (b_coeff, b_rot) = (9,15) (linear budget) or (11,16) (statistical). The one-body term can be made effectively
exact at +N addresses by block-encoding the residual h1'' (Sec. bits_of_precision). Table ccsd_t_dmrg shows CCSD(T)
and DMRG correlation-error metrics disagree by 10x, so Frobenius-type gates (as used by the competition) are a
different, coefficient-level criterion — the README itself says the checks "do not certify a 20 mHa many-electron
energy error".

**FeMoCo numbers** (Table dfthcblisssossa_costs and scans): FeMoCo-76 best (R,B,C) = (15,57,19): eps_corr 0.136 mHa,
eps_fro = 0.0825 Ha (!), Lambda 179.73, E_gap 5.382, lambda_eff 43.65, C_BE 14,563 Toffolis, 1459 qubits, total
9.99e8. Robust (15,64,32): eps_fro 48.9 mHa, (11,16) bits, E_gap 6.198, lambda_eff 50.72, C_walk 17,588, 1560 qubits.
Scan (Table compare_rbc_table_1, FeMoCo-76, |eps_corr| <= 0.3 mHa, (9,15) bits): DF-like (130,76,1): Lambda 140.6,
E_gap 6.149, lambda_eff 41.13, Rot 39,520 + Coeff 1,970 + Select 9,000 = 50,490; (15,57,19): 179.7/5.037/42.25,
3,420 + 2,476 + 9,000 = 14,896; THC-like (1,220,220): 144.7/5.335/38.93, 880 + 4,484 + 9,000 = 14,364 (the
Toffoli-optimal column). Note the competition's eps_fro gate (20 mHa) is 2-4x *tighter* than these solutions, which
is why the baseline (65,60,60) and the public (8,143,60) have far more addresses than (15,57,19) (RB = 855).
Prior art in the same table: DF FeMoCo-76 lambda 584.54 / C_BE 40,442 / 6404 qubits; BLISS-THC 198.9 / 13,763 / 1512.

**Block-encoding circuit** (Fig. fullcircuit, App. B): prep over x_o in [N + RC] (outer; amplitudes lambda_SF,rc,
2 lambda_D1, 2 lambda_Q1, Eq. target_prep_state, coherent alias sampling with QROAM); equal superposition on b with
success flag; unary iteration over x_o combined with QROAM on b outputs alt/keep for b *and* (G, r, c) for free;
two spin qubits (one inside the inner sum for SF, one in the outer sum for D1/Q1) control swaps of the spin-up/down
system halves (4N Toffolis total, Clifford Z-strings for JW); **Rot = QROM on (r, b) (and on x_o for the N one-body
vectors) outputs the N-1 angles, b = B flips the identity flag**; the Givens network rotates gamma_{0 sigma x} to
gamma_{u sigma x} on one spin half; the Majorana operator then acts on a *single* qubit (Z for SF, X or Y for D1/Q1
with the sign qubit, 7 Toffolis incl. success controls, Fig. Majorana); inverse rotations and inverse lookups;
reflect on (b, keep, rotated, inner-spin) qubits (cost ceil(log(B+1)) + b_k2 + 1) and repeat for the square; outer
unprep; walk reflection ceil(log(N+RC)) + ceil(log(B+1)) + b_k1 + b_k2 + 2.

Cost tables (per call; "Calls" = per walk step):
* Outer: Uniform 4ceil(log(N+RC)); Alias ceil((N+RC)/2^k1) + 2^k1 b1, b1 = ceil(log(N+RC)) + b_k1; inverse b1 + ceil((N+RC)/2^k5) + 2^k5; persistent ceil(log(N+RC)) + 2 + b1 + b_k1; temp 2^k1 b1 + ceil(log((N+RC)/2^k1)).
* Inner (x2): Uniform 4ceil(log(B+1)); AliasSampling(b) RC ceil((B+1)/2^k2) + 2^k2 b2, b2 = ceil(log(B+1)) + b_k2
  (alternative RC + (B+1) b2 when all b are output at once); inverse b2 + N + ceil(RC/2^k4) + 2^k4 (B+1);
  persistent b2 + b_k2 + ceil(log R) + ceil(log C) + 2; temp ceil(log(RC ceil((B+1)/2^k2))) + (2^k2 - 1) b2.
* RPREP (x2): QROM(u) N + RB Toffolis (unary iteration, "no advantage to QROAM since the output set of rotations is
  quite large"), persistent (N-1) b_rot, temp max(ceil log(N+RC), ceil log(RB)); erase R + B (binary-to-unary on one
  register, unary iteration on the other).
* SEL (x2): ROT 4 b_rot (N-1) [= 2 x 2(N-1) b_rot forward+reverse rotations by phase-gradient additions], CSWAP 2N,
  Majorana control 7.
* FeMoCo-54 (10,27,27), b_rot = 15, b_coeff = b_k = 15: Outer 310 / Inner 1154 / RPREP 361 / SEL 3295 / REF 67 ->
  9,997 Toffolis per walk step; 913 + 108 system = 1021 persistent, 1131 total qubits.
* Rot ~ N + RB per computation, Qroam ~ RBC/(lambda+1) + lambda b_Q with lambda <= (N-1) b_rot/b_Q (idle angle
  qubits used as QROAM workspace), Sel ~ 4(N-1) b_rot per application; Sel is ~60% of the cost, Rot + Qroam + Sel ~ 90%.

Mapping to the competition: OUTER = Outer PREP rows; INNER = Inner PREP rows; the ANGLE family = RPREP's QROM(u)
split into K batches (the paper loads all (N-1) b_rot bits at once, J = N-1, 795 persistent qubits for FeMoCo-54 — the
competition's J·b_rot persistent registers are the streamed version); Givens = the ROT line with the fused-adder
price. Only the ANGLE part is simulated; everything else is formula. The 128-qubit cap on each ANGLE circuit "keeps
the interesting part of optimizing INNER dominant" and corresponds to "200k physical qubits and < 1 day".

### 2.2 King, Low, Babbush, Somma, Rubin — *Quantum simulation with sum-of-squares spectral amplification*, arXiv:2505.01528

General SOSSA framework behind "DFTHC SOSSA": H + beta·1 = sum_j B_j^dag B_j, H_SOSSA = sum_j |j> (x) B_j block-encoded
with normalisation sqrt(lambda_SOS); query complexities go from Theta(lambda/eps) to Theta(sqrt(Delta·lambda)/eps) for
energy and phase estimation (Table 1), with matching lower bounds (query-optimal in the low-energy setting) and
adaptive versions that need no prior Delta. SOS optimisation: min beta s.t. H + beta = sum B_j(b_j)^dag B_j(b_j) over a
chosen SOS algebra (degree-k Pauli or fermionic monomials), an SDP; larger algebras tighten beta but raise
lambda_SOS and block-encoding cost (SYK example: degree-2 Majorana SOS gives sqrt(Delta lambda) ~ N^{3/2} vs N^2 for LCU;
degree-3 recovers N^2). App. "Double factorization" gives the DF-SOS normalisation
lambda_SOS = sum_j (|e_j| + ||f_j||_1 + ||g~^(R)_j||_1 + ||g~^(I)_j||_1)^2 after Gaussian rotations — the same square-of-1-norm
structure as Lambda_2 above. Useful mainly as the conceptual justification; no new FeMoCo numbers.

### 2.3 Companion paper, arXiv:2610.23832, Sec. III.C and App. A — items not already in `companion-paper.md`

* The user's freedom is exactly {(R,B,C), u, w, W, b_rot, J, tree, ANGLE circuits}; (S, beta_1) fixed; OUTER/INNER
  black boxes "because there are too many possible implementations, and most of them would be difficult to verify".
* Paper's boxed objective: min lambda_eff s.t. eps_fro < 20 mHa, ||u|| = 1; implementation-aware outer objective
  C_BE(R,B,C)·lambda_eff. The verifier instead scores lambda_eff·T·Q with T, Q as in 1.5.
* App. A.2 "Sum-of-squares generators" and A.3 "Registers, address maps, select bits": the outer address
  x_o(G, r, c) = r (D1, r < N_+), N_+ + r (Q1), N + rC + c (SF); the vector address mu in [N + RB] labels the N
  one-body eigenvectors and the RB u's (this is the ANGLE `selection` value a); b = B selects the identity coefficient.
* App. A.1: fermion-to-qubit mapping only changes the fixed Clifford conjugations of each edge rotation, so the
  tree and TreeCoeff are mapping-independent.
* Verification statistics: 64 shots per address; a missed HMR phase correction on a |1> qubit is caught with
  probability 1 - 2^-64 per address; the README stresses this is per-fault, per-address evidence, not a proof.

### 2.4 von Burg, Low, Häner, Steiger, Reiher, Roetteler, Troyer — *Quantum computing enhanced computational catalysis*, Phys. Rev. Research 3, 033055 (2021); arXiv:2007.14460

**Contribution.** Qubitisation of the double-factorised (DF) Hamiltonian; introduces the Majorana-rotation
("basis-transformed Majorana") implementation of one-body squares, programmable rotation arrays fed by QROM, and
Toffoli/qubit formulas; Ru CO2-fixation catalyst resource estimates; FeMoCo-54 estimate 3600 qubits / 2.3e10 Toffolis
(as re-tabulated by Low et al.; Lee et al. re-cost it at 3725 / 1.0e10 with a tighter truncation criterion and
corrected circuit).

**Definitions.** H_CD = sum h~_ij a^dag a + 1/2 sum_r (sum_ij L^(r)_ij a^dag_i a_j)^2, h~ = h - 1/2 sum_l h_illj
(Eq. HamiltonianFactorized); DF: L^(r) = sum_m lambda^(r)_m R_m R_m^T, M = sum_r M^(r) eigenvectors. In Majoranas
(gamma_p0 = a + a^dag, gamma_p1 = -i(a - a^dag)), H_DF -> const + Q_{L^(-1)} + 1/2 sum_r Q_{L^(r)}^2 with
Q_L = (i/2) sum_ij sum_sigma L_ij gamma_i sigma 0 gamma_j sigma 1 and L^(-1) = h - 1/2 sum_l h_illj + sum_l h_llij
(Eq. Ham_df_Majorana). **alpha_DF = ||L^(-1)||_SH + 1/4 sum_r ||L^(r)||_SH^2** (Schatten-1 norms; the competition's
Lambda_2 = 1/4 sum (|w_B| + sum|w_b|)^2 is this with the extra identity offset and without orthonormality of the u's).
Inequality (1/N)||h||_EW <= ||h||_SH <= ||h||_EW (proved in SI) explains why DF beats single factorisation.

**Circuit.** Lemma "Sum of Majorana operators by Majorana rotations": U_u = V^(0)...V^(N-2), V^(p) = exp(theta_p
gamma_p gamma_{p+1}) gives U^dag gamma_0 U = sum_p u_p gamma_p with u_0 = cos 2theta_0, u_p = cos(2theta_p) prod_{j<p}
sin(2theta_j) — the chain Givens tree. Each V^(p) is a Z-rotation conjugated by a fixed Clifford (JW:
gamma_p0 gamma_{p+1,0} -> -i Y_p X_{p+1}, gamma_p1 gamma_{p+1,1} -> i X_p Y_{p+1}); the x = 0 and x = 1 rotations commute
and are applied together, so the basis change for gamma_{u sigma 0} gamma_{u sigma 1} is 2(N-1) Z-rotations per
direction. Multiplexed rotations: data-lookup D_p|k>|z> = |k>|z XOR theta~_{R_k,p}> of beta-bit angles, then beta
controlled rotations by powers of 2 implemented with the phase-gradient trick at **one Toffoli per R_b**, giving
4N beta Toffolis for the rotations of a two-body square and the famous c_W <= 2M/(1+lambda) + 2 lambda N beta + 8N beta + 4N
with N beta (1+lambda) + 2N qubits, beta = ceil(5.652 + log2(N/Delta_W)) (Eqs. Toffoli_cost, Qubit_cost; lambda is
the select-swap parameter, sqrt(M/(N beta)) optimal). Error budget: Delta_W <= 0.1 Delta_E/alpha with
beta = ceil(1/2 + log2(4N pi/eps)) from a triangle inequality over 4N rotations each off by <= pi 2^-beta.
"Programmable rotation gate array" (SI "New quantum circuit primitives"): with kappa data qubits, ceil(Mb/kappa) + 1
lookups suffice because consecutive slices are written as XOR differences — the direct ancestor of ANGLE_k's
delta[k] = batch[k] XOR batch[k-1]. Truncation: coherent (sum of ||H_j|| <= eps_co) vs incoherent
(sqrt(sum ||H_j||^2) <= eps_in) schemes, with ||H_DF - H~_DF|| <= ||L^(r)||_SH |lambda^(r)_m| per dropped eigenvalue;
the incoherent scheme matches DMRG errors better but still overestimates.

### 2.5 Lee, Berry, Gidney, Huggins, McClean, Wiebe, Babbush — *Even more efficient quantum computations of chemistry through tensor hypercontraction*, PRX Quantum 2, 030305 (2021); arXiv:2011.03494

**Contribution.** Qubitisation of the non-orthogonal THC Hamiltonian with O~(N) Toffolis per step; careful
re-costing of sparse, single-factorised and DF algorithms; FeMoCo resource estimates for both active spaces; surface
code layout (~4M physical qubits, < 4 days for Reiher FeMoCo).

**THC.** V_pqrs ~ sum_{mu nu} chi_p^mu chi_q^mu zeta_{mu nu} chi_r^nu chi_s^nu; projecting into the non-orthogonal
THC basis gives a diagonal Coulomb operator G = 1/2 sum_{alpha beta} sum_{mu nu} U_mu^dag n_1 U_mu U_nu^dag n_1 U_nu zeta
with only N/2 Givens rotations per basis change (their N = spin orbitals) controlled by mu, angles from QROM
(Sec. III.C). lambda = sum_l |t_l| + 1/2 sum_{mu nu} |zeta_{mu nu}| (Eq. after Texp) with T'_pq = T_pq + sum_r V_pqrr.
Per-step cost Eq. THCtoffolis: 30 n_M + 4 rotprec - 16 + 2 n_M^2 + 3 zetabits + ceil(d/k_s1) + m(k_s1-1) + ceil(d/k_s2) + k_s2
+ 2M + 4N rotbits - 11N/2 + ceil(M/k_r1) + ceil(N/(2k_r1)) + k_r1 + ceil(M/k_r2) + k_r2, iterations ceil(pi lambda/(2 eps_PEA)),
qubits Eq. THCqubits. **FeMoCo (Table femoco_scalings)**: Reiher: THC M = 350, lambda 306.3, 5.3e9 Toffolis, 2142 qubits
(10 bits prep, 16 bits rotation); DF 3725 / 1.0e10; sparse 2190 / 8.8e10; SF 3320 / 9.5e10; Trotter (Reiher 2017)
111 / 5.0e13. **Li (76o)**: THC M = 450, lambda 1201.5, 3.2e10, 2196 qubits (10 / 20 bits); DF 6404 / 6.4e10; sparse
2489 / 4.4e10; SF 3628 / 1.2e11. Chemical accuracy judged by CCSD(T) correlation-energy change vs THC rank
(Fig. femoco), the criterion that Low et al. and Caesura et al. inherit.

**DF re-costing (App. "double low rank factorization")** — the template for the competition's heuristic:
state-prep QROM over Xi·M entries of b = 2 n_Xi + 2 n_M + zetabits + 2 bits, cost ceil(XiM/k_p) + b(k_p - 1), uncompute
ceil(XiM/k'_p) + k'_p; contiguous-register offsets QROM ceil(M/k_M) + n(k_M - 1); **rotation QROM
ceil(XiM/k_r) + N rotbits (k_r - 1)/2 (N/2 angles of rotbits bits per entry), inverse ceil(XiM/k'_r) + k'_r**;
4N(rotbits - 2) for the controlled rotations (phase-gradient adders with the two trivial top bits dropped), 2N spin
swaps, equal-superposition 3n - 3 eta + 2 rotprec - 9, reflections; total Eq. after qrom2; rotbits = ceil(5.652 +
log(N lambda/(2 eps))). It also fixes a flaw in von Burg's joint-register reflection (one-body term folded in as an
extra l = 0 value with a separate state preparation, Fig. selectdf). Lesson for us: the angle QROM is costed as a
select-swap with k_r and its *uncompute* at ceil(L/k') + k' — the competition forbids this asymmetry (Sec. 1.4).

### 2.6 Berry, Gidney, Motta, McClean, Babbush — *Qubitization of arbitrary basis quantum chemistry leveraging sparsity and low rank factorization*, Quantum 3, 208 (2019); arXiv:1902.02134

Sparse and single-factorised qubitisation; FeMoCo (both active spaces) with ~2e13 Toffolis in the dirty-ancilla
variant. The part that matters here is the **QROM/QROAM cost model** everybody uses: computing a lookup of d entries of
w bits with select-swap parameter k costs ceil(d/k) + w(k - 1) Toffolis; **uncomputing with measurement-based
unlookup costs ceil(d/k) + k** (X-measure outputs, classically conditioned phase fixup done by a Z-type lookup on the
high address bits with binary-to-unary expansion of the low bits; App. "unlookup"), k may differ between compute and
uncompute, and the forward ancillae become reusable; with dirty ancillae 2ceil(d/k) + 4w(k-1) and 2ceil(d/k) + 4k
(Theorem thdirty). kickmix's `del_lookup` is exactly this unlookup (see `kickmix.md`). These are the formulas behind
Low et al.'s "QROM(u)^dag: R + B" and "AliasSampling^dag" rows.

### 2.7 Loaiza, Khah, Wiebe, Izmaylov — *Reducing molecular electronic Hamiltonian simulation cost for LCU approaches*, Quantum Sci. Technol. 8, 035019 (2023); arXiv:2208.08272

**Theorem (1-norm bound)**: every LCU of a bounded Hermitian H has lambda >= Delta E/2 = (E_max - E_min)/2, with the
minimiser H = (E_min + Delta E/2) 1 + (Delta E/4)(U_+ + U_-), U_+- = H_sr +- i sqrt(1 - H_sr^2) (impractical: square
roots). Symmetry shift H_S = H - s_1 N_e - s_2 N_e^2: first minimise the two-electron 1-norm of H_2 - s_2 N_e^2, then the
modified one-body H_1'(s_2) - s_1 N_e (optimal s_1 = median of the one-body eigenvalues); also fermionic-fragment
(DF/CSA) and qubit LCUs, interaction picture. This is where "symmetry shift" enters the lineage: the competition's
beta_1 (N_hat - eta) is the s_1 term; the N_e^2 term is the trace part of S.

### 2.8 Loaiza & Izmaylov — *Block-invariant symmetry shift (BLISS)*, J. Chem. Theory Comput. 19, 8201 (2023); arXiv:2304.13772 (+ Patel et al., arXiv:2409.18277)

BLISS: H_T = H - kappa_1 (N_e - N_e) - kappa_2 (N_e^2 - N_e^2) - sum_ij xi_ij F^i_j (N_e - N_e), xi symmetric, F^i_j the
spin-summed excitation. The product of a one-body operator with the annihilator (N_hat - N_e) is *not* a symmetry,
so other particle-number sectors' spectra change, but the target sector is untouched (block-invariant). Constraints:
Hermitian, same polynomial degree as H, spin-symmetric coefficients. Results: spectral range reduced by 42% on
average (31% for the partial shift), DF and orbital-optimised anticommuting-grouping 1-norms reduced ~49%, i.e.
"practically halves the cost" of LCU methods; the BLISS-shifted spectral range is close to the N_e-sector range
Delta E_{N_e}, "cannot undergo significant further improvements". Works for initial states with ground-state overlap
> 0.5 even if symmetry-broken. Patel, Brahmachari, Cantin, Wang, Izmaylov (arXiv:2409.18277) show the BLISS
1-norm minimisation can be solved to the global optimum by linear programming. In Caesura et al.'s notation
H_BI = H - alpha_1 N - (alpha_2/2) N^2 - 1/2 B(N - eta), h^BI_pq = h_pq - 1/2 sum_r g_prrq - alpha_1 delta + 1/2 beta_pq eta,
g^BI_pqrs = g_pqrs - alpha_2 delta delta - 1/2(beta_pq delta_rs + delta_pq beta_rs) — compare the competition's
h2 + 1/2 (S (x) I + I (x) S), h1 - (eta/2) S + beta_1 I: S = -beta (sign convention) and beta_1 = -alpha_1. **[derived]**

### 2.9 Cortes, Rocca, Gonthier, Ollitrault, Parrish, Anselmetti, Degroote, Moll, Santagati, Streif — *Assessing the query complexity limits of quantum phase estimation using symmetry-aware spectral bounds*, arXiv:2403.04737

Hierarchy (Corollary): Delta_mu/2 <= Delta_s/2 <= Delta/2, Delta_mu = E_max^mu - E_min^mu in sector mu = (eta, S),
Delta_s = max_mu Delta_mu, Delta = full range. Theorems: lambda_S >= Delta_s/2 for symmetry-shifted Hamiltonians
(H - f(S)), **lambda_BI >= Delta_mu/2 for block-invariant Hamiltonians** (the true floor for BLISS/DFTHC-type
LCUs). Numerics by orbital-optimised single determinants (variational, hence conservative) for FeMoCo (Reiher, S = 0),
FeMoCo (Li, S = 3/2), P450, heme-artemisinin (Table results_1, Ha):

| system | Delta/2 | Delta_s/2 | Delta_mu/2 (coherent) | Delta_mu/2 incoherent (1-body + 2-body) |
|---|---|---|---|---|
| FeMoCo Reiher 54o | 135.0 | 45.7 | 38.8 | 45.9 = 19.5 + 26.4 |
| FeMoCo Li 76o | 559.4 | 106.2 | **57.6** | 108.9 = 41.2 + 67.7 |
| P450 58o | 209.7 | 57.5 | 49.9 | 69.3 |

So for FeMoCo-76 no BLISS-type factorisation (DFTHC included, since it factorises one- and two-body parts separately:
the *incoherent* bound 108.9 is the relevant one for "contemporary tensor factorization techniques") can have
Lambda below ~58 Ha (coherent) / ~109 Ha (incoherent); Caesura's BLISS-THC at 198.9 and Low's DFTHC at 179.7 are
within 2x of the incoherent bound. Low et al. use the sector bound in lambda_eff >= sqrt(E_gap(Delta_mu - E_gap)) =
21.69 Ha. The competition's Lambda floor 49.0 sits just below Delta_mu/2 = 57.6 — "these floors rule out degenerate
factorizations that shrink the normalization or the gap to game lambda_eff". **[inference]** Realistically Lambda is
bounded below by ~110-180 Ha with a fixed, non-co-optimised shift; the DF-like column of Low's scan reached 140.6.

### 2.10 Rocca, Cortes, Gonthier, Ollitrault, Parrish, Anselmetti, Degroote, Moll, Santagati, Streif — *Reducing the runtime of fault-tolerant quantum simulations in chemistry through symmetry-compressed double factorization*, J. Chem. Theory Comput. (2024); arXiv:2403.03502

SCDF = compressed DF (optimised U^t, rank-1 W^t W^t) + per-leaf symmetry shift alpha^t with the N_e^2 shift applied
*after* factorisation: cost L = 1/2||(pq|rs) - sum_t U U (W_k W_l) U U||_F^2 + rho sum_t sum_kl |W^t_k W^t_l - alpha^t|
(Eq. costfRXDF1norm2); shifted leaves become rank 2 but only N_alpha of the alpha^t are nonzero. FeMoCo-54 (Table
results_femoco): XDF lambda 293.9 (9.6e9 Toffolis, 3722 qubits), XDF + symmetry shift 182.9 (6.0e9), THC 306.3
(5.3e9, 2142), **SCDF 5N leaves, Xi = 35: lambda 78.0, 2.4e9 Toffolis, 3722 qubits; with k_r = 2: 2.6e9, 1994 qubits**
(the DF-vs-qubit trade-off through the angle select-swap parameter); P450 111.3. Lessons: optimised (non-eigen) leaves
with a 1-norm penalty halve lambda again over plain shifts; Lambda-regularised training is the state of the art the
DFTHC program generalises.

### 2.11 Oumarou, Scheurer, Parrish, Hohenstein, Gogolin — *Accelerating quantum computations of chemistry through regularized compressed double factorization*, Quantum 8, 1371 (2024); arXiv:2212.07957

RC-DF: C-DF (Parrish-style two-step optimisation of orbital rotations U^t and core tensors Z^t) plus an L2
regulariser sum_tkl rho |Z^t_kl|^2 (Eq. regularization_term) to stop Z entries blowing up, matrix-free CG for the
6-index step, initialised from truncated X-DF. For P450 (58o) it almost halves lambda^Burg_DF vs truncated DF at CCSD(T)
error < 5e-5 Ha and reaches 60% of lambda_THC; linear scaling of lambda with n on hydrogen chains; thousands of L-BFGS
iterations (11 h on one GPU for n_t = 100). Relevance: regularised compressed factorisations converge where THC is
finicky; the competition's "weights-only refit" strategies are the cheap end of this.

### 2.12 Caesura, Cortes, Pol, Sim, Steudtner, Anselmetti, Degroote, Moll, Santagati, Streif, Tautermann — *Faster quantum chemistry simulations on a quantum computer with improved tensor factorization and active volume compilation*, arXiv:2501.06165

BLISS-THC (Sec. II.C-D): H_BI in Majoranas, g^BI factorised by THC, lambda~_THC = sum_k |t~_k| + 1/2 sum |zeta~_{mu nu}| -
1/4 sum_mu |zeta~_{mu mu}| (Eq. blissthclambda); cost function Eq. BLISS_THC_Cost = 1/2 ||g^BI(alpha, beta) - THC||^2 +
rho·lambda~ with alpha, beta (shift) co-optimised. **FeMoCo-76** (App. "Speedups ... FeMoco"): M = 290, l2 error 0.086 Ha,
CCSD(T) error -0.26 mHa, lambda 198.9 (vs THC 1201.5, THC* 781.8, DF* 582.4), 4.3e9 Toffolis (4.282e9 with circuit
mods), 1512 qubits, bits (aleph, beth) = (15, 16); overall 278-427x runtime speedup incl. active-volume compilation.
**Givens rotations (Sec. III.B)**: G_k(theta) = exp(-i pi theta X_{k+1} Y_k) exp(i pi theta Y_{k+1} X_k), eigenvalues
{1, e^{+-2 pi i theta}}; implemented by *one fused controlled adder into a phase-gradient register with conditional
flips*, lower Toffoli count and active volume than Lee et al.'s two adders, and one bit shorter since the words hold
theta not theta/2 — this is the "(2 b_t - 1)-Toffoli controlled adder" of the competition heuristic. Also notes that
Lee et al.'s bit choice neglected the one-body preparation.

### 2.13 Kivlichan, McClean, Wiebe, Gidney, Aspuru-Guzik, Chan, Babbush — *Quantum simulation of electronic structure with linear depth and connectivity*, PRL 120, 110501 (2018); arXiv:1711.05395

Givens-rotation networks for preparing Slater determinants / fermionic Gaussian states and for basis changes:
N_G <= N^2/4 Givens rotations on adjacent JW modes in depth N - 1 using the V-freedom of the occupied subspace; the
2-qubit Givens circuit (Fig. givens) is a rotation in the {|01>, |10>} subspace; nearest-neighbour rotations commute
when disjoint. For a *single* rotated vector (what the block encoding needs) only N - 1 rotations are needed (von
Burg Lemma), and any spanning tree of the mode graph works; the ordered tree in the competition is the general case,
a path being Kivlichan/von Burg's chain. **[inference]** A tree with depth log N lets the N - 1 rotations be applied in
O(log N) layers on all-to-all hardware, but the competition only counts Toffolis, so depth is irrelevant to the score.

### 2.14 The FeMoCo integrals: Reiher et al. 2017 (arXiv:1605.03590) and Li, Li, Dattani, Umrigar, Chan 2019 (arXiv:1809.10307)

Reiher, Wiebe, Svore, Wecker, Troyer, PNAS 114, 7555 (2017): FeMoCo model of nitrogenase, structure 1: S = 0, charge
+3, **54 electrons in 54 spatial orbitals (108 spin orbitals)**, orbitals from small-CAS CASSCF/DMRG; structure 2:
65e/57o; Trotter-based estimates ~1e14 T gates. Li, Li, Dattani, Umrigar, Chan, J. Chem. Phys. 150, 024302 (2019),
arXiv:1809.10307 (*The electronic complexity of the ground-state of the FeMo cofactor of nitrogenase as relevant to
quantum simulations*): shows the Reiher active space misses the open-shell character and proposes the
**(113e, 76o) active space (152 qubits), ground state S = 3/2**, which Lee et al., Berry et al. 2024 (DMRG M = 6000
upper bound), Caesura et al., Low et al. and **this competition (`FeMoCo76o113e.fcidump`, N = 76, eta = 113)** use.
High-spin CCSD(T) checks use S_z = 35/2 (Low et al.) and S = 35/2 (Caesura).

### 2.15 Related: Majorana tensor decomposition and SOS lower bounds

Loaiza, Sankar Brahmachari, Izmaylov, *Majorana tensor decomposition* (arXiv:2407.06571) unifies DF/THC/CSA-type
LCUs as low-rank factorisations of the Majorana-representation tensors — the same Majorana bookkeeping Low et al. and
Caesura et al. use. The SOS lower-bound literature Low et al. cite (Mazziotti 2006; Pironio-Navascués-Acín 2010;
Hastings 2022-24 perturbative SOS) is the source of "E_SOS as a certified lower bound"; the only directly reusable
piece for the benchmark is the observation that the spin-free level-2 algebra already gives gaps of ~4 Ha for FeMoCo-76.

---

## 3. Synthesis: what sets lambda_eff x T x Q here, and what we can move

### 3.1 Anatomy of the score (baseline values in brackets)

```
score = lambda_eff(Lambda, E_gap)  x  [ANGLES + outer + inner + Givens]  x  [90 + J·brot + max temp]
        49.30                         [79,480 + 846 + 9,461 + 3,450]       [90 + 96 + 544]
```

* **lambda_eff**: with E_gap pinned at the floor (everyone sits 1e-6 above it), lambda_eff = sqrt(3.9149(2Lambda - 3.9149)).
  Lambda = Lambda_1 + Lambda_2 = ||h1'||_* + 1/4 sum_l (|w_lB| + sum_b |w_lb|)^2. Baseline 308; Low et al.'s best DFTHC
  with a co-optimised shift 180; DF-like 141; Caesura's BLISS-THC 199; symmetry-sector floors 57.6 (coherent) / 109
  (incoherent). **[derived]** E_gap = E_upper + eta beta_1 + 2 sum_j w_{-,j} + 1/2 sum_l W_l^2 depends on the factorisation
  only through the negative-eigenvalue mass of h1' and the identity offsets; with the floor binding, those two sums
  must add to a fixed G_min, and Lambda = Tr h1' + 2 sum w_- + Lambda_2 with Tr h1' = const - sum_l W_l Tr X_l. So the
  W_l are a genuine lever: they move weight between the one-body negative mass (counted once in Lambda, twice in
  E_gap) and 1/2 W^2 (counted in E_gap only) while changing |w_lB| in Lambda_2 and Tr h1'. The organiser's trainer
  presumably already does this; a weights-only refit of a public word table does not.
* **ANGLES** (the only simulated part, 85% of T at the baseline): per circuit, a plain QROM costs L - 2 Toffolis
  (3974 at L = 3976), so ANGLES ~ 2·K·(L - 2) = 2·ceil(75/J)·(L - 2). Select-swap with parameter k costs ~ ceil(L/k) +
  J·brot·(k - 1) but needs J·brot·k + ceil(log2 L) + O(log) qubits <= 128, i.e. J·brot·k <= ~105. With the baseline's
  J·brot = 96 only k = 1 fits. Under the cap the forward+reverse total is roughly
  150·L/(J·k) + 150·brot·(k - 1), minimised when J·k·brot ~ 100, giving ANGLES ~ 1.5·L·brot + O(150·brot·k). **[derived]**
  Hence ANGLES is essentially proportional to **L x brot** (addresses times bits) whatever the batching, and the cap is
  what stops select-swap from paying off; the public frontier's (8,143,60), brot = 8 (L = 1220) fits this scaling.
* **inner / outer**: outer ~ 4log + ceil((N+RC)/2^k1) + 2^k1(log + 10) + inverse (846 at N+RC = 3976, ~400 at 556);
  inner is driven by R·C (unary iteration over the two-body generators) and (B+1)·(log(B+1) + 10) (alias-sampling data
  for b), each twice plus inverses (9,461 at RC = 3900, B = 60). The INNER QROAM's temporary qubits (2^k2 - 1)·b2 set
  the shared `max temp` (544 at the baseline, larger than any ANGLE circuit's workspace), so Q is dominated by
  the state-preparation heuristic, not by the circuits we write.
* **Givens**: 150·(2 brot - 1): only brot matters (3,450 at 12 bits, 2,250 at 8, 1,950 at 7).
* **Q_tot**: 90 + J·brot + max(temp). Cutting J·brot from 96 to 40 saves 56 of 730 (-8%); cutting the inner temp is
  the big Q lever and trades against inner Toffolis through k2.

### 3.2 Levers inside the constraints, with rough gains

1. **Fewer addresses and fewer bits (L x brot)** — the dominant T lever. The two 20 mHa Frobenius gates are the
   constraint. Low et al.'s FeMoCo-76 solutions had eps_fro = 48-83 mHa with RB = 855-960, so hitting 20 mHa needs more
   than that; the public (8,143,60) (RB = 1144, L = 1220) and the THC-like (1,496,384) (L = 572 but RC = 384 and Q = 833)
   bracket the current frontier. Expected: L 1220 -> ~800 and brot 8 -> 7 would be ~1.7x on ANGLES if the error gates
   allow; each is a training problem (Frobenius objective, fixed S0, beta_1, with E_gap >= floor and Lambda penalty).
   Use randomised rounding (Low et al. App. bits) and a shallow tree to make low brot pass the gates; the 76 one-body
   rows are checked separately (error_1) and are only 76 of L addresses, so they can be given a different effective
   precision only through the shared word width — no per-row width exists.
2. **Lambda at the E_gap floor** — the only lambda lever. Public weights-only refits stay at Lambda ~ 300 (lambda_eff
   48.3-48.8, 1-2% below the baseline). A full re-optimisation with the fixed shift, Lambda-regularised like Low's
   program (lambda_reg ~ 100 mHa) and Rocca/Oumarou's compressed-DF experience, targeting Lambda ~ 200-250 would give
   lambda_eff 39-44, i.e. 1.1-1.25x. Whether the fixed S0 permits this is unknown; Low's scan shows Lambda in
   140-206 across (R,B,C) shapes *with* a free shift, so 200-250 with a fixed shift is plausible but unproven.
   **[inference]** The W^(rho c) identity offsets and the split of h1' into positive/negative eigenvalues are the knobs
   that move Lambda at fixed E_gap (3.1); include them explicitly in the optimiser instead of inheriting them.
3. **ANGLE oracle engineering under the 128-qubit cap**: (a) choose (J, brot, k) with J·brot·k <= ~105 and use
   select-swap k = 2-4 with measurement-based erasure of the (k-1)·J·brot temporaries (half-priced conditioned
   Toffolis); (b) order the R·B vectors (free: any permutation of rho and of b within rho, with W permuted
   consistently) so that per-batch words form long runs of identical values or zeros, and skip identical ranges in
   the unary iteration (a contiguous range with identical data costs O(log range) Toffolis instead of O(range)) —
   combine with a tree chosen so that vectors supported on a subtree have zero words on the other edges;
   (c) the baseline wastes nothing on the uncompute side (the XOR oracle is symmetric), so gains here are bounded by
   the ~1.5·L·brot scaling: expect 1.2-1.5x at most on ANGLES, more if the word table is highly compressible.
4. **(R,B,C) co-design with the heuristics**: ANGLES ~ L·brot favours small RB; inner ~ RC + (B+1)(log B + 10) favours
   small RC and B; DF-like shapes (large R, B = N, C = 1) kill inner but blow up RB; THC-like (1,B,C) kills RB but needs
   large B, C (big b2 and temp). Low et al.'s Amdahl heuristic (B, C = Theta(N), R = O~(1)) is the right neighbourhood;
   with the inner heuristic read from `costs_prepare.py`, grid (R,B,C) in R in [2,16], B in [40,200], C in [20,100]
   with the surrogate T·Q·lambda_eff before training anything.
5. **Tree and gauge**: the tree does not change any Toffoli count; use it (and the choice among the many angle
   solutions theta in f^-1(u), including signs/pi-shifts: "exact gauge" in the public notebooks) purely to minimise
   quantisation error at low brot and to shape the word table (zeros, runs). Low et al. note the solution set f^-1(u)
   is multi-valued and any member works.
6. **Things that do not help**: E_gap below the floor (rejected), Lambda below 49 (rejected, and physically bounded
   by ~58-109 anyway), tree depth (not scored), per-row precision (one `brot` for all words), measurement-based
   unlookup as the reverse pass (the same circuit runs both ways), Z_POW (forbidden).

### 3.3 Prioritised plan with estimated gains (multiplicative on the baseline 3.356e9; public frontier ~9.9-10.6x)

| # | action | est. gain | depends on |
|---|---|---|---|
| 1 | Get the verifier package and `scoreinfra/costs_prepare.py`; reproduce baseline 3,355,599,588; build an exact surrogate score(R,B,C,brot,J,circuit-model) | enabling | data download |
| 2 | Reproduce the public frontier shape (8,143,60), brot 8, J = 8 and its ~9.9x; measure where its T and Q go (ANGLES vs inner vs temp) | enabling | 1 |
| 3 | Train DFTHC with the fixed shift: Frobenius <= 20 mHa (both gates), E_gap >= floor + margin, Lambda penalty, randomised rounding at the target brot inside the loop, W and h1' negative mass as explicit variables; scan (R,B,C) from the surrogate | lambda_eff 48 -> 40-44 (1.1-1.2x), L 1220 -> 700-900 (1.3-1.7x on ANGLES) | 1, 2, GPU |
| 4 | ANGLE oracles: select-swap under the cap, run-skipping unary iteration on sorted/compressed word tables, measurement-based temp erasure, kickmix `set_max_qubits` tuning | 1.2-1.5x on ANGLES | 2, 3 |
| 5 | Q: pick (R,B,C) and k2 so inner temp <= ANGLE temp, minimise J·brot | 1.1-1.3x on Q | 1 |
| 6 | brot 8 -> 7 (or 6 on a log-depth tree with gauge optimisation) if gates allow | 1.1-1.15x on T | 3, 5 |

Compounded, 1.5-2.5x over the public frontier looks reachable (~15-25x vs baseline) if items 3 and 4 both work;
item 3 is the research-grade one and should start first because it gates everything else.

### 3.4 Open questions to settle locally

* Exact `SpinFreeData_V1` formulas (inner prep, temp sharing with brot) — the outer part matches Low et al. Table
  "outer_prepare_costs" with chi = 10 exactly; the inner does not with naive k choices.
* How the fixed (S0, beta_1) were produced (with the (65,60,60) baseline? Lambda-regularised?), and how far Lambda can
  fall under it — test by retraining at the baseline shape before changing (R,B,C).
* Whether `error_1`'s eigenvector matching is robust to near-degenerate eigenvalues of h1' at low brot (it reconstructs
  with *exact* eigenvalues and *quantised* vectors, so degenerate subspaces can be rotated freely — a possible gauge
  freedom for the one-body rows). **[inference]**
* Whether the mean-over-shots Toffoli count rewards randomised/measurement-conditioned constructions inside ANGLE_k
  beyond the standard unlookup of temporaries.

---

## 4. Source files

* arXiv sources/PDFs: `papers/{2610.23832,2502.15882,2505.01528,2007.14460,2011.03494,1902.02134,2208.08272,2304.13772,2403.04737,2403.03502,2212.07957,2501.06165,1711.05395,1605.03590}/src/` in the session scratchpad (Li 2019 = arXiv:1809.10307, not downloaded; Patel 2024 = arXiv:2409.18277; MTD = arXiv:2407.06571).
* Competition chemistry text: `papers/2610.23832/src/GH_notes/{dfthc_integrals_optimization_target,majorana_rotations_classical,dfthc_block_encoding}.tex` and `main.tex` lines 735-820, 854-1043.
* Official README mirror: `docs/research/kaggle-raw/mirrors/official_verifiers_dfthcsos_SCORING_README.md`.
