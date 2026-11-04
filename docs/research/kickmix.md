# kickmix technical reference

A circuit-designer's reference to the `kickmix` library (Qualtran, C++20 + pybind11), written for the
Google Quantum AI "Verifiable Quantum Circuit Compilation" Kaggle competition.

Sources used:

- Source tree (sparse clone of Qualtran): `kickmix/src/kickmix/{circuit,sim,gen,build,cmd,py,...}`. All
  `file:line` references below are relative to `kickmix/src/kickmix/` unless stated otherwise.
- Official docs fetched from GitHub: `docs/kickmix/kickmix_format.md`, `kickmix_instructions.md`,
  `kickmix_binary_format.md`.
- Companion paper arXiv:2610.23832 ("Leveraging verifiable structure in quantum circuits to find more
  efficient compilations with agentic AI").
- Originating paper arXiv:2603.28846 ("Securing Elliptic Curve Cryptocurrencies against Quantum
  Vulnerabilities: Resource Estimates and Mitigations", PRX Quantum, DOI 10.1103/j3xf-bw18), Appendix
  on the zero-knowledge proof, which defines kickmix circuits (see Section 10).
- Experiments run against the installed wheel (`kickmix` 0.1, `/home/user/vqcc/.venv`). Scripts live in
  `/tmp/claude-0/-home-user/af1e8b3b-1af8-51dd-9e8d-ec3f80eabc0b/scratchpad/kmexp/`.

Everything labelled **measured** was produced by running code. Anything labelled **(inferred)** is a
reading of the source that was not independently executed.

---

## 0. Mental model in one paragraph

A kickmix circuit is a straight-line program (no loops, no jumps) over three kinds of state: **qubits**
(stored as plain bits, because every allowed instruction maps a computational-basis state to a single
computational-basis state), **classical bits**, and one **global phase per shot** (a sign bit plus a
128-bit fixed-point angle accumulator). The only non-classical operation is `HMR` ("hammer"): Hadamard
then measure then reset. The simulator models it by drawing a *uniformly random* outcome bit and flipping
the tracked phase when (qubit was 1) AND (outcome is 1). That is exactly correct when the measured qubit
is a Z-basis function of the other qubits (measurement-based uncomputation, with the circuit then applying
`CZ ... if b` style fixups) and *incorrect-but-loud* otherwise: an unfixed kickback fails a phase check in
half of the shots. Correctness therefore means: on random computational-basis inputs, named registers hold
the expected values, every unnamed/scratch qubit is back at |0>, and the accumulated phase matches the
target. Resource cost is counted purely syntactically: `CCX`, `CCZ`, `CSWAP` (with or without `if`) are
"Toffoli-like"; `Z_POW` angles are classified by Clifford-hierarchy level; everything else is free.

---

## 1. The `.kmx` text format

### 1.1 Lexical structure (`circuit/mutable_circuit.cc:103-112, 334-452, 470-492`)

```
<CIRCUIT>     ::= <LINE>*
<LINE>        ::= <INDENT> <INSTRUCTION>? <COMMENT>? '\n'
<COMMENT>     ::= '#' /[^\n]*/
<INSTRUCTION> ::= <NAME> <TARGET>* <CONDITION>? <QUOTED_TEXT>?
<CONDITION>   ::= 'if' <BIT_ID>
<TARGET>      ::= <QUBIT_ID> | <BIT_ID> | <REGISTER_ID> | <EXPONENT>
<NAME>        ::= /[A-Z][A-Z0-9_]*/          (names are case sensitive; "x q0" is an error)
<QUBIT_ID>    ::= 'q' /[0-9]+/
<BIT_ID>      ::= 'b' /[0-9]+/
<REGISTER_ID> ::= 'r' /[0-9]+/
<EXPONENT>    ::= /[-+]?[0-9]+\.[0-9]+/      (decimal with a mandatory '.', no exponent notation)
<QUOTED_TEXT> ::= '"' /[^"#\n\r]*/ '"'       (escapes: \B=\  \Q="  \P=#  \n  \r)
```

Parsing facts (all **measured** unless noted):

- Tokens are separated by spaces/tabs; a `#` ends the instruction anywhere (`X q0 # comment` is fine).
  `#` inside quoted text must be escaped as `\P` (`mutable_circuit.cc:108, 137-173`).
- Only the operand types the opcode declares are read; extra tokens give `unexpected_term`
  (`X q0 q1` is rejected). A second `if` is silently ignored: `X q0 if b0 if b1` parses as `X q0 if b0`
  (`try_read_cond` reads a single word after the operands, `mutable_circuit.cc:212-222, 408`).
- Ids are parsed with `try_parse_uint32_t_below_max`; the ceiling is strict (`result >= max` fails), and
  `MAX_NUM_QUBITS`/`MAX_NUM_BITS` are such that `q4294967294` is already `number_too_large`.
  Practically: ids must fit comfortably in 32 bits minus a tag bit (`id/qubit_id.h`).
- Exponent must match `/[-+]?[0-9]+\.[0-9]+/`: `Z_POW q0 1`, `Z_POW q0 .5`, `Z_POW q0 5e-1` are errors.
  Angles are rounded to the nearest multiple of 2^-127 half-turns and canonicalised to [0, 2)
  half-turns on output (`-0.25` prints back as `1.75`; `2.25` prints as `0.25`).
- `PUSH_CONDITION` *requires* `if bN` (`missing_condition`); `POP_CONDITION` and `INFO_TAG` *forbid* it
  (`unexpected_condition`). Every other instruction accepts an optional `if bN`
  (`mutable_circuit.cc:56-76`).
- A qubit may not appear twice in one instruction: `CX q0 q0` raises "Circuit is invalid due to a qubit
  collision" at validation (`circuit.cc:422-492`). The Python builder raises the same error at
  `finish_circuit()`.
- `REGISTER r0 "n"` followed by `REGISTER r0 "m"` keeps the last name. Declaring `rK` implicitly creates
  empty registers `r0..r(K-1)`.
- Qubits/bits that appear only in `APPEND_TO_REGISTER` still count toward `num_qubits`/`num_bits`.

### 1.2 Instruction set (`circuit/op_type.h:34-101`; official list in `kickmix_instructions.md`)

Operand order in the text format is *controls first, target last*. Every row accepts an optional trailing
`if bN` except where noted. The simulator semantics column is the literal bit-vector update from
`sim/sim.h:296-513` (`phase` is the per-shot sign bit, `angle` the per-shot 128-bit accumulator).

| Instruction | Operands | Simulator semantics | Cost class |
|---|---|---|---|
| `X q` | 1 qubit | `q ^= 1` | free |
| `CX c t` | 2 qubits | `t ^= c` | free (Clifford) |
| `CCX c1 c2 t` | 3 qubits | `t ^= c1 & c2` | **Toffoli-like** |
| `Z q` | 1 qubit | `phase ^= q` | free |
| `CZ a b` | 2 qubits | `phase ^= a & b` | free |
| `CCZ a b c` | 3 qubits | `phase ^= a & b & c` | **Toffoli-like** |
| `Z_POW q t` | 1 qubit + exponent | if `q`: `angle += t` half-turns (= `Z**t`, phases \|1> by e^{iπt}) | by hierarchy level |
| `NEG` | none | `phase ^= 1` (global phase; exists only for fuzz-test bookkeeping) | free |
| `SWAP a b` | 2 qubits | exchange | free |
| `CSWAP c a b` | 3 qubits | exchange `a,b` if `c` | **Toffoli-like** |
| `R q` | 1 qubit | `phase ^= q & random`; `q = 0` (dephases as an X-basis measurement with a discarded result) | free |
| `HMR q b` | 1 qubit, 1 bit | `b = random`; `phase ^= q & b`; `q = 0` | free |
| `BIT_INVERT b` | 1 bit | `b ^= 1` | free |
| `BIT_STORE0 b` / `BIT_STORE1 b` | 1 bit | `b = 0` / `b = 1` | free |
| `PUSH_CONDITION if b` | condition only (mandatory) | pushes `(current & b)` onto the condition stack | free |
| `POP_CONDITION` | none (no `if` allowed) | pops (no-op if empty) | free |
| `REGISTER rN ["name"]` | register id, optional quoted name | metadata only, not an op (not counted by `len(circuit)`) | free |
| `APPEND_TO_REGISTER qN rM` / `bN rM` | qubit-or-bit, register | appends (LSB first) | free |
| `INFO_TAG "text"` | quoted text (no `if`) | no effect; `@enter:NAME` / `@exit:NAME` mark subroutines for flame charts | free |
| `DEBUG_PRINT [q\|b\|r]*` | 0..n targets | asks the simulator to print; a register expands to one op per element | free |

How an `if bN` is encoded: each opcode has an `OP_HAS_COND = 0x80` flag bit; `X q0 if b3` is the opcode
`X_IF` (`op_type.h:64-100`). `OperationStatistics` sums the conditional and unconditional variants under
the base name.

Operand conventions used throughout the library and the paper: registers are **little-endian**
(`APPEND_TO_REGISTER` order = increasing significance), and the values the simulator reads/writes for a
register are plain unsigned integers.

### 1.3 Bits vs qubits vs X-basis bits (`xb`)

- `qN` are qubits (simulated as bits + phase bookkeeping). `bN` are classical bits: they can be written
  irreversibly (`BIT_STORE*`), used as `if` conditions, and are the only legal targets of `HMR`.
- There is **no `xb` token in the text format**. `km.xb(n)` / `km.xbool(v)` are *Python builder-level*
  types (`py/val/id.pybind.cc`): an `xb` is "the bit `bN` that an `HMR` just produced, interpreted as an
  X-basis value". Giving an `xb` as the *target* of a bit-flip operation turns the operation into a
  *phase* operation conditioned on that bit. **Measured** downgrades (`build/circuit_builder.cc:789-800`,
  `py/circuit/ops/cx.cc`):
  - `cx(q0, xb(0))` -> `Z q0 if b0`;  `cx(b1, xb(2))` -> `PUSH_CONDITION if b2; NEG if b1; POP_CONDITION`;
    `cx(True, xb(3))` -> `NEG if b3`; `cx(q1, xbool(True))` -> `Z q1`; `cx(q1, xbool(False))` -> nothing.
  - `x(xb(5))` -> `NEG if b5`; `x('|->')` -> `NEG`; `swap(xb(0), xb(1))` -> three `BIT_INVERT ... if ...`.
  - `ccx(..., xb)` is **not** accepted by the Python `ccx` (target must be qubits); use `del_and` or
    `cx`. `z(xb)` is rejected ("can't phase flip X_BIT_ID values").
  This is how measurement-based uncomputation is written: `mx = hmr_raii_xbit(q)` then
  `ccx(c1, c2, mx)` emits `HMR q b; CZ c1 c2 if b` (`circuit_builder.cc:939-942`).

### 1.4 The `.kmb` binary format (`circuit/circuit.cc:1238-1452`, `kickmix_binary_format.md`)

- Magic: 16 bytes `d7 50 c7 d5 c3 29 d3 26 e3 cc 9f 68 34 f2 b8 bf` (`circuit.cc:19-20`). The reader
  autodetects: if the first byte is `0xd7` it insists on the full magic, otherwise it parses text
  (`circuit.cc:121-150`), so `Circuit.from_file(path)` (format `'auto'`) works for both.
- **All integers are little-endian** on disk (the helper names `write_u32_be` are misleading; they only
  byte-swap on big-endian hosts, `util/binary_file_tools.cc`; the official doc says little-endian;
  **measured**: `version` bytes are `02 00 00 00`).
- Header: `magic[16]`, `u32 version (=2)`, `u32 num_qubits`, `u32 num_bits`, `u32 num_registers`, then
  `u64` counts: `num_ops, num_qqq_ops, num_qq_ops, num_q_ops, num_b_ops, num_c_ops, num_angle_ops,
  num_info_tags, num_info_tag_chars`.
- Then fixed-order packets, each `u64 type, u64 payload_len, payload`: one `REGISTER_TARGETS` packet per
  register (`u32 name_len, u32 count, name, u32 ids` with bit 31 set for qubits), `OPERATION_TYPES`
  (one opcode byte per op), then the struct-of-arrays target blobs `qqq0,qqq1,qqq2,qq0,qq1,q0,b0,bc`
  (u32 each), `ANGLE_DATA` (16 bytes per Z_POW), `INFO_TAG_DATA`. Trailing bytes are an error; the header
  `num_qubits`/`num_bits` must equal `max id + 1` (else 0) or loading fails (`circuit.cc:1436-1450`).
- Size: **measured** 1.37M-op adder circuit = 12.9 MB kmb (~9.4 B/op) vs 17.4 MB kmx; kmb read 0.02 s vs
  kmx read 0.57 s.
- Conversion: Python `circuit.to_file(path, format='kmb'|'kmx')`, `km.Circuit.from_file(path, format=
  'auto'|'kmx'|'kmb')` (file objects must be opened in binary mode for kmb); CLI `kickmix kmx2kmb --in
  a.kmx --out a.kmb` / `kickmix kmb2kmx`. The competition hashes the *canonical kmb bytes* (SHA-256 +
  salt) to seed the verifier PRNG (paper Sec. II C), so any byte change re-rolls the test inputs.

---

## 2. Simulation semantics

### 2.1 State and phase tracking (`sim/sim.h:72-137`)

Per batch of `BATCH_SIZE` shots (one bit per shot in a SIMD word), the simulator stores: one word per
qubit, one word per bit, one word of global sign (`state_block[0]`), a per-shot
`FixedPrecisionAngle128 angles[shot]`, and a `condition_stack` of words. The phase of a shot is
`angles[shot]` rotated by 180 degrees if the sign bit is set (`read_shot_phase`, `sim.h:131-137`).
Units are **half-turns** everywhere in the API: `Z` = 1.0, `S` = 0.5, `T` = 0.25; values are reduced
mod 2 into [0, 2). `Simulator.read_shot_phase(i)` returns `0`, `1`, or a `fractions.Fraction`
(**measured**: `X; Z_POW 0.25; Z_POW 0.25; Z_POW -0.75; Z_POW 1.75` -> `Fraction(3, 2)`).
`read_phase_flipped_across_shots()` only works when every shot's angle is exactly 0 or 1 half-turn;
otherwise it raises "Phase angles other than 0 and 1 are present" (**measured**).

Z_POW is the one instruction that is not bit-parallel: for each shot whose qubit is 1 and condition
active, the angle is added with 128-bit arithmetic (`sim.h:380-394`). **Measured** throughput
~320 M shot-ops/s when the qubits are 1 vs ~11 G shot-ops/s for Clifford/Toffoli ops.

### 2.2 HMR, R, and what "random measurement outcome" means (`sim.h:408-432`)

```
HMR q b:   b = rng.next();  phase ^= q & b;  q = 0
R q:       phase ^= q & rng.next();  q = 0
```

- Outcomes are uniform (**measured** 48% ones over 64 shots), drawn from a ChaCha8 stream
  (`util/chacha.h`) seeded from `std::mt19937_64`.
- Python: `km.Simulator(batch_size, seed=int)` takes a 256-bit integer seed (`0 <= seed < 2**256`, else
  `ValueError`); `None` seeds from OS entropy. **Measured**: same seed gives identical outcome bits, a
  different seed differs. The competition seeds from SHA-256(kmb bytes || salt) (paper Sec. II C,
  Benchmark I "Verification strategy").
- `HMR` on a qubit that is |0> never flips the phase. `HMR` on |1> flips the phase in the shots where the
  outcome is 1; the circuit must cancel this with `NEG if b` / `Z q if b` / `CZ a b if b` /
  `CCZ ... if b`. **Measured**: `X q0; HMR q0 b0; NEG if b0` -> zero phase flips; `X q0; HMR q0 b0`
  alone -> flips exactly in shots with `b0 = 1`.
- `R` on |1> randomises the phase with probability 1/2 and **cannot be fixed** (no outcome bit is
  recorded). **Measured**: `X q0; R q0` -> 31/64 shots phase-flipped. So `R` is only for qubits already
  at |0>; it is effectively an assertion. `init_*` builder methods emit `R` on their targets first,
  "transforming any bit errors into probabilistic phase errors" (docstring of `init_lookup`).
- An uncorrected measurement-based uncomputation of an AND ancilla (`R q2; CCX q0 q1 q2; HMR q2 b0` with
  inputs 11) fails ~50% of shots (**measured** 116/256), which is the failure mode the format is designed
  to expose.
- Under a false condition (`if b` or an unsatisfied `PUSH_CONDITION`), `HMR` does nothing *including not
  writing the output bit* (**measured**). Note the simulator still consumes a random number for the shot
  (`sim.h:416` masks the RNG output with `cond`), so the PRNG stream position depends on circuit
  structure, not on branch outcomes.

### 2.3 Condition stack (`sim.h:300, 475-491`)

- `PUSH_CONDITION if b` pushes `current_base_condition & b` — the bit's value *at push time*; later
  writes to `b` do not change the stack (**measured**). `POP_CONDITION` on an empty stack is a no-op
  (**measured**). Everything except `PUSH_CONDITION`, `POP_CONDITION`, `REGISTER`,
  `APPEND_TO_REGISTER`, `INFO_TAG` is skipped while any pushed condition is false. `Circuit.
  compute_max_condition_depth()` exists in C++ (`circuit.cc:742-754`). The Python builder's
  `push_condition` only accepts `km.b`.
- Per-op `if bN` and the stack compose by AND (`cond = current_base_condition & bits[bN]`).

### 2.4 What "clean ancilla", "error", and verification mean

- The C++ `CircuitFuzzer` (`sim/fuzzer.h:152-168`, `fuzzer.cc:155-305`) is the reference notion of
  correctness. Registers named `@clean` are initialised to zero, `@dirty` to random, and any qubit that
  belongs to no register is collected into a synthetic `@unassigned` register initialised to zero. A shot
  is an **error** if any register's output differs from the expected output (by default: equal to the
  input, unless the output sampler changes it) **or** the phase differs from the expected phase
  (`process_shot_data`, `fuzzer.cc:51-130`; `ignore_global_phase` disables the latter). Expected outputs
  for `@clean`/`@unassigned` are zero, so a scratch qubit left at |1> is an error, and a *dirty* ancilla
  must be returned exactly to its random input value.
- The competition verifier (paper Sec. II C, Benchmark I Sec. III A 3) checks three things per shot:
  (1) input/output registers hold the expected bitstrings, (2) **every scratch qubit returns to |0>**,
  (3) the accumulated phase matches the target within tolerance. For Benchmark I: the file must declare
  exactly one named quantum register `"x"` of 22 distinct qubits; all other qubits are unnamed scratch
  that must end at |0>; every x in [1, max x] is run 64 times (to sample HMR/R outcomes); phase compared
  in 64-bit fixed point *turns* (kickmix reports half-turns, so divide by 2).
- A Python recipe to self-verify (see `exp5.py:verify_identity`): build with `create_quantum_register`
  for named inputs, `alloc_qubits` for scratch, run `Simulator.use_same_registers_as(circuit)`,
  `write_within_shot`, `do`, then check named registers, `read_across_shots(km.q(i))` for all unnamed
  ids `< circuit.num_qubits`, and `read_shot_phase(i)` for every shot.
- `Circuit.operation_statistics()` is static (counts every mention, even mutually exclusive
  `PUSH_CONDITION` branches); `Simulator(counting_operations=True).operation_statistics(shot_index)` counts
  only ops whose condition held in that shot; `PUSH/POP_CONDITION` and `INFO_TAG` are always counted
  (`sim.h:478-497, 505-509`). Enabling counting costs ~1.8x (**measured**; docs say 2-4x).

---

## 3. Resource accounting (`py/operation_statistics.pybind.cc:118-158`, `util/fixed_precision_angle_128.cc:15-23`)

| Metric | Definition (exact) |
|---|---|
| `num_toffoli_like` | `CCX + CCX_IF + CCZ + CCZ_IF + CSWAP + CSWAP_IF` |
| `num_t_like` | `Z_POW` ops at Clifford-hierarchy level exactly 3 (odd multiples of 0.25 half-turns, incl. conditional ones) |
| `num_z_pow(min_level=0, max_level=None)` | `Z_POW` ops whose level is in `[min, max]` |
| `z_pow_clifford_hierarchy_counts` | `{level: count}` for present levels |
| `num_non_clifford` | `num_toffoli_like + num_z_pow(3)` (level >= 3) |
| `num_instructions` | total ops of all types (INFO_TAG, PUSH/POP included; REGISTER lines excluded) |
| `stats['X']`, `stats['CCX']`, ... | per-base-name counts, conditional variants merged |

Clifford hierarchy level of an angle `t` (half-turns, stored as a 128-bit fraction of 2 half-turns):
`level = 0` for `t = 0`; `level = 128 - trailing_zero_bits(fraction)`, i.e. `t = odd * 2^(1-level)`:

| exponent (half-turns) | level | meaning |
|---|---|---|
| 0.0 | 0 | identity |
| 1.0 | 1 | Pauli Z |
| 0.5, 1.5 | 2 | S, S^-1 (Clifford) |
| 0.25, 0.75, 1.25, 1.75 | 3 | T-like |
| 0.125 (odd/8) | 4 | T^(1/2)-like |
| odd/2^(k-1) | k | |
| 0.1, 1/3, anything non-dyadic | **128** | rounded to 2^-127 grid, counted at level 128 |

**Measured**: `Z_POW q0 0.1` and `Z_POW q0 0.333...` both land at level 128; the builder rounds Python
floats via `fractions.Fraction` (so `1/3` as a float becomes the exact binary fraction
`0.333333333333333314829616256247390992939472198486328125`). Integer exponents (`z_pow(q, 2)`) become
`0.0`.

Surprises and quirks:

- **`CSWAP` counts as exactly 1 Toffoli-like**, same as `CCX` and `CCZ`; and a classically-controlled
  `CCX ... if b` still counts 1 even though it only runs in some shots (static count). A bit-controlled
  swap (`SWAP a b if b`) costs 0, so `cswap(km.b, ...)` is free while `cswap(km.q, ...)` costs one per
  qubit pair (**measured**: 8-wide cswap = 8 CSWAP vs 8 free SWAP_IF).
- `Z_POW` never contributes to `num_toffoli_like`. A `CCZ` written as 7 `Z_POW 0.25` + 6 `CX` would show
  `num_toffoli_like = 0, num_t_like = 7`. The competition price for Benchmark I is `C = Toffolis + T/4`
  with Clifford `Z_POW` free, level-3 `Z_POW` = 1 T, and finer rotations priced analytically at
  `0.56 log2(1/eps) + 5.3` T each (paper Sec. III A 3), so a CCZ-as-7T costs 1.75 Toffoli-equivalents,
  worse than a native CCZ (1.0). Benchmark III forbids `Z_POW` entirely and Benchmark II counts Toffolis
  only.
- `Circuit::estimate_ccz_state_weight()` (C++ only, `circuit.cc:764-766`) = `num_qqq_ops +
  ceil(num_angle_ops / 2)`, treating every `Z_POW` (even Clifford ones) as half a CCZ. It is not bound
  to Python.
- CLI `kickmix count_operations --magic` prints 3-qubit ops **plus all `Z_POW` ops including Clifford
  ones** (`cmd/main_count_operations.cc:48-57`). Do not use it as the competition metric.
- Multi-controlled X is compiled, not native: `k` quantum controls cost `k-1` Toffolis, `k-2` HMRs and
  `k-2` scratch qubits (AND ladder with measurement-based uncomputation, `py/circuit/subs/
  multi_control_x.pybind.cc`; **measured** k=3..32). A 4-control `cccx` in the C++ builder with a clean
  qubit costs 2 Toffolis + 1 HMR; with **no** clean qubit it silently uses a *dirty helper* (the
  smallest qubit id not among its operands) at **4 Toffolis** (`build/circuit_builder.cc:585-603`).
- `num_qubits` of a circuit is **max qubit id + 1**, not peak live qubits (`circuit.cc:990-1010`;
  **measured** `X q5` -> 6). Qubits mentioned only in `APPEND_TO_REGISTER` count. The paper's `Q` is "the
  circuit's total qubit count", i.e. this number (inferred from the verifier description; it has no
  liveness analysis). `num_bits` likewise = max bit id + 1.
