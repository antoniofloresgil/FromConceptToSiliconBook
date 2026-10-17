#!/usr/bin/env python3
"""Plot actual occupied nextpnr BEL coordinates, not an invented FPGA floorplan."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('routed_json',type=Path)
parser.add_argument('output',type=Path)
args=parser.parse_args()
design=json.loads(args.routed_json.read_text())
require_types={'TRELLIS_COMB','TRELLIS_FF','MULT18X18D'}
tiles=Counter(); dsps=[]; resources=Counter()
for module in design['modules'].values():
    for cell in module['cells'].values():
        kind=cell['type']
        if kind not in require_types: continue
        bel=cell.get('attributes',{}).get('NEXTPNR_BEL','')
        match=re.match(r'X(\d+)/Y(\d+)/',bel)
        if not match: raise ValueError('Missing placed BEL for '+kind)
        x,y=map(int,match.groups());resources[kind]+=1
        if kind=='MULT18X18D': dsps.append((x,y))
        else: tiles[x,y]+=1
coords=list(tiles)+dsps
xmin=min(x for x,y in coords)-1;xmax=max(x for x,y in coords)+1
ymin=min(y for x,y in coords)-1;ymax=max(y for x,y in coords)+1
fig,ax=plt.subplots(figsize=(12,6),layout='constrained')
normalizer=plt.Normalize(vmin=0,vmax=max(tiles.values()))
for (x,y),count in tiles.items():
    ax.add_patch(Rectangle((x-.45,y-.45),.9,.9,facecolor=plt.cm.Blues(normalizer(count)),edgecolor='#325675',linewidth=.35))
for x,y in dsps:
    ax.scatter([x],[y],marker='D',s=170,color='#c93c26',edgecolors='black',zorder=4,label='DSP BEL anchor')
ax.set(xlim=(xmin,xmax),ylim=(ymax,ymin),xlabel='nextpnr BEL X coordinate',ylabel='nextpnr BEL Y coordinate',
       title='Same dot-product RTL: actual ECP5 placement after routing\nOccupied coordinate window; colors count COMB + FF BELs per tile')
ax.set_aspect('equal');ax.grid(alpha=.18);ax.set_axisbelow(True)
fig.colorbar(plt.cm.ScalarMappable(norm=normalizer,cmap='Blues'),ax=ax,label='Occupied COMB + FF BELs at (X,Y)',shrink=.8)
if dsps: ax.legend(loc='upper left')
fig.savefig(args.output,dpi=180)
metadata={'source_json_sha256':hashlib.sha256(args.routed_json.read_bytes()).hexdigest(),
          'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'matplotlib':matplotlib.__version__,'resource_counts':dict(resources),
          'view':'occupied BEL coordinate window; no routed wires or physical DSP footprint shown'}
args.output.with_suffix('.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8',newline='\n')
