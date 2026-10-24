#!/usr/bin/env python3
"""Original conceptual SVGs for the FPGA and ASIC implementation chapters, in the common style.

They reuse `Drawing` from architecture.py unchanged. Every figure is conceptual: it explains an organization,
a flow or a worked example of the chapter and measures nothing. Driven by concepts.py.
"""
from architecture import Drawing, BLUE, GREEN, ORANGE, INK


def mapping_rows(d, y0, pitch, height, rows, widths, colors, arrows=True):
    """Rows of boxes joined left to right; every cell is a tuple of text lines."""
    xs, x = [], 28
    for w in widths:
        xs.append(x)
        x += w + 32
    for i, cells in enumerate(rows):
        y = y0 + i * pitch
        for k, lines in enumerate(cells):
            d.rect(xs[k], y, widths[k], height, colors[k])
            top = y + height / 2 - 13 * (len(lines) - 1) + 6
            for j, line in enumerate(lines):
                d.text(xs[k] + widths[k] / 2, top + 26 * j, line, size=18, anchor='middle', bold=(k == 0))
            if arrows and k:
                d.path(f'M{xs[k] - 32} {y + height / 2}H{xs[k]}')


def yosys_pipeline():
    d = Drawing('yosys-pass-pipeline', 'What Yosys does between RTL and the netlist for nextpnr',
                'Six phases of the open Nexys Video flow • the result is a technology-mapped JSON netlist', 540)
    boxes = [('1  Frontend', 'read_slang, parameters', 'include paths, top level'),
             ('2  Hierarchy, checks', 'hierarchy -top, check', 'undriven or multiply driven'),
             ('3  Process lowering', 'proc: muxes, flip-flops', 'a latch is an RTL defect'),
             ('4  Coarse-grain', 'constants, widths, dead', 'logic, FSM, memories'),
             ('5  Technology mapping', 'synth_xilinx -arch xc7', 'LUTs, carry, BRAM, DSP'),
             ('6  Export, report', 'write_json for nextpnr', 'stat: an estimate')]
    for i, (title, l1, l2) in enumerate(boxes):
        row, col = divmod(i, 3)
        x, y = 28 + col * 312, 105 + row * 170
        d.box(x, y, 290, 120, title, l1, l2, color=GREEN if i in (0, 5) else BLUE)
        if col < 2:
            d.path(f'M{x + 290} {y + 60}H{x + 312}')
    d.path('M787 225V250H173V275')
    d.note(430, 'Run a simulator or linter first: synthesis only checks that the design is synthesizable. The resource report is a design-review '
                'input, not timing sign-off, and tool upgrades can change both mapping and warnings, so pin versions.')
    d.save()


def yosys_inference():
    d = Drawing('yosys-rtl-intent-to-resource', 'Express the intent so the tool can infer the right resource',
                'RTL intent, the FPGA resource it should map to, and the review question', 560)
    d.text(28, 100, 'RTL intent', size=19, bold=True); d.text(360, 100, 'Expected resource', size=19, bold=True); d.text(652, 100, 'Review question', size=19, bold=True)
    rows = [(('Registered pipeline state',), ('Flip-flops, clock enable',), ('Reset on every bit?',)),
            (('Small combinational table',), ('LUT network',), ('Can the case be complete?',)),
            (('Wide add or compare',), ('LUTs plus carry chain',), ('Widths and signedness?',)),
            (('Array, synchronous access',), ('Block or distributed RAM',), ('Does the pattern match?',)),
            (('Multiply-accumulate',), ('DSP block or LUT logic',), ('Is -nodsp intentional?',)),
            (('Clock generation',), ('PLL or MMCM, buffers',), ('Supported and constrained?',))]
    mapping_rows(d, 112, 62, 50, rows, [300, 260, 280], [BLUE, GREEN, ORANGE])
    d.note(495, 'BRAM, DSP and clock resources are limited blocks: a design can synthesize and still fail later through resource use, '
                'an inferred RAM with the wrong read behavior, or a high-fanout reset.')
    d.save()


