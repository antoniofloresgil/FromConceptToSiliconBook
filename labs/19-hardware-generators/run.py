"""Generate real Chisel RTL, retain IRs, compare against an independent contract."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
ORIGINAL='examples/verilator/accumulator.sv'
COMPILED=['build.sbt','project/build.properties','src/main/scala/Accumulator.scala']

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def vectors(width,seed):
    rng=random.Random(seed+width);mask=(1<<width)-1
    stimulus=[(1,1,1,mask),(0,1,1,3),(0,0,1,mask),(0,0,1,1),
              (0,0,0,mask),(0,0,1,mask),(0,1,0,mask),(1,0,1,1)]
    stimulus += [(r,c,e,n) for r in [0,1] for c in [0,1] for e in [0,1] for n in [0,1,mask-1,mask]]
    stimulus += [(int(rng.random()<.05),int(rng.random()<.1),int(rng.random()<.65),rng.getrandbits(width)) for _ in range(512)]
    total=0;rows=[];coverage=Counter()
    for reset,clear,enable,operand in stimulus:
        carry=0;valid=0
        if reset or clear:total=0
        else:
            valid=enable
            if enable:
                wide=total+operand;carry=int(wide>mask);total=wide&mask
        coverage['reset']+=reset;coverage['clear_and_enable']+=int(clear and enable and not reset)
        coverage['hold']+=int(not (reset or clear or enable));coverage['overflow']+=carry
        rows.append(f'{reset} {clear} {enable} {operand:x} {total:x} {valid} {carry}\n')
    if not all(coverage[k]>0 for k in ['reset','clear_and_enable','hold','overflow']):raise ValueError('Incomplete stimulus')
    return ''.join(rows),dict(coverage),len(rows)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir',default='labs/build/hardware-generators');p.add_argument('--seed',type=int,default=2026)
    args=p.parse_args();out=(ROOT/args.output_dir).resolve()
    if not out.is_relative_to((ROOT/'labs/build').resolve()):raise ValueError('Output outside labs/build')
    if out.exists():raise ValueError('Preserve evidence: choose a fresh output directory')
    for name in COMPILED:
        if sha(HERE/name)!=sha(Path('/opt/generator')/name):raise ValueError('Rebuild image after generator change: '+name)
    out.mkdir(parents=True)
    record={'status':'running','seed':args.seed,'image':os.environ.get('CASE_IMAGE_ID','unrecorded'),
      'scope':'Sampled cycle-level checks against an independent integer contract; generic synthesis statistics; no general equivalence or physical PPA claim',
      'versions':{},'toolchain':{'scala':'2.13.12','chisel':'6.5.0','sbt':'1.10.2','firtool':'1.62.0'},
      'commands':[],'cases':{},'original_source':{ORIGINAL:sha(ROOT/ORIGINAL)},
      'sources':{p.relative_to(HERE).as_posix():sha(p) for p in HERE.rglob('*') if p.is_file() and 'reference' not in p.relative_to(HERE).parts and '__pycache__' not in p.parts and p.name!='README.md'}}
    def save():(out/'report.json').write_text(json.dumps(record,indent=2)+'\n')
    def command(argv,log,expected_failure=False,cwd=out):
        item={'argv':list(map(str,argv)),'log':log,'expected_failure':expected_failure};record['commands'].append(item);save()
        result=subprocess.run(list(map(str,argv)),cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=300)
        text=result.stdout.decode(errors='replace');(out/log).write_text(text);item['exit_code']=result.returncode;save()
        if bool(result.returncode)!=expected_failure:raise RuntimeError('Unexpected result: '+log+'\n'+text[-3000:])
        return text
    try:
        for name,argv in {'java':['java','-version'],'firtool':['firtool','--version'],
                          'yosys':['yosys','-V'],'iverilog':['iverilog','-V']}.items():
            text=command(argv,name+'-version.txt').strip()
            record['versions'][name]=text if name=='firtool' else text.splitlines()[0]
        if 'CIRCT firtool-1.62.0' not in record['versions']['firtool']:raise ValueError('Unexpected lowering backend')
        classpath=Path('/opt/generator.classpath').read_text().strip()
        (out/'runtime-classpath.txt').write_text(classpath+'\n')
        (out/'build.txt').write_bytes(Path('/opt/generator-build.txt').read_bytes())
        record['runtime_jars']={name:sha(Path(name)) for name in classpath.split(':') if Path(name).is_file()}
        command(['java','-Duser.home=/tmp','-cp',classpath,'Emit',out],'elaboration.txt',cwd=Path('/opt/generator'))
        for width,bad in [(8,False),(16,False),(32,False),(16,True)]:
            name='fault-w16' if bad else 'w'+str(width);directory=out/name
            fir=directory/'Accumulator.fir';sv=directory/'Accumulator.sv'
            command(['firtool',fir,'--disable-all-randomization','--lowering-options=disallowLocalVariables','-o',sv],name+'-lower.txt')
            command(['firtool',fir,'--ir-hw','-o',directory/'lowered.mlir'],name+'-ir.txt')
            data,coverage,count=vectors(width,args.seed);(directory/'vectors.txt').write_text(data)
            command(['iverilog','-g2012','-s','tb','-Ptb.W='+str(width),'-o',directory/'sim.vvp',
                     HERE/'tb.sv',HERE/'accumulator_sv.sv',ROOT/ORIGINAL,sv],name+'-compile.txt')
            text=command(['vvp',directory/'sim.vvp','+VECTORS='+str(directory/'vectors.txt')],name+'-simulation.txt',bad)
            if bad:
                if 'GENERATED_MISMATCH cycle=1' not in text or 'DIRECT_MISMATCH' in text or 'ORIGINAL_MISMATCH' in text:
                    raise RuntimeError('Negative control did not expose the intended priority bug')
            elif f'GENERATOR_COMPARISON_PASS width={width} cycles={count}' not in text:raise RuntimeError('Missing checks')
            case={'status':'expected_mismatch' if bad else 'pass','width':width,'bad_clear_priority':bad,
                  'cycles':2 if bad else count,'vector_count':count,'stimulus_coverage':coverage}
            if not bad:
                case['synthesis']={}
                for variant,source,top in [('direct',HERE/'accumulator_sv.sv','accumulator_sv'),('generated',sv,'Accumulator')]:
                    output=directory/(variant+'-synth.json')
                    parameter=f' -chparam W {width}' if variant=='direct' else ''
                    script=f'read_verilog -sv {source}; hierarchy -top {top}{parameter}; synth -top {top} -noabc; write_json {output}'
                    command(['yosys','-Q','-T','-p',script],name+'-'+variant+'-synthesis.txt')
                    module=json.loads(output.read_text())['modules'][top]
                    case['synthesis'][variant]={'generic_cells':len(module['cells']),
                        'cell_types':dict(Counter(c['type'] for c in module['cells'].values()))}
            record['cases'][name]=case;save()
        record['status']='pass'
    except Exception as error:record.update(status='fail',error=str(error));raise
    finally:
        record['artifacts']={p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file() and p.name!='report.json'};save()
    print('PASS Chisel/FIRRTL/CIRCT: three widths, independent scoreboard, original 16-bit RTL, generic synthesis and rejected priority defect')

if __name__=='__main__':main()
