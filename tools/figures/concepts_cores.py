#!/usr/bin/env python3
"""Original conceptual SVGs for the core-comparison and privileged-architecture chapters, in the common style.

They reuse `Drawing` from architecture.py unchanged. Every figure is conceptual: it explains an organization,
a protocol or a worked example of the chapter and measures nothing. Driven by concepts.py.
"""
from architecture import Drawing, BLUE, GREEN, ORANGE, INK
from concepts_implementation import mapping_rows


def two_loads_and_add():
    d = Drawing('cores-two-loads-and-add', 'Two loads and an independent add, with and without overlap',
                'Invented time units, not cycles • in-order retirement is not drawn', 640)
    x0, unit = 150, 50
    d.text(28, 112, 'time', size=18)
    for tick in range(0, 15, 2):
        d.text(x0 + tick * unit, 112, str(tick), size=18, anchor='middle')
    d.text(28, 160, 'Blocking cache, one outstanding load', size=20, bold=True)
    for tick in range(0, 15, 2):
        d.path(f'M{x0 + tick * unit} 175V300', arrow=False)
    rows = [(0, 6, 'load 1', BLUE), (6, 12, 'load 2', BLUE), (12, 13, 'add', ORANGE)]
    for k, (a, b, label, color) in enumerate(rows):
        d.rect(x0 + a * unit, 180 + k * 40, (b - a) * unit - 3, 34, color, fill='white')
        d.text(x0 + (a + b) / 2 * unit, 203 + k * 40, label, size=18, anchor='middle')
    d.text(x0 + 13 * unit + 14, 283, 'done at 13', size=18, bold=True, color=ORANGE)
    d.text(28, 340, 'Nonblocking cache and instruction window', size=20, bold=True)
    for tick in range(0, 15, 2):
        d.path(f'M{x0 + tick * unit} 355V480', arrow=False)
    rows = [(0, 6, 'load 1', BLUE), (1, 7, 'load 2', BLUE), (2, 3, 'add', GREEN)]
    for k, (a, b, label, color) in enumerate(rows):
        d.rect(x0 + a * unit, 360 + k * 40, (b - a) * unit - 3, 34, color, fill='white')
        d.text(x0 + (a + b) / 2 * unit, 383 + k * 40, label, size=18, anchor='middle')
    d.text(x0 + 7 * unit + 14, 410, 'done at 7', size=18, bold=True, color=GREEN)
    d.note(505, 'If both loads miss in the same narrow downstream port, the overlap may still be limited: counting execution units cannot '
                'substitute for asking how many misses can be in flight.')
    d.save()


def workload_bottlenecks():
    d = Drawing('cores-workload-bottlenecks', 'Four workloads, four different bottlenecks',
                'One benchmark can reward an architectural accident • separate the pressures on purpose', 520)
    d.text(28, 100, 'Workload', size=19, bold=True); d.text(300, 100, 'Dominant pressure', size=19, bold=True); d.text(622, 100, 'Signal to examine', size=19, bold=True)
    rows = [(('Register-only', 'reduction'), ('Arithmetic throughput', 'and dependencies'), ('CPI, multiplier and', 'divider latency')),
            (('Branch-heavy', 'parser'), ('Predictor and', 'misprediction recovery'), ('Taken branches, flush', 'cycles')),
            (('Pointer chase',), ('Dependent memory', 'latency'), ('Load-to-use delay,', 'miss service time')),
            (('Independent array', 'streams'), ('Memory bandwidth', 'and concurrency'), ('Outstanding requests,', 'misses, bytes per cycle'))]
    mapping_rows(d, 112, 84, 70, rows, [240, 290, 290], [BLUE, GREEN, ORANGE])
    d.note(460, 'If PicoRV32 and Wally differ strongly in the register-only test but little in the pointer chase, memory latency probably '
                'dominates the latter. Hold memory latency fixed and separate cold start from steady state.')
    d.save()


def pte_bits():
    d = Drawing('mmu-pte-bits', 'An Sv32 page-table entry and how to read it',
                'Field widths are not drawn to scale • bit 31 at the left', 560)
    x, widths = 28, [('PPN [31:10], 22 bits', 380, BLUE), ('RSW', 60, INK)]
    for label, width, color in widths:
        d.rect(x, 100, width - 4, 60, color)
        d.text(x + width / 2 - 2, 137, label, size=18, anchor='middle')
        x += width
    for letter in 'DAGUXWRV':
        d.rect(x, 100, 54, 60, ORANGE if letter in 'DA' else GREEN if letter in 'RWX' else BLUE)
        d.text(x + 27, 140, letter, size=22, bold=True, anchor='middle')
        x += 58
    d.text(28, 190, 'V valid • R read • W write • X execute • U user • G global • A accessed • D dirty', size=18)
    d.text(28, 216, 'RSW (bits 9:8) is reserved for software and carries no permission.', size=18)
    rows = [('V = 0', 'entry rejected: page fault', ORANGE), ('V = 1, R = W = X = 0', 'pointer to the next-level table (U, A, D zero in the baseline)', BLUE),
            ('V = 1, legal R/W/X', 'leaf: a mapping with these permissions', GREEN), ('W = 1 with R = 0', 'reserved encoding', ORANGE)]
    for i, (cond, meaning, color) in enumerate(rows):
        y = 250 + i * 54
        d.rect(28, y, 290, 44, color)
        d.text(173, y + 29, cond, size=18, bold=True, anchor='middle')
        d.path(f'M318 {y + 22}H350')
        d.rect(350, y, 582, 44, color, fill='white')
        d.text(366, y + 29, meaning, size=18)
    d.note(480, 'A and D record page use and modification in the PTE; they are not the dirty bits of a cache line. A TLB caches the translation, '
                'so a changed PTE needs sfence.vma before the next local translation relies on it.')
    d.save()


def trap_delegation():
    d = Drawing('mmu-trap-delegation', 'Delegation chooses the handler for a synchronous exception',
                'A trap taken in M-mode stays in M-mode • delegation is not an interrupt enable', 480)
    d.box(28, 155, 270, 140, 'Exception in U or S', 'ecall: code 8 from U,', '9 from S', 'page fault, illegal instruction')
    d.box(350, 175, 190, 100, 'medeleg', 'bit for this cause', 'set?', color=ORANGE)
    d.path('M298 225H350')
    d.box(620, 100, 312, 110, 'S-mode handler', 'stvec, sepc, scause, stval', 'return with sret', color=GREEN)
    d.box(620, 240, 312, 110, 'M-mode handler', 'mtvec, mepc, mcause, mtval', 'return with mret')
    d.path('M540 205H580V155H620', GREEN)
    d.path('M540 245H580V295H620')
    d.text(560, 196, 'yes', size=18, bold=True, color=GREEN, anchor='middle')
    d.text(560, 268, 'no', size=18, bold=True, anchor='middle')
    d.note(385, 'The experiment delegates only the store page fault (cause 15), so its final S-mode ecall stays machine-handled. '
                'Read medeleg back: the implementation decides which bits it accepts.')
    d.save()


FIGURES = [two_loads_and_add, workload_bottlenecks, pte_bits, trap_delegation]
