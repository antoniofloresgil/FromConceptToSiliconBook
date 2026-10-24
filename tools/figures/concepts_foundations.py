#!/usr/bin/env python3
"""Original conceptual SVGs for the foundations and core chapters (clocking, ISA, SystemVerilog, microarchitecture, cores).

They reuse `Drawing` from architecture.py unchanged. Every figure is conceptual: it explains an organization,
a protocol or a worked example of the chapter and measures nothing. Driven by concepts.py.
"""
from architecture import Drawing, BLUE, GREEN, ORANGE, INK


def flip_flop(d, x, y, w, h, label, color=BLUE):
    d.rect(x, y, w, h, color)
    d.text(x + w / 2, y + h / 2 + 7, label, size=20, bold=True, anchor='middle')
    d.parts.append(f'<path d="M{x + 12} {y + h}l10 -14l10 14" fill="none" stroke="{color}" stroke-width="2"/>')


def setup_hold_timing():
    d = Drawing('clocking-setup-hold-timing', 'Setup and hold: two different races against the clock',
                'One register-to-register path • not to scale • slack is what remains after the stated terms', 620)
    t0, t1 = 190, 790
    d.text(28, 100, 'Setup: the slowest data must arrive before the capture edge', size=21, bold=True)
    for x, label in ((t0, 'launch edge'), (t1, 'capture edge')):
        d.path(f'M{x} 132V300', arrow=False)
        d.text(x, 126, label, size=18, anchor='middle')
    segments = [(t0, 80, 'T cq', BLUE), (t0 + 80, 160, 'T comb', BLUE), (t0 + 240, 80, 'T route', BLUE)]
    for x, w, label, color in segments:
        d.rect(x, 150, w - 4, 46, color)
        d.text(x + w / 2 - 2, 180, label, size=18, anchor='middle')
    d.rect(t0 + 320, 150, 90, 46, GREEN, dash=True)
    d.text(t0 + 365, 180, 'slack', size=18, anchor='middle', color=GREEN)
    d.rect(t0 + 414, 150, t1 - t0 - 414, 46, ORANGE)
    d.text((t0 + 414 + t1) / 2, 180, 'T setup + margin', size=18, anchor='middle', color=ORANGE)
    d.path(f'M{t0} 245H{t1}')
    d.path(f'M{t1} 245H{t0}')
    d.text((t0 + t1) / 2, 236, 'clock period T clk', size=18, anchor='middle')
    d.text(28, 340, 'Hold: the fastest data must not arrive before the same edge has done its job', size=21, bold=True)
    d.path(f'M{t0} 392V500', arrow=False)
    d.text(t0, 384, 'same edge', size=18, anchor='middle')
    d.rect(t0, 410, 160, 46, ORANGE)
    d.text(t0 + 80, 440, 'T hold + margin', size=18, anchor='middle', color=ORANGE)
    d.rect(t0 + 164, 410, 120, 46, GREEN, dash=True)
    d.text(t0 + 224, 440, 'hold slack', size=18, anchor='middle', color=GREEN)
    d.rect(t0, 468, 284, 36, BLUE)
    d.text(t0 + 142, 494, 'fastest cq + comb + route', size=18, anchor='middle')
    d.note(530, 'A slower clock repairs a setup failure, never a hold failure: hold depends on minimum delays at one edge. '
                'A design can meet setup and still fail hold, so both reports are required.')
    d.save()


def synchronizer_circuits():
    d = Drawing('clocking-synchronizer-circuits', 'Two small synchronizers and what each one does',
                'Single-bit level and reset release • neither carries a multi-bit word or a short pulse', 560)
    d.text(28, 100, 'Bit synchronizer for a level', size=21, bold=True)
    d.parts.append(f'<path d="M300 108V250" stroke="{INK}" stroke-width="1.5" stroke-dasharray="6 5"/>')
    d.text(290, 128, 'other domain', size=18, anchor='end'); d.text(310, 128, 'clk domain', size=18)
    d.text(28, 190, 'AsyncIn', size=20, bold=True)
    d.path('M120 185H340')
    flip_flop(d, 340, 150, 120, 70, 'Meta')
    d.path('M460 185H540')
    flip_flop(d, 540, 150, 120, 70, 'Sync')
    d.path('M660 185H760'); d.text(770, 192, 'SyncOut', size=20, bold=True)
    d.text(400, 250, 'may be metastable', size=18, anchor='middle', color=ORANGE)
    d.text(600, 278, 'first value the logic may use', size=18, anchor='middle', color=GREEN)
    d.text(28, 330, 'Reset-release synchronizer', size=21, bold=True)
    d.text(28, 400, 'ResetNAsync', size=20, bold=True)
    d.text(28, 424, 'asserts at once', size=18)
    flip_flop(d, 340, 370, 120, 70, 'Rel[0]')
    flip_flop(d, 540, 370, 120, 70, 'Rel[1]')
    d.path('M300 405H340'); d.text(300, 392, 'tied to 1', size=18, anchor='end')
    d.path('M200 380V340H400', ORANGE, arrow=False)
    d.path('M460 405H540'); d.path('M660 405H760'); d.text(770, 412, 'ResetN', size=20, bold=True)
    d.path('M400 340V370', ORANGE); d.path('M600 340V370', ORANGE); d.path('M400 340H600', ORANGE, arrow=False)
    d.text(500, 330, 'asynchronous clear', size=18, anchor='middle', color=ORANGE)
    d.note(470, 'The first flip-flop stays unpredictable; a second stage lowers the chance that it propagates. Each clock domain needs its own '
                'release synchronizer, and the protocol must tolerate the added delay.')
    d.save()


def crossing_chooser():
    d = Drawing('clocking-crossing-chooser', 'Choose the crossing mechanism from what crosses',
                'Common mechanisms and their limits • the relationship between clocks must be true in hardware', 580)
    d.text(28, 95, 'What crosses', size=19, bold=True); d.text(350, 95, 'Mechanism', size=19, bold=True); d.text(690, 95, 'Limit to design around', size=19, bold=True)
    rows = [('Single, slowly changing', 'control bit', 'Two-flop synchronizer', 'for a level signal'),
            ('Pulse or event', '', 'Toggle synchronizer or', 'request/acknowledge'),
            ('Multi-bit data', 'with control', 'Handshake with a', 'stable payload'),
            ('Independent streaming', 'clocks', 'Asynchronous FIFO,', 'Gray-coded pointers'),
            ('Related clocks with', 'known phase', 'Generated-clock', 'constraints')]
    limits = [('a short event can be', 'missed; latency varies'), ('the source observes', 'completion or keeps it'),
              ('the source holds the', 'payload until accepted'), ('pointer sync and an', 'overflow policy'),
              ('the relationship must', 'hold in the hardware')]
    for i, (a1, a2, m1, m2) in enumerate(rows):
        y = 110 + i * 85
        d.box(28, y, 290, 70, a1, *( [a2] if a2 else []))
        d.box(350, y, 290, 70, m1, m2, color=GREEN)
        d.rect(672, y, 260, 70, ORANGE)
        d.text(802, y + 31, limits[i][0], size=18, anchor='middle'); d.text(802, y + 57, limits[i][1], size=18, anchor='middle')
        d.path(f'M318 {y + 35}H350'); d.path(f'M640 {y + 35}H672')
    d.note(540, 'An ordinary two-flop synchronizer is not a safe transport for a multi-bit word, a pulse that can be missed, or a '
                'transaction that needs data and control to stay together.')
    d.save()


FIGURES = [setup_hold_timing, synchronizer_circuits, crossing_chooser]
