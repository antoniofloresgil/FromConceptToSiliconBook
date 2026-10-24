#!/usr/bin/env python3
"""Original conceptual SVGs for the SoC-architecture chapters (buses, memories, boot), in the common style.

They reuse `Drawing` from architecture.py unchanged. Every figure is conceptual: it explains an organization,
a protocol or a worked example of the chapter and measures nothing. Driven by concepts.py.
"""
from architecture import Drawing, BLUE, GREEN, ORANGE, INK


def levels(d, y, values, x0, step, label):
    """A digital waveform row; None marks a value that does not matter."""
    d.text(28, y + 5, label, size=20)
    for i, value in enumerate(values):
        x = x0 + i * step
        if value is None:
            d.parts.append(f'<path d="M{x + 6} {y - 1}H{x + step - 6}" stroke="{INK}" stroke-width="1.2" stroke-dasharray="3 4"/>')
            continue
        yy = y - 14 if value else y + 12
        d.parts.append(f'<path d="M{x} {yy}H{x + step}" fill="none" stroke="{BLUE}" stroke-width="2.5"/>')
        if i and values[i - 1] is not None and values[i - 1] != value:
            d.parts.append(f'<path d="M{x} {y - 14}V{y + 12}" stroke="{BLUE}" stroke-width="2.5"/>')


def core_to_uncore():
    d = Drawing('buses-core-to-uncore', 'From core to uncore: a request path and an event path',
                'Solid blue = request and response • dashed orange = interrupt request, not a bus transaction', 500)
    d.box(28, 100, 190, 80, 'IFU', 'instruction fetch')
    d.box(28, 200, 190, 80, 'LSU', 'loads and stores')
    d.box(290, 100, 190, 180, 'Interconnect', 'decode the address', 'arbitrate', 'route responses', kind='interconnect')
    d.path('M218 140H252V160H290'); d.path('M218 240H252V220H290')
    d.box(550, 100, 180, 80, 'Memory', 'RAM or boot ROM', kind='memory')
    d.box(550, 200, 180, 80, 'Bridge', 'to the register bus')
    d.path('M480 140H550'); d.path('M480 240H550')
    d.box(790, 200, 142, 80, 'Peripheral', 'registers', kind='peripheral')
    d.path('M730 240H790')
    d.box(550, 330, 180, 70, 'Interrupt', 'controller')
    d.box(28, 330, 250, 70, 'CPU trap logic', 'pending, enable, entry')
    d.path('M861 280V365H730', ORANGE, dashed=True)
    d.path('M550 365H278', ORANGE, dashed=True)
    d.text(846, 316, 'event from the device', size=18, color=ORANGE, anchor='end')
    d.text(414, 352, 'interrupt request', size=18, color=ORANGE, anchor='middle')
    d.note(425, 'Software uses the bus to configure interrupt generation and to service a source. The request '
                'itself travels on the event path, so a register read can happen with interrupts disabled.')
    d.save()


def apb_ahb_phases():
    d = Drawing('buses-apb-ahb-phases', 'APB and AHB: how consecutive transfers use their phases',
                'Each column is the interval before its numbered rising edge • worked examples of the chapter', 700)
    x0, step = 190, 148
    d.text(28, 100, 'APB: one transfer with two wait cycles', size=22, bold=True)
    for i in range(5):
        d.path(f'M{x0 + (i + 1) * step} 120V330', arrow=False)
        d.text(x0 + i * step + step / 2, 124, str(i + 1), size=18, anchor='middle')
    phases = ['Setup', 'Access, wait', 'Access, wait', 'Access, ready', 'Idle or Setup']
    for i, phase in enumerate(phases):
        d.text(x0 + i * step + step / 2, 150, phase, size=18, anchor='middle')
    levels(d, 200, [1, 1, 1, 1, 0], x0, step, 'PSEL')
    levels(d, 255, [0, 1, 1, 1, 0], x0, step, 'PENABLE')
    levels(d, 310, [None, 0, 0, 1, None], x0, step, 'PREADY')
    d.parts.append(f'<circle cx="{x0 + 4 * step}" cy="326" r="8" fill="{GREEN}"/>')
    d.text(x0 + 3 * step + step / 2, 352, 'one access completes', size=18, anchor='middle', color=GREEN)
    d.text(28, 400, 'AHB: the next address overlaps the previous data phase', size=22, bold=True)
    for i in range(5):
        d.path(f'M{x0 + (i + 1) * step} 420V610', arrow=False)
        d.text(x0 + i * step + step / 2, 424, str(i + 1), size=18, anchor='middle')
    d.text(28, 482, 'address', size=20)
    d.text(28, 542, 'data', size=20)
    address = [('A', BLUE), ('B', GREEN), ('B held', GREEN), ('C', ORANGE), ('idle', None)]
    data = [('none', None), ('A waits', BLUE), ('A done', BLUE), ('B done', GREEN), ('C done', ORANGE)]
    for i, (text, color) in enumerate(address):
        if color:
            d.rect(x0 + i * step + 6, 450, step - 12, 44, color, fill='white')
        d.text(x0 + i * step + step / 2, 479, text, size=18, anchor='middle')
    for i, (text, color) in enumerate(data):
        if color:
            d.rect(x0 + i * step + 6, 510, step - 12, 44, color, fill='white')
        d.text(x0 + i * step + step / 2, 539, text, size=18, anchor='middle')
    levels(d, 590, [1, 0, 1, 1, 1], x0, step, 'HREADY')
    d.note(630, 'APB never overlaps transfers. AHB overlaps address and data phases, but a stalled data phase still '
                'holds back every later address; AXI removes that coupling with independent channels.')
    d.save()


