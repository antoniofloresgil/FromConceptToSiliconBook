import json
from pathlib import Path
import re
import fitz

base=Path(__file__).resolve().parent;root=base.parents[2]
r=json.loads((base/'publication-final-review.json').read_text(encoding='utf-8'))
doc=fitz.open(root/r['release']/'From-Concept-to-Silicon.pdf')
texts=[' '.join(page.get_text().split()) for page in doc]
selected={'cover':1,'term-index':653,'lab-index':659,'experiment-matrix':668,'appendix-c-audit':711,'cdc':102,'pipeline-detail':117}
toc=[i+1 for i,t in enumerate(texts[:36]) if '24.10' in t]
if toc:selected['contents-24-10']=toc[0]
out=base/'samples';out.mkdir(exist_ok=True)
for label,number in selected.items():
    doc[number-1].get_pixmap(matrix=fitz.Matrix(150/72,150/72),colorspace=fitz.csGRAY).save(out/(label+'.png'))
unresolved=[i+1 for i,t in enumerate(texts) if re.search(r'\bp\.\s*\?\?',t)]
assert not unresolved,unresolved
(base/'visual-sample-pages.json').write_text(json.dumps(dict(pdf_sha256=r['pdf_sha256'],pages=selected,
    unresolved_printed_page_references=unresolved,scope='Grayscale page samples for visual inspection; figure contact sheets cover all 46 figure placements.'),indent=2)+'\n')
print('Generated grayscale samples:',selected,'; no unresolved printed p.?? references')
