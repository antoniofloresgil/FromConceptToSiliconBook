"""Guard inline-code text/escaping preservation across the PDF-only filter."""
from pathlib import Path
import shutil
import subprocess
import unittest

FILTER = Path(__file__).with_name('inline-code.lua').resolve()


@unittest.skipUnless(shutil.which('quarto'), 'Requires the maintained book environment')
class InlineCode(unittest.TestCase):
    def render(self, code, target='latex', filtered=True):
        args = ['quarto', 'pandoc', '--from=markdown', '--to=' + target, '--wrap=none']
        if filtered:
            args += ['--lua-filter', str(FILTER)]
        return subprocess.check_output(args, input='`' + code + '`\n', text=True, encoding='utf-8')

    def test_long_identifiers_keep_native_tex_escaping(self):
        code = 'path/to/' + ('ab_cd%{}\\$#~^&' * 6)
        original = self.render(code, filtered=False)
        wrapped = self.render(code)
        self.assertIn('\\allowbreak{}', wrapped)
        self.assertEqual(wrapped.replace('}\\allowbreak{}\\texttt{', ''), original)

    def test_short_code_is_unchanged(self):
        self.assertEqual(self.render('a <= b'), self.render('a <= b', filtered=False))

    def test_html_is_unchanged(self):
        code = 'sha256:' + '0123456789abcdef' * 8
        self.assertEqual(self.render(code, 'html'), self.render(code, 'html', False))

    def test_non_ascii_is_not_split_inside_utf8(self):
        code = 'signal_' + '\u03b1\u03b2' * 20
        self.assertEqual(self.render(code), self.render(code, filtered=False))


if __name__ == '__main__':
    unittest.main()
