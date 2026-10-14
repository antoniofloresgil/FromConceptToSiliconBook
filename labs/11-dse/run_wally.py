"""Real Wally divider sweep; no FPGA frequency/resource claims are generated."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import sys

PROJECT=Path(__file__).resolve().parent
sys.path.insert(0,str(PROJECT.parent))
import run as runner
from vectors import generate

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wally-root',type=Path,default=os.environ.get('WALLY_ROOT'))
    parser.add_argument('--seed',type=int,default=2026)
    parser.add_argument('--bits',type=int,nargs='+',choices=[1,2,4],default=[1,2,4])
    args=parser.parse_args()
    if not args.wally_root:parser.error('Supply --wally-root or WALLY_ROOT with the pinned revision available')
    destination=runner.BUILD/'dse';destination.mkdir(parents=True,exist_ok=True)
    session=runner.Session('dse-setup',args.seed)
    vendor=destination/'vendor'
    helper=runner.ROOT/'labs/10-dotproduct/prepare_wally.py'
    session.execute([sys.executable,helper,'export',args.wally_root,vendor])
    vectors=generate(destination,args.seed)
    elf=destination/'firmware.elf'
    session.execute(['clang','--target=riscv32','-march=rv32im_zicsr','-mabi=ilp32','-O2',
                     '-ffreestanding','-fno-builtin','-fno-stack-protector','-msmall-data-limit=0',
                     '-Wall','-Wextra','-Werror','-nostdlib','-fuse-ld=lld','-Wl,--no-relax',
                     '-Wl,-T,'+str(runner.ROOT/'labs/10-dotproduct/firmware/link.ld'),
                     '-I'+str(destination),PROJECT/'start.S',PROJECT/'firmware.c','-o',elf])
    session.execute([sys.executable,helper,'hex',elf,destination/'firmware.hex'])
    package=vendor/'src/cvw.sv'
    sources=[package,*[p for p in sorted((vendor/'src').rglob('*.sv')) if p!=package]]
    report={'origin':'measured-rtl','seed':args.seed,'environment':runner.tool_info(),
            'wally_revision':'3b30ba6b6519bd2c26c1437e6d61f632a35cef6c',
            'binary_sha256':sha(elf),'vectors_sha256':sha(destination/'vectors.json'),
            'comparison_status':'incomplete',
            'dependency_sources':{p.relative_to(runner.ROOT).as_posix():sha(p) for p in
                                  [helper,runner.ROOT/'labs/run.py',runner.ROOT/'labs/tools/catalog.py',
                                   runner.ROOT/'labs/10-dotproduct/firmware/link.ld']},
            'sources':{p.relative_to(runner.ROOT).as_posix():sha(p) for p in PROJECT.glob('*') if p.is_file()},
            'scope':'One RV32 divider-heavy ROI; uncached zero-wait AHB RAM; no timing/resource evidence',
            'setup_commands':session.commands,'runs':[]}
    try:
        for bits in dict.fromkeys(args.bits):
            job=runner.Session('dse-div'+str(bits),args.seed)
            row={'divider_bits':bits,'status':'fail','commands':job.commands}
            report['runs'].append(row)
            image=job.directory/'firmware.hex';image.write_bytes((destination/'firmware.hex').read_bytes())
            objects=job.directory/'obj_dir'
            job.execute(['verilator','--binary','--timing','-j','2','-Wno-fatal',
                         '--top-module','tb_wally_dse','--Mdir',objects,'-DDSE_DIV_BITS='+str(bits),
                         '-I'+str(vendor/'config/rv32imc'),'-I'+str(vendor/'config/shared'),
                         *sources,PROJECT/'tb_wally_dse.sv'],timeout=600)
            job.execute([objects/'Vtb_wally_dse'],timeout=120)
            log=(runner.ROOT/job.commands[-1]['log']).read_text()
            matches=re.findall(r'DSE_RESULT divider_bits=(\d+) cycles=(\d+) instret=(\d+) checksum=(\d+) pairs=(\d+)',log)
            if len(matches)!=1:raise RuntimeError('Missing/ambiguous measured result')
            actual,cycles,instructions,checksum,count=map(int,matches[0])
            if actual!=bits or count!=64 or checksum!=vectors['checksum'] or not cycles or not instructions:
                raise RuntimeError('Configuration, oracle or measurement mismatch')
            row.update(status='pass',cycles=cycles,instret=instructions,checksum=checksum,
                       instrumented_cpi=cycles/instructions,pairs=count)
            print(f'PASS real Wally divider={bits}: cycles={cycles} instret={instructions}',flush=True)
        if len({r['instret'] for r in report['runs']})!=1:
            raise RuntimeError('Retired instruction counts differ: review ROI boundary/configuration before comparison')
        report['comparison_status']='pass'
    except (RuntimeError,OSError) as error:
        report.update(comparison_status='fail',error=str(error))
        raise
    finally:
        (destination/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    baseline=next((r for r in report['runs'] if r['divider_bits']==2),report['runs'][0])
    with (destination/'results.csv').open('w',newline='') as output:
        columns=['divider_bits','cycles','instret','instrumented_cpi','cycle_speedup','status']
        writer=csv.DictWriter(output,fieldnames=columns);writer.writeheader()
        for row in report['runs']:
            writer.writerow({**{k:row[k] for k in columns if k!='cycle_speedup'},'cycle_speedup':baseline['cycles']/row['cycles']})
    print(f'Evidence: {destination}/results.json; speedup baseline divider={baseline["divider_bits"]}')

if __name__=='__main__':
    try:main()
    except (RuntimeError,OSError) as error:
        print(f'FAIL DSE: {error}',file=sys.stderr);sys.exit(1)
