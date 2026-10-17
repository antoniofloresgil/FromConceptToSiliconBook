"""Regress the actual address collision and source/manifest drift."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from platform_map import audit_config,check_local_map,validate_window

HERE=Path(__file__).resolve().parent
class PlatformMap(unittest.TestCase):
    def setUp(self):
        self.manifest=json.loads((HERE/'manifest.json').read_text())
    def test_current_sources_agree(self):
        self.assertEqual(check_local_map(HERE,self.manifest),0x10080000)
    def test_gpio_collision_rejected(self):
        regions=[{'name':'GPIO','base':0x10060000,'size':256,'enabled':True}]
        with self.assertRaisesRegex(ValueError,'GPIO'):validate_window(regions,0x10060000,32)
        with self.assertRaisesRegex(ValueError,'GPIO'):validate_window(regions,0x100600e0,32)
        validate_window(regions,0x10080000,4096)
    def test_free_registers_do_not_justify_a_shared_linux_page(self):
        regions=[{'name':'GPIO','base':0x10060000,'size':256,'enabled':True}]
        validate_window(regions,0x10060100,32)
        with self.assertRaisesRegex(ValueError,'GPIO'):validate_window(regions,0x10060000,4096)
    def test_firmware_drift_rejected(self):
        build=HERE.parents[0]/'build';build.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='mmio-map-',dir=build) as temporary:
            target=Path(temporary).resolve();self.assertTrue(target.is_relative_to(build.resolve()))
            for name in ['hsd-dotproduct.c','tb_wally_linux.sv','boot-smoke.S','wally-linux.dts']:shutil.copyfile(HERE/name,target/name)
            p=target/'boot-smoke.S';p.write_text(p.read_text().replace('li t2,0x10080000','li t2,0x10060000'))
            with self.assertRaisesRegex(ValueError,'boot-smoke'):check_local_map(target,self.manifest)
    def test_gpio_cannot_be_disabled(self):
        self.manifest['wally_profile']['gpio']=False
        with self.assertRaisesRegex(ValueError,'GPIO'):check_local_map(HERE,self.manifest)

if __name__=='__main__':unittest.main()