def interrupt_gates():
    d = Drawing('buses-interrupt-gates', 'Device event to trap: every gate can hold the request',
                'Machine-mode path of the chapter • cause codes 11, 7 and 3 • one hart, nested interrupts off', 540)
    d.box(28, 100, 214, 80, 'GPIO or UART', 'pending, enable')
    d.box(28, 220, 214, 80, 'CLINT timer', 'mtime >= mtimecmp')
    d.box(28, 340, 214, 80, 'CLINT msip', 'bit 0 of msip')
    d.box(300, 100, 200, 80, 'PLIC', 'priority > threshold', 'context enable', color=GREEN)
    d.path('M242 140H300')
    d.box(560, 100, 170, 80, 'mip.MEIP', 'external, cause 11')
    d.box(560, 220, 170, 80, 'mip.MTIP', 'timer, cause 7')
    d.box(560, 340, 170, 80, 'mip.MSIP', 'software, cause 3')
    d.path('M500 140H560'); d.path('M242 260H560'); d.path('M242 380H560')
    d.box(780, 195, 152, 130, 'mie bit', 'AND', 'mstatus.MIE', color=ORANGE)
    d.path('M730 140H755V240H780'); d.path('M730 260H780'); d.path('M730 380H755V290H780')
    d.path('M856 325V360', ORANGE)
    d.text(856, 388, 'trap taken:', size=18, bold=True, anchor='middle', color=ORANGE)
    d.text(856, 412, 'mcause = flag', size=18, anchor='middle', color=ORANGE)
    d.text(856, 436, '+ cause code', size=18, anchor='middle', color=ORANGE)
    d.note(460, 'Disabling a gate does not clear the pending state behind it. PLIC priority and the CPU\'s class order '
                '(timer, software, external) are different arbitration layers.')
    d.save()


def plic_claim_sequence():
    d = Drawing('buses-plic-claim-sequence', 'PLIC service: claim, service, order, complete',
                'Teaching context 0 (machine mode) • claim and completion share the register at offset 0x200004', 600)
    lanes = [(150, 'Device'), (480, 'PLIC'), (810, 'Hart software')]
    for x, name in lanes:
        d.box(x - 85, 90, 170, 50, name)
        d.path(f'M{x} 140V505', arrow=False)
    steps = [(185, 150, 480, '1  source asserts (level)', BLUE, False),
             (235, 480, 810, '2  external interrupt, then trap', ORANGE, True),
             (285, 810, 480, '3  read claim', BLUE, False),
             (335, 480, 810, '4  returns the source ID', BLUE, False),
             (395, 810, 150, '5  service, clear the condition', BLUE, False),
             (445, 810, 480, '6  fence, then write the ID', GREEN, False)]
    for y, a, b, label, color, dashed in steps:
        d.path(f'M{a} {y}H{b}', color, dashed=dashed)
        d.text((a + b) / 2 if a != 810 or b != 150 else 330, y - 9, label, size=18, anchor='middle', color=color if color != BLUE else INK)
    d.text(496, 360, 'claim clears the pending bit', size=18, color=GREEN)
    d.text(496, 474, 'if the source is still high,', size=18, color=ORANGE)
    d.text(496, 498, 'it can interrupt again', size=18, color=ORANGE)
    d.note(525, 'Claim has a side effect and is not a read of the pending bitmap; completion does not remove the '
                'device\'s own condition. ID 0 means no claimed interrupt.')
    d.save()


