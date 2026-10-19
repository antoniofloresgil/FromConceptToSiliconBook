import hashlib
from importlib.metadata import version
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

import fitz

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
log=(BASE/'book-render-confirmed.log').read_text(encoding='utf-8')
matches=re.findall(r'Validated release: (/work/_book/[^;]+);',log)
assert len(matches)==1,'No unique newly validated release'
release=ROOT/matches[0].removeprefix('/work/')
manifest=json.loads((release/'build-manifest.json').read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
artifacts={n:sha(release/n)==digest for n,digest in manifest['artifacts'].items()}
sources={n:(ROOT/n).is_file() and sha(ROOT/n)==digest for n,digest in manifest['sources'].items()}

class Page(HTMLParser):
    def __init__(self,path):
        super().__init__(convert_charrefs=True)
        self.ids=set();self.links=[]
        self.feed(path.read_text(encoding='utf-8'))
    def handle_starttag(self,tag,attributes):
        data=dict(attributes)
        if data.get('id'):self.ids.add(data['id'])
        if tag=='a' and data.get('name'):self.ids.add(data['name'])
        for key in ['href','src']:
            if data.get(key):self.links.append(data[key])

pages={p.resolve():Page(p) for p in release.rglob('*.html')}
broken=[];checked=0;external=0;nonhtml_fragments=0
for source,page in pages.items():
    for href in page.links:
        try:url=urlsplit(href)
        except ValueError:
            broken.append(dict(source=source.relative_to(release).as_posix(),href=href,reason='invalid URL'));continue
        if url.scheme or url.netloc:external+=1;continue
        if not url.path and not url.fragment:continue
        name=unquote(url.path)
        target=((release/name.lstrip('/')) if name.startswith('/') else source.parent/name).resolve() if name else source
        if target.is_dir():target=target/'index.html'
        checked+=1;reason=None
        if not target.is_relative_to(release):reason='target outside release'
        elif not target.is_file():reason='missing target'
        elif url.fragment and target in pages and unquote(url.fragment) not in pages[target].ids:reason='missing HTML anchor'
        elif url.fragment and target not in pages:nonhtml_fragments+=1
        if reason:broken.append(dict(source=source.relative_to(release).as_posix(),href=href,reason=reason))

pdf=release/'From-Concept-to-Silicon.pdf'
doc=fitz.open(pdf)
toc=doc.get_toc()
text=[' '.join(page.get_text().split()) for page in doc]
pdf_links=[dict(source_page=i+1,link=link) for i,page in enumerate(doc) for link in page.get_links()]
bad_pdf_links=[dict(source_page=x['source_page'],target_page=x['link'].get('page'),xref=x['link'].get('xref'))
    for x in pdf_links if x['link']['kind']==fitz.LINK_GOTO and not 0<=x['link'].get('page',-1)<doc.page_count]
required=['Glossary','Laboratory Index','Index of Terms','Experiments, Tools, and Requirements','Cold-environment reproduction audits']
found={phrase:[i+1 for i,t in enumerate(text) if phrase.casefold() in t.casefold()] for phrase in required}
summary=dict(status='pass' if all(artifacts.values()) and all(sources.values()) and not broken and not bad_pdf_links and all(found.values()) else 'fail',
    release=release.relative_to(ROOT).as_posix(),revision=manifest['revision'],tracked_worktree_dirty=manifest['tracked_worktree_dirty'],
    image_id=manifest['image_id'],tools=manifest['tools'],artifact_hashes_checked=len(artifacts),
    changed_artifacts=[n for n,v in artifacts.items() if not v],source_hashes_checked=len(sources),
    changed_sources=[n for n,v in sources.items() if not v],html_pages=len(pages),local_links_checked=checked,
    external_links_not_fetched=external,non_html_fragments_not_checked=nonhtml_fragments,broken_links=broken,
    pdf_pages=doc.page_count,pdf_sha256=sha(pdf),pdf_outline_entries=len(toc),pdf_required_text_pages=found,
    pdf_links_checked=len(pdf_links),invalid_pdf_page_destinations=bad_pdf_links,
    review_tools=dict(python=sys.version,pymupdf=version('PyMuPDF'),pillow=version('Pillow')),
    scope='Fresh local dirty-worktree release; no deployment. Local HTML href/src targets and HTML anchors checked; external links and browser JavaScript behavior not tested.')
(BASE/(sys.argv[1] if len(sys.argv)>1 else 'publication-review.json')).write_text(json.dumps(summary,indent=2)+'\n')
(BASE/'release-path.txt').write_text(str(release)+'\n')
print(json.dumps(summary,indent=2))
sys.exit(0 if summary['status']=='pass' else 1)
