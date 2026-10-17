# Complete asynchronous FIFO: CDC and reset epochs

Checked optional experiment for [Chapter 4](../../chapters/01-foundations/clocking-timing.qmd#sec-async-fifo).
Uses the ordinary lab image, no board or PDK. It remains outside the nine
automatic entries in `run all`.

## Interface and supported experiment

`async_fifo.sv` supplies local write/read ready-valid ports, binary addresses,
registered Gray publication, two receiving stages per pointer, and registered
full/empty flags. `DEPTH=2**ADDR_BITS`, with `ADDR_BITS>=1`, `DATA_W>=1`.
The checked matrix uses DATA_W 8/32 and ADDR_BITS 1/2/4 (depth 2/4/16).
Other parameters need their own evidence. The code is original MIT teaching RTL,
following the registered-pointer/local-comparison architecture of Cummings's
FIFO Style #1. No upstream paper or third-party RTL is bundled.

Common `arst_n` asynchronously asserts both local resets. Each release pipeline
waits for two edges of its own clock. Reset discards unread entries, not memory
contents. It must also reset/quiesce connected interfaces. Independent side-only
resets, arbitrary non-power-of-two depths and depth one are unsupported.

The memory has a write-clocked port and an asynchronous combinational read.
This is a fall-through small-array/LUTRAM-style model, not a portable synchronous
BRAM or characterized SRAM wrapper. A synchronous memory needs a read adapter
whose prefetch, output validity and capacity are verified together.

## Reproduce without changing the sources

Build/acquire `from-concept-labs:2026.10` through the [shared guide](../README.md).
The recorded image ID is
`sha256:995529592338d24ea28263345ce2ac981c46da21a7a0e82664ffe3361f9a923c`.
The checked run used UID/GID 1000 and read-only project sources with a separate
writable results mount. Choose a new output directory for a repeat.

Linux/WSL, from the repository or extracted practice-package root:

```sh
mkdir -p labs/build/async-fifo-results
docker run --rm --network none --user "$(id -u):$(id -g)" --env HOME=/tmp \
  --env "LAB_IMAGE_ID=$(docker image inspect --format '{{.Id}}' from-concept-labs:2026.10)" \
  --mount "type=bind,source=$PWD,target=/work,readonly" \
  --mount "type=bind,source=$PWD/labs/build/async-fifo-results,target=/results" \
  from-concept-labs:2026.10 python labs/24-async-fifo/run.py --output /results/run
```

Native Windows PowerShell:

```powershell
New-Item -ItemType Directory -Path labs/build/async-fifo-results -Force | Out-Null
$fifoImageId = docker image inspect --format '{{.Id}}' from-concept-labs:2026.10
docker run --rm --network none --env HOME=/tmp --env "LAB_IMAGE_ID=$fifoImageId" `
  --mount "type=bind,source=${PWD},target=/work,readonly" `
  --mount "type=bind,source=${PWD}/labs/build/async-fifo-results,target=/results" `
  from-concept-labs:2026.10 python labs/24-async-fifo/run.py --output /results/run
```

Python 3.10+, Icarus 12.0 and Yosys 0.33 are the recorded tools. No network or
physical FPGA participates in execution. Native runs can invoke the same Python
entry point when those tools are installed. `run.py` exits nonzero on a failed
simulation, synthesis, structural review, timeout or undetected deliberate defect.

## What the checked run establishes

Each width/depth is simulated with seeds 2026/2027 under four independent clock
schedules (write/read half-periods and read phase, in ns): `(5,7,2)`, `(3,11,1)`,
`(13,2,0)`, `(5,5,0)`. The last schedule intentionally stresses coincident edges;
it does not replace the unequal-period cases.

The [48-run dossier](reference/results.json) records:

- 58,328 accepted writes = 57,744 accepted reads + 584 reset-discarded words.
- Three common-reset epochs per run, including live reset and stopped clocks.
- Writer-first fill while the read clock is stopped; reader-first release after flush.
- Exact directed capacity, repeated pointer/address wraps, producer/consumer stalls.
- 8,108 coincident accepted write/read observations and conservative flag latency.
- 2,060 observed multi-bit differences between successive destination Gray samples.
  These are legal skipped states, not a source unit-distance violation.

The independent queue records input handshakes and compares output handshakes.
Its oracle never reads DUT memory or derives expected data from internal pointers.
It checks source/output stall stability and accepted-transfer conservation, not
instantaneous agreement between delayed local flags and global occupancy.

Six actual generic netlists are retained. `check_structure.py` verifies registered
Gray sources in the sending domain, two receiving flip-flops per pointer bit,
their destination clock, retained attributes and first-stage fanout only to
stage two. This is a limited digital connectivity review, not a dedicated CDC
analysis engine or physical placement/reset-tree qualification.

Four variants under the raw build directory are required to fail:

| Deliberate defect | Required diagnosis |
| --- | --- |
| Flip only one Gray bit in the full comparison | `OVERFLOW` |
| Allow reading with empty storage | `UNDERFLOW` |
| Publish a binary pointer instead of Gray | `GRAY_SOURCE` |
| Bypass the write reset-release pipeline | `RELEASE_WITH_STOPPED_CLOCK` |

Binary publication is rejected by a structural/source-transition obligation;
ideal RTL simulation is not a metastability experiment. The reference RTL is
never overwritten. Healthy simulation is not an MTBF or routed timing result.

## Physical constraints and integration

[`constraints/cdc-template.xdc`](constraints/cdc-template.xdc) is an **adaptation
template**, not a checked Vivado run. Bind actual Gray launch Q pins and stage-one
D pins for both directions, pointer widths, real clocks and reviewed delay/skew
budgets. The template rejects missing collections or unexpected bit counts.
Use margins below each direction's minimum source period and inspect exception
precedence: a blanket asynchronous clock group may override max-delay checks.
Keep first-to-second-stage timing active in the receiving domain. Review the
raw memory data path and reset recovery/removal separately. Synchronizer
attributes alone do not close any of those implementation obligations.

For AXI/streaming integration, carry related metadata in the same entry and
define reset/error handling above this FIFO. Dropping unread entries does not
complete or roll back an already accepted multi-beat transaction. Independent
domain power/reset sequencing requires a separately specified rejoin protocol.

## Collect and audit the portable reference

```sh
python labs/24-async-fifo/collect.py labs/build/async-fifo-results/run \
  --reference-dir labs/build/async-fifo-reference
python labs/24-async-fifo/verify_reference.py --reference-dir labs/build/async-fifo-reference
python labs/24-async-fifo/verify_reference.py
```

The last command audits the delivered reference with Python only. It checks
source/artifact hashes, all 48 configurations, transaction conservation, actual
netlist connections and the expected nonzero exits of faulty variants. Logs
are retained as `.txt`, so the practice ZIP preserves them. There is no formal
multiclock proof, analog metastability model, memory-macro characterization,
placed CDC/RDC analysis or FPGA bring-up claim in this experiment.
