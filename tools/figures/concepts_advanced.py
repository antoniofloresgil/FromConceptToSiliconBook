#!/usr/bin/env python3
"""Original conceptual SVGs for the advanced chapters (multicore, security, accelerators, exploration, vectors, debug, PMU).

They reuse `Drawing` from architecture.py unchanged. Every figure is conceptual: it explains an organization,
a protocol or a worked example of the chapter and measures nothing. Driven by concepts.py.
"""
from architecture import Drawing, BLUE, GREEN, ORANGE, INK


def dirty_input_trace():
    d = Drawing('multicore-dirty-input-trace', 'Dirty input: the CPUs agree, the accelerator does not',
                'Operand starts at 0 • hart 0 writes 7 • a non-snooping DMA read reaches backing memory', 560)
    heads = ['Initial', 'Produce', 'Publish', 'Bad launch', 'Repaired']
    rows = [('Hart 0', [['no modified', 'copy'], ['store 7;', 'line is dirty'], ['release the', 'job token'], ['keeps the', 'dirty line'], ['completes the', 'visibility', 'action']]),
            ('Hart 1', [['no modified', 'copy'], ['waits for', 'the token'], ['acquire token;', 'CPU load', 'sees 7'], ['orders the', 'MMIO start'], ['launches after', 'the handoff']]),
            ('RAM / DMA', [['operand 0'], ['RAM still 0'], ['RAM still 0'], ['DMA reads 0', '(wrong)'], ['DMA reads 7']])]
    x0, w = 150, 154
    for i, head in enumerate(heads):
        d.text(x0 + i * (w + 6) + w / 2, 100, head, size=19, bold=True, anchor='middle')
    for r, (name, cells) in enumerate(rows):
        y = 118 + r * 130
        d.text(28, y + 60, name, size=19, bold=True)
        for i, lines in enumerate(cells):
            wrong = name == 'RAM / DMA' and i == 3
            right = name == 'RAM / DMA' and i == 4
            color = ORANGE if wrong else GREEN if right else BLUE
            d.rect(x0 + i * (w + 6), y, w, 118, color, dash=wrong)
            top = y + 59 - 13 * (len(lines) - 1) + 6
            for k, line in enumerate(lines):
                d.text(x0 + i * (w + 6) + w / 2, top + 26 * k, line, size=18, anchor='middle', bold=wrong or right)
    d.note(520, 'A fence orders accesses the platform already defines, and a lock serializes submitters; neither writes the dirty line back. '
                'The repair is the platform visibility action before the doorbell.')
    d.save()


def job_lifecycle():
    d = Drawing('multicore-job-lifecycle', 'Put the ordering edges on the job lifecycle',
                'One producer hart, one submitting hart, one DMA engine • each edge uses its own mechanism', 560)
    steps = [('1  Initialize', 'the payload', 'producer hart', BLUE), ('2  Publish', 'release store of', 'the epoch', BLUE),
             ('3  Acquire', 'load sees the epoch', 'submitting hart', BLUE), ('4  Prepare', 'DMA-visible state', 'platform DMA API', ORANGE),
             ('5  Doorbell', 'ordered MMIO write', 'device accessor', ORANGE), ('6  Completion', 'observed by the', 'driver', ORANGE),
             ('7  CPU visibility', 'established for', 'the result', ORANGE), ('8  Acknowledge', 'release store;', 'producer acquires', BLUE)]
    for i, (title, l1, l2, color) in enumerate(steps):
        row, col = divmod(i, 4)
        x, y = 28 + col * 228, 110 + row * 170
        d.box(x, y, 208, 110, title, l1, l2, color=color)
        if col < 3:
            d.path(f'M{x + 208} {y + 55}H{x + 228}')
    d.path('M820 220V250H132V280')
    d.text(28, 420, 'Blue edges: CPU-to-CPU synchronization with language atomics. Orange edges: CPU-to-device handoff.', size=18)
    d.text(28, 446, 'Only after step 8 may the next iteration change the job.', size=18, bold=True)
    d.note(480, 'A release operation used for CPU-to-CPU publication is not a universal MMIO barrier, and a lock among harts does not exclude '
                'the DMA engine. The driver turns software ownership into a hardware rule.')
    d.save()


def partial_line_corruption():
    d = Drawing('multicore-partial-line-corruption', 'A shared line lets a stale word overwrite the result',
                'Result word and CPU flag share one line • sequence is timing-dependent, so a small test can pass', 520)
    cols = [('1  CPU writes the flag', ('result 0', 'flag 1 (new)'), ('result 0', 'flag 0'), BLUE),
            ('2  DMA writes the result', ('result 0 (stale)', 'flag 1'), ('result 49', 'flag 0'), GREEN),
            ('3  Dirty line is evicted', ('line leaves', 'the cache'), ('result 0 (lost 49)', 'flag 1'), ORANGE)]
    for k, (title, cache, ram, color) in enumerate(cols):
        x = 28 + k * 306
        d.text(x + 135, 100, title, size=19, bold=True, anchor='middle')
        d.text(x, 135, 'CPU cache line', size=18)
        d.rect(x, 145, 270, 90, color, dash=k == 2)
        d.text(x + 135, 182, cache[0], size=18, anchor='middle'); d.text(x + 135, 210, cache[1], size=18, anchor='middle')
        d.text(x, 275, 'RAM', size=18)
        d.rect(x, 285, 270, 90, color)
        d.text(x + 135, 322, ram[0], size=18, anchor='middle', bold=k == 2); d.text(x + 135, 350, ram[1], size=18, anchor='middle')
        if k == 1:
            d.text(x + 135, 262, 'DMA write', size=18, anchor='middle', color=GREEN)
            d.path(f'M{x + 135} 268V285', color)
        if k == 2:
            d.text(x + 135, 262, 'writeback', size=18, anchor='middle', color=ORANGE)
            d.path(f'M{x + 135} 268V285', color, dashed=True)
    d.note(410, 'Extra fences cannot make a partial dirty writeback merge correctly. Allocate and align independently owned regions at the '
                'maintenance granularity of the real target, and keep CPU-only state out of device payload lines.')
    d.save()


FIGURES = [dirty_input_trace, job_lifecycle, partial_line_corruption]
