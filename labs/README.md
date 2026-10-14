# Reproducible Hardware Design Labs

Run commands from the repository root. The book's [reproduction appendix](../appendices/reproducible-labs.qmd) explains containers, native tools and external repositories.

Original code uses MIT; educational prose and original figures use CC BY-SA 4.0. See the [licensing scope](../LICENSE.md) and [third-party notices](../NOTICE.md), both included with the practice download. The [final project review](../summary.qmd) provides release-evidence and defence guidance.

The [HSD coursework guide](../appendices/hsd-coursework.qmd) defines the 12-week, 6 ECTS course's P0–P5 activities, autonomous workload, deliverables and rubrics. Students reuse these references while developing a Wally-controlled AXI/DMA dot-product accelerator. The executable reference in `10-dotproduct/` supplies the AXI/DMA IP, bounded formal checks and a real Wally firmware platform. The guide distinguishes that reference from assessed student work.

```sh
docker build -f labs/Dockerfile -t from-concept-labs:2026.10 .
docker run --rm --network none --user "$(id -u):$(id -g)" --env HOME=/tmp --mount "type=bind,source=$PWD,target=/work" from-concept-labs:2026.10
```

This **checked recipe** starts in the repository/extracted-package root on Linux or WSL. UID/GID options keep newly generated bind-mount files owned by the invoking host user; `HOME=/tmp` supplies a writable container home. CI uses the same ownership policy.

For native Windows PowerShell with Docker Desktop and a Windows checkout:

```powershell
docker build -f labs/Dockerfile -t from-concept-labs:2026.10 .
docker run --rm --network none --env HOME=/tmp `
  --mount "type=bind,source=${PWD},target=/work" from-concept-labs:2026.10
```

Windows mounts use Windows access controls; do not paste POSIX `id` expressions into PowerShell. For a WSL/Linux checkout, use the Linux recipe in that shell. The default command runs all nine automatic labs. Building needs network; reference execution is offline. Existing root-owned Linux output needs a scoped repair first, as explained in the [appendix](../appendices/reproducible-labs.qmd).

## Recipe status and shared contracts

**Checked recipe** means the stated command/runtime and boundary were exercised in the recorded environment. **Adaptation template** needs external paths, versions, technology or hardware inputs. **Exercise** needs student implementation or new evidence. A checked parser/netlist step does not qualify a whole physical flow.

[Recipe contracts](recipe-contracts.json) identify image, ports, runner minimum and output namespaces. Use `python labs/tools/check_recipes.py` for static Docker/path/version/interface coherence, then `python labs/run.py check` for listing consistency. Neither executes hardware simulation or checks live upstream compatibility. `labs/recipe-audit-results.json` records the controlled Linux-volume ownership reproduction, matched UID/GID run and subsequent write check.

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
| `wally`, `accelerator` | Full-SoC observations and design exercise | Adaptation template / student exercise | [08](08-integration/README.md) |
| `dotproduct` | Complete signed AXI/DMA IP | Every legal length, protocol/error/security tests, reuse, synthesis and bounded formal checks | [10](10-dotproduct/README.md) |
| `dotproduct-wally` | Real pinned Wally core and RV32 firmware | External clone required; polling, DMA, interrupt and cycle measurements | [10](10-dotproduct/README.md) |
| `mmu` | Complete RV32/Sv32 assembly test | Separate Spike run and guided Wally translation/fault trace | [09](09-privileged-mmu/README.md) |
| `dse` | Real Wally divider sweep; illustrative analysis | Checked explicit script with external clone; outside `run all` | [11](11-dse/README.md) |

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

Preserve the unit report: the Wally recipe sets `LAB_BUILD_DIR=/work/labs/build/wally-platform`, producing `labs/build/wally-platform/report.json`. The collector consumes both reports. DSE writes separate results; CI additionally places its builds under `dse-platform/`.

`labs/validated-environment.json` records the tested baseline. Run `python labs/tools/verify_harness.py` to confirm that a deliberately broken FIFO fails the tests; its expected failure evidence stays under `labs/build/fault-injection/`, preserving the reference report.

## Sources and student work

Reference RTL/models in the original unit labs are complete listings exported from the chapters. The dot-product project supplies native complete source files and a separate manifest. `labs/tools/catalog.py` records each origin. `check` detects drift; `sync` is an authoring operation that regenerates exported files after reviewing a chapter change. It overwrites those reference files, so keep student variants in `labs/work/` or a separate Git branch.

The archive produced by `pack` includes labs, standalone examples, a package quick-start README, licenses and checksum/provenance manifests. Chapter text, appendices, textbook figures, bibliography and publishing tools are excluded. Links to omitted book documents point to the published HTML book in the extracted guides. Obtain the complete book PDF separately from the HTML sidebar.

In the full repository, `check` verifies reference code against chapter listings. In an extracted ZIP, it verifies `SHA256SUMS.json` and the 29 listing origins in `LAB-PROVENANCE.json`, which record chapter/file hashes, selectors, repository revision and preview status. Chapter/code equality is checked before the archive is produced, not reconstructed from a checksum. `sync` and `pack` require the full repository. Changing packaged reference files fails integrity checks; student variants remain under `labs/work/`.

For a student variant, copy one lab's complete `rtl/` directory to `labs/work/<name>/rtl/`, edit it and run, for example, `python labs/run.py run transport --rtl-dir labs/work/transport/rtl`. The runner retains the reference tests and records the variant's hashes. The existing reference sources remain synchronized with the chapters.

## Deliverables

For each practice, submit a configuration/seed, relevant disassembly or waveforms, the result report, a minimized failing case if applicable, and an explanation of the checked requirement. For implementation work also submit timing/resource evidence and constraints. A successful syntax check, simulation, synthesis, physical route and board run are different milestones.

## Verification planning and evidence

The [verification methodology](../chapters/03-simulation-verification/verification-methodology.qmd) connects requirements to checkers at every design level. [labs/verification](verification/README.md) supplies the project plan, a template, and a collector that validates source/artifact freshness and checker completion while retaining unexecuted obligations. Run its focused gate tests with `python labs/verification/test_evidence.py`; CI also runs them and collects the scoped project dossier.

## Architectural exploration

[Lab 11](11-dse/README.md) executes a controlled divider sweep on real pinned Wally RTL and provides a separate labelled illustrative performance/Pareto exercise. It is the guided `dse` entry; its script is explicit and is not added to the nine automatic entries. The complete method, measured reference results and gem5/XS-GEM5 research extensions are in the [architecture-exploration chapter](../chapters/07-advanced-topics/architecture-exploration.qmd).
