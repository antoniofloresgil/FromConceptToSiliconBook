"""Export pinned Wally sources without changing its working tree; convert ELF32."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import struct
import subprocess
import tarfile

REVISION = "3b30ba6b6519bd2c26c1437e6d61f632a35cef6c"
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('command',choices=['export','hex'])
parser.add_argument('source',type=Path)
parser.add_argument('destination',type=Path)
args=parser.parse_args()
if args.command=='export':
    archive=subprocess.check_output(['git','-C',str(args.source),'archive',REVISION,
                                     'src','config/rv32imc','config/shared','LICENSE'])
    args.destination.mkdir(parents=True,exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        # Explicit path check works with Python 3.10 as well as newer versions.
        for member in tar.getmembers():
            target=(args.destination/member.name).resolve()
            if not target.is_relative_to(args.destination.resolve()) or member.issym() or member.islnk():
                raise RuntimeError('Unsafe source archive member')
            if member.isfile():
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(tar.extractfile(member).read())
    files={p.relative_to(args.destination).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
           for p in args.destination.rglob('*') if p.is_file() and p.name!='source-identity.json'}
    (args.destination/'source-identity.json').write_text(json.dumps({'revision':REVISION,'files':files},indent=2)+'\n')
else:
    data=args.source.read_bytes()
    if data[:7]!=b'\x7fELF\x01\x01\x01': raise RuntimeError('Requires little-endian ELF32')
    phoff=struct.unpack_from('<I',data,28)[0]
    phentsize,phnum=struct.unpack_from('<HH',data,42)
    memory=bytearray(65536)
    for i in range(phnum):
        kind,offset,vaddr,paddr,size,memsize,flags,align=struct.unpack_from('<8I',data,phoff+i*phentsize)
        if kind!=1: continue
        start=paddr-0x80000000
        if start<0 or start+memsize>len(memory): raise RuntimeError('ELF segment outside platform RAM')
        memory[start:start+size]=data[offset:offset+size]
    args.destination.write_text(''.join(f'{v[0]:08x}\n' for v in struct.iter_unpack('<I',memory)))
