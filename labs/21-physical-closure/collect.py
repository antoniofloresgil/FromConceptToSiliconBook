#!/usr/bin/env python3
"""Collect actual closure runs, rejecting stale inputs and incomplete commands."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def summarize(folder, r):
    if r['target']=='test':
        logs=[(folder/c['log']).read_text() for c in r['commands']]
        if sum('PASS dotproduct: 256 lengths' in s for s in logs)!=2 or not any('PASS Nexys fixture:' in s for s in logs):
            raise ValueError('Missing functional completions')
        return dict(accepted=True,checked_lengths=512,seeds=[2026,2027],fixture=True)
    if r['target']!='asic':
        t=json.loads((folder/'timing.json').read_text())
        clock=t['fmax']['clk']
        if clock['constraint']!=r['requested_mhz']:raise ValueError('Clock target mismatch')
        path=t['critical_paths'][0]['path']
        return dict(requested_mhz=clock['constraint'],achieved_mhz=clock['achieved'],
                    setup_margin_ns=1000/clock['constraint']-1000/clock['achieved'],
                    accepted=clock['achieved']>=clock['constraint'],utilization=t['utilization'],
                    critical_logic_ns=sum(s['delay'] for s in path if s['type']=='logic'),
                    critical_route_ns=sum(s['delay'] for s in path if s['type']=='routing'),power_w=None)
    t=json.loads((folder/'routed-metrics.json').read_text())
    t['cell_um2']=float(re.search(r'Design area ([\d.]+)',(folder/'routed-area.rpt').read_text())[1])
    t['electrical_violations']=(folder/'routed-limits.rpt').read_text().count('(VIOLATED)')
    t['router_drc_empty']=not (folder/'route-drc.rpt').read_text().strip()
    t['unconstrained_report_empty']=not (folder/'routed-constraints.rpt').read_text().strip()
    row=re.search(r'^Total\s+([\d.e+-]+)\s+([\d.e+-]+)\s+([\d.e+-]+)\s+([\d.e+-]+)',(folder/'power.rpt').read_text(),re.M)
    t['power_w']=float(row[4]);t['requested_mhz']=r['requested_mhz']
    t['gds_readback']=json.loads((folder/'gds-readback.json').read_text())
    t['timing_electrical_pass']=t['setup_ns']>=0 and t['hold_ns']>=0 and t['electrical_violations']==0 and t['unconstrained_report_empty']
    t['accepted']=False # Set only after the separate equivalence record has passed.
    t['manufacturing_qualified']=False
    return t

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix',default='closure-final')
    parser.add_argument('--reference-dir',default='labs/21-physical-closure/reference')
    args=parser.parse_args()
    if Path(args.prefix).name!=args.prefix:raise ValueError('Prefix must be a directory-name prefix')
    ref=(ROOT/args.reference_dir).resolve()
    if ref!=HERE/'reference' and not ref.is_relative_to(ROOT/'labs/build'):raise ValueError('Expected reference or labs/build')
    if ref.exists(): raise ValueError('Preserve reference; use a reviewed replacement')
    ref.mkdir()
    results={}
    for target,candidates in [('test',['baseline','pipeline']),('ecp5',['slow','pipeline']),('nexys',['slow','pipeline']),('asic',['baseline','slow','repair'])]:
        for c in candidates:
            name=target+'-'+c
            folder=ROOT/'labs/build'/(args.prefix+'-'+name)
            r=json.loads((folder/'report.json').read_text())
            if r['status']!='completed' or any(x['exit_code']!=0 for x in r['commands']):raise ValueError('Incomplete '+name)
            for f,d in r['sources'].items():
                if sha(ROOT/f)!=d:raise ValueError('Stale source '+f)
            for f,d in r['artifacts'].items():
                if sha(folder/f)!=d:raise ValueError('Changed raw artifact '+f)
            dest=ref/name;dest.mkdir()
            for f in folder.iterdir():
                if f.suffix in {'.rpt','.sdc','.png'} or f.name in {'report.json','timing.json','gds-readback.json','power.rpt','capture.json'} or f.name.endswith('-metrics.json') or f.name.startswith('command-') and f.suffix=='.log':
                    shutil.copyfile(f,dest/(f.stem+'.txt' if f.suffix=='.log' else f.name))
            results[name]=summarize(folder,r)
    raw=ROOT/'labs/build'/(args.prefix+'-asic-repair')
    mapped=[json.loads((ref/('asic-'+c)/'report.json').read_text())['artifacts']['mapped.v'] for c in ['baseline','slow','repair']]
    if len(set(mapped))!=1:raise ValueError('ASIC candidates did not start with the same mapped netlist')
    capture=json.loads((raw/'capture.json').read_text())
    if capture['recipe_sha256']!=sha(ROOT/'labs/17-complete-case/asic-images.tcl') or capture['capture_sha256']!=sha(HERE/'capture.py'):raise ValueError('Stale capture recipe')
    for f,d in capture['inputs'].items():
        if sha(raw/f)!=d:raise ValueError('Capture input mismatch')
    for f,d in capture['images'].items():
        if sha(raw/f)!=d:raise ValueError('Capture image mismatch')
    eq=json.loads((raw/'equivalence.json').read_text())
    if eq['status']!='pass' or eq['recipe_sha256']!=sha(HERE/'verify_netlist.py') or eq['log_sha256']!=sha(raw/'equivalence.log'):raise ValueError('Invalid equivalence')
    for f in ['mapped.v','routed.v','report.json']:
        if eq['inputs'][f]!=sha(raw/f):raise ValueError('Equivalence belongs to a different implementation')
    shutil.copyfile(raw/'equivalence.json',ref/'asic-repair/equivalence.json')
    shutil.copyfile(raw/'equivalence.log',ref/'asic-repair/equivalence.txt')
    results['asic-repair']['accepted']=results['asic-repair']['timing_electrical_pass'] and results['asic-repair']['router_drc_empty'] and not results['asic-repair']['gds_readback']['empty_cells']
    neg=ROOT/'labs/build'/(args.prefix+'-negative')
    n=json.loads((neg/'negative.json').read_text())
    for f,d in n['sources'].items():
        if sha(ROOT/f)!=d:raise ValueError('Stale negative control')
    for f,d in n['artifacts'].items():
        if sha(neg/f)!=d:raise ValueError('Changed negative evidence')
    if n['status']!='pass' or not n['exit_codes'][-1]:raise ValueError('Invalid negative control')
    (ref/'negative').mkdir()
    for f in ['negative.json','command-03.txt']:shutil.copyfile(neg/f,ref/'negative'/f)
    (ref/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    provenance={f:d for r in ref.glob('*/report.json') for f,d in json.loads(r.read_text())['sources'].items()}
    provenance.update(n['sources'])
    provenance['labs/17-complete-case/asic-images.tcl']=sha(ROOT/'labs/17-complete-case/asic-images.tcl')
    provenance.update({f.relative_to(ROOT).as_posix():sha(f) for f in HERE.iterdir() if f.suffix in {'.py','.tcl','.sv','.json'}})
    inventory=dict(sources=provenance,artifacts={f.relative_to(ref).as_posix():sha(f) for f in sorted(ref.rglob('*')) if f.is_file()})
    (ref/'inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
    print('COLLECTED actual closure evidence')

if __name__=='__main__':main()
