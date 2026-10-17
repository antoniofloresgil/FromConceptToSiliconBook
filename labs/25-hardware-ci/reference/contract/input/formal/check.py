"""Bounded RTL checks with Yosys SAT; does not claim unbounded AXI compliance."""
from pathlib import Path
import subprocess
import sys

project=Path(__file__).resolve().parent.parent
destination=Path(sys.argv[1]).resolve()
rtl=Path(sys.argv[2]).resolve() if len(sys.argv)>2 else project/'rtl'
sources=' '.join('"'+p.as_posix()+'"' for p in sorted(rtl.glob('*.sv')))
# Top-level inputs remain symbolic. Initial reset is constrained; subsequent
# resets are unconstrained and properties disable across reset boundaries.
script=(f'read_verilog -formal -sv {sources}; '
        'chparam -set MAX_LENGTH 16 dotproduct_axi; '
        'prep -top dotproduct_axi -flatten; opt_clean; '
        'sat -seq 20 -set-at 1 reset 1 -set-init-zero -prove-asserts -verify '
        '-dump_vcd formal-counterexample.vcd')
result=subprocess.run(['yosys','-Q','-T','-p',script],cwd=destination,
                      stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=300)
(destination/'formal.log').write_text(result.stdout)
if result.returncode:
    print(result.stdout[-4000:]);raise SystemExit(result.returncode)
print('PASS bounded control checks: 20 cycles, symbolic inputs, stalled responses and descriptor stability')
# The control bound is too short to complete a programmed DMA job.
# Check the engine separately with a fixed valid descriptor and
# obtain a reachable DONE witness; do not present a vacuous implication as proof.
prefix=(f'read_verilog -formal -sv {sources}; prep -top dotproduct_engine -flatten; opt_clean; ')
settings=('-seq 24 -set-init-zero -set reset 0 -set-at 1 reset 1 '
          '-set src_a 2147516416 -set src_b 2147517440 -set dst 2147518464 -set length 1 ')
for name, tail in [
    ('engine-proof','-prove-asserts -verify -dump_vcd engine-counterexample.vcd'),
    ('done-witness','-set-at 24 done 1 -show-inputs -show-outputs -dump_vcd done-witness.vcd'),
]:
    result=subprocess.run(['yosys','-Q','-T','-p',prefix+'sat '+settings+tail],cwd=destination,
                          stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=300)
    (destination/(name+'.log')).write_text(result.stdout)
    if result.returncode or (name=='done-witness' and 'model found' not in result.stdout):
        print(result.stdout[-4000:]);raise SystemExit(1)
print('PASS bounded engine checks: 24 cycles; reachable DONE witness saved, no fairness assumption or unbounded claim')
