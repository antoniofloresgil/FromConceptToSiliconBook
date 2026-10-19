import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path('/work');OUT=ROOT/'labs/build'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
names=subprocess.check_output(['git','-c','safe.directory=/work','ls-files','-z'],cwd=ROOT).decode().split('\0')
inventory={n:sha(ROOT/n) for n in names if n}
revision=subprocess.check_output(['git','-c','safe.directory=/work','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
kind=sys.argv[1]
if kind=='before':
    (OUT/'audit-source-before.json').write_text(json.dumps(dict(revision=revision,files=inventory),indent=2)+'\n')
else:
    old=json.loads((OUT/'audit-source-before.json').read_text())
    assert old['revision']==revision and old['files']==inventory,'Source/reference changed during audit'
    (OUT/'audit-source-after.json').write_text(json.dumps(dict(revision=revision,files=inventory),indent=2)+'\n')
print('PASS immutable sources:',revision,len(inventory),'tracked files;',sum('/reference/' in n for n in inventory),'reference artifacts')
