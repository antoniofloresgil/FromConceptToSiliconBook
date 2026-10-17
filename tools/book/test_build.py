"""Regression checks for stale-output rejection and failure-safe release handling."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('book_build', Path(__file__).with_name('build.py'))
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class ReleaseSafety(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for folder in ['chapters', 'appendices', 'figures', '_book/release']:
            (self.root / folder).mkdir(parents=True)
        (self.root / 'index.qmd').write_text('# Test book\n')
        self.previous = self.root / '_book/release/previous.txt'
        self.previous.write_text('Previously validated output')
        # An old source-directory render must never satisfy release checks.
        (self.root / 'index.html').write_text('Old HTML')
        (self.root / 'From-Concept-to-Silicon.pdf').write_bytes(b'Old PDF')
        self.addCleanup(patch.stopall)
        patch.object(builder, 'ROOT', self.root).start()
        patch.object(builder, 'command', return_value='test-tool-version').start()

    def assert_previous_survives(self):
        self.assertEqual(self.previous.read_text(), 'Previously validated output')
        self.assertFalse((self.root / '_book/release-incoming').exists())

    def test_render_failure_keeps_previous_release(self):
        with patch.object(builder.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'quarto')):
            with self.assertRaises(subprocess.CalledProcessError):
                builder.main()
        self.assert_previous_survives()

    def test_old_pdf_cannot_hide_missing_new_pdf(self):
        def html_only(args, cwd, check, env):
            self.assertFalse((cwd / 'index.html').exists())
            self.assertFalse((cwd / 'From-Concept-to-Silicon.pdf').exists())
            output = cwd / '_book'
            output.mkdir()
            (output / 'index.html').write_text('From-Concept-to-Silicon.pdf')
        with patch.object(builder.subprocess, 'run', side_effect=html_only):
            with self.assertRaisesRegex(RuntimeError, 'Missing release artifact: From-Concept-to-Silicon.pdf'):
                builder.main()
        self.assert_previous_survives()

if __name__ == '__main__':
    unittest.main()
