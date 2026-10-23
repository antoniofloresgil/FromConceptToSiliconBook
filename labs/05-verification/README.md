# 05 — Two verification environments

Run `python labs/run.py run verilator` and `python labs/run.py run cocotb`. Both reuse `examples/verilator/accumulator.sv`. The first builds the existing C++ scoreboard and VCD trace; the second uses `examples/cocotb/Makefile` and cocotb 2.0.1 with Icarus. Their original fixed stimulus seed is 2026.

Expected result: all scoreboards pass; the cocotb XML contains a successful testcase. An empty, failed or skipped suite fails the package runner. Build products and the VCD/XML stay under `labs/build/`.

The supplied container's distribution Verilator is used for the standalone C++ example. cocotb uses Icarus: its Verilator backend requires version 5.036 or newer and is not selected automatically.

`python labs/run.py run verilator` also runs `mutation_check.py`: it builds five deliberately faulty copies of the accumulator against the book's 14-vector harness and against the same harness with three added vectors, and fails if any outcome differs from the table in the Verilator chapter. Two of the faults pass the 14 vectors and fail the 17, and one never builds because `-Wall` reports an unused `Clear`.

`python labs/run.py run cocotb` likewise runs `cocotb_mutation_check.py`, which applies the same five faults to the cocotb test as supplied and with three added directed vectors. Random stimulus catches the fault that ignores `Enable`; only a directed zero-operand vector catches the one that needs a nonzero operand. Icarus has no unused-signal lint, so the ignored `Clear` is caught by the scoreboard instead.

Exercise: make overflow incorrectly sticky in a student branch and confirm both environments detect the failure. Minimize the failing sequence, repair the implementation and retain the regression. Explain stimulus-driving and output-sampling phases.
