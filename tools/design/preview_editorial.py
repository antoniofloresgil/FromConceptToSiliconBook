"""Render the maintained editorial specimen in isolation using the book formats."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path,
                        default=ROOT / 'labs/build/editorial-template-preview')
    args = parser.parse_args()
    output = args.output_dir.resolve()
    # Preview publication never overwrites an existing/open proof.
    if output.exists():
        raise SystemExit('Choose a new output directory; existing proofs are preserved: ' + str(output))
    with tempfile.TemporaryDirectory(prefix='editorial-specimen-') as directory:
        source = Path(directory)
        for folder in ['styles', 'design/identity', 'tools/design', 'tools/book']:
            shutil.copytree(ROOT / folder, source / folder,
                            ignore=shutil.ignore_patterns('__pycache__'))
        (source / 'figures').mkdir()
        shutil.copyfile(ROOT / 'figures/async-fifo-ownership.svg',
                        source / 'figures/async-fifo-ownership.svg')
        config = (ROOT / '_quarto.yml').read_text(encoding='utf-8')
        metadata = config.split('book:\n', 1)[1].split('  chapters:\n', 1)[0]
        metadata = metadata.replace('output-file: From-Concept-to-Silicon', 'output-file: editorial-specimen')
        formats = config.split('\nformat:\n', 1)[1]
        formats = formats.replace('    documentclass:', '    keep-tex: true\n    documentclass:')
        (source / '_quarto.yml').write_text(
            'project:\n  type: book\nbook:\n' + metadata +
            '  chapters:\n    - index.qmd\n    - intro.qmd\n    - specimen.qmd\nformat:\n' + formats,
            encoding='utf-8')
        (source / 'index.qmd').write_text(
            '# Preface {.unnumbered}\n\nEditorial layout proof; not a complete book release.\n',
            encoding='utf-8')
        (source / 'intro.qmd').write_text(
            '# Introduction {.unnumbered}\n\nThis proof uses the maintained PDF and HTML format configuration.\n',
            encoding='utf-8')
        specimen = (ROOT / 'design/editorial/specimen.qmd').read_text(encoding='utf-8')
        specimen += '\n| Synthetic row | Description | Value |\n| --- | --- | ---: |\n'
        for number in range(1, 76):
            specimen += f'| Layout-only row {number:03} | Repeated-header and page-break proof | {number} |\n'
        specimen += '\n: Synthetic pagination fixture; not hardware evidence. {#tbl-specimen-long tbl-colwidths="[30,55,15]"}\n'
        (source / 'specimen.qmd').write_text(specimen, encoding='utf-8')
        subprocess.run([sys.executable, 'tools/design/prepare_book.py'], cwd=source, check=True)
        subprocess.run(['quarto', 'render', '--to', 'all'], cwd=source, check=True)
        shutil.copytree(source / '_book', output)
        # Keep generated TeX as an inspectable diagnostic, outside maintained sources.
        tex_files = list(source.glob('*.tex'))
        if len(tex_files) != 1:
            raise RuntimeError('Expected one generated TeX diagnostic')
        shutil.copyfile(tex_files[0], output / 'editorial-specimen.tex')
    print('Editorial proof: ' + str(output))


if __name__ == '__main__':
    main()
