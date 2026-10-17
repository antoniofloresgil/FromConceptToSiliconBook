#!/usr/bin/env python3
"""Qualify a copied IP release; no imports or reads from the surrounding book."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

IP = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('release_verify', IP/'manifest/verify.py')
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--platform', choices=['axi','wally'], required=True)
    parser.add_argument('--profile', choices=['compact','course'], default='course')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--wally-root', type=Path)
    parser.add_argument('--seed', type=int, default=2026)
    args = parser.parse_args()
    release = verifier.verify(IP)
    config = json.loads((IP/'manifest/configurations.json').read_text())
    profile = config['profiles'][args.profile]
    assert profile['MAX_LENGTH'] in (16,256)
    assert profile['DMA_BASE'] == 0x80008000 and profile['DMA_LIMIT'] == 0x8000c000
    if args.platform == 'wally' and args.profile != 'course':
        raise SystemExit('Wally fixture is qualified only for the course profile.')
    out = args.output.resolve()
    if out == IP or out.is_relative_to(IP): raise SystemExit('Build outside the immutable release tree.')
    if out.exists(): raise SystemExit('Choose a fresh output directory.')
    out.mkdir(parents=True)
    def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
    record = dict(status='running', platform=args.platform, profile=args.profile, seed=args.seed,
                  release_sha256=sha(IP/'manifest/release.json'),
                  rtl_sha256={name:sha(IP/name) for name in release['rtl']}, commands=[])
    def run(argv, timeout=300):
        argv = [str(v) for v in argv]
        entry = dict(argv=argv, log=f'command-{len(record["commands"])+1:02d}.txt')
        record['commands'].append(entry)
        start = time.monotonic()
        with (out/entry['log']).open('w') as log:
            result = subprocess.run(argv,cwd=out,stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
        entry.update(returncode=result.returncode, seconds=round(time.monotonic()-start,3))
        if result.returncode:
            raise RuntimeError((out/entry['log']).read_text(errors='replace')[-4000:])
    try:
        rtl = [IP/name for name in release['rtl']]
        sim = IP/'sim'
        if args.platform == 'axi':
            run([sys.executable,sim/'vectors.py',out,args.seed])
            run(['iverilog','-g2012','-I',sim,'-s','tb_dotproduct',
                 f'-DTEST_MAX_LENGTH={profile["MAX_LENGTH"]}','-o',out/'dut.vvp',
                 *rtl,sim/'axi_ram_model.sv',sim/'tb_dotproduct.sv'])
            run(['vvp',out/'dut.vvp',f'+SEED={args.seed}'])
            assert 'PASS' in (out/'command-03.txt').read_text()
            sources = ' '.join('"'+p.as_posix()+'"' for p in rtl)
            run(['yosys','-Q','-T','-p',f'read_verilog -sv {sources}; chparam -set MAX_LENGTH {profile["MAX_LENGTH"]} dotproduct_axi; synth -top dotproduct_axi; check -assert; select -assert-none t:$dlatch; write_json generic.json; stat'])
            run([sys.executable,IP/'formal/check.py',out,IP/'rtl'],timeout=600)
        else:
            if not args.wally_root: raise ValueError('--wally-root is required')
            vendor = out/'vendor'
            run([sys.executable,sim/'prepare_wally.py','export',args.wally_root.resolve(),vendor])
            record['wally_revision'] = json.loads((vendor/'source-identity.json').read_text())['revision']
            expected = json.loads((IP/'manifest/dependencies.json').read_text())['wally']['revision']
            assert record['wally_revision'] == expected
            # This is a PLATFORM adaptation of the exported core's PMA policy,
            # never a change to the three packaged accelerator RTL files.
            mmio = config['platforms']['wally']['mmio_base']
            pma = vendor/'src/mmu/pmachecker.sv'
            original = pma.read_text()
            patched = original
            rules = {
                "  assign Cacheable = (PBMemoryType == 2'b00) ? CacheableRegion : 1'b0;":
                f"  wire ReusableIPMMIO = PhysicalAddress >= 64'h{mmio:x} && PhysicalAddress < 64'h{mmio+32:x};\n  assign Cacheable = ((PBMemoryType == 2'b00) ? CacheableRegion : 1'b0) & ~ReusableIPMMIO;",
                "  assign Idempotent = (PBMemoryType == 2'b00) ? IdempotentRegion : (PBMemoryType == 2'b01);":
                "  assign Idempotent = ((PBMemoryType == 2'b00) ? IdempotentRegion : (PBMemoryType == 2'b01)) & ~ReusableIPMMIO;",
                '  assign AtomicAllowed = SelRegions[1] | SelRegions[3] | SelRegions[5];':
                '  assign AtomicAllowed = (SelRegions[1] | SelRegions[3] | SelRegions[5]) & ~ReusableIPMMIO;',
                '  assign PMAAccessFault          = SelRegions[0] & AccessRWXC | AtomicAccessM & ~AtomicAllowed;':
                '  assign PMAAccessFault = (SelRegions[0] & AccessRWXC) | (AtomicAccessM & ~AtomicAllowed) | (ReusableIPMMIO & ExecuteAccessF);'}
            for before, after in rules.items():
                assert patched.count(before) == 1, before
                patched = patched.replace(before,after)
            record['wally_pma'] = dict(original_sha256=sha(pma),policy='MMIO uncached, non-idempotent, non-atomic, execute-forbidden')
            pma.write_text(patched)
            record['wally_pma']['adapted_sha256'] = sha(pma)
            sw = IP/'sw'
            run(['clang','--target=riscv32','-march=rv32im_zicsr','-mabi=ilp32','-O2',
                 '-ffreestanding','-fno-builtin','-fno-stack-protector','-msmall-data-limit=0',
                 '-Wall','-Wextra','-Werror','-nostdlib','-fuse-ld=lld','-Wl,--no-relax',
                 '-Wl,-T,'+str(sw/'link.ld'),sw/'start.S',sw/'main.c','-o',out/'firmware.elf'])
            run([sys.executable,sim/'prepare_wally.py','hex',out/'firmware.elf',out/'firmware.hex'])
            package = vendor/'src/cvw.sv'
            sources = [package,*[p for p in sorted((vendor/'src').rglob('*.sv')) if p != package]]
            run(['verilator','--binary','--timing','-j','2','-Wno-fatal','--top-module','tb_wally_dotproduct',
                 '--Mdir',out/'obj_dir','-I'+str(vendor/'config/rv32imc'),'-I'+str(vendor/'config/shared'),
                 '-I'+str(sim),*sources,*rtl,sim/'ahb_to_axil.sv',sim/'axi_ram_model.sv',sim/'tb_wally_dotproduct.sv'],timeout=600)
            run([out/'obj_dir/Vtb_wally_dotproduct',f'+SEED={args.seed}'])
            assert 'PASS real Wally:' in (out/'command-05.txt').read_text()
        verifier.verify(IP)
        record['status'] = 'pass'
    finally:
        if record['status'] != 'pass': record['status'] = 'fail'
        record['artifacts'] = {p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name != 'report.json'}
        (out/'report.json').write_text(json.dumps(record,indent=2)+'\n')
    print('PASS packaged IP',args.platform,args.profile,'unchanged RTL; report:',out/'report.json')


if __name__ == '__main__': main()
