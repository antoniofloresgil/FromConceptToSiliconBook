#!/usr/bin/env python3
"""Section structure of the book sources: numbers and identifiers as Quarto renders them (standard library only).

The subject index points at sections by the number and the identifier that the rendered book gives them. This
module reproduces both from the QMD sources; test_sections.py compares them with a rendered book when one exists.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
NUMBER_DEPTH = 4
LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


def book_files():
    """(path, label) in book order: chapter number or appendix letter; front and back matter have no label."""
    config = (ROOT / '_quarto.yml').read_text(encoding='utf-8')
    body = config.split('chapters:', 1)[1]
    main, _, appendices = body.partition('appendices:')
    files, number = [], 0
    for rel in re.findall(r'^\s*- ((?:[\w./-]+)\.qmd)\s*$', main, re.M):
        if rel.startswith('chapters/'):
            number += 1
            files.append((ROOT / rel, str(number)))
        else:
            files.append((ROOT / rel, None))
    for i, rel in enumerate(re.findall(r'^\s*- ((?:[\w./-]+)\.qmd)\s*$', appendices, re.M)):
        files.append((ROOT / rel, LETTERS[i]))
    return files


def auto_identifier(title):
    """Pandoc's auto_identifiers algorithm for a heading title (formatting already removed)."""
    text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', title).lower()
    text = re.sub(r'[^\w\s_.-]', '', text, flags=re.UNICODE)
    text = re.sub(r'\s+', '-', text.strip())
    text = re.sub(r'^[^a-zÀ-￿]+', '', text)
    return text or 'section'


def split_attributes(title):
    match = re.match(r'^(.*?)\s*\{([^}]*)\}\s*$', title)
    if not match:
        return title, '', []
    attrs = match[2]
    identifier = re.search(r'#([^\s}]+)', attrs)
    classes = re.findall(r'\.([\w-]+)', attrs)
    return match[1], identifier[1] if identifier else '', classes


def sections(path, label):
    """Headings of one file with number, identifier, line range and text; fenced code is skipped."""
    lines = path.read_text(encoding='utf-8').replace('\r\n', '\n').split('\n')
    result, counters, used, fenced = [], [0] * NUMBER_DEPTH, {}, False
    start_text = 0
    for index, line in enumerate(lines):
        if line.startswith('```'):
            fenced = not fenced
        match = None if fenced else re.match(r'^(#{1,6}) (.*)$', line)
        if not match:
            continue
        level = len(match[1])
        title, identifier, classes = split_attributes(match[2].rstrip())
        plain = re.sub(r'[`*]|\[\]\{[^}]*\}', '', title)
        plain = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', plain).strip()
        slug = identifier or auto_identifier(plain)
        if not identifier:
            count = used.get(slug, 0)
            used[slug] = count + 1
            if count:
                slug = f'{slug}-{count}'
        numbered = 'unnumbered' not in classes and level <= NUMBER_DEPTH
        number = ''
        if numbered and level == 1:
            number = label or ''
            counters = [0] * NUMBER_DEPTH
        elif numbered and label:
            counters[level - 2] += 1
            for deeper in range(level - 1, NUMBER_DEPTH):
                counters[deeper] = 0
            number = '.'.join([label] + [str(c) for c in counters[:level - 1]])
        result.append(dict(file=path, level=level, title=plain, id=slug, number=number, line=index, classes=classes))
    for i, section in enumerate(result):
        end = result[i + 1]['line'] if i + 1 < len(result) else len(lines)
        section['end'] = end
    return lines, result
