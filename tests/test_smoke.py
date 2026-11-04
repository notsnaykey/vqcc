"""Smoke tests: kickmix imports, a small adder fuzzes clean, cost helpers behave."""

import math
import random

import kickmix as km
import pytest

from vqcc import fuzz_circuit, resources
from vqcc.cost import dqi_rate_penalty, final_score, invsqrt_cost


def build_adder(n: int) -> km.Circuit:
    b = km.CircuitBuilder()
    a = b.create_quantum_register(n, "a")
    t = b.create_quantum_register(n, "t")
    b.iadd(a, target=t)  # t += a (mod 2^n)
    return b.finish_circuit()


def test_adder_fuzzes_clean():
    n = 8
    c = build_adder(n)

    def ref(inp):
        return {"t": (inp["a"] + inp["t"]) % (1 << n)}, 0.0

    r = fuzz_circuit(
        c,
        ref,
        input_registers={"a": None, "t": None},
        output_registers=["t"],
        shots=512,
        seed=1,
    )
    assert r.ok, str(r)
    res = resources(c)
    assert res.qubits >= 2 * n
    assert res.toffoli > 0


def test_fuzz_detects_bug():
    n = 4
    c = build_adder(n)

    def wrong_ref(inp):
        return {"t": (inp["a"] + inp["t"] + 1) % (1 << n)}, 0.0

    r = fuzz_circuit(c, wrong_ref, input_registers={"a": None, "t": None}, output_registers=["t"], shots=32)
    assert not r.ok


def test_cost_helpers():
    res = resources(build_adder(8))
    assert invsqrt_cost(res) == res.qubits * (res.toffoli + res.t_like / 4)
    assert dqi_rate_penalty(0.0) == pytest.approx(1.0)
    assert math.isinf(dqi_rate_penalty(1.0))
    assert final_score([1.0, 1.0, 1.0]) == pytest.approx(1.0)
    assert final_score([2.0, 2.0, 2.0]) == pytest.approx(2.0)
    assert final_score([0.0, 2.0, 2.0]) == 0.0


def test_text_format_roundtrip(tmp_path):
    c = build_adder(3)
    p = tmp_path / "add3.kmx"
    c.to_file(p)
    assert km.Circuit.from_file(p) == c
    pb = tmp_path / "add3.kmb"
    c.to_file(pb, format="kmb")
    assert km.Circuit.from_file(pb) == c
    random.seed(0)
