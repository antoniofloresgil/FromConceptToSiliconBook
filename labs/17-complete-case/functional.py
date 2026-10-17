#!/usr/bin/env python3
"""Run the existing unit or real-Wally stage under the common release manifest."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from run import ROOT, SOURCE, load_manifest, sha

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('stage',choices=['unit','system'])
parser.add_argument('--output-dir',default='labs/build/complete-case')
args=parser.parse_args()
manifest=load_manifest()
manifest_digest=sha(SOURCE/'manifest.json')
out=(ROOT/args.output_dir/args.stage).resolve()
if not out.is_relative_to(ROOT/'labs/build') or (out.exists() and any(out.iterdir())):
    raise ValueError('Choose a fresh output directory inside labs/build')
env={**os.environ,'LAB_BUILD_DIR':str(out)}
lab='dotproduct' if args.stage=='unit' else 'dotproduct-wally'
command=[sys.executable,str(ROOT/'labs/run.py'),'run',lab,'--seed',str(manifest['seed'])]
subprocess.run(command,cwd=ROOT,env=env,check=True)
load_manifest() # Reject source changes during execution.
if sha(SOURCE/'manifest.json')!=manifest_digest:
    raise RuntimeError('Common configuration changed during execution')
report=json.loads((out/'report.json').read_text())
for name,expected in {**manifest['rtl_sha256'],**manifest['firmware_sha256']}.items():
    if report['sources'].get(name)!=expected:
        raise RuntimeError('Stage did not use the locked source: '+name)
(out/'common-manifest.json').write_text(json.dumps({
    'manifest_sha256':manifest_digest,'stage':args.stage,
    'report_sha256':sha(out/'report.json'),'command':command},indent=2)+'\n')
