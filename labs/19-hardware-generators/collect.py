"""Publish a hash-checked compact generator experiment after actual execution."""
import argparse
import json
from pathlib import Path
import shutil
from run import HERE,ROOT,sha

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('report',type=Path);args=p.parse_args()
    report=json.loads(args.report.read_text());base=args.report.resolve().parent
    if report['status']!='pass':raise ValueError('Incomplete generator experiment')
    for name,digest in report['sources'].items():
        if sha(HERE/name)!=digest:raise ValueError('Changed generator recipe: '+name)
    for name,digest in report['original_source'].items():
        if sha(ROOT/name)!=digest:raise ValueError('Changed original accumulator')
    for name,digest in report['artifacts'].items():
        if sha(base/name)!=digest:raise ValueError('Changed execution artifact: '+name)
    dest=HERE/'reference';dest.mkdir(exist_ok=True)
    for name in ['report.json',*[n for n in report['artifacts'] if not n.endswith('.vvp')]]:
        target=(dest/name).resolve()
        if not target.is_relative_to(dest.resolve()):raise ValueError('Unsafe artifact path')
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(base/name,target)
    inventory={'files':{p.relative_to(dest).as_posix():sha(p) for p in dest.rglob('*') if p.is_file() and p.name!='inventory.json'}}
    (dest/'inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
    print('Preserved generated IR/RTL, vectors, simulation/synthesis logs, netlists and source/tool provenance')

if __name__=='__main__':main()
