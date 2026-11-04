import math

import pytest

from vqcc.cost import (
    BASELINE_COST,
    clopper_pearson_upper,
    dfthcsos_cost,
    dfthcsos_lambda_eff,
    dqi_cost,
    dqi_rate_penalty,
    final_score,
    invsqrt_cost,
    rotation_t_cost,
)


def test_clopper_pearson_matches_verifier_floor():
    # k=0 over 102,400 shots at delta=2^-128 gives eps+ = 8.66e-4 and R = 1.1913 (companion paper).
    eps = clopper_pearson_upper(0)
    assert eps == pytest.approx(8.66e-4, rel=2e-3)
    assert dqi_rate_penalty(eps) == pytest.approx(1.1913, rel=1e-3)
    # each early failure costs roughly +0.46%
    r1 = dqi_rate_penalty(clopper_pearson_upper(1)) / dqi_rate_penalty(eps)
    assert 1.003 < r1 < 1.007
    assert math.isinf(dqi_rate_penalty(1 / 16))


def test_dqi_baseline_reproduces():
    # Baseline: Q=1,893, mean Toffoli 5,725,108, zero failures -> ~2.4439e13
    assert dqi_cost(1893, 5_725_108) == pytest.approx(BASELINE_COST["dqi"], rel=1e-3)


def test_invsqrt_baseline_reproduces():
    # Baseline: Q=260, 7,735 Toffoli, 1 T, 37 rotations at eps=1.53e-12 -> 2,076,774.23
    cost = invsqrt_cost(260, 7735, 1, n_rot=37, rot_eps=1.53e-12)
    assert cost == pytest.approx(BASELINE_COST["invsqrt"], rel=1e-3)
    assert rotation_t_cost(1.53e-12) == pytest.approx(27.3, rel=0.02)


def test_dfthcsos_baseline_reproduces():
    # Baseline: lambda_eff 49.3014 (Lambda 308.456, E_gap 3.96548), T 93,237, Q 730
    assert dfthcsos_lambda_eff(3.96548, 308.456) == pytest.approx(49.3014, rel=1e-4)
    assert dfthcsos_cost(93_237, 730, 3.96548, 308.456) == pytest.approx(
        BASELINE_COST["dfthcsos"], rel=1e-4
    )


def test_public_frontier_score():
    # Public per-task frontier early Nov 2026: ~20.6x, ~63x, ~10.5x -> geomean ~23.9
    assert final_score([20.6, 63.0, 10.5]) == pytest.approx(23.9, rel=0.01)
