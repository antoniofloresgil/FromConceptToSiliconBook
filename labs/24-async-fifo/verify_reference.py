#!/usr/bin/env python3
"""Check the actual CDC experiment dossier with only Python's standard library."""
import argparse
import hashlib
import json
from pathlib import Path
from check_structure import check

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference-dir',type=Path,default=HERE/'reference')
    args=parser.parse_args();ref=args.reference_dir.resolve()
    inventory=json.loads((ref/'inventory.json').read_text())
    for group,base in [('sources',ROOT),('artifacts',ref)]:
        for name,digest in inventory[group].items():
            assert hashlib.sha256((base/name).read_bytes()).hexdigest()==digest,('Changed '+group,name)
    report=json.loads((ref/'report.json').read_text())
    result=json.loads((ref/'results.json').read_text())
    assert report['status']==result['status']=='pass'
    assert len(report['simulations'])==48 and len(report['negative'])==4
    expected={(w,d,wh,rh,ph,seed) for w in [8,32] for d in [2,4,16]
              for wh,rh,ph in [(5,7,2),(3,11,1),(13,2,0),(5,5,0)] for seed in [2026,2027]}
    actual={(r['width'],r['depth'],r['write_half_ns'],r['read_half_ns'],r['read_phase_ns'],r['seed']) for r in report['simulations']}
    assert actual==expected
    for run in report['simulations']:
        metrics=run['metrics'];text=(ref/(run['name']+'.txt')).read_text()
        assert 'PASS asynchronous FIFO' in text
        assert metrics['writes']==metrics['reads']+metrics['dropped'] and metrics['epochs']==3
        assert metrics['wstall']>0 and metrics['rstall']>0 and metrics['dropped']>=run['depth']
    for width in [8,32]:
        for depth in [2,4,16]:
            name=f'w{width}-d{depth}'
            structure=check(ref/(name+'.json'))
            assert structure==json.loads((ref/(name+'-structure.json')).read_text())
    markers={r['name']:r['detected_by'] for r in report['negative']}
    for command in report['commands']:
        if command['name'] in markers:
            assert command['exit_code']!=0 and markers[command['name']] in (ref/command['log']).read_text()
        else:assert command['exit_code']==0
    for key,value in result['totals'].items():assert value==sum(r['metrics'][key] for r in report['simulations'])
    assert result['totals']['wjump']+result['totals']['rjump']>0
    assert result['totals']['simultaneous']>0
    print('PASS async FIFO: 48 real dual-clock runs, six synthesized pointer-chain reviews, reset epochs and four rejected defects; digital scope only')


if __name__=='__main__':main()