- `reaction_depth()` (`circuit/circuit_util.cc:7-205`) counts the longest dependency chain of
  Toffoli-like gates and measurement-conditioned corrections, assuming CCZ-state injection; Clifford
  chains contribute 0. **Measured**: `CCX q0 q1 q2; CCX q2 q3 q4` -> 2 (docstring), two disjoint CCX
  -> 1, `CCX; HMR; CZ if b; CCX` on the same qubits -> 1, `CX q0 q1; CX q1 q2` -> 0, two `Z_POW` on one
  qubit -> 1.

---

## 4. The Python `CircuitBuilder` API

Top-level module: `km.Circuit`, `km.CircuitBuilder`, `km.Simulator`, `km.OperationStatistics`,
`km.UnaryIterationCursor`, `km.GF2Field`, `km.array`, ids `km.q(n)`, `km.b(n)`, `km.r(n)`, `km.xb(n)`,
`km.xbool(v)`. All builder methods broadcast over `km.array` arguments (zip semantics when several
arrays are given) and "downgrade" by operand type (bool/bit/qubit) — see 1.3 and the table in 4.2.

### 4.1 Allocation and registers (`py/circuit/circuit_builder.pybind.h:16-93`, `.cc:140-410`)

| Method | Signature | Notes |
|---|---|---|
| `create_quantum_register(length, name)` | -> `km.array` of `km.q` | emits `APPEND_TO_REGISTER`+`REGISTER`; counts toward `max_qubits` |
| `create_classical_register(length, name)` | -> array of `km.b` | |
| `alloc_qubits(count)` / `alloc_bits(count)` | -> array | `alloc_qubits` raises if `num_allocated_qubits + count > max_qubits` |
| `free(q \| b \| array \| sequence)` | | raises on double free / never-allocated id |
| `set_max_qubits(limit: int \| inf)` | | raising below current allocation is an error |
| `max_qubits`, `num_allocated_qubits`, `num_free_qubits` | properties | |
| `finish_circuit()` | -> `km.Circuit` | validates (qubit collisions) |
| `info_tag(text)`, `mark(name)` | | `mark` is a context manager emitting `@enter:`/`@exit:` tags |

