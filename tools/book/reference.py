"""Generate consultation pages from reviewed terms, lab profiles and activity IDs."""
import argparse
import csv
import io
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
DATA = Path(__file__).with_name('reference-data.json')
URL = 'https://antoniofloresgil.github.io/FromConceptToSiliconBook/'


def load():
    return json.loads(DATA.read_text(encoding='utf-8'))


def heading(text, selector):
    # Ignore headings in code fences; allow selectors to match a title exactly.
    fenced = False
    matches = []
    for line in text.splitlines():
        if line.startswith('```'): fenced = not fenced
        if fenced: continue
        m = re.match(r'^(#{1,6}) (.*?)(?: \{([^}]+)\})?$', line)
        if m and m[2] == selector: matches.append((line, m[3] or ''))
    if len(matches) != 1: raise ValueError('Missing or ambiguous heading: '+selector)
    return matches[0]


def validate(data, activities):
    ids = set()
    for t in data['terms']:
        if t['id'] in ids: raise ValueError('Duplicate term: '+t['id'])
        ids.add(t['id'])
        if not t['definition'] or not t['locations']: raise ValueError('Incomplete term')
        for loc in t['locations']:
            text=(ROOT/loc['page']).read_text(encoding='utf-8')
            line, attrs = heading(text, loc['heading'])
            marker='[]{#'+loc['anchor']+' .reference-destination}'
            position=re.search('^'+re.escape(line)+'$',text,re.M).start()
            markers=re.match(r'(?:\s*\[\]\{#[^}]+\})*',text[position+len(line):])[0]
            if '#'+loc['anchor'] not in attrs.split() and marker not in markers:
                raise ValueError('Missing term destination: '+loc['anchor'])
    if {e['page'] for e in activities} != set(data['profiles']):
        raise ValueError('Experiment profile coverage changed')
    if set(data.get('overrides', {})) - {e['id'] for e in activities}:
        raise ValueError('Unknown activity override')
    requirement_ids={r['id'] for r in json.loads((ROOT/'labs/verification/project-plan.json').read_text(encoding='utf-8'))['requirements']}
    for profile in data['profiles'].values():
        if set(profile['requirements'])-requirement_ids:raise ValueError('Unknown project requirement')
    labs = {p.parent.name for p in (ROOT/'labs').glob('[0-9]*/README.md')}
    if labs != {x['folder'] for x in data['labs']}: raise ValueError('Lab directory coverage changed')
    for p in [*data['profiles'].values(), *data['labs'], *data.get('overrides', {}).values()]:
        if not p.get('tools') or not p.get('requires') or not p.get('contract'):
            raise ValueError('Incomplete dependency/contract profile')


def link(label, target):
    return '['+label.replace('|', '/')+']('+target+')'


def location(loc):
    target = loc['page']+'#'+loc['anchor']
    # Real TeX page references, resolved after layout; HTML uses the same anchor.
    return link(loc['heading'].replace('`', ''), target) + ' `\\textnormal{(p.~\\pageref{'+loc['anchor']+'})}`{=latex}'


