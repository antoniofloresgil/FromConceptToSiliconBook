import hashlib
import json
from pathlib import Path
import shutil
import subprocess

base=Path(__file__).resolve().parent;root=base.parents[2]
dest=root/'docs/audits/2026-10-19/follow-up/evidence'
assert not dest.exists(),'Fresh retained evidence required'
shutil.copytree(base/'exported',dest/'raw')
review=json.loads((base/'publication-final-review.json').read_text(encoding='utf-8'))
assert review['status']=='pass'
release=root/review['release']
assert hashlib.sha256((release/'From-Concept-to-Silicon.pdf').read_bytes()).hexdigest()==review['pdf_sha256']
actual_image=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}','from-concept-audit-book:20261019'],text=True).strip()
assert review['image_id']==actual_image
shutil.copyfile(release/'build-manifest.json',dest/'book-build-manifest.json')
for name in ['publication-review.json','publication-final-review.json','visual-sample-pages.json','visual-review-notes.json',
             'book-source-before.json','book-source-corrected.json']:
    shutil.copyfile(base/name,dest/name)
shutil.copyfile(base/'figure-review/inventory.json',dest/'figure-inventory.json')
receipts=[]
for path in sorted(base.glob('*.json')):
    r=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(r,dict) or 'argv' not in r:continue
    log=base/r['log'];assert hashlib.sha256(log.read_bytes()).hexdigest()==r['log_sha256']
    receipts.append(r)
    target=dest/'commands'/log.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(log,target)
dispositions={
    'wally-prepare':dict(kind='not accepted despite exit zero: initial audit shell prechecks failed',superseded_by='wally-prepare-confirmed'),
    'wally-compile':dict(kind='initial audit output-path error',superseded_by='wally-compile-confirmed'),
    'book-render':dict(kind='working-tree appendix encoding error corrected',superseded_by='book-render-confirmed')}
for r in receipts:
    if r['status']!='pass':assert r['name'] in dispositions,('Unclassified failure',r['name'])
for name,data in dispositions.items():
    assert any(r['name']==data['superseded_by'] and r['status']=='pass' for r in receipts),name
for name in ['wally-boot-confirmed','wally-acceptance','publication-pdf-links','figure-proofs-confirmed']:
    assert any(r['name']==name and r['status']=='pass' for r in receipts),name
(dest/'commands.json').write_text(json.dumps(receipts,indent=2)+'\n',encoding='utf-8')
(dest/'command-dispositions.json').write_text(json.dumps(dispositions,indent=2)+'\n',encoding='utf-8')
for path in [*base.glob('*.py'),base/'prepare.sh']:
    target=dest/'harness'/path.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
inventory={p.relative_to(dest).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(dest.rglob('*')) if p.is_file()}
(dest/'inventory.json').write_text(json.dumps(dict(schema=1,files=inventory),indent=2)+'\n',encoding='utf-8')
print('RETAINED',len(inventory),'evidence files;',sum(p.stat().st_size for p in dest.rglob('*') if p.is_file()),'bytes')
