"""Keep repeated tool and image pins equal to tools/environments/environments.json.

Python 3.10+, standard library only. `check` reports pins that differ from the
manifest; `write` rewrites the editable copies. Copies inside recorded evidence
are counted but never rewritten: they belong to the run that produced them. A
rule with `"mode": "prose"` covers sentences that name a pin: `check` fails on a
stale mention, `write` leaves it for a human to reread against the new baseline.
A rule's `advisory` globs name files (the bibliography) whose mentions cite a
specific version of upstream documentation: they are listed, never rewritten,
and do not fail `check`.
"""
import argparse
from fnmatch import fnmatch
import json
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def require(value, message):
    if not value: raise ValueError(message)


def load(manifest):
    data = json.loads(manifest.read_text(encoding='utf-8'))
    require(data.get('schema') == 1, 'Unsupported environments manifest schema')
    require(data.get('values') and data.get('rules'), 'Manifest needs values and rules')
    ids = [rule['id'] for rule in data['rules']]
    require(len(ids) == len(set(ids)), 'Duplicate rule id')
    return data


def tracked(root):
    names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode().split('\0')
    return [name for name in names if name]


def matches(name, patterns):
    return any(fnmatch(name, pattern) for pattern in patterns)


FILTERS = {'nodash': lambda value: value.replace('-', '')}


def expand(template, values):
    def substitute(match):
        key, name = match.group(1), match.group(2)
        require(key in values, 'Unknown value in replacement: ' + match.group(0))
        require(name in FILTERS or name is None, 'Unknown filter in replacement: ' + match.group(0))
        return FILTERS[name](values[key]) if name else values[key]
    return re.sub(r'\{(\w+)(?::(\w+))?\}', substitute, template)


def classify(name, rule, scope):
    """'edit', 'recorded', 'advisory' or None for a tracked path under one rule."""
    if matches(name, scope['exclude']): return None
    if matches(name, rule.get('advisory', [])): return 'advisory'
    if 'files' in rule and not matches(name, rule['files']): return None
    return 'recorded' if matches(name, scope['evidence']) else 'edit'


def rewrite(text, rule, values):
    pattern = re.compile(rule['pattern'])
    replacement = expand(rule['replacement'], values)
    return pattern.sub(lambda match: match.expand(replacement), text)


def scan(root, manifest):
    """Return {rule id: {'edit': [(path, copies, stale)], 'recorded': [...], 'advisory': [...]}}."""
    values, scope = manifest['values'], manifest['scope']
    result = {rule['id']: {'edit': [], 'recorded': [], 'advisory': []} for rule in manifest['rules']}
    for name in tracked(root):
        path = root / name
        if not path.is_file(): continue
        try: text = path.read_bytes().decode('utf-8')
        except UnicodeDecodeError: continue
        for rule in manifest['rules']:
            kind = classify(name, rule, scope)
            if not kind: continue
            found = list(re.finditer(rule['pattern'], text))
            if not found: continue
            updated = rewrite(text, rule, values)
            require(rewrite(updated, rule, values) == updated,
                    f"Rule {rule['id']} is not idempotent")
            replacement = expand(rule['replacement'], values)
            stale = sum(1 for match in found if match.expand(replacement) != match.group(0))
            result[rule['id']][kind].append((name, len(found), stale))
    return result


def prose_rules(manifest):
    return {rule['id'] for rule in manifest['rules'] if rule.get('mode') == 'prose'}


def report(result, prose=frozenset()):
    failures = 0
    for rule_id, groups in result.items():
        editable, recorded = groups['edit'], groups['recorded']
        copies = sum(item[1] for item in editable)
        stale = [item for item in editable if item[2]]
        print(f"{rule_id}: {copies} editable copies in {len(editable)} files, "
              f"{len(recorded)} recorded evidence files" +
              (f", {len(groups['advisory'])} advisory files" if groups['advisory'] else ''))
        if not copies:
            failures += 1
            print('  rule matches nothing: fix the pattern or its file list')
        for name, _, count in stale:
            failures += 1
            print(f'  differs from the manifest: {name}' +
                  (' (reread the sentence against the new baseline)' if rule_id in prose else ''))
        for name, _, count in groups['advisory']:
            if count: print(f'  note, cites another version: {name} (not a failure)')
    return failures


def write(root, manifest, dry_run):
    changed = 0
    for rule in manifest['rules']:
        for name in tracked(root):
            path = root / name
            if rule.get('mode') == 'prose': continue
            if not path.is_file() or classify(name, rule, manifest['scope']) != 'edit': continue
            try: text = path.read_bytes().decode('utf-8')
            except UnicodeDecodeError: continue
            updated = rewrite(text, rule, manifest['values'])
            if updated == text: continue
            changed += 1
            print(('would rewrite ' if dry_run else 'rewrote ') + f"{name} ({rule['id']})")
            if not dry_run: path.write_bytes(updated.encode('utf-8'))
    return changed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('command', choices=['check', 'write'])
    parser.add_argument('--manifest', type=Path, default=HERE / 'environments.json')
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--dry-run', action='store_true', help='with write: list files only')
    args = parser.parse_args(argv)
    manifest = load(args.manifest)
    if args.command == 'check':
        failures = report(scan(args.root, manifest), prose_rules(manifest))
        print('FAIL' if failures else 'OK')
        return 1 if failures else 0
    changed = write(args.root, manifest, args.dry_run)
    print(f'{changed} files' + (' would change' if args.dry_run else ' changed'))
    stale = scan(args.root, manifest)
    for rule_id in sorted(prose_rules(manifest)):
        for name, _, count in stale[rule_id]['edit']:
            if count: print(f'review by hand: {name} ({rule_id})')
    for rule_id, groups in stale.items():
        for name, _, count in groups['advisory']:
            if count: print(f'review if it still cites the baseline: {name} ({rule_id})')
    print('Recorded evidence was not touched; rerun the affected labs (docs/versioning.md, step 3).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
