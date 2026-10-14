# 01 — RTL and instruction building blocks

Prerequisites: ISA formats, two's-complement arithmetic, clocked state and SystemVerilog assignment semantics. Tools: Python and Icarus Verilog.

Run `python labs/run.py run foundations` from the repository root. Expected result: `PASS foundations` and a successful report. The vector generator creates independent finite-width ALU expectations and inverse immediate encodings. Tests cover all 12-bit I/S immediates, all B offsets, J/U boundaries, rejected selectors, supported/unsupported decoder cases and 3000 register-file cycles.

The iterative product is tested at widths 1, 8 and 32, including all 65536 operand pairs at width 8, documented latency, output stalls and reset abort. Basic tests cover mux selection, enabled pipeline capture, FSM ownership, an elastic slice and reset release. Digital simulation of a synchronizer does not measure metastability or prove a physical CDC.

Exercise: change the multiplier's implementation while retaining its interface. Compare functional results, operation latency, initiation interval and synthesis resources. Add a failing test before fixing a deliberately incorrect signed comparison. Submit the report and an annotated edge-by-edge trace.
