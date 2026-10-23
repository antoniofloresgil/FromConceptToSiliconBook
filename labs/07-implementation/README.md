# 07 — Synthesis, then physical implementation

Run `python labs/run.py run synthesis`. Tools: Icarus and Yosys. It tests the **implementation** accumulator's uppercase `Clk`/`Reset` interface, elaborates every complete teaching RTL unit with its dependencies, rejects unintended latches and produces a generic accumulator netlist/resource report. This is not FPGA placement or ASIC sign-off.

`python labs/run.py run synthesis` also runs `synthesis_surprises.py`, which synthesizes the small modules in `surprises/` and checks the results the Yosys chapter reports: a debug counter that disappears when no output observes it, a 1,024-byte memory that maps to 32 `RAM256X1S` primitives with an asynchronous read and to one `RAMB18E1` with a registered read, and a latch that `always_comb` rejects, `always @*` quietly builds and the `$dlatch` gate catches. The counts belong to the Yosys 0.33 of the laboratory container.

`rtl/accumulator.sv`, `constraints.sdc` and `config.yaml` correspond to the OpenROAD/LibreLane chapters. The simulation chapter's accumulator has different clock/reset spelling. The physical-flow configuration deliberately points to this implementation RTL so that `CLOCK_PORT: Clk` is correct.

## Guided ASIC work

Read the book's Digital VLSI Design Fundamentals chapter before interpreting timing/power results. The Physical Validation, DFT and Preparation for Fabrication chapter provides guided scan, memory-test and release-review exercises. These additional exercises require the stated simulators, technology libraries and physical tools; they are not automatic activities in `run all`.

The [measured OpenROAD study](../16-openroad-study/README.md) supplies an executable direct Nangate45 accumulator flow, eleven period/utilization cases, seven actual GUI captures and preserved timing/electrical/placement failures. Its identified report bundle can support P5 analysis when local physical tools are unavailable. This reference technology and accumulator do not establish timing for a student's accelerator or replace a fabrication PDK.

Install OpenROAD/ORFS or LibreLane and the chosen PDK using the book's chapters. With a configured LibreLane environment, run from this directory:

```sh
python -m librelane --pdk-root "$PDK_ROOT" config.yaml
```

Use the installed version's documented command options. Record the tool/PDK/SCL revisions, resolved configuration and logs. For direct OpenROAD, follow the chapter's synthesis, floorplan, PDN, placement, CTS, routing and extraction sequence with the same RTL/constraints. Platform-specific Tcl cannot be completed by guessing library paths or layer names.

Acceptance: positive required setup/hold slack, constraint coverage, applicable DRC/LVS evidence and identified final artifacts. A generated GDS is a milestone, not evidence that every sign-off requirement passed. `python labs/run.py run asic` therefore points to this guide instead of reporting a simulated ASIC success.

## Guided FPGA work

Use the pinned Wally fork and board wrapper from the reproduction appendix and FPGA chapters. Preserve the configuration, firmware image, XDC, chip database and tool revisions. Compile, route and generate the Nexys Video bitstream before physical programming with openFPGALoader. Access to the board/JTAG is a separate host setup; the simulation container does not obtain USB access automatically.

Acceptance: build logs, timing/resource reports, successful programming and an observable internal-memory firmware milestone. DDR3 initialization remains a separate integration investigation at the documented snapshot. Choose on-chip-memory tasks for the first reproducible coursework baseline.

### Without a physical board

This route has the same coursework rubric opportunities. Run `python labs/run.py run synthesis` for the implementation accumulator, and `python labs/run.py run dotproduct` for the accelerator's generic synthesis, functional checks and bounded formal results. Use `--rtl-dir` with a complete student RTL copy as described in the catalog when assessing a variant; an unchanged reference run establishes the environment only.

1. Inspect the generated netlist and synthesis logs. Explain storage, multiplier/adder mapping, latch checks and resource changes for your variant. Generic cells do not imply LUT/BRAM/DSP counts or achieved frequency.
2. Review the selected top's port names, clock/reset and interface budgets. Use XDC for the FPGA wrapper and the matching SDC for the implementation IP; these are different designs and constraints. Inventory missing generated-clock or IO assumptions.
3. With the separate XC7 environment, build, route and generate the same Nexys Video `.bit` without connecting a board. Archive reports, constraints, firmware and tool/database identities plus artifact hashes. Skip the programmer commands. If those tools or compute are unavailable, analyse the instructor's baseline/variant report bundle specified in [the common alternative guide](../NO-FPGA.md#implementation-resources-and-assessment), including a timing or constraint failure and a proposed repair. Identify whose design each report represents.
4. Execute `dotproduct-wally` using [Lab 10's pinned-clone recipe](../10-dotproduct/README.md#real-wally-platform). Explain firmware polling, interrupt completion, result comparison and cycle measurements. This exercises real processor/IP RTL in its documented fixture; it does not validate the Nexys Video fabric or the generated bitstream.
5. Submit a bring-up plan with expected DONE, clock/reset, UART/LED and memory checkpoints. For a wrapper/heartbeat exercise, implement a self-checking RTL bench for reset and output transitions and audit its XDC pin mapping. Preserve the waveform and expected transition count; physical pin voltages, flash persistence and DDR calibration remain untested.

Acceptance without a board: student simulation/synthesis evidence, a constraint inventory, generated or supplied implementation-report analysis, a real-Wally firmware result and the remaining board-check plan. Record programming and board observations as `not_run` due to unavailable hardware. Use on-chip or simulated memory for functional milestones; the snapshot's unresolved DDR3 initialization is not a prerequisite for completing this route. An ASIC implementation is an independent guided activity, not a compulsory substitute for owning an FPGA.
