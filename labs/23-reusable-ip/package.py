#!/usr/bin/env python3
"""Create an autonomous teaching IP release without changing locked Lab 10 RTL."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode('utf-8'))


def generate(schema):
    expected = ['CTRL','STATUS','SRC_A','SRC_B','DST','LENGTH','ERROR_CODE','IRQ_ACK']
    regs = schema['registers']
    assert schema['schema'] == 1 and schema['data_width'] == 32
    assert [r['name'] for r in regs] == expected
    assert len({r['offset'] for r in regs}) == 8
    assert all(type(r['offset']) is int and 0 <= r['offset'] <= 28 and r['offset'] % 4 == 0 for r in regs)
    # This intentionally small backend fixes behavioral semantics. It generates
    # addresses/views, not arbitrary access policies or arbitrary field layouts.
    fields = {'CTRL':[('START',0,1),('IRQ_ENABLE',1,1)],
              'STATUS':[('BUSY',0,1),('DONE',1,1),('ERROR',2,1),('IRQ_PENDING',3,1)],
              'IRQ_ACK':[('ACK',0,1)]}
    access = ['command/rw','ro','rw','rw','rw','rw','ro','w1c']
    for r, policy in zip(regs, access):
        assert r['reset'] == 0 and r['access'] == policy
        assert [(f['name'],f['lsb'],f['width']) for f in r['fields']] == fields.get(r['name'], [])
    rtl = (HERE/'templates/dotproduct_axi.sv.in').read_text(encoding='utf-8')
    header = ['/* Generated from manifest/registers.json; do not edit. */',
              '#ifndef DOTPRODUCT_REGS_H', '#define DOTPRODUCT_REGS_H', '#include <stdint.h>']
    sv = ['// Generated register addresses for integration checkers.', 'package dotproduct_regs_pkg;']
    assembly = ['/* Generated offsets for preprocessed assembly. */']
    docs = ['# Generated register map', '', '| Offset | Register | Access | Reset | Behavior |',
            '| --- | --- | --- | --- | --- |']
    for r in regs:
        name, offset = r['name'], r['offset']
        rtl = rtl.replace('@'+name+'_OFFSET@', f"5'h{offset:02x}")
        header.append(f'#define DP_{name} UINT32_C(0x{offset:02x})')
        assembly.append(f'#define DP_{name} 0x{offset:02x}')
        sv.append(f"  localparam logic [4:0] DP_{name} = 5'h{offset:02x};")
        for f in r['fields']:
            mask = ((1 << f['width'])-1) << f['lsb']
            header.append(f'#define DP_{name}_{f["name"]}_MASK UINT32_C(0x{mask:08x})')
        docs.append(f'| 0x{offset:02x} | {name} | {r["access"]} | 0 | {r["behavior"]} |')
    assert not re.search(r'@[A-Z_]+@', rtl)
    return {'rtl/dotproduct_axi.sv':rtl, 'sw/dotproduct_regs.h':'\n'.join(header+['#endif','']),
            'sw/dotproduct_regs_asm.h':'\n'.join(assembly)+'\n',
            'sim/dotproduct_regs_pkg.sv':'\n'.join(sv+['endpackage','']),
            'docs/registers.md':'\n'.join(docs)+'\n'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if out.exists(): raise SystemExit('Choose a new output directory; releases are not overwritten.')
    schema = json.loads((HERE/'registers.json').read_text())
    generated = generate(schema)
    origin = json.loads((HERE/'origin-lock.json').read_text())
    for name, digest in origin.items():
        if sha(ROOT/name) != digest: raise SystemExit('Changed locked input: '+name)
    out.mkdir(parents=True)
    for folder in ['rtl','sim','formal','sw','constraints','docs','synthesis','manifest']:
        (out/folder).mkdir()
    for name, text in generated.items(): write(out/name, text)
    base = ROOT/'labs/10-dotproduct'
    copies = {
        'rtl/dotproduct_mac.sv':'rtl/dotproduct_mac.sv',
        'rtl/dotproduct_engine.sv':'rtl/dotproduct_engine.sv',
        'rtl/ahb_to_axil.sv':'sim/ahb_to_axil.sv',
        'axi_connections.svh':'sim/axi_connections.svh', 'axi_ram_model.sv':'sim/axi_ram_model.sv',
        'tb_dotproduct.sv':'sim/tb_dotproduct.sv', 'vectors.py':'sim/vectors.py',
        'prepare_wally.py':'sim/prepare_wally.py', 'formal/check.py':'formal/check.py',
        'firmware/link.ld':'sw/link.ld',
        'constraints.sdc':'constraints/example.sdc'}
    for src, dst in copies.items(): shutil.copyfile(base/src, out/dst)
    # These are PLATFORM files; the IP has no knowledge of either MMIO base.
    config = json.loads((HERE/'configurations.json').read_text())
    mmio = config['platforms']['wally']['mmio_base']
    assert mmio == 0x10080000
    fixture = (base/'tb_wally_dotproduct.sv').read_text().replace("34'h010060000", f"34'h{mmio:09x}").replace("34'h010060020", f"34'h{mmio+32:09x}")
    fixture = fixture.replace('c.COUNTERS=3;', f"c.COUNTERS=3; c.EXT_MEM_SUPPORTED=1; c.EXT_MEM_BASE=64'h{mmio:x}; c.EXT_MEM_RANGE=64'h1f;")
    write(out/'sim/tb_wally_dotproduct.sv', fixture)
    firmware = (base/'firmware/main.c').read_text().replace('#include <stdint.h>', '#include <stdint.h>\n#include "dotproduct_regs.h"').replace('0x10060000u', f'0x{mmio:x}u')
    startup = '#include "dotproduct_regs_asm.h"\n'+(base/'firmware/start.S').read_text().replace('li t0, 0x1006001c', f'li t0, 0x{mmio:x} + DP_IRQ_ACK')
    write(out/'sw/start.S', startup)
    for r in schema['registers']:
        # The legacy firmware is a fixed ABI oracle; replace its offsets with
        # generated names, not values read back from the implementation.
        original = ['CTRL','STATUS','SRC_A','SRC_B','DST','LENGTH','ERROR_CODE','IRQ_ACK'].index(r['name'])*4
        firmware = firmware.replace(f'REG({original})', f'REG(DP_{r["name"]})')
    write(out/'sw/main.c', firmware)
    for name in ['run_release.py','verify.py']:
        shutil.copyfile(HERE/name, out/('sim/run.py' if name=='run_release.py' else 'manifest/verify.py'))
    for name in ['registers.json','configurations.json','dependencies.json','origin-lock.json']:
        shutil.copyfile(HERE/name, out/'manifest'/name)
    shutil.copyfile(HERE/'docs/contract.md', out/'docs/contract.md')
    shutil.copyfile(ROOT/'LICENSES/MIT.txt', out/'LICENSE')
    write(out/'synthesis/README.md', 'Generic Yosys netlist is produced by sim/run.py --platform axi.\nNo technology-mapped, LEF, GDS, scan or timing-qualified view is bundled.\n')
    sources = [HERE/'package.py', HERE/'run_release.py', HERE/'verify.py', HERE/'templates/dotproduct_axi.sv.in',
               HERE/'registers.json',HERE/'configurations.json',HERE/'dependencies.json',HERE/'origin-lock.json']
    manifest = dict(schema=1, name='dotproduct_ip', version=schema['ip_version'], register_abi=schema['register_abi'],
                    top='dotproduct_axi', rtl=[f'rtl/{name}.sv' for name in ['dotproduct_mac','dotproduct_engine','dotproduct_axi']],
                    rtl_policy='One generated release, unchanged between integration platforms.',
                    generation={p.relative_to(ROOT).as_posix():sha(p) for p in sources},
                    files={p.relative_to(out).as_posix():sha(p) for p in sorted(out.rglob('*')) if p.is_file()})
    # Path ordering differs between Windows and POSIX. Canonicalize JSON keys
    # so the release identity is independent of the generator's host OS.
    write(out/'manifest/release.json', json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print('PACKAGED', out, len(manifest['files']), 'files')


if __name__ == '__main__': main()