Allocator model (**measured** + source): a LIFO free list. `alloc` pops the most recently freed id,
else takes `next_qubit_id++`. Freed qubits *are* reused (alloc 4, free q1 and q3, alloc 2 -> `[q3, q1]`).
Registers created after frees take fresh ids (`create_quantum_register` bypasses the free list).
Nothing resets or checks that freed qubits are at |0>; the docstring recommends `reset()` before reuse.
There is no notion of "dirty" allocation in Python; the C++ `CircuitGenCtx` distinguishes
`clean_workspace` (assumed |0>) from `dirty_workspace` (borrowed data qubits at rest)
(`build/circuit_gen_ctx.h`). Classical bits for HMR outputs inside generators come from the C++
`raii_bits` pool (`circuit_builder.cc:alloc_dirty_raii_bit`), which is why most subroutines use a single
reused bit (`nb = 1`).

How subroutines get workspace: each binding allocates `min(num_free_qubits, n)` (adders),
`len(address)` (lookups) or `max(1, len(address))` (unary iteration) qubits through the same allocator,
passes them as `clean_workspace`, and frees them afterwards (`py/circuit/subs/iadd.pybind.cc`,
`lookup.pybind.cc`). Consequently **`set_max_qubits` changes the circuits you get**: with
`max_qubits = inf` every subroutine takes the full clean workspace it wants; with a tight budget
generators switch to dirty-ancilla variants or raise. **Measured** (8-bit quantum `iadd`, spare qubits
above the two registers): spare 0 -> 13 Toffolis, 1 -> 12, 2 -> 11, 4 -> 9, >= 6 -> 7, all verified
correct by simulation. Classical-constant `iadd` needs at least 2 clean and `n` total ancillas or raises
(`gen_iadd_classical.cc`); constant comparisons need >= 3 clean (low-space variant, 12 Toffolis for n=8)
or `n-1` clean (7 Toffolis); quantum-quantum comparison needs >= 1 clean (15 Toffolis for n=8) or
`n-1` clean (8 Toffolis).

