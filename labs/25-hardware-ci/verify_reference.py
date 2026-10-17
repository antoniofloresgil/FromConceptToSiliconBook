"""Audit the recorded pipeline evidence, not a fresh EDA or hosted CI run."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
REF=HERE/'reference'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
inv=json.loads((REF/'inventory.json').read_text())
for name,digest in inv['sources'].items():
    p=ROOT/name
    # Workflow snapshots travel inside the practice ZIP; book publishing stays in the repository.
    if name.startswith('.github/') and not p.exists():p=REF/'workflows'/Path(name).name
    assert sha(p)==digest,('stale recipe',name)
for name,digest in inv['artifacts'].items():assert sha(REF/name)==digest,('artifact',name)
policy=json.loads((HERE/'policy.json').read_text())
assert policy['baseline_generic_cells']==5662 and policy['maximum_generic_cells']==5946
expected={'contract':'Elaboration','arithmetic':'Simulation','assertion':'Formal','cell-growth':'Reports'}
negative=json.loads((REF/'negative-results.json').read_text())
assert set(negative)==set(expected)
spec=importlib.util.spec_from_file_location('pipeline',HERE/'run.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
for name in ['positive',*expected]:
    folder=REF/name;r=json.loads((folder/'report.json').read_text())
    assert r['runner_sha256']==sha(HERE/'run.py') and r['policy_sha256']==sha(HERE/'policy.json')
    assert r['contract_sha256']==sha(HERE/'contract.json') and r['tools']==policy['tool_versions']
    assert r['image_id'].startswith('sha256:')
    assert [s['name'] for s in r['stages']]==module.STAGES
    for raw,digest in r['sources'].items():
        assert sha(folder/'input'/raw)==digest,(name,raw)
        if name=='positive' or not raw.startswith('rtl/'):
            assert sha(ROOT/'labs/10-dotproduct'/raw)==digest,('stale input',raw)
    for raw,digest in r['artifacts'].items():
        p=folder/raw
        if p.suffix=='.log':p=p.with_suffix('.txt')
        if p.suffix=='.vcd':p=p.with_suffix('.vcd.txt')
        if p.exists():assert sha(p)==digest,(name,raw)
    if name=='positive':
        assert r['status']=='pass' and all(s['status']=='pass' for s in r['stages'])
        assert all(c['returncode']==0 for c in r['commands'])
        assert json.loads((folder/'interface.json').read_text())==json.loads((HERE/'contract.json').read_text())
        assert (folder/'done-witness.vcd.txt').stat().st_size>0
        for filename,marker in [('formal.txt','SUCCESS'),('engine-proof.txt','SUCCESS'),('done-witness.txt','model found')]:
            assert marker in (folder/filename).read_text(),filename
    else:
        assert r['status']=='fail'
        failed=[s for s in r['stages'] if s['status']=='fail']
        assert len(failed)==1 and failed[0]['name']==expected[name]
        assert negative[name]['stage']==expected[name] and negative[name]['status']=='rejected'
    if name in ['positive','cell-growth']:
        net=json.loads((folder/'synthesized.json').read_text())['modules']['dotproduct_axi']
        counts=Counter(c['type'] for c in net['cells'].values())
        assert r['metrics']['generic_cells']==sum(counts.values())
        assert r['metrics']['cell_types']==dict(counts)
        assert sum(counts.values())==(5662 if name=='positive' else 6668)
        assert ('$dlatch' not in counts)
assert (REF/'assertion/formal-counterexample.vcd.txt').stat().st_size>0
print('PASS integrated hardware CI: six stages, fixed interface, bounded proofs/witness, 5662-cell baseline, four actual rejected mutations (6668 > 5946); no hosted-CI or physical-run claim')
