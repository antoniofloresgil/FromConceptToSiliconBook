#!/usr/bin/env python3
"""Plot the actual routed XC7 placement using Project X-Ray tile coordinates."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('run',type=Path)
parser.add_argument('output',type=Path)
args=parser.parse_args()
args.output.parent.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
design=json.loads((args.run/'routed.json').read_text())['modules']['top']
coords=json.loads((args.run/'site-coordinates.json').read_text())['sites']
tiles=Counter();resources=Counter();special={};omitted=Counter()
for cell in design['cells'].values():
    kind=cell['type'];bel=cell.get('attributes',{}).get('NEXTPNR_BEL','')
    site=bel.split('/')[0]
    if site not in coords:
        omitted[kind]+=1;continue
    xy=tuple(coords[site]);resources[kind]+=1
    if site.startswith('SLICE_'):tiles[xy]+=1
    else:special[xy]=kind
if not tiles:raise ValueError('No placed slice cells')
fig,(ax,zoom)=plt.subplots(1,2,figsize=(13,6),layout='constrained')
points=ax.scatter([xy[0] for xy in tiles],[xy[1] for xy in tiles],c=list(tiles.values()),
                  cmap='Blues',marker='s',s=70,edgecolors='#325675',linewidths=.25)
if special:
    ax.scatter([xy[0] for xy in special],[xy[1] for xy in special],marker='D',s=50,
               color='#c93c26',label='Occupied IO / clock tile')
    ax.legend(loc='best')
ax.set(xlabel='Project X-Ray tile grid X',ylabel='Project X-Ray tile grid Y',
       title='Nexys Video XC7A200T: actual placement after routing\nSame dot-product accelerator plus serial boundary fixture')
ax.invert_yaxis();ax.set_aspect('equal');ax.grid(alpha=.18);ax.set_axisbelow(True)
fig.colorbar(points,ax=ax,label='Placed cells per occupied slice tile',shrink=.75)
dense={xy:count for xy,count in tiles.items() if count>=2}
if not dense:raise ValueError('No dense logic region')
zoom.scatter([xy[0] for xy in tiles],[xy[1] for xy in tiles],c=list(tiles.values()),
             cmap='Blues',norm=points.norm,marker='s',s=100,edgecolors='#325675',linewidths=.25)
zoom.set(xlim=(min(x for x,y in dense)-2,max(x for x,y in dense)+2),
         ylim=(max(y for x,y in dense)+2,min(y for x,y in dense)-2),
         title='Dense logic region (crop)',xlabel='Tile grid X',ylabel='Tile grid Y')
zoom.set_aspect('equal');zoom.grid(alpha=.18);zoom.set_axisbelow(True)
fig.savefig(args.output,dpi=180)
metadata={'routed_json_sha256':sha(args.run/'routed.json'),
          'coordinates_sha256':sha(args.run/'site-coordinates.json'),
          'script_sha256':sha(Path(__file__)),'resource_counts':dict(resources),
          'omitted_unlocated_types':dict(omitted),'matplotlib':matplotlib.__version__,
          'view':'occupied tile window in actual Project X-Ray grid; includes fixture; no routed-wire geometry'}
args.output.with_suffix('.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8',newline='\n')
