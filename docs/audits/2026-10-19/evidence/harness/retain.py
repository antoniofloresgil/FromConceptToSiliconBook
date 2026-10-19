import hashlib,json,shutil
from pathlib import Path
base=Path(__file__).resolve().parent
repo=base.parents[2];dest=repo/'docs/audits/2026-10-19/evidence'
assert not dest.exists(),'Fresh retained evidence required'
# The previous docker cp exports to a separate temporary directory.
shutil.copytree(base/'exported',dest)
receipts=[]
for p in sorted(base.glob('*.json')):
 data=json.loads(p.read_text())
 if 'argv' not in data:continue
 log=base/data['log'];assert hashlib.sha256(log.read_bytes()).hexdigest()==data['log_sha256'],p
 receipts.append(data)
 target=dest/'commands'/log.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(log,target)
dispositions={
 'inventory-before':dict(kind='audit setup correction',superseded_by='inventory-before-owned'),
 'reject-closure':dict(kind='audit probe argument correction',superseded_by='reject-closure-confirmed'),
 'environment-asic':dict(kind='audit headless version-query correction',superseded_by='environment-asic-headless'),
 'missing-tools':dict(kind='expected rejection',confirmed_by='confirm-missing-tools',expected_exit_code=1)}
for r in receipts:
 if r['status']!='pass':
  assert r['name'] in dispositions,('Unresolved command failure',r['name'])
  d=dispositions[r['name']]
  replacement=d.get('superseded_by',d.get('confirmed_by'))
  assert any(x['name']==replacement and x['status']=='pass' for x in receipts)
  if 'expected_exit_code' in d:assert r['exit_code']==d['expected_exit_code']
(dest/'command-dispositions.json').write_text(json.dumps(dispositions,indent=2)+'\n')
(dest/'commands.json').write_text(json.dumps(receipts,indent=2)+'\n')
shutil.copyfile(base/'host.json',dest/'host.json')
for p in base.glob('*.py'):
 target=dest/'harness'/p.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
for p in (repo/'tools/reproducibility').glob('*.py'):
 target=dest/'integrity-tools'/p.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
files={p.relative_to(dest).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(dest.rglob('*')) if p.is_file()}
(dest/'inventory.json').write_text(json.dumps(dict(schema=1,files=files),indent=2)+'\n')
print('RETAINED',len(files),'files;',sum(p.stat().st_size for p in dest.rglob('*') if p.is_file()),'bytes')
