"""Collect portable evidence from real positive and mutation pipeline runs."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('results',type=Path)
p.add_argument('--reference-dir',type=Path,default=HERE/'reference')
a=p.parse_args();ref=a.reference_dir.resolve();ref.mkdir(parents=True,exist_ok=False)
negative=json.loads((a.results/'negative/negative-results.json').read_text())
shutil.copyfile(a.results/'negative/negative-results.json',ref/'negative-results.json')
for name,source in [('positive',a.results/'positive')]+[(n,a.results/'negative'/n/'run') for n in negative]:
    r=json.loads((source/'report.json').read_text())
    if name=='positive' and r['status']!='pass':raise ValueError('Baseline failed')
    if r['runner_sha256']!=sha(HERE/'run.py') or r['policy_sha256']!=sha(HERE/'policy.json'):
        raise ValueError('Stale pipeline or policy')
    dest=ref/name;dest.mkdir()
    shutil.copyfile(source/'report.json',dest/'report.json')
    for raw,digest in r['artifacts'].items():
        f=source/raw
        if sha(f)!=digest:raise ValueError('Changed raw artifact: '+raw)
        if f.suffix not in {'.txt','.log','.json','.vcd','.py','.sv','.svh','.sdc','.c','.S','.ld','.hex'}:continue
        target=dest/raw
        if target.suffix=='.log':target=target.with_suffix('.txt')
        if target.suffix=='.vcd':target=target.with_suffix('.vcd.txt')
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(f,target)
sources=[p for p in HERE.iterdir() if p.suffix in {'.py','.json'}]
sources += [ROOT/'.github/workflows'/n for n in ['hardware-ci.yml','physical-regression.yml','publish.yml']]
(ref/'workflows').mkdir()
for f in sources:
    if f.suffix=='.yml':shutil.copyfile(f,ref/'workflows'/f.name)
inventory=dict(sources={f.relative_to(ROOT).as_posix():sha(f) for f in sources},
               artifacts={f.relative_to(ref).as_posix():sha(f) for f in ref.rglob('*') if f.is_file()})
(ref/'inventory.json').write_text(json.dumps(inventory,indent=2,sort_keys=True)+'\n')
print('COLLECTED five actual pipelines with commands, netlists, witness and counterexample')
