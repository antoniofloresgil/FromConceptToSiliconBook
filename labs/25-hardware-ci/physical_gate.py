"""Accept only the scoped Lab 21 repaired-block timing/electrical gate."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

root=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('closure_collect',root/'labs/21-physical-closure/collect.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
out=Path(sys.argv[1]).resolve()
r=json.loads((out/'report.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert r['status']=='completed' and r['target']=='asic' and r['candidate']=='repair'
assert r['requested_mhz']==100 and all(c['exit_code']==0 for c in r['commands'])
for name,digest in r['sources'].items(): assert sha(root/name)==digest,('stale source',name)
for name,digest in r['artifacts'].items(): assert sha(out/name)==digest,('changed artifact',name)
t=module.summarize(out,r)
eq=json.loads((out/'equivalence.json').read_text())
assert eq['status']=='pass' and eq['exit_code']==0
assert eq['recipe_sha256']==sha(root/'labs/21-physical-closure/verify_netlist.py')
assert eq['log_sha256']==sha(out/'equivalence.log')
for name in ['mapped.v','routed.v','report.json']: assert eq['inputs'][name]==sha(out/name)
assert t['model']=='openrcx_propagated_clock'
assert t['timing_electrical_pass'] and t['router_drc_empty'] and not t['gds_readback']['empty_cells']
t.update(accepted=True,manufacturing_qualified=False,
         scope='Nangate45 typical, 100 MHz accelerator block; no manufacturing or whole-SoC signoff')
(out/'ci-acceptance.json').write_text(json.dumps(t,indent=2)+'\n')
print('PASS scoped physical block gate',t['setup_ns'],t['hold_ns'])
