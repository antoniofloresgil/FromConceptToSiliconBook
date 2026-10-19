import hashlib,json,shutil
from pathlib import Path
base=Path('/work/labs/build');dest=base/'audit-export'
assert not dest.exists(),'Fresh evidence export required'
dest.mkdir()
folders=['formal','audit-fast-gate','audit-fast-mutations','audit-layout',
 'audit-linux','audit-test-baseline','audit-test-pipeline','audit-asic-baseline',
 'audit-asic-slow','audit-asic-repair','audit-ecp5-slow','audit-ecp5-pipeline',
 'audit-nexys-slow','audit-nexys-pipeline','audit-negative']
files=[p for p in base.glob('audit-*.json') if p.is_file()]+[base/'report.json']
for name in folders:
 files.extend(p for p in (base/name).rglob('*') if p.is_file())
files.extend(base.glob('audit-negative-*.txt'))
kept={};omitted=[]
for src in sorted(set(files)):
 if not src.exists():continue
 name=src.relative_to(base).as_posix();size=src.stat().st_size
 if src.suffix not in {'.json','.txt','.rpt','.log','.vcd','.csv'} or size>512*1024:
  omitted.append(dict(path=name,bytes=size));continue
 target=dest/'raw'/name;target.parent.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(src,target)
 kept['raw/'+name]=dict(bytes=size,sha256=hashlib.sha256(target.read_bytes()).hexdigest())
(dest/'raw-index.json').write_text(json.dumps(dict(retained=kept,omitted=omitted,
 scope='Compact audit evidence; full artifact hashes were checked before export. Large EDA/binary/layout outputs remain in the local audit volume; this subset alone cannot rerun raw-report integrity verification.'),indent=2)+'\n')
print('EXPORTED',len(kept),'files;',len(omitted),'omitted;',sum(x['bytes'] for x in kept.values()),'bytes')
