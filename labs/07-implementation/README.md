# 07 — Synthesis, then physical implementation

Run `python labs/run.py run synthesis`. Tools: Icarus and Yosys. It tests the **implementation** accumulator's uppercase `Clk`/`Reset` interface, elaborates every complete teaching RTL unit with its dependencies, rejects unintended latches and produces a generic accumulator netlist/resource report. This is not FPGA placement or ASIC sign-off.

`rtl/accumulator.sv`, `constraints.sdc` and `config.yaml` correspond to the OpenROAD/LibreLane chapters. The simulation chapter's accumulator has different clock/reset spelling. The physical-flow configuration deliberately points to this implementation RTL so that `CLOCK_PORT: Clk` is correct.

## Guided ASIC work

Install OpenROAD/ORFS or LibreLane and the chosen PDK using the book's chapters. With a configured LibreLane environment, run from this directory:

```sh
python -m librelane --pdk-root "$PDK_ROOT" config.yaml
```

Use the installed version's documented command options. Record the tool/PDK/SCL revisions, resolved configuration and logs. For direct OpenROAD, follow the chapter's synthesis, floorplan, PDN, placement, CTS, routing and extraction sequence with the same RTL/constraints. Platform-specific Tcl cannot be completed by guessing library paths or layer names.

Acceptance: positive required setup/hold slack, constraint coverage, applicable DRC/LVS evidence and identified final artifacts. A generated GDS is a milestone, not evidence that every sign-off requirement passed. `python labs/run.py run asic` therefore points to this guide instead of reporting a simulated ASIC success.

## Guided FPGA work

Use the pinned Wally fork and board wrapper from the reproduction appendix and FPGA chapters. Preserve the configuration, firmware image, XDC, chip database and tool revisions. Compile, route and generate the Nexys Video bitstream before physical programming with openFPGALoader. Access to the board/JTAG is a separate host setup; the simulation container does not obtain USB access automatically.

Acceptance: build logs, timing/resource reports, successful programming and an observable internal-memory firmware milestone. DDR3 initialization remains a separate integration investigation at the documented snapshot. Choose on-chip-memory tasks for the first reproducible coursework baseline.
