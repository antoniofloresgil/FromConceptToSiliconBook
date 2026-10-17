#!/usr/bin/env python3
"""Collect the immutable portable IP and compact qualification evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('release',type=Path)
    parser.add_argument('results',type=Path)
    parser.add_argument('--negative',type=Path,required=True)
    parser.add_argument('--image-id',required=True)
    parser.add_argument('--relocation-failure',type=Path,required=True)
    parser.add_argument('--reference-dir',type=Path,default=HERE/'reference')
    args = parser.parse_args()
    dest = args.reference_dir.resolve()
    if dest.exists(): raise SystemExit('Choose a fresh reference directory.')
    assert args.image_id.startswith('sha256:')
    dest.mkdir(parents=True)
    shutil.copytree(args.release,dest/'dotproduct_ip',ignore=shutil.ignore_patterns('__pycache__'))
    jobs = {}
    for name in ['axi-course','axi-compact','wally']:
        src = args.results/name
        report = json.loads((src/'report.json').read_text())
        assert report['status'] == 'pass'
        jobs[name] = report
        (dest/name).mkdir()
        for path in sorted(src.iterdir()):
            if path.is_file() and (path.suffix in {'.txt','.log'} or path.name == 'report.json'):
                # The practice archive excludes transient .log files. Preserve
                # these deliberately retained proof transcripts as .txt.
                retained = path.with_suffix('.txt').name if path.suffix == '.log' else path.name
                shutil.copyfile(path,dest/name/retained)
    lock = json.loads((dest/'dotproduct_ip/manifest/release.json').read_text())
    release_hash = sha(dest/'dotproduct_ip/manifest/release.json')
    assert all(r['release_sha256'] == release_hash for r in jobs.values())
    assert all(r['rtl_sha256'] == jobs['wally']['rtl_sha256'] for r in jobs.values())
    negative = json.loads(args.negative.read_text())
    assert set(negative.values()) == {'rejected'} and len(negative) == 4
    shutil.copyfile(args.negative,dest/'negative.json')
    failure = json.loads((args.relocation_failure/'report.json').read_text())
    assert failure['status'] == 'fail'
    assert 'Firmware failure 00000007' in (args.relocation_failure/'command-05.txt').read_text()
    (dest/'relocation-failure').mkdir()
    for name in ['report.json','command-05.txt']:
        shutil.copyfile(args.relocation_failure/name,dest/'relocation-failure'/name)
    result = dict(status='pass',image_id=args.image_id,ip_version=lock['version'],
                  register_abi=lock['register_abi'], release_sha256=release_hash,
                  rtl_sha256=jobs['wally']['rtl_sha256'],
                  configurations={'axi-course':256,'axi-compact':16,'wally':256},
                  wally_revision=jobs['wally']['wally_revision'], wally_mmio='0x10080000',
                  boundary='AXI bus-functional subsystem and real Wally RTL firmware fixture; no second CPU SoC or physical qualification.')
    (dest/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    sources = sorted(p for p in HERE.rglob('*') if p.is_file() and dest not in p.parents
                     and 'reference' not in p.parts and '__pycache__' not in p.parts and p.suffix != '.md')
    inventory = dict(sources={p.relative_to(ROOT).as_posix():sha(p) for p in sources},
                     artifacts={p.relative_to(dest).as_posix():sha(p) for p in sorted(dest.rglob('*')) if p.is_file()})
    (dest/'inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
    print('COLLECTED one IP release, three qualified configurations, two integration boundaries, failed relocation and four negative controls')


if __name__ == '__main__': main()
