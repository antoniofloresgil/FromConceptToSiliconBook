#!/usr/bin/env python3
"""Original explanatory SVGs for chapters that had no figure, in the book's common architectural style.

They reuse `Drawing` from architecture.py unchanged. Every figure is conceptual: it explains an organization
or a protocol and measures nothing. --check compares the outputs without rewriting them.
"""
import argparse
from pathlib import Path

from architecture import Drawing, outputs, BLUE, GREEN, ORANGE, INK

FIG = Path(__file__).resolve().parents[2] / 'figures'


def isa():
    d = Drawing('isa-instruction-formats', 'RV32I instruction formats',
                '32-bit base words • bit 31 at the left • dashed outline = immediate bits', 600)
    x0, bit, y0, pitch, h = 104, 26, 138, 70, 48
    formats = [
        ('R', [('funct7', 7), ('rs2', 5), ('rs1', 5), ('funct3', 3), ('rd', 5), ('opcode', 7)]),
        ('I', [('imm[11:0]', 12), ('rs1', 5), ('funct3', 3), ('rd', 5), ('opcode', 7)]),
        ('S', [('imm[11:5]', 7), ('rs2', 5), ('rs1', 5), ('funct3', 3), ('imm[4:0]', 5), ('opcode', 7)]),
        ('B', [('imm[12|10:5]', 7), ('rs2', 5), ('rs1', 5), ('funct3', 3), ('imm[4:1|11]', 5), ('opcode', 7)]),
        ('U', [('imm[31:12]', 20), ('rd', 5), ('opcode', 7)]),
        ('J', [('imm[20|10:1|11|19:12]', 20), ('rd', 5), ('opcode', 7)]),
    ]
    for high in [31, 24, 19, 14, 11, 6]:
        d.text(x0 + (31 - high) * bit + 4, y0 - 12, str(high), size=18)
    d.text(x0 + 32 * bit - 4, y0 - 12, '0', size=18, anchor='end')
    for row, (name, fields) in enumerate(formats):
        y = y0 + row * pitch
        d.text(36, y + 33, name, size=26, bold=True)
        x = x0
        for label, bits in fields:
            immediate = label.startswith('imm')
            d.rect(x + 1, y, bits * bit - 2, h, ORANGE if immediate else BLUE, dash=immediate)
            d.text(x + bits * bit / 2, y + 31, label, size=18, anchor='middle')
            x += bits * bit
    d.note(y0 + 5 * pitch + h + 28,
           'R register arithmetic • I immediate ALU, loads, jalr • S stores • B branches • U lui, auipc • J jal.',
           'B and J show the instruction bits an immediate comes from; the text reassembles them, sign-extends and adds the implied zero bit.')
    d.save()


def multicycle():
    d = Drawing('microarchitecture-multicycle-controller', 'A multicycle controller: phases and exits',
                'Illustrative schedule from the chapter • not Wally’s pipeline', 470)
    top = [('Fetch request', 'present the PC once', 'exit: accepted', GREEN), ('Fetch wait', 'hold the PC', 'exit: response', GREEN),
           ('Decode', 'capture operands', 'exit: decoded', BLUE), ('Execute', 'compute the result', 'exit: result ready', BLUE)]
    for i, (title, line, exit_, color) in enumerate(top):
        x = 28 + i * 232
        d.box(x, 100, 205, 100, title, line, exit_, color=color)
        if i:
            d.path(f'M{x - 27} 150H{x}')
    bottom = [(724, 'Data request', 'present the access', 'exit: accepted', GREEN),
              (492, 'Data wait', 'await data or ack', 'exit: response', GREEN),
              (260, 'Commit', 'apply the updates', 'then fetch the next', BLUE)]
    for x, title, line, exit_, color in bottom:
        d.box(x, 285, 205, 100, title, line, exit_, color=color)
    d.path('M826 200V285')
    d.text(836, 262, 'load/store', size=18)
    d.path('M724 335H697')
    d.path('M492 335H465')
    d.path('M260 335H130V200')
    d.path('M760 200V245H362V285', ORANGE, dashed=True)
    d.text(372, 236, 'ALU ops skip the data phases', size=18, color=ORANGE)
    d.note(405, 'A request state leaves when its target accepts. Staying in it while the target is',
           'ready would resend the request on every cycle.')
    d.save()


