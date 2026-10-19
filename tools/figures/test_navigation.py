"""Reject broken editorial figure navigation before rendering."""
import unittest
from print_audit import check_navigation


class Navigation(unittest.TestCase):
    def row(self,identity):return dict(figure_id=identity,caption='An explanatory caption.')
    def test_accepts_a_cross_chapter_reference(self):
        check_navigation([self.row('fig-cache')],'Follow @fig-cache to the refill path.')
    def test_rejects_missing_and_duplicate_ids(self):
        for rows in [[self.row(None)],[self.row('fig-cache')]*2]:
            with self.assertRaises(ValueError):check_navigation(rows,'See @fig-cache.')
    def test_rejects_uncited_and_prefix_only_matches(self):
        for text in ['See Figure 2.','See @fig-cache-extra.']:
            with self.assertRaises(ValueError):check_navigation([self.row('fig-cache')],text)


if __name__=='__main__':unittest.main()
