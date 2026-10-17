#!/usr/bin/env python3
"""Offline integrity and acceptance audit of the preserved closure dossier."""
import argparse
import hashlib
import json
from pathlib import Path
from collect import summarize

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--reference-dir',default='labs/21-physical-closure/reference')
args=parser.parse_args()
ref=(ROOT/args.reference_dir).resolve()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
i=json.loads((ref/'inventory.json').read_text())
for name,d in i['sources'].items():
    if sha(ROOT/name)!=d:raise ValueError('Stale source '+name)
for name,d in i['artifacts'].items():
    if sha(ref/name)!=d:raise ValueError('Changed evidence '+name)
results=json.loads((ref/'results.json').read_text())
for name,t in results.items():
    folder=ref/name
    r=json.loads((folder/'report.json').read_text())
    if r['status']!='completed' or any(c['exit_code'] for c in r['commands']):raise ValueError('Incomplete commands')
    # Preserved command logs retain their exact original bytes under .txt names.
    for c in r['commands']:
        log=Path(c['log'])
        if sha(folder/(log.stem+'.txt'))!=r['artifacts'][log.name]:raise ValueError('Wrong command log')
    if r['target']=='test':
        logs=[(folder/(Path(c['log']).stem+'.txt')).read_text() for c in r['commands']]
        if sum('PASS dotproduct: 256 lengths' in s for s in logs)!=2:raise ValueError('Missing scoreboard')
    else:
        actual=summarize(folder,r)
        if name=='asic-repair':actual['accepted']=actual['timing_electrical_pass'] and actual['router_drc_empty'] and not actual['gds_readback']['empty_cells']
        if actual!=t:raise ValueError('Summary differs from reports '+name)
if not all(results[n]['accepted'] for n in ['test-baseline','test-pipeline','ecp5-slow','nexys-slow','nexys-pipeline','asic-repair']):raise ValueError('Required candidate does not pass')
if results['ecp5-pipeline']['accepted'] or results['asic-slow']['timing_electrical_pass'] or results['asic-baseline']['timing_electrical_pass']:raise ValueError('Expected failed candidates lost')
if len({json.loads((ref/('asic-'+c)/'report.json').read_text())['artifacts']['mapped.v'] for c in ['baseline','slow','repair']})!=1:raise ValueError('Different mapped inputs')
eq=json.loads((ref/'asic-repair/equivalence.json').read_text())
if eq['status']!='pass' or eq['log_sha256']!=sha(ref/'asic-repair/equivalence.txt'):raise ValueError('Missing equivalence')
rr=json.loads((ref/'asic-repair/report.json').read_text())
if eq['recipe_sha256']!=sha(HERE/'verify_netlist.py'):raise ValueError('Stale equivalence recipe')
if eq['inputs']['report.json']!=sha(ref/'asic-repair/report.json'):raise ValueError('Equivalence report identity')
for name in ['mapped.v','routed.v']:
    if eq['inputs'][name]!=rr['artifacts'][name]:raise ValueError('Equivalence netlist identity')
if 'Equivalence successfully proven!' not in (ref/'asic-repair/equivalence.txt').read_text():raise ValueError('Missing proof completion')
n=json.loads((ref/'negative/negative.json').read_text())
if n['status']!='pass' or not n['exit_codes'][-1] or 'Arithmetic/status mismatch' not in (ref/'negative/command-03.txt').read_text():raise ValueError('Negative control missing')
cap=json.loads((ref/'asic-repair/capture.json').read_text())
if cap['inputs']['report.json']!=sha(ref/'asic-repair/report.json'):raise ValueError('Capture report identity')
for name in ['routed.odb','routed.sdc','routed.spef']:
    if cap['inputs'][name]!=rr['artifacts'][name]:raise ValueError('Capture database identity')
for name,digest in cap['images'].items():
    if sha(ref/'asic-repair'/name)!=digest:raise ValueError('Capture image identity')
print('PASS physical closure reference: 9 runs, checked regression/negative control, scoped ASIC equivalence and timing/electrical acceptance')
