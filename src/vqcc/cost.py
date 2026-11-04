"""Resource counting and per-task cost models.

The per-task formulas below are transcribed from public write-ups of the
competition (see docs/competition-notes.md). Treat them as provisional until
checked against the official verifiers in data/, which are the source of truth.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import kickmix as km


@dataclass(frozen=True)
class CircuitResources:
    qubits: int
    bits: int
    toffoli: int  # CCX + CCZ + CSWAP
    t_like: int  # Z_POW at Clifford-hierarchy level 3
    z_pow_non_clifford: int  # all non-Clifford Z_POW (includes T-like and finer rotations)
    instructions: int

    @property
    def toffoli_equivalent(self) -> float:
        """Toffoli-equivalent count using the invsqrt convention of T/4 per T gate."""
        return self.toffoli + self.t_like / 4


def resources(circuit: km.Circuit) -> CircuitResources:
    stats = circuit.operation_statistics()
    return CircuitResources(
        qubits=circuit.num_qubits,
        bits=circuit.num_bits,
        toffoli=stats.num_toffoli_like,
        t_like=stats.num_t_like,
        z_pow_non_clifford=stats.num_z_pow(min_clifford_hierarchy_level=3),
        instructions=stats.num_instructions,
    )


def invsqrt_cost(res: CircuitResources) -> float:
    """Benchmark I: Q x (Toffoli + T/4). Zero failures allowed."""
    return res.qubits * res.toffoli_equivalent


def dqi_rate_penalty(eps_plus: float) -> float:
    """R(eps) = ln 2 / (-ln(1/2 + 2*sqrt(eps))) for the DQI decoder failure bound."""
    if eps_plus < 0:
        raise ValueError("eps_plus must be non-negative")
    inner = 0.5 + 2 * math.sqrt(eps_plus)
    if inner >= 1:
        return math.inf
    return math.log(2) / (-math.log(inner))


def dqi_cost(res: CircuitResources, eps_plus: float) -> float:
    """Benchmark II: R(eps+) x Q^2 x Toffoli, where eps+ is an upper confidence bound on failure."""
    return dqi_rate_penalty(eps_plus) * res.qubits**2 * res.toffoli


def dfthcsos_lambda_eff(e_gap: float, big_lambda: float) -> float:
    """lambda_eff = sqrt(E_gap * (2*Lambda - E_gap))."""
    return math.sqrt(e_gap * (2 * big_lambda - e_gap))


def dfthcsos_cost(total_toffoli: float, qubits: int, e_gap: float, big_lambda: float) -> float:
    """Benchmark III: lambda_eff x Toffoli x Q, charged over the whole block encoding."""
    return dfthcsos_lambda_eff(e_gap, big_lambda) * total_toffoli * qubits


def improvement(baseline_cost: float, cost: float) -> float:
    return baseline_cost / cost


def final_score(improvements: list[float]) -> float:
    """Geometric mean of per-task improvements. The reference submission scores 1.0."""
    if not improvements or any(x <= 0 for x in improvements):
        return 0.0
    return math.exp(sum(math.log(x) for x in improvements) / len(improvements))
