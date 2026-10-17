"""Fail-closed accelerator pipeline; use a fresh output directory for each run."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent/'10-dotproduct'
STAGES = ['Lint', 'Elaboration', 'Simulation', 'Formal', 'Synthesis', 'Reports']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def interface(module):
    return dict(ports={k:dict(direction=v['direction'], width=len(v['bits']),
                             signed=v.get('signed',0)) for k,v in module['ports'].items()},
                parameters=module['parameter_default_values'])

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--rtl', type=Path, default=PROJECT/'rtl')
    a=p.parse_args()
    out=a.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    policy=json.loads((HERE/'policy.json').read_text())
    shutil.copytree(PROJECT, out/'input', ignore=shutil.ignore_patterns('__pycache__'))
    for path in (out/'input/rtl').glob('*.sv'): path.unlink()
    for path in a.rtl.glob('*.sv'): shutil.copyfile(path,out/'input/rtl'/path.name)
    project=out/'input'
    sources=[project/'rtl'/name for name in policy['rtl_files']]
    for path in sources:
        if not path.is_file(): raise ValueError('Missing RTL: '+path.name)
    inputs={str(p.relative_to(project)):sha(p) for p in project.rglob('*') if p.is_file() and p.suffix!='.md'}
    report=dict(status='running', image_id=os.environ.get('LAB_IMAGE_ID','unrecorded'),
                revision=os.environ.get('GITHUB_SHA','local'), seed=2026, sources=inputs,
                runner_sha256=sha(Path(__file__)), policy_sha256=sha(HERE/'policy.json'),
                contract_sha256=sha(HERE/'contract.json'), stages=[], commands=[], metrics={}, tools={})
    for tool in ['verilator','iverilog','yosys']:
        v=subprocess.run([tool,'-V' if tool!='verilator' else '--version'],capture_output=True,text=True)
        report['tools'][tool]=(v.stdout+v.stderr).splitlines()[0]
    def save():
        (out/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    def run(argv, timeout=600):
        n=len(report['commands'])
        start=time.monotonic()
        try:
            r=subprocess.run(list(map(str,argv)),cwd=out,capture_output=True,text=True,timeout=timeout)
            output=r.stdout+r.stderr
            code=r.returncode
        except subprocess.TimeoutExpired as exc:
            output='TIMEOUT\n'+str(exc)
            code=124
        name=f'command-{n:02d}.txt'
        (out/name).write_text(output)
        report['commands'].append(dict(stage=current,argv=list(map(str,argv)),
                                       returncode=code,log=name,seconds=round(time.monotonic()-start,3)))
        save()
        if code: raise RuntimeError(f'{current}: command failed ({code}); see {name}')
        return output
    files=' '.join('"'+p.as_posix()+'"' for p in sources)
    def yosys(script): return run(['yosys','-Q','-T','-p',f'read_verilog -sv {files}; '+script])
    current='Lint'
    try:
        for current in STAGES:
            item=dict(name=current,status='running')
            report['stages'].append(item);save()
            if current=='Lint':
                if report['tools']!=policy['tool_versions']:
                    raise RuntimeError('Tool versions changed; recalibrate lint and cell baseline explicitly')
                log=run(['verilator','--lint-only','--top-module','dotproduct_axi','-Wall','-Wno-fatal',*sources])
                # -Wno-fatal exposes every diagnostic; the exact reviewed multiset below is the gate.
                warnings=re.findall(r'^%Warning-([^:]+): .*[/\\]([^/\\:]+\.sv):\d+:\d+: (.*)$',log,re.M)
                actual=Counter(tuple(w) for w in warnings)
                expected=Counter(tuple(w) for w in policy['reviewed_lint'])
                if actual!=expected: raise RuntimeError('Unreviewed or changed lint diagnostics: '+str(warnings))
                if len(re.findall(r'^%Warning',log,re.M))!=len(warnings):
                    raise RuntimeError('Unparsed lint diagnostic')
            elif current=='Elaboration':
                yosys('hierarchy -check -top dotproduct_axi; proc; check -assert; write_json elaborated.json')
                actual=interface(json.loads((out/'elaborated.json').read_text())['modules']['dotproduct_axi'])
                (out/'interface.json').write_text(json.dumps(actual,indent=2,sort_keys=True)+'\n')
                if actual!=json.loads((HERE/'contract.json').read_text()):
                    raise RuntimeError('Interface/default-parameter contract changed; explicit ABI review required')
            elif current=='Simulation':
                run([sys.executable,project/'vectors.py',out,'2026'])
                for maximum in [256,16]:
                    run(['iverilog','-g2012','-I',project,'-s','tb_dotproduct',
                         f'-DTEST_MAX_LENGTH={maximum}','-o',out/'test.vvp',*sources,
                         project/'axi_ram_model.sv',project/'tb_dotproduct.sv'])
                    log=run(['vvp',out/'test.vvp','+SEED=2026'])
                    if f'PASS dotproduct: {maximum} lengths' not in log:
                        raise RuntimeError('Missing complete simulation marker')
                run(['iverilog','-g2012','-I',project,'-s','tb_bridge','-o',out/'bridge.vvp',
                     *sources,project/'axi_ram_model.sv',project/'tb_bridge.sv'])
                log=run(['vvp',out/'bridge.vvp'])
                if 'PASS' not in log: raise RuntimeError('Missing bridge marker')
            elif current=='Formal':
                log=run([sys.executable,project/'formal/check.py',out,project/'rtl'],timeout=660)
                if 'PASS bounded engine checks' not in log or not (out/'done-witness.vcd').is_file():
                    raise RuntimeError('Missing bounded proof or reachable completion witness')
                report['formal_scope']='20-cycle control BMC; 24-cycle length-one engine BMC and reachable DONE; not induction or full arithmetic proof'
            elif current=='Synthesis':
                yosys('synth -top dotproduct_axi -flatten; check -assert; select -assert-none t:$dlatch; '
                      'stat; write_json synthesized.json')
                m=json.loads((out/'synthesized.json').read_text())['modules']['dotproduct_axi']
                counts=Counter(c['type'] for c in m['cells'].values())
                report['metrics']=dict(generic_cells=sum(counts.values()),cell_types=dict(counts))
            else:
                count=report['metrics']['generic_cells']
                if count>policy['maximum_generic_cells']:
                    raise RuntimeError(f'Generic-cell budget exceeded: {count} > {policy["maximum_generic_cells"]}')
                for name,digest in inputs.items():
                    if sha(project/name)!=digest: raise RuntimeError('Input changed during execution')
                if sha(HERE/'policy.json')!=report['policy_sha256'] or sha(HERE/'contract.json')!=report['contract_sha256']:
                    raise RuntimeError('Policy changed during execution')
            item['status']='pass';save()
            print('PASS',current,flush=True)
        report['status']='pass'
    except Exception as exc:
        if report['stages']: report['stages'][-1].update(status='fail',reason=str(exc))
        report.update(status='fail',error=str(exc))
        print('FAIL',str(exc),flush=True)
    finally:
        done={s['name'] for s in report['stages']}
        report['stages'] += [dict(name=s,status='skipped') for s in STAGES if s not in done]
        report['artifacts']={str(p.relative_to(out)):sha(p) for p in out.rglob('*')
                             if p.is_file() and p.name!='report.json'}
        save()
    return 0 if report['status']=='pass' else 1

if __name__=='__main__': sys.exit(main())
