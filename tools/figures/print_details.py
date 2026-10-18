"""Generate overlapping original-source detail views and a labeled grayscale plot.

The pipeline panels retain the Harris source and its license/attribution scope.
They crop its viewBox only; no circuit geometry or text is reconstructed.
"""
import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import re
from html import escape

ROOT=Path(__file__).resolve().parents[2]
FIG=ROOT/'figures'


def generate():
    source=FIG/'wally-figure-7-13-editable.svg'
    original=source.read_text(encoding='utf-8')
    result={}
    for i,(x,w) in enumerate([(56,190),(220,190),(384,184)],1):
        text=re.sub(r'viewBox="[^"]+"',f'viewBox="{x} 75 {w} 306"',original,count=1)
        text=re.sub(r'width="1024" height="612"',f'width="{w}" height="306"',text,count=1)
        text=text.replace('<defs>',f'<title>Harris Figure 7.13: overlapping detail {i} of 3</title>\n<defs>',1)
        result[f'wally-pipeline-detail-{i}.svg']=text
    # Use the same analysis function and teaching CSV as the existing chapter.
    module=ROOT/'labs/11-dse/analyse.py'
    spec=importlib.util.spec_from_file_location('dse_analysis',module)
    analysis=importlib.util.module_from_spec(spec);spec.loader.exec_module(analysis)
    with (ROOT/'labs/11-dse/illustrative.csv').open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    data=analysis.analyse(rows,'base',50000,150)
    points=[r for r in data if r['status']=='feasible']
    s=['<svg xmlns="http://www.w3.org/2000/svg" width="800" height="500" viewBox="0 0 800 500" role="img">',
       '<title>Illustrative design trade-offs: labeled candidates and distinct markers</title>',
       '<rect width="800" height="500" fill="white"/>',
       '<g font-family="Arial,sans-serif" font-size="20" fill="#182b43">',
       '<text x="25" y="32" font-weight="bold">ILLUSTRATIVE DATA — not Wally measurements</text>',
       '<path d="M90 65V370H750" fill="none" stroke="#172b3a" stroke-width="2"/>']
    maxx=max(r['lut'] for r in points)*1.15;maxy=max(r['geomean_time_us'] for r in points)*1.2
    for tick in range(5):
        x=90+660*tick/4;y=370-305*tick/4
        s += [f'<text x="{x}" y="398" text-anchor="middle">{maxx*tick/4:.0f}</text>',
              f'<text x="78" y="{y+6}" text-anchor="end">{maxy*tick/4:.0f}</text>']
    for row in points:
        x=90+660*row['lut']/maxx;y=370-305*row['geomean_time_us']/maxy
        if row['pareto']:mark=f'<circle cx="{x}" cy="{y}" r="8" fill="#172b3a"/>'
        else:mark=f'<rect x="{x-8}" y="{y-8}" width="16" height="16" fill="white" stroke="#172b3a" stroke-width="2"/>'
        s += [mark,f'<text x="{x+14}" y="{y-12}">{escape(row["candidate"])}</text>']
    s += ['<text x="420" y="430" text-anchor="middle">LUT cost (smaller is better)</text>',
          '<text x="24" y="230" transform="rotate(-90 24 230)" text-anchor="middle">Geometric-mean time (µs)</text>',
          '<text x="35" y="464">● nondominated; □ dominated in time / LUT / BRAM / DSP</text>',
          '</g></svg>']
    result['dse-print-pareto.svg']='\n'.join(s)+'\n'
    inputs=[source,module,ROOT/'labs/11-dse/illustrative.csv',Path(__file__)]
    manifest=dict(schema=1,inputs={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
                  outputs={name:hashlib.sha256(text.encode()).hexdigest() for name,text in result.items()})
    result['print-details-manifest.json']=json.dumps(manifest,indent=2)+'\n'
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');args=p.parse_args()
    for name,text in generate().items():
        path=FIG/name
        if args.check:
            if not path.is_file() or path.read_text(encoding='utf-8')!=text:raise ValueError('Stale print detail: '+name)
        else:path.write_text(text,encoding='utf-8',newline='\n')
    print('PASS print details: three attributed pipeline crops and one shape-coded teaching plot')


if __name__=='__main__':main()
