# Architectural exploration: real RTL and controlled analysis

**Recipe status:** the supplied reference runs are checked in the recorded teaching environment. External clone paths must be set for your machine; Linux/WSL writable mounts use the host UID/GID, while native PowerShell uses Windows access controls. Student/physical extensions require separate implementation and evidence.

Read [the DSE chapter](../../chapters/07-advanced-topics/architecture-exploration.qmd).
Two activities deliberately produce different types of evidence.

## Actual Wally divider sweep

Run in the existing teaching container with a separately acquired Wally clone:

```sh
docker run --rm --network none --user "$(id -u):$(id -g)" --env HOME=/tmp --env WALLY_ROOT=/cvw \
  --mount "type=bind,source=$PWD,target=/work" \
  --mount "type=bind,source=$(cd ../cvw && pwd),target=/cvw,readonly" \
  from-concept-labs:2026.10 python labs/11-dse/run_wally.py --seed 2026
```

PowerShell (replace the clone location when needed):

```powershell
docker run --rm --network none --env HOME=/tmp --env WALLY_ROOT=/cvw `
  --mount "type=bind,source=${PWD},target=/work" `
  --mount "type=bind,source=D:\Repos\cvw,target=/cvw,readonly" `
  from-concept-labs:2026.10 python labs/11-dse/run_wally.py --seed 2026
```

Native Linux with the same tools: `WALLY_ROOT=../cvw python labs/11-dse/run_wally.py`.
Requires Verilator, Clang/LLD, C++/Make and Git. There is no FPGA/PDK dependency.
Missing tools, incorrect results and timeouts fail; there is no fake-core fallback.
Use `--bits 2` for a single smoke configuration or `--bits 1 2 4` for the full sweep.

The script reuses the pinned-source exporter and ELF loader from the executable
project. Acquire the clone from `https://github.com/antoniofloresgil/cvw.git`:
the pinned commit is in that fork, not in upstream `openhwgroup/cvw`.
Revision `3b30ba6b6519bd2c26c1437e6d61f632a35cef6c` is exported with license
and source hashes. The supplied clone's branch remains unchanged.
`tb_wally_dse.sv` derives rv32imc with caches, internal memories and prediction
disabled, external 64 KiB zero-wait AHB RAM and `COUNTERS=3`. Only
`IDIV_BITSPERCYCLE` varies (1,2,4); all runs share one compiled ELF/input set.

An independent Python oracle provides 64 operand pairs and signed/unsigned
quotient/remainder answers, including zero divisor and signed overflow cases.
The measured loop contains 256 DIV/REM/DIVU/REMU instructions, operand loads and
volatile result stores. Inline assembly retains these instructions. Every result
and the checksum are checked after the ROI. No firmware reference divides using
the same hardware to create its expected answer.

64-bit high/low/high CSR snapshots measure `mcycle` and `minstret`; sampling
introduces a fixed boundary overhead. The two counter windows are sequentially
sampled, not an atomic PMU snapshot. The reported ratio is an instrumented-window
CPI. It is not a divider-only latency or a general application result.

Output: `labs/build/dse/results.json`, CSV, common ELF/vectors, source identity and
numbered command logs in `labs/build/dse-setup/` and `dse-div*/`.
The CSV baseline is divider=2 when included, otherwise the first requested value.
The JSON reports source/tool/seed identity. Compare only successful runs with
matching binary, inputs, ROI and instruction count. The runner produces no FPGA
resources, achieved frequency, power estimate or physical Pareto conclusion.

## Illustrative Pareto exercise

```sh
python labs/11-dse/analyse.py labs/11-dse/illustrative.csv --output-dir labs/build/dse-analysis
python labs/11-dse/test_analysis.py
```

These commands require only Python 3.10+. The CSV numbers are **invented teaching
data**, not Wally/Nexys Video measurements. They demonstrate a larger cache
reducing cycles while losing elapsed-time benefit through lower frequency.
The script computes workload-normalized geometric-mean speedup, worst workload
speedup and nondominance in geometric-mean time/LUT/BRAM/DSP. It rejects failed
functional/timing results and budget violations, and refuses unmatched binaries,
inputs, ROI, target/origin or requested-clock substitution.

The default budgets (50,000 LUT and 150 BRAM units) are illustrative allocated
budgets, not device capacity claims. Resource units must match the chosen report.
The generated plot is labelled illustrative and is emitted only for that origin.
The schema represents one aggregate observation per candidate/workload; repeated
raw trials and uncertainty need a separately recorded analysis. Geometric means
give each workload equal log weight, not production workload prevalence.

## Student extension

Explain the measured divider result before adding a cache/predictor sweep.
Establish an independent workload and ROI, confirm actual elaborated parameters,
validate event counters, then change one factor. Integrate selected candidates
into the real FPGA fabric, run implementation and board tests when a board is
available, and replace illustrative rows with provenance-backed physical records.
Without a board, extend the real-RTL sweep with an independently checked workload,
preserve the common binary/input/ROI contract and explain cycle changes. Run
device implementation without programming, or analyse instructor-provided reports
as in [Lab 07](../07-implementation/README.md#without-a-physical-board). Keep
student cycle results, supplied device results and illustrative CSV data separate;
do not combine mismatched designs into a measured physical Pareto claim. Submit
the controlled comparison, failure analysis and remaining physical measurements.
gem5 and XS-GEM5 are
additional research environments; this package does not ship or claim an
executed gem5/Wally performance-equivalence model.

The optional `book_figure.py` authoring helper requires Matplotlib and recreates the published illustrative SVG from `summary.json`. It is not required to run the RTL sweep or standard-library analysis.
