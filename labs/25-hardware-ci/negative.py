"""Run actual RTL changes through the same pipeline; never alter baseline RTL."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--output',required=True,type=Path)
a=p.parse_args()
out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
cases={
    'contract':('dotproduct_axi.sv','MAX_LENGTH = 256','MAX_LENGTH = 257','Elaboration'),
    'arithmetic':('dotproduct_mac.sv','a * b','$unsigned(a) * $unsigned(b)','Simulation'),
    'assertion':('dotproduct_engine.sv','if(f_past_valid && !reset && !$past(reset)) begin',
                 'if(f_past_valid && !reset && !$past(reset)) begin\n      assert(1\'b0);','Formal'),
    'cell-growth':('dotproduct_axi.sv','  logic busy, done, error, pending, enable_irq, launch;',
                   '''  /* verilator lint_off UNUSEDSIGNAL */
  (* keep *) logic [255:0] ci_extra_counter;
  always_ff @(posedge clk)
    if (reset) ci_extra_counter <= 0;
    else ci_extra_counter <= ci_extra_counter + 256'd1;
  /* verilator lint_on UNUSEDSIGNAL */
  logic busy, done, error, pending, enable_irq, launch;''','Reports')
}
results={}
for name,(file,before,after,stage) in cases.items():
    rtl=out/name/'rtl'
    shutil.copytree(HERE.parent/'10-dotproduct/rtl',rtl)
    text=(rtl/file).read_text()
    if text.count(before)!=1: raise RuntimeError('Mutation anchor changed: '+name)
    (rtl/file).write_text(text.replace(before,after))
    r=subprocess.run([sys.executable,HERE/'run.py','--rtl',rtl,'--output',out/name/'run'],
                     capture_output=True,text=True,timeout=900)
    (out/name/'driver.txt').write_text(r.stdout+r.stderr)
    report=json.loads((out/name/'run/report.json').read_text())
    failed=[s for s in report['stages'] if s['status']=='fail']
    if r.returncode==0 or len(failed)!=1 or failed[0]['name']!=stage:
        raise RuntimeError(f'{name}: expected failure at {stage}; got {report["stages"]}')
    if name=='assertion' and not (out/name/'run/formal-counterexample.vcd').is_file():
        raise RuntimeError('Missing formal counterexample')
    results[name]=dict(status='rejected',stage=stage,error=report['error'],metrics=report['metrics'])
    print('PASS rejected',name,'at',stage,flush=True)
(out/'negative-results.json').write_text(json.dumps(results,indent=2,sort_keys=True)+'\n')
