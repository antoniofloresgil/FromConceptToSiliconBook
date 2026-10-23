import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import sync

OLD = 'openroad/orfs@sha256:' + '1' * 64
NEW = 'openroad/orfs@sha256:' + '2' * 64


def manifest(value, rules=None):
    return {
        'schema': 1,
        'values': {'orfs_image': value, 'edition': '2026.10'},
        'scope': {'exclude': ['.git/*'], 'evidence': ['labs/*/reference/*']},
        'rules': rules or [{'id': 'orfs', 'pattern': 'openroad/orfs@sha256:[0-9a-f]{64}',
                            'replacement': '{orfs_image}'}],
    }


class SyncTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for name, text in {'README.md': f'pull {OLD}\r\n', 'labs/16/reference/report.json': f'"{OLD}"'}.items():
            (self.root / name).parent.mkdir(parents=True, exist_ok=True)
            (self.root / name).write_bytes(text.encode())
        subprocess.check_call(['git', 'init', '-q'], cwd=self.root)
        subprocess.check_call(['git', 'add', '-A'], cwd=self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_check_reports_drift_in_editable_copies_only(self):
        result = sync.scan(self.root, manifest(NEW))
        self.assertEqual(result['orfs']['edit'], [('README.md', 1, 1)])
        self.assertEqual(result['orfs']['recorded'], [('labs/16/reference/report.json', 1, 1)])

    def test_write_keeps_evidence_and_line_endings(self):
        self.assertEqual(sync.write(self.root, manifest(NEW), dry_run=False), 1)
        self.assertEqual((self.root / 'README.md').read_bytes(), f'pull {NEW}\r\n'.encode())
        self.assertIn(OLD.encode(), (self.root / 'labs/16/reference/report.json').read_bytes())
        self.assertEqual(sync.report(sync.scan(self.root, manifest(NEW))), 0)

    def test_rule_matching_nothing_fails(self):
        dead = manifest(NEW, [{'id': 'dead', 'pattern': 'nothing-here', 'replacement': 'x'}])
        self.assertEqual(sync.report(sync.scan(self.root, dead)), 1)

    def test_non_idempotent_rule_is_rejected(self):
        loop = manifest(NEW, [{'id': 'loop', 'pattern': 'openroad', 'replacement': 'openroad-openroad'}])
        with self.assertRaises(ValueError):
            sync.scan(self.root, loop)

    def test_unresolved_value_is_rejected(self):
        with self.assertRaises(ValueError):
            sync.expand('{missing}', {'edition': '1'})

    def test_prose_rule_fails_check_but_is_not_rewritten(self):
        (self.root / 'guide.md').write_text('Uses QEMU 8.2.2 here.\n')
        subprocess.check_call(['git', 'add', '-A'], cwd=self.root)
        rule = {'id': 'qemu', 'mode': 'prose', 'files': ['*.md'],
                'pattern': r'(QEMU )\d+\.\d+\.\d+', 'replacement': r'\g<1>{qemu}'}
        current = manifest(NEW, [rule])
        current['values']['qemu'] = '9.0.0'
        self.assertEqual(sync.report(sync.scan(self.root, current), {'qemu'}), 1)
        self.assertEqual(sync.write(self.root, current, dry_run=False), 0)
        self.assertEqual((self.root / 'guide.md').read_text(), 'Uses QEMU 8.2.2 here.\n')

    def test_filter_derives_compact_date(self):
        self.assertEqual(sync.expand('{release}/{release:nodash}', {'release': '2026-10-14'}),
                         '2026-10-14/20261014')
        with self.assertRaises(ValueError):
            sync.expand('{release:unknown}', {'release': '1'})

    def test_files_filter_limits_a_rule(self):
        rule = {'id': 'only-docs', 'files': ['docs/*'], 'pattern': 'openroad/orfs@sha256:[0-9a-f]{64}',
                'replacement': '{orfs_image}'}
        self.assertEqual(sync.scan(self.root, manifest(NEW, [rule]))['only-docs']['edit'], [])

    def test_repository_manifest_loads(self):
        sync.load(sync.HERE / 'environments.json')


if __name__ == '__main__':
    unittest.main()
