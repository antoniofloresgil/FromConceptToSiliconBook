#!/usr/bin/env python3
"""Verify the exact files of a supplied IP release; independent of the book tree."""
import hashlib
import json
from pathlib import Path


def verify(root):
    record = json.loads((root/'manifest/release.json').read_text())
    for name, expected in record['files'].items():
        path = (root/name).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            raise ValueError('Missing or unsafe release path: '+name)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Release checksum mismatch: '+name)
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()
              and '__pycache__' not in p.parts and p.relative_to(root).as_posix() != 'manifest/release.json'}
    if actual != set(record['files']): raise ValueError('Unexpected release files; keep build outputs outside the IP tree.')
    return record


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    print('PASS release integrity:', len(verify(root)['files']), 'files')