def trap_entry_return():
    d = Drawing('buses-trap-entry-return', 'A trap is not a function call',
                'Machine-mode entry and return with direct mtvec • hardware saves state, software saves registers', 450)
    d.box(28, 100, 290, 235, 'Hardware at entry', 'mepc: resume address', 'mcause: flag + code', 'MPIE <- MIE', 'MIE <- 0', 'MPP <- privilege', 'PC <- mtvec base', color=ORANGE)
    d.box(335, 100, 290, 235, 'Handler software', 'save what it clobbers', 'read mcause, test flag', 'case 3, 7 or 11', 'service the source', 'restore registers')
    d.box(642, 100, 290, 235, 'mret, in hardware', 'MIE <- MPIE', 'privilege <- MPP', 'PC <- mepc', color=ORANGE)
    d.path('M318 215H335'); d.path('M625 215H642')
    d.note(360, 'Hardware does not save the integer registers, and ret is not mret. For an interrupt, mepc is not '
                'advanced; advancing it by four is specific to exceptions.')
    d.save()


def memory_hierarchy_paths():
    d = Drawing('memories-hierarchy-paths', 'Three access paths from the core',
                'Alternatives, not a mandatory sequence • check the selected configuration for the levels it has', 500)
    d.box(28, 120, 150, 230, 'CPU', 'registers', kind='cpu')
    boxes = [(100, 'IROM or L1 I-cache', 'instruction path', 'cache'), (205, 'DTIM or L1 D-cache', 'load/store path', 'cache'),
             (310, 'Uncached path', 'device access', None)]
    for y, title, line, kind in boxes:
        d.box(250, y, 280, 80, title, line, kind=kind)
        d.path(f'M178 235H214V{y + 40}H250')
    d.box(590, 100, 140, 290, 'Bus', 'selects a', 'target', kind='interconnect')
    for y in (140, 245, 350):
        d.path(f'M530 {y}H590')
    d.box(790, 130, 142, 90, 'Main', 'memory', kind='memory')
    d.box(790, 280, 142, 90, 'Peripheral', 'registers', kind='peripheral')
    d.path('M730 175H790'); d.path('M730 325H790')
    d.note(410, 'A tightly integrated memory is directly addressed storage with predictable timing; a cache holds '
                'automatically selected copies. Device registers use the uncached path on purpose.')
    d.save()


def cache_address_lookup():
    d = Drawing('memories-cache-address-lookup', 'Address fields and lookup of the teaching cache',
                '4 KiB, two ways, 64-byte lines, 32-bit physical address • S = 32 sets', 600)
    x0, bit = 64, 26
    fields = [('tag [31:11]  21 bits', 21, BLUE), ('set [10:6]', 5, GREEN), ('word [5:2]', 4, ORANGE), ('[1:0]', 2, ORANGE)]
    x = x0
    for label, bits, color in fields:
        d.rect(x + 1, 100, bits * bit - 2, 48, color)
        d.text(x + bits * bit / 2, 131, label, size=18, anchor='middle')
        x += bits * bit
    d.text(x0 + 26 * bit + 3 * bit + 20, 172, 'byte offset [5:0]', size=18, anchor='middle')
    d.rect(48, 205, 568, 130, INK, dash=True)
    d.box(64, 215, 250, 100, 'Way 0, row = set', 'valid, dirty, tag', '64-byte line')
    d.box(350, 215, 250, 100, 'Way 1, row = set', 'valid, dirty, tag', '64-byte line')
    d.path('M675 148V190H480V215', GREEN)
    d.path('M480 190H189V215', GREEN)
    d.text(330, 180, 'set picks one row per way', size=18, color=GREEN)
    d.box(64, 355, 250, 56, 'tag == and valid?')
    d.box(350, 355, 250, 56, 'tag == and valid?')
    d.path('M189 315V355'); d.path('M475 315V355')
    d.box(640, 355, 292, 56, 'hit vector', 'one-hot or zero')
    d.path('M189 411V435H786V411', arrow=False); d.path('M475 411V435', arrow=False)
    d.path('M786 435V411')
    d.box(640, 215, 292, 100, 'data mux', 'both ways in, hit vector', 'selects word and lane')
    d.path('M616 265H640')
    d.path('M786 355V315')
    d.rect(28, 470, 904, 120)
    d.text(44, 498, 'Three addresses, one set', size=19, bold=True)
    rows = [('0x80000000', 'tag 0x100000'), ('0x80000800', 'tag 0x100001'), ('0x80001000', 'tag 0x100002')]
    for i, (address, tag) in enumerate(rows):
        d.text(44 + i * 300, 528, address + ' -> set 0', size=18)
        d.text(44 + i * 300, 552, tag, size=18)
    d.text(44, 578, 'Two coexist; cycling through all three evicts one each time (conflict misses).', size=18)
    d.height = 610
    d.save()


