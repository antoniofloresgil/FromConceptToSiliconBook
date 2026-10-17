#!/usr/bin/env python3
"""Check that the independent regression rejects a pipeline sign-extension bug."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

here=Path(__file__).resolve().parent
root=here.parents[1]
out=(root/sys.argv[1]).resolve()
if not out.is_relative_to(root/'labs/build') or out.exists(): raise ValueError('Use fresh labs/build path')
out.mkdir(parents=True)
src=root/'labs/10-dotproduct'
engine=here/'dotproduct_engine.sv'
text=engine.read_text()
old='{{32{product_q[31]}}, product_q}'
assert text.count(old)==1
(out/'bad-engine.sv').write_text(text.replace(old,"{32'b0, product_q}"))
commands=[['python3',str(src/'vectors.py'),str(out),'2026'],
          ['iverilog','-g2012','-I',str(src),'-s','tb_dotproduct','-o','simulation',
           str(src/'rtl/dotproduct_mac.sv'),str(out/'bad-engine.sv'),str(src/'rtl/dotproduct_axi.sv'),str(src/'axi_ram_model.sv'),str(src/'tb_dotproduct.sv')],
          ['vvp','simulation']]
codes=[]
for i,argv in enumerate(commands):
    with (out/f'command-{i+1:02d}.txt').open('w') as f:
        v=subprocess.run(argv,cwd=out,stdout=f,stderr=subprocess.STDOUT,timeout=120)
    codes.append(v.returncode)
    if i<2 and v.returncode: raise RuntimeError('Negative control setup failed')
log=(out/'command-03.txt').read_text()
if not codes[-1] or 'Arithmetic/status mismatch' not in log: raise RuntimeError('Bug was not detected as intended')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
r={'status':'pass','expected_failure':'lost sign extension of negative product','commands':commands,'exit_codes':codes,
   'sources':{p.relative_to(root).as_posix():sha(p) for p in [here/'negative.py',engine,src/'vectors.py',src/'tb_dotproduct.sv',src/'axi_ram_model.sv',src/'axi_connections.svh',src/'rtl/dotproduct_mac.sv',src/'rtl/dotproduct_axi.sv']},
   'artifacts':{p.name:sha(p) for p in out.iterdir() if p.is_file()}}
(out/'negative.json').write_text(json.dumps(r,indent=2)+'\n')
print('PASS negative control: arithmetic defect rejected')
