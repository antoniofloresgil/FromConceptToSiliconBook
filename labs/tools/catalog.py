"""Declarative mapping from complete chapter listings to runnable lab files."""

SOURCES = []

def module(chapter, folder, name):
    SOURCES.append({"chapter": f"chapters/{chapter}.qmd", "language": "systemverilog",
                    "starts": [f"module {name}"], "file": f"labs/{folder}/rtl/{name}.sv"})

for chapter, names in [
    ("01-foundations/risc-v-isa", ["rv32_immediate"]),
    ("01-foundations/microarchitecture", ["foundation_alu", "foundation_regfile", "iterative_product"]),
    ("01-foundations/systemverilog", ["word_select", "sample_pipeline", "request_control", "rv_slice", "foundation_decode"]),
    ("01-foundations/clocking-timing", ["bit_synchronizer", "reset_release"]),
]:
    for name in names:
        module(chapter, "01-foundations", name)
module("04-soc-architecture/memories-caches", "02-memory", "sync_memory")
for name in ["transport_fifo", "delayed_memory", "queued_memory"]:
    module("04-soc-architecture/pipelines", "03-transport", name)
module("04-soc-architecture/buses-interrupts", "04-mmio", "event_axil")
for name in ["gpio_teaching_apb", "byte_fifo", "pwm_teaching"]:
    module("04-soc-architecture/peripherals", "04-mmio", name)
module("06-asic-implementation/openroad", "07-implementation", "accumulator")

SOURCES += [
    {"chapter": "chapters/01-foundations/risc-v-isa.qmd", "language": "asm",
     "starts": [".option norvc"], "file": "labs/06-isa/isa_demo.S"},
    {"chapter": "chapters/01-foundations/risc-v-isa.qmd", "language": "ld",
     "starts": ["ENTRY(_start)"], "file": "labs/06-isa/isa_demo.ld"},
    {"chapter": "chapters/04-soc-architecture/memories-caches.qmd", "language": "python",
     "starts": ["class CacheModel:"], "file": "labs/02-memory/cache_model.py"},
    {"chapter": "chapters/04-soc-architecture/peripherals.qmd", "language": "c",
     "starts": ["#include <stdint.h>", "#define SPI_BASE"],
     "file": "labs/04-mmio/mmio_drivers.c"},
    {"chapter": "chapters/06-asic-implementation/librelane.qmd", "language": "yaml",
     "starts": ["DESIGN_NAME: accumulator"],
     "file": "labs/07-implementation/config.yaml"},
    {"chapter": "chapters/06-asic-implementation/openroad.qmd", "language": "tcl",
     "starts": ["create_clock -name core_clk"],
     "file": "labs/07-implementation/constraints.sdc"},
]

LABS = {
    "foundations": {"folder": "01-foundations", "mode": "automatic", "goal": "Immediate/decode/ALU, register state and multicycle arithmetic"},
    "memory": {"folder": "02-memory", "mode": "automatic", "goal": "Synchronous RAM and exact-LRU teaching model"},
    "transport": {"folder": "03-transport", "mode": "automatic", "goal": "FIFO ordering, backpressure and queued memory"},
    "mmio": {"folder": "04-mmio", "mode": "automatic", "goal": "AXI-Lite/APB, byte FIFO and period-boundary PWM"},
    "verilator": {"folder": "05-verification", "mode": "automatic", "goal": "Existing C++ accumulator scoreboard and trace"},
    "cocotb": {"folder": "05-verification", "mode": "automatic", "goal": "Existing Python accumulator scoreboard using Icarus"},
    "isa": {"folder": "06-isa", "mode": "automatic", "goal": "Compile RV32I ELF and check the three-word signature"},
    "synthesis": {"folder": "07-implementation", "mode": "automatic", "goal": "Yosys elaboration, no unintended latches and generic netlist"},
    "fpga": {"folder": "07-implementation", "mode": "guided", "goal": "Pinned Wally/Nexys Video build and physical programming"},
    "asic": {"folder": "07-implementation", "mode": "guided", "goal": "Direct OpenROAD / LibreLane with a separately installed PDK"},
    "wally": {"folder": "08-integration", "mode": "guided", "goal": "Cache/MMIO/interrupt observations in the complete SoC"},
    "mmu": {"folder": "09-privileged-mmu", "mode": "guided", "goal": "RV32/Sv32 reference test, delegated store fault and Wally walker observations"},
    "dotproduct": {"folder": "10-dotproduct", "mode": "automatic", "goal": "AXI/DMA signed dot product: arithmetic, bus errors, security window and reuse"},
    "dotproduct-wally": {"folder": "10-dotproduct", "mode": "external", "goal": "Boot firmware on pinned real Wally, AXI control bridge, DMA and interrupt"},
    "accelerator": {"folder": "08-integration", "mode": "exercise", "goal": "Specify and implement the FIR/accelerator extension"},
    "dse": {"folder": "11-dse", "mode": "guided", "goal": "Real Wally divider sweep and controlled performance/Pareto analysis"},
    "boot": {"folder": "12-boot", "mode": "guided", "goal": "Explicit optional QEMU/OpenSBI handoff and Linux userspace boot"},
    "vector": {"folder": "13-vector", "mode": "guided", "goal": "Checked explicit RVV dot product/masked stores at three VLEN values in QEMU"},
    "security": {"folder": "14-security", "mode": "guided", "goal": "Explicit PMP, real DMA, debug admission, cache observations and bounded formal checks"},
}

WALLY_REVISION = "3b30ba6b6519bd2c26c1437e6d61f632a35cef6c"
WALLY_REPOSITORY = "antoniofloresgil/cvw"