def plru_tree():
    d = Drawing('memories-plru-tree', 'Tree pseudo-LRU for four ways',
                'Bits are root / left / right • each bit points toward the subtree chosen for eviction • all ways valid', 470)
    snapshots = [('Initial', '000', 0), ('Access way 0', '110', 2), ('Access way 2', '011', 1),
                 ('Access way 1', '101', 3), ('Access way 3', '000', 0)]
    for k, (label, bits, victim) in enumerate(snapshots):
        cx = 112 + k * 184
        d.text(cx, 100, label, size=18, bold=True, anchor='middle')
        root, left, right = (int(b) for b in bits)
        nodes = {'r': (cx, 140), 'l': (cx - 44, 205), 'rr': (cx + 44, 205)}
        leaves = [(cx - 66, 285), (cx - 22, 285), (cx + 22, 285), (cx + 66, 285)]
        chosen = {'l': root == 0, 'rr': root == 1}
        for child in ('l', 'rr'):
            hot = chosen[child]
            d.parts.append(f'<path d="M{nodes["r"][0]} {nodes["r"][1] + 14}L{nodes[child][0]} {nodes[child][1] - 14}" '
                           f'stroke="{ORANGE if hot else INK}" stroke-width="{4 if hot else 1.2}" fill="none"/>')
        for parent, bit, first in (('l', left, 0), ('rr', right, 2)):
            px, py = nodes[parent]
            for side in (0, 1):
                hot = (bit == side) and chosen[parent]
                lx, ly = leaves[first + side]
                d.parts.append(f'<path d="M{px} {py + 14}L{lx} {ly - 14}" stroke="{ORANGE if hot else INK}" '
                               f'stroke-width="{4 if hot else 1.2}" fill="none"/>')
        for (name, (nx, ny)), bit in zip(nodes.items(), (root, left, right)):
            d.parts.append(f'<circle cx="{nx}" cy="{ny}" r="15" fill="white" stroke="{BLUE}" stroke-width="2"/>')
            d.text(nx, ny + 6, str(bit), size=18, bold=True, anchor='middle')
        for way, (lx, ly) in enumerate(leaves):
            hot = way == victim
            d.parts.append(f'<rect x="{lx - 17}" y="{ly - 14}" width="34" height="30" rx="5" fill="{"#fff3e9" if hot else "white"}" '
                           f'stroke="{ORANGE if hot else BLUE}" stroke-width="{4 if hot else 2}"/>')
            d.text(lx, ly + 7, str(way), size=18, bold=hot, anchor='middle')
        d.text(cx, 335, bits, size=20, bold=True, anchor='middle')
        d.text(cx, 362, f'victim: way {victim}', size=18, anchor='middle', color=ORANGE)
    d.note(390, 'A hit flips the bits on its path to point away from the accessed way. The tree stores an approximation, '
                'not the whole history, and needs forwarding when an update overlaps a lookup.')
    d.save()


def amat_breakdown():
    d = Drawing('memories-amat-breakdown', 'Where the cycles go: three worked estimates',
                'Model arithmetic of the chapter, not measurements • bar length is proportional to cycles', 480)
    scale, x0 = 380, 28
    bars = [('AMAT, one level', [('hit', 1.0, BLUE), ('misses', 1.0, ORANGE)], 'total 2.0 = 1 + 0.05 x 20'),
            ('AMAT, two levels', [('L1', 1.0, BLUE), ('L2', 0.3, GREEN), ('mem', 0.5, ORANGE)], 'total 1.8 = 1 + 0.05 x (6 + 0.2 x 50)'),
            ('CPI estimate', [('base', 1.1, BLUE), ('I', 0.25, GREEN), ('D', 0.3, ORANGE)], 'total 1.65 = 1.1 + 0.01 x 25 + 0.3 x 0.04 x 25')]
    for row, (title, segments, formula) in enumerate(bars):
        y = 100 + row * 110
        d.text(x0, y - 8, title, size=20, bold=True)
        x = x0
        for label, value, color in segments:
            width = value * scale
            d.rect(x, y, width - 4, 46, color)
            d.text(x + (width - 4) / 2, y + 30, f'{label} {value:g}', size=18, anchor='middle')
            x += width
        d.text(x0, y + 72, formula, size=18)
    d.text(28, 440, 'L2 = 0.05 x 6 • mem = 0.05 x 0.2 x 50 • I = instruction misses • D = data misses', size=18)
    d.save()


