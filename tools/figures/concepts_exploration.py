#!/usr/bin/env python3
"""Original conceptual SVGs for the accelerator, exploration, vector, debug and PMU chapters, in the common style.

They reuse `Drawing` from architecture.py unchanged. Every figure is conceptual or a worked example of the chapter;
invented values are labelled as such and nothing is a measurement. Driven by concepts.py.
"""
from architecture import Drawing, BLUE, GREEN, ORANGE, INK
from concepts_implementation import mapping_rows


def accel_design_space():
    d = Drawing('accel-design-space', 'Where to accelerate: six choices, from the compiler to DMA',
                'Operand locality and latency drive the choice • a longer job moves down the list', 600)
    d.text(28, 100, 'Choice', size=19, bold=True); d.text(310, 100, 'Best suited to', size=19, bold=True); d.text(660, 100, 'Main cost', size=19, bold=True)
    rows = [(('Better compiler', 'or algorithm'), ('Irregular code,', 'small kernels'), ('No hardware', 'specialization')),
            (('Standard RISC-V', 'extension'), ('A common operation with', 'ratified semantics'), ('Larger core and', 'toolchain target')),
            (('Custom instruction',), ('Short register-to-register', 'operation'), ('Pipeline and', 'toolchain change')),
            (('Internal', 'functional unit'), ('Core-local', 'multicycle operation'), ('Stalls, forwarding,', 'exceptions')),
            (('MMIO accelerator',), ('Longer job with', 'explicit control'), ('Driver, transfer,', 'synchronization')),
            (('DMA-capable', 'accelerator'), ('Large streaming', 'buffers'), ('Arbitration, coherence,', 'protection'))]
    mapping_rows(d, 112, 70, 60, rows, [250, 320, 270], [BLUE, GREEN, ORANGE])
    d.note(540, 'A population count belongs in the instruction datapath; a 1024-sample filter has descriptors, buffers and a completion event, '
                'so it fits an MMIO or DMA engine.')
    d.save()


def accel_intervals():
    d = Drawing('accel-measured-intervals', 'Measure four intervals separately',
                'One job from input ready to output consumed • axis not to scale', 560)
    ticks = [(60, 1), (170, 2), (330, 3), (580, 4), (780, 5), (900, 6)]
    for x, n in ticks:
        d.path(f'M{x} 128V330', arrow=False)
        d.parts.append(f'<circle cx="{x}" cy="112" r="14" fill="white" stroke="{BLUE}" stroke-width="2"/>')
        d.text(x, 118, str(n), size=18, bold=True, anchor='middle')
    pos = dict((n, x) for x, n in ticks)
    rows = [('Driver setup', 2, 3, 'software and MMIO overhead', BLUE), ('Engine active', 3, 4, 'DMA and compute throughput', GREEN),
            ('Interrupt handling', 4, 5, 'scheduling and ISR overhead', ORANGE), ('Whole application', 1, 6, 'the user-visible benefit', INK)]
    for i, (name, a, b, text, color) in enumerate(rows):
        y = 140 + i * 48
        d.rect(pos[a], y, pos[b] - pos[a], 36, color, fill='white')
        d.text(pos[a] + 12, y + 25, name, size=18, bold=True)
    d.text(28, 352, 'What each interval diagnoses', size=19, bold=True)
    for i, (name, a, b, text, color) in enumerate(rows):
        d.text(28, 382 + i * 26, f'{name}: {text}', size=18)
    d.text(28, 494, '1 input ready   2 first register write   3 START accepted', size=18)
    d.text(28, 518, '4 DONE sticky   5 driver completes   6 output consumed', size=18)
    d.note(540, 'Engine-active time against scalar software time leaves out the cost the user pays; compare the full operation. '
                'For very short buffers setup can dominate and a custom instruction can win.')
    d.save()


