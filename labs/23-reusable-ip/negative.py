#!/usr/bin/env python3
"""Demonstrate rejected schema and release drift without altering the delivered IP."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
from package import generate

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('release',type=Path)
    parser.add_argument('output',type=Path)
    args = parser.parse_args()
    if args.output.exists(): raise SystemExit('Choose a fresh negative-test directory.')
    args.output.mkdir(parents=True)
    schema = json.loads((HERE/'registers.json').read_text())
    results = {}
    for name, mutate in [('duplicate-offset',lambda s:s['registers'][1].update(offset=0)),
                         ('unsupported-field-layout',lambda s:s['registers'][0]['fields'][0].update(lsb=4))]:
        candidate = copy.deepcopy(schema)
        mutate(candidate)
        try: generate(candidate)
        except AssertionError: results[name] = 'rejected'
        else: raise RuntimeError('Accepted '+name)
    release = args.release.resolve()
    spec = importlib.util.spec_from_file_location('ip_verify',release/'manifest/verify.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.verify(release)
    altered = args.output/'tampered_ip'
    shutil.copytree(release,altered,ignore=shutil.ignore_patterns('__pycache__'))
    path = altered/'rtl/dotproduct_engine.sv'
    path.write_bytes(path.read_bytes()+b'\n// unauthorized change\n')
    try: module.verify(altered)
    except ValueError as error:
        assert 'checksum mismatch' in str(error)
        results['rtl-drift'] = 'rejected'
    else: raise RuntimeError('Accepted RTL drift')
    module.verify(release)
    attempt = subprocess.run([sys.executable,str(release/'sim/run.py'),'--platform','wally',
                              '--profile','compact','--output',str(args.output/'unsupported-profile')],
                             stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    assert attempt.returncode != 0 and 'qualified only for the course profile' in attempt.stdout
    results['unsupported-wally-profile'] = 'rejected'
    (args.output/'unsupported-profile.txt').write_text(attempt.stdout)
    (args.output/'negative.json').write_text(json.dumps(results,indent=2)+'\n')
    print('PASS package negative controls:',results)


if __name__ == '__main__': main()