def byte_lanes():
    d = Drawing('memories-byte-lane-mask', 'A masked write changes lanes, not the whole word',
                'Little-endian 32-bit word • the mask is a lane enable, not data', 430)
    x0, w = 190, 140
    for lane in range(4):
        d.text(x0 + lane * w + w / 2, 100, f'byte +{lane}', size=18, anchor='middle', bold=True)
    rows = [('stored word', ['44', '33', '22', '11'], BLUE, '0x11223344'),
            ('write data', ['DD', 'CC', 'BB', 'AA'], GREEN, '0xAABBCCDD'),
            ('mask 0101', ['1', '0', '1', '0'], ORANGE, 'lanes 0 and 2'),
            ('result', ['DD', '33', 'BB', '11'], BLUE, '0x11BB33DD')]
    for r, (label, cells, color, word) in enumerate(rows):
        y = 120 + r * 70
        d.text(28, y + 33, label, size=20)
        for lane, cell in enumerate(cells):
            changed = r == 3 and lane in (0, 2)
            enabled = r == 2 and cell == '1'
            d.rect(x0 + lane * w + 6, y, w - 12, 48, ORANGE if changed or enabled else color, fill='white', dash=r == 2 and cell == '0')
            d.text(x0 + lane * w + w / 2, y + 32, cell, size=22, bold=changed, anchor='middle')
        d.text(x0 + 4 * w + 12, y + 32, word, size=18)
    d.note(400, 'Lanes 0 and 2 take the write data; lanes 1 and 3 keep the stored bytes, so the word becomes 0x11BB33DD.')
    d.save()


def boot_memory_plan():
    d = Drawing('boot-memory-plan', 'One RAM, several owners that must stay disjoint',
                'Placement of the checked QEMU practice, not to scale • other SoCs choose other addresses', 540)
    d.text(28, 105, 'DRAM base', size=18)
    d.text(28, 125, '0x80000000', size=18, bold=True)
    d.box(200, 90, 420, 90, 'OpenSBI firmware', 'resident in M-mode', 'keeps servicing SBI calls', color=ORANGE)
    d.text(28, 235, 'payload', size=18)
    d.text(28, 255, '0x80200000', size=18, bold=True)
    d.rect(200, 210, 420, 190, BLUE)
    d.text(410, 238, 'Supervisor payload window, 1 MiB', size=20, bold=True, anchor='middle')
    for i, name in enumerate(['text, rodata', 'data', 'BSS (cleared at startup)', 'stack, 16 KiB']):
        d.rect(220, 252 + i * 34, 380, 30, GREEN if name.startswith('stack') else BLUE, fill='white')
        d.text(410, 274 + i * 34, name, size=18, anchor='middle')
    d.box(680, 90, 252, 90, 'DTB', 'placement recorded', 'in the plan', color=GREEN)
    d.box(680, 210, 252, 90, 'initramfs, buffers', 'DMA and kernel data', 'in later experiments', color=GREEN)
    d.text(680, 335, 'Their addresses depend on the', size=18)
    d.text(680, 359, 'experiment and must not overlap', size=18)
    d.text(680, 383, 'the regions at the left.', size=18)
    d.note(425, 'A hardware region says where bytes can live, not who owns them. Check the combined placement plan, '
                'including alignment and temporary buffers, because a link map cannot see a separately loaded DTB.')
    d.save()


