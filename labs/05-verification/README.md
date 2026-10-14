# 05 — Two verification environments

Run `python labs/run.py run verilator` and `python labs/run.py run cocotb`. Both reuse `examples/verilator/accumulator.sv`. The first builds the existing C++ scoreboard and VCD trace; the second uses `examples/cocotb/Makefile` and cocotb 2.0.1 with Icarus. Their original fixed stimulus seed is 2026.

Expected result: all scoreboards pass; the cocotb XML contains a successful testcase. An empty, failed or skipped suite fails the package runner. Build products and the VCD/XML stay under `labs/build/`.

The supplied container's distribution Verilator is used for the standalone C++ example. cocotb uses Icarus: its Verilator backend requires version 5.036 or newer and is not selected automatically.

Exercise: make overflow incorrectly sticky in a student branch and confirm both environments detect the failure. Minimize the failing sequence, repair the implementation and retain the regression. Explain stimulus-driving and output-sampling phases.
