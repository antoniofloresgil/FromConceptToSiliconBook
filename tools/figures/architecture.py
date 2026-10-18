#!/usr/bin/env python3
"""Generate the book's original architectural SVGs using one visual vocabulary.

No drawing packages required. --check compares outputs without rewriting them.
Physical panels embed actual OpenROAD captures, never simulated geometry.
"""
import argparse
import base64
import hashlib
from html import escape
import json
from pathlib import Path
import textwrap

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / 'figures'
BLUE, ORANGE, GREEN, INK = '#24577a', '#a34624', '#28705c', '#172b3a'
PALE = {BLUE: '#eef5fa', ORANGE: '#fff3e9', GREEN: '#edf7f1', INK: '#f2f4f6'}
outputs = {}


class Drawing:
    def __init__(self, name, title, subtitle, height=600):
        self.name, self.height, self.initial_height = name, height, height
        self.parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="960" height="{height}" '
                      f'viewBox="0 0 960 {height}" role="img" aria-labelledby="title desc">',
                      f'<title id="title">{escape(title)}</title><desc id="desc">{escape(subtitle)}</desc>',
                      '<defs>']
        for color, key in [(BLUE, 'data'), (ORANGE, 'event'), (GREEN, 'memory')]:
            self.parts.append(f'<marker id="{key}" markerWidth="9" markerHeight="9" '
                              f'refX="8" refY="4" orient="auto"><path d="M0 0L8 4L0 8Z" fill="{color}"/></marker>')
        self.parts += ['</defs>', f'<rect width="960" height="{height}" fill="white"/>',
                       '<g font-family="Arial, sans-serif" fill="#172b3a">']
        self.text(28, 33, title, size=26, bold=True)
        self.text(28, 62, subtitle, size=18)

    def text(self, x, y, value, size=21, bold=False, anchor='start', color=INK):
        self.parts.append(f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" '
                          f'fill="{color}" font-weight="{"bold" if bold else "normal"}">{escape(value)}</text>')

    def rect(self, x, y, w, h, color=BLUE, fill=None, dash=False):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" '
                          f'fill="{fill or PALE[color]}" stroke="{color}" stroke-width="2" '
                          f'stroke-dasharray="{"8 5" if dash else "none"}"/>')

    def box(self, x, y, w, h, title, *lines, color=BLUE):
        self.rect(x, y, w, h, color)
        start = y + h / 2 - len(lines) * 12 + 7
        self.text(x+w/2, start, title, bold=True, anchor='middle')
        for i, line in enumerate(lines):
            self.text(x+w/2, start+26*(i+1), line, size=18, anchor='middle')

    def path(self, path, color=BLUE, dashed=False, arrow=True):
        key = {BLUE: 'data', ORANGE: 'event', GREEN: 'memory'}[color]
        self.parts.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2.5" '
                          f'stroke-dasharray="{"7 5" if dashed else "none"}" '
                          f'marker-end="url(#{key})"/>' if arrow else
                          f'<path d="{path}" fill="none" stroke="{color}" stroke-width="1.2"/>')

    def note(self, y, *lines):
        lines = [part for line in lines for part in textwrap.wrap(line, width=88)]
        self.rect(28, y, 904, 28+25*len(lines), INK)
        for i, line in enumerate(lines):
            self.text(44, y+28+25*i, line, size=19)
        self.height = max(self.height, y+48+25*len(lines))

    def save(self):
        self.parts[0] = self.parts[0].replace(f'height="{self.initial_height}"', f'height="{self.height}"').replace(
            f'0 0 960 {self.initial_height}', f'0 0 960 {self.height}')
        self.parts = [p.replace(f'height="{self.initial_height}"', f'height="{self.height}"')
                      if p == f'<rect width="960" height="{self.initial_height}" fill="white"/>' else p
                      for p in self.parts]
        outputs[self.name+'.svg'] = ('\n'.join(self.parts+['</g></svg>'])+'\n').encode()


