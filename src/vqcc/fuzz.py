"""A small local fuzz harness in the style of the official verifiers.

The verifiers run a kickmix circuit on random classical inputs and check that
(1) output registers hold the expected classical value, (2) ancilla/other
registers are returned to their initial state, and (3) the accumulated phase
matches the expected phase. This module does the same thing for circuits you
build locally, so you can iterate without the ~45 minute Kaggle scoring loop.
"""

from __future__ import annotations

import random
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

import kickmix as km

Inputs = Mapping[str, int]
# Reference function: given the input register values, return expected output
# register values and (optionally) the expected phase in half-turns.
Reference = Callable[[Inputs], tuple[Mapping[str, int], float | None]]


@dataclass
class FuzzResult:
    shots: int
    failures: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.failures

    def __str__(self) -> str:
        if self.ok:
            return f"OK: {self.shots} shots, no failures"
        head = "\n  ".join(self.failures[:10])
        more = "" if len(self.failures) <= 10 else f"\n  ... {len(self.failures) - 10} more"
        return f"FAIL: {len(self.failures)}/{self.shots} shots\n  {head}{more}"


def _register_widths(circuit: km.Circuit) -> dict[str, int]:
    return {str(name): len(arr) for name, arr in circuit.register_data.items()}


def fuzz_circuit(
    circuit: km.Circuit,
    reference: Reference,
    *,
    input_registers: Mapping[str, Callable[[random.Random], int] | None],
    output_registers: list[str],
    shots: int = 256,
    batch_size: int = 64,
    seed: int = 0,
    check_phase: bool = True,
    check_clean: bool = True,
) -> FuzzResult:
    """Run `shots` random inputs through `circuit` and compare against `reference`.

    input_registers maps register name -> sampler(rng) -> int, or None for a
    uniform value over the register width. Registers not named as inputs are
    expected to start at zero and (if check_clean) to end at zero unless they
    are listed as outputs.
    """
    rng = random.Random(seed)
    widths = _register_widths(circuit)
    for name in list(input_registers) + list(output_registers):
        if name not in widths:
            raise KeyError(f"register {name!r} not in circuit; have {sorted(widths)}")

    result = FuzzResult(shots=0)
    sim = km.Simulator(batch_size=batch_size)
    sim.use_same_registers_as(circuit)

    done = 0
    while done < shots:
        n = min(batch_size, shots - done)
        batch_inputs: list[dict[str, int]] = []
        sim.clear_for_shot()
        for i in range(n):
            vals: dict[str, int] = {}
            for name, sampler in input_registers.items():
                v = sampler(rng) if sampler else rng.getrandbits(widths[name])
                vals[name] = v
                sim.write_within_shot(name, i, v)
            batch_inputs.append(vals)
        sim.do(circuit)
        for i in range(n):
            expected_out, expected_phase = reference(batch_inputs[i])
            tag = f"shot {done + i} inputs={batch_inputs[i]}"
            for name, want in expected_out.items():
                got = int(sim.read_within_shot(name, i, out=int))
                if got != want:
                    result.failures.append(f"{tag}: {name} got {got} want {want}")
            if check_clean:
                for name in widths:
                    if name in expected_out or name in input_registers:
                        continue
                    got = int(sim.read_within_shot(name, i, out=int))
                    if got != 0:
                        result.failures.append(f"{tag}: ancilla {name} not clean ({got})")
            if check_phase and expected_phase is not None:
                got_phase = float(sim.read_shot_phase(i)) % 2
                if abs(got_phase - (expected_phase % 2)) > 1e-9:
                    result.failures.append(f"{tag}: phase {got_phase} want {expected_phase}")
        done += n
        result.shots = done
    return result
