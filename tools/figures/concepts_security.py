#!/usr/bin/env python3
"""Original conceptual SVGs for the hardware-security chapter, in the common style.

They reuse `Drawing` from architecture.py unchanged. Every figure is a proposal or a worked example of the chapter:
none of them is a claim about the current Wally repository. Driven by concepts.py.
"""
from architecture import Drawing, BLUE, GREEN, ORANGE, INK


def secure_boot_chain():
    d = Drawing('security-secure-boot-chain', 'A minimal secure boot chain, as a proposal',
                'Template of the chapter, not executable firmware • the anchor is a small trusted first stage', 600)
    cols = [('1  Check', ['bounded manifest parser', 'key from protected policy', 'validate sizes, entry,', 'version, platform', 'authenticate manifest', 'and image digests'], BLUE),
            ('2  Protect and install', ['load into an isolated', 'destination', 'block untrusted writers', 'install memory, DMA and', 'debug policy', 'record the measurement'], GREEN),
            ('3  Enter or recover', ['enter the authorized', 'stage', 'otherwise use an', 'authenticated recovery', 'image and record it'], ORANGE)]
    for i, (title, lines, color) in enumerate(cols):
        x = 28 + i * 307
        d.rect(x, 100, 285, 250, color)
        d.text(x + 142, 132, title, size=21, bold=True, anchor='middle')
        for j, line in enumerate(lines):
            d.text(x + 142, 168 + 28 * j, line, size=18, anchor='middle')
        if i < 2:
            d.path(f'M{x + 285} 225H{x + 307}')
    d.rect(28, 375, 904, 80, INK)
    d.text(44, 405, 'The manifest binds identity, version, load and entry addresses, lengths and hashes,', size=18)
    d.text(44, 431, 'platform features and the next-stage policy. Authenticating bytes alone is not enough.', size=18)
    d.note(485, 'Keep DMA inactive and debug writes rejected between validation and execution. Test corruption, unknown keys, malformed lengths, '
                'old versions and interrupted updates, and a known-valid image as a reachability case.')
    d.save()


def dma_window_check():
    d = Drawing('security-dma-window-check', 'Check the whole span of a DMA descriptor, not only A',
                'Window [B, L) with B = 0x80008000 and L = 0x8000c000 • axis not to scale', 520)
    d.rect(520, 120, 280, 300, GREEN, dash=True)
    d.text(520, 110, 'B', size=19, bold=True, anchor='middle')
    d.text(800, 110, 'L', size=19, bold=True, anchor='middle')
    jobs = [('accepted', 'A >= B and A + N <= L', 560, 700, GREEN),
            ('rejected', 'starts inside, ends outside', 700, 880, ORANGE),
            ('rejected', 'starts below B', 420, 600, ORANGE),
            ('rejected', 'A + N overflows', 836, 932, ORANGE)]
    for i, (verdict, text, x1, x2, color) in enumerate(jobs):
        y = 140 + i * 70
        d.text(28, y + 16, verdict, size=18, bold=verdict == 'accepted')
        d.text(28, y + 42, text, size=18)
        d.rect(x1, y, x2 - x1, 34, color, fill='white', dash=i == 3)
        d.text((x1 + x2) / 2, y + 24, 'A to A+N', size=18, anchor='middle')
    d.text(28, 440, 'Testing only A would accept the second row; wider arithmetic exposes the carry-out of the fourth.', size=18)
    d.note(465, 'Source spans are 4 x length bytes because operands move as four-byte words, not 2 x length. Validate actual transactions, '
                'including padding and stride, rather than an abstract element type.')
    d.save()


def debug_admission():
    d = Drawing('security-debug-admission', 'Lifecycle decides what the debug path may do',
                'The teaching guard admits halt and bus requests • lifecycle and authentication are trusted inputs', 560)
    stages = [('Manufacturing, test', 'test access under production-test rules'), ('Development', 'authenticated sessions inspect broadly'),
              ('Production', 'restricted health and status only'), ('Service, return', 'erase customer secrets first')]
    for i, (name, text) in enumerate(stages):
        y = 100 + i * 92
        d.box(28, y, 390, 68, name, text, color=GREEN if i == 1 else BLUE)
        if i < 3:
            d.path(f'M223 {y + 68}V{y + 92}')
    d.rect(450, 100, 260, 178, INK)
    d.text(580, 130, 'permit requires', size=19, bold=True, anchor='middle')
    for j, line in enumerate(['no reset', "lifecycle == 2'b01", 'authenticated', 'not locked', 'no lock request']):
        d.text(466, 160 + 24 * j, line, size=18)
    d.path('M710 180H750')
    d.box(750, 135, 182, 90, 'permit', 'AND of all', color=ORANGE)
    d.path('M841 225V290H570V320')
    d.path('M841 290V320')
    d.box(450, 320, 240, 70, 'halt_grant', 'permit AND halt_request')
    d.box(700, 320, 232, 70, 'bus_grant', 'permit AND bus_request')
    d.note(470, 'The sticky runtime lock lasts until reset; production stays closed because its lifecycle value is disallowed. The guard admits '
                'requests: it does not drain accepted work, hide returned data or sanitize state.')
    d.save()


FIGURES = [secure_boot_chain, dma_window_check, debug_admission]