def hierarchy():
    d = Drawing('architecture-wally-hierarchy', 'Wally: hierarchy and module ownership',
                'Pinned rv32gc reading baseline • functional groups; conditional subtrees are abbreviated', 665)
    d.rect(28, 85, 904, 460, BLUE, fill='white')
    d.text(48, 115, 'wallypipelinedsoc', bold=True)
    d.box(625, 96, 285, 50, 'resetsync', 'synchronize reset release')
    d.rect(48, 160, 480, 365)
    d.text(66, 190, 'core: wallypipelinedcore', bold=True)
    d.box(68, 212, 210, 78, 'ifu', 'fetch / prediction', 'I-MMU / I-cache')
    d.box(298, 212, 210, 78, 'ieu', 'decode / integer RF', 'ALU / forwarding')
    d.box(68, 306, 210, 78, 'lsu', 'D-MMU / D-cache', 'load/store / atomics')
    d.box(298, 306, 210, 78, 'mdu / fpu', 'multiply / divide', 'floating-point paths')
    d.box(68, 400, 210, 98, 'Privilege / traps', 'CSR / traps / PMP', 'stall / flush control', color=ORANGE)
    d.box(298, 400, 210, 98, 'ebu', 'IFU + LSU requests', 'AHB interface')
    d.rect(565, 160, 345, 365, GREEN)
    d.text(582, 190, 'uncoregen.uncore', bold=True)
    d.box(585, 215, 305, 68, 'Decode / response mux', 'RAM / ROM / external target', color=GREEN)
    d.box(585, 310, 305, 68, 'APB bridge / devices', 'UART / GPIO / SPI / PWM / SD', color=GREEN)
    d.box(585, 408, 305, 80, 'CLINT / PLIC', 'timer / software / external IRQs', color=ORANGE)
    d.path('M508 445H548V250H585')
    d.path('M585 485H548V514H278V458', ORANGE, dashed=True)
    d.text(585, 510, 'Conditional BUS_SUPPORTED', size=18)
    d.note(565, 'Containment identifies RTL ownership; arrows show selected cross-boundary paths.',
           'Cache/MMU internals live below IFU/LSU; this is not an exhaustive elaborated instance tree.')
    d.save()


def ooo():
    d = Drawing('architecture-ooo-window', 'Out-of-order execution: order, readiness and recovery',
                'Conceptual physical-register design • no fixed BOOM or XiangShan widths implied', 620)
    for x, name, line in [(28, 'Fetch / decode', 'program order'), (266, 'Rename', 'map + free list'),
                           (504, 'Dispatch', 'allocate window'), (742, 'Issue queues', 'wait for operands')]:
        d.box(x, 105, 190, 85, name, line)
    for x in [218, 456, 694]: d.path(f'M{x} 147H{x+48}')
    d.box(625, 265, 307, 88, 'Execute / LSQ', 'ready ops may pass older ops')
    d.path('M837 190V265')
    d.box(300, 265, 265, 88, 'Physical register file', 'operand read / result write')
    d.path('M565 286H625')
    d.path('M625 333H565')
    d.path('M900 265V227H750V190', ORANGE, dashed=True)
    d.text(28, 235, 'Allocate ROB entry at dispatch', size=19)
    d.box(28, 392, 600, 96, 'Reorder buffer (ROB): oldest → youngest', 'completion / exceptions; retire only from the head')
    d.path('M599 190V240H120V392')
    d.path('M779 353V373H570V392', ORANGE, dashed=True)
    d.box(742, 392, 190, 96, 'Commit', 'architectural state', 'release old registers')
    d.path('M628 440H742')
    d.path('M837 488V514H12V205H361V190', ORANGE, dashed=True)
    d.text(385, 535, 'Recovery restores rename state and discards younger work', size=19, color=ORANGE)
    d.note(550, 'Issue follows readiness; commit follows program order. A finished instruction may still wait.')
    d.save()


