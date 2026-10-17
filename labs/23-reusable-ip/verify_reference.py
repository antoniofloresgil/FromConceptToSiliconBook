#!/usr/bin/env python3
"""Audit compact packaging evidence without a simulator, compiler or Wally clone."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference-dir',type=Path,default=HERE/'reference')
    args = parser.parse_args()
    ref = args.reference_dir.resolve()
    inventory = json.loads((ref/'inventory.json').read_text())
    def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
    for group, base in [('sources',ROOT),('artifacts',ref)]:
        for name, expected in inventory[group].items():
            assert sha(base/name) == expected, ('Changed '+group,name)
    ip = ref/'dotproduct_ip'
    spec = importlib.util.spec_from_file_location('pack_verify',ip/'manifest/verify.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    lock = module.verify(ip)
    for name, expected in json.loads((HERE/'origin-lock.json').read_text()).items():
        assert sha(ROOT/name) == expected, ('Changed baseline',name)
    for name, expected in lock['generation'].items():
        assert sha(ROOT/name) == expected, ('Changed generator',name)
    result = json.loads((ref/'results.json').read_text())
    assert result['status'] == 'pass' and lock['version'] == '1.1.0'
    assert result['release_sha256'] == sha(ip/'manifest/release.json')
    assert len(result['rtl_sha256']) == 3
    for name, maximum in result['configurations'].items():
        report = json.loads((ref/name/'report.json').read_text())
        assert report['status'] == 'pass' and report['rtl_sha256'] == result['rtl_sha256']
        assert report['release_sha256'] == result['release_sha256']
        assert all(c['returncode'] == 0 for c in report['commands'])
        if name.startswith('axi'):
            assert f'PASS dotproduct: {maximum} lengths' in (ref/name/'command-03.txt').read_text()
            assert 'reachable DONE witness' in (ref/name/'command-05.txt').read_text()
        else:
            assert 'PASS real Wally: five polling jobs, IRQ handler, invalid descriptor' in (ref/name/'command-05.txt').read_text()
            assert report['wally_revision'] == result['wally_revision']
            assert report['wally_pma']['original_sha256'] != report['wally_pma']['adapted_sha256']
    assert set(json.loads((ref/'negative.json').read_text()).values()) == {'rejected'}
    assert result['wally_mmio'] == '0x10080000'
    assert 'Firmware failure 00000007' in (ref/'relocation-failure/command-05.txt').read_text()
    assert len(json.loads((ref/'negative.json').read_text())) == 4
    print('PASS reusable IP: one immutable generated release, AXI 256/16, real Wally firmware/IRQ, generated register views, failed relocation and four rejected defects')


if __name__ == '__main__': main()
