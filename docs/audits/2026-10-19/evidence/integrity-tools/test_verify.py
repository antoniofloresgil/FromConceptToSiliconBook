"""Reject stale artifacts, escaped paths, failed jobs and spurious defect exits."""
import json
from pathlib import Path
import tempfile
import unittest
import verify


class Integrity(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.log=self.root/'job.log';self.src=self.root/'rtl.sv'
        self.log.write_text('observed intended defect\n');self.src.write_text('module rtl; endmodule\n')
        self.path=self.root/'report.json'
        self.data=dict(status='pass',sources={'rtl.sv':verify.sha(self.src)},artifacts={'job.log':verify.sha(self.log)},
            jobs=[dict(exit_code=1,expected_exit=1,status='pass',log='job.log',required_marker='observed intended defect')])

    def check(self):
        self.path.write_text(json.dumps(self.data));return verify.report(self.root,self.path,'formal')

    def test_expected_defect_is_accepted_only_with_marker(self):
        self.assertEqual(self.check()['commands'],1)
        self.log.write_text('tool crashed\n');self.data['artifacts']['job.log']=verify.sha(self.log)
        with self.assertRaisesRegex(ValueError,'Missing formal'):self.check()

    def test_valid_metadata_does_not_hide_changed_bytes(self):
        self.src.write_text('changed source\n')
        with self.assertRaisesRegex(ValueError,'Checksum mismatch'):self.check()
        self.data['sources']['rtl.sv']=verify.sha(self.src);self.log.write_text('changed artifact\n')
        with self.assertRaisesRegex(ValueError,'Checksum mismatch'):self.check()

    def test_escape_and_empty_inventory_rejected(self):
        with self.assertRaisesRegex(ValueError,'escapes'):verify.contained(self.root,'../outside')
        self.data['artifacts']={}
        with self.assertRaisesRegex(ValueError,'Empty'):self.check()

    def test_incomplete_or_failed_jobs_rejected(self):
        self.data['status']='running'
        with self.assertRaisesRegex(ValueError,'Incomplete'):self.check()
        self.data['status']='pass';self.data['jobs'][0]['exit_code']=None
        with self.assertRaisesRegex(ValueError,'noninteger'):self.check()


if __name__=='__main__':unittest.main()
