# AI-agent-discovered kickmix circuit tricks: Gu et al. (2610.22367) and Long et al. (2609.28882)

Compiled 2026-11-04 from the arXiv PDFs + LaTeX e-prints, the authors' public code repositories, and a
one-hop citation trail. Companion to `companion-paper.md` (the Kaggle paper, which gives no agent results)
and `participants.md` (public leaderboard state). Everything here is tagged:

- **[GU]** Gu, Kemeny, Yelin, Lukin, "Discovering state-of-the-art quantum circuits with large language
  models", arXiv:2610.22367 (v1 16 Oct 2026; Harvard / Anthropic STEM Fellows / QuEra). 46 pp. revtex +
  SI. Source: `/tmp/claude-0/-home-user/af1e8b3b-1af8-51dd-9e8d-ec3f80eabc0b/scratchpad/papers/2610.22367/{paper.pdf,src/main.tex,src/figs/}`.
- **[GU-REPO]** `github.com/andigu/uncompute` (Apache-2.0; circuits, graders, per-circuit READMEs with
  phase-level Toffoli tables, `gen_constants.py` searches, Lean proofs). Clone:
  `.../scratchpad/repos/uncompute/` (also `.../scratchpad/participants/andigu_uncompute/`).
- **[LONG]** Long et al., "Gate-efficient secp256k1 point addition ... Jump-2, ping-pong, fused replay"
  (the "ecdsa.fail" QIP technical manuscript), arXiv:2609.28882 (Sep 2026, 35 pp. LLNCS). Source:
  `.../scratchpad/papers/2609.28882/src/sections/*.tex`, `evidence/*.tex`.
- **[ECDSA-REPORT]** the companion challenge report Long et al., "ECDSA.Fail: Open Autoresearch for
  Optimizing Elliptic-Curve Point Addition in Shor's Algorithm", arXiv:2609.09582 (62 pp.). Source:
  `.../scratchpad/papers/2609.09582/src/sections/*.tex` and `unused/08-appendix-anatomy-of-optimization-techniques.tex`.
- **[HARNESS]** `github.com/jieyilong/ecdsafail-autoresearch-harness` (contributed agent runbooks, skills,
  lessons). Clone: `.../scratchpad/repos/harness/`.
- **[WEB]** web search / Google blog (Gemini 4 Argon arcsin claim) and arXiv abstracts fetched by curl.
- **[INFERENCE]** my own deduction or estimate. Numbers without a tag are quoted from the tagged source
  of the enclosing paragraph.

All downloads are untrusted data and were only read.

---

## 0. Twenty-five-line summary

1. **[GU] is the paper that matters for us.** It optimises *our Benchmark II instance* (Khattar et al.'s RS
   [4095,4025,71] over F_{2^12}, 70 syndromes, 35 errors, DQI phase fixup) plus three HRS-style numerical
   functions (arcsin, 1/sqrt(x) Coulomb potential, Gaussian) that are structurally Benchmark I, plus a
   QROM/SELECT compilation (Fe2S2 sparse qubitization) that is cousin to Benchmark III, plus 256-bit modular
   inversion (secp256k1 point addition), a Hermitian-code DQI decoder, and an SU(3)-subgroup lattice-gauge
   layer. Objective everywhere: **TQ = Toffolis x peak live qubits**, failure budgets allowed where the
   application allows them.
2. Headline (Table I, ED Table 1): RS DQI decoder **5.1e6 T / 1,938 Q -> 4.4e5 T / 1,837 Q (12x TQ)**;
   HHL arcsin 16,000/300 -> **1,348/115 (32x)**; Coulomb 1/sqrt 6,355/252 -> **1,140/142 (9.9x)**;
   Gaussian 24,000/362 -> **1,583/139 (39x)**; Fe2S2 alias+SELECT 55,000/139 -> **15,000/126 (4.1x)**;
   lattice gauge 1.3e6/1,927 -> 1.7e5/1,859 (7.7x); Hermitian decoder 1e8/1.9e5 -> 9.3e5/2,395; modinv
   point-add 4.0e6/935 (new divstep architecture) and a 3.4x Toffoli cut of Luo's packed EEA at 843 Q.
3. Three recurring principles [GU, "Design principles"]: (a) **conditional routing** (cheap CSWAPs route data
   through one unconditional kernel instead of two controlled kernels: halves MADD cost), (b) **decode branch
   history from the live state instead of storing it** (invariants let uncompute recover the branch bit),
   (c) **spend the failure budget on rare inputs** (size stacks/windows/schedules to typical inputs,
   measured by classical simulation of the input distribution).
4. RS decoder tricks [GU SI I.1; GU-REPO README]: Berlekamp-Massey instead of synchronised EEA (1.9M -> 140k
   for the key equation); retain/replace on one shared path via rescaling (locator only needed up to scale);
   invariant sigma_0 * delta = 1 so no discrepancy is stored; one-entry (19-qubit) history stack instead of 665
   qubits at 1e-4 failure; per-round coefficient cutoffs measured on 403M classical draws (3.8e-5 failure);
   in-place sigma*S overwriting the syndrome (saves 420 qubits, zeroes the last 35 words = free workspace);
   phase-only Forney via trace: Tr(nu_j omega(beta_j) Psi(beta_j)) where Psi = 1/sigma' mod sigma is
   **precomputed once** by a half-degree Euclid on the even/odd split sigma = E^2 + z O^2 (no per-point
   division); the mask's syndrome-linear part applied with free Z gates (71 positions removed);
   **23 Toffolis per swept point** (11 zero-test + 12 gated rank-12 bilinear form) vs ~80 with a division and
   ~306 in the baseline; **42-Toffoli F_{2^12} multiplier** (CRT evaluation over GF(4), 14 GF(4) products);
   **66-Toffoli inversion** (tower norm GF(2^12)->GF(64)->GF(8), M^-1 = (M^3)^2 free); every bilinear product
   erased by X-measurement + classically-conditioned CZ.
5. Numerical-function tricks [GU SI III; GU-REPO]: dyadic (power-of-two-aligned) intervals selected by input
   prefixes -> unary-iteration tree lookup at ~1 Toffoli per leaf, so 345 or 1,024 pieces are affordable and
   degree drops (cubic->quadratic, quadratic->line); cyclic rotation of the low input bits into one shared local
   coordinate (no subtraction, wrapped bits absorbed into coefficients offline); Booth radix-4 signed-digit rows
   (13 rows -> 7); accumulate products straight into the destination (no product or value register);
   measurement-based unlookup with one **batched** phase repair (one-hot rail + Reed-Muller/Moebius planes:
   17 Toffolis instead of 126 ANDs for Coulomb, 50 instead of 495 for Gaussian); content-pruned QROM
   (1,022 -> 495 Toffolis when subtrees are uniform); backward fitting of integer coefficients through the
   exact truncated pipeline (one error budget for everything); free complement instead of exact |x| (one unit
   of displacement charged to the error ledger); per-position choice measured carry (1 Tof + 1 live qubit) vs
   Cuccaro in-place carry (2 Tof, 0 qubits) under a live-qubit cap; exhaustive classical certification.
6. QROM/SELECT tricks [GU SI IV]: choose the table (address map + alias pairings) so adjacent words repeat and
   prune repeated spans (41,050 -> 10,271 Toffolis); group Pauli rows into blocks generated by commuting
   Clifford "frames" (41,000 -> 3,327 + 534); controlled quadratic phases cost exactly rank(B)/2 CCZs after a
   CNOT change of basis; Z-gauge search (769 -> 108 sign Toffolis); joint unlookup of several measured banks
   in one address walk; exact dynamic program over "hold budgets" (which path ANDs to keep live).
7. Modular inversion [GU SI II]: divsteps made reversible by decoding branch bits from the 2-adic window
   invariant (Lean-proved), cutoff j_store=5 between decode and store, 533-step schedule with termination
   tests only from step 499, 60-qubit history stack, scale 2^-t removed by one modular halving per reverse
   step, g/f_v and f/g_v packed in two 256-qubit registers; Luo's packed EEA specialised with fitted windows,
   schedule cut 1,616 -> 1,432, test-free positions, merged scans, measured carries (70M -> 21M Toffolis).
8. [GU] search loop (Methods "Evolutionary search", ED Fig. 1): **OpenEvolve + Claude Mythos 5**; hand-written
   task spec, blank program; **ideation** step proposes up to five algorithm families; each family evolved in
   parallel; **MAP-Elites** archive over (T,Q) cells keeps the lowest-TQ circuit per cell; every iteration is a
   **fresh agent session** given the parent program + evaluator feedback + a few archive programs + short
   `DISCOVERY:` notes; the agent can run drafts (`run_candidate(trial_eval=true)`), query a classical oracle
   for the reference function, and delegate subtasks to subagents; periodic cross-family sharing; evaluator is
   ground truth. **Not reported**: iteration counts, token/compute budget, wall-clock, number of valid
   candidates, acceptance rates, or prompts beyond the ED Fig. 1 excerpts.
9. [LONG]/[ECDSA-REPORT] is a public, many-team "open autoresearch" record (100+ participants, 400+ promoted
   submissions in 8 weeks, QxT 10.75e9 -> 1.496e9 = 7.2x by cutoff; later 1.26e9). Tricks: Jump-2 GCD
   macro-steps + base-5 transcript codec (609 vs 783 qubits); comparison-free **ping-pong** GCD (low-2-bit
   add/sub decision, fixed register alternation, 1 bit/round, -340k static Toffolis vs Jump-2, +171 qubits);
   fused doubling+signed-add modular replay (446 -> 393 Tof/cell); streamed Karatsuba square with sparse-prime
   fold; split-address MBU lookup cleanup C(w)=2(2^floor(w/2)+2^ceil(w/2))-4 (164,090 -> 3,060 Toffolis for
   three unloads); constant propagation, CCX fan-out identity, classical folding, measured carries,
   phase-conditioned comparator replay, measured-fast adders on non-peak adders, NAF recoding, free-and-
   recompute, range-bound guard bits, borrowed carries, segmentation of the peak binder.
10. [ECDSA-REPORT] loop design is organisational rather than algorithmic: shared evaluator + leaderboard,
    profile-before-ideate, value-exact vs island-exact candidate classes, staged validation
    (smoke -> regression -> full), orchestrator + clean-context workers in git worktrees, watcher agents that
    diff the frontier, append-only negative-result memory, versioned skills, human steering on direction and
    non-monotonic exploration. Negative results: jump=4 GCD refuted (+32-67% Toffoli: CSWAPs are billed by
    classical condition), ping-pong needs 1,135-1,239 rounds on some valid inputs (704-768 budgeted), nonce
    grinding of the Fiat-Shamir seed is a real integrity problem, sampling cannot certify value-exactness,
    "search-and-distill" small models plateaued, agents missed the Khattar->ECDLP literature transfer.
