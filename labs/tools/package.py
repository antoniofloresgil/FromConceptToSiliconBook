"""Portable practice archive: no book text, with listing provenance and integrity."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit
import zipfile

BOOK_URL = 'https://antoniofloresgil.github.io/FromConceptToSiliconBook/'
REPOSITORY = 'https://github.com/antoniofloresgil/FromConceptToSiliconBook'
MANIFEST = 'LAB-PROVENANCE.json'
EXAMPLES = [
    {'chapter': 'chapters/03-simulation-verification/verilator.qmd', 'language': 'systemverilog',
     'starts': ['module accumulator'], 'file': 'examples/verilator/accumulator.sv'},
    {'chapter': 'chapters/03-simulation-verification/verilator.qmd', 'language': 'cpp',
     'starts': ['#include "Vaccumulator.h"'], 'file': 'examples/verilator/sim_main.cpp'},
    {'chapter': 'chapters/03-simulation-verification/cocotb.qmd', 'language': 'python',
     'starts': ['import random'], 'file': 'examples/cocotb/test_accumulator.py'},
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def source_identity(root):
    revision = os.environ.get('BOOK_REVISION')
    dirty = os.environ.get('BOOK_SOURCE_DIRTY')
    if not revision and (root / '.git').exists():
        prefix = ['git', '-c', f'safe.directory={root}']
        revision = subprocess.check_output([*prefix, 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
        dirty = 'true' if subprocess.check_output(
            [*prefix, 'status', '--porcelain', '--untracked-files=no'], cwd=root, text=True).strip() else 'false'
    return {'repository': REPOSITORY, 'revision': revision,
            'tracked_worktree_dirty': {'true': True, 'false': False}.get(dirty)}


def online_book_links(root, path, text):
    """Keep local executable links; send omitted book documents to the HTML site."""
    def replace(match):
        target = match.group(1).strip('<>')
        if urlsplit(target).scheme or target.startswith('#'):
            return match.group(0)
        relative, separator, fragment = target.partition('#')
        destination = (path.parent / unquote(relative)).resolve()
        if not destination.is_relative_to(root):
            return match.group(0)
        name = destination.relative_to(root).as_posix()
        if destination.suffix == '.qmd':
            return '](' + BOOK_URL + str(Path(name).with_suffix('.html')).replace('\\', '/') + (separator + fragment if separator else '') + ')'
        return match.group(0)
    return re.sub(r'\]\(([^\n)]+)\)', replace, text)


def build_package(root, sources):
    root = root.resolve()
    if not (root / 'chapters').is_dir():
        raise RuntimeError('pack requires the full book repository; the practice ZIP contains no chapter text')
    payload = {}
    excluded = {'build', 'work', '__pycache__', 'sim_build', 'obj_dir', '.venv', 'runs', '.git'}
    generated = {'.vcd', '.fst', '.pyc', '.html', '.pdf', '.o', '.elf', '.dump', '.sig', '.log', '.vvp'}
    for base in ['labs', 'examples']:
        for folder, directories, files in os.walk(root / base):
            directories[:] = sorted(d for d in directories if d not in excluded)
            for filename in sorted(files):
                path = Path(folder) / filename
                name = path.relative_to(root).as_posix()
                if path.is_symlink() or path.suffix in generated or filename == 'results.xml' or name in {'labs/PACKAGE.md', 'labs/tools/test_package.py'}:
                    continue
                data = path.read_bytes()
                if path.suffix == '.md':
                    data = online_book_links(root, path, data.decode('utf-8')).encode('utf-8')
                payload[name] = data
    for name in ['LICENSE.md', 'NOTICE.md', '.dockerignore', '.gitattributes']:
        payload[name] = (root / name).read_bytes()
    for path in sorted((root / 'LICENSES').glob('*.txt')):
        payload[path.relative_to(root).as_posix()] = path.read_bytes()
    payload['README.md'] = (root / 'labs/PACKAGE.md').read_bytes()
    identity = source_identity(root)
    revision = identity['revision'] or 'main'
    manifest = {'schema': 1, 'kind': 'hardware-design-labs', 'source': identity,
                'book_url': BOOK_URL, 'listing_origins': []}
    for item in [*sources, *EXAMPLES]:
        manifest['listing_origins'].append({**item,
            'file_sha256': sha(payload[item['file']]),
            'chapter_sha256': sha((root / item['chapter']).read_bytes()),
            'source_url': f"{REPOSITORY}/blob/{revision}/{item['chapter']}",
            'book_url': BOOK_URL + str(Path(item['chapter']).with_suffix('.html')).replace('\\', '/')})
    payload[MANIFEST] = (json.dumps(manifest, indent=2) + '\n').encode('utf-8')
    hashes = {name: sha(data) for name, data in sorted(payload.items())}
    payload['SHA256SUMS.json'] = (json.dumps(hashes, indent=2) + '\n').encode('utf-8')
    destination = root / 'downloads/hardware-design-labs.zip'
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(payload.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    print(f'Package: {destination} sha256={sha(destination.read_bytes())}; {len(payload)} files, no book text')


def check_package(root, sources):
    index = root / 'SHA256SUMS.json'
    if not index.is_file():
        raise RuntimeError('Practice package is missing SHA256SUMS.json')
    hashes = json.loads(index.read_text(encoding='utf-8'))
    if MANIFEST not in hashes:
        raise RuntimeError('Practice provenance manifest is missing from the checksum index')
    for name, expected in hashes.items():
        path = (root / name).resolve()
        if not path.is_relative_to(root) or path.is_symlink() or not path.is_file() or sha(path.read_bytes()) != expected:
            raise RuntimeError(f'Downloaded package checksum mismatch: {name}')
    manifest = json.loads((root / MANIFEST).read_text(encoding='utf-8'))
    if manifest.get('schema') != 1 or manifest.get('kind') != 'hardware-design-labs':
        raise RuntimeError('Unsupported practice provenance manifest')
    origins = manifest.get('listing_origins', [])
    expected_sources = [*sources, *EXAMPLES]
    if len(origins) != len(expected_sources):
        raise RuntimeError('Practice listing provenance is incomplete')
    by_file = {item['file']: item for item in origins}
    for expected in expected_sources:
        item = by_file.get(expected['file'])
        if not item or any(item.get(key) != value for key, value in expected.items()):
            raise RuntimeError(f"Practice listing origin mismatch: {expected['file']}")
        if item.get('file_sha256') != hashes.get(expected['file']):
            raise RuntimeError(f"Practice listing hash mismatch: {expected['file']}")
        if not re.fullmatch('[0-9a-f]{64}', item.get('chapter_sha256', '')):
            raise RuntimeError(f"Practice chapter fingerprint missing: {expected['file']}")
    print(f'PASS practice package: checksums and {len(origins)} listing origins; source chapters checked when packaged')
