"""Check audit source snapshots or raw lab-report integrity, without running EDA.

Python 3.10+, standard library only. Integrity is not functional/physical signoff.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value, message):
    if not value: raise ValueError(message)


def contained(root, name):
    require(not Path(name).is_absolute(), 'Absolute manifest path: '+name)
    path=(root/name).resolve()
    require(path.is_relative_to(root.resolve()), 'Manifest path escapes its scope: '+name)
    require(path.is_file(), 'Missing file: '+str(path))
    return path


def check_hashes(base, mapping):
    require(isinstance(mapping,dict) and mapping, 'Empty or invalid hash inventory')
    for name,digest in mapping.items():
        require(isinstance(digest,str) and re.fullmatch('[0-9a-f]{64}',digest), 'Invalid digest: '+name)
        require(sha(contained(base,name))==digest, 'Checksum mismatch: '+name)
    return len(mapping)


def snapshot(root):
    def git(*args):
        return subprocess.check_output(['git','-c','safe.directory='+str(root),*args],cwd=root)
    names=git('ls-files','-z').decode('utf-8').split('\0')
    return dict(schema=1,revision=git('rev-parse','HEAD').decode().strip(),
                files={name:sha(contained(root,name)) for name in names if name})


def compare_snapshot(root, before):
    require(before.get('schema')==1, 'Unsupported snapshot schema')
    after=snapshot(root)
    require(before['revision']==after['revision'], 'Source revision changed')
    require(before['files']==after['files'], 'Tracked sources or references changed')
    return after


def report(root, path, kind):
    data=json.loads(path.read_text(encoding='utf-8'))
    expected='pass' if kind in {'formal','linux'} else 'completed'
    require(data.get('status')==expected, 'Incomplete or failed '+kind+' report')
    source_root=root/'labs/18-linux-accelerator' if kind=='linux' else root
    artifact_root=root if kind=='formal' else path.parent
    sources=check_hashes(source_root,data.get('sources'))
    artifacts=check_hashes(artifact_root,data.get('artifacts'))
    commands=data.get('jobs' if kind=='formal' else 'commands',[])
    require(commands, 'Missing command records')
    for command in commands:
        code=command.get('exit_code')
        require(type(code) is int, 'Missing/noninteger command exit code')
        if kind=='formal':
            require(command.get('status')=='pass', 'Failed formal job')
            expected_code=command.get('expected_exit',0)
            require(code==0 if expected_code==0 else code!=0, 'Unexpected formal exit')
            log=contained(root,command['log'])
            require(command['log'] in data['artifacts'], 'Unbound formal log')
            marker=command.get('required_marker')
            require(isinstance(marker,str) and marker in log.read_text(encoding='utf-8'), 'Missing formal completion/defect marker')
        else:
            require(code==0, 'Failed tool command')
            require(command['log'] in data['artifacts'], 'Unbound command log')
    if kind=='linux':
        require(set(data.get('runs',{}))=={'normal','dma-error','timeout'}, 'Missing Linux boot modes')
        require(all(x.get('status')=='pass' for x in data['runs'].values()), 'Failed Linux boot')
        require(len(data.get('metrics',[]))==10, 'Missing Linux metric rows')
        check_hashes(root,data['manifest']['rtl_sha256'])
        check_hashes(path.parent/'bundle',data['bundle'])
        require(sha(root/'labs/18-linux-accelerator/manifest.json')==data['manifest_sha256'], 'Changed Linux manifest')
    return dict(kind=kind,sources=sources,artifacts=artifacts,commands=len(commands),
                qualification='not determined by this integrity check')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path.cwd())
    modes=p.add_subparsers(dest='mode',required=True)
    write=modes.add_parser('snapshot');write.add_argument('output',type=Path)
    compare=modes.add_parser('unchanged');compare.add_argument('before',type=Path)
    check=modes.add_parser('report');check.add_argument('kind',choices=['formal','linux','closure','layout']);check.add_argument('path',type=Path)
    a=p.parse_args();root=a.root.resolve()
    if a.mode=='snapshot':
        data=snapshot(root)
        with a.output.open('x',encoding='utf-8') as stream:json.dump(data,stream,indent=2);stream.write('\n')
        print('PASS snapshot:',data['revision'],len(data['files']),'tracked files')
    elif a.mode=='unchanged':
        data=compare_snapshot(root,json.loads(a.before.read_text(encoding='utf-8')))
        print('PASS unchanged sources/references:',len(data['files']),'tracked files')
    else:print('PASS report integrity:',json.dumps(report(root,a.path.resolve(),a.kind)))


if __name__=='__main__':
    try:main()
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as error:
        print('FAIL audit integrity:',error,file=sys.stderr);sys.exit(1)
