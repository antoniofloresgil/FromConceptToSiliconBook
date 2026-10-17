"""Regression checks against false joins and stale physical evidence."""
import json
from pathlib import Path
import tempfile
import unittest
from collect import physical
from run import ROOT, SOURCE, load_manifest, sha


class CollectionGates(unittest.TestCase):
    def setUp(self):
        base=ROOT/'labs/build';base.mkdir(parents=True,exist_ok=True)
        temp=tempfile.TemporaryDirectory(prefix='case-gate-',dir=base)
        self.addCleanup(temp.cleanup)
        self.directory=Path(temp.name).resolve()
        self.assertTrue(self.directory.is_relative_to(base.resolve()))
        self.manifest=load_manifest()
        artifact=self.directory/'timing.txt';artifact.write_text('actual observed result')
        self.report={'status':'completed','manifest_sha256':sha(SOURCE/'manifest.json'),
                     'rtl_sha256':self.manifest['rtl_sha256'],
                     'parameters':dict(self.manifest['parameters']),
                     'commands':[{'exit_code':0}], 'artifacts':{'timing.txt':sha(artifact)}}

    def check(self):
        path=self.directory/'report.json';path.write_text(json.dumps(self.report))
        return physical(path,self.manifest)

    def test_matching_record_is_accepted(self): self.check()

    def test_changed_artifact_is_rejected(self):
        (self.directory/'timing.txt').write_text('a different result')
        with self.assertRaises(ValueError): self.check()

    def test_wrong_manifest_is_rejected(self):
        self.report['manifest_sha256']='0'*64
        with self.assertRaises(ValueError): self.check()

    def test_wrong_rtl_is_rejected(self):
        self.report['rtl_sha256']={}
        with self.assertRaises(ValueError): self.check()

    def test_failed_command_is_rejected(self):
        self.report['commands'][0]['exit_code']=1
        with self.assertRaises(ValueError): self.check()

    def test_different_parameters_are_rejected(self):
        self.report['parameters']['MAX_LENGTH']=16
        with self.assertRaises(ValueError): self.check()


if __name__=='__main__': unittest.main()
