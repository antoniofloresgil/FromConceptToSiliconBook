#!/usr/bin/env python3
"""Export actual repaired OpenROAD layout, critical path and clock tree."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

root=Path(__file__).resolve().parents[2]
out=(root/sys.argv[1]).resolve()
if not out.is_relative_to(root/'labs/build'):raise ValueError('Expected labs/build')
recipe=root/'labs/17-complete-case/asic-images.tcl'
env={**os.environ,'CASE_OUT':str(out),'QT_QPA_PLATFORM':'offscreen'}
argv=['openroad','-gui','-no_init','-exit',str(recipe)]
with (out/'capture.log').open('w') as f:
    subprocess.run(argv,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=180)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
r=dict(command=argv,recipe_sha256=sha(recipe),capture_sha256=sha(Path(__file__)),
       inputs={p.name:sha(p) for p in [out/'report.json',out/'routed.odb',out/'routed.sdc',out/'routed.spef']},
       images={n:sha(out/n) for n in ['implementation.png','critical-path.png','clocktree.png']})
(out/'capture.json').write_text(json.dumps(r,indent=2)+'\n')
print('CAPTURED actual repaired physical database')
