# Continuous accelerator verification

Executable companion to [Appendix C](../../appendices/reproducible-labs.qmd#sec-hardware-ci)
and [Chapter 7](../../chapters/03-simulation-verification/verification-methodology.qmd).
The ordinary teaching image executes the same Lab 10 accelerator, unmodified:

```text
Lint -> Elaboration -> Simulation -> Formal -> Synthesis -> Reports
```

## Run locally, offline

Build `from-concept-labs:2026.10` using the [shared guide](../README.md).
Use fresh child output names on a repeat. Linux/WSL, from the repository or
extracted practice-package root:

```bash
mkdir -p labs/build/hardware-ci
identity=$(docker image inspect --format '{{.Id}}' from-concept-labs:2026.10)
docker run --rm --network none --user "$(id -u):$(id -g)" --env HOME=/tmp \
  --env LAB_IMAGE_ID="$identity" \
  --mount "type=bind,source=$PWD,target=/work,readonly" \
  --mount "type=bind,source=$PWD/labs/build/hardware-ci,target=/results" \
  from-concept-labs:2026.10 python labs/25-hardware-ci/run.py --output /results/positive
docker run --rm --network none --user "$(id -u):$(id -g)" --env HOME=/tmp \
  --env LAB_IMAGE_ID="$identity" \
  --mount "type=bind,source=$PWD,target=/work,readonly" \
  --mount "type=bind,source=$PWD/labs/build/hardware-ci,target=/results" \
  from-concept-labs:2026.10 python labs/25-hardware-ci/negative.py --output /results/negative
```

Native PowerShell, for the positive run:

```powershell
New-Item -ItemType Directory -Force labs/build/hardware-ci | Out-Null
$ciImageId = docker image inspect --format '{{.Id}}' from-concept-labs:2026.10
docker run --rm --network none --env HOME=/tmp --env "LAB_IMAGE_ID=$ciImageId" `
  --mount "type=bind,source=${PWD},target=/work,readonly" `
  --mount "type=bind,source=${PWD}/labs/build/hardware-ci,target=/results" `
  from-concept-labs:2026.10 python labs/25-hardware-ci/run.py --output /results/positive
```

For negatives, substitute `negative.py --output /results/negative` in the same
container invocation. Test a student copy with `run.py --rtl /work/labs/work/my-ip/rtl
--output /results/my-ip`; copy all four Lab 10 RTL files first. Tool failures,
timeouts, unexpected lint messages and incomplete simulation/proof results reject
the candidate. Reports distinguish `fail` from later `skipped` stages.

## Fixed contract and review budget

`contract.json` preserves elaborated port directions, widths, signedness and
default parameters. Behavioral register/AXI/DMA contracts remain checked by the
independent Lab 10 tests and bounded assertions; the JSON is not a semantic ABI
proof. Both maximum lengths 256/16 and the AHB bridge are simulated with seed 2026.
Formal checks are 20-cycle symbolic control BMC and a 24-cycle length-one engine
check with a reachable DONE witness. They are not unbounded progress or a full
arithmetic proof.

`policy.json` records exact tool versions and a reviewed multiset of six existing
Verilator diagnostics. Four address zero-extension warnings and two intentionally
unused signals are retained visibly in logs; no warning class is globally waived
by the gate. `-Wno-fatal` lets the parser inspect all warnings, then unrecognized,
changed, additional or missing diagnostics fail the stage. A new tool version
requires explicit baseline/lint review. Do not silently loosen policy on failure.

The fixed, flattened Yosys synthesis at `MAX_LENGTH=256` has **5,662 generic cells**.
The cap is **5,946 = ceil(5,662 × 1.05)**: a teaching review budget allowing up to
5% logical growth before requiring an explicit architecture/cost decision.
There is no physical-area, maximum-frequency or power inference from that count.
The successful pipeline and all four actual mutations are retained in `reference/`:

| Mutation | Rejection stage | Observation |
| --- | --- | --- |
| Change default MAX_LENGTH from 256 to 257 | Elaboration | Contract mismatch |
| Unsigned multiplication | Simulation | Independent arithmetic mismatch |
| Insert deliberately false formal assertion | Formal | Failure with a VCD counterexample |
| Add retained, unused 256-bit counter | Reports | Functional/proof stages pass; 6,668 cells exceed 5,946 |

The false assertion checks sensitivity of the proof stage; it is not a newly
discovered design defect. The unused counter is deliberately preserved with
`keep` so optimization cannot remove the cost-control experiment.

## CI tiers and qualification boundary

The repository's `publish.yml` calls `hardware-ci.yml` on main-branch pushes and
pull requests. Publication depends on this gate and the broader labs/Wally suite.
`hardware-ci.yml` can also be dispatched explicitly. `if: always()` uploads
reports, logs, netlists, witness/counterexample and snapshotted inputs on failure.
The workflow definitions are supplied as [evidence snapshots](reference/workflows/hardware-ci.yml)
in the downloadable package; the book-publishing workflow needs the full book.
Branch protection/reviewer rules are repository settings, not enabled by these files.

`physical-regression.yml` is **manual only**, depends on a fresh fast gate at the
same Git revision, and uses the pinned ORFS image to rerun the Lab 21 repaired
100 MHz ASIC, equivalence and `physical_gate.py`. It checks extracted setup/hold,
electrical limits, constraints, final router DRC and GDS readback. The Lab 17
manifest rejects a changed locked physical baseline: a modified IP needs a new
reviewed candidate manifest and physical campaign, never inherited old results.
FPGA candidate sweeps and the separate reference-PDK DRC/LVS continuation retain
their [Lab 21](../21-physical-closure/README.md) and [Lab 22](../22-layout-verification/README.md)
recipes. No per-commit place-and-route or manufacturing qualification is implied.

The new fast pipeline and mutations were executed locally in Docker, without
network, as UID/GID 1000 with read-only sources. The physical acceptance helper
was checked against the existing actual Lab 21 run; this addition does not claim
a new physical implementation or a completed GitHub-hosted Actions run.

## Audit or collect evidence

```bash
python labs/25-hardware-ci/verify_reference.py
python labs/25-hardware-ci/collect.py labs/build/hardware-ci --reference-dir labs/build/hardware-ci-reference
```

The first command audits shipped hashes, stage outcomes, real synthesized cell
counts, bounded-proof logs and failure counterexample with Python only. It does
not rerun tools. The collector needs the real positive and negative output folders;
it converts formal transcripts to `.txt` and waveforms to `.vcd.txt` for portable
ZIP inclusion. Rename a waveform copy to `.vcd` to open it in GTKWave. Raw tool
binaries are omitted from the compact reference; commands and their hashes remain
recorded. Outputs are never automatically promoted into the policy baseline.
