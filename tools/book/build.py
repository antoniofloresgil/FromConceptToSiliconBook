"""Build a complete release in isolation; publish outputs only after validation."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from pypdf import PdfReader
from publish import publish_release

ROOT = Path(__file__).resolve().parents[2]
EXCLUDED = {'.git', '_book', '.quarto', '.quarto-check', '.vscode', 'downloads',
            'build', 'work', '__pycache__', '.venv', 'obj_dir', 'sim_build', 'runs'}
GENERATED = {'.html', '.pdf', '.pyc', '.log', '.tex', '.aux', '.vcd', '.fst', '.o', '.elf'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(args, cwd=ROOT):
    return subprocess.check_output(args, cwd=cwd, text=True, stderr=subprocess.STDOUT).strip()


def validate_structure(pdf):
    entries = []
    def visit(outline, depth=1):
        for entry in outline:
            if isinstance(entry, list):
                visit(entry, depth + 1)
            else:
                entries.append((entry.title, pdf.get_destination_page_number(entry), depth))
    visit(pdf.outline)
    positions = {}
    for title in ['Credits and license', 'Preface', 'Contents', 'Introduction']:
        matches = [page for name, page, depth in entries if name == title and depth == 1]
        if len(matches) != 1:
            raise RuntimeError('Missing or duplicate PDF navigation landmark: ' + title)
        positions[title] = matches[0]
    if not (positions['Credits and license'] == 3 < positions['Preface'] <
            positions['Contents'] < positions['Introduction']):
        raise RuntimeError('PDF preliminaries are out of order')
    labels = pdf.page_labels
    if labels[1:5] != ['i', 'ii', 'iii', 'iv'] or labels[positions['Introduction']] != '1':
        raise RuntimeError('PDF Roman/Arabic pagination is incorrect')
    if max(depth for _, _, depth in entries) > 3:
        raise RuntimeError('PDF outline exceeds parts, chapters and main sections')
    return {'contents_pages': positions['Introduction'] - positions['Contents'],
            'outline_entries': len(entries), 'landmark_pages':
            {title: page + 1 for title, page in positions.items()}}


def main():
    retained_file = ROOT / 'tools/book/retained-resources.json'
    retained = {entry['path'] for entry in json.loads(retained_file.read_text(encoding='utf-8'))['files']} if retained_file.exists() else set()
    versions = {tool: command([tool, '--version']).splitlines()[0]
                for tool in ['quarto', 'rsvg-convert', 'lualatex', 'python']}
    revision = os.environ.get('BOOK_REVISION')
    if not revision:
        try:
            revision = command(['git', '-c', 'safe.directory=' + str(ROOT), 'rev-parse', 'HEAD'])
        except subprocess.CalledProcessError:
            revision = 'unversioned-source'
    try:
        dirty = bool(command(['git', '-c', 'safe.directory=' + str(ROOT),
                              'status', '--porcelain', '--untracked-files=no']))
    except subprocess.CalledProcessError:
        dirty = None
    inputs = {}
    with tempfile.TemporaryDirectory(prefix='book-release-') as directory:
        source = Path(directory) / 'source'
        source.mkdir()
        paths = []
        for folder, directories, files in os.walk(ROOT):
            directories[:] = sorted(d for d in directories if d not in EXCLUDED)
            paths.extend(Path(folder) / name for name in sorted(files))
        for path in paths:
            relative = path.relative_to(ROOT)
            if any(part in EXCLUDED for part in relative.parts):
                continue
            # Maintained TeX style includes are sources, unlike render-generated TeX.
            style_tex = relative.parent == Path('styles') and path.suffix == '.tex'
            if not path.is_file() or path.is_symlink() or (path.suffix in GENERATED and not style_tex and relative.as_posix() not in retained):
                continue
            target = source / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            inputs[relative.as_posix()] = digest(path)
        if retained - inputs.keys():
            raise RuntimeError('Missing declared retained resources: ' + ', '.join(sorted(retained - inputs.keys())))
        converted = Path(directory) / 'vector-pdf'
        converted.mkdir()
        for svg in sorted((source / 'figures').glob('*.svg')):
            subprocess.run(['rsvg-convert', '--format', 'pdf', '--output',
                            str(converted / (svg.stem + '.pdf')), str(svg)], check=True)
        render_env = {**os.environ, 'BOOK_REVISION': revision,
                      'BOOK_SOURCE_DIRTY': str(dirty).lower() if dirty is not None else 'unknown'}
        subprocess.run(['quarto', 'render', '--to', 'all'], cwd=source, env=render_env, check=True)
        output = source / '_book'
        # Archive the vector figure conversions alongside the HTML originals.
        (output / 'figures').mkdir(exist_ok=True)
        for figure in converted.glob('*.pdf'):
            shutil.copyfile(figure, output / 'figures' / figure.name)
        required = ['index.html', 'From-Concept-to-Silicon.pdf', 'downloads/hardware-design-labs.zip']
        required += ['learning-paths.html', 'downloads/learning-activities.csv']
        required += ['glossary.html', 'term-index.html', 'lab-index.html',
                     'experiment-index.html', 'downloads/experiment-matrix.csv']
        required += [p.relative_to(source).with_suffix('.html').as_posix()
                     for folder in ['chapters', 'appendices'] for p in (source / folder).rglob('*.qmd')]
        for name in required:
            path = output / name
            if not path.is_file() or path.stat().st_size == 0:
                raise RuntimeError('Missing release artifact: ' + name)
        if 'From-Concept-to-Silicon.pdf' not in (output / 'index.html').read_text():
            raise RuntimeError('HTML does not expose the PDF download')
        pdf = PdfReader(output / 'From-Concept-to-Silicon.pdf')
        if len(pdf.pages) < 2:
            raise RuntimeError('The PDF is not a complete book')
        layout = json.loads((source / 'design/identity/pdf-layout.json').read_text(encoding='utf-8'))
        page_width, page_height = (layout['width_mm'] * 72 / 25.4, layout['height_mm'] * 72 / 25.4)
        if any(abs(float(page.mediabox.width) - page_width) > .1 or
               abs(float(page.mediabox.height) - page_height) > .1 for page in pdf.pages):
            raise RuntimeError('PDF pages do not match the maintained print dimensions')
        structure = validate_structure(pdf)
        for name, page, required_text in [('front', pdf.pages[0], ['From', 'Concept', 'Silicon', 'Antonio Flores Gil']),
                                           ('back', pdf.pages[-1], ['Design. Verify. Integrate.', 'Foundations', 'ASIC Design'])]:
            text = page.extract_text()
            if any(item not in text for item in required_text):
                raise RuntimeError('Missing editorial cover or back cover in the PDF')
            expected = PdfReader(source / '.quarto/identity' / (name + '.pdf')).pages[0].extract_text()
            if ' '.join(text.split()) != ' '.join(expected.split()):
                raise RuntimeError('Editorial cover text changed or page furniture was overlaid')
        manifest = {'schema': 1, 'revision': revision, 'tracked_worktree_dirty': dirty,
                    'image_id': os.environ.get('BOOK_IMAGE_ID', 'not-recorded'),
                    'laboratory_validation_run': os.environ.get('BOOK_VALIDATION_RUN_URL'),
                    'tools': versions, 'pdf_pages': len(pdf.pages), 'pdf_structure': structure,
                    'sources': inputs,
                    'artifacts': {p.relative_to(output).as_posix(): digest(p)
                                  for p in sorted(output.rglob('*')) if p.is_file()}}
        packages = Path('/opt/book-packages.tsv')
        manifest['packages'] = packages.read_text() if packages.exists() else 'not-recorded'
        extra_tex = Path('/opt/book-extra-tex.txt')
        manifest['extra_tex_packages'] = extra_tex.read_text() if extra_tex.exists() else 'not-recorded'
        (output / 'build-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        # Preserve previous/open PDFs, including Windows file-sharing locks.
        release = publish_release(output, ROOT / '_book')
        print(f'Validated release: {release}; {len(pdf.pages)} PDF pages; revision {revision}')


if __name__ == '__main__':
    main()