def miss():
    d = Drawing('architecture-cache-miss', 'A dirty cache miss: follow ownership of a line',
                'Blocking write-back example • translation/protection already completed successfully', 610)
    xs = [125, 365, 605, 835]
    for x, title in zip(xs, ['CPU / LSU', 'D-cache', 'EBU / bus', 'RAM']):
        d.box(x-96, 92, 192, 50, title)
        d.path(f'M{x} 145V515', arrow=False)
    def event(a, b, y, label, color=BLUE):
        d.path(f'M{xs[a]} {y}H{xs[b]}', color)
        d.text((xs[a]+xs[b])/2, y-10, label, size=18, anchor='middle')
    event(0, 1, 185, '1  Load request')
    d.text(380, 216, 'tag miss; select dirty victim', size=18)
    event(1, 3, 255, '2  Write back victim address + data')
    event(3, 1, 304, '3  Writeback complete; victim may be replaced', GREEN)
    event(1, 3, 356, '4  Request missed line')
    event(3, 1, 410, '5  Refill accepted beat by beat', GREEN)
    d.text(380, 444, 'install tag / data; set valid; clear dirty', size=18)
    event(1, 0, 492, '6  Return requested word', GREEN)
    d.text(42, 349, 'CPU waits', size=19, color=ORANGE)
    d.note(535, 'A clean or invalid victim skips writeback. Backpressure lengthens the intervals.',
           'In the chapter’s RV32 / 32-bit AHB baseline, a 64-byte line needs 16 accepted data beats.')
    d.save()


def wave(name, title, subtitle, rows, notes, transfers):
    # Values denote the interval immediately BEFORE each numbered rising edge.
    d = Drawing(name, title, subtitle, 170+45*len(rows)+35*len(notes))
    x0, step, n = 176, 86, 8
    for i in range(n):
        x = x0+(i+1)*step
        d.path(f'M{x} 110V{125+45*len(rows)}', arrow=False)
        d.text(x, 97, str(i+1), size=18, anchor='middle')
    d.text(28, 97, 'Rising edge →', size=18)
    for row, (label, values) in enumerate(rows):
        y = 135+45*row
        d.text(28, y+5, label, size=20)
        if all(isinstance(v, int) for v in values):
            path = ''
            for i, value in enumerate(values):
                x, yy = x0+i*step, y-12 if value else y+10
                path += f' {"M" if i==0 else "L"}{x} {yy}H{x+step}'
            d.path(path, arrow=False)
        else:
            for i, value in enumerate(values):
                d.rect(x0+i*step+3, y-17, step-6, 30, BLUE, fill='white')
                d.text(x0+i*step+step/2, y+4, str(value), size=18, anchor='middle')
        for r, edge in transfers:
            if r == row:
                x = x0+edge*step
                d.parts.append(f'<circle cx="{x}" cy="{y}" r="6" fill="{GREEN}"/>')
    d.note(143+45*len(rows), *notes)
    d.save()


def axi():
    wave('architecture-axi-write', 'AXI4 write: independent channels and retained response',
         'Single-beat example • green dots mark acceptance at rising edges; dash = no valid payload',
         [('AWVALID', [1,1,0,0,0,0,0,0]), ('AWREADY', [0,1,1,1,1,1,1,1]),
          ('AWADDR', ['A','A','—','—','—','—','—','—']),
          ('WVALID', [0,0,1,1,1,0,0,0]), ('WREADY', [0,0,0,0,1,1,1,1]),
          ('WDATA', ['—','—','D0','D0','D0','—','—','—']),
          ('BVALID', [0,0,0,0,0,1,1,1]), ('BREADY', [0,0,0,0,0,0,0,1])],
         ['AW accepted at edge 2; W (WLAST=1) accepted at edge 5; B accepted at edge 8.',
          'Keep WDATA / WSTRB / WLAST stable through edge 5; keep BRESP stable through edge 8.'],
         [(0,2),(3,5),(6,8)])
    wave('architecture-axi-read', 'AXI4 read burst: a stalled beat is still the same beat',
         'Four-beat INCR read • ARLEN=3, ARSIZE=2; one ID, no interleaving shown',
         [('ARVALID', [1,0,0,0,0,0,0,0]), ('ARREADY', [1,1,1,1,1,1,1,1]),
          ('RVALID', [0,1,1,1,1,1,1,0]), ('RREADY', [0,1,0,0,1,1,1,1]),
          ('RDATA', ['—','D0','D1','D1','D1','D2','D3','—']),
          ('RLAST', [0,0,0,0,0,0,1,0])],
         ['Accept D0, D1, D2, D3 at edges 2, 5, 6, 7. Edges 3–4 do not advance the burst.',
          'While stalled, retain RDATA / RRESP / RID / RLAST. LAST belongs to the final beat.'],
         [(0,1),(2,2),(2,5),(2,6),(2,7)])


