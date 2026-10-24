#!/usr/bin/env python3
"""Draft one Quarto reveal.js deck per chapter from the chapter's own structure (standard library only).

Slides come from headings, short lists, small tables, figures, code and the closing review block; the prose of
each subsection becomes speaker notes. Quarto cannot render reveal.js inside a book project, so the decks live in
the separate project `slides/`. The generated `slides/decks/` and `slides/_assets/` are build outputs.

Per-chapter overrides keep the chapters clean: `slides/overrides/<chapter>.json` may hold
  {"skip": ["Heading text"], "bullets": {"Heading text": ["Own bullet", ...]}, "title": {"Heading text": "Own title"}}

Usage: python tools/slides/build_slides.py [chapter-stem ...] [--report]
"""
import argparse
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[2]
SLIDES = ROOT / 'slides'
MIN_SLIDES, MAX_SLIDES = 40, 60
WORDS_FOR_MIN, WORDS_FOR_MAX = 1500, 6300
LANGS = {'systemverilog', 'cpp', 'c', 'python', 'sh', 'bash', 'tcl', 'text', 'yaml', 'asm', 'ld', 'powershell'}
COMMENT = {'python': '# …', 'sh': '# …', 'bash': '# …', 'tcl': '# …', 'yaml': '# …', 'powershell': '# …', 'text': '…'}
ABBREVIATIONS = ('e.g.', 'i.e.', 'vs.', 'etc.', 'cf.', 'Fig.', 'No.', 'et al.')


# ---------------------------------------------------------------- source parsing
def chapter_order():
    """(path, part title) in book order, read from _quarto.yml."""
    order, part = [], ''
    for line in (ROOT / '_quarto.yml').read_text(encoding='utf-8').splitlines():
        match = re.match(r'\s*- part: "(.+)"', line)
        if match:
            part = match[1]
        match = re.match(r'\s*- (chapters/.+\.qmd)\s*$', line)
        if match:
            order.append((ROOT / match[1], part))
    return order


def heading_titles():
    """id -> title for every heading with an identifier, so @sec- references can be named."""
    titles = {}
    for path, _ in chapter_order():
        for line in path.read_text(encoding='utf-8').splitlines():
            match = re.match(r'^#{1,6} (.*?) \{[^}]*#(sec-[\w-]+)[^}]*\}\s*$', line)
            if match:
                titles[match[2]] = match[1]
    return titles


def parse_blocks(text):
    lines = text.replace('\r\n', '\n').split('\n')
    blocks, i, review = [], 0, False
    while i < len(lines):
        line = lines[i]
        if line.startswith('<!-- chapter-review'):
            review = True
            i += 1
            continue
        if not line.strip():
            i += 1
            continue
        if line.startswith('```'):
            lang = line[3:].strip().strip('{}').lstrip('.').split()[0] if line[3:].strip() else ''
            j = i + 1
            while j < len(lines) and not lines[j].startswith('```'):
                j += 1
            blocks.append(dict(kind='code', lang=lang, text='\n'.join(lines[i + 1:j]), review=review))
            i = j + 1
            continue
        if line.startswith(':::'):
            depth, j = 1, i + 1
            while j < len(lines) and depth:
                if lines[j].startswith(':::'):
                    depth += 1 if re.match(r':::+\s*[{\w]', lines[j]) else -1
                j += 1
            blocks.append(dict(kind='div', attrs=line, text='\n'.join(lines[i + 1:j - 1]), review=review))
            i = j
            continue
        match = re.match(r'^(#{1,6}) (.*)$', line)
        if match:
            raw = match[2]
            attrs = re.search(r'\s*\{([^}]*)\}\s*$', raw)
            title = raw[:attrs.start()] if attrs else raw
            attr_text = attrs[1] if attrs else ''
            blocks.append(dict(kind='heading', level=len(match[1]), title=title.strip(), attrs=attr_text,
                               review=review or 'unlisted' in attr_text))
            i += 1
            continue
        if line.startswith('|'):
            j = i
            while j < len(lines) and lines[j].startswith('|'):
                j += 1
            blocks.append(dict(kind='table', lines=lines[i:j], review=review))
            i = j
            continue
        if line.startswith('!['):
            blocks.append(dict(kind='figure', text=line, review=review))
            i += 1
            continue
        if re.match(r'^\s*([-*]|\d+\.) ', line):
            j = i + 1
            while j < len(lines) and lines[j].strip() and not re.match(r'^(#{1,6} |```|:::|\|)', lines[j]):
                j += 1
            blocks.append(dict(kind='list', text='\n'.join(lines[i:j]), review=review))
            i = j
            continue
        j = i + 1
        while j < len(lines) and lines[j].strip() and not re.match(r'^(#{1,6} |```|:::|\||!\[)', lines[j]):
            j += 1
        blocks.append(dict(kind='para', text=' '.join(x.strip() for x in lines[i:j]), review=review))
        i = j
    return blocks