def buffer_ownership():
    d = Drawing('accel-buffer-ownership', 'Who owns the buffers during a DMA job',
                'The ownership protocol matters as much as the arithmetic • numbered steps follow the chapter', 520)
    d.rect(28, 140, 330, 70, BLUE)
    d.text(193, 182, 'software owns the buffers', size=19, bold=True, anchor='middle')
    d.rect(358, 140, 300, 70, ORANGE)
    d.text(508, 182, 'hardware owns them', size=19, bold=True, anchor='middle')
    d.rect(658, 140, 274, 70, BLUE)
    d.text(795, 182, 'software owns again', size=19, bold=True, anchor='middle')
    marks = [(80, '1'), (193, '2'), (320, '3'), (508, '4'), (720, '5')]
    for x, n in marks:
        d.parts.append(f'<circle cx="{x}" cy="116" r="14" fill="white" stroke="{INK}" stroke-width="2"/>')
        d.text(x, 122, n, size=18, bold=True, anchor='middle')
    steps = ['1  allocate aligned source, destination and coefficient buffers', '2  write the data; do the required cache maintenance',
             '3  program the descriptor and write START', '4  hardware reads and writes until DONE or an error',
             '5  observe DONE, do post-DMA maintenance, consume the output']
    for i, text in enumerate(steps):
        d.text(28, 255 + i * 28, text, size=18)
    d.note(410, 'The protocol keeps software from changing coefficients while hardware reads them, and keeps the accelerator from overwriting a '
                'buffer that the CPU still treats as live. A fence orders accesses; it does not write back dirty lines.')
    d.save()


def cycles_versus_time():
    d = Drawing('explore-cycles-versus-time', 'Fewer cycles can still be slower',
                'Worked arithmetic of the chapter • invented values, not Wally measurements', 460)
    d.text(28, 100, 'Cycles', size=21, bold=True)
    for i, (name, cycles) in enumerate([('A', 10000), ('B', 8000)]):
        y = 118 + i * 52
        d.text(28, y + 30, name, size=20, bold=True)
        d.rect(70, y, cycles * 0.06, 42, BLUE if i == 0 else GREEN)
        d.text(70 + cycles * 0.06 + 14, y + 29, f'{cycles:,} cycles', size=18)
    d.text(28, 260, 'Time = cycles / frequency', size=21, bold=True)
    for i, (name, freq, micro) in enumerate([('A', '50 MHz', 200.0), ('B', '35 MHz', 228.6)]):
        y = 278 + i * 52
        d.text(28, y + 30, name, size=20, bold=True)
        d.rect(70, y, micro * 2.6, 42, BLUE if i == 0 else ORANGE)
        d.text(70 + micro * 2.6 + 14, y + 29, f'{micro:g} us at {freq}', size=18)
    d.note(390, 'B reduces cycles by 20 percent and still takes longer, because its implementation forces a lower clock.')
    d.save()


def amdahl_bound():
    d = Drawing('explore-amdahl-bound', 'A bound tells you where to measure first',
                'Worked example of the chapter • invented profile • S = 1 / ((1 - p) + p / s)', 440)
    d.text(28, 100, 'Baseline application time', size=20, bold=True)
    d.rect(60, 115, 760 - 2, 46, BLUE); d.text(440, 145, 'everything else, 95 percent', size=18, anchor='middle')
    d.rect(820, 115, 40, 46, ORANGE); d.text(840, 106, 'division 5%', size=18, anchor='middle', color=ORANGE)
    d.text(28, 215, 'Division cost eliminated completely', size=20, bold=True)
    d.rect(60, 230, 760 - 2, 46, GREEN); d.text(440, 260, 'unchanged 95 percent', size=18, anchor='middle')
    d.text(60, 305, 'speedup at most 1.053x, however good the divider', size=19, bold=True, color=GREEN)
    d.note(335, 'A large divider gain can be irrelevant to the application. Frequency, overhead and contention come on top of the bound, '
                'so measure them.')
    d.save()