### 4.2 Gate-level methods

| Method | Emits (by operand type) |
|---|---|
| `x(target)` | `X q`; `BIT_INVERT b`; `NEG if b` for `xb`; `NEG` for `xbool(True)`/`'\|->'`; error for plain `bool` |
| `cx(control, target)` | `CX`; `X q if b`; `BIT_INVERT b if b`; `BIT_INVERT`/`X` for `True`; nothing for `False`; `xb`/`xbool` targets become `Z`/`NEG` (see 1.3); qubit control with bit target is an error |
| `ccx(c1, c2, target: q)` | `CCX`; `CX ... if b`; `PUSH_CONDITION if b1; X q if b2; POP_CONDITION` for two bits; `CX` for `True`; nothing for `False` |
| `cz(a, b)`, `ccz(a, b, c)` | downgrade likewise (`CZ q q if b`, `Z q if b`, `NEG if b`) |
| `z(target)` | `Z q`; `NEG if b`; `NEG` for True; rejects `xb` |
| `z_pow(target, exponent)` | `Z_POW`; exponent via `fractions.Fraction`, canonical [0,2), 2^-127 grid |
| `swap(a, b)` | `SWAP`; bits -> 3 conditional `BIT_INVERT`s |
| `cswap(control, a, b)` | `CSWAP` (1 Toffoli each) for qubit control; `SWAP ... if b` (free) for bit control; `SWAP` for True |
| `hmr(target, output)` | `HMR q b` (broadcasts; output must be bits) |
| `reset(target)` | `R q` |
| `neg()`, `neg_if(b)` | `NEG`, `NEG if b` |
| `bit_store(target, value, control=True)` | `BIT_STORE0/1 [if b]`; control must be classical |
| `push_condition(b)` / `pop_condition()` | stack ops |
| `init_and(c1, c2, t)` / `del_and(c1, c2, t)` | `R t; CCX c1 c2 t` / `HMR t b; CZ c1 c2 if b` (0 Toffolis to uncompute) |
| `multi_controlled_x(controls, target(s))` | see 3; bit controls become `PUSH_CONDITION`s; multiple targets fan out with CX |
| `debug_print(...)` | `DEBUG_PRINT` ops |

### 4.3 Arithmetic subroutines and measured costs

All `nq` values are `circuit.num_qubits` with `max_qubits = inf`, registers only (no other scratch);
ancilla = `nq - register qubits`. "Tof" = `num_toffoli_like`.

**`iadd(offset, *, target, control=True, btol=inf)` / `isub`** (`gen/adders/gen_iadd.cc`,
`gen_iadd_classical.cc`). In-place 2's-complement add mod `2**len(target)`.

| variant | Tof | HMR | ancilla | CX | formula |
|---|---|---|---|---|---|
| quantum offset, n=4/8/16/32/64 | 3/7/15/31/63 | 2/6/14/30/62 | 2/6/14/30/62 | 15/43/99/211/435 | **n-1 Tof, n-2 HMR, n-2 ancilla, ~7n-13 CX** |
| quantum offset, qubit-controlled, n=4/8/16/32 | 11/19/35/67 | 2/6/14/30 | n-2 | | **2n+3 Tof** |
| classical constant (odd) or classical-bit register, n=4/8/16/32 | 2/6/14/30 | 3/7/15/31 | n-1 | n | **n-2 Tof** |
| classical constant, qubit-controlled, n=4/8/16/32 | 5/9/17/33 | 3/7/15/31 | n | | **n+1 Tof** |
| `iadd(1)` increment n=4..32 | n-2 | n-1 | n-1 | n | |
| n-bit quantum offset into 2n-bit target, n=4/8 | 8/20 | 5/9 | | | pads offset with clean qubits (`gen_iadd.cc:33-48`) |
| `isub` quantum | same as `iadd` (conjugated by X) | | | | |

The quantum adder is Gidney's temporary-logical-AND ripple adder (`CCX` into a fresh ancilla per bit,
carry propagated by CX, uncomputed with `HMR` + `CZ ... if b`), with the control folded in via
`cccx`/`mux_ccx`. The constant adder is a carry-ripple that uses `parity_ccx` tricks and the same
measurement-based uncomputation; it degrades gracefully to a "vented carries" dirty-ancilla form
(`gen_iadd_classical.cc:280-420`). `btol`: for classical offsets only, carries into the leading run of
identical offset bits are skipped: **measured** 8-bit `iadd(0b11110000, btol=2)` -> 4 Tof (6 exact),
`iadd(0b10000000, btol=2)` -> 6 (no run to skip). `btol` with a quantum offset raises.

