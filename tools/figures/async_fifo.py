#!/usr/bin/env python3
"""Original CDC ownership diagram in the book's common architectural style."""
from pathlib import Path
from architecture import Drawing,outputs,BLUE,GREEN,ORANGE

d=Drawing('async-fifo-ownership','Asynchronous FIFO: publish ownership, retain the word',
          'Only registered Gray pointers cross through synchronizers; payloads use shared storage',650)
d.rect(28,95,430,365,BLUE)
d.text(48,126,'Write domain: wclk',bold=True)
d.rect(502,95,430,365,GREEN)
d.text(522,126,'Read domain: rclk',bold=True)
d.box(48,150,390,85,'Write pointer + full flag','binary address / registered Gray','advance only on w_valid && w_ready')
d.box(522,150,390,85,'Read pointer + empty flag','binary address / registered Gray','advance only on r_valid && r_ready',color=GREEN)
d.box(522,275,390,75,'W Gray: stage 1 → stage 2','sampled by rclk; compare for empty',color=GREEN)
d.box(48,360,390,75,'R Gray: stage 1 → stage 2','sampled by wclk; compare for full')
d.path('M438 175H485V312H522',ORANGE,dashed=True)
d.path('M522 210H472V398H438',ORANGE,dashed=True)
d.path('M230 360V235')
d.path('M715 275V235',GREEN)
d.box(260,490,440,75,'Shared DATA_W × DEPTH array','write port + combinational read port',color=GREEN)
d.path('M48 192H12V527H260')
d.text(140,512,'w_data',size=18)
d.path('M700 527H925V194H912',GREEN)
d.text(795,512,'r_data',size=18)
d.note(585,'Full and empty are conservative local views. Common reset starts a new empty epoch.',
       'A synchronous-read RAM needs a different read adapter; Gray coding does not qualify physical routing.')
d.save()
target=Path(__file__).resolve().parents[2]/'figures/async-fifo-ownership.svg'
target.write_bytes(outputs['async-fifo-ownership.svg'])
print('GENERATED',target)
