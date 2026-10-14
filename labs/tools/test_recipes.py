"""Reject documented ownership/namespace/case regressions without Docker."""
from pathlib import Path
import tempfile
import unittest
import check_recipes as audit

class RecipeContracts(unittest.TestCase):
    def setUp(self):
        self.contracts={'image_tag':'from-concept-labs:2026.10','ci_image_tag':'from-concept-labs:ci',
                        'outputs':{'wally_build_dir':'/work/labs/build/wally-platform'}}
        self.command=('docker run --rm --network none --user "$(id -u):$(id -g)" --env HOME=/tmp '
                      '--mount "type=bind,source=$PWD,target=/work" from-concept-labs:2026.10 python labs/run.py run all')
    def test_linux_policy(self):self.assertEqual(audit.docker_errors('bash',self.command,self.contracts),[])
    def test_root_mount_rejected(self):
        command=self.command.replace('--user "$(id -u):$(id -g)" ','')
        self.assertTrue(any('UID/GID' in e for e in audit.docker_errors('bash',command,self.contracts)))
    def test_home_required(self):
        self.assertTrue(audit.docker_errors('bash',self.command.replace('--env HOME=/tmp ',''),self.contracts))
    def test_powershell_without_posix_identity(self):
        command=self.command.replace('--user "$(id -u):$(id -g)" ','')
        self.assertEqual(audit.docker_errors('powershell',command,self.contracts),[])
    def test_posix_id_in_powershell_rejected(self):
        self.assertTrue(audit.docker_errors('powershell',self.command,self.contracts))
    def test_wally_cannot_overwrite_unit_report(self):
        command=self.command.replace('run all','run dotproduct-wally')
        self.assertTrue(any('overwrite' in e for e in audit.docker_errors('bash',command,self.contracts)))
    def test_version_tag_drift(self):
        self.assertTrue(audit.docker_errors('bash',self.command.replace(':2026.10',':latest'),self.contracts))
    def test_case_sensitive_path_on_windows(self):
        with tempfile.TemporaryDirectory(dir=audit.ROOT/'labs/build') as temporary:
            root=Path(temporary);(root/'Source.sv').write_text('module example; endmodule')
            self.assertEqual(audit.exact_path(root,'Source.sv'),root/'Source.sv')
            with self.assertRaisesRegex(ValueError,'cased'):audit.exact_path(root,'source.sv')
    def test_clock_port_case_is_preserved(self):
        text='module accumulator(\ninput logic Clk, Reset,\noutput logic [15:0] Sum\n); endmodule'
        self.assertEqual(audit.module_ports(text,'accumulator'),['Clk','Reset','Sum'])
    def test_validated_wally_fork_is_accepted(self):
        text='repository: antoniofloresgil/cvw\n          ref: '+audit.WALLY_REVISION
        audit.validate_wally_checkout(text,audit.WALLY_REPOSITORY,audit.WALLY_REVISION)
    def test_fork_commit_in_upstream_is_rejected(self):
        text='repository: openhwgroup/cvw\n          ref: '+audit.WALLY_REVISION
        with self.assertRaisesRegex(ValueError,'repository/revision'):
            audit.validate_wally_checkout(text,audit.WALLY_REPOSITORY,audit.WALLY_REVISION)
    def test_unvalidated_wally_revision_is_rejected(self):
        text='repository: antoniofloresgil/cvw\n          ref: main'
        with self.assertRaisesRegex(ValueError,'repository/revision'):
            audit.validate_wally_checkout(text,audit.WALLY_REPOSITORY,audit.WALLY_REVISION)

if __name__=='__main__':
    (audit.ROOT/'labs/build').mkdir(parents=True,exist_ok=True)
    unittest.main()