def sbi_privilege_boundaries():
    d = Drawing('boot-sbi-boundaries', 'Two different ecalls, two different contracts',
                'An application system call and an SBI call both use ecall but ask different layers', 520)
    d.box(28, 110, 250, 100, 'Application', 'U-mode', color=GREEN)
    d.box(355, 110, 250, 100, 'Kernel', 'S-mode')
    d.box(682, 110, 250, 100, 'OpenSBI', 'M-mode, resident', color=ORANGE)
    d.path('M278 140H355'); d.path('M605 140H682')
    d.path('M355 185H278', GREEN, dashed=True); d.path('M682 185H605', GREEN, dashed=True)
    d.text(316, 128, 'ecall', size=18, anchor='middle'); d.text(643, 128, 'ecall', size=18, anchor='middle')
    d.text(28, 242, 'operating-system ABI', size=18, bold=True); d.text(355, 242, 'SBI ABI', size=18, bold=True)
    d.rect(355, 258, 577, 160)
    d.text(372, 288, 'a7 = extension ID, a6 = function ID', size=18)
    d.text(372, 314, 'a0 to a5 = arguments', size=18)
    d.text(372, 340, 'returns a0 = error code, a1 = value', size=18)
    d.text(372, 366, '(the value is not meaningful on an error)', size=18)
    d.text(372, 400, 'BASE 0x10 • TIME • IPI • RFENCE • HSM • SRST • DBCN', size=18)
    d.rect(28, 258, 305, 160)
    d.text(44, 288, 'The kernel serves user', size=18); d.text(44, 314, 'requests; arbitrary user', size=18)
    d.text(44, 340, 'requests are not forwarded', size=18); d.text(44, 366, 'into firmware.', size=18)
    d.note(440, 'Firmware entry uses a0 = hart ID, a1 = DTB and, for dynamic firmware, a2 = dynamic information. '
                'This is a different convention from the one used by later SBI calls.')
    d.save()


def firmware_packaging():
    d = Drawing('boot-firmware-packaging', 'Where OpenSBI learns what to run next',
                'Three packaging styles • the next stage must exist in memory before firmware jumps to it', 520)
    rows = [(100, 'FW_DYNAMIC', 'a loader tells firmware', 'at run time (pointer in a2)', 'Loader'),
            (230, 'FW_JUMP', 'next-stage address fixed', 'at build time', 'Another agent'),
            (360, 'FW_PAYLOAD', 'next stage embedded', 'inside the firmware image', 'Build step')]
    for y, name, line1, line2, source in rows:
        d.box(28, y, 190, 90, source, 'provides it', color=GREEN)
        d.box(330, y, 270, 90, name, line1, line2)
        d.box(720, y, 212, 90, 'Next stage', 'usually S-mode')
        d.path(f'M218 {y + 45}H330'); d.path(f'M600 {y + 45}H720')
    d.note(480, 'Choose one on purpose: a real Wally boot ROM has to provide the services QEMU supplies here, or adopt '
                'a different packaging style. Placement and size limits remain the integrator\'s responsibility.')
    d.save()


def slots(d, x, y, count, filled, color, size=44):
    """A row of FIFO slots; the first `filled` slots hold an item."""
    for i in range(count):
        d.rect(x + i * (size + 4), y, size, size, color, fill=None if i < filled else 'white', dash=i >= filled)
        if i < filled:
            d.text(x + i * (size + 4) + size / 2, y + size / 2 + 6, '■', size=18, anchor='middle')


def queued_capacity():
    d = Drawing('pipelines-queued-capacity', 'Queues around a service: how much work is outstanding',
                'Depth D = 2 on both sides • a congested snapshot after the consumer pauses', 520)
    d.box(28, 130, 140, 100, 'Client', 'source, sink')
    d.box(210, 130, 200, 100, 'Request FIFO', 'depth D')
    d.box(450, 130, 190, 100, 'Service', 'one operation', 'or one result')
    d.box(680, 130, 252, 100, 'Response FIFO', 'depth D')
    d.path('M168 160H210'); d.path('M410 180H450'); d.path('M640 180H680')
    d.path('M806 130V104H98V130', GREEN)
    d.text(450, 96, 'responses return to the client', size=18, anchor='middle', color=GREEN)
    d.text(310, 268, 'items held: 2', size=18, anchor='middle')
    d.text(545, 268, 'items held: 1', size=18, anchor='middle')
    d.text(806, 268, 'items held: 2', size=18, anchor='middle')
    d.rect(250, 290, 120, 52, BLUE); d.text(310, 324, '■   ■', size=22, anchor='middle')
    d.rect(487, 290, 116, 52, BLUE); d.text(545, 324, '■', size=22, anchor='middle')
    d.rect(746, 290, 120, 52, BLUE); d.text(806, 324, '■   ■', size=22, anchor='middle')
    d.path('M250 372H866', arrow=False)
    d.text(310, 398, 'D', size=20, bold=True, anchor='middle'); d.text(545, 398, '+ 1', size=20, bold=True, anchor='middle'); d.text(806, 398, '+ D', size=20, bold=True, anchor='middle')
    d.text(560, 430, 'at most 2D + 1 = 5 outstanding items', size=20, bold=True, anchor='middle')
    d.note(450, 'The source keeps any request that was not accepted; nothing is deleted to make room. '
                'Space on the request side says nothing about the capacity to execute another operation.')
    d.save()