def fpga_reset_chain():
    d = Drawing('fpga-reset-release-chain', 'Reset release when Wally depends on DDR3',
                'The shared 40 MHz clock removes a bus crossing but creates a reset dependency', 640)
    steps = ['Board power and reset', 'Clock source; clock primitive locks', 'LiteDRAM reset released',
             'Service firmware: DDR init, leveling', 'init_done and not init_error', 'Wally reset released',
             'Wally boot ROM executes', 'UART or GPIO software milestone']
    for i, text in enumerate(steps):
        y = 95 + i * 66
        d.rect(28, y, 450, 44, GREEN if i in (5,) else BLUE)
        d.text(253, y + 29, text, size=19, bold=i == 5, anchor='middle')
        if i < 7:
            d.path(f'M253 {y + 44}V{y + 66}')
    d.rect(520, 160, 412, 90, ORANGE, dash=True)
    d.text(536, 193, 'A PLL lock alone is too early to', size=18, color=ORANGE)
    d.text(536, 219, 'release Wally when it needs DDR3.', size=18, color=ORANGE)
    d.rect(520, 380, 412, 116, INK)
    d.text(536, 413, 'A test that uses only internal ROM and', size=18); d.text(536, 439, 'RAM may use a documented mode that', size=18)
    d.text(536, 465, 'does not wait. Keep the two cases apart.', size=18)
    d.path('M478 205H520', ORANGE, dashed=True); d.path('M478 425H520', dashed=True)
    d.save()


def fpga_evidence_ladder():
    d = Drawing('fpga-evidence-ladder', 'Each FPGA claim needs its own evidence',
                'A bitstream that configures is a different milestone from a validated memory system', 560)
    d.text(28, 100, 'Claim', size=19, bold=True); d.text(412, 100, 'Evidence required', size=19, bold=True)
    rows = [(('RTL compiles',), ('Yosys log and a reproducible', 'source list')),
            (('Routes at 40 MHz',), ('nextpnr timing report for the', 'stated clocks')),
            (('Bitstream configures',), ('Programmer result and the board', 'DONE indication')),
            (('Wally runs from internal ROM',), ('UART or LED software milestone,', 'or a debug observation')),
            (('DDR controller initializes',), ('init_done, calibration logs and', 'a memory test')),
            (('Linux and DDR3 work',), ('Sustained hardware and software', 'tests, not only synthesis'))]
    mapping_rows(d, 112, 66, 56, rows, [340, 500], [BLUE, GREEN])
    d.save()


def nextpnr_triage():
    d = Drawing('nextpnr-critical-path-triage', 'Read the reported endpoints first, then pick the response',
                'Common critical-path patterns and the smallest change that addresses each', 640)
    d.text(28, 100, 'Critical-path pattern', size=19, bold=True); d.text(440, 100, 'RTL or architecture response', size=19, bold=True)
    rows = [(('Deep arithmetic plus compare',), ('Pipeline it, or use a dedicated', 'arithmetic resource')),
            (('Long priority chain',), ('Recode or balance the decision;', 'register an intermediate result')),
            (('High-fanout control or reset',), ('Reduce fanout, localize enables,', 'use intended distribution')),
            (('RAM output into complex decode',), ('Register the RAM output and', 'accept the added cycle')),
            (('Ready/valid loop across modules',), ('Break it with an elastic', 'register or pipeline stage')),
            (('Slow external interface path',), ('Add valid IO constraints; pipeline', 'if the protocol permits'))]
    mapping_rows(d, 112, 66, 56, rows, [380, 460], [BLUE, GREEN])
    d.note(520, 'Retiming changes latency and reset behavior, so it is an architectural change unless the interface contract tolerates it. '
                'After any change, rerun simulation and the formal checks before trusting the new timing report.')
    d.save()


def logical_effort():
    d = Drawing('vlsi-logical-effort-stages', 'The same load of 64 with one, three or four inverters',
                'Capacitances relative to the first inverter input • no branching • illustrative sizing', 560)
    plans = [('1 stage', [1, 64], 'stage effort 64'), ('3 stages', [1, 4, 16, 64], 'stage effort 4 each'),
             ('4 stages', [1, 2.83, 8, 22.6, 64], 'stage effort about 2.83, one more parasitic delay')]
    for row, (name, caps, comment) in enumerate(plans):
        y = 130 + row * 120
        d.text(28, y + 6, name, size=20, bold=True)
        n = len(caps) - 1
        x0, span = 210, 560
        step = span / n
        for k, cap in enumerate(caps):
            x = x0 + k * step
            d.parts.append(f'<circle cx="{x}" cy="{y}" r="6" fill="{BLUE}"/>')
            d.text(x, y + 38, f'{cap:g}', size=18, anchor='middle', bold=k in (0, n))
            if k < n:
                tx = x + step / 2 - 20
                d.parts.append(f'<path d="M{tx} {y - 18}L{tx + 36} {y}L{tx} {y + 18}Z" fill="white" stroke="{BLUE}" stroke-width="2"/>')
                d.parts.append(f'<circle cx="{tx + 40}" cy="{y}" r="4" fill="white" stroke="{BLUE}" stroke-width="2"/>')
                d.parts.append(f'<path d="M{x + 6} {y}H{tx}M{tx + 44} {y}H{x + step - 6}" stroke="{BLUE}" stroke-width="2"/>')
        d.text(x0, y + 66, comment, size=18)
    d.note(470, 'An odd number of inverters changes the logical polarity, and the optimum is not found by adding buffers: each stage adds '
                'parasitic delay. Check the result with characterized timing analysis.')
    d.save()


