#!/usr/bin/env python3
"""Generate the original conceptual SVGs added to the technical chapters, in the book's common style.

The drawings live in the concepts_*.py modules and reuse `Drawing` from architecture.py unchanged. --check compares
the outputs without rewriting them; --list prints the figure names.
"""
import argparse
from pathlib import Path

from architecture import outputs
import concepts_advanced
import concepts_cores
import concepts_exploration
import concepts_foundations
import concepts_implementation
import concepts_language
import concepts_security
import concepts_soc
import concepts_verification

FIG = Path(__file__).resolve().parents[2] / 'figures'
MODULES = [concepts_language, concepts_foundations, concepts_cores, concepts_verification, concepts_soc, concepts_implementation,
           concepts_advanced, concepts_security, concepts_exploration]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--list', action='store_true')
    args = parser.parse_args()
    for module in MODULES:
        for draw in module.FIGURES:
            draw()
    if args.list:
        print('\n'.join(sorted(Path(name).stem for name in outputs)))
        return
    for name, data in outputs.items():
        target = FIG / name
        if args.check:
            if not target.is_file() or target.read_bytes() != data:
                raise ValueError('Stale figure: ' + str(target))
        else:
            target.write_bytes(data)
    print(('CHECKED' if args.check else 'GENERATED'), len(outputs), 'concept SVG figures')


if __name__ == '__main__':
    main()
