#!/usr/bin/env python3
"""Check preserved report identities and the chapter's measured diagnostic case."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    manifest = json.loads((SOURCE/'reference/manifest.json').read_text())
    for name, expected in manifest['files'].items():
        path = (ROOT/name).resolve()
        require(path.is_relative_to(ROOT) and path.is_file(), f'Missing reference: {name}')
        require(sha(path) == expected, f'Modified reference: {name}')
    local_sources = 0
    for name, expected in manifest['recorded_inputs'].items():
        if name.startswith('/work/'):
            path = ROOT/name.removeprefix('/work/')
            require(path.is_file() and sha(path) == expected, f'Stale source: {name}')
            local_sources += 1
    for key, name in [('image_script_sha256', 'images.tcl'),
                      ('summarizer_sha256', 'summarize.py')]:
        require(sha(SOURCE/name) == manifest[key], f'Stale evidence script: {name}')
    extracted = (ROOT/'LAB-PROVENANCE.json').is_file() and not (ROOT/'chapters').exists()
    if not extracted:
        for name, expected in manifest['figures'].items():
            require((ROOT/name).is_file() and sha(ROOT/name) == expected, f'Stale figure: {name}')
    rows = json.loads((SOURCE/'reference/summary.json').read_text())
    require(len(rows) == 11, 'Incomplete recorded sweep')
    require(sum(r['status'] == 'completed' for r in rows) == 8, 'Changed completion boundary')
    focus = next(r for r in rows if r['name'] == 'u55-p0.91')
    require(focus['cts_setup_ns'] > 0 > focus['routed_setup_ns'],
            'Missing measured pre-route pass/post-route failure')
    require(focus['routed_hold_ns'] < 0, 'Hold failure must remain explicit')
    for row in rows:
        if row['target_util_pct'] == 80:
            require(row['status'] == 'failed' and 'GPL-0301' in row['failure'],
                    'Infeasible floorplan must not acquire invented routed metrics')
        else:
            require(not row['hold_pass'], 'Unexpected timing-closure claim')
    print(f'PASS physical-study reference: {len(manifest["files"])} artifact hashes, '
          f'{local_sources} local input hashes, 8 routed/3 rejected cases; '
          + ('figures omitted from practice ZIP' if extracted else '7 actual GUI captures'))


if __name__ == '__main__':
    main()
