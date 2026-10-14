"""The reference suite must reject arithmetic and premature-completion defects."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

project=Path(__file__).resolve().parent
build=Path(sys.argv[1]).resolve()
build.mkdir(parents=True,exist_ok=True)
subprocess.run([sys.executable,project/'vectors.py',build,'2026'],check=True)
mutations={
 'unsigned': ('a * b','$unsigned(a) * $unsigned(b)'),
 'early-done': ('state <= WRITE; aw_sent <= 0; w_sent <= 0;',
                'done <= 1; state <= WRITE; aw_sent <= 0; w_sent <= 0;'),
}
records={}
for name,(before,after) in mutations.items():
    variant=build/name
    variant.mkdir(exist_ok=True)
    for source in (project/'rtl').glob('*.sv'): shutil.copyfile(source,variant/source.name)
    engine=variant/('dotproduct_mac.sv' if name=='unsigned' else 'dotproduct_engine.sv');text=engine.read_text()
    if text.count(before)!=1: raise RuntimeError('Mutation anchor changed')
    engine.write_text(text.replace(before,after))
    executable=variant/'test.vvp'
    subprocess.run(['iverilog','-g2012','-I',str(project),'-s','tb_dotproduct',
                    '-DTEST_MAX_LENGTH=16','-o',str(executable),
                    *map(str,sorted(variant.glob('*.sv'))),str(project/'axi_ram_model.sv'),
                    str(project/'tb_dotproduct.sv')],check=True,stdout=subprocess.DEVNULL)
    result=subprocess.run(['vvp',str(executable)],cwd=build,capture_output=True,text=True,timeout=60)
    (variant/'simulation.log').write_text(result.stdout+result.stderr)
    marker='Arithmetic/status mismatch' if name=='unsigned' else 'Premature DONE'
    if result.returncode==0 or marker not in result.stdout: raise RuntimeError(f'Tests did not detect {name}')
    records[name]={'simulation':'expected failure','message':result.stdout.strip()}
    if name=='early-done':
        counterexample=variant/'engine-counterexample.vcd'
        if counterexample.exists(): counterexample.unlink()
        result=subprocess.run([sys.executable,project/'formal/check.py',variant,variant],
                              capture_output=True,text=True,timeout=600)
        (variant/'formal-driver.log').write_text(result.stdout+result.stderr)
        if result.returncode==0 or not (variant/'engine-counterexample.vcd').exists():
            raise RuntimeError('Formal check failed to produce the expected counterexample')
        records[name]['formal']='expected failure with counterexample'
    print(f'PASS negative test: {name} was rejected')
(build/'negative-results.json').write_text(json.dumps(records,indent=2)+'\n')
