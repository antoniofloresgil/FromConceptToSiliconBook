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


def main():
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
            if not path.is_file() or path.is_symlink() or path.suffix in GENERATED:
                continue
            target = source / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            inputs[relative.as_posix()] = digest(path)
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
        manifest = {'schema': 1, 'revision': revision, 'tracked_worktree_dirty': dirty,
                    'image_id': os.environ.get('BOOK_IMAGE_ID', 'not-recorded'),
                    'laboratory_validation_run': os.environ.get('BOOK_VALIDATION_RUN_URL'),
                    'tools': versions, 'pdf_pages': len(pdf.pages), 'sources': inputs,
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
