#!/usr/bin/env python3
"""Tests for the table caption checker."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_tables as checker  # noqa: E402

TABLE = '| a | b |\n| --- | --- |\n| 1 | 2 |\n'


def run(text, extra=''):
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / 'x.qmd'
        path.write_text(text + extra, encoding='utf-8')
        checker.ROOT = Path(folder)
        return checker.check([path])


class TableCaptionTests(unittest.TestCase):
    def test_captioned_table_passes(self):
        problems, count, refs = run(TABLE + '\n: What it shows {#tbl-one}\n\nSee @tbl-one.\n')
        self.assertEqual((problems, count, refs), ([], 1, 1))

    def test_missing_caption_is_reported(self):
        problems, _, _ = run(TABLE + '\nText follows.\n')
        self.assertEqual(len(problems), 1)
        self.assertIn('without a caption', problems[0])

    def test_attribute_only_caption_is_rejected(self):
        problems, _, _ = run(TABLE + '\n: {tbl-colwidths="[50,50]"}\n')
        self.assertEqual(len(problems), 1)

    def test_extra_attributes_are_allowed(self):
        problems, _, _ = run(TABLE + '\n: Wide first column {#tbl-wide tbl-colwidths="[70,30]"}\n')
        self.assertEqual(problems, [])

    def test_duplicate_identifier_is_reported(self):
        problems, _, _ = run(TABLE + '\n: First {#tbl-same}\n\n' + TABLE + '\n: Second {#tbl-same}\n')
        self.assertTrue(any('duplicate' in p for p in problems))

    def test_unresolved_reference_is_reported(self):
        problems, _, _ = run('See @tbl-missing.\n')
        self.assertTrue(any('no table' in p for p in problems))

    def test_table_in_code_fence_is_ignored(self):
        problems, count, _ = run('```text\n' + TABLE + '```\n')
        self.assertEqual((problems, count), ([], 0))

    def test_book_sources_pass(self):
        checker.ROOT = Path(__file__).resolve().parents[2]
        problems, count, _ = checker.check(checker.sources())
        self.assertEqual(problems, [])
        self.assertGreater(count, 200)


if __name__ == '__main__':
    unittest.main()
