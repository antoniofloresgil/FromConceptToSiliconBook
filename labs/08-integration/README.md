# 08 — Wally observations and an accelerator exercise

These guided activities require the separately obtained Wally project and its matching build/harness. They are not included in the nine automatic entries. For the executable AXI/DMA accelerator platform and real Wally firmware test, use [the dot-product project](../10-dotproduct/README.md).

Pin revision `3b30ba6b6519bd2c26c1437e6d61f632a35cef6c` in the fork documented in the appendix. Follow the complete-SoC section of `core-v-wally.qmd`: a cold/warm RAM load, an exactly-once GPIO write and timer entry/return. Use its `rv32gc` reading configuration for cache observations; do not assume that it is the reduced Nexys Video configuration.

For each journey retain instruction context, accepted requests, target completion and architectural/device effects. Use a known image and established trap-entry wrapper. The guide is complete enough to specify observations; actual execution needs the selected Wally harness and firmware.

**Without a board:** carry out these observations in the selected full-Wally RTL simulation. Replace GPIO/LED observation with accepted MMIO writes and checked output transitions, and timer observation with trap entry, acknowledgement and return traces. A UART extension needs a simulated serial decoder/scoreboard. These are harness adaptations, not checked extra scripts. For a supplied executable integration milestone, run `dotproduct-wally` in Lab 10 and explain polling, DMA/result checks and interrupt return. Its cache-disabled fixture and direct interrupt input do not replace the full-SoC cache, timer or PLIC observations; retain those as separate simulation exercises. No `.bit` programming is required. See [the common alternatives](../NO-FPGA.md).

The accelerator chapter's short `fir_engine` listing is an interface/design skeleton, not a completed engine. Treat it as an exercise: specify fixed-point arithmetic and overflow, implement the control/data path, build an independent oracle, add transaction tests and then integrate. Submit a contract, failing/passing cases, resource/timing evidence and an end-to-end software comparison.

For the FIR exercise without physical tools, submit your generic synthesis resources and simulated end-to-end cycle comparison, then analyse provided implementation reports as in [Lab 07](../07-implementation/README.md#without-a-physical-board). Keep supplied timing evidence distinct from results for your own RTL.

No placeholder design or missing board/PDK run is labelled as a passing automated test.
