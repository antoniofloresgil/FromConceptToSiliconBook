"""Small program-specific RV32I oracle, not a replacement for Spike or Sail."""
import struct
import sys

blob=open(sys.argv[1],"rb").read()
assert blob[:6]==b"\x7fELF\x01\x01", "32-bit little-endian ELF required"
header=struct.unpack_from("<16sHHIIIIIHHHHHH",blob)
assert header[2]==243, "RISC-V machine type required"
pc=header[4];phoff,phsize,phnum=header[5],header[9],header[10]
memory={}
for index in range(phnum):
    kind,offset,address,_,filesz,memsz,_,_=struct.unpack_from("<IIIIIIII",blob,phoff+index*phsize)
    if kind==1:
        for n in range(memsz):memory[address+n]=blob[offset+n] if n<filesz else 0

def read(address,count):
    return sum(memory[address+n]<<(8*n) for n in range(count))

def signed(value,width):
    return value-(1<<width) if value&(1<<(width-1)) else value

registers=[0]*32
for steps in range(1000):
    ins=read(pc,4)
    op,rd,f3,r1,r2=ins&127,(ins>>7)&31,(ins>>12)&7,(ins>>15)&31,(ins>>20)&31
    next_pc=(pc+4)&0xffffffff;result=None;imm=signed(ins>>20,12)
    if op==0x17:result=pc+(ins&0xfffff000)
    elif op==0x13 and f3==0:result=registers[r1]+imm
    elif op==0x33 and f3==0 and ins>>25==0:result=registers[r1]+registers[r2]
    elif op==0x03:
        address=(registers[r1]+imm)&0xffffffff
        if f3==2:result=read(address,4)
        elif f3==0:result=signed(read(address,1),8)
        elif f3==4:result=read(address,1)
        else:raise AssertionError("unsupported load in oracle")
    elif op==0x23 and f3==2:
        displacement=signed(((ins>>25)<<5)|((ins>>7)&31),12)
        address=(registers[r1]+displacement)&0xffffffff
        for n in range(4):memory[address+n]=(registers[r2]>>(8*n))&255
    elif op==0x63 and f3==1:
        displacement=signed(((ins>>31)<<12)|(((ins>>7)&1)<<11)|(((ins>>25)&63)<<5)|(((ins>>8)&15)<<1),13)
        if registers[r1]!=registers[r2]:next_pc=(pc+displacement)&0xffffffff
    elif op==0x6f:
        displacement=signed(((ins>>31)<<20)|(((ins>>12)&255)<<12)|(((ins>>20)&1)<<11)|(((ins>>21)&1023)<<1),21)
        if displacement==0 and rd==0:break
        result=next_pc;next_pc=(pc+displacement)&0xffffffff
    else:raise AssertionError(f"unsupported instruction {ins:08x}")
    if result is not None and rd:registers[rd]=result&0xffffffff
    assert registers[0]==0
    pc=next_pc
else:raise AssertionError("completion timeout")
signature=[read(0x80001100+4*n,4) for n in range(3)]
assert signature==[16,0xfffffffd,0xfd],signature
print(f"PASS RV32I demo steps={steps} signature={[hex(x) for x in signature]}")
