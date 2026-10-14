"""Check byte masks, dirty eviction and flush against a flat memory oracle."""
import argparse
import random
from cache_model import CacheModel

p=argparse.ArgumentParser();p.add_argument("--seed",type=int,default=2026);args=p.parse_args()
rng=random.Random(args.seed)
for sets,ways in [(4,1),(2,2),(4,4)]:
    cache=CacheModel(sets,ways);oracle={}
    for _ in range(3000):
        address=rng.randrange(256)*4
        old=oracle.get(address,0)
        if rng.randrange(2):
            value=rng.getrandbits(32);mask=rng.randrange(16)
            expected=bytearray(old.to_bytes(4,"little"));incoming=value.to_bytes(4,"little")
            for byte in range(4):
                if mask & (1<<byte):expected[byte]=incoming[byte]
            oracle[address]=int.from_bytes(expected,"little")
            actual=cache.access(address,value,mask)
        else: actual=cache.access(address)
        assert actual==oracle.get(address,0),(sets,ways,address,actual)
    cache.clean();cache.invalidate()
    for address,value in oracle.items():assert cache.access(address)==value
    for bad in (-4,1,2**32):
        try:cache.access(bad)
        except ValueError:pass
        else:raise AssertionError("invalid address accepted")
    dirty=CacheModel();dirty.access(0,1)
    try:dirty.invalidate()
    except RuntimeError:pass
    else:raise AssertionError("dirty invalidation allowed")
assert CacheModel(4,1).line_bytes==16
print(f"PASS cache model: 9000 random accesses seed={args.seed}, clean/refill and errors")
