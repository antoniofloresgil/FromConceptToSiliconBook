"""Publish validated artifacts while preserving an open/locked previous edition."""
from pathlib import Path
import shutil
import tempfile
import time
import uuid


def rename_ready(source,destination):
    for attempt in range(20):
        try:
            source.rename(destination)
            return
        except PermissionError:
            if attempt==19:raise
            time.sleep(0.5)


def publish_release(output, bookdir):
    output=Path(output);bookdir=Path(bookdir)
    bookdir.mkdir(parents=True,exist_ok=True)
    incoming=Path(tempfile.mkdtemp(prefix='release-incoming-',dir=bookdir))
    shutil.copytree(output,incoming,dirs_exist_ok=True)
    release=bookdir/'release';backup=None
    if release.exists():
        backup=bookdir/('release-previous-'+uuid.uuid4().hex[:10])
        try:release.rename(backup)
        except PermissionError:
            # A Windows PDF reader can lock the directory. Preserve it intact.
            alternate=bookdir/('release-'+uuid.uuid4().hex[:10])
            rename_ready(incoming,alternate)
            return alternate
    try:rename_ready(incoming,release)
    except OSError:
        if backup is not None and backup.exists() and not release.exists():backup.rename(release)
        raise
    return release