def boot():
    d = Drawing('architecture-boot-timeline', 'Reset → OpenSBI → Linux: execution and handoff contracts',
                'Conventional single-hart path • milestone order, not a calibrated time scale', 605)
    d.path('M55 112H910')
    for x, text in [(55,'reset'),(295,'firmware'),(555,'kernel'),(820,'userspace')]:
        d.text(x, 98, text, size=19)
    d.box(28, 145, 205, 115, 'ROM / loader', 'M-mode entry', 'stack / memory ready', 'place images + DTB')
    d.box(265, 145, 205, 115, 'OpenSBI init', 'M-mode firmware', 'trap / PMP policy', 'SBI services')
    d.box(505, 145, 205, 115, 'Linux entry', 'S-mode kernel', 'MMU / timer / drivers', 'mount root filesystem')
    d.box(745, 145, 187, 115, 'Application', 'U-mode process', 'syscalls → kernel')
    for x in [233,470,710]: d.path(f'M{x} 201H{x+32 if x!=710 else 745}')
    d.box(350, 320, 530, 85, 'Kernel entry contract', 'a0 = hart ID; a1 = DTB address; satp = 0', color=GREEN)
    d.path('M505 246H490V362H350', GREEN)
    d.box(265, 445, 667, 65, 'Resident OpenSBI: M-mode service runtime', 'remains available after kernel startup', color=ORANGE)
    d.path('M368 260V445', ORANGE, dashed=True)
    d.path('M605 405V445', ORANGE, dashed=True)
    d.text(628, 432, 'SBI ecall / mret', size=18, color=ORANGE)
    d.note(530, 'An optional bootloader may run between firmware and kernel.',
           'QEMU loads images for the experiment; a physical platform must supply its own loading path.')
    d.save()


def nexys():
    d = Drawing('architecture-nexys-domains', 'Nexys Video: Wally, DDR service and clock domains',
                'Open fpgaOpenSource target • distinct from the standalone AXI/DMA implementation fixture', 660)
    d.box(28, 97, 210, 78, 'Board oscillator', '100 MHz input')
    d.box(310, 97, 370, 78, 'LiteDRAM clock generation', 'shared system clock: 40 MHz')
    d.path('M238 136H310')
    d.rect(28, 217, 904, 290)
    d.text(48, 247, 'Shared system-clock domain', bold=True)
    d.box(48, 272, 238, 90, 'Wally SoC', 'IROM / DTIM', 'CLINT / UART / GPIO')
    d.box(325, 272, 255, 90, 'AHB → Wishbone', 'single NONSEQ transfers', 'registered region select')
    d.box(625, 272, 287, 90, 'LiteDRAM controller', 'user port + DDR scheduling')
    d.path('M286 315H325'); d.path('M580 315H625')
    d.box(325, 398, 255, 85, 'DDR service CPU', 'VexRiscv / ROM / CSRs', 'DDR init / calibration', color=GREEN)
    d.path('M580 440H770V362', GREEN)
    d.path('M495 175V217')
    d.box(625, 535, 287, 75, 'Artix-7 PHY → DDR3', 'PHY clocks / delays / pins', color=GREEN)
    d.path('M875 362H945V572H912', GREEN)
    d.path('M625 342H606V525H168V362', ORANGE, dashed=True)
    d.text(190, 550, 'Release Wally only when', size=19, color=ORANGE)
    d.text(190, 577, 'init_done && !init_error', size=19, color=ORANGE)
    d.text(28, 638, 'PHY domains require their own constraints; routed timing alone does not prove DDR calibration.', size=18)
    d.save()