11. **Transfer (Sec. 6)**: Benchmark II gets the most (42-Tof multiplier, 66-Tof inversion, Psi precompute,
    trace contraction, free Z-linear mask part, failure-budgeted windows/stack, in-place evaluator); but the
    public frontier (Q=892, ~404k T, 63x) is already past Gu's 1,837-qubit design because our score is
    R Q^2 T. Benchmark I: Gu's HHL/Gaussian recipe is essentially the public 62-qubit/1,325-T frontier
    design; the remaining transferable pieces are backward fitting, batched phase repair, carry-mode dial,
    live-qubit cap sweep. Benchmark III: repeated-span pruning + address-map freedom + joint phase repair +
    hold-budget DP apply directly to the ANGLE QROMs.
12. **Loop (Sec. 7)**: replicate [GU]'s evaluator-in-the-loop MAP-Elites with family seeding, fresh-context
    sessions, DISCOVERY notes; add [ECDSA-REPORT]'s profiling-first, exact-vs-approximate labelling, staged
    validation and negative-result ledger; score with our three exact cost functions, not TQ.

---

## 1. Gu et al., arXiv:2610.22367 — "Discovering state-of-the-art quantum circuits with LLMs"

### 1.1 Problem class, circuit model, verifier (Methods "Circuit model and validity", "Validation")

- Target maps: `|x>|y> -> (-1)^{g(x)} |pi(x)>|y xor f(x)>` with every ancilla back to |0>; numerical tasks
  instead specify an error bound on an additive fixed-point accumulator `|x>|k> -> |x>|k + f~(x)>`
  (SI III, with circular distance mod 2^n).
- Model = kickmix of Babbush et al. 2603.28846: reversible classical gates (X, CNOT, Toffoli, SWAP), diagonal
  sign gates (Z, CZ, CCZ, global sign), destructive X-basis measurement (MBU) with classically conditioned
  diagonal corrections; measurement outcomes may be XOR-combined and may control *only* diagonal gates
  (Eq. `kickmix-record`, `kickmix-phase-correctness`). Note: **no Z_POW** in their model; everything is
  sign-exact. Their `Builder` API (ED Fig. 1c): `alloc_qubit(s)`, `free`, `ccx`, `cx`, `cz`, `hmr(t) -> m`,
  `cz(..., cond=m)`, `emit()`; T counts Toffoli + CCZ, a gate under a classical condition "counts at its
  promoted arity" [GU-REPO task READMEs]; Clifford free.
- Verifier = per-shot basis-state simulation; checks output, input restored, ancillas zero, **exact sign**.
  Sampled tests: k passes give eps <= ln(1/delta)/k; with b allowed failures the binomial tail (Methods Eq.
  P_{k,b}); fidelity bound ||Phi_V - Phi_U|| <= 2 sqrt(eps) (Eq. `transfer`). Tests seeded from a hash of the
  emitted circuit ("any change to the circuit draws new tests") [GU-REPO README] — same Fiat-Shamir idea as
  Kaggle.
- Test budgets (ED Table 1): 1e5 shots for RS/Hermitian/modinv/lattice; 9e3 for the numerical tasks
  (plus exhaustive classical certification of the integer pipeline in `checks.py`); 2e7 for Fe2S2 ("every
  table row and 2^24 random inputs").
- Failure budgets: RS/Hermitian <= 100 wrong signs in 1e5 (=> eps <= 2.434e-3 at 97.5%; DQI loss
  <= 4 eps <f>, Eq. `dqi-budget-bound`, Lean-proved in `lean/dqi`); modinv <= 2e-4 per point addition;
  numerical tasks and Fe2S2 exact.
- Scoring = TQ, T = Toffoli+CCZ count (executed; measured on the op stream), Q = peak simultaneously allocated
  qubits. They explicitly say the objective is swappable (Q^kappa T, active volume, depth) and that the
  modinv search produced a whole (T,Q) frontier (SI Table S-"modinv-frontier").

### 1.2 Search methodology (Methods "Evolutionary search"; Fig. 1a; ED Fig. 1; ED Fig. 2)

What is stated:

| Element | [GU] description |
|---|---|
| Framework | OpenEvolve (Sharma 2025, github algorithmicsuperintelligence/openevolve) driving **Claude Mythos 5** (cites Anthropic Opus 5 / Mythos 5 system cards). |
| Candidate representation | Python program that builds the circuit with the Builder ("functions, loops, named registers preserve the organization"; "a single conceptual change can reorganize operations throughout the circuit"). Not gate lists. |
| Input to the search | One fixed hand-written task specification per task (behaviour, interface, model, correctness criteria, failure budget); **blank program**; "no implementation guidance". |
| Ideation stage | LLM sees spec + circuit model + correctness criteria only, returns "up to five distinct circuit architectures ... one implementable datapath per family; merge families with the same main datapath" (ED Fig. 1a). Example for F_{2^4} inversion: Fermat chain, full QROM lookup, tower field. For RS: extended Euclid, Berlekamp-Massey, PGZ (Fig. 1a). |
| Families | Each architecture founds a family evolved **independently in parallel**; "keeping the families separate at first gives each approach time to mature even if its earliest circuits are less efficient"; "periodically, leading programs are shared across families". |
| Archive / selection | **MAP-Elites** over the (T,Q) plane: cells, keep lowest TQ per cell, so "a space-efficient circuit can remain available ... even when its higher Toffoli count gives it a worse TQ". Progress non-monotone (ED Fig. 2 Gaussian lineage: descendants temporarily worse in T or Q before reaching lower TQ). Report the global best at the end. |
| Per-iteration session | **New agent session each iteration**: receives spec, a selected parent program, its evaluator feedback, "alternative programs from the archive and their resource costs" (complete elite + cell-diverse inspiration programs), brief summaries of earlier attempts, recorded insights. "The agent never sees the complete search history." |
| Tools inside a session | `run_candidate(program, trial_eval=true)` (ED Fig. 1b transcript: returns `valid: executed_toffoli=..; qubits=..` or `invalid: ancilla t not returned to |0> at free`), a **classical oracle** for the reference function on chosen inputs, and **subagents** for focused subtasks. |
| Output | Complete rewritten program + up to three lines beginning `DISCOVERY:` ("these notes travel with the program"; e.g. "squaring in a binary field is CNOT-only"). |
| Acceptance | Evaluator rejects invalid; valid scored by TQ; "considered for retention in its family". The LLM "is free to propose broad changes without having to judge their correctness". |
| Human role | "without substantive human intervention"; humans wrote specs, chose objectives, and (SI) ran the offline classical searches / proofs that the discovered designs rely on (`gen_constants.py`, Lean). |
| Evaluator access | "The LLM has no access to the evaluator beyond the feedback returned after each submission." |

Prompt excerpts (ED Fig. 1, verbatim fragments): ideation instruction "From the task specification alone,
propose up to five distinct circuit architectures that reduce executed Toffolis and peak live qubits. Give one
implementable datapath per family; merge families with the same main datapath."; rewrite instruction "Task:
Optimize a reversible circuit for F_{2^4} inversion. Objective: Minimize executed Toffoli x peak live qubits.
API: alloc/free, ccx, free Clifford gates, and corrected measurement-based uncomputation. Return the complete
Python program; the evaluator is ground truth. Discoveries: Print up to three lines beginning DISCOVERY:";
parent block "fitness=<score>, qubits=<Q>, toffoli=<T>", "# FOUNDING DIRECTION --- F1 Fermat chain",
"# Feedback [phase costs and evaluator output]", "# Archive context [recent attempts; complete elite and
cell-diverse inspiration programs]", "# Task Rewrite the parent to improve fitness; return the complete program."

What is **not** reported anywhere in paper or repo: number of iterations/generations per task, number of
families actually run per task, population/cell sizes, compute or token budget, wall-clock, acceptance rate,
how often cross-family sharing happened, which ideas came from ideation vs. evolution, and the full prompts.
The repo ships only final circuits, graders and offline constant searches (`gen_constants.py` is a
deterministic classical search, 100-200 CPU-hours for the Gaussian; `search.c` for RS windows).
[INFERENCE] The level of engineering in the final circuits (exact DP over hold budgets, Lean proofs,
custom bilinear multiplier synthesis) implies long campaigns and substantial human curation of the final
artefacts; the "no substantive human intervention" claim should be read as "the agent chose the algorithm and
circuit structure", not "nobody touched the code".

### 1.3 The three design principles (main text "Design principles", Fig. 1b-d)

1. **Conditional routing.** Branches that differ only in which values occupy which roles: CSWAP the operands
   under the branch bit, run one unconditional kernel, swap back. Example: x <- x + c*y (b=0) / x + c*z (b=1):
   T_naive = 3n^2+17n-2 (two controlled schoolbook MADDs) -> T_routed = (3n^2+17n-2)/2. General form
   U_b = R_b^-1 K R_b; the hard part is "canonicalising" branch states so one K serves both (e.g. rescaling
   the BM locator). In kickmix terms: `cswap` under a qubit control costs 1 Toffoli per qubit pair, under a
   classical bit it is free (see `kickmix.md`), so routing beats duplicating any kernel wider than ~1 Toffoli
   per routed qubit.
2. **Branch decoding instead of history storage.** If the forward update leaves a distinguishable pattern in
   registers that are still live at uncompute time, recover the branch bit there and clear it. Toy: g_{j+1} =
   g_j + b_j 2^j with invariant g_j < 2^j => b_j = bit j of g_{j+1}. Requires designing representation +
   uncompute together; ambiguity can vanish "once the circuit is restricted to states reachable from the
   prescribed initialization".
3. **Failure budget on rare inputs.** Identify the inputs that set the worst-case resource (stack depth,
   iteration count, coefficient width), reorganise so that their extra resources are *localised* (extra
   stack entries, extra iterations, extra lanes), then omit them and measure the failure probability by
   classical simulation of the input distribution.

### 1.4 Trick catalogue (per task)

Legend: **Gain** = as reported; **Applies** = where the mechanism is reusable; **Generalises?** = my reading
[INFERENCE] of how instance-specific the trick is.

#### 1.4.1 Reed-Solomon syndrome decoder for DQI (SI I.1; Fig. 2 = `fig-rs-shared-update`; Fig. S1 = `fig-dqi-rs`; GU-REPO `tasks/dqi-reed-solomon/`)