def outputs(data, activities):
    terms = sorted(data['terms'], key=lambda t: t['term'].casefold())
    glossary = ['# Technical Glossary {.unnumbered}', '',
        'Concise definitions for consultation. Follow **Read in context** for the assumptions, examples and limitations. The [term index](term-index.qmd) also includes aliases; the [lab index](lab-index.qmd) and [experiment matrix](experiment-index.qmd) lead to executable work.', '']
    index = ['# Index of Terms {.unnumbered}', '',
        'A selected technical index, rather than a list of every textual occurrence. Entries point to the explanation or worked example; page references in print refer to those destinations. Aliases lead to the same glossary definition.', '']
    previous = ''
    for t in terms:
        glossary += ['## '+t['term']+' {#gloss-'+t['id']+' .reference-entry}', '', t['definition'], '',
                     '**Read in context:** '+ '; '.join(location(l) for l in t['locations'])+'.', '']
    entries = sorted([(name, t) for t in terms for name in [t['term'], *t.get('aliases', [])]], key=lambda x:x[0].casefold())
    for name, t in entries:
        letter = name[0].upper()
        if letter != previous: index += ['', '## '+letter+' {.reference-entry}', '']; previous = letter
        index += ['- **'+link(name, 'glossary.qmd#gloss-'+t['id'])+'** — '+ '; '.join(location(l) for l in t['locations'])+'.']
    labs = ['# Laboratory Index {.unnumbered}', '',
        'Directory of all numbered practice folders. A lab is a maintained package; an experiment is an individual learning activity and may use more than one package. The [experiment matrix](experiment-index.qmd) provides the reverse lookup. The README is the authority for commands, pinned versions and outputs; tools below are dependencies, not claims that every extension has been run.', '',
        'The [no-board guide](labs/NO-FPGA.md) gives hardware alternatives. Role and C0–C3 compute labels belong to individual [activities](learning-paths.qmd#sec-path-labels), not to a whole folder.', '']
    for lab in data['labs']:
        labs += ['## '+lab['folder']+' {#lab-'+lab['folder']+' .reference-entry}', '',
                 link(lab['title'], 'labs/'+lab['folder']+'/README.md')+'.', '',
                 '**Tools:** '+lab['tools']+'. **Prerequisites:** '+lab['requires']+'.', '',
                 '**Contract / evidence to inspect:** '+lab['contract']+'.', '',
                 '**Book activities:** '+', '.join(link(p['label'], p['page']) for p in lab['reading'])+'.', '']
    matrix = ['# Experiments, Tools, and Requirements {.unnumbered}', '',
        'This consultation matrix includes all '+str(len(activities))+' classified activities, including short reviews and project milestones. Select an activity by its stable ID and follow the link to the instructions and cost label. These are **prerequisites and contracts to check**, not a record of completed proof or tool execution. Page profiles list the tool choices used in that topic; a paper review does not require installing every listed tool. The individual instructions decide which alternative is needed.', '',
        'Download the [complete experiment matrix as CSV](downloads/experiment-matrix.csv) to filter by tool, requirement, role, compute class or lab. The [laboratory index](lab-index.qmd) gives environment entry points; the [learning-path guide](learning-paths.qmd) explains P0–P5 and C0–C3.', '',
        'Where relevant, **Related project obligations** reuses the DP identifiers in the [project verification plan](labs/verification/project-plan.json). This is a learning correspondence: a FIFO exercise can teach a method needed for DP-FORMAL without proving the accelerator. Only the plan and fresh execution evidence establish coverage. Manufacturing obligations remain visible even where no execution exists.', '']
    rows=[]
    # Follow the published chapter order; activity IDs remain catalogue identities.
    config=(ROOT/'_quarto.yml').read_text(encoding='utf-8')
    pages=[p for p in re.findall(r'^\s*- ([^\s]+\.qmd)\s*$',config,re.M) if p in data['profiles']]
    if set(pages)!=set(data['profiles']):raise ValueError('Book/matrix ordering drift')
    for page in pages:
        profile=data['profiles'][page]
        matrix += ['## '+profile['title']+' {#matrix-'+Path(page).stem+' .reference-entry}', '',
                   '**Tools / alternatives:** '+profile['tools']+'. **Prerequisites:** '+profile['requires']+'.', '',
                   '**Contract / expected evidence:** '+profile['contract']+'.', '',
                   '| Activity | Role / compute |', '| :--- | :--- |']
        if profile['requirements']:
            matrix[-2:-2]=['**Related project obligations:** '+', '.join(profile['requirements'])+'.', '']
        for e in (e for e in activities if e['page']==page):
            p={**profile, **data.get('overrides', {}).get(e['id'], {})}
            target=page+'#act-'+e['id']
            matrix += ['| '+link(e['id']+' — '+e['title'], target)+' | '+e['role']+' / '+e['cost']+' |']
            if e['id'] in data.get('overrides', {}):
                matrix += ['| ↳ '+p['tools']+'; '+p['requires']+'; '+p['contract']+' | selected variant |']
            rows.append(dict(id=e['id'],title=e['title'],tools=p['tools'],requires=p['requires'],contract=p['contract'],
                labs='; '.join(p['labs']),requirement_ids='; '.join(p['requirements']),role=e['role'],practice=e['practice'],cost=e['cost'],hardware=e['hardware'],
                notes=e['notes'],book_url=URL+str(Path(page).with_suffix('.html')).replace('\\','/')+'#act-'+e['id']))
        if profile['labs']:
            matrix += ['', '**Lab entry points:** '+', '.join(link(n,'lab-index.qmd#lab-'+n) for n in profile['labs'])+'.']
        matrix += ['']
    csvfile=io.StringIO(newline=''); writer=csv.DictWriter(csvfile,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    return {'glossary.qmd':'\n'.join(glossary)+'\n','term-index.qmd':'\n'.join(index)+'\n',
            'lab-index.qmd':'\n'.join(labs)+'\n','experiment-index.qmd':'\n'.join(matrix)+'\n',
            'downloads/experiment-matrix.csv':csvfile.getvalue()}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    args=parser.parse_args()
    data=load();activities=json.loads((ROOT/'tools/book/learning-paths.json').read_text(encoding='utf-8'))['activities']
    validate(data,activities)
    for name,text in outputs(data,activities).items():
        path=ROOT/name
        # Download CSV is generated, not committed. Always refresh it before render.
        if args.write or name.startswith('downloads/'):
            path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8',newline='')
        elif not path.is_file() or path.read_text(encoding='utf-8')!=text:
            raise ValueError('Stale consultation page; run python tools/book/reference.py --write: '+name)
    print(f"PASS consultation navigation: {len(data['terms'])} terms, {len(data['labs'])} labs, {len(activities)} activities")


if __name__=='__main__':main()
