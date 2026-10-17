#!/usr/bin/env python3
"""Reproduce actual dual-clock simulations, synthesis and rejected FIFO defects."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from check_structure import check

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'labs/build/async-fifo')
    args=parser.parse_args()
    out=args.output.resolve()
    if out.exists():raise SystemExit('Use a fresh output directory.')
    out.mkdir(parents=True)
    sources=[p for p in sorted(HERE.rglob('*')) if p.is_file() and 'reference' not in p.parts
             and '__pycache__' not in p.parts and p.suffix not in {'.md'}]
    report=dict(status='running',image_id=os.environ.get('LAB_IMAGE_ID','not-recorded'),
                scope='Digital dual-clock RTL, shared reset epochs and generic netlist structure; no analog metastability/MTBF or physical signoff',
                sources={p.relative_to(ROOT).as_posix():sha(p) for p in sources},commands=[],simulations=[],negative=[])
    def execute(name,argv,expect=None):
        argv=[str(x) for x in argv]
        log=out/(name+'.txt')
        with log.open('w') as stream:
            result=subprocess.run(argv,cwd=out,stdout=stream,stderr=subprocess.STDOUT,timeout=120)
        text=log.read_text(errors='replace')
        report['commands'].append(dict(name=name,argv=argv,exit_code=result.returncode,log=log.name))
        if expect:
            if result.returncode==0 or expect not in text:raise RuntimeError(f'{name}: defect not detected: '+text[-2000:])
        elif result.returncode:
            raise RuntimeError(f'{name}: '+text[-3000:])
        return text
    try:
        report['tools']={tool:execute('version-'+tool,[tool,flag]).splitlines()[0]
                         for tool,flag in [('iverilog','-V'),('yosys','-V')]}
        clocks=[(5,7,2),(3,11,1),(13,2,0),(5,5,0)]
        for width in (8,32):
            for bits in (1,2,4):
                tag=f'w{width}-d{1<<bits}'
                exe=out/(tag+'.vvp')
                execute(tag+'-compile',['iverilog','-g2012','-s','tb_async_fifo',
                        f'-Ptb_async_fifo.DATA_W={width}',f'-Ptb_async_fifo.ADDR_BITS={bits}',
                        '-o',exe,HERE/'async_fifo.sv',HERE/'tb_async_fifo.sv'])
                for wh,rh,phase in clocks:
                    for seed in (2026,2027):
                        name=f'{tag}-c{wh}-{rh}-{phase}-s{seed}'
                        text=execute(name,['vvp',exe,f'+WH={wh}',f'+RH={rh}',f'+PHASE={phase}',f'+SEED={seed}'])
                        assert 'PASS asynchronous FIFO' in text
                        metrics=dict((k,int(v)) for k,v in re.findall(r'(\w+)=(\d+)',next(line for line in text.splitlines() if line.startswith('METRIC '))))
                        assert metrics['writes']==metrics['reads']+metrics['dropped']
                        assert metrics['epochs']==3 and metrics['wstall']>0 and metrics['rstall']>0
                        report['simulations'].append(dict(name=name,width=width,depth=1<<bits,write_half_ns=wh,
                                                          read_half_ns=rh,read_phase_ns=phase,seed=seed,metrics=metrics))
                script=(f'read_verilog -sv "{HERE / "async_fifo.sv"}"; '
                        f'chparam -set DATA_W {width} -set ADDR_BITS {bits} async_fifo; '
                        f'synth -top async_fifo; check -assert; select -assert-none t:$dlatch; write_json {tag}.json')
                execute(tag+'-synthesis',['yosys','-Q','-T','-p',script])
                structure=check(out/(tag+'.json'))
                (out/(tag+'-structure.json')).write_text(json.dumps(structure,indent=2)+'\n')
                print('PASS',tag,'8 schedules/seeds and synthesized pointer chains',flush=True)
        original=(HERE/'async_fifo.sv').read_text()
        mutants=[('wrong-full-mask',"{2'b11, {(ADDR_BITS-1){1'b0}}}","{2'b10, {(ADDR_BITS-1){1'b0}}}",'OVERFLOW'),
                 ('read-empty','rrst_n && !r_empty','rrst_n','UNDERFLOW'),
                 ('binary-pointer','(w_bin_next >> 1) ^ w_bin_next','w_bin_next','GRAY_SOURCE'),
                 ('unsynchronized-release','wire wrst_n = w_release[1];','wire wrst_n = arst_n;','RELEASE_WITH_STOPPED_CLOCK')]
        for name,before,after,marker in mutants:
            assert original.count(before)==1
            path=out/(name+'.sv');path.write_bytes(original.replace(before,after).encode())
            exe=out/(name+'.vvp')
            execute(name+'-compile',['iverilog','-g2012','-s','tb_async_fifo','-o',exe,path,HERE/'tb_async_fifo.sv'])
            execute(name,['vvp',exe],expect=marker)
            report['negative'].append(dict(name=name,detected_by=marker,status='rejected'))
        assert sum(r['metrics']['rjump']+r['metrics']['wjump'] for r in report['simulations'])>0
        report['status']='pass'
    finally:
        if report['status']!='pass':report['status']='fail'
        report['artifacts']={p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name!='report.json'}
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS asynchronous FIFO: 48 digital runs, six netlists, four rejected defects')


if __name__=='__main__':main()
