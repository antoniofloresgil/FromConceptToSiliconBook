#!/usr/bin/env python3
"""Tests for the slide-deck generator (standard library only)."""
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_slides as slides  # noqa: E402


class CleanTextTests(unittest.TestCase):
    def setUp(self):
        self.titles = {'sec-pipelines': 'Pipelines'}

    def test_references_citations_and_links_become_plain_text(self):
        text = 'See @sec-pipelines and @fig-x [@laforest2020, p. 3]. A [link](a.qmd#b){.x} stays readable.'
        out = slides.clean(text, self.titles)
        self.assertEqual(out, 'See Pipelines and the figure. A link stays readable.')

    def test_activity_labels_and_anchors_are_removed(self):
        text = '[Core · P1 · C0](../learning-paths.qmd#x){#act-a .learning-activity} Run it.[]{#ref-a .reference-destination}'
        self.assertEqual(slides.clean(text, self.titles), 'Run it.')

    def test_sentences_do_not_split_on_abbreviations(self):
        parts = slides.sentences('Use a tool, e.g. Verilator. Then run it.')
        self.assertEqual(parts, ['Use a tool, e.g. Verilator.', 'Then run it.'])

    def test_shorten_keeps_markup_balanced(self):
        out = slides.shorten('A `very long' + ' word' * 40 + '` sentence.', 10)
        self.assertEqual(out.count('`') % 2, 0)


class DeckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        titles = slides.heading_titles()
        cls.decks = []
        for number, (path, part) in enumerate(slides.chapter_order(), 1):
            name, count, target, _ = slides.write_deck(number, path, part, number, titles)
            cls.decks.append((slides.SLIDES / 'decks' / name, count))

    def test_every_chapter_has_a_deck(self):
        self.assertEqual(len(self.decks), len(slides.chapter_order()))

    def test_slide_counts_stay_in_the_agreed_range(self):
        for deck, count in self.decks:
            self.assertGreaterEqual(count, slides.MIN_SLIDES, deck.name)
            self.assertLessEqual(count, slides.MAX_SLIDES, deck.name)

    def test_decks_carry_no_unresolved_quarto_syntax(self):
        for deck, _ in self.decks:
            text = deck.read_text(encoding='utf-8')
            self.assertIsNone(re.search(r'@(fig|sec|tbl)-|\[@|\.learning-activity|\{#ref-', text), deck.name)

    def test_figure_assets_exist(self):
        for deck, _ in self.decks:
            for ref in re.findall(r'\]\(\.\./_assets/([^)]+)\)', deck.read_text(encoding='utf-8')):
                self.assertTrue((slides.SLIDES / '_assets' / ref).is_file(), f'{deck.name}: {ref}')


if __name__ == '__main__':
    unittest.main()
