"""Audit preserved generator evidence offline, including its negative control."""
from collections import Counter
import json
import re
from run import HERE,ROOT,sha

def require(condition,message):
    if not condition:raise ValueError(message)

def main():
    reference=HERE/'reference';inventory=json.loads((reference/'inventory.json').read_text())
    for name,digest in inventory['files'].items():require(sha(reference/name)==digest,'Changed evidence: '+name)
    report=json.loads((reference/'report.json').read_text())
    require(report['status']=='pass','Experiment did not complete')
    for name,digest in report['sources'].items():require(sha(HERE/name)==digest,'Changed recipe: '+name)
    for name,digest in report['original_source'].items():require(sha(ROOT/name)==digest,'Changed original accumulator')
    for name,digest in inventory['files'].items():
        if name!='report.json':require(report['artifacts'][name]==digest,'Evidence not from preserved execution')
    require(set(report['cases'])=={'w8','w16','w32','fault-w16'},'Incomplete width/negative-control matrix')
    require('CIRCT firtool-1.62.0' in report['versions']['firtool'],'Unexpected backend')
    for name,case in report['cases'].items():
        width=case['width'];bad=case['bad_clear_priority']
        text=(reference/(name+'-simulation.txt')).read_text()
        require(case['vector_count']==len((reference/name/'vectors.txt').read_text().splitlines()),'Incomplete vectors')
        require(all(case['stimulus_coverage'].get(k,0)>0 for k in ['reset','clear_and_enable','hold','overflow']),'Missing planned contract cases')
        require('circuit Accumulator' in (reference/name/'Accumulator.fir').read_text(),'Missing early FIRRTL')
        require('hw.module' in (reference/name/'lowered.mlir').read_text(),'Missing lowered HW representation')
        require(re.search(r'\bmodule\s+Accumulator\s*\(',(reference/name/'Accumulator.sv').read_text()),'Missing generated RTL')
        if bad:
            require(case['status']=='expected_mismatch' and case['cycles']==2 and 'GENERATED_MISMATCH cycle=1' in text,'Missing priority counterexample')
        else:
            require(case['status']=='pass' and f'GENERATOR_COMPARISON_PASS width={width} cycles={case["cycles"]}' in text,'Missing sampled comparison')
            require(case['cycles']==case['vector_count'],'Positive simulation did not consume all vectors')
            for variant,top in [('direct','accumulator_sv'),('generated','Accumulator')]:
                module=json.loads((reference/name/(variant+'-synth.json')).read_text())['modules'][top]
                stats={'generic_cells':len(module['cells']),'cell_types':dict(Counter(c['type'] for c in module['cells'].values()))}
                require(case['synthesis'][variant]==stats,'Changed synthesis statistics')
    for command in report['commands']:
        require(bool(command['exit_code'])==command['expected_failure'],'Unexpected tool result')
    require(sum(c['expected_failure'] for c in report['commands'])==1,'Missing unique negative control')
    print('PASS generator evidence: real Chisel/FIRRTL/CIRCT, three sampled widths, original SV, priority defect and six generic synthesis results')

if __name__=='__main__':main()