def skid_buffer():
    d = Drawing('pipelines-skid-buffer', 'A skid buffer absorbs the item sent during the stop delay',
                'Conceptual two-entry buffer • four snapshots • the source sees ready one cycle late', 500)
    snaps = [('1  flowing', 'A', '', 'ready high', 'A is the output item'),
             ('2  sink stops', 'A', 'B', 'ready low,', 'seen one cycle late'),
             ('3  source holds', 'A', 'B', 'ready low', 'source keeps C'),
             ('4  sink resumes', 'B', '', 'ready high', 'A left, B moved up')]
    for k, (title, main, skid, ready, comment) in enumerate(snaps):
        x = 28 + k * 228
        d.text(x + 100, 100, title, size=19, bold=True, anchor='middle')
        d.rect(x, 120, 200, 56, BLUE, fill='white')
        d.text(x + 100, 156, 'output  ' + main if main else 'output', size=20, anchor='middle')
        d.rect(x, 190, 200, 56, GREEN, fill='white', dash=not skid)
        d.text(x + 100, 226, 'skid  ' + skid if skid else 'skid  empty', size=20, anchor='middle')
        d.text(x + 100, 285, ready, size=18, anchor='middle', color=ORANGE if 'low' in ready else GREEN)
        d.text(x + 100, 310, comment, size=18, anchor='middle')
    d.rect(28, 340, 904, 56)
    d.text(44, 375, 'Link accepts R items per cycle and reports a stop after B cycles: reserve at least R x B entries.', size=18)
    d.note(412, 'A skid buffer fixes local timing and elasticity. It cannot compensate for a consumer that is slower for good, '
                'and a full-state recovery bubble is possible.')
    d.save()


