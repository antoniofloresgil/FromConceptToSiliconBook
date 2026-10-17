"""Run Linux -> real kernel driver -> emulated MMIO/DMA/IRQ -> userspace checks."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import os
from platform_map import check_local_map

ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
BUILT=Path('/opt/hsd');KERNEL=Path('/opt/linux/arch/riscv/boot/Image')
FW=Path('/usr/lib/riscv64-linux-gnu/opensbi/generic/fw_dynamic.bin')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',default='labs/build/linux-accelerator')
    args=parser.parse_args();out=(ROOT/args.output_dir).resolve()
    if not out.is_relative_to((ROOT/'labs/build').resolve()):raise ValueError('Output outside labs/build')
    if out.exists() and any(out.iterdir()):raise ValueError('Preserve evidence: select a fresh output directory')
    out.mkdir(parents=True)
    inputs=['hsd-dotproduct.c','hsd-dotproduct.h','dotproduct-driver.c','dotproduct-uapi.h','linux-app.c','prepare.py']
    for name in inputs:
        if sha(HERE/name)!=sha(BUILT/name):raise ValueError('Rebuild image after source change: '+name)
    manifest=json.loads((HERE/'manifest.json').read_text())
    mmio=check_local_map(HERE,manifest)
    for name,digest in manifest['rtl_sha256'].items():
        if sha(ROOT/name)!=digest:raise ValueError('Original RTL release changed: '+name)
    record={'status':'running','scope':'QEMU virt RV64 software-visible device model; no RTL timing/performance claim',
            'manifest':manifest,'manifest_sha256':sha(HERE/'manifest.json'),
            'image':os.environ.get('CASE_IMAGE_ID','unrecorded'),
            'sources':{n:sha(HERE/n) for n in inputs},'commands':[],'runs':{},
            'qemu':subprocess.check_output(['qemu-system-riscv64','--version'],text=True).splitlines()[0]}
    def save():(out/'report.json').write_text(json.dumps(record,indent=2)+'\n')
    def command(argv,log,timeout=120):
        item={'argv':argv,'log':log};record['commands'].append(item);save()
        with (out/log).open('w') as stream:
            result=subprocess.run(argv,stdout=stream,stderr=subprocess.STDOUT,timeout=timeout)
        item['exit_code']=result.returncode;save()
        if result.returncode:raise RuntimeError('Command failed: '+str(out/log))
    save()
    try:
        bundle=out/'bundle';bundle.mkdir()
        command(['python3',str(HERE/'model_test.py'),str(out/'model')],'model-test.txt')
        for source,name in [(KERNEL,'Image'),(BUILT/'rootfs.cpio','rootfs.cpio'),(FW,'fw_dynamic.bin'),
                            (Path('/opt/linux/.config'),'kernel.config')]:shutil.copyfile(source,bundle/name)
        base=['qemu-system-riscv64','-machine','virt','-m','256M','-smp','1','-nographic','-no-reboot',
              '-bios',str(FW),'-kernel',str(KERNEL),'-initrd',str(BUILT/'rootfs.cpio')]
        command([*base,'-machine','dumpdtb='+str(out/'virt.dtb')],'dumpdtb.txt')
        command(['dtc','-I','dtb','-O','dts','-o',str(out/'virt.dts'),str(out/'virt.dtb')],'dtc.txt')
        dts=(out/'virt.dts').read_text()
        if any(s not in dts for s in ['hsd,dotproduct-v1','shared-dma-pool','0x88000000',f'dotproduct@{mmio:x}',f'0x{mmio:x}']):raise RuntimeError('Missing DT integration')
        for mode,extra,marker in [
            ('normal',[],'HSD_LINUX_ACCEL_PASS'),
            ('dma-error',['-global','hsd-dotproduct.dma-error=on'],'HSD_DMA_ERROR_PASS'),
            ('timeout',['-global','hsd-dotproduct.drop-irq=on'],'HSD_TIMEOUT_QUARANTINE_PASS')]:
            command([*base,*extra,'-append','console=ttyS0 earlycon=uart8250,mmio,0x10000000 rdinit=/init nokaslr '+
                     ' '.join(manifest['profile']['common_kernel_args'])+' hsd.test='+mode],mode+'.txt')
            text=(out/(mode+'.txt')).read_text()
            if marker not in text or 'HSD_DRIVER_READY' not in text or 'Linux version 6.12' not in text or 'HSD_LINUX_ACCEL_FAIL' in text or 'Kernel panic' in text:
                raise RuntimeError('Incomplete Linux/driver evidence: '+mode)
            record['runs'][mode]={'status':'pass','marker':marker};save()
        normal=(out/'normal.txt').read_text()
        metrics=[{'mode':mode,'length':int(n),'software_ns':int(sw),'end_to_end_ns':int(total),'kernel_ns':int(kernel)}
                 for mode,n,sw,total,kernel in re.findall(r'HSD_METRIC mode=(irq|poll) n=(\d+) software_ns=(\d+) end_to_end_ns=(\d+) kernel_ns=(\d+)',normal)]
        if [(m['mode'],m['length']) for m in metrics]!=[(mode,n) for mode in ['irq','poll'] for n in [1,8,32,128,256]]:
            raise RuntimeError('Missing userspace metrics')
        transfers=[tuple(map(int,m)) for m in re.findall(r'HSD_MODEL n=(\d+) error=(\d+) reads=(\d+) writes=(\d+)',normal)]
        if sorted(transfers)!=sorted((n,0,2*n,2) for n in [1,8,32,128,256] for _ in range(2)):
            raise RuntimeError('Wrong accepted DMA transaction counts')
        record['metrics']=metrics;record['timing_interpretation']='emulator/software overhead with a fixed 10000 ns virtual device delay; not a physical accelerator speedup'
        record['bundle']={p.name:sha(p) for p in bundle.iterdir()}
        record['status']='pass'
    except (OSError,ValueError,RuntimeError,subprocess.TimeoutExpired) as error:
        record.update(status='fail',error=str(error));raise
    finally:
        record['artifacts']={p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file() and p.name!='report.json'}
        save()
    print('PASS Linux accelerator: DT, kernel driver, coherent DMA pool, IRQ/poll, application, errors and timeout quarantine')

if __name__=='__main__':main()
