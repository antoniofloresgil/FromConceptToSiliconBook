import hashlib
import json
from pathlib import Path
import shutil

base=Path('/work/labs/build');dest=base/'audit-followup-export'
assert not dest.exists(),'Fresh compact export required'
dest.mkdir()
names=['report.json','uart.txt','smoke.txt','progress.txt','wally-linux.dts','dtc.txt',
       'boot-build.txt','smoke-build.txt','compile.txt','address-map.json']
kept={}
files=[base/'audit-wally-rtl'/n for n in names]
files += [base/n for n in ['audit-wally-external-before.json','audit-wally-external-after.json',
    'audit-wally-collection.json','audit-wally-final-checks.json','audit-wally-environment.json']]
for src in files:
    assert src.is_file(),src
    name=src.relative_to(base).as_posix();target=dest/name
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,target)
    kept[name]=dict(bytes=src.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest())
(dest/'raw-index.json').write_text(json.dumps(dict(retained=kept,
    omitted='Compiled simulator, boot ELF/binary/hex, exported upstream source and kernel/initramfs binaries are not copied. Full hashes and current acceptance checks were evaluated before export; raw outputs remain in the audit volumes.'),indent=2)+'\n')
print('EXPORTED',len(kept),'raw evidence files;',sum(x['bytes'] for x in kept.values()),'bytes')
