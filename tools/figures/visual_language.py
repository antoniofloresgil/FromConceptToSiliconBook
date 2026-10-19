"""Generate conceptual diagrams and non-destructive capture reading panels."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import struct
from architecture import Drawing, outputs, BLUE, GREEN, ORANGE, INK, ROOT, FIG

TRACE = ROOT / 'docs/audits/2026-10-19/evidence/raw/formal/fault-counterexample.vcd'
PROFILE = ROOT / 'labs/18-linux-accelerator/manifest.json'


def legend():
    d = Drawing('visual-component-language', 'One vocabulary for SoC diagrams',
                'Conceptual symbols; category comes from shape marks and labels, never hue alone', 520)
    entries = [('cpu','CPU / core','double outline'), ('cache','Cache','three short rules'),
               ('memory','Memory','two short rules'), ('interconnect','Interconnect','heavy top spine'),
               ('peripheral','Peripheral','edge ports'), ('accelerator','Accelerator','compute chevrons')]
    for i,(kind,title,detail) in enumerate(entries):
        x,y=28+(i%3)*310,105+(i//3)*135
        d.box(x,y,284,105,title,detail,kind=kind,color=GREEN if kind in ['cache','memory'] else BLUE)
    d.path('M45 415H245');d.text(270,422,'Solid arrow: stated data / request direction',size=19)
    d.path('M45 452H245',ORANGE,dashed=True);d.text(270,459,'Dashed arrow: event / control / dependency',size=19)
    d.text(28,500,'Containment is ownership; timing and coherence require their own explicit contracts.',size=18)
    d.save()


def datapath():
    d=Drawing('visual-wally-datapath','Five stages: follow an instruction and its result',
              'Conceptual orientation for the simplified pipeline; arrows are dependencies, not cycle counts',650)
    titles=['F: fetch','D: decode','E: execute','M: memory','W: writeback']
    for i,title in enumerate(titles):
        d.box(28+183*i,205,170,95,title, ['PC / instruction','RF / operands','ALU / branch','load / store','rd / write enable'][i])
        if i<4:d.path(f'M{198+183*i} 252H{211+183*i}')
    d.box(28,95,250,65,'Instruction memory','synchronous read',kind='memory',color=GREEN)
    d.path('M113 205V160',GREEN);d.path('M278 128H296V205',GREEN)
    d.box(545,370,225,80,'Data memory','request / response',kind='memory',color=GREEN)
    d.path('M620 300V370',GREEN);d.path('M770 410H845V300',GREEN)
    d.path('M845 300V492H296V300');d.text(325,480,'Writeback returns the selected value to the register file',size=18)
    d.path('M479 205V182H113V205',ORANGE,dashed=True)
    d.text(400,150,'Branch / redirect control',size=19,color=ORANGE)
    d.note(535,'Carry PC, destination, validity and control with the payload across every stage boundary.',
           'Stall, flush and bypass logic are omitted here; use the enlarged attributed datapath for exact signals.')
    d.save()


def comparison():
    d=Drawing('visual-core-organizations','Core organizations: where instructions wait',
              'Conceptual comparison; no fixed configuration, widths or performance numbers are implied',610)
    rows=[('Time-shared', ['Fetch','Decode / RF','ALU / memory','Writeback']),
          ('Short pipeline',['Fetch + buffer','Decode / ALU','Memory wait','Retire']),
          ('In-order pipeline',['Fetch','Decode / RF','Execute','Memory / WB'])]
    for i,(name,stages) in enumerate(rows):
        y=110+i*130;d.text(28,y,name,size=21,bold=True)
        for j,stage in enumerate(stages):
            d.box(28+j*233,y+20,205,65,stage)
            if j<3:d.path(f'M{233+j*233} {y+52}H{261+j*233}')
    d.note(505,'Rows are organizations, not matched cycle-by-cycle timelines or exact processor schematics.',
           'PicoRV32, Ibex and CV32E40P motivate different points; inspect the selected core configuration.')
    d.save()


def verification():
    d=Drawing('visual-verification-flow','Verification: independent expectations and observations',
              'Conceptual workflow; a passing test or bounded check is not universal correctness',610)
    d.box(28,100,260,85,'Contract','events / reset / errors')
    d.box(365,100,260,85,'Independent model','expected transactions')
    d.path('M288 142H365')
    for x,title,line in [(28,'Driver','legal + stress traffic'),(365,'RTL DUT','state / interfaces'),(702,'Monitor','accepted events only')]:
        d.box(x,270,230,85,title,line)
    d.path('M258 312H365');d.path('M595 312H702')
    d.box(702,100,230,85,'Scoreboard','compare results')
    d.path('M625 142H702');d.path('M817 270V185')
    d.box(28,435,370,85,'Formal harness','assume env; assert guarantees')
    d.box(515,435,417,85,'Evidence / regression','covers + counterexamples')
    d.path('M158 185V225H12V410H213V435',ORANGE,dashed=True)
    d.path('M398 477H515');d.path('M932 142H948V477H932',ORANGE,dashed=True)
    d.note(545,'The reference model must not copy the RTL algorithm blindly. Log the configuration and random seed.')
    d.save()


def scheduling():
    d=Drawing('visual-sampling-timeline','Simulation: an edge is not the end of the time step',
              'Conceptual event ordering for the cocotb example; horizontal spacing is not measured time',440)
    names=[('Drive inputs','before active edge'),('RisingEdge(clk)','wake sequential logic'),('RTL settles','NBA + combinational'),('ReadOnly()','sample stable results')]
    for i,(a,b) in enumerate(names):
        d.box(28+i*233,140,205,105,a,b)
        if i<3:d.path(f'M{233+i*233} 192H{261+i*233}')
    d.path('M830 245V305H133V245',ORANGE,dashed=True)
    d.text(225,295,'Advance to a writable phase / next drive opportunity',size=19,color=ORANGE)
    d.note(335,'RisingEdge alone need not observe the final nonblocking-assignment result.',
           'Do not drive new inputs during ReadOnly; the next transfer still needs a legal clock handshake.')
    d.save()


def trace_rows():
    symbols={};values={};rows={};time=None
    for line in TRACE.read_text(encoding='utf-8').splitlines():
        if line.startswith('$var'):
            a=line.split();symbols[a[3]]=a[4].lstrip('\\')
        elif line.startswith('#'):
            if time is not None:rows[time]=values.copy()
            time=int(line[1:])
        elif line.startswith('b'):
            v,key=line[1:].split();values[symbols[key]]=int(v,2) if re.fullmatch('[01]+',v) else v
        elif line and line[0] in '01' and line[1:] in symbols:
            values[symbols[line[1:]]]=int(line[0])
    if time is not None:rows[time]=values.copy()
    return rows


def counterexample():
    rows=trace_rows()
    assert rows[4]['in_valid']==rows[4]['in_ready']==rows[4]['out_valid']==rows[4]['out_ready']==1
    assert rows[4]['occupancy']==1 and rows[5]['occupancy']==2
    d=Drawing('visual-formal-counterexample','A real counterexample: exchange creates a phantom item',
              'Derived from the retained Lab 15 VCD; observations 3, 4 and 5 are formal steps, not nanoseconds',650)
    xs=[425,625,825]
    for x,t in zip(xs,[3,4,5]):d.text(x,115,f'Step {t}',size=21,bold=True,anchor='middle')
    fields=[('Reset','reset'),('Input valid / ready',None),('Output valid / ready','output'),
            ('Input byte','in_data'),('Observed occupancy','occupancy')]
    for i,(label,key) in enumerate(fields):
        y=165+54*i;d.text(28,y,label,size=21,bold=key=='occupancy')
        for x,t in zip(xs,[3,4,5]):
            r=rows[t]
            value=(f"{r['in_valid']} / {r['in_ready']}" if key is None else
                   f"{r['out_valid']} / {r['out_ready']}" if key=='output' else
                   f"0x{r[key]:02x}" if key=='in_data' else str(r[key]))
            d.text(x,y,value,size=21,anchor='middle')
    d.path('M625 420V460H825V420',ORANGE,dashed=True)
    d.text(28,480,'At step 4: push = pop = 1; required next occupancy = 1.',size=21,bold=True)
    d.note(520,'BUG=1 prioritizes push and increments the count to two. Reset at the following observation',
           'masks the interface but does not erase the already observed invariant failure.',
           'This figure rereads preserved evidence; it does not run a new proof or predict another solver trace.')
    d.save()


def memory_map():
    p=json.loads(PROFILE.read_text(encoding='utf-8'))['profile']
    d=Drawing('visual-mmio-map','Decode the address before interpreting the register offset',
              'Selected platform bases only; omitted regions and gaps are not to scale',640)
    d.box(28,115,230,90,'CPU / load-store','physical address',kind='cpu')
    d.box(350,115,230,90,'Address decoder','region + offset',kind='interconnect')
    d.path('M258 160H350')
    for i,(title,line,kind) in enumerate([('UART','0x10000000','peripheral'),('GPIO','0x10060000','peripheral'),
               ('Dot-product MMIO',p['MMIO_BASE'],'accelerator'),('RAM base',p['ram_base'],'memory')]):
        y=95+115*i;d.box(680,y,252,90,title,line,kind=kind,color=GREEN if kind=='memory' else BLUE)
        d.path(f'M580 160H620V{y+45}H680')
    d.note(565,'The accelerator IP receives offsets; the platform supplies its base and decode window.',
           'DMA accesses shared RAM through a separate port. This is not a complete Wally or QEMU memory map.')
    d.save()


def capture_panels():
    records=[]
    sources=sorted({r['image'] for r in __import__('print_audit').inventory() if r['image'].endswith('.png')})
    # Stable inventory also accepts already wrapped chapter placements on regeneration.
    if (FIG/'visual-manifest.json').exists():
        sources=sorted(set(sources)|{r['source'] for r in json.loads((FIG/'visual-manifest.json').read_text())['captures']})
    for source in sources:
        path=ROOT/source;name='visual-capture-'+path.stem
        if '/21-physical-closure/' in source:name+='-repaired'
        is_fpga='fpga' in path.stem or 'nexys' in path.stem
        if is_fpga:
            notes=['1  Read coordinates / resource categories from the axes, not as a die photograph.',
                   '2  Occupied resources do not establish routed timing or measured power.']
        elif 'clock' in path.stem:
            notes=['1  Follow the root-to-leaf topology and the insertion-delay scale in ns.',
                   '2  Hold acceptance also needs data-path delays and the extracted hold report.']
        elif 'critical' in path.stem:
            notes=['1  Locate the highlighted path in the retained routing context.',
                   '2  Identify launch, capture and interface budgets in the linked timing report.']
        elif any(k in path.stem for k in ['placed','cts']):
            notes=['1  Inspect rows, cell distribution and free space; compare the stated utilization.',
                   '2  Placement alone does not include the final signal-wire RC or prove timing.']
        else:
            notes=['1  Inspect the distribution of routed connections and the implementation boundary.',
                   '2  Dense geometry is not a timing, DRC/LVS or power acceptance report.']
        w,h=struct.unpack('>II',path.read_bytes()[16:24]);shown_h=min(630,904*h/w)
        d=Drawing(name,'Read the implementation capture',
                  'Experimental image preserved byte-for-byte inside this SVG; numbered observations are editorial',int(shown_h+275))
        data=base64.b64encode(path.read_bytes()).decode()
        d.parts.append(f'<image x="28" y="90" width="904" height="{shown_h}" preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,{data}"/>')
        d.note(110+shown_h,*notes)
        d.save();records.append(dict(source=source,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),output=name+'.svg',observations=notes))
    return records


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    for draw in [legend,datapath,comparison,verification,scheduling,counterexample,memory_map]:draw()
    captures=capture_panels()
    inputs=[Path(__file__),ROOT/'tools/figures/architecture.py',TRACE,PROFILE]
    record=dict(schema=1,kind='Conceptual SVGs, one retained-trace visualization, and editorial capture wrappers',
                inputs={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
                captures=captures,outputs={n:hashlib.sha256(b).hexdigest() for n,b in outputs.items()})
    outputs['visual-manifest.json']=(json.dumps(record,indent=2)+'\n').encode()
    for name,data in outputs.items():
        if args.check:
            if not (FIG/name).is_file() or (FIG/name).read_bytes()!=data:raise ValueError('Stale visual asset: '+name)
        else:(FIG/name).write_bytes(data)
    print('PASS visual vocabulary:',len(outputs)-1,'SVGs;',len(captures),'unaltered capture inputs')


if __name__=='__main__':main()
