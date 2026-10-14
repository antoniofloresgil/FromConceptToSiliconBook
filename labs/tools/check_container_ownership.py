"""Check Linux container outputs and subsequent same-user host writes."""
import argparse
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BUILD=ROOT/'labs/build'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true',help='Create the probe inside the non-root container')
    args=parser.parse_args()
    if not hasattr(os,'getuid'):raise RuntimeError('This ownership check is for Linux/WSL filesystems, not native Windows ACLs')
    uid,gid=os.getuid(),os.getgid()
    if uid==0:raise RuntimeError('Ownership regression must be checked as the non-root host identity')
    probe=BUILD/'ownership-probe.json'
    if args.write:
        BUILD.mkdir(parents=True,exist_ok=True)
        probe.write_text(json.dumps({'uid':uid,'gid':gid})+'\n')
        print(f'PASS container created output as uid={uid} gid={gid}')
    else:
        expected=json.loads(probe.read_text())
        if expected!={'uid':uid,'gid':gid}:raise RuntimeError('Container and host numeric identities differ')
        for path in BUILD.rglob('*'):
            if path.is_file() and not path.is_symlink() and path.stat().st_uid!=uid:
                raise RuntimeError('Foreign-owned build output: '+str(path.relative_to(ROOT)))
        with probe.open('a') as output:output.write('host append succeeded\n')
        print('PASS host can append to container output; build files match the host UID')

if __name__=='__main__':
    try:main()
    except (RuntimeError,OSError) as error:raise SystemExit(f'FAIL ownership: {error}')