def factor_grid():
    d = Drawing('explore-factor-grid', 'Compare all four corners before crediting either factor',
                'Baseline, A only, B only and A + B • the benefit of A can depend on B', 480)
    d.text(330, 110, 'A off', size=20, bold=True, anchor='middle'); d.text(640, 110, 'A on', size=20, bold=True, anchor='middle')
    d.text(28, 200, 'B off', size=20, bold=True); d.text(28, 330, 'B on', size=20, bold=True)
    cells = [(180, 125, 'baseline', BLUE), (490, 125, 'A only', GREEN), (180, 255, 'B only', GREEN), (490, 255, 'A + B', ORANGE)]
    for x, y, label, color in cells:
        d.rect(x, y, 290, 110, color)
        d.text(x + 145, y + 66, label, size=21, bold=True, anchor='middle')
    d.note(385, 'Prune illegal or infeasible combinations before expensive evaluation, but keep the reasons. Failed builds and wrong results '
                'remain part of the record.')
    d.save()


def mask_tail_store():
    d = Drawing('rvv-mask-tail-store', 'Active, masked-off and tail elements in a masked store',
                'Eight element slots, vl = 6 • the destination array starts with a sentinel S everywhere', 520)
    x0, w = 160, 96
    for i in range(8):
        d.text(x0 + i * w + w / 2, 100, str(i), size=18, bold=True, anchor='middle')
    inputs = ['3', '-1', '5', '0', '7', '-2', 'tail', 'tail']
    mask = ['1', '0', '1', '0', '1', '0', '-', '-']
    action = ['store', 'skip', 'store', 'skip', 'store', 'skip', 'no store', 'no store']
    dest = ['3', 'S', '5', 'S', '7', 'S', 'S', 'S']
    rows = [('input', inputs, BLUE), ('mask v0', mask, ORANGE), ('action', action, GREEN), ('destination', dest, BLUE)]
    for r, (label, cells, color) in enumerate(rows):
        y = 116 + r * 66
        d.text(28, y + 31, label, size=19, bold=True)
        for i, cell in enumerate(cells):
            tail = i >= 6
            d.rect(x0 + i * w + 4, y, w - 8, 46, color, fill='white', dash=tail)
            d.text(x0 + i * w + w / 2, y + 30, cell, size=18, anchor='middle', bold=(r == 3 and cell != 'S'))
    d.path(f'M{x0 + 4} 395H{x0 + 6 * w - 4}'); d.path(f'M{x0 + 6 * w - 4} 395H{x0 + 4}')
    d.text(x0 + 3 * w, 388, 'vl = 6 active elements', size=18, anchor='middle')
    d.note(415, 'A masked-off element is not written, and tail elements generate no stores. Choosing a mask-agnostic policy gives no permission to '
                'clear the unused destination locations; the lab checks guards around the output range.')
    d.save()


def debug_sequence():
    d = Drawing('debug-halt-read-resume', 'Halt, read x10, write it back and resume',
                'Architectural sequence of the chapter • abstract commands through the Debug Module', 560)
    lanes = [(130, 'Debugger'), (480, 'Debug Module'), (830, 'Hart 0')]
    for x, name in lanes:
        d.box(x - 95, 90, 190, 50, name)
        d.path(f'M{x} 140V500', arrow=False)
    steps = [(180, 130, 480, '1  set haltreq', BLUE, False), (225, 480, 830, '2  halt the hart', ORANGE, True),
             (275, 480, 130, '3  dmstatus: halted', BLUE, False), (325, 130, 480, '4  command: read x10', BLUE, False),
             (370, 480, 130, '5  busy clear, cmderr 0, read data0', BLUE, False), (420, 130, 480, '6  write data0, command: write x10', GREEN, False),
             (465, 130, 480, '7  set resumereq: the hart runs again', BLUE, False)]
    for y, a, b, label, color, dashed in steps:
        d.path(f'M{a} {y}H{b}', color, dashed=dashed)
        d.text((a + b) / 2, y - 9, label, size=18, anchor='middle', color=color if color != BLUE else INK)
    d.note(520, 'Clear stale cmderr before the first command, poll abstractcs.busy after each one, and check dcsr, dpc and register contents '
                'at the architectural boundary.')
    d.save()


