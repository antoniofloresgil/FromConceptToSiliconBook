"""Compare the installed lab tools with labs/validated-environment.json.

Run it inside the teaching image. A host with other versions fails by design and
a missing tool is a failure, never a skip: a PASS says the reported versions equal
the validated ones, not that any lab ran.
"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'labs'))
import run  # noqa: E402

RECORD = ROOT / 'labs/validated-environment.json'


def version(entry):
    return entry.get('version') if isinstance(entry, dict) else entry


def compare(observed, expected):
    """Return one message per tool whose version differs from the validated record."""
    problems = []
    for name, record in expected.items():
        want, have = version(record), version(observed.get(name))
        if have is None: problems.append(f'{name}: not installed, validated {want}')
        elif have != want: problems.append(f'{name}: installed {have}, validated {want}')
    return problems


def main():
    expected = json.loads(RECORD.read_text(encoding='utf-8'))['tools']
    problems = compare(run.tool_info(), expected)
    for problem in problems: print('DIFFERS ' + problem)
    if problems:
        print('The installed tools are not the validated baseline. Use the pinned teaching image, or '
              'follow docs/versioning.md to adopt the new versions.')
        return 1
    print(f'PASS environment: {len(expected)} tool versions equal labs/validated-environment.json; '
          'no lab was run')
    return 0


if __name__ == '__main__':
    sys.exit(main())
