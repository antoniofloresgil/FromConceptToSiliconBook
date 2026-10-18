"""Check consultation links, coverage and stable catalogue identities."""
import copy
import csv
import io
import json
import unittest
import reference


class Consultation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=reference.load()
        cls.activities=json.loads((reference.ROOT/'tools/book/learning-paths.json').read_text(encoding='utf-8'))['activities']

    def test_all_destinations_and_dependency_profiles(self):
        reference.validate(self.data,self.activities)
        for profile in self.data['profiles'].values():
            for lab in profile['labs']:
                self.assertTrue((reference.ROOT/'labs'/lab/'README.md').is_file())

    def test_matrix_preserves_every_activity_and_destination(self):
        output=reference.outputs(self.data,self.activities)
        rows=list(csv.DictReader(io.StringIO(output['downloads/experiment-matrix.csv'])))
        self.assertEqual({x['id'] for x in rows},{e['id'] for e in self.activities})
        self.assertEqual(len(rows),len(self.activities))
        for row in rows:
            self.assertTrue(row['tools'] and row['requires'] and row['contract'])
            self.assertTrue(row['book_url'].endswith('#act-'+row['id']))

    def test_unknown_activity_or_missing_lab_is_rejected(self):
        invalid=copy.deepcopy(self.data);invalid['overrides']['unknown']={}
        with self.assertRaisesRegex(ValueError,'Unknown activity'):reference.validate(invalid,self.activities)
        invalid=copy.deepcopy(self.data);invalid['labs'].pop()
        with self.assertRaisesRegex(ValueError,'Lab directory coverage'):reference.validate(invalid,self.activities)

    def test_stale_or_duplicate_terms_are_rejected(self):
        invalid=copy.deepcopy(self.data);invalid['terms'].append(invalid['terms'][0])
        with self.assertRaisesRegex(ValueError,'Duplicate term'):reference.validate(invalid,self.activities)
        invalid=copy.deepcopy(self.data);invalid['terms'][0]['locations'][0]['anchor']='absent-anchor'
        with self.assertRaisesRegex(ValueError,'Missing term destination'):reference.validate(invalid,self.activities)

    def test_aliases_and_real_print_page_references(self):
        output=reference.outputs(self.data,self.activities)
        self.assertIn('\n\n## B {.reference-entry}\n',output['term-index.qmd'])
        self.assertNotIn('. `\\textnormal{',output['term-index.qmd'])
        for term in self.data['terms']:
            self.assertIn('{#gloss-'+term['id']+' .reference-entry}',output['glossary.qmd'])
            for alias in term.get('aliases',[]):self.assertIn('['+alias+']',output['term-index.qmd'])
            for location in term['locations']:
                self.assertIn('\\pageref{'+location['anchor']+'}',output['term-index.qmd'])


if __name__=='__main__':unittest.main()
