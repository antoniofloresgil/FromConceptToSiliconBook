"""Optional authoring helper (Matplotlib); all data must be illustrative."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('summary',type=Path)
parser.add_argument('output',type=Path)
args=parser.parse_args()
rows=json.loads(args.summary.read_text())
if any(row['origin']!='illustrative' for row in rows):raise ValueError('This book figure is restricted to illustrative data')
plt.rcParams.update({'svg.fonttype':'none','font.size':11})
fig,ax=plt.subplots(figsize=(8,4.5),layout='constrained')
for row in rows:
    if row['status']!='feasible':continue
    x,y=row['lut'],row['geomean_time_us']
    ax.scatter(x,y,color='#167d8d' if row['pareto'] else '#888888',s=85,zorder=3)
    ax.annotate(row['candidate'],(x,y),xytext=(10,8),textcoords='offset points')
ax.set(xlabel='LUT cost (illustrative units)',ylabel='Geometric-mean time (µs)',
       xlim=(15000,39000),ylim=(250,390),title='Illustrative trade-offs — not Wally FPGA measurements')
ax.grid(alpha=.25)
fig.text(.5,-.025,'Teal: nondominated in time/LUT/BRAM/DSP. Grey: dominated. Budget failure omitted.',ha='center',fontsize=9)
args.output.parent.mkdir(parents=True,exist_ok=True)
fig.savefig(args.output,bbox_inches='tight')
if args.output.suffix.lower()=='.svg':
    text=args.output.read_text(encoding='utf-8')
    args.output.write_text('\n'.join(line.rstrip() for line in text.splitlines())+'\n',encoding='utf-8',newline='\n')
