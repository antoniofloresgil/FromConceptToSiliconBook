#!/usr/bin/env python3
"""Generate the subject index: for each curated term, the numbered sections where it is discussed.

Entries live in subject-index.json. A section counts as a location when the term appears in its heading, in bold,
or at least twice in its own text; the best sections (at most `limit`) are listed in book order. The page shows the
section number and, in print, its page. Standard library only; see test_subject_index.py.
"""
import argparse
import json
from pathlib import Path
import re
import sys

import sections as S

ROOT = S.ROOT
DATA = Path(__file__).with_name('subject-index.json')
OUTPUT = ROOT / 'subject-index.qmd'
DEFAULT_LIMIT = 8


def load():
    return json.loads(DATA.read_text(encoding='utf-8'))


def clean_text(lines):
    """Prose of a section: no fenced code, comments, link targets, attribute blocks or table rules."""
    out, fenced = [], False
    for line in lines:
        if line.startswith('```'):
            fenced = not fenced
            continue
        if fenced or line.startswith('![') or re.match(r'^\|[\s:|-]+\|\s*$', line) or line.startswith('<!--'):
            continue
        line = re.sub(r'\]\([^)]*\)', ']', line)
        line = re.sub(r'\{[#.][^}]*\}', '', line)
        out.append(line)
    return '\n'.join(out)


def compile_entry(entry):
    exact = entry.get('exact', False)
    flags = 0 if exact else re.I
    words = '|'.join(re.escape(m).replace(r'\ ', r'[\s-]+') for m in entry.get('match', [entry['term']]))
    pattern = re.compile(r'(?<![\w])(?:' + words + r')(?:s|es)?(?![\w])', flags)
    removed = [re.compile(re.escape(x), flags) for x in entry.get('not', [])]
    return pattern, removed


def score(pattern, removed, section_title, text):
    for rx in removed:
        text = rx.sub(' ', text)
        section_title = rx.sub(' ', section_title)
    count = len(pattern.findall(text))
    in_heading = bool(pattern.search(section_title))
    bold = bool(re.search(r'\*\*[^*\n]*' + pattern.pattern + r'[^*\n]*\*\*', text, pattern.flags))
    return count + (5 if in_heading else 0) + (3 if bold else 0), count, in_heading, bold


def collect():
    book = []
    for path, label in S.book_files():
        if label is None:
            continue
        lines, found = S.sections(path, label)
        for i, section in enumerate(found):
            if not section['number'] or section['level'] < 2:
                continue
            # the section's own text, up to the next heading of any level
            body = clean_text(lines[section['line'] + 1:section['end']])
            book.append(dict(section, text=body, order=len(book), chapter=found[0]['title']))
    return book


def unique_ids(book):
    seen = {}
    for section in book:
        seen.setdefault(section['id'], []).append(section)
    return {k for k, v in seen.items() if len(v) == 1}


def locate(entries, book, unique):
    result = {}
    for entry in entries:
        if 'see' in entry:
            continue
        pattern, removed = compile_entry(entry)
        scored = []
        for section in book:
            value, count, in_heading, bold = score(pattern, removed, section['title'], section['text'])
            if count and pattern.search(section.get('chapter', '')):
                value += 2  # a chapter devoted to the term outranks incidental mentions elsewhere
            if section['id'] in unique and (count >= entry.get('min', 2) or in_heading or bold):
                scored.append((value, section))
        scored.sort(key=lambda x: (-x[0], x[1]['order']))
        chosen = scored[:entry.get('limit', DEFAULT_LIMIT)]
        result[entry['term']] = sorted((s for _, s in chosen), key=lambda s: s['order'])
    return result


def link(section, unique):
    rel = section['file'].relative_to(ROOT).as_posix()
    text = '[§' + section['number'] + '](' + rel + '#' + section['id'] + ')'
    if section['id'] in unique:
        text += ' `\\textnormal{(p.~\\pageref{' + section['id'] + '})}`{=latex}'
    return text


def render(data):
    entries = sorted(data['entries'], key=lambda e: e['term'].casefold())
    book = collect()
    unique = unique_ids(book)
    found = locate(entries, book, unique)
    names = {e['term'] for e in entries}
    lines = ['# Subject Index {.unnumbered}', '', data['intro'], '']
    previous, problems = '', []
    for entry in entries:
        letter = entry['term'][0].upper()
        if letter != previous:
            lines += ['', '## ' + letter + ' {.reference-entry}', '']
            previous = letter
        name = '**' + entry['term'] + '**'
        if 'glossary' in entry:
            name = '**[' + entry['term'] + '](glossary.qmd#gloss-' + entry['glossary'] + ')**'
        if 'see' in entry:
            if entry['see'] not in names:
                problems.append('see target missing for ' + entry['term'] + ': ' + entry['see'])
            lines.append('- ' + name + ' — *see* ' + entry['see'] + '.')
            continue
        places = found[entry['term']]
        if not places:
            problems.append('no location found for ' + entry['term'])
            continue
        lines.append('- ' + name + ' — ' + '; '.join(link(s, unique) for s in places) + '.')
    return '\n'.join(lines) + '\n', problems, found, unique


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--report', action='store_true', help='print the locations found for each entry')
    args = parser.parse_args()
    data = load()
    text, problems, found, unique = render(data)
    if args.report:
        for term, places in found.items():
            print(f'{term:30s} {len(places):2d}  ' + ' | '.join(s['number'] + ' ' + s['title'][:34] for s in places))
    if problems:
        print('\n'.join(problems))
        sys.exit(f'{len(problems)} index problem(s)')
    if args.write:
        OUTPUT.write_text(text, encoding='utf-8', newline='')
    elif not OUTPUT.is_file() or OUTPUT.read_text(encoding='utf-8') != text:
        sys.exit('Stale subject index; run python tools/book/subject_index.py --write')
    print(f'PASS subject index: {len(data["entries"])} entries')


if __name__ == '__main__':
    main()
