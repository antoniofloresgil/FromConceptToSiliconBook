# 04 — Buses and peripheral effects

Run `python labs/run.py run mmio`. Tools: Icarus and Clang with a RISC-V target. C routines are compiled freestanding; this does not execute them on a board.

The AXI4-Lite endpoint tests write-address-before-data and data-before-address, 100 byte-strobed writes, retained B/R responses, invalid and read-only addresses, event counting and an event concurrent with pending clear. The GPIO/APB test checks setup/access, output masks, invalid registers, synchronized input events and W1C. These are teaching peripherals, not copies of Wally's complete device implementations.

The byte FIFO test checks 2000 cycles. Its documented depth must be a power of two. PWM tests zero/full duty, clamping and period-boundary updates. `mmio_drivers.c` combines the chapter's UART and dependent SPI routines in one translation unit; actual use requires the Wally register map, initialization and exclusive device ownership.

Exercise: add an interrupt handler and a device-level scoreboard in a full integration harness. Preserve the accepted read/side-effect semantics. Extend the AXI test to cover simultaneous reads/writes and further reset points; the supplied suite is a baseline, not an exhaustive protocol certification.

No board is required. For GPIO/PWM extensions, drive logical inputs in simulation and check output values, duty/period and reset transitions with a scoreboard. UART/SPI driver execution needs a CPU/device harness and a serial peer model; keep the existing compile-only result separate. Use [Lab 08](../08-integration/README.md) for full-SoC interrupt observations or [Lab 10](../10-dotproduct/README.md) for the checked accelerator firmware/IRQ example. These do not establish electrical IO behavior.
