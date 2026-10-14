# 09 — Privileged architecture and MMU

Read [the privileged-memory chapter](../../chapters/04-soc-architecture/privileged-mmu.qmd). Use the complete assembly, linker script and expected signature in `examples/privileged-mmu/`.

This guided activity has two verification boundaries:

1. Compile and run the self-checking RV32/Sv32 example with a separately installed Spike and RISC-V toolchain. Require zero exit and exact signature agreement. Repeat with the read-only alias made writable in a separate variant; the reference test must reject it.
2. Port the program to the pinned full Wally `rv32gc` environment. Adapt loading and termination to its established harness, then trace privilege, tables, TLB misses, walker/LSU ownership, completion and the faulting store. A Spike pass is not Wally RTL evidence.

Deliver address/PTE calculations, tool/revision identities, program hashes, disassembly, reference signature and a documented fault. For Wally also provide annotated waveforms showing that the denied store never updates its shared physical page. Use the chapter's additional exercises for translation fencing, U/S permissions, PMP denial and A/D handling.

`python labs/run.py run mmu` points to this guide. `run all` retains the eight existing automatic labs; it does not silently assume that Spike or a full Wally harness is installed.