**Comparators** `flip_if_less_than / flip_if_greater_than(lhs, rhs, *, target, or_equal=False,
control=True, btol=inf)`, `flip_if_equal(lhs, rhs, *, target, control=True)` (`gen/comparators/`).
Keyword-only `target`.

| variant (n bits) | Tof | HMR | ancilla |
|---|---|---|---|
| `< const` / `> const` | n-1 | n-1 | n-1 |
| `< quantum` | n | n-1 | n-1 (2n with both inputs) |
| `< quantum`, qubit-controlled | n+2 | n | n-1 |
| `== const` | n | n | n |
| `== quantum` | n | n | n |
| `< quantum, btol=k` (n=16) | k-1 (2->1, 4->3, 8->7), exact at k>=n | | |

Algorithm: `gen_flip_if_lt` computes a carry chain of "all more-significant bits equal so far" ANDs
into clean qubits, flips the output with a `cccx`, and uncomputes every AND by `HMR` + conditioned
`Z/CZ` corrections (`gen_cmp.cc`). With fewer than `n-1` clean qubits and a classical rhs it falls back
to `gen_xif_less_than_3anc_2ntof` (3 clean ancillas, ~2n Toffolis via toggle detection,
`gen_cmp_low_space.cc`); with a quantum rhs and little workspace it uses `gen_flip_if_lt_qq`
(in-place subtraction-style chain, `gen_cmp_qq.cc`). `btol` keeps only the top `ceil(btol)` bits.

**`init_lookup(*, table, address, target)` / `del_lookup(...)`** (`gen/lookup/gen_lookup.cc`,
`py/circuit/subs/lookup.pybind.cc`). QROM. `table` must have **exactly `2**len(address)`** entries
(shorter tables raise "table contents didn't match"); `len(address) <= 32`; `target` width `w` =
number of output bits (little-endian). `init_lookup` resets the targets first.

| N = 2^a (a address bits) | init Tof | init HMR | init ancilla | del Tof (w=1 / w=8) | del classical bits |
|---|---|---|---|---|---|
| 2 (a=1) | 0 | 1 | 1 | 0 / 0 | 3 |
| 4 | 2 | 3 | 2 | 0 / 0 | 5 |
| 8 | 6 | 7 | 3 | 2 / 2 | 9 |
| 16 | 14 | 15 | 4 | 3 / 3 | 17 |
| 32 | 30 | 31 | 5 | 7 / 7 | 33 |
| 64 | 62 | 63 | 6 | **error** / 10 | 65 |
| 128 | 126 | 127 | 7 | error / 18 | 129 |
| 256 | 254 | 255 | 8 | error / 25 | 257 |
| 512 | 510 | 511 | 9 | error / 41 | 513 |
| 1024 | 1022 | 1023 | 10 | error / error | |
| 4096 | 4094 | 4095 | 12 | | |

- `init_lookup` is **unary iteration over the address** (`gen_lookup.cc:153-212`: one `reset_and` per
  recursion level, `del_and` to uncompute): **N-2 Toffolis, N-1 HMR, `a` ancillas, CX count ~ number
  of set table bits** (an all-zero table still costs N-2 Toffolis; the control ladder is table-blind).
  Output width `w` is free in Toffolis.
- `del_lookup` is the **measurement-based unlookup** (Berry et al. "phase lookup"): HMR every output
  qubit, build a `2^a`-entry *classical* phase table (allocates `2^a` classical bits, which is why
  `num_bits` explodes), then a `Z`-type lookup on the high half of the address with a
  binary-to-unary expansion of the low half (`gen_lookup.cc:73-151`). Cost ~ `2^(a-h) + 2^h`-ish
  Toffolis with `h = a//2` (measured table above).
- **Pitfall**: the Python `del_lookup` only hands the generator `len(address)` clean qubits, but the
  unary expansion needs `2^(a//2)` qubits drawn from (low address bits + output qubits + clean).
  It raises "tried to take 1 clean qubits, but only 0 were available" whenever
  `2^(a//2) - a//2 - w > a//2`, i.e. **w=1 fails for a>=6, w=8 fails for a>=10** (**measured**).
  **Workaround (verified correct by simulation)**: pass extra freshly allocated |0> qubits as part of
  `target` (`del_lookup(table=tbl, address=a, target=t + extra)`); the table's high bits are zero so the
  extra qubits are HMR'd harmlessly and serve as workspace (a=6, w=1 works with one extra qubit).
- `del_lookup` with the wrong table fails loudly: **measured** 11/256 shots with a wrong phase after
  flipping one table entry.
- Round trip `init_lookup` + `del_lookup` (a=4, w=3) **measured** correct: all addresses, ancillas at
  |0>, phase 0, 17 Toffolis total (14 + 3).

**`unary_iteration(address, address_values=None, *, control=True)`** (`gen/iteration/
gen_unary_iteration.cc`). Returns a reusable `UnaryIterationCursor`; `with cursor as it:` allocates
`max(1, len(address))` workspace qubits; `for v, m in it` or `it.move_to(v)`; `it.match_qubit` is ON
when `address == v` (and `control`). Use it only as a control, never modify `address` while open.
Cost (**measured**, full range over `a` bits, uncontrolled / qubit-controlled): Tof = `2^a - 2` /
`2^a - 1`, HMR = `2^a - 1`, ancilla `a`. Per-move cost: entering costs <= `a` Toffolis (`a-1`
uncontrolled), moving between `x` and `y` costs `bit_width(x ^ y) - 1`, closing costs 0 (tear-down is
all `del_and`). `address` <= 63 qubits; `address_values` must be a step-1 `range`. A cursor that is
never opened emits nothing; an unclosed cursor's destructor emits nothing (so always use `with`).

**`left_rotate(target, shift=1, *, control=True)` / `right_rotate`** (`gen/bits/gen_bit_rotate.cc`).
Constant shift: `n-1` SWAPs, 0 Toffolis (plus `log`-depth decomposition). Quantum shift register of
`log2 n` bits: barrel shifter of CSWAP layers, **measured** n=4/8/16/32 -> 4/13/36/91 CSWAPs (about
`n log2 n - n + ...`), +`log2(n)+1` CCX and HMR when additionally qubit-controlled (AND of control with
each shift bit).

**GF(2^m) arithmetic** (`gen/gf_arithmetic/`, Python `gf2_*`, `init_gf2_*`, `del_gf2_*`,
`ixor_gf2_*`; `km.GF2Field(degree, modulus=None, primitive_element=None)` defaults to a low-weight
primitive polynomial, accepts `galois` fields):

| op (m = 2/4/8/12/16/32/64) | Tof | notes |
|---|---|---|
| `init_gf2_mul(lhs, rhs)` / `ixor_gf2_mul` | 3/9/27/63/81/243/729 | in-place Karatsuba (Kepley–Steinwandt), `3^log2(m)`, no ancilla beyond target |
| `del_gf2_mul` | **0** | HMR outputs + `m^2` classically conditioned CZ (`gen_gf_phase_by_product`) |
| `init_gf2_mul(..., control=q)` | mul + m | computes into temp, controlled-add, free uncompute |
| `gf2_phase_by_product(lhs, rhs, mask=bits)` | 0 | phase kickback without materialising the product |
| `init_gf2_inverse` | 0/18/108/315/486/1944/7290 | Itoh–Tsujii addition chain; Frobenius (squaring) is CNOT-only; 6 registers for m=8 |
| `init_gf2_inverse_with_scaffold` | same Tof, no HMR, keeps chain (24 qubits for m=8) | `del_..._with_scaffold` is then **0 Toffolis** |
| `del_gf2_inverse` (no scaffold) | rebuilds the chain: same Tof again | |
| `init_gf2_div` | inverse + mul (135 for m=8) | `del_gf2_div` 108, `del_gf2_div_with_scaffold` 0 |
| `gf2_imul(const)`, `gf2_idiv(const)`, `gf2_iadd` | 0 | CNOT/SWAP linear maps (`gen_linear_map.cc`, PLU decomposition) |

Register disjointness is **not checked** by the GF generators (silently wrong results), though the
final `finish_circuit` catches direct same-qubit collisions.