def description_to_hardware():
    d = Drawing('systemverilog-description-to-hardware', 'From a description to the circuit it implies',
                'The process type decides what is built; a declaration alone does not', 640)
    rows = [(100, 'always_comb', 'y = a & b;'),
            (250, 'always_ff @(posedge clk)', 'q <= d;'),
            (400, 'two chained nonblocking', 's1 <= d;  s2 <= s1;')]
    for y, title, code in rows:
        d.box(28, y, 330, 110, title, code, color=INK)
    d.path('M358 155H430')
    d.box(430, 115, 250, 80, 'Combinational logic', 'no storage, no clock')
    d.path('M680 155H760'); d.text(780, 162, 'y', size=21, bold=True)
    d.path('M358 305H430')
    d.box(430, 265, 250, 80, 'Flip-flop', 'samples d on clk edge')
    d.parts.append(f'<path d="M444 345l10-14l10 14" fill="none" stroke="{BLUE}" stroke-width="2"/>')
    d.path('M680 305H760'); d.text(780, 312, 'q', size=21, bold=True)
    d.path('M358 455H400')
    d.box(400, 415, 150, 80, 'Flip-flop', 's1')
    d.path('M550 455H590')
    d.box(590, 415, 150, 80, 'Flip-flop', 's2')
    d.path('M740 455H800'); d.text(820, 462, 's2', size=21, bold=True)
    d.parts.append(f'<path d="M414 495l10-14l10 14M604 495l10-14l10 14" fill="none" stroke="{BLUE}" stroke-width="2"/>')
    d.note(540, 'Both assignments in the last row update on the same edge, so s2 holds',
           'what d was two edges ago. A combinational process that leaves an output',
           'unassigned on some path describes a latch.')
    d.save()


def ready_valid():
    d = Drawing('pipelines-ready-valid-waveform', 'Ready/valid: an item is transferred once',
                'Values just before each rising edge • a dot marks valid and ready both high', 540)
    x0, step, n = 166, 126, 6
    signals = [('valid', [1, 1, 1, 1, 1, 0]), ('ready', [1, 0, 0, 1, 1, 1]),
               ('payload', ['A', 'B', 'B', 'B', 'C', '—']), ('transfer', [])]
    actions = ['Accept A', 'Hold B', 'Hold B', 'Accept B', 'Accept C', 'No transfer']
    for i in range(n):
        x = x0 + (i + 1) * step
        d.path(f'M{x} 110V350', arrow=False)
        d.text(x, 97, str(i), size=18, anchor='middle')
    d.text(28, 97, 'Edge →', size=18)
    for row, (label, values) in enumerate(signals):
        y = 150 + row * 62
        d.text(28, y + 5, label, size=20)
        if not values:
            continue
        if all(isinstance(v, int) for v in values):
            path = ''
            for i, value in enumerate(values):
                x, yy = x0 + i * step, y - 14 if value else y + 12
                path += f' {"M" if i == 0 else "L"}{x} {yy}H{x + step}'
            d.path(path, arrow=False)
        else:
            for i, value in enumerate(values):
                d.rect(x0 + i * step + 4, y - 19, step - 8, 34, BLUE, fill='white')
                d.text(x0 + i * step + step / 2, y + 5, value, size=20, anchor='middle')
    for edge in (0, 3, 4):
        d.parts.append(f'<circle cx="{x0 + (edge + 1) * step}" cy="{150 + 3 * 62}" r="8" fill="{GREEN}"/>')
    for i, action in enumerate(actions):
        d.text(x0 + i * step + step / 2, 395, action, size=18, anchor='middle')
    d.note(420, 'B stays valid and unchanged until it is accepted at edge 3.',
           'B in three intervals is one request; the observer counts A, B and C once.',
           'Changing B to C before its handshake would break the contract.')
    d.save()


def sv32_walk():
    d = Drawing('mmu-sv32-two-level-walk', 'Sv32: a two-level walk for a 4 KiB page',
                'Worked example from the chapter • VA 0x40000120 translates to PA 0x80012120', 620)
    x0, bit = 64, 26
    fields = [('VPN[1]  31:22', 10, '= 256'), ('VPN[0]  21:12', 10, '= 0'), ('offset  11:0', 12, '= 0x120')]
    d.text(28, 100, 'Virtual address 0x40000120', size=19, bold=True)
    x = x0
    centers = []
    for label, bits, value in fields:
        d.rect(x + 1, 112, bits * bit - 2, 54, BLUE)
        d.text(x + bits * bit / 2, 134, label, size=18, anchor='middle')
        d.text(x + bits * bit / 2, 156, value, size=18, anchor='middle')
        centers.append(x + bits * bit / 2)
        x += bits * bit
    d.box(28, 255, 180, 110, 'satp.PPN', 'root = PPN × 4 KiB', color=ORANGE)
    d.box(260, 255, 210, 110, 'Root table', '0x80010000', '[256] → 0x20004401')
    d.box(520, 255, 210, 110, 'Level-0 table', '0x80011000', '[0] → 0x200048c7', color=GREEN)
    d.box(780, 255, 152, 110, 'Data page', '0x80012000', color=GREEN, kind='memory')
    d.path('M208 310H260', ORANGE)
    d.path('M470 310H520')
    d.path('M730 310H780', GREEN)
    d.path(f'M{centers[0]} 166V210H365V255')
    d.path(f'M{centers[1]} 166V210H625V255')
    d.path(f'M{centers[2]} 166V210H856V255')
    d.text(238, 298, '1', size=18, bold=True, anchor='middle', color=ORANGE)
    d.text(495, 298, '2', size=18, bold=True, anchor='middle')
    d.text(755, 298, '3', size=18, bold=True, anchor='middle', color=GREEN)
    d.path('M856 365V425', GREEN)
    d.box(520, 425, 412, 76, 'Physical address 0x80012120', 'page 0x80012000 + offset 0x120', color=GREEN)
    d.text(28, 410, '1  satp locates the root table', size=18)
    d.text(28, 440, '2  a non-leaf PTE names the next table', size=18)
    d.text(28, 470, '3  the leaf PTE names the page', size=18)
    d.note(520, 'An invalid entry, a denied permission or a misaligned superpage is a page fault; a failing physical read is an access fault.')
    d.save()