def debug_access_mechanisms():
    d = Drawing('debug-access-mechanisms', 'Three ways to reach the target',
                'Each mechanism raises its own integration question', 560)
    cols = [('Abstract commands', ['halted hart', 'register and CSR access', 'through data registers', 'poll busy, check cmderr'], ('What does cmderr', 'report?'), BLUE),
            ('Program buffer', ['halted hart executes', 'a short sequence', 'an implicit ebreak', 'ends it'], ('What state may it', 'clobber?'), GREEN),
            ('System Bus Access', ['the DM is a bus manager', 'no hart involved', 'works while a hart runs', 'physical addresses'], ('Identity, coherency,', 'side effects?'), ORANGE)]
    for i, (title, lines, question, color) in enumerate(cols):
        x = 28 + i * 312
        d.rect(x, 100, 285, 200, color)
        d.text(x + 142, 134, title, size=21, bold=True, anchor='middle')
        for j, line in enumerate(lines):
            d.text(x + 142, 172 + 28 * j, line, size=18, anchor='middle')
        d.rect(x, 345, 285, 76, color, fill='white', dash=True)
        d.text(x + 142, 376, question[0], size=18, bold=True, anchor='middle')
        d.text(x + 142, 402, question[1], size=18, bold=True, anchor='middle')
    d.text(28, 332, 'Integration question', size=19, bold=True)
    d.note(445, 'Run-control debug does not expose every internal wire: if post-silicon work needs microarchitectural events, add trace or '
                'performance counters. SBA data may not be coherent with what each hart observes.')
    d.save()


def rv32_safe_read():
    d = Drawing('pmu-rv32-safe-read', 'Why an RV32 counter read repeats the high half',
                'A 64-bit counter wraps its low half between two reads • high, low, high, then compare', 520)
    d.rect(28, 105, 470, 56, BLUE)
    d.text(263, 140, 'counter 0x00000000 FFFFFFFF', size=19, bold=True, anchor='middle')
    d.rect(498, 105, 434, 56, GREEN)
    d.text(715, 140, 'counter 0x00000001 00000000', size=19, bold=True, anchor='middle')
    d.path('M498 95V175', ORANGE, arrow=False)
    d.text(498, 90, 'low half wraps', size=18, anchor='middle', color=ORANGE)
    reads = [(300, 'csrr mcycleh', 'hi0 = 0', BLUE), (640, 'csrr mcycle', 'lo = 0x00000000', BLUE), (830, 'csrr mcycleh', 'hi1 = 1', GREEN)]
    for x, op, value, color in reads:
        d.path(f'M{x} 215V175', color)
        d.text(x, 240, op, size=18, anchor='middle')
        d.text(x, 266, value, size=19, bold=True, anchor='middle')
    d.rect(28, 310, 904, 96, ORANGE, dash=True)
    d.text(44, 338, 'Without the check, {hi0, lo} = 0x00000000 00000000:', size=18)
    d.text(44, 364, 'the value jumped back by about 4.29 billion counts.', size=18)
    d.text(44, 390, 'With it, hi0 != hi1, so the loop repeats and returns a consistent value.', size=18, bold=True)
    d.note(430, 'The same pattern applies to minstret and every RV32 hpmcounter. For a short window, still keep the 64-bit difference: a 32-bit '
                'delta can wrap.')
    d.save()


FIGURES = [accel_design_space, accel_intervals, buffer_ownership, cycles_versus_time, amdahl_bound, factor_grid,
           mask_tail_store, debug_sequence, debug_access_mechanisms, rv32_safe_read]
