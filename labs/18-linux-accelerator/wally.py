"""Advanced real Wally RV64 RTL Linux platform: prepare, compile, then bounded run."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tarfile
from platform_map import audit_config,check_local_map

ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
REVISION='3b30ba6b6519bd2c26c1437e6d61f632a35cef6c'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['prepare','compile','run'])
    parser.add_argument('--bundle',default='labs/build/linux-accelerator/bundle')
    parser.add_argument('--output-dir',default='labs/build/linux-wally')
    parser.add_argument('--seconds',type=int,default=1800)
    parser.add_argument('--cycles',type=int,default=500000000)
    args=parser.parse_args();out=(ROOT/args.output_dir).resolve();bundle=(ROOT/args.bundle).resolve()
    manifest=json.loads((HERE/'manifest.json').read_text())
    mmio=check_local_map(HERE,manifest)
    for name,digest in manifest['rtl_sha256'].items():
        if sha(ROOT/name)!=digest:raise ValueError('Changed original RTL release: '+name)
    if not out.is_relative_to((ROOT/'labs/build').resolve()):raise ValueError('Output outside labs/build')
    out.mkdir(parents=True,exist_ok=True);path=out/'report.json'
    record=json.loads(path.read_text()) if path.exists() else {'status':'not_run','stages':{},'commands':[]}
    record['image']=os.environ.get('CASE_IMAGE_ID',record.get('image','unrecorded'))
    def save():path.write_text(json.dumps(record,indent=2)+'\n')
    def command(argv,log,timeout=600,workdir=None):
        item={'argv':list(map(str,argv)),'log':log,'cwd':str(workdir or out)};record['commands'].append(item);save()
        with (out/log).open('w') as stream:
            try:result=subprocess.run(list(map(str,argv)),cwd=workdir or out,stdout=stream,stderr=subprocess.STDOUT,timeout=timeout)
            except subprocess.TimeoutExpired:
                item['timeout']=True;save();raise
        item['exit_code']=result.returncode;save()
        if result.returncode:raise RuntimeError('Inspect '+str(out/log))
    def replace(p,old,new):
        text=p.read_text()
        if text.count(old)!=1:raise ValueError('Pinned-source patch mismatch: '+str(p))
        p.write_text(text.replace(old,new))
    try:
        if args.stage=='prepare':
            if record['stages']:raise ValueError('Select a fresh advanced output directory')
            clone=os.environ.get('WALLY_ROOT')
            if not clone:raise ValueError('Set WALLY_ROOT to the read-only pinned clone')
            vendor=out/'vendor';vendor.mkdir()
            archive=subprocess.check_output(['git','-c','safe.directory='+clone,'-C',clone,'archive',REVISION,
                'src','config/rv64gc','config/shared','LICENSE'])
            with tarfile.open(fileobj=io.BytesIO(archive)) as packed:
                for member in packed.getmembers():
                    target=(vendor/member.name).resolve()
                    if not target.is_relative_to(vendor) or member.issym() or member.islnk():raise ValueError('Unsafe source archive')
                    if member.isfile():target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(packed.extractfile(member).read())
            before={p.relative_to(vendor).as_posix():sha(p) for p in vendor.rglob('*') if p.is_file()}
            address_map=audit_config(vendor/'config/rv64gc/config.vh',manifest)
            (out/'address-map.json').write_text(json.dumps(address_map,indent=2)+'\n')
            for name in ['wally/wallypipelinedsoc.sv','uncore/uncore.sv']:
                p=vendor/'src'/name;text=p.read_text();i=text.index('\n',text.index('module '))+1
                p.write_text(text[:i]+'  input logic AcceleratorIRQ, // HSD advanced PLIC source 20\n'+text[i:])
            replace(vendor/'src/wally/wallypipelinedsoc.sv','.HCLK, .HRESETn, .TIMECLK,','.HCLK, .HRESETn, .TIMECLK, .AcceleratorIRQ,')
            replace(vendor/'src/uncore/uncore.sv','.PWMIntr, .MExtInt,','.PWMIntr, .AcceleratorIRQ, .MExtInt,')
            p=vendor/'src/uncore/plic_apb.sv'
            replace(p,'UARTIntr,GPIOIntr, SPIIntr, SDCIntr,','UARTIntr,GPIOIntr, SPIIntr, SDCIntr, AcceleratorIRQ,')
            replace(p,'    requests = {P.PLIC_NUM_SRC{1\'b0}};',
                    '    requests = {P.PLIC_NUM_SRC{1\'b0}};\n    if(P.PLIC_NUM_SRC>=20) requests[20] = AcceleratorIRQ;')
            replace(vendor/'src/mmu/pmachecker.sv',
                    "  assign Cacheable = (PBMemoryType == 2'b00) ? CacheableRegion : 1'b0;",
                    "  // HSD Linux profile: line-aligned 16 KiB trusted DMA pool is uncached.\n"
                    "  wire LinuxDMAPool = PhysicalAddress >= 64'h88000000 && PhysicalAddress < 64'h88004000;\n"
                    f"  wire LinuxAcceleratorMMIO = PhysicalAddress >= 64'h{mmio:x} && PhysicalAddress < 64'h{mmio+32:x};\n"
                    "  assign Cacheable = (PBMemoryType == 2'b00) ? (CacheableRegion & ~LinuxDMAPool & ~LinuxAcceleratorMMIO) : 1'b0;")
            replace(vendor/'src/mmu/pmachecker.sv',
                    "  assign Idempotent = (PBMemoryType == 2'b00) ? IdempotentRegion : (PBMemoryType == 2'b01);",
                    "  assign Idempotent = ((PBMemoryType == 2'b00) ? IdempotentRegion : (PBMemoryType == 2'b01)) & ~LinuxAcceleratorMMIO;")
            replace(vendor/'src/mmu/pmachecker.sv',
                    "  assign AtomicAllowed = SelRegions[1] | SelRegions[3] | SelRegions[5];",
                    "  assign AtomicAllowed = (SelRegions[1] | SelRegions[3] | SelRegions[5]) & ~LinuxAcceleratorMMIO;")
            replace(vendor/'src/mmu/pmachecker.sv',
                    "  assign PMAAccessFault          = SelRegions[0] & AccessRWXC | AtomicAccessM & ~AtomicAllowed;",
                    "  assign PMAAccessFault          = (SelRegions[0] & AccessRWXC) | (AtomicAccessM & ~AtomicAllowed) | (LinuxAcceleratorMMIO & ExecuteAccessF);")
            after={p.relative_to(vendor).as_posix():sha(p) for p in vendor.rglob('*') if p.is_file()}
            record.update(revision=REVISION,original_sources=before,patched_sources=after,
                          scope='Actual Wally RV64 SoC + original accelerator RTL; D-cache enabled with an uncached PMA DMA pool; behavioral shared RAM; no FPGA claim',
                          local_sources={p.name:sha(p) for p in HERE.iterdir() if p.suffix in {'.py','.sv','.S','.dts','.json'}})
            if (bundle/'rootfs.cpio').stat().st_size>0x200000:raise ValueError('Initramfs exceeds advanced placement')
            dts=(HERE/'wally-linux.dts').read_text().replace('linux,initrd-end = <0 0x84200000>',
                'linux,initrd-end = <0 '+hex(0x84000000+(bundle/'rootfs.cpio').stat().st_size)+'>')
            (out/'wally-linux.dts').write_text(dts)
            command(['dtc','-I','dts','-O','dtb','-o',out/'wally-linux.dtb',out/'wally-linux.dts'],'dtc.txt')
            command(['clang','--target=riscv64','-march=rv64im_zicsr','-mabi=lp64','-nostdlib','-fuse-ld=lld',
                '-Wl,--no-relax','-Wl,-Ttext=0x1000',HERE/'boot-wally.S','-o',out/'boot.elf'],'boot-build.txt')
            elf=(out/'boot.elf').read_bytes()
            if elf[:6]!=b'\x7fELF\x02\x01':raise ValueError('Expected little-endian ELF64')
            shoff=struct.unpack_from('<Q',elf,40)[0]
            entsize,num,names=struct.unpack_from('<HHH',elf,58)
            sections=[struct.unpack_from('<IIQQQQIIQQ',elf,shoff+i*entsize) for i in range(num)]
            strings=elf[sections[names][4]:sections[names][4]+sections[names][5]]
            textsection=next(s for s in sections if strings[s[0]:].split(b'\0')[0]==b'.text')
            (out/'boot.bin').write_bytes(elf[textsection[4]:textsection[4]+textsection[5]])
            def hex_segment(stream,address,data):
                stream.write('@'+format(address//8,'x')+'\n')
                data+=bytes((-len(data))%8)
                stream.writelines(f'{word[0]:016x}\n' for word in struct.iter_unpack('<Q',data))
            with (out/'bootrom.hex').open('w') as stream:hex_segment(stream,0,(out/'boot.bin').read_bytes())
            smoke=out/'smoke';smoke.mkdir()
            command(['clang','--target=riscv64','-march=rv64im_zicsr','-mabi=lp64','-nostdlib','-fuse-ld=lld',
                '-Wl,--no-relax','-Wl,-Ttext=0x1000',HERE/'boot-smoke.S','-o',smoke/'boot.elf'],'smoke-build.txt')
            smoke_elf=(smoke/'boot.elf').read_bytes()
            smoke_shoff=struct.unpack_from('<Q',smoke_elf,40)[0]
            smoke_entsize,smoke_num,smoke_names=struct.unpack_from('<HHH',smoke_elf,58)
            smoke_sections=[struct.unpack_from('<IIQQQQIIQQ',smoke_elf,smoke_shoff+i*smoke_entsize) for i in range(smoke_num)]
            name_section=smoke_sections[smoke_names]
            smoke_strings=smoke_elf[name_section[4]:name_section[4]+name_section[5]]
            smoke_text=next(s for s in smoke_sections if smoke_strings[s[0]:].split(b'\0')[0]==b'.text')
            with (smoke/'bootrom.hex').open('w') as stream:
                hex_segment(stream,0,smoke_elf[smoke_text[4]:smoke_text[4]+smoke_text[5]])
            (smoke/'ram.hex').write_text('@0\n0000000000000000\n')
            with (out/'ram.hex').open('w') as stream:
                for name,addr in [('fw_dynamic.bin',0x80000000),('Image',0x80200000),('rootfs.cpio',0x84000000)]:
                    hex_segment(stream,addr-0x80000000,(bundle/name).read_bytes())
                hex_segment(stream,0x87000000-0x80000000,(out/'wally-linux.dtb').read_bytes())
            record['bundle']={p.name:sha(p) for p in bundle.iterdir() if p.is_file()}
            record['prepared_artifacts']={n:sha(out/n) for n in ['address-map.json','ram.hex','bootrom.hex','wally-linux.dtb','smoke/bootrom.hex','smoke/ram.hex']}
            record['stages']['prepare']='pass';record['status']='prepared_not_booted'
        elif args.stage=='compile':
            if record['stages'].get('prepare')!='pass':raise ValueError('Run prepare first')
            vendor=out/'vendor';package=vendor/'src/cvw.sv'
            sources=[package,*[p for p in sorted((vendor/'src').rglob('*.sv')) if p!=package]]
            rtl=ROOT/'labs/10-dotproduct/rtl'
            record['compiled_sources']={str(p.relative_to(ROOT)):sha(p) for p in [*sources,*sorted(rtl.glob('*.sv')),HERE/'tb_wally_linux.sv',HERE/'wally-dpi.cpp']}
            command(['verilator','--binary','--timing','-j','2','-CFLAGS','-O3','-Wno-fatal','--top-module','tb_wally_linux',
                '--Mdir',out/'obj_dir','-I'+str(vendor/'config/rv64gc'),'-I'+str(vendor/'config/shared'),
                *sources,*sorted(rtl.glob('*.sv')),HERE/'tb_wally_linux.sv',HERE/'wally-dpi.cpp'],'compile.txt',1200)
            record['executable_sha256']=sha(out/'obj_dir/Vtb_wally_linux')
            record['stages']['compile']='pass';record['status']='compiled_not_booted'
        else:
            if record['stages'].get('compile')!='pass':raise ValueError('Compile the real RTL first')
            if sha(out/'obj_dir/Vtb_wally_linux')!=record['executable_sha256']:raise ValueError('Changed executable')
            for name,digest in record['compiled_sources'].items():
                if sha(ROOT/name)!=digest:raise ValueError('Changed compiled RTL: '+name)
            for name,digest in record['prepared_artifacts'].items():
                if sha(out/name)!=digest:raise ValueError('Changed boot artifact: '+name)
            record['stages']['run']='running';save()
            command(['stdbuf','-oL',out/'obj_dir/Vtb_wally_linux','+MMIO_SMOKE','+MAX_CYCLES=200000'],
                    'smoke.txt',120,workdir=out/'smoke')
            if 'WALLY_MMIO_SMOKE_PASS' not in (out/'smoke.txt').read_text():raise RuntimeError('Missing CPU/MMIO/DMA preflight')
            record['stages']['smoke']='pass';save()
            command(['stdbuf','-oL',out/'obj_dir/Vtb_wally_linux','+MAX_CYCLES='+str(args.cycles)],'uart.txt',args.seconds)
            text=(out/'uart.txt').read_text()
            for marker in ['OpenSBI','Linux version 6.12','HSD_DRIVER_READY','HSD_LINUX_ACCEL_PASS','WALLY_LINUX_ACCEL_PASS']:
                if marker not in text:raise RuntimeError('Missing actual RTL checkpoint: '+marker)
            if 'HSD_LINUX_ACCEL_FAIL' in text or 'Kernel panic' in text:raise RuntimeError('Failed RTL Linux run')
            record['stages']['run']='pass';record['status']='pass'
        save();print('Wally advanced',args.stage,record['status'])
    except (OSError,ValueError,RuntimeError,subprocess.TimeoutExpired,subprocess.CalledProcessError) as error:
        record['stages'][args.stage]='fail'
        record['status']='fail';record['error']=str(error);save();raise

if __name__=='__main__':main()
