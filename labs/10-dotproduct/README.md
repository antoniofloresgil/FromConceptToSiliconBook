# Executable HSD project: Wally-controlled AXI/DMA dot product

Run from the book/package root. This reference is a complete starting platform
for P1–P5 and the final project, not the expected extent of student changes.
The [coursework contract](../../appendices/hsd-coursework.qmd) remains the
acceptance specification. The [book walkthrough](../../appendices/executable-project.qmd)
connects the code, experiments and evidence.

## Quick start: standalone reference

```sh
docker build -f labs/Dockerfile -t from-concept-labs:2026.10 .
docker run --rm --network none --mount "type=bind,source=$PWD,target=/work" \
  from-concept-labs:2026.10 python labs/run.py run dotproduct --seed 2026
```

PowerShell:

```powershell
docker run --rm --network none `
  --mount "type=bind,source=${PWD},target=/work" `
  from-concept-labs:2026.10 python labs/run.py run dotproduct --seed 2026
```

The runner generates independent Python integer vectors, simulates all lengths
1–256, repeats with `MAX_LENGTH=16`, checks security/error/reset cases, synthesizes
the IP with Yosys, and runs bounded formal checks. Output is under
`labs/build/dotproduct/`; the run manifest is `labs/build/report.json`.
`run all` includes this entry and the eight earlier automatic entries.

To test a student variant, copy **all** files in `rtl/` to
`labs/work/dotproduct/rtl/` and run:

```sh
python labs/run.py run dotproduct --rtl-dir labs/work/dotproduct/rtl --seed 2027
```

## Real Wally platform

Obtain Wally once, before offline execution:

```sh
git clone https://github.com/openhwgroup/cvw.git ../cvw
git -C ../cvw cat-file -e 3b30ba6b6519bd2c26c1437e6d61f632a35cef6c^{commit}
docker run --rm --network none --env WALLY_ROOT=/cvw \
  --mount "type=bind,source=$PWD,target=/work" \
  --mount "type=bind,source=$(cd ../cvw && pwd),target=/cvw,readonly" \
  from-concept-labs:2026.10 python labs/run.py run dotproduct-wally
```

For PowerShell, use the actual absolute location of the clone:

```powershell
docker run --rm --network none --env WALLY_ROOT=/cvw `
  --mount "type=bind,source=${PWD},target=/work" `
  --mount "type=bind,source=D:\Repos\cvw,target=/cvw,readonly" `
  from-concept-labs:2026.10 python labs/run.py run dotproduct-wally
