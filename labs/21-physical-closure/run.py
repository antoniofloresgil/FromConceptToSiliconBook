#!/usr/bin/env python3
"""Explicit continuation of the immutable Lab 17 physical baseline."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT/'labs/17-complete-case'
LIB = Path('/OpenROAD-flow-scripts/flow/platforms/nangate45')

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('target', choices=['test','ecp5','nexys','asic'])
    p.add_argument('--candidate', choices=['baseline','slow','pipeline','repair'], required=True)
    p.add_argument('--output-dir', required=True)
    a = p.parse_args()
    if a.candidate == 'repair' and a.target != 'asic': p.error('repair is ASIC only')
    m = json.loads((BASE/'manifest.json').read_text())
    for name, digest in m['rtl_sha256'].items():
        if sha(ROOT/name) != digest: raise ValueError('Changed baseline '+name)
    out = (ROOT/a.output_dir).resolve()
    if not out.is_relative_to((ROOT/'labs/build').resolve()) or (out.exists() and any(out.iterdir())):
        raise ValueError('Use a fresh directory under labs/build')
    out.mkdir(parents=True, exist_ok=True)
    files = [ROOT/n for n in m['component_rtl']]
    if a.candidate == 'pipeline': files = [HERE/'dotproduct_engine.sv' if f.name == 'dotproduct_engine.sv' else f for f in files]
    inputs = files + [HERE/'manifest.json', BASE/'manifest.json', BASE/'asic.sdc', BASE/'asic.tcl', BASE/'streamout.py',
                      BASE/'nexys_video.sv', BASE/'nexys-video.xdc', BASE/'tb_nexys.sv',
                      ROOT/'labs/10-dotproduct/tb_dotproduct.sv', ROOT/'labs/10-dotproduct/axi_connections.svh',
                      ROOT/'labs/10-dotproduct/axi_ram_model.sv', ROOT/'labs/10-dotproduct/vectors.py',
                      HERE/'run.py', HERE/'repair.tcl', HERE/'dotproduct_engine.sv']
    r = dict(status='running', target=a.target, candidate=a.candidate, seed=2026,
             requested_mhz=75 if a.candidate=='slow' else 100,
             common_manifest_sha256=sha(BASE/'manifest.json'),
             sources={str(f.relative_to(ROOT)):sha(f) for f in inputs},
             image=os.environ.get('CASE_IMAGE_ID','unrecorded'), commands=[], tools={})
    def save(): (out/'report.json').write_text(json.dumps(r,indent=2)+'\n')
    def run(argv, timeout=2400):
        log = out/f'command-{len(r["commands"])+1:02d}.log'
        item = dict(argv=list(map(str,argv)), log=log.name)
        r['commands'].append(item); save()
        with log.open('w') as f:
            v = subprocess.run(item['argv'],cwd=out,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
        item['exit_code']=v.returncode; save()
        if v.returncode or '[ERROR ' in log.read_text(): raise RuntimeError('Inspect '+str(log))
    read = 'read_verilog -sv '+' '.join(str(f) for f in files)+'; '
    read += 'hierarchy -top dotproduct_axi; '
    read += "chparam -set MAX_LENGTH 256 -set DMA_BASE 32'h80008000 -set DMA_LIMIT 33'h08000c000 dotproduct_axi; "
    try:
        if a.target=='test':
            src = ROOT/'labs/10-dotproduct'
            run(['iverilog','-g2012','-I',src,'-s','tb_dotproduct','-o','simulation',*files,src/'axi_ram_model.sv',src/'tb_dotproduct.sv'])
            for seed in [2026,2027]:
                run([sys.executable,src/'vectors.py',out,str(seed)])
                run(['vvp','simulation'])
            run(['iverilog','-g2012','-s','tb_nexys','-o','fixture',*files,BASE/'nexys_video.sv',BASE/'tb_nexys.sv'])
            run(['vvp','fixture'])
        else:
            r['tools']['yosys']=subprocess.check_output(['yosys','-V'],text=True).strip()
            if a.target=='asic':
                lib=LIB/'lib/NangateOpenCellLibrary_typical.lib'
                r['tools']['openroad']=subprocess.check_output(['openroad','-version'],text=True).strip()
                r['technology_sha256']={str(f.relative_to(LIB)):sha(f) for f in [lib,LIB/'rcx_patterns.rules',LIB/'lef/NangateOpenCellLibrary.tech.lef',LIB/'lef/NangateOpenCellLibrary.macro.mod.lef']}
                run(['yosys','-Q','-T','-p',read+'synth -top dotproduct_axi -flatten; '+f'dfflibmap -liberty {lib}; abc -liberty {lib}; hilomap -hicell LOGIC1_X1 Z -locell LOGIC0_X1 Z; read_liberty -lib {lib}; clean; check -assert; write_verilog -noattr -noexpr mapped.v'])
                os.environ.update(CASE_OUT=str(out),CASE_PERIOD=str(1000/r['requested_mhz']),CASE_UTIL='45',CASE_SDC=str(BASE/'asic.sdc'))
                run(['openroad','-no_init','-exit','-threads','2',HERE/'repair.tcl' if a.candidate=='repair' else BASE/'asic.tcl'])
                run(['klayout','-zz','-rd',f'out={out}','-rm',BASE/'streamout.py'])
            elif a.target=='ecp5':
                r['tools']['nextpnr']=subprocess.check_output(['nextpnr-ecp5','--version'],text=True,stderr=subprocess.STDOUT).strip()
                run(['yosys','-Q','-T','-p',read+'synth_ecp5 -top dotproduct_axi -json mapped.json'])
                run(['nextpnr-ecp5','--25k','--package','CABGA381','--speed','6','--out-of-context','--json','mapped.json','--write','routed.json','--report','timing.json','--freq',r['requested_mhz'],'--timing-allow-fail','--seed',2026])
            else:
                r['tools']['nextpnr']=subprocess.check_output(['nextpnr-xilinx','--version'],text=True,stderr=subprocess.STDOUT).strip()
                r['chipdb_sha256']=sha(Path('/opt/xc7a200t.bin'))
                run(['yosys','-Q','-T','-p','read_verilog -sv '+' '.join(str(f) for f in files)+f' {BASE}/nexys_video.sv; synth_xilinx -top nexys_video_case -arch xc7 -abc9 -nodsp; flatten; delete t:$scopeinfo; write_json mapped.json'])
                run(['nextpnr-xilinx','--chipdb','/opt/xc7a200t.bin','--xdc',BASE/'nexys-video.xdc','--json','mapped.json','--top','nexys_video_case','--freq',r['requested_mhz'],'--seed',2026,'--timing-allow-fail','--write','routed.json','--report','timing.json','--fasm','nexys.fasm'])
        for name,digest in r['sources'].items():
            if sha(ROOT/name)!=digest: raise RuntimeError('Input changed during run: '+name)
        r['status']='completed'
    except Exception as e:
        r.update(status='failed',error=str(e)); raise
    finally:
        r['artifacts']={f.name:sha(f) for f in out.iterdir() if f.is_file() and f.name!='report.json'}
        save()
    print('COMPLETED',a.target,a.candidate,'; inspect acceptance separately')

if __name__=='__main__': main()
