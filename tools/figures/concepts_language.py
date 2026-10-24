#!/usr/bin/env python3
"""Original conceptual SVGs for the ISA, SystemVerilog and microarchitecture chapters, in the common style.

They reuse `Drawing` from architecture.py unchanged. Every figure is conceptual: it explains an organization,
a protocol or a worked example of the chapter and measures nothing. Driven by concepts.py.
"""
from architecture import Drawing, BLUE, GREEN, ORANGE, INK


def register_map():
    d = Drawing('isa-register-map', 'The architectural state of one RV32I hart',
                'Program counter and 32 integer registers, XLEN = 32 bits • ABI aliases', 560)
    d.rect(28, 90, 150, 46, INK)
    d.text(103, 120, 'PC', size=22, bold=True, anchor='middle')
    d.text(200, 120, 'plus memory, CSRs and privilege state where provided', size=18)
    aliases = (['zero', 'ra', 'sp', 'gp', 'tp', 't0', 't1', 't2', 's0', 's1'] + [f'a{i}' for i in range(8)]
               + [f's{i}' for i in range(2, 12)] + [f't{i}' for i in range(3, 7)])
    for n, alias in enumerate(aliases):
        color = INK if alias in ('zero', 'ra', 'sp', 'gp', 'tp') else ORANGE if alias[0] == 't' else GREEN if alias[0] == 's' else BLUE
        row, col = divmod(n, 8)
        x, y = 28 + col * 113, 160 + row * 72
        d.rect(x, y, 107, 62, color, dash=alias == 'zero')
        d.text(x + 53, y + 27, alias, size=21, bold=True, anchor='middle')
        d.text(x + 53, y + 51, f'x{n}', size=18, anchor='middle')
    legend = [(INK, 'special: zero, ra, sp, gp, tp'), (ORANGE, 't: caller-saved temporaries'),
              (GREEN, 's: callee-saved values'), (BLUE, 'a: arguments; a0 and a1 also return')]
    for i, (color, text) in enumerate(legend):
        x, y = 28 + (i % 2) * 452, 462 + (i // 2) * 30
        d.rect(x, y - 16, 24, 20, color)
        d.text(x + 34, y, text, size=18)
    d.note(525, 'x0 reads as zero and ignores writes. Register width (XLEN), instruction length, address width and bus width are '
                'separate facts: give each its own row in a configuration table.')
    d.save()


def load_store_bytes():
    d = Drawing('isa-load-store-bytes', 'Little-endian bytes and the two ways to load a byte',
                'sw of 0x12345678 at an aligned address A • LB sign-extends, LBU zero-extends', 560)
    d.text(28, 100, 'sw x5, 0(A) with x5 = 0x12345678', size=21, bold=True)
    for i, (value, addr) in enumerate([('78', 'A'), ('56', 'A+1'), ('34', 'A+2'), ('12', 'A+3')]):
        x = 190 + i * 185
        d.rect(x, 125, 170, 52, BLUE, fill='white')
        d.text(x + 85, 160, value, size=24, bold=True, anchor='middle')
        d.text(x + 85, 200, addr, size=18, anchor='middle')
    d.text(28, 160, 'byte value', size=18)
    d.text(28, 200, 'byte address', size=18)
    d.text(28, 262, 'Loading the byte 0xfd (1111 1101) into a 32-bit register', size=21, bold=True)
    for row, (name, bit, result) in enumerate([('LB', '1', '0xfffffffd'), ('LBU', '0', '0x000000fd')]):
        y = 290 + row * 80
        d.text(28, y + 33, name, size=22, bold=True)
        d.rect(100, y, 480, 48, ORANGE, dash=True)
        d.text(340, y + 31, '24 copies of bit 7 (1)' if row == 0 else '24 zero bits', size=18, anchor='middle', color=ORANGE)
        d.rect(584, y, 150, 48, BLUE)
        d.text(659, y + 31, '1111 1101', size=20, bold=True, anchor='middle')
        d.text(750, y + 31, '= ' + result, size=19, bold=True)
    d.note(465, 'A byte store changes one byte and leaves its neighbours alone. A misaligned access either traps or is handled, depending on the '
                'execution environment; silently dropping the low address bits hides a software bug.')
    d.save()


def width_and_shift():
    d = Drawing('sv-width-and-shift', 'Width and signedness are part of the circuit',
                'Worked examples of the chapter • operand extension, then logical and arithmetic shift', 560)
    d.text(28, 100, 'Addition: extend the operands to keep the carry', size=21, bold=True)
    for i, (name, value, width) in enumerate([('Left', '0xFFFF', '16 bits'), ('Right', '0x0001', '16 bits')]):
        y = 125 + i * 56
        d.text(28, y + 31, name, size=19)
        d.rect(110, y, 130, 44, BLUE, fill='white')
        d.text(175, y + 29, value, size=20, anchor='middle')
        d.text(252, y + 29, width, size=18)
    d.box(400, 125, 210, 100, "{1'b0, Left} +", "{1'b0, Right}", color=GREEN)
    d.path('M350 175H400')
    d.rect(700, 125, 232, 44, GREEN)
    d.text(816, 154, '0x10000', size=20, bold=True, anchor='middle')
    d.text(816, 190, '17-bit WideSum', size=18, anchor='middle')
    d.rect(700, 215, 232, 44, ORANGE, dash=True)
    d.text(816, 244, '0x0000', size=20, bold=True, anchor='middle')
    d.text(816, 280, 'carry lost in 16 bits', size=18, anchor='middle', color=ORANGE)
    d.path('M610 160H700'); d.path('M610 200H655V237H700', ORANGE, dashed=True)
    d.text(28, 345, "Right shift by one of Data = 32'h80000000", size=21, bold=True)
    cells = [('Data', '1000 0000 ...', '0x80000000', BLUE), ('Data >> 1', '0100 0000 ...', '0x40000000', GREEN),
             ('$signed(Data) >>> 1', '1100 0000 ...', '0xc0000000', ORANGE)]
    for i, (name, bits, value, color) in enumerate(cells):
        x = 28 + i * 306
        d.rect(x, 370, 290, 100, color)
        d.text(x + 145, 400, name, size=19, bold=True, anchor='middle')
        d.text(x + 145, 430, bits, size=20, anchor='middle')
        d.text(x + 145, 457, value, size=18, anchor='middle')
    d.text(334, 494, 'zero fills from the left', size=18, color=GREEN)
    d.text(640, 494, 'the sign bit is copied', size=18, color=ORANGE)
    d.note(512, 'The register declaration cannot tell which instruction is executing, so a RISC-V ALU provides both shifts. '
                'Sized literals and explicit extension keep widths unambiguous.')
    d.save()


def packed_layout():
    d = Drawing('sv-packed-struct-and-arrays', 'Packed layout versus an array of elements',
                'The declaration order of a packed struct fixes its bit layout • field widths are not drawn to scale', 600)
    d.text(28, 100, 'request_t: one packed 77-bit value, first field at the top', size=21, bold=True)
    fields = [('write', '[76]', 100, BLUE), ('tag', '[75:68]', 150, GREEN), ('address', '[67:36]', 250, BLUE),
              ('data', '[35:4]', 250, GREEN), ('byte_enable', '[3:0]', 154, ORANGE)]
    x = 28
    for name, rng, width, color in fields:
        d.rect(x, 125, width - 4, 64, color)
        d.text(x + width / 2 - 2, 154, name, size=18, bold=True, anchor='middle')
        d.text(x + width / 2 - 2, 178, rng, size=18, anchor='middle')
        x += width
    d.text(28, 220, 'bit 76', size=18)
    d.text(932, 220, 'bit 0', size=18, anchor='end')
    d.text(28, 275, 'Word: one packed vector', size=21, bold=True)
    d.rect(28, 290, 904, 46, BLUE, fill='white')
    d.text(480, 320, 'logic [31:0] Word', size=20, anchor='middle')
    d.text(28, 380, 'Words [0:15]: sixteen separate elements', size=21, bold=True)
    for i in range(16):
        x, y = 28 + (i % 8) * 113, 397 + (i // 8) * 54
        d.rect(x, y, 107, 46, GREEN, fill='white')
        d.text(x + 53, y + 30, f'Words[{i}]', size=18, anchor='middle')
    d.note(515, "A packed vector's bit order is not a statement of memory endianness: mapping a word to byte addresses is an interface "
                'convention that byte-lane wiring and loaders must implement.')
    d.save()


def datapath_dependencies():
    d = Drawing('microarchitecture-datapath-dependencies', 'Datapath value dependencies, before registers are placed',
                'An arrow is a dependency, not proof that the path is combinational • decide where registers go', 460)
    d.box(28, 150, 150, 80, 'Instruction', 'fetched bits')
    d.box(220, 150, 130, 80, 'Decode', 'fields')
    d.path('M178 190H220')
    d.box(385, 100, 215, 80, 'Operands', 'two register reads')
    d.box(385, 215, 215, 80, 'Immediate', 'rebuilt from bits')
    d.path('M350 175H367V140H385'); d.path('M350 205H367V255H385')
    d.box(650, 150, 105, 100, 'ALU', 'add, logic', 'compare')
    d.path('M600 140H625V185H650'); d.path('M600 255H625V215H650')
    d.box(795, 150, 137, 100, 'Result', 'selection')
    d.path('M755 200H795')
    d.box(385, 320, 215, 70, 'Memory data', 'load response', color=GREEN)
    d.path('M600 355H775V235H795', GREEN)
    d.box(795, 320, 137, 70, 'Register', 'write', color=ORANGE)
    d.path('M863 250V320', ORANGE)
    d.note(415, 'For each mux, list its sources and the control condition that chooses each one, and annotate the number of cycles '
                'between register boundaries.')
    d.save()


def execution_time_bars():
    d = Drawing('microarchitecture-execution-time-bars', 'Time per instruction = clock period x CPI',
                'Invented values that demonstrate the equation • not measurements of Wally or of any FPGA', 430)
    bars = [('Single cycle', 20, 1.0, 'period 20 ns, CPI 1'), ('Multicycle', 5, 4.0, 'period 5 ns, CPI 4'),
            ('Pipelined', 5, 1.2, 'period 5 ns, CPI 1.2')]
    scale = 25
    for i, (name, period, cpi, label) in enumerate(bars):
        y = 105 + i * 92
        d.text(28, y + 30, name, size=20, bold=True)
        total = period * cpi
        d.rect(190, y, total * scale, 46, BLUE if i == 0 else GREEN if i == 1 else ORANGE)
        d.text(190 + total * scale + 14, y + 30, f'{total:g} ns per instruction', size=19, bold=True)
        d.text(190, y + 72, label, size=18)
    d.note(380, 'A faster clock alone does not make a faster program: compare instruction count, CPI and clock period together.')
    d.save()


FIGURES = [register_map, load_store_bytes, width_and_shift, packed_layout, datapath_dependencies, execution_time_bars]
