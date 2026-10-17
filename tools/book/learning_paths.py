"""Maintain visible experiment labels from a reviewed learning-path catalogue."""
import argparse
import csv
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]
CATALOGUE=Path(__file__).with_name('learning-paths.json')
LABEL=re.compile(r'\[(?:Preparation|Core option|Core|Advanced)[^\n]*?\]\([^\n]*?\)\{#act-[^}\n]+ \.learning-activity\}')
ROLES={'preparation':'Preparation','core':'Core','option':'Core option','advanced':'Advanced'}
LIST_SECTIONS={'Fundamentals exercises','Full-SoC integration experiments','6. Extend verification','7. Extend the checks'}

def strip_labels(text):
    text=re.sub(r'^'+LABEL.pattern+r'\n\n','',text,flags=re.M)
    return re.sub(LABEL.pattern+r' — ','',text)

def discover(text):
    """Activity units, not numbered substeps/questions inside a named experiment."""
    result=[];active=False;level=0;lists=False;fence=False
    for line in strip_labels(text).splitlines():
        if re.match(r'^```',line):fence=not fence
        if fence:continue
        h=re.match(r'^(#{2,4})\s+(.*)',line)
        if h:
            n=len(h[1]);title=h[2]
            if re.search('hands-on',title,re.I):active=True;level=n;lists=True
            elif active and n<=level:active=False;lists=False
            elif active:
                named=(re.match(r'Experiment\b',title) is not None or
                       title in {'Ready/valid experiment','Decoder and arithmetic integration experiment'})
                if named:
                    result.append(('heading',line,'hands'));lists=False
                else:lists=title in LIST_SECTIONS
            if not active and re.match(r'Experiment(?:\s+[0-9A-Z]+)?\s*:',title):
                result.append(('heading',line,'hands'))
            if title.startswith('Try it yourself '):result.append(('heading',line,'review'))
        if active and lists and re.match(r'^\d+\. ',line):result.append(('list',line,'hands'))
    return result

def label(entry,page):
    fields=[ROLES[entry['role']]]
    if entry['practice']:fields.append(entry['practice'])
    fields.append(entry['cost'])
    if entry['hardware']=='board':fields.append('board')
    if entry['hardware']=='optional':fields.append('board optional')
    depth=len(Path(page).parts)-1
    target='../'*depth+'learning-paths.qmd#sec-path-labels'
    return '['+' · '.join(fields)+']('+target+'){#act-'+entry['id']+' .learning-activity}'

def render(text,entries,page):
    text=strip_labels(text)
    for entry in entries:
        anchor=entry['anchor']
        if text.splitlines().count(anchor)!=1:raise ValueError('Missing/nonunique activity anchor: '+entry['id'])
        if entry['kind']=='heading':replacement=anchor+'\n\n'+label(entry,page)
        else:
            match=re.match(r'^(\d+\. )(.*)',anchor)
            replacement=match[1]+label(entry,page)+' — '+match[2]
        text=text.replace(anchor+'\n',replacement+'\n',1)
    return text

def validate(data):
    ids=set()
    for e in data['activities']:
        if e['id'] in ids:raise ValueError('Duplicate activity ID: '+e['id'])
        ids.add(e['id'])
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',e['id']):raise ValueError('Invalid activity ID')
        if e['role'] not in ROLES or e['hardware'] not in {'none','optional','board'}:raise ValueError('Invalid role/hardware')
        if not re.fullmatch(r'C[0-3](?: (?:review|build|run|rerun|local|system))?(?: / C[0-3](?: (?:review|build|run|rerun|local|system))?)*',e['cost']):
            raise ValueError('Invalid compute class: '+e['cost'])
        if e['role'] in {'core','option'} and not e['practice']:raise ValueError('Core activity needs a milestone')
        if e['practice'] and not re.fullmatch(r'P[0-5](?:–P[0-5])?',e['practice']):raise ValueError('Invalid milestone')
    pages={e['page'] for e in data['activities']}
    chapters={p.relative_to(ROOT).as_posix() for p in (ROOT/'chapters').rglob('*.qmd')}
    if not chapters<=pages:raise ValueError('Unclassified chapter: '+str(chapters-pages))
    for page in pages:
        text=(ROOT/page).read_text(encoding='utf-8')
        plain=strip_labels(text)
        for e in data['activities']:
            if e['page']==page and e['group']=='review' and e['cost']=='C0':
                body=plain.partition(e['anchor']+'\n')[2].lstrip().split('\n\n',1)[0]
                if re.match(r'Run\b',body):raise ValueError('Executable review cannot be C0: '+e['id'])
        expected=set(discover(text))
        actual={(e['kind'],e['anchor'],e['group']) for e in data['activities'] if e['page']==page and e['group'] in {'hands','review'}}
        if expected!=actual:raise ValueError('Activity coverage drift in '+page+': '+str(expected^actual))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check',action='store_true');mode.add_argument('--write',action='store_true')
    p.add_argument('--export',type=Path)
    args=p.parse_args();data=json.loads(CATALOGUE.read_text(encoding='utf-8'));validate(data)
    for page in sorted({e['page'] for e in data['activities']}):
        path=ROOT/page;text=path.read_text(encoding='utf-8')
        expected=render(text,[e for e in data['activities'] if e['page']==page],page)
        if expected!=text:
            if args.check:raise ValueError('Stale/missing activity labels: '+page)
            path.write_text(expected,encoding='utf-8',newline='\n')
    if args.export:
        args.export.parent.mkdir(parents=True,exist_ok=True)
        with args.export.open('w',encoding='utf-8',newline='') as f:
            fields=['id','title','role','practice','cost','hardware','notes','book_url']
            writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
            for e in data['activities']:
                row={k:e[k] for k in fields if k!='book_url'}
                row['book_url']='https://antoniofloresgil.github.io/FromConceptToSiliconBook/'+str(Path(e['page']).with_suffix('.html')).replace('\\','/')+'#act-'+e['id']
                writer.writerow(row)
    print(f"PASS learning paths: {len(data['activities'])} classified activities; every chapter covered; labels agree with the reviewed catalogue")

if __name__=='__main__':main()
