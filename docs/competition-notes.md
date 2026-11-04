# Competition notes

Gathered 2026-11-04 from Google's announcement, kickmix source, and public
participant repos. Kaggle itself was not reachable from the session that wrote
this, so **re-verify every number against the Kaggle overview and the official
verifiers in `data/`.**

## Key facts

| Item | Value |
|---|---|
| Host | Google Quantum AI + Kaggle |
| Prize pool | $150,000 (plus a $10,000 mid-competition milestone prize, 2026-11-20) |
| Entry deadline | 2027-01-13 |
| Final deadline | 2027-01-20 23:59 UTC |
| Submissions | 5 per day, ~45 min scoring each, zip named `submission.zip` |
| Library | kickmix 1.0.0 on PyPI (C++20 + pybind11; source under `Qualtran/kickmix`) |
| Paper | arXiv:2610.23832, "Leveraging verifiable structure in quantum circuits to find more efficient compilations with agentic AI" |
| License of baselines/verifiers | Apache 2.0 |

## Why verification is cheap

Kickmix circuits use only reversible classical logic (X, CX, CCX, CSWAP, ...),
diagonal phase gates (Z, CZ, CCZ, Z_POW) and HMR (Hadamard-measure-reset,
measurement-based uncomputation). Such circuits map computational-basis inputs
to computational-basis outputs with a tracked phase, so a classical simulator
can fuzz them at tens of millions of gates per second. The verifier:

* seeds random inputs and measurement outcomes with a salted Fiat–Shamir hash of
  the submission (no hidden test set, no seed grinding);
* checks output registers, that ancillas are returned clean, and the phase;
* any failing benchmark zeroes the whole submission.

## Benchmarks and cost models (provisional, from public write-ups)

### I. `invsqrt` — fusion energy (Trotter simulation of electrons on a grid)
* Circuit computes a 1/sqrt(x) phasing for each electron pair.
* Cost = **Q × (Toffoli + T/4)**, rotations priced in T.
* Hard constraint: **zero failures** over ~200.5M shots (exhaustive over all
  3,133,452 inputs).
* Public leaderboard: one participant reported ~3.7× local improvement.

### II. `dqi` — combinatorial optimisation (Decoded Quantum Interferometry)
* Reversible Reed–Solomon syndrome decoder (GF(2^m) arithmetic; kickmix has
  native `gf2_*` builder ops).
* Cost = **R(ε⁺) × Q² × Toffoli**, with R(ε) = ln2 / (−ln(½ + 2√ε)) and ε⁺ an
  upper confidence bound on decoder failure from 102,400 shots. Imperfect
  decoding is allowed and traded against gates. Qubits count twice.
* Reference parameters seen in a public repo: `--m 4095 --n 70 --degree 12`.

### III. `dfthcsos` — quantum chemistry (FeMoCo phase estimation)
* Submit ANGLE circuits (`angle_k_0..n-1`) plus `submission.npz` holding the
  tensor factorisation `(U, W, H2_I, H1_I, Hsym_lower)` and Givens tree
  `tree_edges`.
* Cost = **λ_eff × Toffoli × Q** over the whole block encoding,
  λ_eff = sqrt(E_gap (2Λ − E_gap)).
* Rejected if Hamiltonian error > 20 mHa, Λ ≤ 49.0, E_gap ≤ 3.914898 Ha, or any
  ANGLE circuit > 128 qubits.
* Needs the FeMoCo data from the Kaggle bundle.

### Final score
`geomean(baseline_i / cost_i)` over the three benchmarks. Reference = 1.0.
A big win on one task is damped by the geometric mean, so all three matter.

## Submission zip layout
```
invsqrt.kmb | .kmx
dqi.kmb     | .kmx
dfthcsos/angle_k_0.kmb ... angle_k_{n-1}.kmb
dfthcsos/submission.npz
```
Files at the zip root, no wrapper folder. `vqcc.submission` enforces this.

## kickmix API cheat-sheet
* `km.CircuitBuilder()`: `create_quantum_register`, `alloc_qubits`, `x/cx/ccx/cz/ccz/cswap`,
  `init_and`/`del_and` (measurement-based uncompute), `iadd/isub`, `flip_if_*`
  comparators, `left_rotate`, `init_lookup`/`del_lookup` (QROM), `unary_iteration`,
  `gf2_*` field ops, `z_pow`, `hmr`, `push_condition/pop_condition`, `set_max_qubits`.
* `builder.finish_circuit()` → `km.Circuit`; `.to_file(path, format='kmb'|'kmx')`,
  `.operation_statistics()` (`num_toffoli_like`, `num_t_like`, `num_z_pow(...)`),
  `.num_qubits`, `.register_data`, `.text_diagram()`, `.flame_chart_svg()`.
* `km.Simulator(batch_size=n)`, `use_same_registers_as(circuit)`,
  `write_within_shot(reg, shot, value)`, `do(circuit)`,
  `read_within_shot(reg, shot, out=int)`, `read_shot_phase(shot)`, `clear_for_shot()`.
* CLI tools in the C++ source: `count_operations`, `diagram`, `sample`, `kmb2kmx`,
  `kmx2kmb`, `generate_circuit`.
* Build from source needs C++20 (g++ ≥ 13) and pybind11 2.12.

## Ideas to explore first
1. Reproduce baseline 1.0 locally with the official verifiers (~4 min).
2. `invsqrt`: table-lookup + Newton iteration tradeoffs, measurement-based
   uncomputation to cut Toffolis, qubit reuse (cost is linear in Q).
3. `dqi`: Q² makes qubit count dominant; accept a small ε⁺ to shrink the decoder.
4. `dfthcsos`: factorisation rank vs. λ_eff; biggest lever may be the `.npz`
   not the circuits.
5. Agentic search loops (the paper's approach) once the local eval is fast.

## Sources
* https://opensource.googleblog.com/2026/10/announcing-verifiable-quantum-circuit-compilation-competition-on-kaggle.html
* https://github.com/quantumlib/Qualtran/tree/main/kickmix
* https://github.com/Inzainos/quantum-circuit-compilation
* https://github.com/somfieao/kickmix-compiler
* https://github.com/clduab11/quantum-hackathon
