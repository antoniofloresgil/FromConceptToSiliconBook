# 20 — Advanced multicore integration: two Linux CPUs and DMA

Read [Multicore SoC Integration: Coherence, Interconnects, and Verification](../../chapters/07-advanced-topics/multicore-integration.qmd). This is optional advanced study, outside the compulsory twelve-week/6 ECTS workload and the nine automatic labs. No FPGA is required.

## Two separate evidence boundaries

1. **Actual Linux execution on QEMU:** two online CPUs, processes pinned to logical CPUs 0 and 1, an unchanged Lab 18 kernel driver/device model, 64 release/acquire job handoffs and 32 jobs from overlapping callers. Every result is checked against independent signed integer arithmetic. The driver copies userspace arrays into its private DMA allocation; this is not zero-copy DMA from the userspace shared mapping.
2. **Explicit finite models:** two coherent CPU views and a non-snooping DMA agent, dirty-owner forwarding, whole-line clean/invalidate/writeback, visibility-event publication, resource dependencies, simple arbitration and hypothetical completion generations. These produce concrete stale-data/lost-result traces and repaired cases. They are not a complete cache protocol, RVWMO model, coherent Wally RTL or physical performance model.

The QEMU run must not be used as evidence that real private caches were cleaned or snooped. The actual Wally reference remains single-hart; adding a coherent fabric, secondary boot, cache maintenance and multicore firmware to it is a separate guided extension.

## Reproduce

First build the boot and Linux accelerator images using [Lab 18](../18-linux-accelerator/README.md). Its preserved sources are reused unchanged. Then build this small additional image:

```sh
docker build --platform linux/amd64 -f labs/20-multicore/Dockerfile -t from-concept-multicore:2026.10 .
```

The image compiles only the new static PID 1/application and packages its initramfs. It inherits the existing QEMU 8.2.2 device model, Linux 6.12 SMP kernel, OpenSBI, UAPI and driver. The runner checks the image's cached source hashes and the new application against the supplied sources. Record/preserve the actual image ID; local image tags alone are not immutable environment locks.

Linux/WSL:

```bash
docker run --rm --platform linux/amd64 --network none --user "$(id -u):$(id -g)" --env HOME=/tmp \
  --env CASE_IMAGE_ID="$(docker image inspect --format '{{.Id}}' from-concept-multicore:2026.10)" \
  --mount "type=bind,source=$PWD,target=/work" from-concept-multicore:2026.10 \
  python3 labs/20-multicore/run.py --output-dir labs/build/multicore-run
```

PowerShell with Docker Desktop Linux containers:

```powershell
$multicoreImage = docker image inspect --format '{{.Id}}' from-concept-multicore:2026.10
docker run --rm --platform linux/amd64 --network none --env HOME=/tmp `
  --env "CASE_IMAGE_ID=$multicoreImage" `
  --mount "type=bind,source=${PWD},target=/work" from-concept-multicore:2026.10 `
  python3 labs/20-multicore/run.py --output-dir labs/build/multicore-run
```

Select a fresh output directory each time. The runner requires two DT hart nodes, two online CPUs, actual affinity checks, all 64 handoff records, correct accepted DMA transaction counts for all 96 jobs, overlapping caller phases and interrupt accounting. A timeout, wrong numerical result, missing marker or incomplete boot fails. The output preserves guest logs, configuration, DT, disassembly, command/tool/image/source identities and artifact hashes.

## Contract and source files

`smp.c` is the executable application. The producer fills a shared job and publishes an epoch with release semantics. The CPU 1 worker acquires it before the ioctl, then publishes completion with release semantics. CPU 0 acquires completion before reading the result or reusing the job. Lock-free atomics are required; both processes check their affinity. Epochs do not wrap within this bounded test.

After 64 jobs, both CPUs rendezvous before issuing 16 private jobs each. Their measured caller intervals must overlap. This demonstrates concurrent offered load and correct serialization through the driver; it does not measure individual mutex wait times or require a particular fairness policy. Both caller buffers remain private during this phase. The engine still has a single hardware descriptor context and executes one job at a time.

`models.py` implements a separate two-word-per-line visibility abstraction. It permits dirty-owner forwarding between CPUs while DMA accesses backing RAM. A fence changes ordering only. A local clean cannot write back another hart's dirty entry; the explicitly modeled domain clean can. Output invalidation and a dirty-line overwrite are separate tests. The local-only action is deliberately not asserted to implement architectural Zicbom semantics. The RISC-V specification defines the actual scope/observation point of those operations.

The event enumerator retains only executions where the consumer sees this epoch's published flag. Its release/acquire labels add particular visibility edges, not the full C11 or RVWMO axioms. In this finite abstraction, neither edge permits 6 stale outcomes in 12 executions; release-only and acquire-only each permit 1 in 4; both permit 0 in 1. Do not run a racy C program and interpret undefined behavior as a hardware litmus result.

The dependency graph finds an explicit request/probe/response wait cycle and removes a blocking dependency in its repaired variant. Arbitration counts assume continuously requesting clients and an always-accepting sink. The completion-generation example is hypothetical: the actual IP has no reset/epoch register and retains Lab 18's quarantine policy after timeout.

## Evidence and interpretation

The compact [execution report](reference/report.json), [guest log](reference/uart.txt), [DT](reference/virt.dts) and [model traces](reference/models.json) are actual author evidence. The raw run also retains full static-binary disassembly and the DTB; their hashes remain in the report but those bulky/generated artifacts are omitted from the compact reference.

Audit the preserved sources and evidence without QEMU using `python labs/20-multicore/verify_reference.py`. To publish a new completed author run, use `python labs/20-multicore/collect.py labs/build/multicore-run/report.json` and rerun the verifier. `python labs/20-multicore/models.py labs/build/multicore-models/models.json` runs the finite examples without Docker or a compiler.

Emulator timings describe software scheduling, copies and the QEMU device's declared virtual delay. The total handoff interval includes publication, scheduling, ioctl/DMA completion, checking and guest logging. It is not hardware multicore speedup, cache/NoC latency or energy. Physical cache-line size and maintenance reach are not inferred from the source's illustrative 64-byte alignment.

## Advanced extensions

- Replace the publication with a correctly scoped formal litmus test and an identified language/ISA model. Preserve useful-traffic witnesses as well as forbidden outcomes.
- Study an existing coherent subsystem revision, follow a real ownership transaction and explain finite resource admission/response rules. Add one meaningful stress test or property.
- Integrate a real two-client coherent RTL subsystem. Establish dirty-input and stale-output scenarios deliberately, then add pressure, errors and reset. A second Wally core instance alone does not provide that subsystem.
- Implement and measure a matched physical or calibrated timing model, retaining identical work, source/configuration and measurement intervals. Keep these results separate from the current emulator/model dossier.
