"""Analyse a matched illustrative/physical campaign without inventing missing results."""
import argparse
import csv
import html
import json
import math
from pathlib import Path
import statistics

def analyse(rows,baseline,lut_limit,bram_limit):
    groups={}
    for row in rows:groups.setdefault(row['candidate'],[]).append(row)
    if baseline not in groups:raise ValueError('Baseline candidate is missing')
    base={r['workload']:r for r in groups[baseline]}
    if len(base)!=len(groups[baseline]):raise ValueError('Duplicate baseline workloads')
    summary=[]
    for candidate,records in groups.items():
        item={'candidate':candidate,'status':'rejected','reason':'','origin':records[0]['origin']}
        summary.append(item)
        if any(r['status']!='pass' or r['timing_status']!='pass' for r in records):
            item['reason']='Functional/timing qualification is incomplete or failed';continue
        if {r['workload'] for r in records}!=set(base) or len(records)!=len(base):
            raise ValueError('Every candidate requires exactly the same workload set')
        for field in ('lut','bram','dsp','frequency_mhz','target','origin'):
            if len({r[field] for r in records})!=1:raise ValueError(f'Inconsistent candidate {field}')
        lut,bram,dsp=(float(records[0][k]) for k in ('lut','bram','dsp'))
        if not all(math.isfinite(x) and x>=0 for x in (lut,bram,dsp)):raise ValueError('Invalid resource value')
        if lut>lut_limit or bram>bram_limit:
            item['reason']='Resource budget exceeded';continue
        speedups=[];times=[]
        for row in records:
            reference=base[row['workload']]
            for key in ('binary_sha256','roi','input_sha256','target','origin'):
                if row[key]!=reference[key]:raise ValueError(f'Unmatched workload or evidence origin: {key}')
            if reference['status']!='pass' or reference['timing_status']!='pass':raise ValueError('Baseline is not qualified')
            if row['frequency_basis']!='achieved' or reference['frequency_basis']!='achieved':
                raise ValueError('Elapsed-time comparisons require achieved frequency')
            cycles,freq,base_cycles,base_freq=map(float,(row['cycles'],row['frequency_mhz'],reference['cycles'],reference['frequency_mhz']))
            if not all(math.isfinite(x) and x>0 for x in (cycles,freq,base_cycles,base_freq)):raise ValueError('Invalid cycle/frequency value')
            time=cycles/freq
            times.append(time);speedups.append((base_cycles/base_freq)/time)
        geomean_speedup=math.exp(statistics.mean(math.log(s) for s in speedups))
        geomean_time=math.exp(statistics.mean(math.log(t) for t in times))
        item.update(status='feasible',lut=lut,bram=bram,dsp=dsp,
                    geomean_speedup=geomean_speedup,geomean_time_us=geomean_time,
                    worst_workload_speedup=min(speedups),pareto=True)
    feasible=[r for r in summary if r['status']=='feasible']
    for row in feasible:
        metrics=('geomean_time_us','lut','bram','dsp')
        row['pareto']=not any(other is not row and all(other[m]<=row[m] for m in metrics)
                             and any(other[m]<row[m] for m in metrics) for other in feasible)
    return summary

def plot(rows,path):
    points=[r for r in rows if r['status']=='feasible']
    if not points:return
    maxx=max(p['lut'] for p in points)*1.15 or 1
    maxy=max(p['geomean_time_us'] for p in points)*1.2
    chunks=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 480">',
            '<rect width="800" height="480" fill="white"/>',
            '<g font-family="sans-serif" fill="#202a36">',
            '<text x="40" y="30" font-size="20">ILLUSTRATIVE DATA — not Wally FPGA measurements</text>',
            '<path d="M80 60V400H750" fill="none" stroke="#334455"/>',
            '<text x="350" y="460">LUT cost (smaller is better)</text>',
            '<text x="15" y="240" transform="rotate(-90 15 240)">Geometric-mean time (µs)</text>']
    for tick in range(5):
        x=80+tick*670/4;y=400-tick*340/4
        chunks.append(f'<text x="{x-15}" y="425">{maxx*tick/4:.0f}</text>')
        chunks.append(f'<text x="30" y="{y+4}">{maxy*tick/4:.1f}</text>')
    for row in points:
        x=80+670*row['lut']/maxx;y=400-340*row['geomean_time_us']/maxy
        color='#167d8d' if row['pareto'] else '#888888'
        chunks.append(f'<circle cx="{x}" cy="{y}" r="7" fill="{color}"/>')
        chunks.append(f'<text x="{x+12}" y="{y-10}">{html.escape(row["candidate"])}</text>')
    chunks.append('<text x="80" y="445">Teal: nondominated in time/LUT/BRAM/DSP; grey: dominated</text></g></svg>')
    path.write_text('\n'.join(chunks),encoding='utf-8')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--baseline',default='base')
    parser.add_argument('--lut-limit',type=float,default=50000)
    parser.add_argument('--bram-limit',type=float,default=150)
    args=parser.parse_args()
    with args.input.open(newline='',encoding='utf-8') as source:rows=list(csv.DictReader(source))
    result=analyse(rows,args.baseline,args.lut_limit,args.bram_limit)
    args.output_dir.mkdir(parents=True,exist_ok=True)
    (args.output_dir/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    # This plot is specifically the pedagogical dataset, not arbitrary data.
    if {r['origin'] for r in rows}=={'illustrative'}:plot(result,args.output_dir/'pareto.svg')
    for r in result:
        if r['status']=='feasible':print(f'{r["candidate"]}: speedup={r["geomean_speedup"]:.3f}, Pareto={r["pareto"]}')
        else:print(f'{r["candidate"]}: rejected — {r["reason"]}')

if __name__=='__main__':
    try:main()
    except (ValueError,KeyError,OSError) as error:raise SystemExit(f'FAIL analysis: {error}')
