#!/usr/bin/env python3
"""Tests for the section numbering and identifiers of the book sources."""
from pathlib import Path
import re
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sections  # noqa: E402

SAMPLE = '''# Chapter title {#sec-title}

## Concepts

### Memory hierarchy and technology

```text
### not a heading
```

### AXI: why independent channels matter

#### The five channels

### Concepts

## Key ideas {.unnumbered .unlisted}

## Concepts
'''


class SectionTests(unittest.TestCase):
    def parse(self, label='13'):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'x.qmd'
            path.write_text(SAMPLE, encoding='utf-8')
            return sections.sections(path, label)[1]

    def test_identifiers_follow_the_pandoc_algorithm(self):
        self.assertEqual(sections.auto_identifier('Memory hierarchy and technology'), 'memory-hierarchy-and-technology')
        self.assertEqual(sections.auto_identifier('AXI: why independent channels matter'), 'axi-why-independent-channels-matter')
        self.assertEqual(sections.auto_identifier('1. Start here'), 'start-here')
        self.assertEqual(sections.auto_identifier('!!!'), 'section')

    def test_numbers_follow_the_rendered_book(self):
        found = self.parse()
        numbers = [(s['title'], s['number']) for s in found]
        self.assertEqual(numbers[0], ('Chapter title', '13'))
        self.assertIn(('Memory hierarchy and technology', '13.1.1'), numbers)
        self.assertIn(('The five channels', '13.1.2.1'), numbers)
        self.assertEqual([s['number'] for s in found if s['title'] == 'Key ideas'], [''])

    def test_duplicate_titles_get_numbered_suffixes_and_code_is_skipped(self):
        found = self.parse()
        ids = [s['id'] for s in found]
        self.assertEqual([i for i in ids if i.startswith('concepts')], ['concepts', 'concepts-1', 'concepts-2'])
        self.assertNotIn('not-a-heading', ids)

    def test_chapter_and_appendix_labels(self):
        files = sections.book_files()
        labels = [label for _, label in files if label]
        self.assertEqual(labels[0], '1')
        self.assertIn('F', labels)
        self.assertTrue(all(re.fullmatch(r'\d+|[A-Z]', label) for label in labels))

    @unittest.skipUnless((sections.ROOT / '_book').is_dir(), 'needs a rendered book')
    def test_numbers_and_identifiers_agree_with_a_rendered_book(self):
        checked = 0
        for path, label in sections.book_files():
            html = sections.ROOT / '_book' / path.relative_to(sections.ROOT).with_suffix('.html')
            if label is None or not html.is_file():
                continue
            rendered = {m[3]: m[2] for m in re.finditer(r'<h([2-6]) data-number="([^"]+)"[^>]*data-anchor-id="([^"]+)"', html.read_text(encoding='utf-8'))}
            for section in sections.sections(path, label)[1]:
                if section['level'] >= 2 and section['number'] and section['id'] in rendered:
                    self.assertEqual(rendered[section['id']], section['number'], section['id'])
                    checked += 1
        self.assertGreater(checked, 500)


if __name__ == '__main__':
    unittest.main()
