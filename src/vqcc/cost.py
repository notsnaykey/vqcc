"""Resource counting and per-task cost models.

Formulas follow the official verifiers and the companion paper (arXiv:2610.23832);
see docs/research/FACTS.md. Where the official verifier simulates, Toffoli counts
are the MEAN executed per shot (conditioned gates count only when their bit is set);
the static counts here are an upper bound.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import kickmix as km

# Official baseline costs (reference submissions score exactly 1.0). Hosted = local.
BASELINE_COST = {
    "invsqrt": 2_076_774.2337,
    "dqi": 2.443946e13,  # 7th digit depends on the split salt
    "dfthcsos": 3_355_599_588.3155,
}

DQI_SHOTS = 102_400
DQI_CONFIDENCE_DELTA = 2.0**-128
DQI_REJECT_EPS = 1 / 16
DFTHCSOS_MAX_QUBITS = 128
DFTHCSOS_MIN_LAMBDA = 49.0
DFTHCSOS_MIN_E_GAP = 3.914898
DFTHCSOS_MAX_ERROR_HA = 0.020


@dataclass(frozen=True)
class CircuitResources:
    qubits: int
    bits: int
    toffoli: int  # CCX + CCZ + CSWAP (static count)
    t_like: int  # Z_POW at Clifford-hierarchy level 3
    rotations: int  # non-Clifford, non-T Z_POW (priced by precision for invsqrt)
    instructions: int


def resources(circuit: km.Circuit) -> CircuitResources:
    stats = circuit.operation_statistics()
    non_clifford_zpow = stats.num_z_pow(min_clifford_hierarchy_level=3)
    return CircuitResources(
        qubits=circuit.num_qubits,
        bits=circuit.num_bits,
        toffoli=stats.num_toffoli_like,
        t_like=stats.num_t_like,
        rotations=non_clifford_zpow - stats.num_t_like,
        instructions=stats.num_instructions,
    )


# --- Benchmark I: invsqrt -------------------------------------------------------------


def rotation_t_cost(eps: float) -> float:
    """T gates charged per arbitrary Z_POW rotation synthesised to precision eps."""
    return 0.56 * math.log2(1 / eps) + 5.3


def invsqrt_rotation_eps(min_margin_turns: float, n_rot: int) -> float:
    """Circuit-wide synthesis precision: eps = pi * min_x(tol(x) - |err(x)|) / n_rot (turns)."""
    return math.pi * min_margin_turns / n_rot


def invsqrt_cost(
    qubits: int, mean_toffoli: float, t_count: float, n_rot: int = 0, rot_eps: float | None = None
) -> float:
    """S = Q x (Toffoli + (T + n_rot * rotation_t_cost(eps)) / 4). Clifford Z_POW are free."""
    rot_t = n_rot * rotation_t_cost(rot_eps) if n_rot else 0.0
    return qubits * (mean_toffoli + (t_count + rot_t) / 4)


# --- Benchmark II: dqi ----------------------------------------------------------------


def _binom_cdf_log(k: int, n: int, p: float) -> float:
    """log P[X <= k] for X ~ Binomial(n, p)."""
    if p <= 0:
        return 0.0
    if p >= 1:
        return -math.inf
    lp, lq = math.log(p), math.log1p(-p)
    terms = [
        math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1) + i * lp + (n - i) * lq
        for i in range(k + 1)
    ]
    m = max(terms)
    return m + math.log(sum(math.exp(t - m) for t in terms))


def clopper_pearson_upper(k: int, n: int = DQI_SHOTS, delta: float = DQI_CONFIDENCE_DELTA) -> float:
    """One-sided upper confidence bound eps+ with P[X <= k | eps+] = delta."""
    if k >= n:
        return 1.0
    lo, hi = 0.0, 1.0
    target = math.log(delta)
    for _ in range(200):
        mid = (lo + hi) / 2
        if _binom_cdf_log(k, n, mid) > target:
            lo = mid
        else:
            hi = mid
    return hi


def dqi_rate_penalty(eps_plus: float) -> float:
    """R(eps) = ln 2 / (-ln(1/2 + 2*sqrt(eps))); infinite (rejected) once eps >= 1/16."""
    if eps_plus < 0:
        raise ValueError("eps_plus must be non-negative")
    inner = 0.5 + 2 * math.sqrt(eps_plus)
    if inner >= 1:
        return math.inf
    return math.log(2) / (-math.log(inner))


def dqi_cost(qubits: int, mean_toffoli: float, failures: int = 0) -> float:
    """S = R(eps+) x Q^2 x Toffoli with eps+ from `failures` out of 102,400 shots."""
    return dqi_rate_penalty(clopper_pearson_upper(failures)) * qubits**2 * mean_toffoli


# --- Benchmark III: dfthcsos ----------------------------------------------------------


def dfthcsos_lambda_eff(e_gap: float, big_lambda: float) -> float:
    """lambda_eff = sqrt(E_gap * (2*Lambda - E_gap)); floors Lambda > 49.0, E_gap > 3.914898."""
    return math.sqrt(e_gap * (2 * big_lambda - e_gap))


def dfthcsos_cost(total_toffoli: float, total_qubits: int, e_gap: float, big_lambda: float) -> float:
    """S = lambda_eff x T_total x Q_total over the whole block encoding (angles + heuristics)."""
    return dfthcsos_lambda_eff(e_gap, big_lambda) * total_toffoli * total_qubits


# --- Overall ----------------------------------------------------------------------------


def improvement(task: str, cost: float) -> float:
    return BASELINE_COST[task] / cost


def final_score(improvements: list[float]) -> float:
    """Geometric mean of per-task improvements. The reference submission scores 1.0."""
    if not improvements or any(x <= 0 for x in improvements):
        return 0.0
    return math.exp(sum(math.log(x) for x in improvements) / len(improvements))
