"""Synthetic Prime+Probe costs using the existing teaching cache model."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('teaching_cache', ROOT / 'labs/02-memory/cache_model.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def observe(secret, uniform=False):
    cache = module.CacheModel(sets=16, ways=1, line_bytes=64)
    for index in range(16):
        cache.access(index * 64)  # Attacker-owned lines.
    selected = range(16) if uniform else [secret]
    for index in selected:
        cache.access((16 + index) * 64)  # Disjoint victim addresses, same sets.
    costs = []
    for index in range(16):
        before = cache.misses
        cache.access(index * 64)
        costs.append(12 if cache.misses != before else 1)
    return costs


def experiment():
    vulnerable = [observe(secret) for secret in range(16)]
    uniform = [observe(secret, uniform=True) for secret in range(16)]
    assert all(trace.index(12) == secret for secret, trace in enumerate(vulnerable))
    assert len({tuple(trace) for trace in uniform}) == 1
    return {'scope': 'Deterministic teaching cache; costs assigned 1/12, not Wally cycles',
            'vulnerable_observations': vulnerable, 'uniform_observations': uniform,
            'recovered_synthetic_secrets': list(range(16)),
            'claim': 'Uniform addresses remove this modelled observation only; no physical security proof'}
