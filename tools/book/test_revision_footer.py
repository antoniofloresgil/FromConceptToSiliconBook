"""Check the revision note for clean, modified and unversioned builds."""
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location('revision_footer', Path(__file__).with_name('revision_footer.py'))
footer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(footer)


class RevisionNoteTest(unittest.TestCase):
    def test_clean_build_names_revision_and_date(self):
        text = footer.note('b4280c5', 'false', '2026-10-23')
        self.assertIn('Live edition, revision <code>b4280c5</code>', text)
        self.assertIn('built 2026-10-23', text)

    def test_modified_sources_are_marked_as_preview(self):
        self.assertIn('Preview build', footer.note('b4280c5', 'true', '2026-10-23'))
        self.assertIn('modifications', footer.note('b4280c5', 'true', '2026-10-23'))
        self.assertIn('Preview build', footer.note('b4280c5', 'unknown', '2026-10-23'))

    def test_unversioned_sources_never_claim_a_revision(self):
        text = footer.note(None, 'unknown', '2026-10-23')
        self.assertIn('unversioned sources', text)
        self.assertNotIn('<code>', text)

    def test_revision_is_sanitised(self):
        import os
        os.environ['BOOK_REVISION'] = '"><script>'
        try:
            self.assertIsNone(footer.revision())
        finally:
            del os.environ['BOOK_REVISION']


if __name__ == '__main__':
    unittest.main()