def uart_frame():
    d = Drawing('peripherals-uart-frame', 'An 8N1 UART frame carrying 0x53',
                'Line idles high • start bit low • eight data bits, least-significant first • one high stop bit', 460)
    x0, step = 100, 66
    bits = [1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1]
    names = ['idle', 'start', 'D0', 'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'stop', 'idle']
    for i, name in enumerate(names):
        d.text(x0 + i * step + step / 2, 112, name, size=18, anchor='middle', bold=name in ('start', 'stop'))
        d.path(f'M{x0 + i * step} 125V285', arrow=False)
    d.path(f'M{x0 + 12 * step} 125V285', arrow=False)
    path = ''
    for i, bit in enumerate(bits):
        x, y = x0 + i * step, 160 if bit else 250
        path += f'M{x} {y}H{x + step}' if i == 0 else f'L{x} {y}H{x + step}'
    d.parts.append(f'<path d="{path.replace("M", "M", 1)}" fill="none" stroke="{BLUE}" stroke-width="3"/>')
    d.text(28, 170, '1', size=20); d.text(28, 260, '0', size=20)
    for i in range(1, 11):
        d.parts.append(f'<circle cx="{x0 + i * step + step / 2}" cy="{160 if bits[i] else 250}" r="7" fill="{GREEN}"/>')
        d.text(x0 + i * step + step / 2, 310, str(bits[i]), size=20, bold=True, anchor='middle')
    d.text(28, 310, 'value', size=18)
    d.path(f'M{x0 + step} 345H{x0 + 11 * step}'); d.path(f'M{x0 + 11 * step} 345H{x0 + step}')
    d.text(x0 + 6 * step, 332, 'ten baud intervals carry eight payload bits', size=18, anchor='middle')
    d.text(28, 400, 'Green dots: the receiver samples near the middle of each interval.', size=18, color=GREEN)
    d.note(412, 'At 115,200 baud the continuous payload rate is at most 11,520 bytes per second; '
                'formatting, idle gaps and flow control lower it.')
    d.save()


def spi_modes():
    d = Drawing('peripherals-spi-modes', 'SPI modes: where the clock samples and where it shifts',
                'Leading means the first edge away from idle • filled dot = sample edge • open circle = shift edge', 700)
    x0, half = 280, 52
    modes = [(0, 0, 0), (1, 0, 1), (2, 1, 0), (3, 1, 1)]
    for row, (mode, cpol, cpha) in enumerate(modes):
        y = 130 + row * 135
        d.text(28, y - 4, f'Mode {mode}', size=21, bold=True)
        d.text(28, y + 22, f'CPOL {cpol}, CPHA {cpha}', size=18)
        idle, active = (150 if cpol == 0 else 90), (90 if cpol == 0 else 150)
        base = y - 40
        low, high = base + 56, base
        idle_y, active_y = (low, high) if cpol == 0 else (high, low)
        path = f'M{x0 - 60} {idle_y}H{x0}'
        for k in range(3):
            xa = x0 + k * 2 * half
            path += f'V{active_y}H{xa + half}V{idle_y}H{xa + 2 * half}'
        path += f'H{x0 + 6 * half + 60}'
        d.parts.append(f'<path d="{path}" fill="none" stroke="{BLUE}" stroke-width="3"/>')
        for k in range(3):
            lead, trail = x0 + k * 2 * half, x0 + k * 2 * half + half
            sample_x, shift_x = (lead, trail) if cpha == 0 else (trail, lead)
            mid = (low + high) / 2
            d.parts.append(f'<circle cx="{sample_x}" cy="{mid}" r="8" fill="{GREEN}"/>')
            d.parts.append(f'<circle cx="{shift_x}" cy="{mid}" r="8" fill="white" stroke="{ORANGE}" stroke-width="3"/>')
        d.text(x0 + 6 * half + 80, base + 34, 'SCK', size=18)
    d.note(660, 'In CPHA 0 the first data bit must already be available before the first sample edge. Bit order, frame length and select '
                'polarity come from the device specification.')
    d.save()


def uart_fifo_deadline():
    d = Drawing('peripherals-uart-fifo-deadline', 'How long software has before a 16-byte UART FIFO overflows',
                'Continuous 8N1 traffic at 115,200 baud • one byte takes about 86.8 microseconds', 460)
    x0, size = 70, 46
    d.text(28, 100, 'RX FIFO, 16 entries', size=20, bold=True)
    slots(d, x0, 125, 16, 12, BLUE, size)
    d.path(f'M{x0 + 12 * (size + 4) - 2} 118V108', ORANGE, arrow=False)
    d.text(x0 + 12 * (size + 4) - 2, 105, 'interrupt raised at 12 entries', size=18, anchor='middle', color=ORANGE)
    d.path(f'M{x0} 200H{x0 + 16 * (size + 4) - 4}'); d.path(f'M{x0 + 16 * (size + 4) - 4} 200H{x0}')
    d.text(x0 + 8 * (size + 4), 192, 'empty to full: 16 byte times, about 1.39 ms', size=18, anchor='middle')
    d.path(f'M{x0 + 12 * (size + 4)} 262H{x0 + 16 * (size + 4) - 4}', ORANGE); d.path(f'M{x0 + 16 * (size + 4) - 4} 262H{x0 + 12 * (size + 4)}', ORANGE)
    d.text(x0 + 14 * (size + 4), 292, '4 byte times,', size=18, anchor='middle', color=ORANGE)
    d.text(x0 + 14 * (size + 4), 316, 'about 347 us', size=18, anchor='middle', color=ORANGE, bold=True)
    d.text(x0, 292, 'The deadline must cover interrupt masking, arbitration,', size=18)
    d.text(x0, 316, 'handler entry and the actual service time, minus bytes', size=18)
    d.text(x0, 340, 'already in flight.', size=18)
    d.note(375, 'Internal ready/valid backpressure cannot pause an external UART sender. RTS/CTS can when it is implemented '
                'and wired; otherwise buffering and a bounded service policy have to cover the gap.')
    d.save()


FIGURES = [core_to_uncore, apb_ahb_phases, interrupt_gates, plic_claim_sequence, trap_entry_return,
           memory_hierarchy_paths, cache_address_lookup, plru_tree, amat_breakdown, byte_lanes,
           boot_memory_plan, sbi_privilege_boundaries, firmware_packaging,
           queued_capacity, skid_buffer, uart_frame, spi_modes, uart_fifo_deadline]
