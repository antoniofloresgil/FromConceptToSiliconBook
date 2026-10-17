"""Real two-CPU Linux/QEMU DMA handoffs, plus separately scoped abstract models."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from models import experiment

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];LAB18=ROOT/'labs/18-linux-accelerator'
INPUTS=['hsd-dotproduct.c','hsd-dotproduct.h','dotproduct-driver.c','dotproduct-uapi.h','linux-app.c','prepare.py']
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',default='labs/build/multicore')
    a=p.parse_args();out=(ROOT/a.output_dir).resolve()
    if not out.is_relative_to((ROOT/'labs/build').resolve()) or out.exists():raise ValueError('Choose a fresh labs/build directory')
    for name in INPUTS:
        if sha(LAB18/name)!=sha(Path('/opt/hsd')/name):raise ValueError('Rebuild Linux base image: '+name)
    if sha(HERE/'smp.c')!=sha(Path('/opt/multicore/smp.c')):raise ValueError('Rebuild multicore image')
    out.mkdir(parents=True)
    profile=json.loads((LAB18/'manifest.json').read_text())
    record={'status':'running','scope':'Actual Linux two-CPU software integration on QEMU; no modeled CPU cache hierarchy, coherent RTL or hardware performance claim',
        'image':os.environ.get('CASE_IMAGE_ID','unrecorded'),'sources':{p.name:sha(p) for p in HERE.iterdir() if p.is_file() and p.name!='README.md'},
        'dependencies':{str((LAB18/n).relative_to(ROOT)):sha(LAB18/n) for n in [*INPUTS,'manifest.json']},
        'commands':[],'profile':{'cpus':2,'ram_bytes':268435456,'mmio':profile['profile']['MMIO_BASE'],
        'dma_base':profile['profile']['DMA_BASE'],'jobs':96,'handoffs':64,'contenders_per_cpu':16},'tools':{}}
    def save():(out/'report.json').write_text(json.dumps(record,indent=2)+'\n')
    def command(argv,log,timeout=180):
        item={'argv':list(map(str,argv)),'log':log};record['commands'].append(item);save()
        try:result=subprocess.run(list(map(str,argv)),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
        except subprocess.TimeoutExpired as error:
            (out/log).write_bytes(error.stdout or b'');item['timeout']=True;save();raise
        (out/log).write_bytes(result.stdout);item['exit_code']=result.returncode;save()
        if result.returncode:raise RuntimeError('Command failed: '+log)
        return result.stdout.decode(errors='replace')
    try:
        record['tools']['qemu']=command(['qemu-system-riscv64','--version'],'qemu-version.txt').splitlines()[0]
        record['tools']['compiler']=command(['riscv64-linux-gnu-gcc','--version'],'compiler-version.txt').splitlines()[0]
        config=Path('/opt/linux/.config').read_text()
        if 'CONFIG_SMP=y' not in config:raise ValueError('Kernel lacks SMP')
        (out/'kernel.config').write_text(config)
        record['bundle']={str(p):sha(p) for p in [Path('/opt/linux/arch/riscv/boot/Image'),Path('/opt/multicore/rootfs.cpio'),
                Path('/usr/lib/riscv64-linux-gnu/opensbi/generic/fw_dynamic.bin'),Path('/opt/multicore/init')]}
        command(['riscv64-linux-gnu-objdump','-d','/opt/multicore/init'],'disassembly.txt')
        model=experiment();(out/'models.json').write_text(json.dumps(model,indent=2)+'\n')
        base=['qemu-system-riscv64','-machine','virt','-m','256M','-smp','2','-nographic','-no-reboot',
            '-bios','/usr/lib/riscv64-linux-gnu/opensbi/generic/fw_dynamic.bin','-kernel','/opt/linux/arch/riscv/boot/Image',
            '-initrd','/opt/multicore/rootfs.cpio']
        command([*base,'-machine','dumpdtb='+str(out/'virt.dtb')],'dumpdtb.txt')
        command(['dtc','-I','dtb','-O','dts','-o',out/'virt.dts',out/'virt.dtb'],'dtc.txt')
        text=command([*base,'-append','console=ttyS0 earlycon=uart8250,mmio,0x10000000 rdinit=/init nokaslr '+
                     ' '.join(profile['profile']['common_kernel_args'])],'uart.txt')
        for marker in ['HSD_DRIVER_READY','HSD_SMP_READY online=2','HSD_SMP_CONTENTION_PASS cpu0_jobs=16 cpu1_jobs=16',
                       'HSD_MULTICORE_PASS jobs=96 producer_cpu=0 worker_cpu=1']:
            if marker not in text:raise RuntimeError('Missing actual checkpoint: '+marker)
        if 'HSD_MULTICORE_FAIL' in text or 'Kernel panic' in text:raise RuntimeError('Failed guest experiment')
        metrics=[{'epoch':int(e),'cpu':int(cpu),'length':int(n),'mode':mode,'ioctl_ns':int(t)} for e,cpu,n,mode,t in
            re.findall(r'HSD_SMP_JOB epoch=(\d+) cpu=(\d+) n=(\d+) mode=(irq|poll) ioctl_ns=(\d+)',text)]
        if [(m['epoch'],m['cpu'],m['length'],m['mode']) for m in metrics]!=[(e,1,[1,8,32,128,256][(e-1)%5],'poll' if e%2 else 'irq') for e in range(1,65)]:
            raise RuntimeError('Incomplete pinned-CPU handoff regression')
        transfers=Counter(tuple(map(int,t)) for t in re.findall(r'HSD_MODEL n=(\d+) error=(\d+) reads=(\d+) writes=(\d+)',text))
        expected=Counter((n,0,2*n,2) for n in [[1,8,32,128,256][i%5] for i in range(64)]+[32]*32)
        if transfers!=expected:raise RuntimeError('Wrong accepted DMA counts')
        if 'cpu@0' not in (out/'virt.dts').read_text() or 'cpu@1' not in (out/'virt.dts').read_text():raise RuntimeError('Missing two DT harts')
        elapsed=re.search(r'HSD_SMP_METRIC handoffs=64 elapsed_ns=(\d+)',text)
        if not elapsed:raise RuntimeError('Missing elapsed interval')
        overlap=re.search(r'HSD_SMP_OVERLAP ns=(\d+)',text)
        if not overlap or int(overlap[1])<=0:raise RuntimeError('Concurrent callers did not overlap')
        irq=re.search(r'HSD_SMP_IRQ_COUNTS\s+\d+:\s+(\d+)\s+(\d+)',text)
        if not irq or sum(map(int,irq.groups()))<48:raise RuntimeError('Missing IRQ accounting for interrupt-mode jobs')
        record.update(status='pass',metrics=metrics,handoff_elapsed_ns=int(elapsed[1]),
                      contender_overlap_ns=int(overlap[1]),irq_counts=list(map(int,irq.groups())),
                      timing_scope='Single emulator elapsed-time observations; no physical cache/NoC timing or multicore hardware speedup claim')
    except Exception as error:record.update(status='fail',error=str(error));raise
    finally:
        record['artifacts']={p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file() and p.name!='report.json'};save()
    print('PASS two-CPU Linux: 64 release/acquire DMA handoffs, 32 contending jobs, IRQ/poll and separate abstract witnesses')

if __name__=='__main__':main()
