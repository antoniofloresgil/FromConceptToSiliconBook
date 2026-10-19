"""Inventory every Markdown figure; optionally make grayscale proofs from a release.

Source inventory: standard library. PDF proofs: PyMuPDF 1.26.5, Pillow 11.3.0.
The font estimate is a screening metric, not a substitute for inspecting the PDF.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import struct
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
SVG='{http://www.w3.org/2000/svg}'


def inventory():
    rows=[]
    for page in sorted([*ROOT.glob('chapters/**/*.qmd'),*ROOT.glob('appendices/*.qmd')]):
        text=page.read_text(encoding='utf-8')
        for m in re.finditer(r'!\[([^\n]*?)\]\(([^\n)]+)\)(?:\{([^\n}]+)\})?',text):
            caption,name,attrs=m[1],m[2],m[3] or ''
            image=(page.parent/name).resolve()
            if not image.is_file(): raise ValueError('Missing figure '+name)
            row=dict(page=page.relative_to(ROOT).as_posix(),line=text[:m.start()].count('\n')+1,
                image=image.relative_to(ROOT).as_posix(),caption=caption,
                sha256=hashlib.sha256(image.read_bytes()).hexdigest())
            identity=re.search(r'#(fig-[\w-]+)',attrs)
            row['figure_id']=identity[1] if identity else None
            row['category']='experimental-capture' if image.suffix=='.png' else ('retained-counterexample' if image.stem=='visual-formal-counterexample' else 'attributed-datapath' if image.stem.startswith(('wally-figure-7-13','wally-pipeline-detail')) else 'conceptual')
            match=re.search(r'width=(\d+)%',attrs);fraction=int(match[1])/100 if match else 1.0
            if image.suffix=='.svg':
                svg=ET.parse(image).getroot();box=svg.get('viewBox','').split()
                w,h=map(float,box[2:]) if box else (float(svg.get('width')),float(svg.get('height')))
                raw=image.read_text(encoding='utf-8')
                if 'data:image/png' in raw:row['category']='experimental-capture-with-editorial-notes'
                fonts=[float(x) for x in re.findall(r'font-size[=:]["\s]*([\d.]+)',raw)]
                # Some original figures use only inherited CSS font declarations.
                fonts += [float(x) for x in re.findall(r'font-size="([\d.]+)',raw)]
                scale=min(430*fraction/w,610/h)
                row.update(kind='capture-panel' if 'data:image/png' in raw else 'vector',width=w,height=h,min_source_font=min(fonts) if fonts else None,
                    estimated_min_pt=round(min(fonts)*scale,2) if fonts else None)
                row['review']='small-label review' if fonts and min(fonts)*scale<7 else 'inspect grayscale and line styles'
            elif image.suffix=='.png':
                w,h=struct.unpack('>II',image.read_bytes()[16:24])
                row.update(kind='capture',width=w,height=h,min_source_font=None,estimated_min_pt=None,
                    review='inspect at print scale; geometry overview, not readable GUI text')
            else: raise ValueError('Unreviewed image format: '+str(image))
            rows.append(row)
    return rows


def check_navigation(rows, text):
    identities=set()
    for row in rows:
        identity=row['figure_id']
        if not identity or identity in identities:
            raise ValueError('Missing or duplicate figure ID: '+str(identity))
        identities.add(identity)
        if not re.search('@'+re.escape(identity)+r'(?![\w-])',text):
            raise ValueError('Figure has no automatic prose reference: '+identity)
        if not row['caption'].strip():raise ValueError('Empty figure caption: '+identity)


def proofs(pdf,output,rows):
    import fitz
    from PIL import Image,ImageDraw
    doc=fitz.open(pdf);selected={};labels=[]
    # Find figures through their actual PDF caption, not assumed page numbers.
    for row in rows:
        # A short distinctive fragment tolerates caption line wrapping/hyphenation.
        words=re.sub(r'[*`\[\]]','',row['caption']).split()
        key=' '.join(words[:7]).casefold()
        candidates=[i for i,p in enumerate(doc) if key in ' '.join(p.get_text().split()).casefold()]
        if not candidates:
            # PDF line-end hyphens can split a word in the seven-word fragment.
            key=' '.join(words[:4]).casefold()
            candidates=[i for i,p in enumerate(doc) if key in ' '.join(p.get_text().split()).casefold()]
        if not candidates: raise ValueError('Caption not found in PDF: '+row['image'])
        row['pdf_pages']=[i+1 for i in candidates]
        for i in candidates:selected[i]=True
        labels.append((row,candidates[-1]))
    proof=fitz.open()
    for i in sorted(selected):
        page=doc[i];pix=page.get_pixmap(matrix=fitz.Matrix(150/72,150/72),colorspace=fitz.csGRAY)
        new=proof.new_page(width=page.rect.width,height=page.rect.height)
        new.insert_image(new.rect,stream=pix.tobytes('png'))
    proof.save(output/'figure-grayscale-proof.pdf',deflate=True)
    # Contact sheets retain the full page to expose layout/scale problems.
    for start in range(0,len(labels),9):
        sheet=Image.new('RGB',(1410,2115),'white');draw=ImageDraw.Draw(sheet)
        for n,(row,i) in enumerate(labels[start:start+9]):
            pix=doc[i].get_pixmap(matrix=fitz.Matrix(.65,.65),colorspace=fitz.csGRAY)
            im=Image.frombytes('L',[pix.width,pix.height],pix.samples).convert('RGB')
            im.thumbnail((458,670));x=(n%3)*470;y=(n//3)*705
            sheet.paste(im,(x,y));draw.text((x+5,y+672),str(i+1)+' '+Path(row['image']).name[:45],fill='black')
        sheet.save(output/f'contact-{start//9+1}.png')
    print(f'Proof: {len(selected)} distinct pages; {len(rows)} figure placements; PDF sha256='+hashlib.sha256(pdf.read_bytes()).hexdigest())


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check',action='store_true',help='Reject new unreadably small vector labels')
    p.add_argument('--pdf',type=Path);p.add_argument('--output',type=Path,default=ROOT/'labs/build/figure-print-audit')
    args=p.parse_args();args.output.mkdir(parents=True,exist_ok=True);rows=inventory()
    if args.check:
        text='\n'.join(p.read_text(encoding='utf-8') for p in [*ROOT.glob('chapters/**/*.qmd'),*ROOT.glob('appendices/*.qmd')])
        check_navigation(rows,text)
        review=json.loads(Path(__file__).with_name('print-review.json').read_text(encoding='utf-8'))['assets']
        if set(review)!={r['image'] for r in rows}:raise ValueError('Figure review coverage changed')
        for row in rows:
            if review[row['image']]['sha256']!=row['sha256']:
                raise ValueError('Figure changed since its print review: '+row['image'])
        failures=[r['image'] for r in rows if r['review']=='small-label review' and r['image']!='figures/wally-figure-7-13-editable.svg']
        if failures:raise ValueError('Small vector labels need a print treatment: '+str(failures))
        if not all(any(r['image']==f'figures/wally-pipeline-detail-{i}.svg' for r in rows) for i in range(1,4)):
            raise ValueError('Dense pipeline overview requires all three readable detail views')
    if args.pdf:proofs(args.pdf,args.output,rows)
    (args.output/'inventory.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
    with (args.output/'inventory.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),extrasaction='ignore');writer.writeheader();writer.writerows(rows)
    print(f'PASS figure inventory: {len(rows)} placements; {len({r["image"] for r in rows})} assets; '+
          str(sum(r['review']=='small-label review' for r in rows))+' small-label screenings')
    for row in rows:
        if row['review']=='small-label review':print(row['image'],row['estimated_min_pt'])


if __name__=='__main__':main()
