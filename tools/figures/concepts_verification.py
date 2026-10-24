#!/usr/bin/env python3
"""Original conceptual SVGs for the simulation and verification chapters, in the common style.

They reuse `Drawing` from architecture.py unchanged. Every figure is conceptual: it explains an organization,
a protocol or a worked example of the chapter and measures nothing. Driven by concepts.py.
"""
from architecture import Drawing, BLUE, GREEN, ORANGE, INK


def verification_ladder():
    d = Drawing('verification-levels-ladder', 'Ten levels of verification, each with its own question',
                'A chain of contracts: a downstream pass cannot make up for a missing upstream obligation', 700)
    rows = [('Static analysis, elaboration', 'Does it elaborate and mean what we intend?', BLUE),
            ('Self-checking unit tests', 'Does the block meet its contract?', BLUE),
            ('Assertions and formal', 'Do the properties hold, bounded or proven?', BLUE),
            ('Coverage', 'What did the tests actually reach?', BLUE),
            ('Processor architecture', 'Are the visible instruction effects correct?', GREEN),
            ('Subsystem, firmware, SoC', 'Do blocks, firmware and interrupts interact?', GREEN),
            ('Synthesis and equivalence', 'Did the transformation keep the behavior?', ORANGE),
            ('Clocks, CDC/RDC, STA', 'Are timing and crossing contracts met?', ORANGE),
            ('FPGA and ASIC physical', 'Do geometry and electrical rules hold?', ORANGE),
            ('Silicon and production test', 'Does the real part work; which parts pass?', INK)]
    for i, (title, question, color) in enumerate(rows):
        y = 92 + i * 52
        d.rect(28, y, 904, 46, color)
        d.parts.append(f'<circle cx="62" cy="{y + 23}" r="17" fill="white" stroke="{color}" stroke-width="2"/>')
        d.text(62, y + 30, str(i + 1), size=19, bold=True, anchor='middle')
        d.text(94, y + 30, title, size=19, bold=True)
        d.text(430, y + 30, question, size=18)
    d.text(28, 640, 'Levels 1-4: RTL unit • 5-6: processor and system • 7-9: implementation • 10: the device', size=18)
    d.note(655, 'Each level needs its own evidence: LVS can match the wrong netlist, and a booting FPGA can still hide an arithmetic corner case.')
    d.save()


def plan_entry():
    d = Drawing('verification-plan-entry', 'What one entry of a verification plan contains',
                'Example row DP-NUM of the dot-product project • an unexecuted row stays visible in the plan', 540)
    rows = [('1  Requirement', 'ID, source, statement', ('DP-NUM: low 16-bit signed samples', 'accumulate exactly into 64 bits')),
            ('2  Level and environment', 'where it runs, assumptions', ('named per entry, with trust and', 'reset assumptions')),
            ('3  Stimulus', 'including a failure case', ('signed extremes, mixed signs,', 'noisy upper bits, every length')),
            ('4  Checker and observation', 'oracle and expected outcome', ('independent Python model; both', 'result words after success')),
            ('5  Coverage and evidence', 'status and references', ('result status plus immutable', 'evidence references'))]
    for i, (title, sub, example) in enumerate(rows):
        y = 95 + i * 82
        d.box(28, y, 330, 66, title, sub, color=GREEN if i in (0, 4) else BLUE)
        d.rect(400, y, 532, 66, INK)
        d.text(416, y + 29, example[0], size=18)
        d.text(416, y + 55, example[1], size=18)
        d.path(f'M358 {y + 33}H400')
        if i < 4:
            d.path(f'M193 {y + 66}V{y + 82}', arrow=False)
    d.note(510, 'Review the plan for omitted features as well as omitted tests: a checker that disagrees with the specification is a verification defect '
                'even when every regression is green.')
    d.save()


def assert_assume_cover():
    d = Drawing('formal-assert-assume-cover', 'Assume, assert and cover around one design',
                'FIFO example of the chapter • the solver explores symbolic inputs, not one generated sequence', 520)
    d.box(28, 130, 250, 140, 'assume A', 'the environment:', 'producer holds an', 'unaccepted request', color=GREEN)
    d.box(340, 130, 250, 140, 'Design + harness', 'initial state I', 'next-state function T')
    d.box(650, 100, 282, 100, 'assert P', 'occupancy <= capacity', 'stalled output keeps its item', color=ORANGE)
    d.box(650, 230, 282, 100, 'cover C', 'full, exchange, then empty', 'must be reachable', color=GREEN)
    d.path('M278 200H340'); d.path('M590 170H650'); d.path('M590 235H650', GREEN, dashed=True)
    d.note(360, 'An assumption is part of the interface contract. Assuming that the consumer always accepts data, or that no input arrives, '
                'makes the proof empty; the cover witness shows that useful traffic is still admitted. A guarantee becomes another '
                "block's assumption only after the connection and reset contract have been checked.")
    d.save()