# ---------------------------------------------------------------- text cleaning
def clean(text, titles):
    text = re.sub(r'\[\]\{#[^}]*\}', '', text)
    text = re.sub(r'\[(?:Preparation|Core option|Core|Advanced)[^\]]*\]\([^)]*\)\{#act-[^}]+\}\s*(?:—\s*)?', '', text)
    text = re.sub(r'`\\textnormal\{[^`]*\}`\{=latex\}', '', text)
    text = re.sub(r'\s*\[-?@[^\]]+\]', '', text)
    text = re.sub(r'\(@[\w-]+\)', '', text)
    text = re.sub(r'@fig-[\w-]+', 'the figure', text)
    text = re.sub(r'@tbl-[\w-]+', 'the table', text)
    text = re.sub(r'@(sec-[\w-]+)', lambda m: titles.get(m[1], 'the related chapter'), text)
    text = re.sub(r'\[([^\]]+)\]\([^)]*\)(\{[^}]*\})?', r'\1', text)
    text = re.sub(r'\{[#.][^}]*\}', '', text)
    return re.sub(r'\s+', ' ', text).strip()


def sentences(text):
    protected = text
    for abbreviation in ABBREVIATIONS:
        protected = protected.replace(abbreviation, abbreviation.replace('.', '․'))
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z`*(\[])', protected)
    return [part.replace('․', '.').strip() for part in parts if part.strip()]


def balance(text):
    for marker in ('**', '`', '*'):
        if text.count(marker) % 2:
            text = text.replace(marker, '', 1) if marker != '*' else text.replace('*', '')
    return text


def shorten(sentence, limit=34):
    words = sentence.split()
    if len(words) <= limit:
        return balance(sentence)
    for cut in (';', ':', ' —'):
        position = sentence.find(cut)
        if position > 0 and 8 <= len(sentence[:position].split()) <= limit:
            return balance(sentence[:position].rstrip(' ,') + '.')
    head = ' '.join(words[:limit])
    comma = head.rfind(', ')
    if comma > 60:
        return balance(head[:comma] + '.')
    return balance(head + ' …')


def bullets_from(paragraph, count=3, words=85):
    chosen, used = [], 0
    for sentence in sentences(paragraph):
        item = shorten(sentence)
        size = len(item.split())
        if chosen and used + size > words:
            break
        chosen.append(item)
        used += size
        if len(chosen) == count:
            break
    return chosen


