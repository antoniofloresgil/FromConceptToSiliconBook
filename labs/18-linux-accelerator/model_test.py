"""Exercise real QEMU MMIO/DMA model with qtest, independently of Linux driver."""
import argparse
import json
from pathlib import Path
import socket
import subprocess
import time
import tempfile

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path)
    out=parser.parse_args().output;out.mkdir(parents=True,exist_ok=True)
    temporary=tempfile.TemporaryDirectory(prefix='hsd-qtest-')
    sockpath=Path(temporary.name)/'qtest.sock'
    argv=['qemu-system-riscv64','-machine','virt','-m','256M','-smp','1','-display','none','-nodefaults',
          '-bios','none','-accel','qtest','-qtest','unix:'+str(sockpath)+',server=on,wait=off','-qtest-log','/dev/null']
    transcript=[];passed=[]
    with (out/'model.txt').open('w') as log:
        process=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT)
        try:
            for _ in range(100):
                if sockpath.exists():break
                if process.poll() is not None:raise RuntimeError('QEMU qtest start failed')
                time.sleep(.05)
            s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);s.settimeout(5);s.connect(str(sockpath));f=s.makefile('rwb',buffering=0)
            def command(text):
                f.write((text+'\n').encode());reply=f.readline().decode().strip();transcript.append([text,reply])
                if not reply.startswith('OK'):raise RuntimeError('qtest: '+text+' -> '+reply)
                return reply
            def write(addr,value):command(f'writel {addr:#x} {value:#x}')
            def read(addr):return int(command(f'readl {addr:#x}').split()[1],16)
            profile=json.loads((Path(__file__).resolve().parent/'manifest.json').read_text())['profile'];base=int(profile['MMIO_BASE'],0);pool=int(profile['DMA_BASE'],0)
            def descriptor(a=pool,b=pool+1024,dst=pool+2048,n=1):
                for offset,value in [(8,a),(12,b),(16,dst),(20,n)]:write(base+offset,value)
            write(pool,0xdead8000);write(pool+1024,0xbeef7fff)
            descriptor();write(base,3)
            if read(base+4)!=1:raise AssertionError('Asynchronous busy missing')
            write(base+20,256) # Busy descriptor writes are ignored by the model.
            command('clock_step 10001')
            if read(base+4)!=10 or read(pool+2048)!=0xc0008000 or read(pool+2052)!=0xffffffff:raise AssertionError('Signed result/completion')
            write(base+28,1)
            if read(base+4)!=2:raise AssertionError('IRQ acknowledgement')
            passed.append('signed result, ignored upper bits, asynchronous completion, busy descriptor and IRQ acknowledgement')
            for name,kwargs in [('zero',{'n':0}),('excess',{'n':257}),('unaligned',{'a':pool+1}),
                                ('out-of-window',{'a':pool-4}),('overlap',{'dst':pool}),
                                ('wrap',{'a':0xfffffffc,'n':2})]:
                descriptor(**kwargs);write(base,3)
                if read(base+4)!=12 or read(base+24)!=1:raise AssertionError(name)
                write(base+28,1);passed.append(name)
            f.close();s.close()
        finally:
            process.terminate();process.wait(timeout=5);temporary.cleanup()
    text=(out/'model.txt').read_text()
    if text.count('error=1 reads=0 writes=0')!=6:raise AssertionError('Invalid commands performed DMA or missing negative controls')
    (out/'report.json').write_text(json.dumps({'status':'pass','argv':argv,'checks':passed,'transcript':transcript},indent=2)+'\n')
    print('PASS QEMU model: signed DMA, completion/ACK, busy stability and six rejected descriptors with zero DMA')

if __name__=='__main__':main()