def security():
    d = Drawing('architecture-security-surfaces', 'Trust boundaries and attack surfaces',
                'Proposed security architecture • guards / root of trust are additions, not existing Wally claims', 630)
    d.box(28, 100, 250, 85, 'External inputs', 'UART / network / storage', 'untrusted data and images', color=ORANGE)
    d.box(355, 100, 250, 85, 'Debug / test pins', 'JTAG / halt / bus access', 'lifecycle + authentication', color=ORANGE)
    d.box(682, 100, 250, 85, 'Physical access', 'clock / voltage / power', 'faults and observations', color=ORANGE)
    d.rect(28, 235, 904, 290, BLUE, fill='white', dash=True)
    d.text(48, 268, 'SoC boundary: admission policy must cover every master', bold=True)
    d.box(48, 305, 245, 82, 'Boot / policy root', 'verify image + version', 'protect keys / policy', color=GREEN)
    d.box(355, 305, 250, 82, 'CPU + PMP', 'privilege / access checks', 'CPU requests only')
    d.box(665, 305, 245, 82, 'DMA / debug guards', 'bounds / ownership', 'independent admission')
    d.box(355, 435, 555, 65, 'Interconnect → RAM / peripherals / secrets', 'authorization must hold at the actual target')
    d.path('M153 185V305', ORANGE, dashed=True)
    d.path('M480 185V213H788V305', ORANGE, dashed=True)
    d.path('M807 185H945V420H910', ORANGE, dashed=True)
    d.text(650, 412, 'fault / leakage surfaces', size=18, color=ORANGE)
    d.path('M293 345H355', GREEN)
    d.path('M480 387V435'); d.path('M788 387V435')
    d.note(550, 'A verified boot image does not confine DMA. CPU PMP does not authorize debug or other masters.',
           'Threat model + enforcement + negative tests belong to each boundary; no aggregate “secure” claim.')
    d.save()


def rvv():
    d = Drawing('architecture-rvv-registers', 'RVV: architectural groups and physical banks',
                'Illustration: VLEN=128, SEW=16, LMUL=2 → VLMAX=16 elements', 610)
    d.text(28, 104, 'Architectural view: 32 × VLEN bits; v8–v9 form one aligned group', size=21, bold=True)
    for i in range(4):
        y = 130+i*52
        d.text(28, y+26, 'v'+str(8+i), bold=True)
        for j in range(8):
            d.rect(105+j*96, y, 90, 40, BLUE if i<2 else INK)
            d.text(150+j*96, y+27, f'e{i*8+j}' if i<2 else '…', size=19, anchor='middle')
    d.path('M907 130H925V222H907', GREEN, arrow=False)
    d.text(28, 365, 'Possible physical organization (implementation choice)', size=21, bold=True)
    for x, name in [(28,'Bank 0'),(266,'Bank 1'),(504,'Bank 2'),(742,'Bank 3')]:
        d.box(x, 390, 190, 65, name, 'register slices')
        d.path(f'M{x+95} 455V480')
    d.box(28, 480, 904, 48, 'Operand routing / lane execution / writeback')
    d.note(548, 'LMUL groups architectural registers; it does not specify banks, lane count, ports or cycle latency.')
    d.save()


