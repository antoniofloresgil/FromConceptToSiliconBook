# Reproducible Hardware Design Labs

Run commands from the repository root. The book's [reproduction appendix](../appendices/reproducible-labs.qmd) explains containers, native tools and external repositories.

```sh
docker build -f labs/Dockerfile -t from-concept-labs:2026.10 .
docker run --rm --network none --mount "type=bind,source=$PWD,target=/work" from-concept-labs:2026.10
```

In PowerShell, use `${PWD}` as the mount source. The default container command runs all eight automatic labs. Building needs network access; their execution needs none. The container does not program a board or download a PDK.

| ID | Material | Verification boundary | Guide |
|---|---|---|---|
| `foundations` | Eleven complete RTL modules | Integer vectors, decode, registers, basic control/reset and iterative product | [01](01-foundations/README.md) |
| `memory` | Synchronous RAM and Python cache | Read-first, masks, stalls, dirty eviction/clean/refill | [02](02-memory/README.md) |
| `transport` | FIFO and queued memory | Ordering, conservation, response pressure and persistent writes | [03](03-transport/README.md) |
| `mmio` | AXI-Lite endpoint, GPIO/APB, FIFO, PWM, C drivers | Channel independence, events, masks and driver compilation | [04](04-mmio/README.md) |
| `verilator`, `cocotb` | Existing accumulator examples | C++/Python unit scoreboards | [05](05-verification/README.md) |
| `isa` | Assembly and linker script | ELF/signature check in a program-specific oracle | [06](06-isa/README.md) |
| `synthesis` | Implementation accumulator and all teaching RTL | Behavioral test, elaboration, no latches and generic synthesis | [07](07-implementation/README.md) |
| `fpga`, `asic` | Board/PDK-dependent flows | Guided integration, separate tools and acceptance criteria | [07](07-implementation/README.md) |
| `wally`, `accelerator` | Full-SoC observations and design exercise | Guided full-system work; exercise implementation by the student | [08](08-integration/README.md) |

## Commands

```sh
python labs/run.py list
python labs/run.py doctor
python labs/run.py check
python labs/run.py run all --seed 2026
python labs/run.py run transport --seed 2027
python labs/run.py pack
```

`run all` includes only automatic labs. Missing tools, assertions, compiler errors and timeouts fail the run with a nonzero exit code. Guided labs are listed explicitly; requesting them through `run` reports their guide instead of pretending that a board/PDK test passed.

`labs/build/report.json` records actual per-lab seeds, tool versions, source hashes, commands, logs, result and artifact hashes. The existing C++/cocotb examples retain their fixed seed 2026; `--seed` controls the new randomized tests. Compile and simulation logs are in `labs/build/<id>/`. Report paths refer to the environment in which the run occurred.

`labs/validated-environment.json` records the tested baseline. Run `python labs/tools/verify_harness.py` to confirm that a deliberately broken FIFO fails the tests; its expected failure evidence stays under `labs/build/fault-injection/`, preserving the reference report.

## Sources and student work

Reference RTL/models are complete listings exported from the chapters. `labs/tools/catalog.py` records each origin. `check` detects drift; `sync` is an authoring operation that regenerates exported files after reviewing a chapter change. It overwrites those reference files, so keep student variants in `labs/work/` or a separate Git branch.

The archive produced by `pack` includes labs, existing examples, chapter text for provenance and SHA-256 checksums. Build products are excluded. Extract the archive and use the same commands from its root. Changes to source produce a different checksum.

For a student variant, copy one lab's complete `rtl/` directory to `labs/work/<name>/rtl/`, edit it and run, for example, `python labs/run.py run transport --rtl-dir labs/work/transport/rtl`. The runner retains the reference tests and records the variant's hashes. The existing reference sources remain synchronized with the chapters.

## Deliverables

For each practice, submit a configuration/seed, relevant disassembly or waveforms, the result report, a minimized failing case if applicable, and an explanation of the checked requirement. For implementation work also submit timing/resource evidence and constraints. A successful syntax check, simulation, synthesis, physical route and board run are different milestones.