Instance: identical to ours except the field polynomial (Gu: x^12+x^7+x^6+x^5+x^3+x+1 = 4331, `galois`
default; ours: 4179) and the mask (Gu: fixed SHA-256 mask with popcount 24,492; ours: fresh classical bits c
per test). Syndromes S_i = e(gamma^i), i = 1..70, same as ours. Baseline reconstructed from Khattar's Zenodo
code: 5,125,070 T / 1,938 Q, phases `init` 6,661, `eea` 1,904,770 (222 cycles + Forney flag), `sweep`
1,302,208 (4,095 points x ~306 T forward incl. one per-point Itoh-Tsujii-style division), `adjoint` 1,911,431
[GU-REPO khattar-eea README]. (Ours: 5,725,461 T / 1,893 Q with kickmix's 63-T multiplier and 315-T
inversion instead of Khattar's 51/255 — see `companion-paper.md` 3.3.)

Discovered circuit: **442,397 T / 1,837 Q**, 7 wrong signs in 1e5. Phase table [GU-REPO discovered README]:

| Phase | Toffolis | Share | Mechanism |
|---|---:|---:|---|
| `bm` (70 shared-path locator updates) | 141,071 | 31.9% | BM + routing + measured windows |
| `monicize` / `unmonicize` | 1,583 x2 | 0.8% | divide by sigma_0 (66-T inversion + mults) |
| `omega` / `omega_restore` (in-place sigma*S over 70 words) | 15,246 x2 | 6.8% | 363 middle products via eval/interp |
| `euclid` / `euclid_inv` (Psi = 1/sigma' mod sigma, half degree) | 44,470 x2 | 20.2% | fixed 17-block Euclid, quotients parked in cleared words |
| `sweep` (4,024 points x 23) | 92,552 | 20.9% | Chien by CNOT parities; 11-T zero test + 12-T gated bilinear form |
| `reverse` (69 BM rounds backward) | 86,176 | 19.5% | recomputes only what MBU erased |
| `init`, `zlin`, `cleanup` | 0 | | Z gates for the syndrome-linear mask part |

Tricks:

| # | Trick | Mechanism | Gain | Generalises? |
|---|---|---|---|---|
| R1 | **Berlekamp-Massey instead of synchronised EEA** for the key equation | 70 rounds, each touching only the active coefficient range; discrepancy = convolution with the next syndrome (Fig. 2d) | key-equation solve 1.9M -> 140k T (Fig. S1a) | Yes: any RS/BCH syndrome decoder; the cost is per-round work ~ active degree |
| R2 | **Retain/replace on one shared path by rescaling** | replace branch computes tau - alpha^{-1} sigma = -alpha^{-1}(sigma - alpha tau): same roots. CSWAP (sigma, z tau) and (Delta, delta) under the replace flag, multiplier w = alpha or alpha^{-1} chosen by a 12-T controlled select, one shared DIV + MADD (Fig. 2c vs 2b) | halves the per-round arithmetic and removes the displaced-template history (red registers in Fig. 2b) | Yes wherever an output is needed only up to a nonzero scalar (locators, projective coords) |
| R3 | **Invariant sigma_0 * delta = 1** | after rescaled replace sigma_0 <- alpha^{-1} sigma_0 = Delta^{-1}; retain leaves both; so delta is never stored, p = Delta sigma_0 = alpha is formed with one mult and inverted once; temporaries erased by MBU against identities p = Delta(tau_0+sigma_0)+[replace], Delta = [replace] sigma_0^{-1} | no persistent discrepancy register; replace rounds need no history | Instance-specific algebra but the pattern (derive a hidden value from a live register through an invariant) is principle 2 |
| R4 | **One-entry tagged stack** for retain rounds | only Delta != 0, d < 0 rounds must save Delta (12 bits + 7-bit round tag = 19 qubits); worst case 35 entries = 665 qubits; under the DQI weight law a 2nd entry is needed with prob 1.0e-4 (Fig. S1b hatched); 2 entries would cost +19 Q and +2,470 T (Fredkin moves) for 1.6% worse TQ | -646 qubits | Yes: any history stack whose depth distribution is measured |
| R5 | **Per-round coefficient cutoffs (`bm_windows`)** measured on 403M classical BM runs so every clipped slot carries < 4e-5 of the mass | worst case deg sigma <= min(r,35) but typical ~ r/2 (Fig. S1b); windows grow with r; failure 3.8e-5 | the rising-cost profile of Fig. S1a | Yes (also used for the Psi cofactor windows); needs an exact classical model of the circuit's own update |
| R6 | **Tie-breaking choice in BM** ("replace" when counts tie, allowed by Massey p.125) reduces stored history | more replace rounds, fewer retain pushes | fewer stack entries | Yes for BM |
| R7 | **In-place evaluator** omega = sigma S mod z^35 written over the first 35 syndrome words (triangular, reversible); extending the product to all 70 words zeroes the last 35 on a correct decode -> 420 free qubits for Euclid cofactors | monicise sigma first (sigma_0=1; if sigma_0=0 on an approximate path use scale 1 so the map is total); middle products by evaluation-interpolation: 363 variable products total | saves a 420-qubit omega register and supplies 421 qubits of workspace | Yes: triangular in-place transforms of read-only inputs |
| R8 | **Phase-only Forney via trace** | <c_j,e_j> = Tr(mu_j e_j); e_j = kappa_j omega(beta_j)/sigma'(beta_j); fold kappa_j and the residual mask into nu_j; never materialise e_j | the 12-bit quotient never exists | Yes for any "parity of a decoded symbol" output (this is exactly our contract) |
| R9 | **Syndrome-linear part of the mask applied with Z gates** | choose U(X) = sum_{i=1}^{70} u_i X^i agreeing with mu_j at 70 positions; sum_j Tr(U(gamma^j) e_j) = sum_i Tr(u_i S_i) is a fixed parity of syndrome bits | 71 positions dropped from the sweep (70 + one accidental zero), 0 Toffolis | Yes; with a per-test classical mask the u_i are F2-linear in c (Vandermonde solve offline) [INFERENCE: see Sec. 6.2] |
| R10 | **Precomputed reciprocal Psi** with Psi sigma' = 1 mod sigma; **half-degree split** sigma = E^2 + z O^2 (char 2: sqrt is linear, sigma' = O^2), EEA on (E,O) of degree <= 17 gives A E + B O = 1, Psi = B^2 + z A^2 | division once per shot instead of per point; EEA cost ~quadratic in degree so halving degree quarters it | sweep 321,920 -> 92,552 T; Euclid 44,470 each way | Yes: any "divide only at roots" situation over char-2 fields |
| R11 | **Fixed-schedule Euclid**: shift (E,O) by m = floor((35-L)/2) words so deg E' = 17 always (m read from the BM counter bits); 17 blocks of two eliminations; each block: top-word nonzero test, CSWAP halves, one pivot inversion, two quotient coefficients, one eval/interp product; the two cleared top words equal quotient x pivot so **measurement erases them for free and the quotients move into the cleared words** | no history for the Euclid pass; zero-pivot (degree drop by 2, 0.36% of shots) handled by one controlled rotation + 6-bit record; a second zero pivot (4.5e-6) is a failure | Yes: "park the quotient in the word it clears" is the Proos-Zalka/Kaye-Zalka idea pushed to a fixed shape |
| R12 | **Sweep without rotating words**: at point gamma^t read every operand as a fixed parity of the stored (unrotated) words; root test = XOR of 36 locator words is zero (11 T), pairing = rank-12 bilinear form gated by the root flag (12 T) | 23 T/point; Clifford count differs only; whole sweep recorded as one data-gated `repeat` body | | Yes: Chien search by parity reads; our `gf2_imul(const)` is already CNOT-only |
| R13 | **42-Toffoli GF(2^12) multiplier** = bilinear rank 42: view as 6-term polynomial product over GF(4), evaluate at the 4 GF(4) points + infinity and mod three irreducible quadratics -> 14 GF(4) products x 3 T; GF(64) 15 T, GF(8) 6 T | vs 51 (Khattar) / 63 (kickmix `init_gf2_mul`) | Yes: representation-independent up to free CNOT basis change (participants already use rank 42, `participants.md`) |
| R14 | **66-Toffoli inversion by tower norms**: N = x xbar in GF(64) (15 T), M = N Nbar in GF(8) (6 T), M^-1 = (M^3)^2 (3 products + free squaring), N^-1 = Nbar M^-1 (12 T), x^-1 = xbar N^-1 (30 T); zero maps to zero without a branch | vs 255 (Khattar) / 315 (kickmix `init_gf2_inverse`) | Yes; a one-level tower would need a generic GF(64) product |
| R15 | **Measurement-erase every bilinear product** whose factors stay live (X-measure + classically conditioned CZ "claims"); reverse pass recomputes only what was erased | `reverse` (86k) < `bm` (141k) | Already a kickmix primitive (`del_gf2_mul` = 0 T) |

Failure accounting (GU-REPO): cutoff crossings 3.8e-5 + stack overflow 1.0e-4 + second zero pivot 4.5e-6
~ 1.4e-4 aggregate (7x under their 1e-3 allowance); failures are wrong phase or (on some overflows) a dirty
bank qubit; the syndrome is always restored. Peak 1,837 occurs in `euclid/seed`, `euclid/R`, `euclid_inv/R`.

#### 1.4.2 Hermitian-code decoder for HOPI (SI I.2) — less relevant, listed for completeness

Locator as null vector of the symmetric 48x48 matrix A_{kk'} = S(psi_k psi_k') never stored; apply A by
**evaluation-interpolation** (Phi^T diag(eta) Phi u: 123 pointwise GF(64) products x 15 T = 1,845 T);
**Lanczos** three-term recurrence builds the null vector while basis vectors are live; block-Lanczos repairs
of self-orthogonal breakdowns concentrated in 17 scheduled **repair rounds** (ordinary round 5,400 T, depth-2
repair 12,000, depth-3 17,000) with the walk frozen in between (principle 3); walk reversal measures the
locator register and corrects phases with CZs, stores one bit per round (52); phase scan in 24 **stripes** of
16 points recomputing omega per stripe by eval/interp (3,090 T/stripe) instead of storing >100 symbols; GF(64)
division via GF(8) at 33 T/point. 1e8/1.9e5 -> 930,000 T / 2,395 Q, 30 wrong signs in 1e5.

#### 1.4.3 Numerical functions: HHL arcsin, Coulomb 1/sqrt, Gaussian (SI III; Fig. S-`hhl-spine`; GU-REPO READMEs)

Baselines are tuned Haener-Roetteler-Svore piecewise polynomials (arbitrary interval boundaries ->
comparisons; Horner with general fixed-point multiplies; registers for products and value; reverse pass).

| # | Trick | Mechanism | Where / gain | Generalises? |
|---|---|---|---|---|
| N1 | **Dyadic (power-of-two-aligned) leaves** selected by input prefixes; unary-iteration tree lookup ~1 Toffoli per internal split (343 T for 345 leaves) | interval membership = prefix test; finer partition lowers degree: HHL cubic->quadratic with 345 leaves of width 2^8..2^15 (uniform would need 7,936); Coulomb quadratic->128 lines; Gaussian 1,024 segments of width 2^-7 | HHL 16,468/300 -> 1,348/115; Coulomb 6,355/252 -> 1,140/142; Gaussian 23,784/362 -> 1,583/139 | Yes: this is the public invsqrt frontier's structure too ("256 (e,a) segments", `participants.md`) |
| N2 | **Shared local coordinate by cyclic rotation** of the low 15 input bits by sh = 15-b (three controlled rotations by 1,2,4 = 42 CSWAPs each way); wrapped fixed bits c_L are absorbed into the coefficients offline | no subtraction X-L, no rescaling, no coordinate register | HHL (`rotate`/`unrotate`) | Yes when leaf widths differ |
| N3 | **Booth radix-4 signed digits** d_t = y_{2t-1}+y_{2t}-2y_{2t+1} in {-2..2}: 13-bit multiplier -> 7 rows, 5-bit curvature -> 3 rows; one AND per digit for the |d|=2 selector; conditional complement for negatives | HHL digit rows 643 T total; Gaussian 6 + 9 rows | Yes for every truncated multiply (our Horner/NR multiplies) |
| N4 | **Direct accumulation**: t <- g_1 - g_2 d stored over the slope word, then k <- k + g_0 - d t straight into the accumulator; never form d^2, x^2, a product, or the value | HHL `vcompute`/`product`; Gaussian "changing slope" form s' = s + sum floor(u_t c 2^{2t-15}), k <- k + 2^7 a_0 - floor(s' D / 2^21) | removes 2-3 registers | Yes |
| N5 | **Truncation schedule per row** chosen by search (HHL B=[4,5,5,5,6,6,6], shifts sig=[13,12,10,8,7,5,3]; Gaussian per-row cutoffs with a conditioned rounding bit that centres the truncation error) | fitted coefficients absorb the residual | | Yes; needs the exact integer model |
| N6 | **Backward fitting through the exact integer pipeline**: start from the allowed output band, pull it back through rescaling/rounding to admissible intermediate sets A(n_2), intersect over inputs sharing an address, search slopes outward from the analytic derivative, split on failure (Coulomb `fit/build`); HHL fit-time bound 428.5 of 429 units; Gaussian least squares on 129 nodes then 20 quantised variants/segment, grid of 15,552 knob tuples ranked by *built-circuit* TQ, accept the first passing the exact scan | "uses error wherever the actual circuit permits it ... does not reserve independent margins" | all three | Yes — this is the single most transferable methodological point for Benchmark I's k=0 contract |
| N7 | **Exhaustive certification** (`checks.py`): all 2,031,616 HHL inputs; all achievable squared distances; aligned-stretch endpoint scan over 2^25 coordinates per Gaussian segment using monotonicity | fit sampled, proof exhaustive | | Yes (our I has 3.1M inputs: trivially exhaustive) |
| N8 | **Measurement-based unlookup + one batched phase repair**: X-measure coefficient words when done (intercept right after its add; slope/curvature after reverse rows restore them); repair all (-1)^{m . d(a)} phases in one address walk: HHL upper tree to level 12 (182 T) + 5-bit one-hot bank (30 T) = 212 instead of 343; Coulomb 3 high bits walk (6 T) + Reed-Muller monomial bank over 4 low bits (11 T) = 17 instead of 126; Gaussian 14 + 36 = 50 instead of 495 | repair cost scales with address entropy, not word width | all three | Yes; kickmix `del_lookup` is this primitive — check its repair cost (see `kickmix.md`) |
| N9 | **Content-pruned QROM** (variable-spaced QROM of Sanders et al. 2020): stop the walk when a subtree is uniform; Gaussian 455 quadratic + 59 constant (22 runs) + 510 zero segments -> 1,022 -> 495 T | | Gaussian | Yes: any table with repeated/zero words (Benchmark III!) |
| N10 | **Free fold**: complement instead of exact |x| (no +1 carry chain), charge <= 0.858 output units to the error ledger | CNOT-only | Gaussian | Yes where an off-by-one is inside tolerance |
| N11 | **Carry-mode dial per position**: measured carry = 1 T + 1 live qubit; in-place (Cuccaro MAJ/UMA) = 2 T, 0 qubits; hybrid adder with measured-carry prefix (HHL prefix 11; intercept adder 41 T); choose under a **live-qubit cap** (HHL cap 117 chosen by full sweep: +64 T, -12 Q); Coulomb uses an ancilla-free Cuccaro adder for the final accumulate because ~23 carry ANDs would exceed headroom | TQ-optimal mix | all | Yes; kickmix `iadd` has clean/dirty variants (`kickmix.md`) |
| N12 | **Exponent-free normalisation**: four zero tests on 8/4/2/1 leading bits + CSWAP shifts; the four flags encode shift and parity (no exponent register); cap the shift and **patch** the 3 tiny inputs with 2 ANDs | Coulomb | | Yes (our baseline uses a 10-flag thermometer and 110 CSWAPs each way) |
| N13 | **Packed squared distance**: terms of d^2 grouped into four sparse integers with <= 1 term per column; 11 ripple adds with "carry ceiling" (stop at the highest reachable bit); exhaustive DP over emission order (135 vs 141 ANDs) | Coulomb `squarer` | | Irrelevant to I (w is given), but the scheduling DP idea generalises |
| N14 | **Reuse freed coefficient wires** as carry ancillas / one-hot rail; borrow input wires that are provably zero after the fold (Gaussian X_35..37) | Q 362 -> 139 | | Yes |
| N15 | **Phase-gradient target**: additive form serves both an accumulator and a phase-gradient register | | | Our I phases with Z_POW per output bit; same additive structure |

