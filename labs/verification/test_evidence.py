"""Release-evidence gate: reject stale/skipped/false passes and retain gaps."""
import copy
from pathlib import Path
import tempfile
import unittest
import evidence

class EvidenceGate(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(dir=evidence.ROOT/'labs/build')
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)
        (self.root/'rtl.sv').write_text('module example; endmodule\n')
        (self.root/'check.log').write_text('PASS checked result\n')
        self.record={'status':'pass','commands':[{'log':'check.log','returncode':0}],
                     'artifacts':{'check.log':evidence.digest(self.root/'check.log')}}
        self.report={'sources':{'rtl.sv':evidence.digest(self.root/'rtl.sv')},'labs':{'unit':self.record}}
        self.plan={'project':'gate-test','sources':{'unit':['rtl.sv']},'requirements':[
            {'id':'NUM','requirement':'exact result','level':'rtl-unit','scope':'one reviewed configuration',
             'coverage':'directed check','required_reference':True,
             'evidence':{'report':'unit','lab':'unit','markers':['PASS checked result']}},
            {'id':'STA','requirement':'timing','level':'physical','scope':'target not selected',
             'coverage':'setup/hold','status':'not_run','rationale':'No target STA report'}]}
    def collect(self):
        return evidence.build(self.root,self.plan,{'unit':self.report})
    def test_pass_keeps_physical_gap(self):
        result=self.collect()
        self.assertEqual(result['summary']['pass'],1)
        self.assertEqual(result['summary']['not_run'],1)
        self.assertEqual(evidence.exit_status(result,self.plan),0)
    def test_changed_source_rejected(self):
        (self.root/'rtl.sv').write_text('module different; endmodule\n')
        with self.assertRaisesRegex(ValueError,'source identity'):self.collect()
    def test_changed_log_rejected(self):
        (self.root/'check.log').write_text('PASS different run\n')
        with self.assertRaisesRegex(ValueError,'artifact'):self.collect()
    def test_missing_log_rejected(self):
        (self.root/'check.log').unlink()
        with self.assertRaisesRegex(ValueError,'artifact'):self.collect()
    def test_false_pass_rejected(self):
        self.record['commands'][0]['returncode']=1
        with self.assertRaisesRegex(ValueError,'PASS record'):self.collect()
    def test_skipped_checker_rejected(self):
        self.plan['requirements'][0]['evidence']['markers']=['PASS checker that did not run']
        with self.assertRaisesRegex(ValueError,'completion'):self.collect()
    def test_missing_required_report_fails_gate(self):
        result=evidence.build(self.root,self.plan,{'unit':None})
        self.assertEqual(result['requirements'][0]['status'],'not_run')
        self.assertEqual(evidence.exit_status(result,self.plan),1)
    def test_failed_check_remains_failure(self):
        self.record['status']='fail';self.record['commands'][0]['returncode']=1
        result=self.collect()
        self.assertEqual(result['requirements'][0]['status'],'fail')
        self.assertEqual(evidence.exit_status(result,self.plan),1)
    def test_no_evidence_cannot_be_marked_pass(self):
        self.plan['requirements'][1]['status']='pass'
        with self.assertRaisesRegex(ValueError,'test result requires evidence'):self.collect()
    def test_unknown_required_result_fails_gate(self):
        row=self.plan['requirements'][0]
        del row['evidence'];row.update(status='unknown',rationale='Solver timeout')
        self.assertEqual(evidence.exit_status(self.collect(),self.plan),1)
    def test_duplicate_requirement_rejected(self):
        self.plan['requirements'].append(copy.deepcopy(self.plan['requirements'][0]))
        with self.assertRaisesRegex(ValueError,'Duplicate'):self.collect()
    def test_path_escape_rejected(self):
        self.plan['sources']['unit']=['../unrelated.sv']
        with self.assertRaisesRegex(ValueError,'escapes'):self.collect()
    def test_student_variant_cannot_use_reference_claim(self):
        self.record['student_rtl']={'custom.sv':'identity'}
        with self.assertRaisesRegex(ValueError,'reference RTL'):self.collect()

if __name__=='__main__':
    (evidence.ROOT/'labs/build').mkdir(parents=True,exist_ok=True)
    unittest.main()
