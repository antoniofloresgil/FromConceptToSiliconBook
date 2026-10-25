#!/usr/bin/env python3
"""Tests for the subject index generator."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import subject_index as index  # noqa: E402


def section(order, title, text, identifier=None):
    return dict(title=title, text=text, id=identifier or f'id-{order}', number=f'1.{order}', order=order,
                file=index.ROOT / 'chapters/x.qmd')


class MatchingTests(unittest.TestCase):
    def count(self, entry, text, title=''):
        pattern, removed = index.compile_entry(entry)
        return index.score(pattern, removed, title, text)

    def test_plurals_and_hyphen_variants_match(self):
        entry = dict(term='cache line')
        self.assertEqual(self.count(entry, 'A cache line and two cache-lines and cache lines.')[1], 3)

    def test_exact_case_for_acronyms(self):
        entry = dict(term='CDC', exact=True)
        self.assertEqual(self.count(entry, 'CDC and cdc and CDCs')[1], 2)

    def test_excluded_phrases_do_not_count(self):
        entry = dict(term='AXI4', exact=True, **{'not': ['AXI4-Lite']})
        self.assertEqual(self.count(entry, 'AXI4 and AXI4-Lite')[1], 1)

    def test_heading_and_bold_raise_the_score(self):
        entry = dict(term='burst')
        plain = self.count(entry, 'one burst')[0]
        self.assertGreater(self.count(entry, 'one burst', title='Burst transfers')[0], plain)
        self.assertGreater(self.count(entry, 'a **burst** here')[0], plain)


class LocationTests(unittest.TestCase):
    def test_threshold_limit_and_book_order(self):
        book = [section(i, f'S{i}', 'burst ' * (i % 4 + 1)) for i in range(10)]
        unique = {s['id'] for s in book}
        entries = [dict(term='burst', limit=3), dict(term='rare', **{'min': 1})]
        found = index.locate(entries, book, unique)
        self.assertEqual(len(found['burst']), 3)
        self.assertEqual([s['order'] for s in found['burst']], sorted(s['order'] for s in found['burst']))
        self.assertTrue(all(s['text'].count('burst') >= 3 for s in found['burst']))
        self.assertEqual(found['rare'], [])

    def test_sections_with_repeated_identifiers_are_never_listed(self):
        book = [section(1, 'Concepts', 'burst burst', 'concepts'), section(2, 'Concepts', 'burst burst', 'concepts')]
        found = index.locate([dict(term='burst')], book, index.unique_ids(book))
        self.assertEqual(found['burst'], [])

    def test_clean_text_drops_code_links_and_tables_rules(self):
        text = index.clean_text(['See [burst](file.qmd#burst).', '```c', 'burst();', '```', '| --- | --- |', 'plain'])
        self.assertNotIn('burst();', text)
        self.assertNotIn('file.qmd', text)
        self.assertIn('plain', text)


class DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = index.load()
        cls.glossary = {t['id'] for t in json.loads((index.ROOT / 'tools/book/reference-data.json').read_text(encoding='utf-8'))['terms']}

    def test_entries_are_unique_and_reference_known_glossary_terms_and_targets(self):
        terms = [e['term'] for e in self.data['entries']]
        self.assertEqual(len(terms), len(set(terms)))
        for entry in self.data['entries']:
            if 'glossary' in entry:
                self.assertIn(entry['glossary'], self.glossary, entry['term'])
            if 'see' in entry:
                self.assertIn(entry['see'], terms, entry['term'])
                self.assertNotIn('see', next(e for e in self.data['entries'] if e['term'] == entry['see']))

    def test_generated_page_is_fresh_and_every_entry_has_a_location(self):
        text, problems, _, _ = index.render(self.data)
        self.assertEqual(problems, [])
        self.assertEqual(index.OUTPUT.read_text(encoding='utf-8'), text)

    def test_page_numbers_are_requested_only_for_unique_labels(self):
        text = index.OUTPUT.read_text(encoding='utf-8')
        labels = [m for m in __import__('re').findall(r'\\pageref\{([^}]+)\}', text)]
        book = index.collect()
        counts = {}
        for s in book:
            counts[s['id']] = counts.get(s['id'], 0) + 1
        self.assertTrue(labels)
        self.assertTrue(all(counts[label] == 1 for label in labels))


if __name__ == '__main__':
    unittest.main()