#### 1.4.4 Fe2S2 alias table + SELECT (SI IV; Fig. S-`fe2s2-blocks`; GU-REPO `chemistry-fe2s2`)

Task: U_alias^dagger SELECT U_alias for L = 41,052 Pauli terms (16-bit bucket i, 16-bit tau, 40 system
qubits; 34-bit alias word = 16-bit keep + 16-bit alt + 2 signs). Baseline 55,473 T / 139 Q (lookup 13,000
with merged repeated words, SELECT 41,000). Discovered 14,978 T / 126 Q.

| # | Trick | Mechanism | Gain | Generalises? |
|---|---|---|---|---|
| Q1 | **Melt scheduling** of the alias table: pairing freedom (which underfilled bucket a heavy term donates to) spent on making adjacent rows byte-identical (A,A,B,B not A,B,A,B); 18,463 of 20,374 spin-paired rows identical | exact (distribution unchanged) | | Yes: **any time we control the address->data map** (Benchmark III address map, angle ordering) |
| Q2 | **Repeated-span pruning**: skip an address bit when both halves of a subtree hold identical word sequences; out-of-domain leaves chosen to complete agreements | 41,050 -> 10,271 T | | Yes |
| Q3 | **Frame blocks for SELECT**: Pauli rows related by fixed commuting Clifford frames F_1..F_k are generated from one representative with k address bits controlling the frames; 7 frames, 3,221 blocks, 14 contiguous regions; walk representatives (3,327 T) + frame apparatus (534 T) instead of 41,050 | SELECT 12x cheaper | | Chemistry-specific (spin symmetry, site reflections); not applicable to III's angle oracles |
| Q4 | **Controlled quadratic phase = rank(B)/2 CCZs**: polarisation matrix of the Boolean quadratic form, CNOT change of coordinates to a symplectic normal form; e.g. frame C 19 -> 10 CCZs | exact lower bound reached | | Yes for any controlled Clifford/phase polynomial |
| Q5 | **Z-gauge search** over sign redistribution between representative and frames (769 -> 117 T) and placing 7 recurring sign monomials on existing walk controls (-> 108) | | | Yes: fold phases onto controls you already pay for |
| Q6 | **Joint unlookup**: XOR the Boolean phase functions of several measured banks classically and repair with one address traversal (642 windows of 64 rows, 16-slot one-hot rail + Reed-Muller planes: 15 + 767 T) | one repair instead of two | | Yes |
| Q7 | **Hold-budget dynamic program**: at every node of the fixed lookup/repair trees choose keep-path-AND-live vs recompute (shared split wire / accumulator forms as intermediates), minimising exact temporary-AND count under a qubit ceiling; lookup saturates at 15 live holds, repair at 11 | Toffoli-optimal within the ceiling | | Yes: directly applicable to `unary_iteration`-based lookups under the 128-qubit cap of III |
| Q8 | **Borrow-chain comparator** with all 16 borrow ANDs temporary (measured), 64 T for two comparators + two 16-bit CSWAPs | | | Yes |

#### 1.4.5 Prime-field modular inversion / point addition (SI II; Fig. 3 = `fig-divstep`; Fig. S-`modinv-walk`; App. A)

