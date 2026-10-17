"""KLayout batch script: merge real cell GDS into the routed DEF, then reopen it."""
import json
from pathlib import Path
import pya

out = Path(out)  # Supplied by KLayout -rd, not the host Python runner.
platform = Path('/OpenROAD-flow-scripts/flow/platforms/nangate45')
technology = pya.Technology()
technology.load(str(platform/'FreePDK45.lyt'))
options = technology.load_layout_options
options.lefdef_config.lef_files = [str(platform/'lef/NangateOpenCellLibrary.tech.lef'),
                                 str(platform/'lef/NangateOpenCellLibrary.macro.mod.lef')]
layout = pya.Layout()
layout.read(str(out/'routed.def'), options)
top = layout.cell('dotproduct_axi')
for cell in layout.each_cell():
    if cell != top and not cell.name.startswith('VIA_') and not cell.name.endswith('_DEF_FILL'):
        cell.clear()
layout.read(str(platform/'gds/NangateOpenCellLibrary.gds'))
final = pya.Layout()
final.dbu = layout.dbu
final.create_cell('dotproduct_axi').copy_tree(layout.cell('dotproduct_axi'))
empty = [cell.name for cell in final.each_cell() if cell.is_empty()]
if empty:
    raise RuntimeError('Unresolved cell geometry: '+str(empty))
final.write(str(out/'dotproduct_axi.gds'))
check = pya.Layout()
check.read(str(out/'dotproduct_axi.gds'))
if len(check.top_cells()) != 1 or check.top_cell().name != 'dotproduct_axi':
    raise RuntimeError('Unexpected stream-out hierarchy')
box = check.top_cell().bbox()
record = {'top': check.top_cell().name, 'cells': check.cells(), 'dbu_um': check.dbu,
          'bbox_um': [v*check.dbu for v in [box.left,box.bottom,box.right,box.top]],
          'empty_cells': empty, 'validation': 'readback and nonempty cell geometry; no DRC/LVS claim'}
(out/'gds-readback.json').write_text(json.dumps(record, indent=2)+'\n')
print('PASS GDS stream-out/readback:', record)
