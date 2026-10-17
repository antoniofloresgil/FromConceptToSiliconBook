#!/usr/bin/env python3
"""Implement the locked accelerator plus serial boundary fixture on Nexys Video."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
from run import ROOT, SOURCE, load_manifest, sha


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',default='labs/build/complete-case-nexys')
    args=parser.parse_args()
    manifest=load_manifest()
    profile=json.loads((SOURCE/'nexys-profile.json').read_text())
    if profile['common_manifest_sha256']!=sha(SOURCE/'manifest.json'):
        raise ValueError('Different common RTL release')
    for name,digest in profile['inputs'].items():
        if sha(SOURCE/name)!=digest: raise ValueError('Changed Nexys fixture: '+name)
    out=(ROOT/args.output_dir).resolve()
    if not out.is_relative_to((ROOT/'labs/build').resolve()): raise ValueError('Output must stay in labs/build')
    if out.exists() and any(out.iterdir()): raise ValueError('Preserve results: choose a fresh directory')
    out.mkdir(parents=True,exist_ok=True)
    record={'status':'running','profile':profile,'profile_sha256':sha(SOURCE/'nexys-profile.json'),
            'manifest_sha256':sha(SOURCE/'manifest.json'),'rtl_sha256':manifest['rtl_sha256'],
            'parameters':manifest['parameters'],'image':os.environ.get('CASE_IMAGE_ID','unrecorded'),
            'recipe_sha256':sha(Path(__file__)),'commands':[],'tools':{}}
    def save(): (out/'report.json').write_text(json.dumps(record,indent=2)+'\n')
    def command(argv,timeout=1800):
        log=out/f'command-{len(record["commands"])+1:02d}.log'
        item={'argv':argv,'log':log.name};record['commands'].append(item);save()
        with log.open('w') as stream:
            result=subprocess.run(argv,cwd=out,stdout=stream,stderr=subprocess.STDOUT,timeout=timeout)
        item['exit_code']=result.returncode;save()
        if result.returncode: raise RuntimeError('Failed command: '+str(log))
    save()
    try:
        record['tools']['yosys']=subprocess.check_output(['yosys','-V'],text=True).strip()
        record['tools']['nextpnr']=subprocess.check_output(['nextpnr-xilinx','--version'],text=True,stderr=subprocess.STDOUT).strip()
        record['nextpnr_revision']=subprocess.check_output(['git','-c','safe.directory=/opt/nextpnr-xilinx','-C','/opt/nextpnr-xilinx','rev-parse','HEAD'],text=True).strip()
        if record['nextpnr_revision']!=profile['nextpnr_revision']:
            raise RuntimeError('Wrong nextpnr-Xilinx revision')
        database='/opt/nextpnr-xilinx/xilinx/external/prjxray-db'
        record['database_revision']=subprocess.check_output(['git','-c','safe.directory='+database,'-C',database,'rev-parse','HEAD'],text=True).strip()
        record['chipdb_sha256']=sha(Path('/opt/xc7a200t.bin'))
        files=' '.join('"'+(ROOT/p).as_posix()+'"' for p in manifest['component_rtl'])
        command(['iverilog','-g2012','-s','tb_nexys','-o','fixture-test',
                 *[str(ROOT/p) for p in manifest['component_rtl']],
                 str(SOURCE/'nexys_video.sv'),str(SOURCE/'tb_nexys.sv')])
        command(['vvp','fixture-test'])
        script=f'read_verilog -sv {files} "{(SOURCE/"nexys_video.sv").as_posix()}"; '
        script+='synth_xilinx -top nexys_video_case -arch xc7 -abc9 -nodsp; '
        script+='flatten; delete t:$scopeinfo; write_json mapped.json'
        command(['yosys','-Q','-T','-p',script])
        design=json.loads((out/'mapped.json').read_text())['modules']['nexys_video_case']
        counts={scope:dict(Counter(cell['type'] for name,cell in design['cells'].items()
                                  if (scope=='accelerator')==name.startswith(('dut.','$flatten\\dut.'))))
                for scope in ['accelerator','fixture']}
        (out/'synthesis-resources.json').write_text(json.dumps(counts,indent=2)+'\n')
        command(['nextpnr-xilinx','--chipdb','/opt/xc7a200t.bin','--xdc',str(SOURCE/'nexys-video.xdc'),
                 '--json','mapped.json','--top','nexys_video_case','--freq',str(profile['requested_mhz']),
                 '--seed',str(manifest['seed']),'--timing-allow-fail','--write','routed.json',
                 '--report','timing.json','--fasm','nexys.fasm'])
        gridpath=Path('/opt/nextpnr-xilinx/xilinx/external/prjxray-db/artix7/xc7a200t/tilegrid.json')
        grid=json.loads(gridpath.read_text())
        allsites={site:[tile['grid_x'],tile['grid_y']] for tile in grid.values() for site in tile['sites']}
        routed=json.loads((out/'routed.json').read_text())['modules']['top']
        sites={cell.get('attributes',{}).get('NEXTPNR_BEL','').split('/')[0] for cell in routed['cells'].values()}
        coordinates={'tilegrid_sha256':sha(gridpath),'sites':{s:allsites[s] for s in sorted(sites) if s in allsites}}
        (out/'site-coordinates.json').write_text(json.dumps(coordinates,indent=2)+'\n')
        load_manifest()
        if record['profile_sha256']!=sha(SOURCE/'nexys-profile.json'):
            raise RuntimeError('Target profile changed during implementation')
        record['status']='completed'
    except (OSError,RuntimeError,subprocess.TimeoutExpired) as error:
        record.update(status='failed',error=str(error));raise
    finally:
        record['artifacts']={p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name!='report.json'}
        save()
    print('COMPLETED Nexys Video implementation; review timing before accepting the target')


if __name__=='__main__':main()
