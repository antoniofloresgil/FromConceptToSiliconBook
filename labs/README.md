# Reproducible Hardware Design Labs

Run commands from the repository root. The book's [reproduction appendix](../appendices/reproducible-labs.qmd) explains containers, native tools and external repositories.

The [HSD coursework guide](../appendices/hsd-coursework.qmd) defines the 12-week, 6 ECTS course's P0–P5 activities, autonomous workload, deliverables and rubrics. Students reuse these references while developing a Wally-controlled AXI/DMA dot-product accelerator. The executable reference in `10-dotproduct/` supplies the AXI/DMA IP, bounded formal checks and a real Wally firmware platform. The guide distinguishes that reference from assessed student work.

```sh
docker build -f labs/Dockerfile -t from-concept-labs:2026.10 .
docker run --rm --network none --mount "type=bind,source=$PWD,target=/work" from-concept-labs:2026.10
```

In PowerShell, use `${PWD}` as the mount source. The default container command runs all nine automatic labs. Building needs network access; their execution needs none. The container does not program a board or download a PDK.

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
| `dotproduct` | Complete signed AXI/DMA IP | Every legal length, protocol/error/security tests, reuse, synthesis and bounded formal checks | [10](10-dotproduct/README.md) |
| `dotproduct-wally` | Real pinned Wally core and RV32 firmware | External clone required; polling, DMA, interrupt and cycle measurements | [10](10-dotproduct/README.md) |
| `mmu` | Complete RV32/Sv32 assembly test | Separate Spike run and guided Wally translation/fault trace | [09](09-privileged-mmu/README.md) |

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

Reference RTL/models in the original unit labs are complete listings exported from the chapters. The dot-product project supplies native complete source files and a separate manifest. `labs/tools/catalog.py` records each origin. `check` detects drift; `sync` is an authoring operation that regenerates exported files after reviewing a chapter change. It overwrites those reference files, so keep student variants in `labs/work/` or a separate Git branch.

The archive produced by `pack` includes labs, existing examples, chapter text for provenance and SHA-256 checksums. Build products are excluded. Extract the archive and use the same commands from its root. Changes to source produce a different checksum.

For a student variant, copy one lab's complete `rtl/` directory to `labs/work/<name>/rtl/`, edit it and run, for example, `python labs/run.py run transport --rtl-dir labs/work/transport/rtl`. The runner retains the reference tests and records the variant's hashes. The existing reference sources remain synchronized with the chapters.

## Deliverables

For each practice, submit a configuration/seed, relevant disassembly or waveforms, the result report, a minimized failing case if applicable, and an explanation of the checked requirement. For implementation work also submit timing/resource evidence and constraints. A successful syntax check, simulation, synthesis, physical route and board run are different milestones.

## Verification planning and evidence

The [verification methodology](../chapters/03-simulation-verification/verification-methodology.qmd) connects requirements to checkers at every design level. [labs/verification](verification/README.md) supplies the project plan, a template, and a collector that validates source/artifact freshness and checker completion while retaining unexecuted obligations. Run its focused gate tests with `python labs/verification/test_evidence.py`; CI also runs them and collects the scoped project dossier.

## Architectural exploration

[Lab 11](11-dse/README.md) executes a controlled divider sweep on real pinned Wally RTL and provides a separate labelled illustrative performance/Pareto exercise. It is the guided `dse` entry; its script is explicit and is not added to the nine automatic entries. The complete method, measured reference results and gem5/XS-GEM5 research extensions are in the [architecture-exploration chapter](../chapters/07-advanced-topics/architecture-exploration.qmd).
