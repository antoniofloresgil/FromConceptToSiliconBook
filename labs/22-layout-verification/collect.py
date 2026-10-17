#!/usr/bin/env python3
"""Preserve compact, source-bound reference DRC/LVS evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('raw',type=Path)
    p.add_argument('--reference-dir',default='labs/22-layout-verification/reference')
    p.add_argument('--input-report',type=Path,default=ROOT/'labs/build/closure-final-asic-repair/report.json')
    a=p.parse_args();raw=a.raw.resolve();ref=(ROOT/a.reference_dir).resolve()
    if not raw.is_relative_to(ROOT/'labs/build') or ref.exists():raise ValueError('Expected raw labs/build and fresh reference')
    if ref!=HERE/'reference' and not ref.is_relative_to(ROOT/'labs/build'):raise ValueError('Expected reference or labs/build')
    r=json.loads((raw/'report.json').read_text())
    if r['status']!='completed' or any(c['exit_code'] for c in r['commands']):raise ValueError('Incomplete run')
    for n,d in r['sources'].items():
        if sha(ROOT/n)!=d:raise ValueError('Stale source '+n)
    for n,d in r['artifacts'].items():
        if sha(raw/n)!=d:raise ValueError('Altered artifact '+n)
    if sha(a.input_report)!=r['input_report_sha256']:raise ValueError('Wrong input implementation report')
    ports=json.loads((raw/'port-identity.json').read_text())
    if not ports['identity_pass'] or ports['input_report_sha256']!=sha(raw/'report.json') or ports['database_sha256']!=r['artifacts']['finished-lvs.lvsdb'] or ports['recipe_sha256']!=sha(HERE/'audit_ports.py'):raise ValueError('Port identity audit missing or stale')
    ref.mkdir(parents=True)
    shutil.copyfile(a.input_report,ref/'input-report.json')
    for f in raw.iterdir():
        if f.suffix in {'.json','.rpt','.lyrdb','.lydrc'} or f.name.startswith('command-'):
            shutil.copyfile(f,ref/f.name)
    # Full cross-probing databases stay as hashed reproduction outputs.
    diagnostics={}
    for f in raw.glob('*.lvsdb'):
        s=f.read_text();errors=re.findall(r"M\(E B\('([^\n]*)",s)
        diagnostics[f.stem]={'error_count':len(errors),'first_errors':errors[:6],
                             'database_sha256':sha(f)}
    (ref/'diagnostics.json').write_text(json.dumps(diagnostics,indent=2)+'\n')
    sources={f.relative_to(ROOT).as_posix():sha(f) for f in HERE.rglob('*')
             if f.is_file() and 'reference' not in f.relative_to(HERE).parts and '__pycache__' not in f.relative_to(HERE).parts and f.suffix not in {'.md','.pyc'}}
    sources.update(r['sources'])
    sources.update(json.loads(a.input_report.read_text())['sources'])
    (ref/'inventory.json').write_text(json.dumps({'sources':sources,'artifacts':{
        f.name:sha(f) for f in sorted(ref.iterdir()) if f.is_file()}},indent=2)+'\n')
    print('COLLECTED actual reference DRC/LVS and finishing evidence')

if __name__=='__main__':main()
