#!/usr/bin/env python3
"""Physical stages of one locked dot-product RTL/configuration release."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).resolve().parent
PLATFORM = Path('/OpenROAD-flow-scripts/flow/platforms/nangate45')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest():
    path = SOURCE/'manifest.json'
    manifest = json.loads(path.read_text())
    for name, expected in {**manifest['rtl_sha256'],**manifest['firmware_sha256']}.items():
        if sha(ROOT/name) != expected:
            raise RuntimeError('Locked RTL changed: '+name)
    if manifest['parameters'] != {'MAX_LENGTH':256,'DMA_BASE':2147516416,'DMA_LIMIT':2147532800}:
        raise RuntimeError('The reference checks require the documented baseline parameters')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['check', 'fpga', 'asic'])
    parser.add_argument('--output-dir', default='labs/build/complete-case')
    args = parser.parse_args()
    manifest = load_manifest()
    if args.stage == 'check':
        print('PASS common manifest:', sha(SOURCE/'manifest.json'))
        return
    base = (ROOT/args.output_dir).resolve()
    if not base.is_relative_to(ROOT/'labs/build'):
        raise ValueError('Output must stay inside labs/build')
    out = base/args.stage
    if out.exists() and any(out.iterdir()):
        raise ValueError('Select a fresh --output-dir; preserve existing evidence')
    out.mkdir(parents=True, exist_ok=True)
    record = {'stage':args.stage,'status':'running','manifest_sha256':sha(SOURCE/'manifest.json'),
              'rtl_sha256':manifest['rtl_sha256'],'parameters':manifest['parameters'],
              'profile':manifest['profiles'][args.stage], 'commands':[],
              'image':os.environ.get('CASE_IMAGE_ID','unrecorded'), 'tools':{},
              'recipe_sha256':{p.name:sha(p) for p in SOURCE.iterdir()
                                if p.suffix in {'.py','.tcl','.sdc'}}}
    env = dict(os.environ)

    def save():
        (out/'report.json').write_text(json.dumps(record,indent=2)+'\n')

    def command(command, timeout=1200):
        log = out/f'command-{len(record["commands"])+1:02d}.log'
        item={'argv':command,'log':log.name}
        record['commands'].append(item);save()
        with log.open('w') as stream:
            result=subprocess.run(command,cwd=out,env=env,stdout=stream,
                                  stderr=subprocess.STDOUT,timeout=timeout)
        item['exit_code']=result.returncode;save()
        if result.returncode or '[ERROR ' in log.read_text():
            raise RuntimeError(f'Stage command failed; inspect {log}')
        return log.read_text()

    files=' '.join('"'+(ROOT/p).as_posix()+'"' for p in manifest['component_rtl'])
    params=manifest['parameters']
    values={key:(str(value) if key=='MAX_LENGTH' else
                 str(33 if key=='DMA_LIMIT' else 32)+"'h"+format(value,'x'))
            for key,value in params.items()}
    read=(f'read_verilog -sv {files}; hierarchy -top dotproduct_axi; '
          + ''.join(f'chparam -set {key} {value} dotproduct_axi; ' for key,value in values.items()))
    save()
    try:
        record['tools']['yosys']=subprocess.check_output(['yosys','-V'],text=True).strip()
        if args.stage == 'fpga':
            record['tools']['nextpnr']=subprocess.check_output(['nextpnr-ecp5','--version'],text=True,stderr=subprocess.STDOUT).strip()
            command(['yosys','-Q','-T','-p',read+'synth_ecp5 -top dotproduct_axi -json mapped.json'])
            command(['nextpnr-ecp5','--25k','--package','CABGA381','--speed','6',
                     '--out-of-context','--json','mapped.json','--write','routed.json',
                     '--report','timing.json','--freq',str(1000/manifest['clock_period_ns']),
                     '--timing-allow-fail','--placed-svg','placed.svg','--seed','2026'])
        else:
            record['tools']['openroad']=subprocess.check_output(['openroad','-version'],text=True).strip()
            lib=PLATFORM/'lib/NangateOpenCellLibrary_typical.lib'
            command(['yosys','-Q','-T','-p',read+'synth -top dotproduct_axi -flatten; '
                     f'dfflibmap -liberty {lib}; abc -liberty {lib}; '
                     f'hilomap -hicell LOGIC1_X1 Z -locell LOGIC0_X1 Z; read_liberty -lib {lib}; clean; '
                     'check -assert; write_verilog -noattr -noexpr mapped.v'])
            env.update(CASE_OUT=str(out),CASE_PERIOD=str(manifest['clock_period_ns']),
                       CASE_UTIL=str(manifest['profiles']['asic']['target_util_pct']),
                       CASE_SDC=str(SOURCE/'asic.sdc'))
            record['technology_sha256']={str(p.relative_to(PLATFORM)):sha(p) for p in [
                lib,PLATFORM/'lef/NangateOpenCellLibrary.tech.lef',
                PLATFORM/'lef/NangateOpenCellLibrary.macro.mod.lef',
                PLATFORM/'rcx_patterns.rules',PLATFORM/'gds/NangateOpenCellLibrary.gds']}
            command(['openroad','-no_init','-exit','-threads','2',str(SOURCE/'asic.tcl')])
            command(['klayout','-zz','-rd',f'out={out}','-rm',str(SOURCE/'streamout.py')])
            if not (out/'dotproduct_axi.gds').is_file():
                raise RuntimeError('Missing GDS stream-out')
        record['status']='completed'
    except (OSError,RuntimeError,subprocess.TimeoutExpired) as error:
        record.update(status='failed',error=str(error))
        raise
    finally:
        record['artifacts']={p.name:sha(p) for p in sorted(out.iterdir())
                             if p.is_file() and p.name!='report.json'}
        save()
    print('COMPLETED',args.stage,': tool completion is not physical qualification')


if __name__=='__main__':
    main()
