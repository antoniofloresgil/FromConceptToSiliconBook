"""Integration regressions for the independently executable practice download."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'labs'))
import run as runner
from tools.package import BOOK_URL


class PracticeDownload(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        runner.pack()
        cls.archive = ROOT / 'downloads/hardware-design-labs.zip'

    def setUp(self):
        (ROOT / 'labs/build').mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='practice-package-', dir=ROOT / 'labs/build')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        with zipfile.ZipFile(self.archive) as archive:
            archive.extractall(self.root)

    def command(self, *args):
        return subprocess.run([sys.executable, 'labs/run.py', *args], cwd=self.root,
                              text=True, capture_output=True, timeout=30)

    def test_no_book_text_or_publishing_environment(self):
        for name in ['chapters', 'appendices', 'figures', 'tools', '_quarto.yml', 'references.bib', 'summary.qmd', 'labs/tools/test_package.py']:
            self.assertFalse((self.root / name).exists(), name)
        self.assertFalse(list(self.root.rglob('*.qmd')))
        for name in ['README.md', 'LAB-PROVENANCE.json', 'SHA256SUMS.json',
                     'LICENSES/MIT.txt', 'LICENSES/CC-BY-SA-4.0.txt', 'NOTICE.md', 'labs/Dockerfile']:
            self.assertTrue((self.root / name).is_file(), name)

    def test_extracted_package_checks_without_chapters(self):
        guide = (self.root / 'labs/README.md').read_text(encoding='utf-8')
        self.assertNotIn('../learning-paths.qmd', guide)
        self.assertIn(BOOK_URL + 'learning-paths.html', guide)
        result = self.command('check')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('29 listing origins', result.stdout)
        guides = subprocess.run([sys.executable, 'labs/tools/check_recipes.py'], cwd=self.root,
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(guides.returncode, 0, guides.stdout + guides.stderr)

    def test_changed_reference_fails_before_tool_execution(self):
        target = self.root / 'labs/01-foundations/rtl/foundation_alu.sv'
        target.write_text(target.read_text(encoding='utf-8') + '\n// changed reference\n', encoding='utf-8')
        result = self.command('run', 'foundations')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('checksum mismatch', result.stderr)
        self.assertFalse((self.root / 'labs/build/report.json').exists())

    def test_missing_checksum_index_fails_closed(self):
        (self.root / 'SHA256SUMS.json').unlink()
        result = self.command('check')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('missing SHA256SUMS.json', result.stderr)

    def test_incomplete_origin_mapping_fails_with_valid_checksums(self):
        path = self.root / 'LAB-PROVENANCE.json'
        manifest = json.loads(path.read_text(encoding='utf-8'))
        manifest['listing_origins'].pop()
        path.write_text(json.dumps(manifest), encoding='utf-8')
        index_path = self.root / 'SHA256SUMS.json'
        index = json.loads(index_path.read_text(encoding='utf-8'))
        index['LAB-PROVENANCE.json'] = hashlib.sha256(path.read_bytes()).hexdigest()
        index_path.write_text(json.dumps(index), encoding='utf-8')
        result = self.command('check')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('provenance is incomplete', result.stderr)

    def test_authoring_commands_do_not_silently_skip_missing_chapters(self):
        for command in ['sync', 'pack']:
            result = self.command(command)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('full book repository', result.stderr)


if __name__ == '__main__':
    unittest.main()