def xilinx_flow():
    d = Drawing('nextpnr-xilinx-to-bitstream', 'From a netlist to a configured FPGA',
                'Open Xilinx 7-series flow for the Nexys Video • each arrow is an inspectable file', 660)
    d.box(28, 95, 250, 70, 'Yosys netlist', 'nexysvideo.json')
    d.box(28, 185, 250, 70, 'XDC constraints', 'clocks, pins, IO standards')
    d.box(28, 275, 250, 70, 'Chip database', 'X-Ray, one exact part', color=GREEN)
    d.box(330, 150, 250, 130, 'nextpnr-xilinx', 'pack, place, route', 'timing at --freq')
    for y in (130, 220, 310):
        d.path(f'M278 {y}H304V215H330')
    d.box(650, 95, 282, 70, 'Routed netlist', 'nexysvideo-routed.json', color=GREEN)
    d.box(650, 185, 282, 70, 'Report', 'nexysvideo-report.json', color=GREEN)
    d.box(650, 275, 282, 70, 'FASM', 'nexysvideo.fasm', color=GREEN)
    for y in (130, 220, 310):
        d.path(f'M580 215H615V{y}H650')
    d.rect(330, 305, 250, 62, ORANGE, dash=True)
    d.text(455, 331, 'Timing not met?', size=18, bold=True, anchor='middle', color=ORANGE)
    d.text(455, 355, 'change RTL or constraints', size=18, anchor='middle', color=ORANGE)
    d.path('M791 345V415H520', GREEN)
    d.box(350, 380, 170, 70, 'fasm2frames', 'X-Ray database')
    d.box(105, 380, 200, 70, 'xc7frames2bit', 'serialize frames')
    d.path('M350 415H305')
    d.box(105, 500, 200, 70, '.bit', 'configuration image', color=GREEN)
    d.path('M205 450V500')
    d.box(350, 500, 250, 70, 'openFPGALoader', 'program the board', kind='peripheral')
    d.path('M305 535H350')
    d.note(595, 'FASM lists features; it is not the bitstream. A report that meets timing',
           'does not show that the board works.')
    d.save()

def pmu_counter():
    d = Drawing('pmu-counter-path', 'From an event to software: one performance counter',
                'mhpmeventN, mhpmcounterN and mcountinhibit • the event encoding is implementation-defined', 600)
    d.box(28, 100, 240, 95, 'Event sources', 'retire, branch, cache', 'stall, exception')
    d.box(310, 100, 230, 95, 'Event select', 'one signal per counter')
    d.box(590, 100, 342, 95, 'Counter N', '64-bit; low and high', 'halves on RV32')
    d.path('M268 147H310'); d.path('M540 147H590')
    d.box(310, 250, 230, 80, 'mhpmeventN', 'machine-mode CSR', color=ORANGE)
    d.path('M425 250V195', ORANGE, dashed=True)
    d.box(590, 250, 250, 80, 'mcountinhibit', 'bit N = 1 stops it', color=ORANGE)
    d.path('M715 250V195', ORANGE, dashed=True)
    d.box(590, 395, 342, 80, 'CSR read port', 'mcounteren gates lower privilege')
    d.path('M860 195V395', GREEN)
    d.box(28, 395, 480, 80, 'Software', 'RV32: read high, low, high', 'until the high half is stable')
    d.path('M590 435H508')
    d.note(505, 'Counters observe the workload and are not part of it.',
           'A selector that does nothing gives misleading measurements.')
    d.save()