Not exposed to Python (C++ only, `gen/modular_arithmetic/`, `gen/qft/`): `gen_iadd_mod`/`gen_isub_mod`
(add then subtract modulus on underflow, measurement-based uncompute of the underflow qubit),
`gen_imul2_mod`, `gen_ineg_mod`, `gen_idouble_approx_below_power_of_2`,
`gen_qft_demolition_measure`, `gen_iadd1`, `gen_binary_to_unary`/`gen_unary_to_binary`,
`masked_phase_by_prefix_using_dirty_workspace`, `gen_linear_map` directly.

### 4.4 `Simulator` (`py/interactive_simulator.pybind.cc`)

`km.Simulator(batch_size, *, debug_print=True, counting_operations=False, seed=None)`.
`do(circuit)` applies instructions to the persistent state (call `clear_for_shot()` between
independent runs; it clears qubits, bits, phases, condition stack but *not* operation statistics).
`use_same_registers_as(circuit)` enables register names/`km.r` in `read_/write_within_shot(index,
shot, value)` and `read_/write_across_shots(index, value)` (bit-packed ints, little-endian across
shots; `out=int` option). `read_shot_phase(i)`, `write_shot_phase(i, half_turns)`,
`read_phase_flipped_across_shots()`. `debug_print=True` writes `DEBUG_PRINT` output to **stderr**
(pass `False` or a callback). Internally shots are processed in 256-shot SIMD words
(`PY_SIM_WORD_BITS = 256`, `interactive_simulator.pybind.h:11`): **batch sizes 1..256 cost the same
time** (**measured** 0.029 s for both 1 and 64 and 256 shots of a 1.37M-op circuit).

---

## 5. The generator library (`gen/`)

| Directory | Generators | Technique | Python exposure |
|---|---|---|---|
| `adders/gen_iadd` | `gen_iadd`, `gen_isub` | Gidney temporary-AND ripple-carry adder (n-1 Tof, measurement-based uncompute); handles `target <= offset+1` sizes; dirty-carry fallback | `iadd`/`isub` with quantum offset |
| `adders/gen_iadd_classical` | `gen_iadd_classical`, `gen_isub_classical`, `gen_ixor_carries_from_addition`, `..._vented_carries`, `_simple` | constant/bit-register adder (n-2 Tof with n-1 clean ancillas; 2-clean + n-2 dirty variant with "vented" carry bits); `btol` carry truncation | `iadd`/`isub` with int or bit-register offset, `btol` |
| `adders/gen_iadd_control` | `gen_iadd_control` | controlled quantum add with carry-in | via `iadd(control=q)` |
| `adders/gen_iadd1` | `gen_iadd1` | increment | (C++ only) |
| `comparators/gen_cmp` | `gen_flip_if_lt/le/gt/ge/eq` | AND-ladder comparator, n-1 Tof | `flip_if_*` |
| `comparators/gen_cmp_qq` | `gen_flip_if_lt_qq` | low-workspace quantum-quantum compare (in-place borrow chain) | automatic fallback |
| `comparators/gen_cmp_low_space` | `gen_xif_less_than_3anc_2ntof`, `masked_phase_by_prefix_using_dirty_workspace` | toggle-detection with 3 clean ancillas, ~2n Tof (4n with dirty only) | automatic fallback |
| `lookup/gen_lookup` | `gen_lookup` (X or Z type, controlled), `gen_unlookup`, `gen_binary_to_unary`, `gen_unary_to_binary` | unary-iteration QROM (N-2 Tof); measurement-based unlookup with classical phase table and select-swap-style unary expansion | `init_lookup`, `del_lookup` |
| `iteration/gen_unary_iteration` | `UnaryIterationCursor`, `gen_unary_iteration` | Babbush et al. unary iteration with random-access `move_to` | `unary_iteration` |
| `bits/gen_bit_rotate` | `gen_left_rotate`, `gen_right_rotate` | SWAP networks / CSWAP barrel shifter | `left_rotate`, `right_rotate` |
| `gf_arithmetic/*` | `gen_gf_mul/unmul/phase_by_product`, `gen_gf_inverse/uninverse` (+chain), `gen_gf_div/undiv`, `gen_gf_imul_x`, `gen_gf_imul_classical`, `gen_gf_ifrobenius`, `gen_gf_iadd`, `gen_linear_map` | in-place Karatsuba, Itoh–Tsujii, Frobenius-as-linear-map, PLU CNOT synthesis | all exposed (`gf2_*`) |
| `modular_arithmetic/*` | `gen_iadd_mod`, `gen_isub_mod`, `gen_imul2_mod`, `gen_imul2_inv_mod`, `gen_ineg_mod`, `gen_idouble/ihalve_approx_below_power_of_2` | compare-and-correct modular ops | not exposed |
| `qft/gen_qft_demolition_measure` | demolition frequency-basis measurement | `HMR` + conditioned `Z_POW` corrections (inferred) | not exposed |

Common C++ plumbing: `CircuitGenCtx{clean_workspace, dirty_workspace, minimize_qubits}`
(`build/circuit_gen_ctx.h`), `take_clean(n, name)` which throws the "tried to take N clean qubits"
error, `CircuitBuilder::c_push/c_resolve` for building multi-controlled ops with mixed
qubit/bit/bool controls (`circuit_builder.cc:687-786`; at most 3 qubit controls for X, 4 for Z),
`parity_ccx` (controls given as XOR pairs), `hmr_raii_xbit`, `raii_push_condition`, and `for_each`
loop builders (`build/circuit_pattern.h`) that emit repeated patterns fast.

---

## 6. Memory / qubit model summary

- Circuit-level: `num_qubits = max qubit id + 1`, `num_bits = max bit id + 1`; the simulator allocates
  one SIMD word per qubit/bit (`sim.h:280-294`), so sparse ids waste memory but are legal.
- Builder-level (Python): LIFO free list; `alloc_qubits` reuses freed ids; `create_*_register` uses fresh
  ids; `set_max_qubits` bounds *live* allocations (`num_allocated_qubits`) and indirectly selects
  lower-workspace generator variants. There is no peak-usage query; peak = `finish_circuit().num_qubits`
  when all qubits come from the allocator.
- Builder-level (C++): `CircuitBuilder` only has `next_qubit_id`/`reserve_qubits`; no free list. Generators
  take explicit `clean`/`dirty` spans. A `cccx` with no clean qubit borrows an arbitrary *dirty* qubit
  (lowest id not in the gate), costing 4 Toffolis.
- Classical bits: generators mostly reuse one RAII bit; `del_lookup` allocates `2^a` bits. Bits are
  free in every cost model.
- Freed qubits are *not* cleaned; `init_*` methods emit `R` on targets, `del_*` leave targets at |0>
  but do not free them.

---

## 7. CLI tools (`cmd/`, entry `main.cc`)

Build (Bazel, `kickmix/BUILD`): `bazel build //:kickmix` (binary, `-O3 -march=native`),
`//:kickmix_test`, `//:kickmix_perf`, `//:kickmix.so` + `//:kickmix_dev_wheel`. The pip wheel is built
from `setup.py` with `-O3 -std=c++20 -mno-avx` on x86 (so the wheel's SIMD words are the SSE/polyfill
variants, `simd/simd.h`); all `*.test.cc`, `*.perf.cc`, `main.cc` are excluded from the extension.
`pip install ./kickmix` (needs `pybind11==2.12.0`).

Subcommands (`kickmix <sub> [--in file] [--out file] ...`; `--in` defaults to stdin and autodetects
kmx/kmb):

| Subcommand | Flags | Purpose |
|---|---|---|
| `circuit` | `--kind {iadd, flip_if_lt, iadd_classical, iadd_classical_simple, imul2_mod, lookup, unlookup}`, `--n`, `--w`, `--mod`, `--clean`, `--dirty`, `--controlled`, `--btol`, `--minimize_qubits`, `--validate`, `--kmb`, `--diagram`, `--flame_out`, `--skip_output`, `--out` | generate a benchmark circuit from the C++ generators (`main_generate_circuit.cc:35-230`) |
| `count_operations` | `--groups`, `--magic` | static per-opcode counts; `--magic` prints 3-qubit ops + all Z_POW |
| `count_operations_sampled` | `--shots`, `--init`, `--groups` | counts only executed ops over simulated shots (b64 word) |
| `sample` | `--shots`, `--init`, `--decimal`, `--hex` | run shots; prints `(before)reg, reg, ..., global_phase` rows (`main_sample.cc`) |
| `spin` | `--shots`, `--mode {64,128,256,512,*-polyfill}` | timing benchmark; prints ops/sec |
| `diagram` | `--kind` (text/html/svg) | draw a circuit |
| `kmx2kmb` / `kmb2kmx` | | format conversion |

