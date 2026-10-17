# 19 — Hardware generators: Chisel → FIRRTL/CIRCT → SystemVerilog

Read [Hardware Generators and Modern HDL Toolchains](../../chapters/01-foundations/systemverilog.qmd#sec-hardware-generators). SystemVerilog remains the course's main language. This optional experiment uses a small Scala/Chisel generator, actual CIRCT lowering and independent simulation checks. No FPGA or processor generator is required; this is outside the nine automatic labs and the compulsory 6 ECTS workload.

## Contract and comparison

All operands and sums are unsigned. On each rising edge, synchronous active-high reset has first priority, then `Clear`, then `Enable`. Reset/clear zero the sum and both flags. Otherwise `Valid` equals the sampled enable, `Overflow` is the carry on that enabled addition, and disabled cycles retain the sum while clearing both flags. The sum wraps modulo 2^W; overflow is a pulse, not a sticky bit.

- `src/main/scala/Accumulator.scala` constructs widths 8, 16 and 32 and one faulty 16-bit configuration. `+&` retains the extra carry bit; Scala parameters select hardware at elaboration.
- `accumulator_sv.sv` directly expresses the same contract with a SystemVerilog parameter. At width 16 the testbench also instantiates the unchanged [original accumulator](../../examples/verilator/accumulator.sv).
- `run.py` creates expected results using Python integer arithmetic, then tests each RTL description against those results. Each positive configuration has 552 sampled cycles: directed reset/priority/overflow/hold boundaries and 512 seeded random cases. Stimulus changes before the rising edge; checks occur after nonblocking updates.
- The faulty generator uses `Clear && !Enable` as its clear condition. The test must fail with `GENERATED_MISMATCH cycle=1` when clear and enable are both asserted. A compiler failure is not accepted as the expected mismatch.
- Both positive descriptions are synthesized with the same Yosys generic flow (`synth -noabc`). Cell-type/count statistics describe that generic netlist, not FPGA resources, ASIC area, timing or power.

Passing the sampled regression is not an all-traces equivalence proof. Neither textual similarity nor equal cell counts supplies such a proof. A formal extension should map corresponding inputs/outputs and specify sampled reset and initial-state assumptions before constructing a miter; see the [formal practice](../15-formal/README.md).

## Build once, execute offline

From the repository or extracted-package root, first build the [teaching image](../README.md). Then:

```sh
docker build --platform linux/amd64 -f labs/19-hardware-generators/Dockerfile -t from-concept-generators:2026.10 .
```

The image fixes SBT 1.10.2, Scala 2.13.12, Chisel and its compiler plugin 6.5.0, and `firtool` 1.62.0. Launcher/backend downloads have checked SHA-256 digests. OpenJDK 17 and the inherited teaching tools come from distribution packages; the execution report records actual versions and the image ID. The [official compatibility table](https://www.chisel-lang.org/chisel3/docs/appendix/versioning.html) documents the Chisel/backend pairing. This deliberately pinned example does not claim these are the latest releases.

The build downloads dependencies and compiles the generator into `/opt/generator`. The runtime verifies its compiled input hashes against the supplied sources; changing the Scala source or build definition requires rebuilding the image. Runtime elaboration invokes the compiled Scala program directly with Java and the recorded classpath, so it needs no writable SBT cache or SBT server. Subsequent execution requires no network and supports an unprivileged UID with a writable output directory.

Linux/WSL:

```bash
docker run --rm --platform linux/amd64 --network none --user "$(id -u):$(id -g)" --env HOME=/tmp \
  --env CASE_IMAGE_ID="$(docker image inspect --format '{{.Id}}' from-concept-generators:2026.10)" \
  --mount "type=bind,source=$PWD,target=/work" from-concept-generators:2026.10 \
  python labs/19-hardware-generators/run.py --output-dir labs/build/hardware-generators-run
```

PowerShell with Docker Desktop Linux containers:

```powershell
$generatorImage = docker image inspect --format '{{.Id}}' from-concept-generators:2026.10
docker run --rm --platform linux/amd64 --network none --env HOME=/tmp `
  --env "CASE_IMAGE_ID=$generatorImage" `
  --mount "type=bind,source=${PWD},target=/work" from-concept-generators:2026.10 `
  python labs/19-hardware-generators/run.py --output-dir labs/build/hardware-generators-run
```

Choose a fresh output directory for every execution. Building or emitting `.sv` alone does not produce a passing report. The runner requires all three positive simulations, the intended negative control and six successful synthesis runs.

## Intermediate files and provenance

Each configuration retains `Accumulator.fir` from Chisel elaboration, `lowered.mlir` from `firtool --ir-hw`, emitted `Accumulator.sv`, input/expected vectors and both generic synthesis netlists. The report records generator/build/test source hashes, configuration, seed, image ID, actual tool versions, exact commands, runtime JAR hashes and artifact hashes. The build log/classpath also preserve SBT's version and dependencies; simulation logs preserve the observed failure. SystemVerilog source comments retain available Scala locations; optimization can merge, duplicate or remove objects, so names/line numbers are navigation aids rather than a one-to-one proof of correspondence.

The emitter uses `--disable-all-randomization` and `--lowering-options=disallowLocalVariables`. The latter avoids automatic block-local variables unsupported by the tested Icarus frontend. This syntax compatibility choice is recorded with the command; source-language support alone does not determine downstream frontend support.

The compact [reference report](reference/report.json) and [priority counterexample](reference/fault-w16-simulation.txt) are actual tool evidence. Audit them without Java or CIRCT using `python labs/19-hardware-generators/verify_reference.py`. To publish a new author reference after execution, run `python labs/19-hardware-generators/collect.py labs/build/hardware-generators-run/report.json`, then the verifier. Simulation bytecode is omitted from the compact reference; the original report retains its hash.

The preserved run passed 552 cycles per positive width. `stimulus_coverage` describes the supplied vector file; the faulty run stops after two sampled edges (failure at zero-based cycle index 1), rather than completing the remaining vectors.

| Width | Positive sampled cycles | Direct SV generic cells | Chisel-generated generic cells |
| ---: | ---: | ---: | ---: |
| 8 | 552 | 61 | 63 |
| 16 | 552 | 130 | 132 |
| 32 | 552 | 271 | 273 |

These are Yosys 0.33 `synth -noabc` counts under the preserved commands. The two-cell difference is a generic structural observation; physical mapping and any performance conclusions require a separate experiment.

## Questions and extensions

1. Locate the carry-width operation in Scala, FIRRTL, lowered IR and emitted RTL. Which signals survive synthesis?
2. Explain why the width-32 case still needs a 33-bit intermediate sum. Change `+&` to `+` in a private variant and investigate the compile/test outcome.
3. Trace the first negative-control edge. Which requirement distinguishes the generated variant from the direct RTL?
4. Compare generic cell types at each width. Explain why identical counts would not establish equivalence, and different counts would not establish a functional mismatch.
5. Construct an explicitly scoped formal miter, or implement both preserved RTL variants on the same target with identical constraints. Record that new evidence separately from this simulation/synthesis result.
