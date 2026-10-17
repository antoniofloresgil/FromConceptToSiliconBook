"""Publish only completed two-CPU execution and separately scoped model evidence."""
import argparse
import json
from pathlib import Path
import shutil
from run import HERE,ROOT,sha

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('report',type=Path);a=p.parse_args()
    report=json.loads(a.report.read_text());base=a.report.resolve().parent
    if report['status']!='pass':raise ValueError('Incomplete multicore experiment')
    for name,digest in report['sources'].items():
        if sha(HERE/name)!=digest:raise ValueError('Changed local source: '+name)
    for name,digest in report['dependencies'].items():
        if sha(ROOT/name)!=digest:raise ValueError('Changed reused source: '+name)
    for name,digest in report['artifacts'].items():
        if sha(base/name)!=digest:raise ValueError('Changed artifact: '+name)
    dest=HERE/'reference';dest.mkdir(exist_ok=True)
    # Full static-glibc disassembly stays in the raw run; it is not a compact lab artifact.
    for name in ['report.json',*[n for n in report['artifacts'] if n not in {'disassembly.txt','virt.dtb'}]]:
        shutil.copyfile(base/name,dest/name)
    inventory={p.name:sha(p) for p in dest.iterdir() if p.is_file() and p.name!='inventory.json'}
    (dest/'inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
    print('Preserved actual SMP boot/driver/DMA evidence and separately scoped model witnesses')

if __name__=='__main__':main()
