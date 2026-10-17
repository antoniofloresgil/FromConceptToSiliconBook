"""Offline audit of the two-CPU experiment; never treats QEMU as a cache protocol model."""
import json
from models import experiment
from run import HERE,ROOT,sha

def require(value,message):
    if not value:raise ValueError(message)

def main():
    dest=HERE/'reference';inventory=json.loads((dest/'inventory.json').read_text())
    for name,digest in inventory.items():require(sha(dest/name)==digest,'Changed evidence: '+name)
    report=json.loads((dest/'report.json').read_text())
    require(report['status']=='pass' and len(report['metrics'])==64,'Incomplete two-CPU execution')
    require(report['profile']['jobs']==96 and report['profile']['cpus']==2,'Wrong workload or CPU count')
    require(report['contender_overlap_ns']>0 and sum(report['irq_counts'])>=48,'Missing overlapping callers or IRQ deliveries')
    for name,digest in report['sources'].items():require(sha(HERE/name)==digest,'Changed multicore source: '+name)
    for name,digest in report['dependencies'].items():require(sha(ROOT/name)==digest,'Changed original dependency: '+name)
    for name,digest in inventory.items():
        if name!='report.json':require(report['artifacts'][name]==digest,'Artifact is not from recorded run')
    require(all(c['exit_code']==0 for c in report['commands']),'Failed or incomplete command')
    text=(dest/'uart.txt').read_text()
    for marker in ['HSD_DRIVER_READY','HSD_SMP_READY online=2','HSD_SMP_CONTENTION_PASS cpu0_jobs=16 cpu1_jobs=16',
                   'HSD_MULTICORE_PASS jobs=96 producer_cpu=0 worker_cpu=1']:
        require(marker in text,'Missing real guest marker: '+marker)
    require('HSD_MULTICORE_FAIL' not in text and 'Kernel panic' not in text,'Failed guest')
    require('cpu@0' in (dest/'virt.dts').read_text() and 'cpu@1' in (dest/'virt.dts').read_text(),'Missing DT harts')
    require(json.loads((dest/'models.json').read_text())==experiment(),'Changed finite models/witnesses')
    print('PASS multicore reference: actual 2-CPU Linux, 96 DMA jobs, ownership/contenders; separate cache/ordering/dependency models')

if __name__=='__main__':main()