def bmc_and_induction():
    d = Drawing('formal-bmc-induction', 'Bounded checking and induction answer different questions',
                'A twelve-step check is bounded; an unbounded result needs a base case and an inductive step', 620)
    d.text(28, 100, 'Bounded model checking, horizon 12', size=21, bold=True)
    for i in range(13):
        x = 70 + i * 66
        d.parts.append(f'<circle cx="{x}" cy="160" r="17" fill="white" stroke="{BLUE}" stroke-width="2"/>')
        d.text(x, 166, str(i), size=18, anchor='middle')
        if i:
            d.path(f'M{x - 66 + 17} 160H{x - 17}')
    d.text(70, 205, 'reset', size=18, anchor='middle')
    d.text(500, 205, 'no violation found within these steps: a bounded result', size=18, anchor='middle')
    d.text(28, 265, 'Induction', size=21, bold=True)
    d.box(28, 285, 430, 100, 'Base case', 'the properties hold from', 'the specified initial state', color=GREEN)
    d.box(502, 285, 430, 100, 'Inductive step', 'invariants that hold over the window', 'still hold after the next transition', color=GREEN)
    d.path('M458 335H502')
    d.text(28, 412, 'Possible outcomes', size=19, bold=True)
    d.box(28, 424, 290, 80, 'Proved', 'for the modeled system', color=GREEN)
    d.box(335, 424, 290, 80, 'Counterexample', 'a failing trace', color=ORANGE)
    d.box(642, 424, 290, 80, 'Inconclusive', 'say so plainly', color=BLUE)
    d.note(530, 'The step may start from states unreachable from reset, for example equal occupancies with unrelated pointers. '
                'Strengthen the invariant with the relationship that is missing; never assume the mismatch away.')
    d.save()


def cocotb_architecture():
    d = Drawing('cocotb-architecture', 'Where cocotb sits between the test and the simulator',
                'The circuit stays in SystemVerilog or VHDL • a HDL simulator executes it • cocotb is not a simulator', 500)
    d.box(28, 110, 250, 130, 'Python test', 'async coroutines', 'driver, monitor,', 'reference model', color=GREEN)
    d.box(335, 110, 230, 130, 'cocotb', 'triggers, await', 'dut.signal.value')
    d.box(622, 110, 310, 130, 'HDL simulator', 'executes the RTL', 'schedules every event')
    d.path('M278 165H335'); d.path('M565 165H622')
    d.path('M335 205H278', GREEN, dashed=True); d.path('M622 205H565', GREEN, dashed=True)
    d.text(450, 90, 'edges, ReadOnly, values', size=18, anchor='middle')
    d.box(622, 290, 310, 100, 'RTL under test', 'SystemVerilog or VHDL')
    d.path('M777 240V290')
    d.box(28, 290, 537, 100, 'Evidence', 'Python assertions and a non-zero exit status;', 'an XML report alone is not enough')
    d.path('M335 240V265H190V290', GREEN, dashed=True)
    d.note(415, 'Calls between Python and the simulator have a cost: measure the actual workload before deciding which testbench language '
                'is faster. A passing test is evidence, not proof.')
    d.save()


def cocotb_vectors():
    d = Drawing('cocotb-directed-random-vectors', 'What directed and random vectors each find',
                'The accumulator test: 14 directed vectors, then 100 seeded random vectors • three seeded faults', 500)
    x0, w = 64, 832
    scale = w / 114
    d.rect(x0, 150, 14 * scale - 2, 48, BLUE)
    d.rect(x0 + 14 * scale, 150, 100 * scale, 48, GREEN)
    d.text(x0 + 7 * scale, 180, 'directed', size=18, anchor='middle')
    d.text(x0 + 64 * scale, 180, '100 pseudo-random vectors, seed 2026', size=18, anchor='middle')
    for value in (0, 14, 114):
        d.text(x0 + value * scale, 226, str(value), size=18, anchor='middle')
    d.text(28, 250, 'vector index', size=18)
    marks = [(11, 'cycle 11: overflow also at the exact maximum', 100), (17, 'cycle 17: overflow ignores Enable', 128)]
    for idx, text, y in marks:
        x = x0 + idx * scale + scale / 2
        d.path(f'M{x} 148V{y + 8}', ORANGE)
        d.text(x + 14, y + 6, text, size=18, color=ORANGE)
    d.rect(28, 290, 904, 100, INK)
    d.text(44, 322, 'Valid also requires a nonzero operand: no marker. Only Enable high with operand 0 differs,', size=18)
    d.text(44, 348, 'one value in 65,536, so a hundred random vectors almost never draw it.', size=18)
    d.text(44, 374, 'Three added directed vectors expose it.', size=18, bold=True)
    d.note(410, 'Random stimulus works best with a coverage plan, a reproducible seed and bounded execution; directed vectors cover the boundaries it will not reach.')
    d.save()