def timing_budget():
    d = Drawing('vlsi-timing-budget', 'A worked setup and hold budget for one register path',
                'Invented teaching values, not accumulator measurements • positive skew of 0.05 ns • not to scale', 560)
    d.text(28, 100, 'Setup at a period of 3.00 ns', size=21, bold=True)
    terms = [('clock-to-Q', '0.20', BLUE, '+'), ('data', '2.50', BLUE, '+'), ('setup', '0.15', BLUE, '+'),
             ('uncertainty', '0.10', ORANGE, '-'), ('skew', '0.05', GREEN, '')]
    for i, (name, value, color, op) in enumerate(terms):
        x = 28 + i * 168
        d.rect(x, 120, 132, 64, color)
        d.text(x + 66, 148, name, size=18, anchor='middle')
        d.text(x + 66, 172, value + ' ns', size=19, bold=True, anchor='middle')
        if i < 4:
            d.text(x + 150, 160, '+' if i < 3 else '-', size=24, bold=True, anchor='middle')
    d.rect(28, 210, 300, 56, BLUE)
    d.text(178, 245, 'required time 2.90 ns', size=20, bold=True, anchor='middle')
    d.text(350, 245, '<', size=26, bold=True)
    d.rect(380, 210, 250, 56, BLUE)
    d.text(505, 245, 'period T = 3.00 ns', size=20, bold=True, anchor='middle')
    d.text(655, 245, '=>', size=24, bold=True)
    d.rect(700, 210, 232, 56, GREEN, dash=True)
    d.text(816, 245, 'slack 0.10 ns', size=20, bold=True, anchor='middle', color=GREEN)
    d.text(28, 325, 'Hold, with the same skew', size=21, bold=True)
    d.rect(28, 345, 190, 64, BLUE); d.text(123, 373, 'min clock-to-Q', size=18, anchor='middle'); d.text(123, 397, '0.06 ns', size=19, bold=True, anchor='middle')
    d.text(235, 385, '+', size=24, bold=True)
    d.rect(258, 345, 190, 64, BLUE); d.text(353, 373, 'min data', size=18, anchor='middle'); d.text(353, 397, '0.04 ns', size=19, bold=True, anchor='middle')
    d.text(465, 385, '=', size=24, bold=True)
    d.rect(490, 345, 130, 64, BLUE); d.text(555, 385, '0.10 ns', size=19, bold=True, anchor='middle')
    d.text(633, 385, '<', size=26, bold=True)
    d.rect(660, 345, 272, 64, ORANGE)
    d.text(796, 373, 'hold 0.05 + U 0.03', size=18, anchor='middle'); d.text(796, 397, '+ skew 0.05 = 0.13 ns', size=18, bold=True, anchor='middle')
    d.rect(660, 425, 272, 44, ORANGE, dash=True)
    d.text(796, 454, 'violation 0.03 ns', size=20, bold=True, anchor='middle', color=ORANGE)
    d.note(490, 'A longer period does not change the hold inequality: repair it with inserted delay or a revised clock or data path. '
                'Real STA uses the required corners and the detailed clock paths.')
    d.save()


