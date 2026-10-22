"""Write the HTML revision note that shows readers which build of the live edition they are reading."""
import datetime
import html
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / '.quarto' / 'revision-footer.html'
POLICY = 'https://github.com/antoniofloresgil/FromConceptToSiliconBook/blob/main/docs/versioning.md'


def revision():
    value = os.environ.get('BOOK_REVISION')
    if not value:
        try:
            value = subprocess.run(['git', '-c', 'safe.directory=' + str(ROOT), 'rev-parse', 'HEAD'],
                                   cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            value = ''
    return value[:7] if re.fullmatch(r'[0-9a-f]{7,40}', value) else None


def source_dirty():
    """'true', 'false' or 'unknown'; the release builder passes it, a local build asks Git."""
    value = os.environ.get('BOOK_SOURCE_DIRTY')
    if value in {'true', 'false'}:
        return value
    try:
        out = subprocess.run(['git', '-c', 'safe.directory=' + str(ROOT), 'status', '--porcelain',
                              '--untracked-files=no'], cwd=ROOT, check=True, capture_output=True, text=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return 'unknown'
    return 'true' if out.strip() else 'false'


def build_date():
    epoch = os.environ.get('SOURCE_DATE_EPOCH')
    moment = (datetime.datetime.fromtimestamp(int(epoch), datetime.timezone.utc) if epoch
              else datetime.datetime.now(datetime.timezone.utc))
    return moment.date().isoformat()


def note(rev, dirty, date):
    if rev is None:
        state = 'Preview build from unversioned sources'
    elif dirty != 'false':
        state = f'Preview build of revision <code>{html.escape(rev)}</code> with local or unverified modifications'
    else:
        state = f'Live edition, revision <code>{html.escape(rev)}</code>'
    return ('<div class="revision-note" style="margin:2rem 0 1rem;padding-top:.75rem;'
            'border-top:1px solid rgba(128,128,128,.4);font-size:.8rem;opacity:.75">'
            f'{state}, built {date}. Cite sections by their identifiers. '
            f'<a href="{POLICY}">How editions and revisions work</a>.</div>\n')


def main():
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(note(revision(), source_dirty(), build_date()),
                      encoding='utf-8', newline='\n')
    print(f'Revision note: {OUTPUT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