| # | Trick | Mechanism | Gain | Generalises? |
|---|---|---|---|---|
| M1 | **Divsteps** (Bernstein-Yang) as the inversion recurrence: counter z, f odd, g halved; no comparisons, no quotients; (z,f,g,f_v,g_v) updates of Eq. `divstep-recurrence` | each step cheap; 533 steps | | Needs prime-field integers; not our setting |
| M2 | **Exact branch recovery** (App. A, Lean-proved): swap visible as v_2(f_v')=1; nonswap with z'>=1 => b=0; g'=0 => b=1 (two thirds of decisions); ambiguous ones decoded from b = bit_{j-1}(g_v' q^-1 mod 2^j) via the window invariant g_v = q c mod 2^{j-z}, c < 2^j; depth-j decoder is a 2(j-1)-bit Boolean function (3/3/11/26 SOP terms at j=2..5, 79/268/1,092 at 6..8) | principle 2 at scale | | The *method* (prove an invariant, compile decoders as truth tables, cut off at j_store) generalises |
| M3 | **Decode/store cutoff** j_store = 5: 50.1/25.0/12.5% of ambiguous decisions at depth 2/3/4, 12.4% stored; 198 -> 60 history qubits; frontier 3.3M/1,191 ... 7.9M/893 | tunable T-Q trade | | Yes |
| M4 | **Stopping-time window**: 533 scheduled steps, termination test (zero test on g + control on every update) only from step 499; walks ending earlier fail (1.4e-6); z-register overflow 9e-8 | principle 3 | | Yes (our EEA step budget) |
| M5 | **Scale removal without a counter**: r = a f f_v = 2^t a w^-1; attach one modular halving of r to each *active* reverse step (frozen flag marks active) -> r = a w^-1, no record of t | avoids counting t and a controlled 2^-t multiply | | Yes where a data-dependent power of 2 accumulates |
| M6 | **Step-dependent packing**: g and f_v share one 256-bit register, f and g_v the other (shrinking value and growing coefficient from opposite ends; widths fixed per step at build time) | 1,024 -> 512 register qubits | | Yes (this is Proos-Zalka register sharing; our baseline already does it for polynomials) |
| M7 | **Fused coordinate arithmetic**: lambda^2 as three 128-bit-half products added one at a time into the coordinate register; sparse prime fold 2^256 = 2^32+977 applied while forming each product; truncated carries (58/60 bits, 2^-26 per reduction) and 27-bit comparisons | avoids square register and a second multiply | | Pattern generalises |
| M8 | **Specialised packed Euclid** (Luo et al.): fitted windows per step, schedule cut 1,616 -> 1,432, test-free positions (counter tests cost ~10 T/position), merged scans sharing comparison bits erased by measurement, renumber positions instead of moving qubits, measured carries | 69.5M -> 20.5M T at +5 Q (Fig. S-modinv-walk d: cumulative ablation) | | **Yes — this is the closest analogue to our pointer-driven EEA baseline (Sec. 6.2)** |

Failure union bound for point addition (Table S-`divstep-failures`): multiplier carry/comparison 7.07e-5,
stopping/integer size 7.56e-5, early-stopping/z 6.18e-6, history 6.8e-6, fused-square carry 6e-7; total
1.6e-4 < 2e-4; 4 fails in 1e5 tests. Toffoli split: four walks 2.5M (63%), field mults 1.4M (35%), fused
square + adds 0.1M. Comparison table (Table S-`modinv-frontier`): Schrottenloher 1.9e6 T / 1,446 Q; divstep
4.0e6 / 935; Luo 7.0e7 / 838; specialised Euclid 2.1e7 / 843.

#### 1.4.6 Nonabelian lattice gauge (SI V) — pattern only

Representation change (X -> X_o = CEX so the V,X_o part closes on itself), **different factor orders for the
running product and the incoming link** so combinable factors are adjacent, store P~ = P + QR to fold
recurring corrections, **one-hot encoding of the single hot register's mod-3 coordinates** (add = cyclic
permutation, negate = swap, controlled ops = controlled permutations): 146 -> 35 T per update; **reuse the
running product** across loops via cyclic/inversion invariance of the trace with a classical DP over
representatives (5.4 vs 6-10 multiplications per loop); **read the 7-valued trace directly as six flags**
(20 T) controlling additions of known constants instead of a 216-entry 51-bit QROM (478 -> 76 T).
1.3e6/1,927 -> 170,000/1,859.

### 1.5 Before/after tables

Main Table I / ED Table 1 [GU]:

| Task | I/O qubits | Tolerance | Tests | Baseline (T,Q) | Ours (T,Q) | G_TQ |
|---|---|---|---|---|---|---|
| Prime-field modinv (point add) | 512/512 | fail <= 2e-4 | 1e5 | (see frontier table) | (4.0e6, 935) | — |
| RS DQI decoder | 840/— | fail <= 1e-3 | 1e5 | (5.1e6, 1,938) | (4.4e5, 1,837) | 12 |
| Hermitian DQI decoder | 738/— | fail <= 1e-3 | 1e5 | (1.0e8, 1.9e5) naive | (9.3e5, 2,395) | — |
| HHL rotation angle | 21/33 | < 1e-7 rad | 9e3 | (1.6e4, 300) | (1,348, 115) | 32 |
| Coulomb potential | 48/25 | <= 2e-6 abs | 9e3 | (6,355, 252) | (1,140, 142) | 9.9 |
| Fixed-point Gaussian | 39/39 | < 1e-7 abs | 9e3 | (2.4e4, 362) | (1,583, 139) | 39 |
| Fe2S2 alias-SELECT | 32/40 | exact | 2e7 | (5.5e4, 139) | (1.5e4, 126) | 4.1 |
| Nonabelian lattice gauge | 1,728/51 | exact | 1e5 | (1.3e6, 1,927) | (1.7e5, 1,859) | 7.7 |

Certified repo values [GU-REPO results.jsonl]: RS 442,397/1,837 (TQ 8.13e8) vs 5,125,070/1,938; HHL
1,348/115 vs 16,468/300; Coulomb 1,140/142 vs 6,355/252; Gaussian 1,583/139 vs 23,784/362; Fe2S2
14,978/126 vs 55,473/139.

### 1.6 Negative results, failure modes, limitations [GU]

