# Competition notes (overview)

Start here, then read `docs/research/FACTS.md` (consolidated fact sheet) and the
detailed reports in `docs/research/`.

## Confirmed facts (official metric script + verifiers + companion paper)

| Item | Value |
|---|---|
| Host | Google Quantum AI + Kaggle; started 2026-10-22 |
| Prizes | $150k: 50/25/10/5/5/5k for places 1–6; $10k milestone (2026-11-20, needs a public notebook); $10k longest leader (to 2027-01-04); 3 × $10k single-task prizes (all three tasks must pass) |
| Deadlines | entry + team merger 2027-01-13; final 2027-01-20 23:59 UTC |
| Limits | 5 submissions/day, 2 final picks, teams ≤ 5; zip must be named `submission.zip` |
| Winner obligations | Apache-2.0 release of submission and generator code, reproducible environment docs; competition data may not be redistributed |
| Library | kickmix 1.0.0 (PyPI), C++20 + pybind11; source in `Qualtran/kickmix`; introduced in Babbush et al., arXiv:2603.28846 |
| Companion paper | Khattar et al., arXiv:2610.23832 (benchmark definitions, no results) |
| Score | geometric mean over three benchmarks of `baseline_cost / cost`; any failing benchmark on any split voids the whole submission; each split uses a secret salt |

## Benchmarks

| | I `invsqrt` | II `dqi` | III `dfthcsos` |
|---|---|---|---|
| Task | phase by 1/√x, x ∈ [1, 3,133,452], rel. tol 2⁻²⁴, exhaustive, 64 shots each, zero failures | RS(4095, 4025) syndrome decoder over GF(2¹²), 35 errors, 840 syndrome qubits, 102,400 shots | FeMoCo-76 DF-THC-SOS angle oracles (`angle_k_*`, ≤128 qubits, no Z_POW) + factorisation npz |
| Cost | Q × (Tof + (T + Σrot)/4); rotation = 0.56·log₂(1/ε)+5.3 T | R(ε⁺) × Q² × Tof; ε⁺ Clopper–Pearson at 2⁻¹²⁸; reject if ε⁺ ≥ 1/16 | λ_eff × T_total × Q_total; λ_eff = √(E_gap(2Λ−E_gap)); Λ > 49, E_gap > 3.914898, errors ≤ 20 mHa |
| Baseline | Q 260, 7,735 Tof, 37 rotations → 2,076,774 | Q 1,893, 5.725M Tof → 2.444e13 | λ_eff 49.30, T 93,237, Q 730 → 3.356e9 |
| Public frontier (early Nov) | Q 62, ~1,326 Tof, 41 rot → ~100.6k (≈20.6×) | Q 892, ~404k Tof → ~3.85e11 (≈63×) | (R,B,C)=(9,143,40), Q 428, T ~16k, λ_eff 47.0 → ~3.2e8 (≈10.5×) |
| Best published research | Gu et al. 2610.22367: table of 128 lines + MBU, 1,140 Tof/142 Q on a looser spec | Gu et al.: Berlekamp–Massey + phase-only Forney, 442k Tof / 1,837 Q | Low et al. 2502.15882 (PRX 2025) defines the method |

Toffolis are counted as the mean executed per shot (gates under a measured-bit
condition count only when taken). Q is `circuit.num_qubits` = max qubit id + 1,
so ids must be reused tightly.

## Leaderboard context

Assembling the public Apache-2.0 circuits gives ≈ geomean(20.6, 63, 10.5) ≈ 23.9;
about half the field sits at 22.9–23.2. Leader on 2026-11-02 was ≈ 28.8. To place,
one benchmark has to move well beyond its public frontier.

## Reading order

1. `docs/research/FACTS.md` — consolidated numbers, contracts, contradictions.
2. `docs/research/kickmix.md` — the library and the cost of every primitive.
3. `docs/research/companion-paper.md` — the official benchmark definitions.
4. Per benchmark: `deep-invsqrt-papers.md`, `deep-dqi-papers.md`, `deep-chemistry-papers.md`.
5. `docs/research/ai-found-tricks.md` — what LLM-agent search already found (Gu et al., ecdsa.fail).
6. `docs/research/participants.md`, `kaggle-notebooks.md`, `kaggle-pages.md` — the public field.
7. `docs/research/qualtran-bloqs.md`, `papers.md` — building blocks and bibliography.
