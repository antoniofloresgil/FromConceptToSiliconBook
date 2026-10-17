#!/usr/bin/env python3
"""Prove the repaired cell netlist equivalent to its mapped input, at zero delay."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

out = Path(sys.argv[1]).resolve()
root = Path(__file__).resolve().parents[2]
if not out.is_relative_to(root/'labs/build'): raise ValueError('Expected labs/build')
lib = Path('/OpenROAD-flow-scripts/flow/platforms/nangate45/lib/NangateOpenCellLibrary_typical.lib')
script = ''
for net, name in [('mapped','gold'),('routed','gate')]:
    script += f'read_liberty -ignore_miss_func {lib}; read_verilog {out}/{net}.v; hierarchy -check -top dotproduct_axi; flatten; proc; opt; check -assert; rename dotproduct_axi {name}; design -stash {name}; '
script += 'design -copy-from gold -as gold gold; design -copy-from gate -as gate gate; equiv_make gold gate equiv; hierarchy -top equiv; equiv_simple; equiv_induct -seq 5; equiv_status -assert'
argv = ['yosys','-Q','-T','-p',script]
with (out/'equivalence.log').open('w') as f:
    result = subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,timeout=1200)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
r = dict(status='pass' if result.returncode == 0 else 'fail', command=argv, exit_code=result.returncode,
         scope='Mapped versus repaired routed cell netlist, zero-delay functional model; not extracted LVS or baseline/pipelined sequential equivalence',
         inputs={p.name:sha(p) for p in [out/'report.json',out/'mapped.v',out/'routed.v',lib]},
         recipe_sha256=sha(Path(__file__)), log_sha256=sha(out/'equivalence.log'))
(out/'equivalence.json').write_text(json.dumps(r,indent=2)+'\n')
if result.returncode: raise SystemExit('Netlist equivalence failed; inspect equivalence.log')
print('PASS mapped/routed zero-delay equivalence')
