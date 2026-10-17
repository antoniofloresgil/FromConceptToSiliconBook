"""Independent integer oracle: low 16 signed bits, arbitrary-precision sum."""
import json
from pathlib import Path
import random
import sys

destination = Path(sys.argv[1])
seed = int(sys.argv[2])
rng = random.Random(seed)
a = [0xdead8000, 0xbeef7fff, 0x1234ffff, 0xaaaa0000]
b = [0xffff7fff, 0x11117fff, 0x55550001, 0xbbbbffff]
a += [rng.getrandbits(32) for _ in range(252)]
b += [rng.getrandbits(32) for _ in range(252)]
def signed(word):
    value = word & 0xffff
    return value - 65536 if value >= 32768 else value
expected = [sum(signed(x)*signed(y) for x,y in zip(a[:n],b[:n])) & ((1<<64)-1)
            for n in range(1,257)]
for name, words, width in [('a',a,8),('b',b,8),('expected',expected,16)]:
    (destination / (name+'.hex')).write_text(''.join(f'{v:0{width}x}\n' for v in words))
square=[sum(signed(x)**2 for x in a[:n]) for n in range(1,257)]
(destination/'square.hex').write_text(''.join(f'{v:016x}\n' for v in square))
(destination/'vectors.json').write_text(json.dumps({'seed':seed,'a':a,'b':b,'expected':expected},indent=2)+'\n')
