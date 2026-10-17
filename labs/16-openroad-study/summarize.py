#!/usr/bin/env python3
"""Validate and summarize actual direct-flow artifacts; never invent missing timing."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--publish-reference', action='store_true',
                        help='Author operation: replace reference reports and book figures')
    args = parser.parse_args()
    directory = args.directory.resolve()
    study = json.loads((directory/'study.json').read_text())
    rows = []
    for case in study['cases']:
        folder = directory/case['name']
        for name, expected in case['artifacts'].items():
            if sha(folder/name) != expected:
                raise ValueError(f'Stale or modified artifact: {case["name"]}/{name}')
        row = {k:case[k] for k in ['name', 'period_ns', 'target_util_pct', 'status']}
        row['requested_mhz'] = 1000/case['period_ns']
        log = (folder/'flow.log').read_text()
        if case['status'] == 'completed':
            for stage in ['placed', 'cts', 'global', 'routed']:
                metrics = case['stages'][stage]
                row[stage+'_setup_ns'] = metrics['setup_wns']
                row[stage+'_hold_ns'] = metrics['hold_wns']
            row['core_um2'] = case['stages']['routed']['core_area']
            row['cell_um2'] = float(re.search(r'Design area ([\d.]+)', (folder/'routed-area.rpt').read_text())[1])
            lengths = re.findall(r'Total wire length = ([\d.]+) um', log)
            row['routed_wire_um'] = float(lengths[-1])
            row['router_drc_report_empty'] = (folder/'route-drc.rpt').stat().st_size == 0
            row['setup_pass'] = row['routed_setup_ns'] >= 0
            row['hold_pass'] = row['routed_hold_ns'] >= 0
        else:
            errors = re.findall(r'\[ERROR[^\n]+', log)
            row['failure'] = errors[-1] if errors else case.get('error', 'unclassified failure')
        rows.append(row)
    keys = list(dict.fromkeys(k for row in rows for k in row))
    with (directory/'summary.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=keys, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    (directory/'summary.json').write_text(json.dumps(rows, indent=2)+'\n')
    print(json.dumps(rows, indent=2))
    if args.publish_reference:
        reference = SOURCE/'reference'
        reference.mkdir(exist_ok=True)
        for case in study['cases']:
            origin = directory/case['name']
            target = reference/case['name']
            target.mkdir(exist_ok=True)
            for path in origin.iterdir():
                if path.suffix in {'.rpt', '.txt', '.log'}:
                    # Package excludes transient .log files; preserve reference logs as text.
                    name = path.with_suffix('.txt').name if path.suffix == '.log' else path.name
                    shutil.copyfile(path, target/name)
        for name in ['study.json', 'summary.json', 'summary.csv', 'mapped.v', 'images.json']:
            shutil.copyfile(directory/name, reference/name)
        shutil.copyfile(directory/'synthesis.log', reference/'synthesis.txt')
        focus = directory/'u55-p0.91'
        for name in ['placed', 'cts', 'routed', 'clocktree', 'critical-path']:
            picture = focus/(name+'.png')
            if not picture.is_file():
                raise ValueError(f'Missing actual GUI export: {picture}')
            shutil.copyfile(picture, ROOT/'figures'/('openroad-study-'+name+'.png'))
        for util in [45, 65]:
            picture = directory/f'u{util}-p1.00/placed.png'
            if not picture.is_file():
                raise ValueError(f'Missing actual GUI export: {picture}')
            shutil.copyfile(picture, ROOT/'figures'/f'openroad-study-u{util}-placed.png')
        manifest = {'image': study['image'], 'tools': study['tools'],
                    'recorded_inputs': study['inputs'],
                    'image_script_sha256': sha(SOURCE/'images.tcl'),
                    'summarizer_sha256': sha(Path(__file__)),
                    'files': {p.relative_to(ROOT).as_posix(): sha(p)
                              for p in sorted(reference.rglob('*')) if p.is_file() and p.name != 'manifest.json'}}
        manifest['figures'] = {p.relative_to(ROOT).as_posix(): sha(p)
                               for p in sorted((ROOT/'figures').glob('openroad-study-*.png'))}
        (reference/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')


if __name__ == '__main__':
    main()