```

For a native Linux installation of the same tools:

```sh
WALLY_ROOT=../cvw python labs/run.py run dotproduct-wally
```

The runner exports the pinned revision, preserves its license and source
headers, records file hashes, compiles RV32IM/Zicsr firmware with Clang/LLD,
loads its ELF segments into simulated RAM, and compiles the **real**
`wallypipelinedcore` with Verilator. It does not modify or check out the supplied
clone. No FPGA board, vendor tools, privileged Docker access or PDK is required.

The external entry is explicit and excluded from `run all`, since the archive
does not bundle a complete Wally checkout. A missing clone/object/tool, timeout
or firmware failure is a failure; there is no behavioral CPU fallback.

The fixture derives `rv32imc` parameters with IROM/DTIM and both caches disabled,
64 KiB external RAM, and three architectural counter slots. Firmware uses only
RV32IM/Zicsr instructions. The reset vector is `0x80000000`.

| Platform region | Range | Ownership |
| --- | --- | --- |
| RAM | `0x80000000–0x8000ffff` | Shared simulation memory |
| Code/data/stack | Below `0x80008000` | CPU; outside DMA window |
| DMA window | `[0x80008000, 0x8000c000)` | Buffers and result |
| Accelerator | `0x10060000–0x1006001f` | AXI4-Lite via AHB adapter |
| Metrics | `0x8000fe00` onwards | CPU writes; outside DMA window |
| Finish mailbox | `0x8000fff0` | CPU writes PASS/failure code |

The accelerator occupies Wally's configured GPIO address slot; the fixture
instantiates the core, not Wally's complete uncore, so there is no GPIO collision.
`ahb_to_axil.sv` captures the AHB address and **following data phase**, holds
HREADY low through the AXI transaction, accepts AW/W independently, and returns
the two-cycle AHB error response. It supports aligned 32-bit control accesses.

CPU and DMA see the same RAM array. Firmware observes descriptor/result
ownership and `fence iorw, iorw`. The direct connection from `irq` to `MExtInt`
is an explicitly simplified single-source machine-external interrupt route;
the RV32 trap handler executes on Wally and acknowledges the IP. A PLIC,
arbitrated physical RAM fabric, caches/coherence and OS driver are later
integration work. The two-access simulation array is not a synthesized memory
controller or proof of arbitration under conflicting CPU/DMA accesses.

## RTL contract

`dotproduct_mac` holds the exact signed arithmetic expression;
`dotproduct_engine` sequences DMA; `dotproduct_axi` owns registers, validates and
latches descriptors, and reports status/interrupts. `ip-manifest.json` is the
release inventory. All modules use a single clock and active-high synchronous
reset. Legal `MAX_LENGTH` is 1–256; configure it at elaboration.

Each sample occupies a 32-bit word. Only the low 16 bits are signed data;
the upper 16 bits are ignored. The exact signed 64-bit sum is stored low-word
first at an eight-byte-aligned destination. There is no saturation or rounding.

| Offset | Register | Meaning |
| --- | --- | --- |
| `00` | CTRL | Bit 0 START, bit 1 interrupt enable; START reads zero |
| `04` | STATUS | Bits 0 BUSY, 1 DONE, 2 ERROR, 3 IRQ_PENDING |
| `08` | SRC_A | Source A byte address |
| `0c` | SRC_B | Source B byte address |
| `10` | DST | Eight-byte result address |
| `14` | LENGTH | Number of operand pairs |
| `18` | ERROR_CODE | 0 none; 1 descriptor; 2 read; 3 write |
| `1c` | IRQ_ACK | Bit 0 write-one-to-clear; reads zero |

AXI4-Lite AW/W may arrive in either order; one pair is buffered. Responses are
retained under stalls. Descriptor writes use WSTRB byte merging. CTRL/ACK act
only when byte zero is enabled. Unaligned, read-only/unknown writes and
unaligned reads return SLVERR. While busy, descriptor/CTRL writes return SLVERR,
even a CTRL write with zero strobes; active values remain unchanged. ACK/status
accesses remain available. CTRL's enable bit is latched for the job. If a new
terminal event coincides with ACK, the event wins.

An accepted START clears previous completion/error/pending state. An invalid
descriptor is an accepted command with ERROR_CODE=1 and **zero DMA transactions**,
not a slave-access error. Validate the full ranges with widened arithmetic,
length, alignments and destination/source non-overlap. A and B may overlap.
`DMA_BASE` and exclusive `DMA_LIMIT` are trusted parameters, not MMIO registers.

The DMA is a 32-bit AXI4 single-beat INCR master, ID zero, SIZE=2, LEN=0,
WLAST/RLAST and full WSTRB. It issues sequential A/B reads and two result writes,
with LOCK=0, CACHE=0, PROT=0 and QOS=0 sidebands; the teaching RAM does
not enforce protection attributes, so review those defaults for a real fabric,
with at most one transaction outstanding. There is no dependency on WREADY to
assert AWVALID, or on AWREADY to assert WVALID. RRESP/BRESP errors end the job;
DONE requires both write responses to be OKAY. Unexpected response IDs or
missing RLAST are classified as read/write faults. This fixture assumes a
protocol-compliant single-beat target; it is not a recovery engine for malformed
multi-beat traffic.

Reset is coordinated across CPU, adapter, IP and RAM protocol state. RAM contents
persist. An error/reset cannot roll back writes; a second-write error can leave
a partial result. Software accepts the result only with DONE and no ERROR.
There is no watchdog for a nonresponding target: bounded test timeouts detect
such hangs, but hardware needs a separately specified timeout/recovery policy.

## Tests, formal scope and negative evidence

The independent Python oracle decodes signed values without using RTL helpers.
Tests cover every legal baseline length, negative products, noisy upper bits,
wide accumulation, aliased read-only sources, byte strobes, both AW/W arrival
orders, stalled responses, busy rejection, IRQ ACK, polling, eight invalid
descriptor classes, injected first-read/second-write errors, reset during a job
and restart. A deterministic seeded RAM model applies independent wait states.
It checks DMA attributes/ranges and counts exactly `2*N` reads and two writes.
The adapter test poisons address-phase write data, checks that the following
data phase is captured, and checks two-cycle AHB errors and recovery.

`formal/check.py` runs Yosys SAT on the real RTL: 20-cycle bounded control checks
with symbolic inputs and reset in cycle one; 24-cycle engine checks with a
constant valid N=1 descriptor. Assertions check stalled payloads, immutable
active descriptors, DMA range and terminal-write ordering. A separate SAT run
produces a **reachable DONE witness**, saved as `done-witness.vcd`.
Control and engine bounds are different and do not establish unbounded
correctness, all lengths, fairness or full AXI compliance. Simulation supplies
the long-job arithmetic and end-to-end evidence.

```sh
docker run --rm --network none --mount "type=bind,source=$PWD,target=/work" \
  from-concept-labs:2026.10 python labs/10-dotproduct/verify_negative.py /work/labs/build/dotproduct-negative
