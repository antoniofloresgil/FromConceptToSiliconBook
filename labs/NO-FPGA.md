# Completing the laboratories without an FPGA board

The online course can be completed without buying or borrowing an FPGA. Keep the physical-board activities as an additional route for students with access. Both routes require student changes, independent checks, implementation analysis and the same explanation of learning outcomes. Owning a board is not a rubric criterion.

Run commands from the repository or extracted-package root, using the containers and shell-specific commands in [the lab catalog](README.md). A simulator executes RTL or an architectural model; it does not load or execute a `.bit` file. Bitstream generation and device-specific place-and-route can be done without a connected board, but still need their separate tools and databases.

## Activity map

The generator and multicore practices are optional advanced routes. They add no compulsory work to the course and require no physical board.

| Lab | Route without a physical board | Required evidence / boundary |
| --- | --- | --- |
| 01 Foundations | Run `foundations`; implement the arithmetic variant in simulation | Independent expected values, latency/stall/reset trace; generic synthesis for the resource comparison |
| 02 Memory | Run `memory`; compare cache traces and RAM contracts | Hits/misses/writebacks and collision checks; device memory inference, when attempted, needs synthesis tools but no board |
| 03 Transport | Run `transport`; test the pipelined student variant | Accepted/completed transaction counts, backpressure and reset regression |
| 04 MMIO | Run `mmio`; extend a simulated bus/device harness | Register effects, masks and interrupt behavior; compilation of C drivers alone does not execute them |
| 05 Verification | Run `verilator` and `cocotb` | Scoreboards, VCD/XML and a diagnosed failure |
| 06 ISA | Run `isa`; use separately installed matching Spike/Sail for the extension | ELF/disassembly/signature; the supplied oracle covers only its demonstration program |
| 07 Implementation | Run `synthesis`, then the [implementation alternative](07-implementation/README.md#without-a-physical-board) | Student netlist/resource interpretation, constraint review, implementation-report analysis and simulated system result |
| 08 Integration | Use the selected full-Wally simulation harness for cache/MMIO/timer observations; use `dotproduct-wally` for the executable accelerator milestone | Accepted transactions, architectural/device effects and interrupt return; the two harnesses have different configurations |
| 09 Privilege/MMU | Run the guided Spike test and port to the full-Wally simulation harness | Exact signature, denied-store/fault trace and privilege/PTE calculations; the reduced accelerator fixture does not supply an MMU |
| 10 Dot product | Run `dotproduct` and explicit `dotproduct-wally` with the external pinned clone | Numerical/protocol/error tests, bounded checks, firmware polling/IRQ and cycle comparisons |
| 11 DSE | Run `11-dse/run_wally.py`; analyse the separately labelled illustrative CSV | Controlled real-RTL cycle comparison; physical report review if supplied, with no invented frequency or energy |
| 12 Boot | Run the separate QEMU/OpenSBI container; optionally build Linux/initramfs | Handoff/console/DTB and source identities; QEMU `virt` is a different platform from Wally |
| 13 Vector | Run the supplied QEMU RVV experiment at all three VLEN values | Same-ELF functional checks and memory guards; no hardware timing claim |
| 14 Security | Run the QEMU PMP and digital RTL/formal/model experiments | Allowed/denied cases, no unauthorized DMA effects, debug witness and stated timing-model limits |
| 15 Formal | Run `python labs/15-formal/run.py` in the standard teaching image | FIFO BMC, induction/equivalence, traffic/vacuity witnesses, actual counterexample and repair/regression; no extra solver or hardware |
| 16 Physical study | Run the separate OpenROAD image or analyse its supplied reports/captures | Measured period/utilization sweep, pre/post-route setup and hold diagnosis, infeasible floorplans and a proposed RTL/physical repair; no chip fabrication |
| 17 Complete case | Run the common-manifest stages or inspect the joined report bundle and book visuals | Same IP RTL in tests/formal/Wally and both physical block targets; cycle/resource/area/timing/power-model analysis and acceptance decision; no board/fabrication |
| 18 Linux accelerator | Execute the QEMU/Linux driver/application experiment; Wally RV64 RTL Linux is advanced | Device Tree, reserved DMA ownership, IRQ/polling, errors and timeout quarantine; emulator timing and RTL boot checkpoints distinguished |
| 19 Hardware generators | Execute the separate Chisel/CIRCT image and compare generated/direct RTL | Independent vectors, generated IR/RTL, intended priority failure and generic synthesis; no physical PPA claim |
| 20 Multicore | Run two Linux CPUs in QEMU and the finite ownership/visibility/dependency models | 96 modeled DMA jobs plus abstract witnesses; coherent two-hart Wally RTL and physical performance remain separate advanced work |

The command names in backticks such as `memory` mean `python labs/run.py run memory`. Labs 09 and 11–14 have explicit scripts or external environments documented in their individual guides; requesting a guided entry from the runner only displays guidance. `run all` executes the nine automatic entries. An absent external dependency must be resolved or reported, rather than replaced by a claimed PASS.

## Replacing a physical observation

| Physical activity retained in the book | Alternative to submit without a board |
| --- | --- |
| Load `.bit` through JTAG and observe DONE | Generate/archive the bitstream if the FPGA environment is available; review part, firmware and constraint identities. Supply the programming procedure and expected checkpoints; mark programming/DONE as unexecuted |
| Observe GPIO/LED/heartbeat | Drive reset and input changes in an RTL bench; compare logical output transitions with a scoreboard and annotated waveform. Review port-to-XDC mapping separately |
| Observe a UART banner | In a matching SoC harness, decode simulated TX and compare bytes with the expected string. For the supplied accelerator fixture use its checked firmware mailbox/result instead, identifying that different observation interface |
| Power-cycle SRAM versus flash configuration | Explain configuration persistence and the expected power-cycle sequence, referencing the selected board procedure. Simulate application reset/restart separately; reset simulation does not test configuration memory persistence |
| Observe DDR initialization or memory traffic | Test a bridge against a documented memory/handshake model, inject stalls/errors/reset and review the reset dependency. Calibration, PHY margins and physical DDR operation remain untested |
| Measure workload cycles/throughput | Run the same workload on real Wally RTL and compare software/accelerator cycle counts. Report the memory/wait-state model; wall-clock simulator runtime is not target latency |
| Compare device resources and timing | Run synthesis/place-and-route without connecting a board, or analyse an instructor-provided report bundle with source/target/tool/constraint provenance. Separate computed timing from measured operation |

The wrapper, UART decoder, DDR bridge bench and modified full-SoC scenarios above are student exercises, not additional checked scripts supplied by this package. The checked starting point for CPU-controlled acceleration is [Lab 10](10-dotproduct/README.md). Its fixture instantiates real Wally RTL with simulated RAM and a direct interrupt input; it does not reproduce the Nexys Video wrapper, LiteDRAM or PLIC.

## Implementation resources and assessment

[Lab 21](21-physical-closure/README.md) supplies an executed repair comparison for the same dot-product block: lower-clock FPGA routes, a separately tested registered-product engine, and an ASIC electrical/hold repair with extracted timing and netlist equivalence. Its preserved reports and actual physical captures support the full diagnosis exercise without a board. Accept only the stated block/tool-model scope; manufacturing and board qualification remain separate.

If XC7 tools/databases or local compute are unavailable, the instructor supplies a review bundle before P5: source revision and parameters, FPGA part, tool/database versions, XDC/clock definitions, synthesis utilization, route/timing logs including warnings and constraint coverage, and hashes of generated artifacts. Include one baseline and one changed timing target or configuration for comparison. Supply a failing report or constraint case for diagnosis. If no bitstream was produced, record that explicitly. A screenshot of utilization alone is insufficient.

Students still synthesize their own RTL with the teaching container, explain its structure/resources, review clock/reset/IO requirements and demonstrate their changes in simulation. They then analyse the provided physical reports, identify the critical path and timing margin, explain any failure and propose a checked next experiment. Reports for an instructor design illustrate that design's implementation; they do not establish timing closure for a student's modified IP. ASIC tools/PDKs are separate resources and are not required merely because an FPGA is unavailable.

For each replaced observation submit the requirement, selected configuration, executable check or analytical procedure, expected/actual outcome, artifact path/hash and residual physical checks. Label evidence as student-generated, instructor-provided or proposed. Submit the same P1–P5/final-project evidence and receive the same rubric opportunities in either route; physical programming is an extension milestone. A student using the board route also retains the simulation regression.

Use the [verification dossier](verification/README.md) to preserve the distinction. Leave board qualification as `not_run` with the reason “no physical board available”; a justified exclusion from the assessed route is not a hardware PASS. Keep timing/physical checks unexecuted unless their actual tools/results exist. The instructor evaluates the replacement analysis and functional demonstration against the agreed scope while the dossier continues to expose physical qualification gaps.
