# 08 — Wally observations and an accelerator exercise

These guided activities require the separately obtained Wally project and its matching build/harness. They are not included in the eight automatic unit labs.

Pin revision `3b30ba6b6519bd2c26c1437e6d61f632a35cef6c` in the fork documented in the appendix. Follow the complete-SoC section of `core-v-wally.qmd`: a cold/warm RAM load, an exactly-once GPIO write and timer entry/return. Use its `rv32gc` reading configuration for cache observations; do not assume that it is the reduced Nexys Video configuration.

For each journey retain instruction context, accepted requests, target completion and architectural/device effects. Use a known image and established trap-entry wrapper. The guide is complete enough to specify observations; actual execution needs the selected Wally harness and firmware.

The accelerator chapter's short `fir_engine` listing is an interface/design skeleton, not a completed engine. Treat it as an exercise: specify fixed-point arithmetic and overflow, implement the control/data path, build an independent oracle, add transaction tests and then integrate. Submit a contract, failing/passing cases, resource/timing evidence and an end-to-end software comparison.

No placeholder design or missing board/PDK run is labelled as a passing automated test.