```

This must reject an unsigned multiplier and an early-DONE mutation. The latter
must also produce a formal counterexample. The mutations occur only in ignored
build copies. `negative-results.json` records expected failures separately.

## Measurements and implementation boundary

`firmware/main.c` compares polling jobs at N=1,8,32,128,256 against a C reference,
then runs an interrupt job and a descriptor rejection. The simulator prints
software cycles and accelerator end-to-end cycles including register setup,
polling and result loads. These are observations in the stated zero-wait CPU
RAM/random-wait DMA fixture; they are not board throughput or achieved MHz.
Use the report's seed, source hashes and tool versions for comparisons.

Yosys generates a generic-cell `dotproduct.json` and statistics. It is not an
FPGA utilization report or a technology timing report. `constraints.sdc`
expresses an illustrative 100 MHz clock and 2 ns interface budgets; review them
with the target fabric and reset strategy before a real physical flow.

The supplied package has RTL, models, firmware, bounded properties, tests,
constraints and a view inventory. It does **not** supply placed/routed views,
scan insertion, ATPG, silicon security certification or fabrication readiness.
For RA7, review controllability/observability of the accumulator and protocol
state, scan/reset/clock interactions, shared-memory test needs, stuck-target
recovery, non-atomic writes and fault containment. Buffer range checks isolate
this IP's traffic but do not constitute a complete SoC security policy; CPU
PMP does not automatically constrain DMA.

## Student progression

1. P1: add an independent dataset and demonstrate the signed numerical contract.
2. P2: reconstruct transactions, then reuse the IP with a smaller maximum length
   or a different trusted window and matching platform/model.
3. P3: boot Wally, explain address/data phases and interrupt return, then measure
   setup, compute and completion separately.
4. P4: add a meaningful bounded property and witness, strengthen the threat model
   and demonstrate a counterexample before repairing the defect.
5. P5: run a chosen technology flow, justify timing/DFT/reliability conclusions
   and mark each IP view as produced, supplied or missing.

Students must make and defend a specified change. Running the supplied reference
alone does not demonstrate the final project's individual learning outcomes.