# ---------------------------------------------------------------- slide candidates
def table_lines(body, factor=1.0):
    """Estimated rendered text lines of a pipe table, to decide whether it fits on one slide."""
    rows = [[c.strip() for c in line.strip().strip('|').split('|')] for line in body.split('\n') if not set(line) <= set('|- ')]
    per = max(1, int(84 * factor / len(rows[0])))
    return sum(max(max(1, -(-len(cell) // per)) for cell in row) for row in rows)


def table_markdown(block, titles):
    rows = [[clean(cell, titles) for cell in line.strip().strip('|').split('|')] for line in block['lines']]
    if len(rows) < 3 or len(rows[0]) > 5:
        return None
    markdown = '\n'.join('| ' + ' | '.join(row) + ' |' for row in rows[:1] + [['---'] * len(rows[0])] + rows[2:])
    return markdown if table_lines(markdown, 1.3) <= 10 else None


def code_markdown(block):
    if block['lang'] not in LANGS:
        return None
    lines = block['text'].split('\n')
    if len(lines) < 2:
        return None
    if len(lines) > 12:
        lines = lines[:11] + [COMMENT.get(block['lang'], '// …')]
    return f"```{block['lang']}\n" + '\n'.join(lines) + '\n```'


class Slide:
    def __init__(self, kind, title, body, notes='', priority=1, order=0):
        self.kind, self.title, self.body, self.notes, self.priority, self.order = kind, title, body, notes, priority, order

    def markdown(self, small=False):
        dense = small or (self.kind == 'code' and self.body.count('\n') > 9) or (self.kind == 'table' and table_lines(self.body) > 7)
        head = f'## {self.title}' + (' {.smaller}' if dense else '')
        out = [head, '', self.body.rstrip()]
        if self.notes.strip():
            out += ['', '::: {.notes}', self.notes.strip(), ':::']
        return '\n'.join(out) + '\n'


def build_deck(path, part, number, titles, overrides, pair=2):
    text = path.read_text(encoding='utf-8')
    blocks = parse_blocks(text)
    chapter_title = next(b['title'] for b in blocks if b['kind'] == 'heading' and b['level'] == 1)
    body_words = sum(len(b['text'].split()) for b in blocks if b['kind'] in ('para', 'list') and not b['review'])
    skip = set(overrides.get('skip', []))
    own_bullets, own_titles = overrides.get('bullets', {}), overrides.get('title', {})

    units, current, h2 = [], None, ''
    for b in blocks:
        if b['kind'] == 'heading':
            if b['level'] == 1:
                continue
            if b['review']:
                current = dict(title=b['title'], review=True, items=[], h2=b['title'])
                units.append(current)
            elif b['level'] == 2:
                h2 = b['title']
                current = dict(title=b['title'], review=False, items=[], h2=h2, level=2)
                units.append(current)
            else:
                current = dict(title=b['title'], review=False, items=[], h2=h2, level=3)
                units.append(current)
            continue
        if current is not None:
            current['items'].append(b)

    slides, order = [], 0

    def add(*args, **kwargs):
        nonlocal order
        order += 1
        slides.append(Slide(*args, order=order, **kwargs))

    def figure_slide(block, title):
        info = re.match(r'!\[(.*)\]\(([^)]+)\)(?:\{([^}]*)\})?', block['text'])
        if not info:
            return
        caption, name = info[1], info[2]
        source = (path.parent / name).resolve()
        if not source.is_file() or source.suffix != '.svg':
            return
        target = SLIDES / '_assets' / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        alt = re.search(r'fig-alt="([^"]*)"', info[3] or '')
        short = clean(sentences(caption)[0] if sentences(caption) else caption, titles)
        add('figure', title, f'![{short}](../_assets/{source.name}){{fig-alt="{alt[1] if alt else short}" fig-align="center" height=470}}',
            notes=clean(caption, titles), priority=1)

    deck_title = clean(chapter_title, titles)
    for unit in units:
        if unit['title'] in skip or unit['review']:
            continue
        title = own_titles.get(unit['title'], clean(unit['title'], titles))
        items = unit['items']
        if unit.get('level') == 2:
            add('section', title, '', priority=1)
        prose = [b for b in items if b['kind'] == 'para' and not b['text'].startswith(('**Recipe status', '**Exercise'))]
        topics, details, equations = [], [], []
        for block in prose:
            parts = sentences(clean(block['text'], titles))
            if not parts or parts[0][:1].islower() or re.match(r'(?i)^(the )?(figure|table|following)\b', parts[0]) or (len(parts) == 1 and parts[0].endswith(':')):
                continue
            if parts[0].startswith('$$'):
                equations.append(parts[0])
                continue
            lead = parts[0]
            rest = parts[1:]
            if len(lead.split()) < 6 and rest:
                lead, rest = f'{lead} {rest[0]}', rest[1:]
            topics.append(shorten(lead, 28))
            if rest:
                details.append([shorten(x, 30) for x in rest[:2]])
        notes = '\n\n'.join(clean(b['text'], titles) for b in items if b['kind'] in ('para', 'list'))
        if unit['title'] in own_bullets:
            topics = own_bullets[unit['title']]
        lists = [b for b in items if b['kind'] == 'list' and len(b['text'].split()) <= 130 and b['text'].count('\n') <= 8]
        if not topics and lists:
            add('list', title, clean_list(lists.pop(0)['text'], titles), notes=notes, priority=1)
        pages = -(-len(topics) // 5)
        for number in range(pages):
            group = topics[number * len(topics) // pages:(number + 1) * len(topics) // pages]
            add('lead', title if not number else f'{title} ({number + 1})', '\n'.join(f'- {x}' for x in group),
                notes=notes if not number else '', priority=1)
        for equation in equations[:2]:
            add('math', f'{title}: equation', equation, priority=3)
        for block in lists:
            add('list', f'{title}: key points', clean_list(block['text'], titles), priority=2)
        for number in range(0, len(details), pair):
            group = [x for sentences_ in details[number:number + pair] for x in sentences_]
            add('extra', f'{title}: detail', '\n'.join(f'- {x}' for x in group), priority=3)
        for block in items:
            if block['kind'] == 'figure':
                figure_slide(block, title)
            elif block['kind'] == 'table':
                markdown = table_markdown(block, titles)
                if markdown:
                    add('table', f'{title}: summary', markdown, priority=2)
            elif block['kind'] == 'code':
                markdown = code_markdown(block)
                if markdown:
                    short = block['text'].count('\n') < 12
                    add('code', f'{title}: code' if short else f'{title}: code excerpt', markdown,
                        notes='The complete listing is in the chapter.', priority=2 if short else 3)
            elif block['kind'] == 'div' and 'callout' in block['attrs'] and 'Wally' not in block['attrs']:
                chosen = bullets_from(clean(block['text'], titles), count=2, words=60)
                if chosen:
                    add('callout', f'{title}: note', '\n'.join(f'- {x}' for x in chosen), priority=3)

    # closing slides from the review block
    closers = []
    for unit in units:
        if not unit['review']:
            continue
        name = unit['title']
        paragraphs = [b for b in unit['items'] if b['kind'] == 'para']
        lists = [b for b in unit['items'] if b['kind'] == 'list']
        divs = [b for b in unit['items'] if b['kind'] == 'div']
        if name == 'Key ideas' and lists:
            closers.append(('Key ideas', clean_list(lists[0]['text'], titles)))
        elif name.startswith('What you should now') and paragraphs:
            closers.append(('You should now be able to…', '\n'.join(f'- {x}' for x in bullets_from(clean(paragraphs[0]['text'], titles), 3, 90))))
        elif name == 'Common mistakes' and paragraphs:
            closers.append(('Common mistakes', '\n'.join(f'- {x}' for x in bullets_from(clean(paragraphs[0]['text'], titles), 4, 110))))
        elif name == 'Try it yourself' and paragraphs:
            closers.append(('Try it yourself', '\n'.join(f'- {x}' for x in bullets_from(clean(paragraphs[-1]['text'], titles), 3, 90))))
        elif name.startswith('Where this appears') and divs:
            closers.append(('Where this appears in Wally', '\n'.join(f'- {x}' for x in bullets_from(clean(divs[0]['text'], titles), 2, 70))))
    target = round(MIN_SLIDES + (MAX_SLIDES - MIN_SLIDES) * (min(max(body_words, WORDS_FOR_MIN), WORDS_FOR_MAX) - WORDS_FOR_MIN)
                   / (WORDS_FOR_MAX - WORDS_FOR_MIN))
    fixed = 2 + len(closers)  # title and agenda plus the closers
    chosen = select(slides, target - fixed)
    agenda, group = [], None
    for u in units:
        if u['review']:
            continue
        if u.get('level') == 2:
            group = [clean(u['title'], titles), []]
            agenda.append(group)
        elif group is not None:
            group[1].append(clean(u['title'], titles))
    return deck_title, part, chosen, agenda, closers, target, body_words


def clean_list(text, titles):
    items = []
    for raw in re.split(r'\n(?=\s*(?:[-*]|\d+\.) )', text):
        item = clean(re.sub(r'^\s*(?:[-*]|\d+\.)\s+', '', raw), titles)
        if item:
            items.append(f'- {shorten(item, 30)}')
    return '\n'.join(items[:8])


def select(slides, budget):
    """Keep structure and core content; drop or add lower-priority slides until the budget is met."""
    keep = [s for s in slides if s.priority <= 2]
    optional = [s for s in slides if s.priority == 3]
    if len(keep) > budget:
        for kind in ('table', 'list', 'section'):
            while len(keep) > budget:
                candidates = [s for s in keep if s.kind == kind]
                if not candidates:
                    break
                keep.remove(candidates[-1] if kind != 'table' else max(candidates, key=lambda s: len(s.body)))
        while len(keep) > budget:
            leads = [s for s in keep if s.kind == 'lead']
            keep.remove(min(leads, key=lambda s: len(s.body)))
    room = budget - len(keep)
    if room > 0 and optional:
        # spread the optional slides evenly through the chapter instead of filling from the start
        chosen = optional if room >= len(optional) else [optional[i * len(optional) // room] for i in range(room)]
        keep.extend(chosen)
    return sorted(keep, key=lambda s: s.order)


def write_deck(index, path, part, number, titles):
    overrides_path = SLIDES / 'overrides' / f'{path.stem}.json'
    overrides = json.loads(overrides_path.read_text(encoding='utf-8')) if overrides_path.is_file() else {}
    for pair in (2, 1):
        title, part, slides, agenda, closers, target, words = build_deck(path, part, number, titles, overrides, pair)
        if 2 + len(slides) + len(closers) >= MIN_SLIDES:
            break
    out = [f'---\ntitle: "{title}"\nsubtitle: "{part} · Chapter {number}"\nauthor: "Antonio Flores Gil"\n---\n']
    shown = 3 if len(agenda) <= 3 else 2 if len(agenda) <= 5 else 0  # keep the agenda on one slide
    lines = [f'- **{name}**' + (': ' + ' · '.join(subs[:shown]) + (' …' if len(subs) > shown else '') if subs and shown else '')
             for name, subs in agenda[:8]]
    out.append('## What this chapter covers\n\n' + '\n'.join(lines) + ('\n- …' if len(agenda) > 8 else '') + '\n')
    for s in slides:
        if s.kind == 'section':
            out.append(f'# {s.title} {{background-color="#101f30"}}\n')
        else:
            out.append(s.markdown())
    for name, body in closers:
        out.append(f'## {name}\n\n{body}\n')
    deck = SLIDES / 'decks' / f'{index:02d}-{path.stem}.qmd'
    deck.parent.mkdir(parents=True, exist_ok=True)
    deck.write_text('\n'.join(out), encoding='utf-8', newline='\n')
    count = 1 + 1 + sum(1 for s in slides) + len(closers)
    return deck.name, count, target, words


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('stems', nargs='*')
    parser.add_argument('--report', action='store_true')
    args = parser.parse_args()
    titles = heading_titles()
    for old in (SLIDES / 'decks').glob('*.qmd') if (SLIDES / 'decks').exists() else []:
        old.unlink()
    results = []
    for number, (path, part) in enumerate(chapter_order(), 1):
        if args.stems and path.stem not in args.stems:
            continue
        results.append(write_deck(number, path, part, number, titles))
    for name, count, target, words in results:
        print(f'{name:58s} slides {count:3d}  target {target:2d}  words {words}')
    print(f'{len(results)} decks written to slides/decks/')


if __name__ == '__main__':
    main()
