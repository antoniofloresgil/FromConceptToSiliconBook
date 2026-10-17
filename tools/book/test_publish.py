"""Regression for the Windows open-PDF publication failure."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from publish import publish_release

class Publication(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.source=self.root/'new';self.source.mkdir()
        (self.source/'book.pdf').write_bytes(b'new complete PDF')
        self.book=self.root/'_book';self.old=self.book/'release';self.old.mkdir(parents=True)
        (self.old/'book.pdf').write_bytes(b'previous PDF')
    def test_previous_edition_survives_success(self):
        result=publish_release(self.source,self.book)
        self.assertEqual((result/'book.pdf').read_bytes(),b'new complete PDF')
        self.assertEqual(next(self.book.glob('release-previous-*')).joinpath('book.pdf').read_bytes(),b'previous PDF')
    def test_locked_pdf_preserves_old_and_publishes_complete_alternate(self):
        rename=Path.rename
        def locked(path,target):
            if path==self.old:raise PermissionError('PDF is open')
            return rename(path,target)
        with patch.object(Path,'rename',locked):result=publish_release(self.source,self.book)
        self.assertNotEqual(result,self.old)
        self.assertEqual((self.old/'book.pdf').read_bytes(),b'previous PDF')
        self.assertEqual((result/'book.pdf').read_bytes(),b'new complete PDF')
    def test_failed_final_move_restores_previous_edition(self):
        rename=Path.rename
        def fail(path,target):
            if path.name.startswith('release-incoming-'):raise OSError('publication interrupted')
            return rename(path,target)
        with patch.object(Path,'rename',fail),self.assertRaises(OSError):publish_release(self.source,self.book)
        self.assertEqual((self.old/'book.pdf').read_bytes(),b'previous PDF')
    def test_transient_incoming_lock_is_retried(self):
        rename=Path.rename;attempts=[]
        def transient(path,target):
            if path.name.startswith('release-incoming-'):
                attempts.append(path)
                if len(attempts)<3:raise PermissionError('bind mount settling')
            return rename(path,target)
        with patch.object(Path,'rename',transient),patch('publish.time.sleep'):
            result=publish_release(self.source,self.book)
        self.assertEqual(len(attempts),3)
        self.assertEqual((result/'book.pdf').read_bytes(),b'new complete PDF')
    def test_permanent_incoming_lock_restores_old_release(self):
        rename=Path.rename
        def locked(path,target):
            if path.name.startswith('release-incoming-'):raise PermissionError('permanent lock')
            return rename(path,target)
        with patch.object(Path,'rename',locked),patch('publish.time.sleep'),self.assertRaises(PermissionError):
            publish_release(self.source,self.book)
        self.assertEqual((self.old/'book.pdf').read_bytes(),b'previous PDF')

if __name__=='__main__':unittest.main()
