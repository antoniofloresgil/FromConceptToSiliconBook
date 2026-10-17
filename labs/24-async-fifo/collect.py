#!/usr/bin/env python3
"""Retain compact, downloadable CDC experiment transcripts and generic netlists."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run',type=Path)
    parser.add_argument('--reference-dir',type=Path,default=HERE/'reference')
    args=parser.parse_args()
    run=args.run.resolve();dest=args.reference_dir.resolve()
    if dest.exists():raise SystemExit('Choose a fresh reference directory.')
    report=json.loads((run/'report.json').read_text())
    assert report['status']=='pass' and len(report['simulations'])==48 and len(report['negative'])==4
    for name,digest in report['sources'].items():assert sha(ROOT/name)==digest,('Changed recipe',name)
    dest.mkdir(parents=True)
    for path in sorted(run.iterdir()):
        if path.suffix in {'.txt','.json','.sv'}:
            if path.name!='report.json':assert sha(path)==report['artifacts'][path.name]
            shutil.copyfile(path,dest/path.name)
    totals={key:sum(job['metrics'][key] for job in report['simulations']) for key in report['simulations'][0]['metrics']}
    results=dict(status='pass',simulations=48,netlists=6,negative_controls=4,
                 widths=[8,32],depths=[2,4,16],seeds=[2026,2027],totals=totals,
                 image_id=report['image_id'],tools=report['tools'],
                 scope=report['scope'],constraints='Vivado adaptation template; not physically applied or qualified')
    (dest/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    sources=[p for p in sorted(HERE.rglob('*')) if p.is_file() and 'reference' not in p.parts
             and '__pycache__' not in p.parts and p.suffix!='.md']
    inventory=dict(sources={p.relative_to(ROOT).as_posix():sha(p) for p in sources},
                   artifacts={p.name:sha(p) for p in sorted(dest.iterdir()) if p.is_file()})
    (dest/'inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
    print('COLLECTED',len(inventory['artifacts']),'CDC evidence files and six actual generic netlists')


if __name__=='__main__':main()