`--init` strings (`sim/sim.cc:12-65`): comma-separated `rN=VALUE` (fixed), `rN<VALUE` (uniform random
below VALUE), `rN=*` (uniform random over the register), e.g. `r0=5,r1<0x500,r2=*`.

---

## 8. Performance notes (**measured** on this container, AVX-512 CPU, pip wheel built with `-mno-avx`)

- Build: 1.37M-instruction circuit (2000 x 64-bit `iadd`) in 0.04 s = ~35 M instr/s from Python
  (paper: 2e7/s).
- Simulate: 45 M instr/s per 256-shot word, i.e. **~11.6 G shot-instructions/s** at batch 256; batch
  sizes 1..256 take the same time; 1024 and 4096 scale linearly (`0.13 s`, `0.49 s`). Paper quotes
  6e10/s for the native `-march=native` build with 512-bit words.
- `counting_operations=True`: ~1.8x slower.
- `Z_POW`: ~0.3 G shot-ops/s when the target qubit is 1 (serial per-shot 128-bit adds); ~1.3 G when the
  qubits are 0 (mask scan only).
- I/O: kmb write 0.04 s / read 0.02 s vs kmx 0.5 s / 0.6 s for 1.37M ops.
- `DEBUG_PRINT` with the default `debug_print=True` goes to stderr for every shot word; disable for big
  runs.

---

## 9. Pitfalls and gotchas (from tests, docs, and experiments)

1. **Scoring counts `CSWAP`, `CCX`, `CCZ` identically (1 each) and ignores `Z_POW`** in
   `num_toffoli_like`; the competition adds `T/4` for level-3 angles and prices finer angles
   analytically. Replacing a Toffoli by 7 T gates is a loss under `C = Tof + T/4`.
2. **`num_qubits` is `max id + 1`**. Ancilla ids left over from early allocations stay in the count even
   if freed and never reused; keep allocations LIFO and tight, and prefer reusing freed scratch.
3. **`R` on a non-zero qubit cannot be fixed** (random unrecorded phase). Use `HMR` and correct the
   kickback, or ensure the qubit is already |0>.
4. **`HMR` on a qubit that is not a Z-basis function of the rest** is simulated incorrectly on purpose and
   fails half the shots. Measurement outcomes under a false condition are not written.
5. `PUSH_CONDITION` snapshots the bit value; later writes do not affect the stack. `POP_CONDITION` on an
   empty stack is silently ignored. Static `operation_statistics()` double-counts mutually exclusive
   conditional branches; use `Simulator(counting_operations=True)` for per-shot counts.
6. `del_lookup` needs more clean qubits than the binding gives it when `2^(a//2) > 2*(a//2) + w`
   (e.g. 1-bit outputs with >= 6 address bits). Pad `target` with extra |0> qubits.
7. `init_lookup`/`del_lookup` require `len(table) == 2**len(address)` exactly and `len(address) <= 32`;
   tables are little-endian ints, `table[addr] >> k & 1` is output bit `k`.
8. `set_max_qubits` silently changes generated circuits (Toffoli count goes up as workspace shrinks) and
   some generators raise ("need 2 clean qubits", "tried to take 3 clean qubits"). With `max_qubits=inf`
   each subroutine takes up to `n` clean qubits.
9. `flip_if_*`, `iadd`, `isub`, `init_lookup`, `del_lookup`: `target` is **keyword-only**
   (`iadd_test.py:136`, `flip_if_cmp_test.py:215`). `btol` only works for classical offsets.
10. `unary_iteration`: `address_values` must be a step-1 `range`; address <= 63 qubits; cursor must be
    closed (use `with`); do not touch `address`/`control`/`match_qubit` while open; "Not enough free
    qubits" if `max_qubits` is tight (`unary_iteration_test.py:408`).
11. GF generators do not check register disjointness; `gf2_imul`/`gf2_idiv` accept only non-zero
    classical constants that are field elements (`gf_arithmetic_test.py:781-813`), quantum factors
    raise `NotImplementedError`; `field` must be `None`, `km.GF2Field`, or a `galois.GF` of
    characteristic 2.
12. `cx(q, b)` (quantum control, classical target), `bit_store(..., control=q)`, `push_condition(q)`,
    `x(True)` are type errors; `ccx(False, ...)`, `cx(False, ...)`, `cswap(False, ...)` emit nothing.
13. `z_pow` on `xbool`/`xb` is rejected; exponents must be `float | int | Fraction | str` (strings must
    parse as a `Fraction`; `"0.125"` works).
14. `read_phase_flipped_across_shots()` raises when any shot's angle is not 0 or 1 half-turn; use
    `read_shot_phase(i)`.
15. `Simulator` state persists across `do()` calls; call `clear_for_shot()` between experiments.
    Operation statistics persist across `clear_for_shot()` (use `clear_operation_statistics()`).
16. `Circuit + Circuit` keeps the left operand's register data (or the right's if the left has none);
    `Circuit * n` repeats instructions but not registers.
17. Text format: `Z_POW q0 1` and `.5` are parse errors; a stray `#` inside an `INFO_TAG` string must be
    `\P`; `x q0` (lowercase) is unknown; `X q0 if b0 if b1` silently drops the second condition.
18. `kmb` is little-endian despite `*_be` helper names; writing kmb to a text-mode Python file object is
    an error; `from_file(format='kmb')` on a kmx file raises "magic bytes".
19. `count_operations --magic` is not the competition metric (it includes Clifford `Z_POW`).
20. The `@clean`/`@dirty`/`@unassigned` naming convention is only honoured by the C++ fuzzer; the
    competition verifier instead requires exactly the named input registers and treats every other
    qubit as must-return-to-zero scratch.

---

## 10. Origin of the kickmix circuit class: the ECC paper (arXiv:2603.28846, PRX Quantum, DOI 10.1103/j3xf-bw18)

"Securing Elliptic Curve Cryptocurrencies against Quantum Vulnerabilities: Resource Estimates and
Mitigations" (Babbush, Zalcman, Gidney, Broughton, Khattar, Neven, Bergamaschi, Drake, Boneh) introduced
the term and the version-1 `.kmx` format; `kickmix_format.md` cites it as the origin and the companion
Kaggle paper (arXiv:2610.23832) builds on it. The relevant material is Appendix "Zero-Knowledge Proof"
Secs. 3–7 (PDF pp. 55–57; `ecc.txt:3290-3502` in the scratch extraction).

### 10.1 Formal definition (Appendix Sec. 4)

- *Measurement-based uncomputation (MBUC)*: if an ancilla `q` holds a deterministic Boolean function
  `f(k)` of the data register in every branch, `sum_k a_k |k>|f(k)>`, then measuring `q` in the Pauli-X
  basis yields two equally probable outcomes: `|+>` (False): `q` is disentangled, state becomes
  `sum_k a_k |k>`, nothing else to do; `|->` (True): `q` is erased but a phase kickback negates the
  amplitudes where `f(k) = 1`, state becomes `sum_k a_k (-1)^{f(k)} |k>`, and a phase correction that is a
  function of `k` must follow. The paper notes the correction is usually slightly cheaper (Gidney 2018
  adder) and sometimes much cheaper (Berry et al. 2019 phase-unlookup) than computing `f`.
- *Kickmix circuit* (verbatim definition): "the specific subclass of quantum circuits composed entirely
  of classical reversible logic gates, measurement-based uncomputation via Pauli-X basis measurements,
  and diagonal phasing gates for phase correction. By restricting the architecture exclusively to this
  gate set, we ensure the circuit never generates intractable quantum entanglement and can be efficiently
  simulated classically." Etymology: phase **kick**back + **mix**ing of classical states.
- Classical simulability rests on Gidney's 2019 note "Verifying Measurement Based Uncomputation"
  (algassert.com/post/1903, ref. [326]): track each qubit as a bit, sample each X-measurement outcome
  uniformly, and track the resulting sign. This is precisely `sim/sim.h:408-422`.

