"""Check the Linux MMIO contract and audit the pinned Wally memory map."""
import hashlib
from pathlib import Path
import re

REGIONS=('DTIM','IROM','BOOTROM','UNCORE_RAM','EXT_MEM','CLINT','GPIO','UART','PLIC','SDC','SPI','PWM')

def validate_window(regions,base,size):
    if size<=0 or base<0 or base+size>1<<32:raise ValueError('Invalid 32-bit MMIO window')
    for r in regions:
        if r['enabled'] and base<r['base']+r['size'] and r['base']<base+size:
            raise ValueError('MMIO overlaps Wally '+r['name'])

def check_local_map(here,manifest):
    here=Path(here);base=int(manifest['profile']['MMIO_BASE'],0)
    if manifest['profile']['MMIO_BYTES']!=32 or base%4096:raise ValueError('Require a dedicated aligned MMIO page and 32-byte aperture')
    patterns={
        'hsd-dotproduct.c':r'#define BASE (0x[0-9a-fA-F]+)',
        'tb_wally_linux.sv':r'c\.EXT_MEM_BASE=64\x27h([0-9a-fA-F]+)',
        'boot-smoke.S':r'li t2,(0x[0-9a-fA-F]+)',
        'wally-linux.dts':r'dotproduct@([0-9a-fA-F]+)'}
    for name,pattern in patterns.items():
        match=re.search(pattern,(here/name).read_text())
        if not match or int(match[1],16)!=base:raise ValueError('MMIO manifest/source mismatch: '+name)
    dts=(here/'wally-linux.dts').read_text()
    if f'reg = <0 {base:#x} 0 0x20>' not in dts:raise ValueError('MMIO Device Tree reg mismatch')
    tb=(here/'tb_wally_linux.sv').read_text()
    if 'c.GPIO_SUPPORTED=1;' not in tb or not manifest['wally_profile']['gpio']:
        raise ValueError('The relocated Linux profile must preserve GPIO')
    return base

def audit_config(config,manifest):
    text=Path(config).read_text(encoding='utf-8');regions=[]
    def value(name):
        match=re.search(r'\b'+name+r'\s*=\s*(?:64\x27h([0-9a-fA-F_]+)|([01]))\s*;',text)
        if not match:raise ValueError('Unsupported pinned Wally parameter: '+name)
        return int(match[1].replace('_',''),16) if match[1] else int(match[2])
    for name in REGIONS:
        region={'name':name,'base':value(name+'_BASE'),'size':value(name+'_RANGE')+1,'enabled':bool(value(name+'_SUPPORTED'))}
        if name=='EXT_MEM':continue # This disabled native aperture is reassigned to the accelerator.
        if name=='UNCORE_RAM':region.update(base=int(manifest['profile']['ram_base'],0),size=manifest['profile']['ram_bytes'])
        regions.append(region)
    base=int(manifest['profile']['MMIO_BASE'],0)
    validate_window(regions,base,4096) # Check the whole Linux mapping page, not only the registers.
    gpio=next(r for r in regions if r['name']=='GPIO')
    if not gpio['enabled'] or not manifest['wally_profile']['gpio']:raise ValueError('GPIO must remain enabled')
    return {'status':'pass','config_sha256':hashlib.sha256(Path(config).read_bytes()).hexdigest(),
            'scope':'Pinned RV64gc map with the declared Linux RAM override; GPIO preserved; dedicated MMIO page',
            'base':base,'aperture_bytes':32,'page_bytes':4096,'regions':regions}
