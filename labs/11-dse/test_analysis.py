"""Check selection, comparison contracts and the independent division oracle."""
import copy
import csv
from pathlib import Path
import unittest
from analyse import analyse
from vectors import answers

class DesignExploration(unittest.TestCase):
    def setUp(self):
        with Path(__file__).with_name('illustrative.csv').open() as source:
            self.rows=list(csv.DictReader(source))
    def test_frequency_changes_the_ranking(self):
        results={r['candidate']:r for r in analyse(self.rows,'base',50000,150)}
        self.assertGreater(results['small-cache']['geomean_speedup'],results['large-cache']['geomean_speedup'])
        self.assertTrue(results['small-cache']['pareto'])
        self.assertFalse(results['large-cache']['pareto'])
        self.assertEqual(results['too-large']['status'],'rejected')
    def test_unmatched_binary_rejected(self):
        self.rows[3]['binary_sha256']='different-program'
        with self.assertRaisesRegex(ValueError,'Unmatched'):analyse(self.rows,'base',50000,150)
    def test_requested_clock_is_not_measurement(self):
        self.rows[3]['frequency_basis']='requested'
        with self.assertRaisesRegex(ValueError,'achieved'):analyse(self.rows,'base',50000,150)
    def test_failed_timing_not_ranked(self):
        self.rows[3]['timing_status']='fail'
        r={r['candidate']:r for r in analyse(self.rows,'base',50000,150)}
        self.assertEqual(r['small-cache']['status'],'rejected')
        self.assertNotIn('pareto',r['small-cache'])
    def test_no_zero_frequency(self):
        for row in self.rows[3:6]:row['frequency_mhz']='0'
        with self.assertRaisesRegex(ValueError,'cycle/frequency'):analyse(self.rows,'base',50000,150)
    def test_same_workload_set(self):
        del self.rows[3]
        with self.assertRaisesRegex(ValueError,'workload set'):analyse(self.rows,'base',50000,150)
    def test_mixed_origins_not_ranked_together(self):
        for row in self.rows[3:6]:row['origin']='measured'
        with self.assertRaisesRegex(ValueError,'origin'):analyse(self.rows,'base',50000,150)
    def test_duplicate_workload_rejected(self):
        self.rows.append(copy.deepcopy(self.rows[3]))
        with self.assertRaisesRegex(ValueError,'workload set'):analyse(self.rows,'base',50000,150)
    def test_identical_metrics_do_not_dominate_each_other(self):
        self.rows=self.rows[:3]+[{**r,'candidate':'equal'} for r in self.rows[:3]]
        results=analyse(self.rows,'base',50000,150)
        self.assertTrue(all(r['pareto'] for r in results))
    def test_signed_division_truncates_toward_zero(self):
        self.assertEqual(answers(0xfffffff9,3)[:2],[0xfffffffe,0xffffffff])
        self.assertEqual(answers(7,0xfffffffd)[:2],[0xfffffffe,1])
    def test_architectural_special_cases(self):
        self.assertEqual(answers(0x80000000,0xffffffff)[:2],[0x80000000,0])
        self.assertEqual(answers(7,0),[0xffffffff,7,0xffffffff,7])

if __name__=='__main__':unittest.main()