- Costly things kept because the alternative is worse in TQ: reconstructing retain-round discrepancies is
  possible (rule Delta = [z^m](sigma' Q^-1)/sigma'_0, verified on 7,527 pushes) but would cost ~7.7k T to save
  19 Q -> not done; a 2nd stack entry rejected (+1.6% TQ); decoding depths >= 5 in divsteps rejected (terms
  triple per depth, history halves); HHL cap tighter than 117 does not lower the peak (other moments bind).
- Approximate paths can leave a dirty bank qubit (tag overwritten on stack overflow) — counts as failure.
- Hermitian: dependent conditions 8e-8; walks not finished after 52 rounds fail; lambda_0 != 0 fails.
- Their framework excludes encoding changes (coset representations) and Z_POW; objective is TQ only; task
  boundary/input distribution/accuracy target bake in assumptions ("which states it receives and how its
  outputs are consumed").
- Discussion: "some apparent costs of quantum arithmetic reflect limitations of existing reversible
  constructions rather than of the algorithms themselves"; benefits of changes "depend on one another" so a
  design must be "carried through several unresolved mathematical and implementation problems before its
  resource advantage becomes apparent" (motivates families + non-monotone archive).
- Stated future work: hardware-aware objectives (Q^kappa T, active volume, depth), end-to-end co-design with
  QEC/magic-state layers, applying to any problem with an expressive task interface and cheap evaluation.

---

## 2. Long et al., arXiv:2609.28882 (+ challenge report 2609.09582) — ecdsa.fail

### 2.1 Setting and evaluator [LONG Sec. 3; ECDSA-REPORT Sec. 4-5]

secp256k1 mixed point addition |x_R>|y_R> -> |x_R'>|y_R'> with classical addend (p = 2^256-2^32-977);
restricted kickmix model (reversible gates, diagonal phases, reset, destructive X-measurement with
feed-forward; "unrestricted Hadamard and persistent |+> excluded"); score S = Q x T with Q = max qubit id + 1
and T = **mean executed** CCX+CCZ over 9,024 SHAKE256(circuit)-derived inputs; checks cls/anc/pha; a
"free 96-gate identity tail (`DIALOG_TAIL_NONCE`) reseeds those shots" [HARNESS] -> **nonce grinding** for a
favourable "island" is part of the game (the manuscript separates static counts from sampled execution and
uses frozen 100,000-input fresh studies for its claims).

### 2.2 Tricks [LONG Sec. 4-5; ECDSA-REPORT Sec. 5.3 and Appendix "Anatomy"; HARNESS skills]

| # | Trick | Mechanism | Numbers | Generalises? |
|---|---|---|---|---|
| L1 | **Record-and-replay (dialog) GCD** (Khattar et al. -> Schrottenloher): record per-round control symbols on the value walk, replay the transcript on (0,y) to get y x^-1 (linear map D_x), reverse the walk to clear | architecture of every top circuit | Yes: our RS EEA is the polynomial version |
| L2 | **Jump-2 macro-steps**: fold the mandatory halving plus a possible second halving into one recorded step; symbol (b,s,s_2) has only 5 reachable patterns -> **base-5 codec** packs 3 symbols into 7 qubits (2+86x7+5 = 609 vs 783) streamed into space freed by shrinking operands; 258->261 steps cut nonconvergence 2.8e-4 -> 2.9e-5 | historical best 1,151 Q / 1.299M T | Yes: compress transcripts over reachable alphabets |
| L3 | **Ping-pong GCD** (plus-minus GCD + dialog): keep both operands odd, alternate target register on a fixed schedule, decide add vs subtract from the two low bits (e = t[1] xor s[1]), t' = (t +- s)/2; one transcript bit per round, no full-width comparison, no data-dependent swap | GCD value updates 633,994 -> 395,368 static T; backend swap at fixed square -340,442 T, +171 Q (Table `mechanism-ablation`); mixed circuit 1,321 Q / 952,719 T | Yes in prime fields; the "fixed alternation + 1-bit decision" idea also suggests fixed-schedule polynomial EEAs [INFERENCE] |
| L4 | **Fused modular replay**: retain doubling overflow and addition carry, one correction kappa F (kappa in {-1,0,1,2}, F = 2^32+977 sparse so supplied bit by bit) instead of two; carry measured and phase-corrected | 446 -> 393 T per inverse cell (+1 workspace qubit); 56-bit correction window (approximate) | Yes: fuse adjacent modular ops sharing a correction |
| L5 | **Zero-payload repair**: record h = [c != 0], mask replay signs by h, uncompute from the output zero predicate; exact chunk-carry predicate [z<a] or (c_in and [z=a]) | removes phase defects on zero/zero-slope inputs; 1,419 Q / 1.356M T, 0/100,000 | Lesson: representation (zero as word p) and omitted equality terms cause *phase* errors that classical checks miss |
| L6 | **Streamed Karatsuba square** with 2^256 = 2^32 + 977: compute c_2, a_2, b_2 in turn, accumulate -beta c_2, -a_2+beta a_2, beta b_2 - F b_2 into X and uncompute each before the next; F = 2^32+2^10-2^5-2^4+1 (NAF) | no 512-bit product register | Yes |
| L7 | **Materialise classical data only where used** (3x_A computed as x_A + 2x_A then unloaded; classical fold of constant arithmetic into free bit ops: coord_add3x 754 -> 326 T) | | Yes (kickmix classical `iadd` offsets) |
| L8 | **Split-address MBU lookup cleanup**: measure payload, decode low/high address halves into one-hot, CZ per row needing a flip, reverse decoders; C(w) = 2(2^floor(w/2)+2^ceil(w/2))-4 = 1,020 T at w=16 | three unloads 164,090 -> 3,060 T; -9.56%/-12.5% mean T, Q unchanged (Table `exact-cleanup-effects`) | Yes — same as Gu N8 with a 2-level split instead of a tree+rail |
| L9 | **Constant propagation** over the op stream ({0,1,unknown} + affine relations): known-0 control -> drop, known-1 -> CX, equal controls -> CX, complementary -> drop; `single_ccx_fanout` identity CCX(a,b,t);CX(t,u);CCX(a,b,t) = CX(t,u);CCX(a,b,u) | the dominant late-stage Toffoli lever; "dead-code elimination" family gets 39% of attributed frontier improvement | Yes: a peephole pass on `.kmx` streams [INFERENCE: worth building] |
| L10 | **Measured uncompute / phase-conditioned replay** (Levers B, H): HMR a cleanup or comparison flag, replay the predicate classically conditioned to cancel the phase | -387 T, -2,597 T etc.; "the cleanest class" | Yes (kickmix `del_and`, `hmr` + conditioned CZ) |
| L11 | **Measured-fast adders on non-peak adders**; asymmetric 2-block windowed adders (small low block + wide fast high block) | -1,434 / -2,124 exec T | Yes (= Gu N11) |
| L12 | **Exact adder can beat truncated adder** (truncation needs carry-escape logic) | -2,597 T, fewer hard inputs | Yes: audit every truncation |
| L13 | **NAF / signed-digit recoding of constants**; majority identity maj(a,k,c) = c xor ((a xor c)&(k xor c)) | fewer passes | Yes |
| L14 | **Peak reduction levers** (HARNESS peak skill): free-and-recompute idle ancillae across the widest region (1220->1218); range-bound a register to delete a guard bit by reordering adds before subtracts (1221->1220); segment the peak-binding operation and co-descend all co-binders; keep-alive when recompute transiently widens; in-place decode of compressed blocks (1218->1215); borrowed carries from live zero scratch | | Yes, all mechanical and apply to our Q-weighted scores |
| L15 | **Windowed Solinas shift**: replace 22 no-op double-and-correct iterations by one swap shift + spill register + sparse correction | exact | Pattern: batch no-op stretches |
| L16 | **Dead-CCX index drop** (charged-but-inert gates whose quantum controls never both fire on the island) | island-exact; superset of constprop | **Not transferable honestly**: relies on a fixed sampled island |

Attribution (ECDSA-REPORT appendix "score-weighted view"): the 70 largest deltas carry 91.6% of the gross
reduction; structural families (register/scratch allocation 21%, fusion 18%, windowing 13%, uncompute
strategy 8%) get ~60% across only 26 commits; dead-code elimination 39%; algorithmic substitution,
codec/encoding and constant propagation "essentially no delta" on the scalar frontier.

### 2.3 Before/after tables [LONG]

Fresh frozen study, 100,000 inputs, 9 lookup tables, w = 16 (Table `fresh-operating-points`):

| Windowed circuit | Q | T (M) | QT (B) | failures | 95% upper |
|---|---:|---:|---:|---:|---:|
| Ping-pong original (704 rounds) | 1,338 | 1.128 | 1.5086 | 39 | 0.115% |
| Ping-pong conservative (736 rounds, wider guards) | 1,392 | 1.253 | 1.7440 | 0 | 0.0030% |
| Jump-2 (261 steps, 609-qubit transcript) | 1,162 | 1.523 | 1.7699 | 215 | 0.353% |
| Ping-pong zero-payload repair (768 rounds; separate study) | 1,419 | 1.356 | 1.925 | 0 | 0.0030% |

Static ledger (Table `mechanism-static`, windowed): GCD value updates 633,994 / 395,368 / 439,196; replay
setup 22,526 / 828 / 956; ordinary field replay 704,939 / 551,772 / 670,876; transcript codec 6,378 / 0 / 0;
squaring + slope masking 55,668 / 64,968 / 64,968; coordinates ~4k; lookup + address control 167,208 each;
totals 1,593,346 / 1,184,131 / 1,347,296 (Jump-2 / original / conservative ping-pong). Peak ledger: payload
512 + tape 704-736 + values 16-22 + carries 88-104 + controls 18.

External context (Table `external-pa-comparison`): Google low-gate <= 1,441 Q / <= 2.297M; Schrottenloher
low-gate 1,462 / ~2.06M; conservative ping-pong 1,392 / 1.253M ("70 fewer qubits and ~39% less counted
work" but "differing accounting and correctness evidence preclude formal dominance").

Full-width references (App. "safegcd"): safegcd 741 rounds 3,300 Q / 7.50M T 0/128; ping-pong 768 rounds
2,320 Q / 6.29M 12/128; ping-pong 1,536 rounds 3,088 Q / 12.57M 0/128.

### 2.4 Negative results and failure modes [LONG Sec. 7, App.; ECDSA-REPORT; HARNESS LESSONS]

- **Finite schedules are not justified**: ideal ping-pong needs up to 3n(n+1) = 197,376 rounds in theory;
  denominators 1, 3, 2^255 need 512/1,135/1,239 transitions and violate tapered widths; 10M-denominator study:
  mean 621.5, max 743; exceedances 1,535/6/0/0 at 704/736/768/800. Random-input cleanliness != correctness.
- **Phase defects invisible to classical checks**: zero encoded as word p, omitted equality term in the chunk
  carry predicate, final-y subtraction; found only by separate pha/anc channels and targeted witnesses.
- **jump=4 refuted** (HARNESS toffoli skill): value-correct but +32-67% T because each controlled shift is a
  CSWAP billed as a Toffoli by its classical condition regardless of firing; wider swap comparator; modelled
  -14% missed three real costs. Lesson: *cost model lens* — in kickmix too, `cswap` on qubits is 1 Toffoli per
  pair, `cswap` under a classical bit is free (`kickmix.md`).
- **Sampling cannot certify value-exactness** (a control that fires 1 in 1e6 passes 1e6 shots); only static
  proofs (liveness, algebraic identity). "mod-q-correct is not circuit-correct" (non-canonical representatives
  consumed bit-exactly downstream).
- **Nonce grinding** of the Fiat-Shamir seed selects favourable islands; the paper treats 9,024-case passes as
  "benchmark-valid, not all-input correctness" and demands frozen holdouts. Kaggle's salted hash removes this
  axis for us (`competition-notes.md`), which also means island-exact truncations (L16, carry notches) are
  only usable if they survive *random* inputs at the contract's failure budget.
- **Search-and-distill failed**: training a smaller model on evaluator-generated low-cost correct subcircuits
  plateaued; "tool access and evaluator-guided iteration may be more important than scaling a model trained to
  reproduce a fixed procedure".
- **Literature transfer missed**: no agent transferred Khattar's dialog-GCD to ECDLP until Schrottenloher's
  paper appeared (days after launch); "cross-domain retrieval and abstraction" flagged as the capability gap.
- A mature peak is a multi-binder floor; "it looks idle" is not a proof; a wider window (jump) can lose.
- Open per the authors: canonical replay at competitive cost, justified widths and round tails, optimised
  reversible safegcd baseline, certified good subspaces for the composition bound.

---

## 3. One-hop citation trail (what else reports AI/agent-found circuits)

| Source | Relevance | Notes |
|---|---|---|
| Khattar et al. 2510.10967 "Verifiable quantum advantage via optimized DQI circuits" | **Our Benchmark II baseline** (5.72M T, 1,885 Q decoder; 51-T multiplier) | not AI-found; Gu reconstructs it at 5,125,070 T / 1,938 Q from Zenodo code |
| Babbush et al. 2603.28846 (kickmix, PRX Quantum 7, 031001) | defines the model and the ECDLP benchmark; Gu's modinv failure budget and 28-call window algorithm come from it | ZK-attested costs only |
| Schrottenloher 2606.02235 "Optimized point addition circuits for ECDLP" [WEB abstract] | explicit circuits matching Babbush (+1.5% Q, -6.5..10% T); dialog-GCD adaptation that the ecdsa.fail agents then implemented | human |
| Luo et al. 2607.13816 "Space-efficient point addition" [WEB abstract] | packed EEA inversion, 835 Q total; **Gu specialises it 3.4x in Toffolis (M8)** | human; closest to our Proos-Zalka EEA |
| Gu, `uncompute` Lean proofs (`gu2026lean`) | machine-checked divstep decoding rule and DQI error bound | LLM "developed it into a proof" per main text |
| Macarone-Palmieri & Lo Franco 2602.03466 "Quantum circuit generation via test-time learning with LLMs" [WEB abstract] | memory-augmented LLM black-box optimisation of **Meyer-Wallach entanglement** of 20-25-qubit circuits; episodic memory + score-difference feedback + restart-from-best | not reversible arithmetic; the loop ingredients (memory of high scorers, feedback deltas, restart from best) echo [GU] |
| Liang et al. 2307.08191 (QGAS) | LLM proposes variational ansatz architectures | not relevant |
| AlphaTensor-Quantum (Ruiz et al., Nat. Mach. Intell. 2025; arXiv:2402.14396) [LONG cites; WEB] | RL over tensor decompositions to minimise **T-count** of Clifford+T circuits, incl. arithmetic (binary field multiplication, Shor components); plus a 2025 reusability report (arXiv:2511.09951) | relevant precedent for "bilinear-rank" style multiplier search (Gu's 42-T GF(2^12) multiplier is a rank search by hand/CRT); not kickmix |
| FunSearch / AlphaEvolve (Romera-Paredes 2024; Novikov 2025) | the evolutionary-program-search template Gu adopts via OpenEvolve | no quantum-arithmetic results in the cited versions; a 2025 AlphaEvolve application generates Trotter circuits for a nuclear-spin molecular-geometry paper (2510.19550) [WEB] |
| Su et al. 2305.06378, Olle et al. 2024, OmniQEC 2607.25865 | RL/LLM discovery of QEC codes and encoders | cited by Gu as motivation for end-to-end co-design; not circuits |
| **Gemini 4 Argon** (Google blog, 13 Oct 2026; Kohli/Neven posts) [WEB] | "For arcsin, a building block in recent quantum simulation algorithms, an implementation written by Argon and formally verified in Lean cuts spacetime cost by more than 100x compared to a published quantum CORDIC baseline" (baseline = Burge & Barbeau 2411.14434 "Quantum CORDIC - Arcsin on a Budget") | **no circuit, metric or numbers published**; same task class as Gu's HHL arcsin (32x TQ vs HRS) and as our Benchmark I; Google Quantum AI is the competition host, so their withheld internal Benchmark I/II/III runs likely used this toolchain [INFERENCE] |
| Jang, Kim, Seo, Chattopadhyay, ePrint 2026/1446 [WEB] | LLM guided by a structured optimisation-technique list produces cipher circuits (CRAFT, MANTIS, QARMA) minimising qubits or Toffoli depth, checked by test vectors | agentic, reversible logic, but no kickmix/MBU; no numbers extracted |
| ecdsa.fail harness repos: `jieyilong/ecdsafail_skills`, `ecdsafail_gpu_toolkit`, `BitWonka/ecdsafail-tools`, `trailofbits/trailmix` | skills, dead-CCX finder, GPU nonce hunt, TrailMix shrunken-PZ inversion (1,050 Q / 32M T) | tooling; the skills' *structure* is reusable (Sec. 7) |
| `tatra-labs/kickmix-arena` | open evaluator for Gu's tasks | see `participants.md` |

Nothing else in either bibliography reports concrete agent-found kickmix results. The companion Kaggle paper
2610.23832 gives none (see `companion-paper.md`).

---

## 4. Our baselines vs. what the agents started from

| | Benchmark I (invsqrt) | Benchmark II (dqi) | Benchmark III (dfthcsos) |
|---|---|---|---|
| Our reference | Q 260, 7,735 T + 37 rotations, C 7,988, score 2.08e6 | Q 1,893, T 5,725,461, R 1.191, score 2.44e13 | lambda_eff 49.30, T 93,237, Q 730, score 3.36e9 (`participants.md`) |
| Our score | Q x (Toffoli + T/4), k = 0 over 3.1M inputs x 64 shots | R(eps+) x Q^2 x T, 102,400 shots | lambda_eff x T_tot x Q_tot, exact, <= 128 Q per ANGLE circuit, no Z_POW |
| Gu's nearest task | HHL arcsin (21-bit in, 33-bit out, 345 dyadic leaves, 1,348 T / 115 Q) and Coulomb 1/sqrt (1,140 / 142) | the same RS instance: 442,397 T / 1,837 Q (TQ), 1.4e-4 failures | Fe2S2 alias QROM (14,978 / 126) and the Gaussian/HHL content-pruned lookups |
| Public frontier (early Nov, `participants.md`) | 62 Q / 1,325 T / 41 rot, cost 100,568 (**20.65x**): signed-digit centred quadratic per 256 (e,a) segments, QROM coefficients, derivative split, virtual low bit, LP-calibrated angles | 892 Q / ~404k T (**63-64x**): Hankel/Schur in-place continued fraction of S(z), rank-42 multiplier, classical mask projection, rare-branch approximations | lambda_eff ~47.0, T ~15.7-16.2k, Q 428 (**10.3-10.6x**): (R,B,C) = (9,143,40), 8-bit words, J = 5, ANF/paired-product XOR oracles 294-318 T per circuit |

[INFERENCE] Gu's RS circuit evaluated under our metric: Q^2 T = 1,837^2 x 442,397 = 1.49e12; expected
~14 failures in 102,400 at 1.4e-4 -> eps+ ~ 1.3e-3 -> R ~ 1.24 -> score ~1.85e12 = **~13x**, i.e. between
our baseline and the public 63x frontier. Its 1,837-qubit peak (840 syndrome + locator/template/Euclid
cofactor banks) is what kills it under Q^2; the public lineage keeps ~52 qubits above the syndrome. So we
transfer *components*, not the architecture.

---

## 5. Transfer to our benchmarks

Estimates are [INFERENCE] unless a number is quoted; "gain" is relative to the *reference*, and I note when
the public frontier already contains the idea.

### 5.1 Benchmark I — 1/sqrt(x) phasing (Q x (Toffoli + T/4), k = 0)

The HHL/Gaussian/Coulomb recipe is essentially what the public 62-qubit design does (dyadic/segmented
quadratic, QROM coefficients, direct accumulation). What Gu adds that the public write-ups do not mention:

| Trick | Expected effect on reference | kickmix notes |
|---|---|---|
| N1+N2+N4 direct piecewise quadratic on x_norm (no Newton), dyadic leaves addressed by (s, top bits) | ~5-6x on T, ~2.5x on Q (Gu: 12x T, 2.6x Q on arcsin with a 21-bit input and 33-bit output; our output is 40 bits at 2^-24 relative) — already in the public 20x design | `init_lookup(table, address=top bits, target=coef words)`; leaves of unequal width = a hand-rolled `unary_iteration` with early-stopping children (kickmix `init_lookup` walks the full address; write the dyadic walk with `unary_iteration` cursors + `init_and`/`del_and`), or pad to uniform segments (public design uses 256 uniform (e,a) segments) |
| N6 backward fitting through the exact integer pipeline + N7 exhaustive check | the k = 0, per-x relative tolerance makes this the right fitting method: fit coefficients so every x lands inside tol(x) after truncation, rounding and the rotation budget; the public frontier's "LP-calibrated angles" is the same idea | pure classical code; 3,133,452 inputs x cheap integer model; keep margin for the rotation price 0.56 log2(1/eps)+5.3 T |
| N3 Booth radix-4 rows + N5 per-row truncation search | ~45% fewer rows than binary shift-and-add on each truncated multiply | `iadd(offset_slice, target=..., control=digit flags)`; a negative digit = complement target around the add (X gates) + carry-in; one `init_and` per digit for the |d| = 2 selector, `del_and` free |
| N8 batched phase repair after `del_lookup` | coefficient words freed right after use instead of at the mirror pass -> peak drop (Gu: 51 -> ~?); repair cost ~tree-prefix + one-hot bank (HHL 212 T for 345 leaves, Gaussian 50 for 514 live words) | `del_lookup` already does MBU; measure its emitted Toffoli repair cost on our table size (kickmix.md: `del_lookup` = HMR outputs + classical phase table + select-swap-style unary expansion); if larger than Gu's one-hot + Reed-Muller rail, hand-roll with `hmr` + `cz` under classical conditions |
| N9 content pruning | zero for I (all leaves distinct) | — |
| N11 carry-mode dial + live-qubit cap sweep | Gu: +64 T / -12 Q at the TQ optimum; for us Q x C is symmetric so sweep the cap | `iadd` clean-ancilla (n-1 T, MBU) vs dirty/low-space variants; sweep `set_max_qubits`-like caps per adder |
| N12 cheaper normalisation (zero tests on 8/4/2/1 bit groups + CSWAP shifts, no exponent register) | reference spends 230 (norm) + 600 (denorm) T; a log-depth barrel shifter ~4 x 35 CSWAPs | `cswap` under qubit flags; in Gu's Coulomb design the 4 flags double as shift+parity address bits |
| N14 reuse freed words as carries; borrow provably-zero input bits | -10..20 Q | after `del_lookup`, reuse the ids (Q = max id + 1, so reuse *ids*, not just count) |
| Error ledger with a free complement (N10) | n/a for I | — |

Risks: k = 0 is strict and `R`/`hmr` on a dirty qubit fails with prob 1/2 per shot, so every MBU claim must be
provable; rotation pricing eats leftover margin (companion-paper 2.2).

### 5.2 Benchmark II — RS syndrome decoder (R x Q^2 x T)

| Trick | Expected effect on reference | kickmix notes |
|---|---|---|
| R13 42-T multiplier, R14 66-T inversion | multiplier 63 -> 42 (-33% on every quantum x quantum product), inversion 315 -> 66 (-79%); the public lineage already has rank 42 | kickmix `init_gf2_mul` is fixed Karatsuba (63); implement the GF(4)-CRT bilinear form by hand: CNOT networks (`gf2_iadd`/`cx`) + 42 `init_and` on parity pairs, outputs fanned out by CX; erase with `hmr` + 42 conditioned `cz`s (= `del_gf2_mul` semantics). Basis change 4179 <-> any tower basis is a free linear map (`gen_linear_map`). Inversion: norm to GF(64) (15 T) and GF(8) (6 T), cube + square free |
| R8+R9+R10 phase-only Forney with precomputed Psi, Z-linear mask part | reference sweep = 4,095 x 351 T = 1.44M (25%); Gu: 4,024 x 23 = 92.6k + 2 x 44.5k Euclid ~ 181k -> **~8x on the sweep stage**; the public lineage ("scan" 44,275 + convert 69,220 + unconvert 70,342) already does something similar | our mask c arrives as **classical bits per test**, Gu's is fixed. The Z-linear projection u = V^-1 mu is F2-linear in c, so [INFERENCE] build it as free classical-conditioned gates: accumulate parity bits of c into scratch qubits with `x(q, control=c_bit)` chains (Clifford, free), then `z`/`cz` on syndrome bits controlled by those parities; the per-point constants nu_j also depend on c -> the 12-T "rank-12 bilinear form" becomes "multiply U by Psi (42 T, gated) then Z on the 12 product bits under the 12 classical c-bits" ~ 11 + 42 = 53 T/point instead of 23 (still ~6.6x below the reference's 351), unless the per-point mask is folded via a per-point classical-conditioned linear map on the operand parities (CNOTs under classical conditions are free) — worth a careful derivation: Tr(mu(c) U Psi) = sum_b c_b Tr(lambda_b U Psi) and each Tr(lambda_b U Psi) is a bilinear form of rank <= 12 in (U,V); 12 such forms gated by c_b would be up to 144 T but they share the same 12x12 product structure, so computing the 12 bits of U*V once (42 T) and reading parities for free is the cheap route [INFERENCE] |
| R1-R6 BM on a shared path with a failure-budgeted stack and measured windows | key equation 1.9M -> 140k + reverse 86k; but **qubits**: Gu's 1,837 vs public 892. nasir26's note (`participants.md`): a naive reversible BM needs ~2,600 Q; Gu's routing + sigma_0 delta = 1 + one-entry stack is exactly what removes that. Under Q^2 the 840 syndrome + ~36 locator words (432) + template (432) + stack 19 + counters already ~1,750 unless locator/template share the syndrome space as the Schur lineage does | counters/flags: `iadd` on small registers; branch routing: `cswap` of whole 12-qubit words under the replace flag (12 T per word pair — note that Gu priced a *second* 19-qubit stack entry at 2,470 T in total because every push/pop moves it with 19 Fredkins); windows: static per-round slices; stack tag compare: `flip_if_*` comparators |
| R7 in-place evaluator and cofactors in zeroed syndrome words | -420 Q vs a separate omega register; +workspace | triangular middle products with `init_gf2_mul` into syndrome words; reversible since each word is replaced by itself + f(earlier words) |
| R11 fixed-schedule Euclid, quotients parked in cleared words, zero-pivot repair with a 6-bit record | 17 blocks x ~900 T each way | `cswap` halves under the top-word-nonzero flag (11-T zero test), one inversion per block |
| R12 Chien by parity reads | CNOT-only advance (we already have `gf2_imul(const)` = 0 T); sweep as one `repeat` body shrinks the file (our dqi reference .kmb is 845 MiB, 86M ops) | `push_condition`/`pop_condition` for the root-gated body |
| M8 (Luo-EEA specialisation): fitted windows per step, schedule cut, test-free positions, merged scans, measured carries | **directly applicable to our pointer-driven 222-cycle EEA** if we keep the EEA: Gu got 3.4x on the integer analogue; our EEA is 50% of T (nasir26) and counter tests ~10 T/position; expect ~2x on the EEA stage at ~1e-4 failure [INFERENCE] | replace `unary_iteration` over degree pointers by static slices per cycle where the sampled degree sequences never vary; measure window misses on the DQI weight law (mean weight 31.05) |
| Failure budget economics | our R table (`companion-paper.md` 3.4): 10 failures ~ +3%, 100 ~ +17%; Gu's aggregate 1.4e-4 -> ~14 failures -> R ~1.24 (+4%) buys -646 Q (-50% in Q^2) and the window savings | choose stack depth 1 and windows at the 1e-4 level; never drop weight-35 support (2.8%) |

### 5.3 Benchmark III — DF-THC-SOS angle QROMs (lambda_eff x T_tot x Q_tot, exact, <= 128 Q)

| Trick | Expected effect | kickmix notes |
|---|---|---|
| Q1+Q2 choose the address map so adjacent words repeat, prune repeated spans; N9 content pruning of zero/constant subtrees | the address->vector map is ours (companion-paper 4.3); sort/permute addresses so angle words share prefixes and so many Delta-words (XOR between consecutive batches) are zero; Gu: 41,050 -> 10,271 T on a 2^16 alias table, 1,022 -> 495 on a 1,024-entry table with 50% zeros | implement the walk with `unary_iteration` + per-node early stop (`init_lookup` has no pruning; write a custom tree with `init_and`/`del_and` and CNOT fan-out at leaves); the verifier only checks words, so ordering is free |
| Q7 hold-budget DP under the 128-qubit cap | Toffoli-optimal path-AND retention given selection (~11-12 qubits) + J words (<= 100 qubits) + headroom | classical DP at build time; kickmix unary iteration keeps one AND per level by default |
| N8/Q6 joint phase repair | reverse traversal must clear words: self-inverse oracles (each Angles_k is applied forward and reverse) mean the reverse pass is another lookup; MBU is allowed (no Z_POW rule only bans rotations; conditioned CZ is fine) — measure if `del_lookup`'s repair beats a second walk for our ~1.3k-row, 8-bit-word tables | `del_lookup(table, address, target)`; or `hmr` + one-hot rail + CZ |
| Q4/Q5 CCZ-rank and gauge of Boolean phases | relevant if angle words are produced as XOR-of-products (the public ANF loaders): cost = number of bilinear terms, minimise rank | `init_and` per bilinear term; CNOT basis changes free |
| Fe2S2 lesson: the *data* is the lever | public frontier gets 10.6x mostly from (R,B,C), 8-bit words, J = 5; Gu's table scheduling adds a further 2-4x on the lookup itself only when the data has structure — quantisation-aware factorisation that *creates* repeated/zero words is the way to manufacture that structure [INFERENCE] | classical optimisation of (U,W,H) under the 20 mHa constraint with a word-repetition penalty |

### 5.4 Cross-cutting

- Build a `.kmx` peephole optimiser (L9): constant/affine propagation and CCX-fanout retargeting on the emitted
  stream; cheap and value-exact.
- Audit every `init_and`/`del_and` pair and every adder for measured vs in-place carries under each
  benchmark's Q weighting (N11, L11).
- Audit every truncation: exact may be cheaper (L12).
- Compute the "break-even" of Q vs T for each score (I: dC/dQ = C/Q ~ 31 T per qubit at the reference; II:
  2T/Q ~ 6,050 T per qubit; III: T_tot/Q_tot ~ 128 T per qubit) and rank levers by it (HARNESS runbook).

---

## 6. Search loop design (to replicate with our harness)

### 6.1 What [GU] ran (distilled)

```
spec = hand-written task contract (interface, model, correctness checks, failure budget, objective)
families = LLM.ideate(spec)                      # <= 5 architectures, one datapath each; merged if same datapath
archive[family] = MAP-Elites over (T, Q) cells  # keep lowest-TQ program per cell; programs carry DISCOVERY notes
loop:
    for each family (in parallel):
        parent = select(archive[family])         # elite or cell-diverse
        session = new_agent(spec, parent.program, parent.feedback,
                            inspiration = a few archive programs + costs,
                            summaries of recent attempts, DISCOVERY notes)
        # inside the session the agent may: run_candidate(prog, trial_eval=True) -> valid/invalid + T,Q
        #                                   oracle(x) -> f(x) ; spawn subagents
        child = session.submit()                 # complete program + <= 3 DISCOVERY lines
        verdict, T, Q, feedback = evaluator(child)   # ground truth; hash-seeded tests; exact sign check
        if valid: archive[family].insert(child, TQ)
    periodically: share leading programs across families
report global min TQ
```

Key properties: candidates are *programs* (structure-preserving edits), ground truth is the evaluator, context
per iteration is bounded and fresh, diversity is kept along two axes (family, (T,Q) cell), insights persist
as text notes, the agent has a cheap local trial evaluator and a reference oracle.

### 6.2 What ecdsa.fail participants converged on [ECDSA-REPORT Sec. 4.3; HARNESS]

- **Profile before ideating** (peak binder, Toffoli attribution per phase); rank levers by score sensitivity.
- **Classify candidates**: value-exact (same function on all inputs; certify statically) vs approximate
  (budgeted failures; measure the failure rate on the *real* input distribution before building).
- **Staged validation**: small-domain exhaustive -> smoke -> regression -> full evaluator; separate cls / pha /
  anc channels; repair the smallest faulty component first; rebuild clean before measuring.
- **Organisation**: orchestrator + clean-context workers each owning one hypothesis in its own worktree, returning
  "a measured patch or a quantified kill"; route bake-offs with equal initial budgets (beam search over
  architectures); cross-model review; watcher agents diffing the public frontier; versioned skills that are
  updated when a technique or failure mode is learned; append-only experiment memory with assumptions so
  dead ideas can be revisited; persistent goals (`/loop`, `/goal`) with stall checkpoints; humans pick
  regimes, supply domain knowledge, and authorise non-monotone restructures.
- Consolidated two-process framework (Alg. "consolidated"): Process A monitors frontier + literature and
  updates skills/memory; Process B is a token-bounded candidate cycle (sync -> choose base -> profile ->
  hypotheses -> parallel fresh-context subagents -> cls/pha/anc tests -> full evaluator -> rebuild/remeasure
  best -> submit if it beats the frontier -> distil outcomes).

### 6.3 Proposed harness for vqcc [INFERENCE]

1. **Evaluator = the official verifiers** wrapped as a tool returning `{verdict, cost, Q, T(or C), eps+, failing
   shots, first failing input, phase/ancilla diagnosis}`; a fast `trial_eval(subrange, shots)` for I and a
   reduced-shot mode for II; stage-level Toffoli attribution from `operation_statistics` on labelled
   `push_condition` regions (Gu's `meta.json` phase labels + `liveness.json` are the model).
2. **Candidate = Python generator** using `km.CircuitBuilder`; keep structure (functions per stage,
   `constants.json` produced by a separate classical search like `gen_constants.py`).
3. **Objective = the benchmark's own score** (not TQ): I: Q x (Tof + T/4) with the real rotation pricing; II:
   R(eps+) Q^2 T with Clopper-Pearson eps+ at 102,400 shots; III: lambda_eff T_tot Q_tot with the heuristic
   Outer/Inner/Givens costs. MAP-Elites cells over (Q, T) still useful because each score weights Q differently.
4. **Seeding**: (a) the reference generator; (b) ideation prompt asking for distinct families — for II at
   least {EEA-fixed-schedule (M8 style), BM-shared-path (R1-R6), Hankel/Schur in-place continued fraction
   (public frontier), PGZ/Gaussian elimination}; for I {direct piecewise quadratic (N1-N5), Newton on a coarser
   guess, lookup-dominant low-degree}; for III {address-map scheduling + pruned trees, ANF/paired-product
   loaders, batching/J sweeps}; (c) seed programs from the tricks tables above as "inspiration" archive
   entries with their costs.
5. **Session contract** (from ED Fig. 1): spec + parent + feedback + 2-3 inspiration programs + recent
   summaries + DISCOVERY notes; tools: trial_eval, oracle (reference function), profiler, subagent; output:
   full program + <= 3 DISCOVERY lines + a `class: exact|approx` tag and, for approx, a measured failure
   estimate on the contract distribution.
6. **Acceptance gates**: exact candidates must pass the full verifier (I: exhaustive; III: all addresses fwd +
   rev); approx candidates (II only) must report eps on >= 1e6 classical draws of the DQI weight law before
   the 102,400-shot run; dirty-reset/phase failures are always rejected.
7. **Memory**: per-family notes + a global negative-result ledger (hypothesis, assumption, measured delta,
   why it died); a skills file per benchmark with the lever list of Sec. 5 that gets edited when a lever is
   confirmed or refuted; watcher pass over Kaggle discussion/notebooks (participants.md).
8. **Human steering**: choose families to fund, approve non-monotone restructures, write the classical
   searches (window fitting, backward coefficient fitting, address scheduling) that agents are bad at
   finishing, and audit value-exactness claims.
9. **Budget signals to log** (absent in [GU]): iterations, valid fraction, best-so-far per family over time,
   tokens; use them to decide family pruning.

---

## 7. Open questions the sources leave

- [GU] does not say how many iterations or how much compute the eight searches took, nor how much of each
  final circuit was agent-written vs human-polished; the repo's deterministic classical searches
  (`gen_constants.py`, 100-200 CPU-hours for the Gaussian) are clearly human-curated.
- [GU]'s RS circuit's qubit peak sits in the Euclid passes; whether a Q^2-weighted search would have found a
  sub-900-qubit BM variant is untested (the public Schur lineage suggests the syndrome words can host nearly
  everything).
- Per-test classical masks (our contract) vs Gu's fixed mask: the Z-linear projection and nu_j folding need a
  classical-conditioned derivation (Sec. 5.2) — to be worked out and costed.
- Gemini 4 Argon's arcsin result is unverifiable from public material; if Google releases the circuit it is
  the most direct comparator for Benchmark I.
- Whether kickmix's `del_lookup` phase repair is as cheap as Gu's one-hot + Reed-Muller rail for our table
  shapes: measure.
