"""Offline audit of preserved Linux experiment sources, checkpoints and scope."""
import json
from run import ROOT,HERE,sha
from platform_map import check_local_map,validate_window
def require(value,message):
    if not value:raise ValueError(message)
def main():
    dest=HERE/'reference';inventory=json.loads((dest/'inventory.json').read_text())
    require(inventory['manifest_sha256']==sha(HERE/'manifest.json'),'Changed platform profile')
    for name,digest in inventory['recipes'].items():require(sha(HERE/name)==digest,'Changed Linux recipe: '+name)
    for name,digest in inventory['files'].items():require(sha(dest/name)==digest,'Changed evidence: '+name)
    manifest=json.loads((HERE/'manifest.json').read_text())
    mmio=check_local_map(HERE,manifest)
    require(sha(ROOT/'labs/17-complete-case/manifest.json')==manifest['common_manifest_sha256'],'Changed common RTL release manifest')
    for name,digest in manifest['rtl_sha256'].items():require(sha(ROOT/name)==digest,'Changed accelerator RTL')
    q=json.loads((dest/'qemu-report.json').read_text());summary=json.loads((dest/'results.json').read_text())
    require(q['status']==summary['qemu']=='pass' and len(q['metrics'])==10,'Missing Linux results')
    for name,digest in q['sources'].items():require(sha(HERE/name)==digest,'Changed compiled software/model')
    for name,marker in [('normal.txt','HSD_LINUX_ACCEL_PASS'),('dma-error.txt','HSD_DMA_ERROR_PASS'),
                        ('timeout.txt','HSD_TIMEOUT_QUARANTINE_PASS')]:
        text=(dest/name).read_text();require(marker in text and 'HSD_DRIVER_READY' in text and 'Kernel panic' not in text,'Missing OS/driver checkpoint')
    require(summary['measurement_scope'].startswith('emulator/'),'Hardware speedup must not be claimed from QEMU timing')
    if summary['wally']=='pass':
        w=json.loads((dest/'wally-report.json').read_text());text=(dest/'wally-uart.txt').read_text()
        require(w['status']=='pass' and w['bundle']==q['bundle'],'Different Wally software/boot bundle')
        require(w['local_sources']['manifest.json']==inventory['manifest_sha256'],'Different advanced platform profile')
        for name in ['wally.py','platform_map.py','tb_wally_linux.sv','boot-wally.S','boot-smoke.S','wally-linux.dts']:
            require(sha(HERE/name)==w['local_sources'][name],'Changed Wally execution input')
        address_map=json.loads((dest/'wally-address-map.json').read_text())
        require(address_map['status']=='pass' and address_map['base']==mmio and address_map['page_bytes']==4096 and address_map['aperture_bytes']==32,'Invalid Wally mapping audit')
        require(address_map['config_sha256']==w['original_sources']['config/rv64gc/config.vh'],'Different pinned memory map')
        require(sha(dest/'wally-address-map.json')==w['prepared_artifacts']['address-map.json'],'Changed prepared memory map')
        require(any(r['name']=='GPIO' and r['enabled'] for r in address_map['regions']),'GPIO must remain enabled')
        validate_window(address_map['regions'],mmio,4096)
        require(all(command.get('exit_code')==0 for command in w['commands']),'Incomplete/failed advanced command')
        require(len(summary['wally_metrics'])==10,'Incomplete advanced measurements')
        require(w['stages'].get('smoke')=='pass' and 'WALLY_MMIO_SMOKE_PASS' in (dest/'wally-smoke.txt').read_text(),'Missing CPU/MMIO/DMA preflight')
        require(all(marker in text for marker in ['OpenSBI','Linux version 6.12','HSD_DRIVER_READY','HSD_LINUX_ACCEL_PASS','WALLY_LINUX_ACCEL_PASS']),'Missing real RTL Linux checkpoints')
    print('PASS Linux evidence: real QEMU/kernel/driver/DMA/IRQ/application and faults; advanced Wally status='+summary['wally'])
if __name__=='__main__':main()
