# 06 — From assembly to a signature

Run `python labs/run.py run isa`. Tools: Clang with RISC-V assembly support and LLD. The runner compiles the chapter's uncompressed RV32I program, links its explicit memory layout and verifies the signature `0x10`, `0xfffffffd`, `0xfd` at `0x80001100`.

`check_signature.py` is a small independent, program-specific execution oracle. It checks the instructions used by this example and bounded completion; it does not implement the full ISA, privilege, timing or a device platform. The Spike/Sail chapter and `examples/reference-models/` provide a separate RV64 reference-model example. Do not run that RV64 executable on this RV32 oracle.

`python labs/run.py run isa` also runs the retirement-comparison demo from the Spike/Sail chapter. `retire_model.py` is a Python stand-in for a processor's retirement log (not RTL) with a seeded signed-compare fault, `compare_retirement.py` reports the first retired instruction that differs from a Spike log, and `divergence_demo.py` checks that the healthy model matches Spike and that the fault is found at `0x80000028`. The reference is the recorded Spike 1.1.1-dev log in `reference/spike-check.commit.log`; `reference/spike-run.json` records its command, image identity and hashes. With Spike available, `divergence_demo.py BUILD_DIRECTORY --spike spike` produces the reference live. No Spike or RISC-V toolchain is needed for the default run.

Exercise: inspect the ELF using GNU or LLVM tools, reconstruct the backward branch offset and compare signed/unsigned byte loads. Change input data, predict the new signature and update the expected result. Then compare against Spike/Sail under a matching ISA and loader convention.
