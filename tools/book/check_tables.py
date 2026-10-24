#!/usr/bin/env python3
"""Check that every pipe table of the book sources has a caption with a unique #tbl- identifier.

A table needs the caption line `: Caption text {#tbl-identifier}` after one blank line, so that it is announced by a
screen reader, numbered, and citable with @tbl-identifier. Every @tbl- reference must resolve. Standard library only.
"""
import argparse
import glob
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
CAPTION = re.compile(r'^: (?P<text>.+?) \{#(?P<id>tbl-[a-z0-9]+(?:-[a-z0-9]+)*)(?: [^}]*)?\}\s*$')
SEPARATOR = re.compile(r'^\|[\s:|-]+\|\s*$')


def sources():
    names = sorted(glob.glob(str(ROOT / 'chapters/**/*.qmd'), recursive=True)) + sorted(glob.glob(str(ROOT / 'appendices/*.qmd')))
    return [Path(n) for n in names] + [ROOT / 'intro.qmd']


def tables(text):
    """(first line, line after the table) of each pipe table outside fenced code."""
    lines, fenced, found, i = text.replace('\r\n', '\n').split('\n'), False, [], 0
    while i < len(lines):
        if lines[i].startswith('```'):
            fenced = not fenced
        if not fenced and lines[i].startswith('|') and i + 1 < len(lines) and SEPARATOR.match(lines[i + 1]):
            j = i + 2
            while j < len(lines) and lines[j].startswith('|'):
                j += 1
            found.append((i, j))
            i = j
            continue
        i += 1
    return lines, found


def check(paths):
    problems, ids, refs = [], {}, []
    for path in paths:
        text = path.read_text(encoding='utf-8')
        lines, found = tables(text)
        name = path.relative_to(ROOT).as_posix()
        for start, end in found:
            caption = CAPTION.match(lines[end + 1]) if end + 1 < len(lines) and lines[end] == '' else None
            if not caption:
                problems.append(f'{name}:{start + 1}: pipe table without a caption line ": Caption {{#tbl-...}}"')
                continue
            if caption['id'] in ids:
                problems.append(f'{name}:{end + 2}: duplicate identifier {caption["id"]} (also {ids[caption["id"]]})')
            ids[caption['id']] = f'{name}:{end + 2}'
        refs += [(name, m[1]) for m in re.finditer(r'@(tbl-[a-z0-9]+(?:-[a-z0-9]+)*)', text)]
    for name, ref in refs:
        if ref not in ids:
            problems.append(f'{name}: reference @{ref} has no table')
    return problems, len(ids), len(refs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='accepted for symmetry with the other generators')
    parser.parse_args()
    problems, count, refs = check(sources())
    for problem in problems:
        print(problem)
    if problems:
        sys.exit(f'{len(problems)} table problem(s)')
    print(f'PASS tables: {count} captioned with unique identifiers; {refs} references resolve')


if __name__ == '__main__':
    main()