def debug_architecture():
    d = Drawing('debug-architecture', 'Debug: transport, module and hart',
                'Execution-based design • from the debugger to the hart through the DTM and the DM', 520)
    chain = [('Debugger', 'GDB, OpenOCD'), ('Probe', 'host to target'), ('JTAG DTM', 'transport'), ('DM', 'run control'), ('Hart', 'Debug Mode')]
    for i, (title, line) in enumerate(chain):
        x = 28 + i * 191
        d.box(x, 100, 140, 95, title, line, color=GREEN if title == 'Hart' else BLUE, kind='cpu' if title == 'Hart' else None)
        if i:
            d.path(f'M{x - 51} 147H{x}')
    d.text(385, 134, 'JTAG', size=18, anchor='middle')
    d.text(576, 134, 'DMI', size=18, anchor='middle')
    d.box(601, 290, 331, 95, 'System Bus Access', 'SoC interconnect', kind='interconnect', color=GREEN)
    d.path('M671 195V290', GREEN)
    d.text(681, 250, 'SBA', size=18, color=GREEN)
    d.rect(28, 290, 520, 95, ORANGE, dash=True)
    d.text(44, 322, 'Policy: lifecycle and authentication decide what', size=18, color=ORANGE)
    d.text(44, 348, 'the debug path may do; a DMI request is not trusted.', size=18, color=ORANGE)
    d.path('M548 337H601', ORANGE, dashed=True)
    d.note(410, 'DM = Debug Module; DMI = Debug Module Interface. Abstract commands reach the',
           'registers through a debug ROM and the program buffer; System Bus Access',
           'reads memory without running the hart.')
    d.save()

def verilator_flow():
    d = Drawing('verilator-build-and-run', 'From RTL to a running Verilator model',
                'accumulator example • editing the RTL means rebuilding the executable', 560)
    d.box(28, 100, 250, 70, 'accumulator.sv', 'the RTL under test')
    d.box(28, 190, 250, 70, 'sim_main.cpp', 'stimulus, clock, checks', color=GREEN)
    d.box(340, 125, 250, 110, 'verilator', '--cc --exe --build', '-Wall --trace')
    d.path('M278 135H309V150H340'); d.path('M278 225H309V210H340')
    d.box(650, 125, 282, 110, 'Generated C++ model', 'obj_dir/Vaccumulator.h', 'plus build rules')
    d.path('M590 180H650')
    d.text(340, 262, '-Wall warnings stop the build', size=18, color=ORANGE)
    d.box(28, 330, 250, 80, 'C++ compiler', 'make builds the model', 'and the harness')
    d.box(340, 330, 250, 80, 'Vaccumulator', 'executable simulation')
    d.box(650, 330, 282, 80, 'Result', 'PASS or FAIL, exit status', 'accumulator.vcd', color=GREEN)
    d.path('M791 235V292H153V330')
    d.path('M278 370H340'); d.path('M590 370H650')
    d.note(440, 'Each simulated cycle drives the inputs with the clock low, evaluates, raises',
           'the clock, evaluates, checks, lowers the clock and evaluates again.')
    d.save()


def reference_comparison():
    d = Drawing('reference-model-comparison', 'One program, several executors, one comparison',
                'The functional models and the RTL run the same ELF', 570)
    d.box(28, 215, 190, 110, 'check.elf', 'same bytes for', 'every executor', color=INK)
    runners = [(100, 'Spike', 'functional reference', None, BLUE, 235), (230, 'Sail model', 'functional reference', None, BLUE, 275),
               (360, 'RTL under test', 'testbench logger', 'cpu', GREEN, 315)]
    for y, title, line, kind, color, target in runners:
        d.box(290, y, 250, 90, title, line, kind=kind, color=color)
        d.path(f'M218 270H254V{y + 45}H290')
        d.path(f'M540 {y + 45}H580V{target}H620')
    d.box(620, 195, 312, 150, 'Comparator', 'signature words', 'retired instructions')
    d.text(776, 395, 'first difference wins:', size=18, color=ORANGE, anchor='middle')
    d.text(776, 421, 'repair it, then rerun', size=18, color=ORANGE, anchor='middle')
    d.path('M776 372V347', ORANGE, dashed=True)
    d.note(472, 'A signature points to a wrong stored word; the retirement log points',
           'to the first instruction that differs. Timing needs other measurements.')
    d.save()

FIGURES = [isa, multicycle, description_to_hardware, ready_valid, sv32_walk, xilinx_flow, pmu_counter,
           debug_architecture, verilator_flow, reference_comparison]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    for draw in FIGURES:
        draw()
    for name, data in outputs.items():
        target = FIG / name
        if args.check:
            if not target.is_file() or target.read_bytes() != data:
                raise ValueError('Stale figure: ' + str(target))
        else:
            target.write_bytes(data)
    print(('CHECKED' if args.check else 'GENERATED'), len(outputs), 'explanatory SVG figures')


if __name__ == '__main__':
    main()
