"""Check PDF-only contents relocation without changing chapter text or HTML."""
from pathlib import Path
import shutil
import subprocess
import unittest

FILTER=Path(__file__).with_name('pdf-structure.lua').resolve()


@unittest.skipUnless(shutil.which('quarto'), 'Requires the maintained book environment')
class Structure(unittest.TestCase):
    def render(self, text, target='latex', filtered=True):
        args=['quarto','pandoc','--from=markdown','--to='+target,'--wrap=none']
        if filtered:args+=['--lua-filter',str(FILTER)]
        return subprocess.check_output(args,input=text,text=True,encoding='utf-8')

    def test_contents_between_preface_and_introduction(self):
        text='# Preface {.unnumbered}\n\nPreface prose.\n\n# Introduction {.unnumbered}\n\nBody prose.\n'
        result=self.render(text)
        self.assertEqual(result.count('\\BookContents'),1)
        self.assertLess(result.index('Preface prose.'),result.index('\\BookContents'))
        self.assertLess(result.index('\\BookContents'),result.index('Introduction'))
        self.assertIn('\\BookMainMatter',result)
        self.assertIn('Body prose.',result)

    def test_html_retains_original_navigation(self):
        text='# Preface\n\nBefore.\n\n# Introduction\n\nAfter.\n'
        self.assertEqual(self.render(text,'html'),self.render(text,'html',False))

    def test_section_named_introduction_does_not_restart_book(self):
        result=self.render('# Another chapter\n\n## Introduction\n\nText.\n')
        self.assertNotIn('\\BookMainMatter',result)

    def test_chapter_extract_without_introduction_is_unchanged(self):
        text='# RTL and Simulation\n\nAn independent extract.\n'
        self.assertEqual(self.render(text),self.render(text,filtered=False))

    def test_explicit_image_height_and_html_remain_unchanged(self):
        text='![Diagram](diagram.png){width=100% height=20mm}\n'
        self.assertEqual(self.render(text),self.render(text,filtered=False))
        self.assertEqual(self.render(text,'html'),self.render(text,'html',False))


if __name__=='__main__':unittest.main()