def accelerator():
    d = Drawing('architecture-dotproduct-dma', 'AXI/DMA dot product: control, computation and memory',
                'Executable Lab 10 / Wally integration • signed 16-bit operands in 32-bit words; 64-bit sum', 665)
    d.box(28, 95, 265, 80, 'CPU / firmware', 'program descriptors; START', 'poll status or service IRQ')
    d.box(355, 95, 285, 80, 'AHB → AXI4-Lite', 'CPU control adapter')
    d.path('M293 136H355')
    d.rect(28, 225, 612, 315)
    d.text(48, 258, 'dotproduct_axi', bold=True)
    d.box(48, 285, 265, 96, 'AXI4-Lite registers', 'AW / W captured separately', 'status / error / IRQ_ACK')
    d.box(355, 285, 265, 96, 'Descriptor validation', 'bounds / length / alignment', 'latch active A / B / dst / N')
    d.path('M313 330H355')
    d.path('M495 175V205H181V285')
    d.box(48, 415, 265, 98, 'dotproduct_mac', 'signed 16 × 16 product', 'sign-extend + 64-bit add')
    d.box(355, 415, 265, 98, 'Engine FSM', 'read A; read B; accumulate', 'write low / high; check B')
    d.path('M488 381V415')
    d.path('M355 442H313'); d.path('M313 490H355')
    d.box(710, 285, 222, 100, 'AXI4 memory port', 'single-beat, ID 0', 'one outstanding access', color=GREEN)
    d.box(710, 435, 222, 78, 'Shared memory', 'input A / B; result dst', color=GREEN)
    d.path('M620 466H666V335H710', GREEN)
    d.path('M821 385V435', GREEN)
    d.path('M48 355H12V195H161V175', ORANGE, dashed=True)
    d.text(38, 211, 'IRQ → platform completion path', size=18, color=ORANGE)
    d.note(565, 'Linux/Wally extension decodes MMIO at 0x10080000; the IP itself receives register offsets.',
           'Driver-managed buffers / ordering remain separate from the DMA bounds checked by the RTL.')
    d.save()


def physical():
    d = Drawing('architecture-openroad-checkpoints', 'One accumulator through four physical checkpoints',
                'Actual Nangate45 OpenROAD captures • 55% target utilization; requested period 0.91 ns', 855)
    images = [('architecture-floorplan.png', '1  Floorplan', 'Rows, I/O pins and supply grid; cells not placed.'),
              ('openroad-study-placed.png', '2  Placement', 'Logic legalized in rows; clock still ideal.'),
              ('openroad-study-cts.png', '3  Clock-tree synthesis', 'Clock buffers inserted; clock propagated.'),
              ('openroad-study-routed.png', '4  Detailed routing', 'Signal wires realized; extracted RC used for STA.')]
    for i, (name, title, detail) in enumerate(images):
        x, y = 28+(i%2)*464, 95+(i//2)*350
        d.rect(x, y, 440, 335, BLUE, fill='white')
        d.text(x+14, y+30, title, bold=True)
        encoded = base64.b64encode((FIG/name).read_bytes()).decode()
        d.parts.append(f'<image x="{x+14}" y="{y+42}" width="412" height="246" '
                       f'preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,{encoded}"/>')
        # Keep the small panel caption to two lines.
        before, after = detail.split('; ') if '; ' in detail else (detail, '')
        d.text(x+14, y+307, before+(';' if after else ''), size=17)
        if after: d.text(x+14, y+329, after, size=17)
    d.text(28, 824, 'Only panel 1 is a new prefix replay; panels 2–4 preserve the recorded Lab 16 implementation.', size=18)
    d.save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    for draw in [hierarchy, ooo, miss, axi, boot, nexys, security, rvv, accelerator, physical]:
        draw()
    source = ROOT / 'tools/figures/architecture.py'
    inputs = [source, FIG/'architecture-floorplan.json', FIG/'architecture-floorplan.png']
    inputs += [FIG / ('openroad-study-'+stage+'.png') for stage in ['placed', 'cts', 'routed']]
    record = dict(schema=1, generator='tools/figures/architecture.py',
                  inputs={p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
                  outputs={name: hashlib.sha256(data).hexdigest() for name, data in outputs.items()})
    outputs['architecture-manifest.json'] = (json.dumps(record, indent=2)+'\n').encode()
    for name, data in outputs.items():
        if args.check:
            assert (FIG/name).read_bytes() == data, 'Stale figure: '+name
        else:
            (FIG/name).write_bytes(data)
    print(('CHECKED' if args.check else 'GENERATED'), len(outputs)-1, 'original SVG figures and provenance manifest')


if __name__ == '__main__':
    main()
