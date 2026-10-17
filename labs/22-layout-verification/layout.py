"""KLayout preflight and deliberately broken geometry for checker controls."""
import json
from pathlib import Path
import pya

out=Path(out)
source=Path(source)
layout=pya.Layout();layout.read(str(source))
def region(cell, layer):return pya.Region(cell.shapes(layout.layer(layer,0)))
bad=[]
unmarked=[]
for cell in layout.each_cell():
    # All transistor active is implanted; only the known body-tie master has
    # unmarked active. Reject other libraries instead of silently guessing.
    missing=region(cell,1)-(region(cell,4)|region(cell,5))
    if not missing.is_empty():
        unmarked.append(cell.name)
        if cell.name!='TAPCELL_X1':bad.append(cell.name)
    for layer in [6,7,8]:
        if not region(cell,layer).is_empty():bad.append(cell.name+':unexpected VT marker')
if bad:raise RuntimeError('Unsupported device/implant convention: '+str(bad))
top=layout.top_cell()
# A single 1 nm wide M2 sliver outside the core must trigger width/grid checks.
top.shapes(layout.layer(13,0)).insert(pya.Box(-10000,-10000,-9990,0))
layout.write(str(out/'bad-drc.gds'))
# The LVS control joins the two existing M1 supply rails through a cell.
# Coordinates derive from actual labelled VDD/VSS pin positions and placement.
layout=pya.Layout();layout.read(str(source));top=layout.top_cell()
chosen=None
for inst in top.each_inst():
    cell=inst.cell
    if cell.name=='INV_X1':
        points={s.text.string:inst.trans*pya.Point(s.text.trans.disp.x,s.text.trans.disp.y) for s in cell.shapes(layout.layer(11,0)).each() if s.is_text()}
        if 'VDD' in points and 'VSS' in points:chosen=points;break
if chosen is None:raise RuntimeError('Missing cell for the negative control')
a,b=chosen['VDD'],chosen['VSS']
top.shapes(layout.layer(11,0)).insert(pya.Box(min(a.x,b.x)-100,min(a.y,b.y)-100,max(a.x,b.x)+100,max(a.y,b.y)+100))
layout.write(str(out/'bad-lvs.gds'))
(out/'layout-preflight.json').write_text(json.dumps({'unsupported':bad,'unmarked_active_masters':sorted(unmarked),
  'device_flavour':'Nangate VTL, absent VT-marker layers checked',
  'negative_drc':'1 nm M2 sliver','negative_lvs':'geometrical VDD/VSS metal1 bridge at an actual INV_X1'},indent=2)+'\n')