def evidence_package():
    d = Drawing('rtl-to-gdsii-evidence-package', 'A GDSII file is one part of the tapeout evidence',
                'The decision needs more than the layout • provider requirements come from the foundry or shuttle', 520)
    d.box(340, 215, 280, 100, 'Tapeout decision', 'a reproducible', 'evidence package', color=ORANGE)
    items = [(28, 100, 'GDSII layout', 'necessary, not sufficient'), (345, 100, 'Physical verification', 'clean DRC, LVS, antenna'),
             (662, 100, 'Timing and power', 'reviewed budget'), (28, 350, 'Package and pad ring', 'integration, ESD, bumps'),
             (632, 350, 'Foundry requirements', 'current submission rules')]
    for x, y, title, line in items:
        d.box(x, y, 300 if x == 632 else 270, 80, title, line, color=GREEN)
    d.path('M163 180V215H340'); d.path('M480 180V215'); d.path('M797 180V215H620')
    d.path('M163 350V315H340'); d.path('M782 350V315H620')
    d.note(450, 'An open PDK and an MPW announcement are a good start; current eligibility and acceptance come from the provider, '
                'and a local flow result is not a standing right to manufacture.')
    d.save()


def openroad_view_matrix():
    d = Drawing('openroad-views-matrix', 'Which view serves which activity in the implementation flow',
                'A dot marks the activity that mainly uses the view • mismatched views give runs that look fine', 600)
    cols = ['Simulate,', 'Timing', 'Place and', 'Verify and']
    cols2 = ['synthesize', 'analysis', 'route', 'hand off']
    x0, w = 430, 125
    for k in range(4):
        d.text(x0 + k * w + w / 2, 100, cols[k], size=18, bold=True, anchor='middle')
        d.text(x0 + k * w + w / 2, 122, cols2[k], size=18, bold=True, anchor='middle')
    rows = [('SystemVerilog', 'behavioral RTL', (1, 0, 0, 0)), ('Gate-level Verilog', 'technology cells and nets', (0, 1, 1, 1)),
            ('Liberty (.lib)', 'delay, power, limits', (1, 1, 0, 0)), ('Technology LEF', 'layers, vias, sites', (0, 0, 1, 0)),
            ('Cell LEF', 'outlines, pins, blockages', (0, 0, 1, 0)), ('DEF', 'floorplan, instances, routes', (0, 0, 1, 0)),
            ('SDC', 'clocks, I/O delays, exceptions', (0, 1, 0, 0)), ('SPEF', 'extracted R and C', (0, 1, 0, 0)),
            ('GDSII', 'exact polygons', (0, 0, 0, 1))]
    for i, (name, what, marks) in enumerate(rows):
        y = 138 + i * 48
        d.rect(28, y, 904, 42, BLUE if i % 2 == 0 else GREEN, fill='white')
        d.text(40, y + 27, name, size=19, bold=True)
        d.text(240, y + 27, what, size=18)
        for k, mark in enumerate(marks):
            if mark:
                d.parts.append(f'<circle cx="{x0 + k * w + w / 2}" cy="{y + 21}" r="9" fill="{BLUE}"/>')
    d.note(580, 'Liberty tells the timer how fast a cell is; LEF tells the placer how wide it is and where its pins are. Freeze the PDK and library revision together.')
    d.save()


def openroad_triage():
    d = Drawing('openroad-failure-triage', 'Find the first stage where the design becomes invalid',
                'Symptom, first check and the stage that usually owns the repair', 620)
    stages = [('Read and link', ['cells cannot be linked: check_setup, synthesis log', 'no clock or zero sinks: report_clocks, SDC port names'], BLUE),
              ('Floorplan, place', ['illegal cells: check_placement, rows and site', 'routing overflow: congestion report, add whitespace'], BLUE),
              ('Clock tree', ['hold failure after CTS: minimum-delay report, hold repair'], GREEN),
              ('Route, extract', ['setup failure after route: compare pre- and post-route paths', 'antenna or DRC markers: detailed-route report'], GREEN),
              ('Hand-off', ['great reports but no fabrication path: tapeout checklist'], ORANGE)]
    y = 100
    for name, lines, color in stages:
        height = 26 + 26 * len(lines) + 12
        d.rect(28, y, 200, height, color)
        d.text(128, y + height / 2 + 6, name, size=19, bold=True, anchor='middle')
        d.rect(250, y, 682, height, color, fill='white')
        for j, line in enumerate(lines):
            d.text(266, y + 34 + 26 * j, line, size=18)
        y += height + 14
    d.note(y + 4, 'Modify one controlled input, keep the reports and compare with the baseline. A failed endpoint after routing may call for RTL, '
                  'a constraint, a larger die or a different pin location.')
    d.save()


