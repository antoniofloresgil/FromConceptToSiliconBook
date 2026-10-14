"""Independent finite-width integer expectations and inverse immediate encoding."""
import argparse
from pathlib import Path
import random

p = argparse.ArgumentParser()
p.add_argument("destination", type=Path)
p.add_argument("--seed", type=int, default=2026)
args = p.parse_args()
rng = random.Random(args.seed)
mask = (1 << 32) - 1
signed = lambda x: x if x < (1 << 31) else x - (1 << 32)
alu = []
boundaries = [0, 1, mask, 0x80000000, 0x7fffffff, 31, 32, 63]
for op in range(16):
    pairs = [(a,b) for a in boundaries for b in boundaries]
    pairs += [(rng.getrandbits(32), rng.getrandbits(32)) for _ in range(200)]
    for a,b in pairs:
        results = [a+b, a-b, a&b, a|b, a^b, a*(2**(b%32)), a//(2**(b%32)),
                   signed(a)//(2**(b%32)), int(signed(a)<signed(b)), int(a<b)]
        expected = (results[op] & mask) if op < 10 else 0
        alu.append(((((op << 32) | a) << 32 | b) << 33) | (expected << 1) | int(op < 10))

immediates = []
for kind in range(5):
    if kind in (0,1): values = list(range(-2048, 2048))
    elif kind == 2: values = list(range(-4096,4096,2))
    elif kind == 3: values = [0,0x80000000,0xfffff000] + [rng.getrandbits(20)<<12 for _ in range(500)]
    else: values = [-1048576,1048574,-4,2,4,0]+[rng.randrange(-524288,524288)*2 for _ in range(500)]
    for value in values:
        v = value & mask
        if kind == 0: ins = (v & 0xfff) << 20
        elif kind == 1: ins = ((v >> 5 & 127) << 25) | ((v & 31) << 7)
        elif kind == 2: ins = ((v>>12&1)<<31)|((v>>11&1)<<7)|((v>>5&63)<<25)|((v>>1&15)<<8)
        elif kind == 3: ins = v
        else: ins = ((v>>20&1)<<31)|((v>>12&255)<<12)|((v>>11&1)<<20)|((v>>1&1023)<<21)
        immediates.append((kind << 65) | (ins << 33) | (v << 1) | 1)
for kind in (5,6,7): immediates.append((kind << 65) | (rng.getrandbits(32)<<33))
for name, rows in [("alu-vectors.hex",alu),("immediate-vectors.hex",immediates)]:
    (args.destination/name).write_text(str(len(rows))+"\n"+"".join(f"{row:x}\n" for row in rows))
print(f"PASS generated seed={args.seed} ALU={len(alu)} immediates={len(immediates)}")
