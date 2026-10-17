"""Preserve separately scoped Linux/QEMU and advanced Wally execution evidence."""
import argparse
import json
from pathlib import Path
import re
import shutil
from run import ROOT,HERE,sha
from platform_map import audit_config,check_local_map

def require(value,message):
    if not value:raise ValueError(message)
def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qemu',type=Path,required=True);parser.add_argument('--wally',type=Path)
    parser.add_argument('--publish-reference',action='store_true');args=parser.parse_args()
    report=json.loads(args.qemu.read_text());base=args.qemu.parent
    check_local_map(HERE,report['manifest'])
    require(report['status']=='pass','Incomplete QEMU experiment')
    require(report['manifest_sha256']==sha(HERE/'manifest.json'),'Different Linux profile')
    for name,digest in report['sources'].items():require(sha(HERE/name)==digest,'Changed compiled input: '+name)
    for name,digest in report['artifacts'].items():require(sha(base/name)==digest,'Stale QEMU artifact: '+name)
    model=json.loads((base/'model/report.json').read_text());require(model['status']=='pass' and len(model['checks'])==7,'Incomplete model tests')
    summary={'qemu':'pass','qemu_metrics':report['metrics'],'wally':'not_run',
             'measurement_scope':report['timing_interpretation'],'manifest_sha256':report['manifest_sha256']}
    wally=None
    if args.wally:
        wally=json.loads(args.wally.read_text());summary['wally']=wally['status'];summary['wally_stages']=wally['stages']
        if wally['status']=='pass':
            require(all(wally['stages'].get(stage)=='pass' for stage in ['prepare','compile','smoke','run']),'Incomplete Wally stages')
            require(all(command.get('exit_code')==0 for command in wally['commands']),'Failed/incomplete Wally command')
            require(wally['local_sources']['manifest.json']==report['manifest_sha256'],'Different Wally platform profile')
            for name in ['wally.py','platform_map.py','tb_wally_linux.sv','boot-wally.S','boot-smoke.S','wally-linux.dts']:
                require(sha(HERE/name)==wally['local_sources'][name],'Changed Wally execution recipe: '+name)
            address_map=json.loads((args.wally.parent/'address-map.json').read_text())
            require(address_map==audit_config(args.wally.parent/'vendor/config/rv64gc/config.vh',report['manifest']),'Stale Wally address map')
            require(address_map['config_sha256']==wally['original_sources']['config/rv64gc/config.vh'],'Different pinned memory map')
            text=(args.wally.parent/'uart.txt').read_text()
            require('WALLY_MMIO_SMOKE_PASS' in (args.wally.parent/'smoke.txt').read_text(),'Missing CPU/MMIO/DMA preflight')
            for arg in report['manifest']['profile']['common_kernel_args']:
                require(arg in (args.wally.parent/'wally-linux.dts').read_text(),'Different advanced kernel arguments')
            for marker in ['OpenSBI','Linux version 6.12','HSD_DRIVER_READY','HSD_LINUX_ACCEL_PASS','WALLY_LINUX_ACCEL_PASS']:
                require(marker in text,'Missing actual Wally Linux checkpoint: '+marker)
            for name,digest in wally['compiled_sources'].items():require(sha(ROOT/name)==digest,'Changed RTL after execution')
            for name,digest in wally['patched_sources'].items():
                require(sha(args.wally.parent/'vendor'/name)==digest,'Changed Wally source/configuration after preparation: '+name)
            for name,digest in wally['prepared_artifacts'].items():
                require(sha(args.wally.parent/name)==digest,'Changed Wally boot/preflight artifact: '+name)
            require(sha(args.wally.parent/'obj_dir/Vtb_wally_linux')==wally['executable_sha256'],'Changed RTL executable')
            require(wally['bundle']==report['bundle'],'Wally used a different kernel/driver/application bundle')
            summary['wally_cycles']=int(re.search(r'WALLY_LINUX_ACCEL_PASS cycles=(\d+)',text)[1])
            metrics=[{'mode':mode,'length':int(n),'software_ns':int(sw),'end_to_end_ns':int(total),'kernel_ns':int(kernel)}
                     for mode,n,sw,total,kernel in re.findall(r'HSD_METRIC mode=(irq|poll) n=(\d+) software_ns=(\d+) end_to_end_ns=(\d+) kernel_ns=(\d+)',text)]
            require([(m['mode'],m['length']) for m in metrics]==[(mode,n) for mode in ['irq','poll'] for n in [1,8,32,128,256]],'Missing Wally application measurements')
            summary['wally_metrics']=metrics
            summary['wally_measurement_scope']='CPU/RTL simulation with a 100 MHz timebase, D-cache enabled, an uncached PMA DMA pool and behavioral shared RAM; not implemented FPGA/DDR timing. wally_cycles covers reset, firmware, kernel boot and the complete userspace regression.'
    if args.publish_reference:
        dest=HERE/'reference';dest.mkdir(exist_ok=True)
        for name in ['normal.txt','dma-error.txt','timeout.txt','virt.dts']:
            shutil.copyfile(base/name,dest/name)
        shutil.copyfile(args.qemu,dest/'qemu-report.json')
        shutil.copyfile(base/'model/report.json',dest/'model-report.json')
        shutil.copyfile(base/'model/model.txt',dest/'model.txt')
        if wally:
            shutil.copyfile(args.wally,dest/'wally-report.json')
            for name in ['address-map.json','uart.txt','smoke.txt','progress.txt','wally-linux.dts']:
                if (args.wally.parent/name).exists():shutil.copyfile(args.wally.parent/name,dest/('wally-'+name))
        write(dest/'results.json',summary)
        recipes={p.name:sha(p) for p in HERE.iterdir() if p.is_file() and p.name!='README.md'}
        inventory={'manifest_sha256':summary['manifest_sha256'],'recipes':recipes,
                   'files':{p.name:sha(p) for p in dest.iterdir() if p.is_file() and p.name!='inventory.json'}}
        write(dest/'inventory.json',inventory)
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