def accumulator_sequence():
    d = Drawing('verilator-accumulator-sequence', 'The accumulator contract on one directed sequence',
                'Reset and clear beat enable • valid marks an accepted addition • overflow is a one-cycle report', 520)
    cycles = [(1, 0, 0, 0), (1, 0, 1, 99), (0, 0, 1, 5), (0, 0, 1, 9), (0, 0, 0, 12345), (0, 1, 1, 100), (0, 0, 1, 60000), (0, 0, 1, 10000)]
    sums, valid, overflow = [0, 0, 5, 14, 14, 0, 60000, 4464], [0, 0, 1, 1, 0, 0, 1, 1], [0, 0, 0, 0, 0, 0, 0, 1]
    x0, w = 160, 96
    labels = ['reset', 'clear', 'enable', 'operand', 'sum', 'valid', 'overflow']
    d.text(28, 100, 'cycle', size=18, bold=True)
    for c in range(8):
        d.text(x0 + c * w + w / 2, 100, str(c), size=18, bold=True, anchor='middle')
    for r, label in enumerate(labels):
        y = 116 + r * 44 + (14 if r >= 4 else 0)
        d.text(28, y + 28, label, size=19, bold=r >= 4)
        for c in range(8):
            reset, clear, enable, operand = cycles[c]
            value = [reset, clear, enable, operand, sums[c], valid[c], overflow[c]][r]
            hot = (r == 4 and c in (1, 5)) or (r == 6 and c == 7 and value == 1)
            d.rect(x0 + c * w + 3, y, w - 6, 38, ORANGE if hot else BLUE if r < 4 else GREEN, fill='white')
            d.text(x0 + c * w + w / 2, y + 27, str(value), size=18, anchor='middle', bold=hot)
    d.text(x0 + 1 * w + w / 2, 460, 'reset beats enable', size=18, anchor='middle', color=ORANGE)
    d.text(x0 + 5 * w + w / 2, 460, 'clear beats enable', size=18, anchor='middle', color=ORANGE)
    d.text(x0 + 7 * w + w / 2 + 40, 484, '60000 + 10000 = 70000, modulo 65536 = 4464', size=18, anchor='end', color=ORANGE)
    d.height = 510
    d.save()


def first_divergence():
    d = Drawing('reference-first-divergence', 'A signature says it is wrong; the retirement log says where',
                'Recorded example: Spike reference against a faulty stand-in • retired instructions #22 to #25', 560)
    d.text(28, 100, 'Signature view', size=21, bold=True)
    d.rect(28, 112, 904, 50, ORANGE, dash=True)
    d.text(44, 144, 'faulty signature: differs at word 3, a stored word, with a long program in between', size=18)
    d.text(28, 205, 'Retirement view', size=21, bold=True)
    d.text(260, 235, 'reference (Spike)', size=19, bold=True, anchor='middle')
    d.text(700, 235, 'faulty stand-in', size=19, bold=True, anchor='middle')
    rows = [('#22', '0x8000001c', 'x5  <- 0x7', 'x5  <- 0x7', False), ('#23', '0x80000020', 'branch, no write', 'branch, no write', False),
            ('#24', '0x80000024', 'x5  <- 0xff..ff', 'x5  <- 0xff..ff', False), ('#25', '0x80000028', 'x12 <- 0x1', 'x12 <- 0x0', True)]
    for i, (n, pc, ref, dut, bad) in enumerate(rows):
        y = 250 + i * 54
        d.text(28, y + 31, n, size=19, bold=bad)
        d.text(88, y + 31, pc, size=18)
        d.rect(250, y, 330, 44, ORANGE if bad else BLUE, fill='white')
        d.text(415, y + 29, ref, size=18, anchor='middle')
        d.rect(600, y, 332, 44, ORANGE if bad else BLUE, fill='white', dash=bad)
        d.text(766, y + 29, dut, size=18, anchor='middle', bold=bad)
    d.text(28, 482, 'First divergence: encoding 0x0012a613, slti a2,t0,1. PC and encoding match;', size=18, color=ORANGE)
    d.text(28, 506, 'only the destination value differs.', size=18, color=ORANGE)
    d.note(525, 'Compare at architectural boundaries: a pipeline cycle cannot be matched against one ISS step, so log each instruction where it retires.')
    d.save()


FIGURES = [verification_ladder, plan_entry, assert_assume_cover, bmc_and_induction, cocotb_architecture,
           cocotb_vectors, accumulator_sequence, first_divergence]