### 10.2 Verification guarantee (Appendix Secs. 3, 5, 6)

- Approximate correctness suffices: Shor's algorithm tolerates a small fraction of wrong superposition
  components ("1% of points in the wrong place" -> fails at most ~1% of the time), so the claim proved is
  that the circuit is correct on **at least 99% of inputs**.
- Fuzz testing with the **Fiat–Shamir heuristic**: inputs are derived from a SHAKE256 XOF seeded with the
  raw bytes of the circuit; the same XOF stream also supplies the PRNG for the simulated MBUC measurement
  outcomes. The soundness bound is the simple binomial one: if more than 1% of inputs were wrong, passing
  N = 9024 independent tests with zero failures has probability at most `(1 - 0.01)^9024 ~ 2^-130`, i.e.
  128-bit security. (The Kaggle paper generalises this to the Clopper–Pearson bound
  `eps+ ~ ln(1/delta)/N ~ 88.7/N` at `delta = 2^-128` and adds the trace-distance argument that a
  per-input failure rate `eps` on the verifier's input distribution bounds the coherent error by
  `2 sqrt(eps)`.)
- Each test is a single classical trajectory: the verifier checks the output register, and the
  simulator's tracked phase exposes any unfixed kickback. The ECC paper's test points are curve points
  `G * k` for random 256-bit `k`; correctness was checked on the point-addition output only (the kickmix
  format doc, written for this paper, adds that fuzz tests "must verify that the phase behaved as
  expected").
- The whole simulation ran inside the SP1 zkVM (Rust re-implementation of the kickmix simulator) and was
  wrapped in a Groth16 SNARK so the circuit stays secret: public outputs are the SHA-256 of the circuit
  bytes and the asserted resource bounds. Hash semantics changed between v1 and v2 of the paper: v2
  hashes the **circuit file bytes directly** rather than a serialised parsed object — the same convention
  the Kaggle verifier uses on the canonical `.kmb`.

### 10.3 Resource counting in that paper (Appendix Sec. 3, 6)

- "Non-Clifford gates" = **`CCX + CCZ`** only (the ZK statements: 2.7M non-Clifford / 1,175 qubits / 17M
  total ops for the low-qubit variant; 2.1M / 1,425 / 17M for the low-gate variant). The authors say
  "Toffoli count" loosely for this CCX+CCZ count.
- Because some instructions are conditioned on classical bits, they report the **average *executed*
  Toffoli count** over the 9024 test runs (the zkVM simulator counted executed CCX/CCZ per run) rather
  than the static count. "Total operations" (17M) is a static instruction count.
- "Logical qubits" is the qubit count of the circuit (the format doc notes simulators allocate memory
  proportional to the largest id, matching `num_qubits = max id + 1`).

### 10.4 Differences between the paper's description and the shipped library

| Aspect | ECC paper (v1 format / zkVM) | Shipped `kickmix` (v2 format, Qualtran) |
|---|---|---|
| Gate set | reversible classical gates + X-basis MBUC + diagonal phase corrections; non-Clifford = CCX, CCZ | adds native `CSWAP` (counted as Toffoli-like) and `Z_POW` with a 128-bit angle (classified by Clifford-hierarchy level); also `R`, `NEG`, classical `BIT_*` ops |
| Format | `.kmx` version 1 (no register names, no `Z_POW`, no `INFO_TAG`, no `CSWAP`) | version 2 text plus the `.kmb` binary format; v1 files remain valid v2 text |
| Measurement PRNG | SHAKE256 XOF seeded with the circuit bytes, shared with input generation | ChaCha8 seeded from a 256-bit integer (`Simulator(seed=...)`), caller supplies inputs; the Kaggle verifier seeds from SHA-256(kmb) + salt |
| Test count / bound | 9024 shots, 99% correctness at 2^-130 | benchmark-specific: exhaustive 64 shots/input (Bench. I), 102,400 shots with Clopper–Pearson `eps+` (Bench. II) |
| Phase check | correctness stated on outputs; phase tracked by the simulator | explicit: phase must match target within tolerance, scratch qubits must be |0> |
| Resource metric | average executed CCX+CCZ, qubits, total ops | static `num_toffoli_like` (CCX+CCZ+CSWAP, conditional variants counted once) plus `Z_POW` levels; per-shot executed counts available via `Simulator(counting_operations=True)` — the library offers both, the competition uses the static count plus `T/4` (Bench. I) |
| Simulator | Rust port inside SP1 zkVM | C++20 SIMD batch simulator (64–512 shots/word) with Python bindings |
| Verification artefact | Groth16 SNARK of the whole fuzz run | plain simulation; no ZK layer in the library |

Nothing in the shipped library contradicts the paper's definitions; the library is a strict superset
(more instructions, richer cost accounting, binary format) of the circuit class the paper defined.

---

## Appendix A. Measured cost tables (raw numbers)

Quantum-offset `iadd` (`n`: Tof / HMR / CX / num_qubits): 2: 1/0/2/4; 3: 2/1/8/7; 4: 3/2/15/10;
8: 7/6/43/22; 16: 15/14/99/46; 32: 31/30/211/94; 64: 63/62/435/190.

Constant `iadd` (n: Tof / HMR / num_qubits): 4: 2/3/7; 8: 6/7/15; 16: 14/15/31; 32: 30/31/63.
Qubit-controlled quantum `iadd`: 4: 11; 8: 19; 16: 35; 32: 67. Qubit-controlled constant: 5/9/17/33.

Comparators (n = 2/4/8/16/32): `<const` 1/3/7/15/31 Tof; `<qq` 2/4/8/16/32; `<qq` controlled
4/6/10/18/34; `==const` 2/4/8/16/32; `==qq` 2/4/8/16/32.

`init_lookup` (N: Tof): 2:0, 4:2, 8:6, 16:14, 32:30, 64:62, 256:254, 1024:1022, 4096:4094
(independent of `w`; CX grows with `w` and table density: N=1024, w=16 -> 9230 CX).
`del_lookup` (N, w=8: Tof): 8:2, 16:3, 32:7, 64:10, 128:18, 256:25, 512:41.

`unary_iteration` full sweep (a bits, uncontrolled/qubit-controlled Tof): 1: 0/1; 2: 2/3; 3: 6/7;
4: 14/15; 6: 62/63; 8: 254/255.

`multi_controlled_x` (k controls: Tof/HMR/ancilla): 3: 2/1/1; 4: 3/2/2; 5: 4/3/3; 8: 7/6/6;
16: 15/14/14; 32: 31/30/30.

`left_rotate` by quantum shift (n: CSWAP): 4: 4, 8: 13, 16: 36, 32: 91 (+3/4/5/6 CCX when controlled).

GF(2^m) (m: mul / cmul / inverse / inverse-with-scaffold qubits / div): 2: 3/5/0/4/3; 4: 9/13/18/12/27;
8: 27/35/108/40/135; 12: 63/75/315/72/378; 16: 81/97/486/112/567; 32: 243/275/1944/288/2187;
64: 729/793/7290/704/8019. `del_gf2_mul` = 0 Toffolis, `m` HMR.

## Appendix B. Competition scoring as stated in the paper (arXiv:2610.23832, Sec. III)

- Benchmark I (1/sqrt(x) phase oracle): `S = Q x C`, `C = Toffolis + T/4`; Clifford `Z_POW` free,
  level-3 `Z_POW` = 1 T, finer rotations `0.56 log2(1/eps) + 5.3` T each; all `3,133,452` inputs x 64
  shots must pass, tolerance `2^-24 beta/sqrt(x)` turns; register `"x"` (22 qubits) must be restored,
  all other qubits to |0>. Reference: Q=260, 7735 Toffoli, 1 T, 37 rotations, C=7988.
- Benchmark II (Reed–Solomon decoding for DQI): `S = R(eps+) Q^2 T` with `T` = Toffoli count including
  cleanup; 102,400 shots; zero failures still pays `R ~ 1.19`; `eps+ >= 1/16` scores infinity. Qubits
  weigh twice as much as Toffolis.
- Benchmark III (QROM/Majorana angle oracles): `S = lambda_eff T_tot Q_tot`; each `Angles_k` circuit
  may use at most 128 qubits; `Z_POW` **not allowed** (phases must be multiples of pi).
