"""The vendored official verifiers run through the vqcc.verify wrappers.

Fast (< 10 s total, no competition data): a hand-made Benchmark I circuit at a reduced
instance and a tiny Benchmark II instance built with the official reference generator.
The full-size runs, which need data/, are documented in docs/verification.md.
"""

from __future__ import annotations

import pathlib
from fractions import Fraction

import kickmix as km
import pytest

from vqcc.verify import DATA_DIR, VERIFIERS_DIR, load_dqi, load_invsqrt


def _phase_circuit(half_turns: Fraction, width: int = 22) -> km.Circuit:
    """x register of `width` qubits; phase |x=1> by Z_POW(half_turns) on bit 0 via a Toffoli-gated ancilla."""
    b = km.CircuitBuilder()
    x = b.create_quantum_register(width, "x")
    anc = b.alloc_qubits(2)  # unnamed scratch: the verifier allows only the register "x"
    b.x(anc[0])
    b.ccx(x[0], anc[0], anc[1])  # anc[1] = x0 (one Toffoli)
    b.z_pow(anc[1], half_turns)
    b.ccx(x[0], anc[0], anc[1])  # uncompute (second Toffoli)
    b.x(anc[0])
    return b.finish_circuit()


def test_vendored_tree_present():
    assert (VERIFIERS_DIR / "invsqrt" / "verify_submission_invsqrt.py").is_file()
    assert (VERIFIERS_DIR / "dqi" / "verify_submission_dqi.py").is_file()
    assert (VERIFIERS_DIR / "dfthcsos" / "verify.py").is_file()
    assert (VERIFIERS_DIR / "LICENSE.txt").is_file()


def test_invsqrt_official_verifier_tiny_instance():
    """max_x = 1 and beta = 1/4: the target phase is exactly 1/4 turn on x = 1."""
    m = load_invsqrt()
    spec = m.ProblemSpecInvSqrt(width=22, max_x=1, beta=Fraction(1, 4), precision_bits=24,
                                shots_per_x=64, system_qubits=0)
    good = _phase_circuit(Fraction(1, 2))  # Z^(1/2) = S: 1/4 turn
    out = m.verify(good, spec, batch_size=64, max_workers=1, salt="pytest")
    assert out["status"] == "PASS"
    assert out["verified_shots"] == 64
    assert out["toffoli_count"] == 2
    assert out["t_count"] == 0 and out["rotation_count"] == 0
    assert out["score"] == pytest.approx(out["num_qubits"] * 2)

    bad = _phase_circuit(Fraction(1, 4))  # T: 1/8 turn, off by 1/8 turn
    with pytest.raises(AssertionError, match="phase error"):
        m.verify(bad, spec, batch_size=64, max_workers=1, salt="pytest")


def test_dqi_official_verifier_tiny_instance(tmp_path: pathlib.Path):
    """RS over GF(2^4) with m = 15, n = 4, built by the official reference generator."""
    import importlib

    gen = importlib.import_module("dqi.dqi_reference_circuit")
    circuit = gen.build_reference_circuit(m=15, n=4, degree=4)
    m = load_dqi()
    spec = m.ProblemSpecDQI.benchmark_instance(m=15, n=4, degree=4, num_shots=2560)
    # 2,560 shots is the smallest multiple of 256 whose Clopper-Pearson bound at delta = 2^-128
    # stays below 1/16 with zero failures.
    out = m.verify(circuit, spec, max_workers=1, salt="pytest")
    assert out["status"] == "PASS"
    assert out["value_errors"] == 0 and out["phase_errors"] == 0
    assert out["num_qubits"] == circuit.num_qubits
    assert out["score"] == pytest.approx(out["repetition_factor"] * out["num_qubits"] ** 2 * out["toffoli_count"])
    # Through the CLI wrapper on a file, too.
    path = tmp_path / "dqi_small.kmb"
    circuit.to_file(path, format="kmb")
    from vqcc.verify.dqi import verify as verify_file

    out2 = verify_file(path, instance={"m": 15, "n": 4, "degree": 4, "num_shots": 2560}, max_workers=1, salt="pytest")
    assert out2["score"] == out["score"]


@pytest.mark.skipif(
    not (DATA_DIR / "dfthcsos" / "FeMoCo76o113e.fcidump").is_file()
    or not (DATA_DIR / "sample_submission" / "dfthcsos" / "submission.npz").is_file(),
    reason="competition data not downloaded (see data/README.md)",
)
def test_dfthcsos_official_verifier_reduced_shots():
    """The reference dfthcsos submission at 1 shot per address (the metrics do not depend on shots)."""
    from vqcc.verify.dfthcsos import verify

    out = verify(str(DATA_DIR / "sample_submission" / "dfthcsos"), shots_per_address=1, salt="pytest")
    assert out["status"] == "PASS"
    assert out["num_qubits"] == 730
    assert out["toffoli_count"] == 93237.0
    assert out["lambda_eff"] == pytest.approx(49.301369, abs=1e-6)
    assert out["score"] == pytest.approx(3355599588.3155, rel=1e-12)