def librelane_layers():
    d = Drawing('librelane-config-layers', 'How LibreLane resolves one configuration',
                'Each layer overrides the one below it • the result is fixed for the run', 520)
    layers = [('Command-line flags', 'temporary overrides', ORANGE), ('Design file', 'clock, sources, utilization, pins', GREEN),
              ('PDK and cell library', 'technology-specific values', BLUE), ('Built-in flow', 'defaults', BLUE)]
    for i, (title, line, color) in enumerate(layers):
        y = 100 + i * 80
        d.box(28, y, 400, 66, title, line, color=color)
        if i < 3:
            d.path(f'M228 {y + 80}V{y + 66}')
    d.box(560, 180, 372, 110, 'resolved.json', 'validated and immutable', 'for the run', color=GREEN)
    for y in (133, 213, 293, 373):
        d.path(f'M428 {y}H470', arrow=False)
    d.path('M470 133V373', arrow=False)
    d.path('M470 235H560')
    d.rect(560, 320, 372, 100, INK)
    d.text(576, 352, 'Write design intent only.', size=18, bold=True)
    d.text(576, 378, 'Inspect resolved.json for what', size=18)
    d.text(576, 404, 'you did not write yourself.', size=18)
    d.note(440, 'A successful SKY130 configuration does not transfer unchanged to another process: re-evaluate the clock target, utilization, '
                'I/O requirements, macro views, power intent and sign-off criteria.')
    d.save()


def librelane_evidence():
    d = Drawing('librelane-run-evidence', 'A run is a chain of states, and each step leaves evidence',
                'Find the earliest invalid step, not the last line of the console', 580)
    steps = [('Synthesis', 'netlist'), ('Floorplan', 'geometry'), ('Placement', 'placed cells'), ('Routing', 'routes'), ('Sign-off', 'GDSII')]
    for i, (name, state) in enumerate(steps):
        x = 28 + i * 184
        d.box(x, 100, 168, 80, name, 'adds ' + state, color=GREEN if i == 4 else BLUE)
        if i < 4:
            d.path(f'M{x + 168} 140H{x + 184}')
    d.text(28, 225, 'Evidence kept for every run tag', size=21, bold=True)
    items = [('resolved.json', 'which library and clock'), ('Per-step log', 'first warning or error'), ('Per-step report', 'timing, area, DRC, LVS'),
             ('State or checkpoint', 'reopen the design'), ('Metrics', 'compare runs, CI gates'), ('Final views', 'DEF, GDSII, netlist, SPEF')]
    for i, (name, line) in enumerate(items):
        x, y = 28 + (i % 3) * 306, 245 + (i // 3) * 96
        d.box(x, y, 290, 80, name, line)
    d.note(450, 'Use a unique run tag for every experiment, never reuse one after changing RTL or configuration, and keep generated files out '
                'of the source repository: commit the inputs, a short results summary and the scripts.')
    d.save()


def release_candidate_layout():
    d = Drawing('physical-release-candidate-layout', 'A suggested layout for the tapeout evidence',
                'Not a universal foundry specification • the provider defines its own deliverables', 580)
    rows = [('manifest.json', 'identities, versions, corners, check status, licenses'), ('design/', 'final layout and netlists'),
            ('constraints/', 'functional and test-mode timing budgets'), ('reports/', 'STA, DRC, LVS, antenna, density, PDN, DFT'),
            ('integration/', 'pad and package mapping, macro inventory'), ('test/', 'patterns, protocol, bring-up instructions'),
            ('checksums.sha256', 'integrity of every file above')]
    for i, (name, text) in enumerate(rows):
        y = 100 + i * 58
        d.rect(28, y, 260, 48, GREEN if i in (0, 6) else BLUE)
        d.text(158, y + 31, name, size=19, bold=True, anchor='middle')
        d.rect(310, y, 622, 48, BLUE if i not in (0, 6) else GREEN, fill='white')
        d.text(326, y + 31, text, size=18)
    d.note(512, 'Keep unresolved items visible, and make the test patterns and firmware correspond to the same design identity. '
                'Accepting a waiver belongs to the project and the provider.')
    d.save()


FIGURES = [yosys_pipeline, yosys_inference, fpga_reset_chain, fpga_evidence_ladder, nextpnr_triage, logical_effort,
           timing_budget, evidence_package, openroad_view_matrix, openroad_triage, librelane_layers, librelane_evidence,
           release_candidate_layout]
