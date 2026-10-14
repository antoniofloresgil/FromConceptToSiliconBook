"""Independent RV32 division oracle and reproducible C input/answer arrays."""
import json
from pathlib import Path
import random

def signed(x):
    return x-(1<<32) if x & (1<<31) else x

def answers(a,b):
    x,y=signed(a),signed(b)
    if y==0: q,r=-1,x
    elif x==-(1<<31) and y==-1: q,r=x,0
    else:
        q=abs(x)//abs(y)
        if (x<0)!=(y<0): q=-q
        r=x-q*y
    uq,ur=(0xffffffff,a) if b==0 else (a//b,a%b)
    return [v & 0xffffffff for v in (q,r,uq,ur)]

def generate(destination,seed=2026):
    rng=random.Random(seed)
    pairs=[(0,0),(1,0),(0x80000000,0xffffffff),(0x80000000,1),
           (0xffffffff,2),(7,3),(0xfffffff9,3),(7,0xfffffffd)]
    pairs += [(rng.getrandbits(32),rng.getrandbits(32)) for _ in range(56)]
    expected=[answers(a,b) for a,b in pairs]
    checksum=2166136261
    for row in expected:
        for value in row: checksum=((checksum^value)*16777619)&0xffffffff
    def array(rows):
        return ',\n'.join('{'+','.join(f'0x{x:08x}u' for x in row)+'}' for row in rows)
    header=('#define PAIRS 64\n'
            f'static const uint32_t operands[PAIRS][2]={{\n{array(pairs)}\n}};\n'
            f'static const uint32_t expected[PAIRS][4]={{\n{array(expected)}\n}};\n'
            f'#define EXPECTED_CHECKSUM 0x{checksum:08x}u\n')
    destination.mkdir(parents=True,exist_ok=True)
    (destination/'vectors.h').write_text(header,encoding='utf-8')
    record={'seed':seed,'pairs':pairs,'expected':expected,'checksum':checksum}
    (destination/'vectors.json').write_text(json.dumps(record,indent=2)+'\n')
    return record
