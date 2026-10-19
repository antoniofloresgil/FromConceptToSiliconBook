# Editorial template

The chapter QMD files contain semantic content, not the book's typography. The
runtime layers are:

| File | Responsibility |
| --- | --- |
| `_quarto.yml` | Metadata, chapter order, bibliography, references, output formats, filters and template selection |
| `styles/book.tex` | PDF fonts, A4 geometry, hierarchy, running heads, captions, tables, code, footnotes and semantic callouts |
| `styles/book.scss` | Equivalent HTML identity, responsive figures/tables, code scrolling, notes, footnotes and keyboard focus |

`styles/frontmatter.tex` isolates the cover, title/credits pages, contents and
pagination transitions. The two short Quarto partials select their placement;
they do not contain chapter prose. Cover artwork remains independent of all
chapter files.

## Edit the sources, then regenerate

The three style includes are generated. Edit the matching
[`templates/*.in`](templates/) file for rules; edit
[`palette.json`](../design/identity/palette.json) for the shared core identity or
[`pdf-layout.json`](../design/identity/pdf-layout.json) for print dimensions and
type size. Do not hand-edit the generated includes.

```bash
python tools/design/identity.py
python tools/design/identity.py --check
```

This command also refreshes the independent editable cover SVGs. To change their
composition, edit the cover functions in `tools/design/identity.py`; the selected
illustration is protected by its separate asset manifest. See the
[identity guide](../design/identity/README.md). Changing a title style, cover or
palette requires no chapter edits.

## Authoring conventions

- Use Markdown headings and cross-references. Leave numbering, page geometry,
  running heads and contents indentation to the template.
- Keep original diagrams in `figures/`, preferably editable SVG. Keep measured
  captures in their lab reference directories with their provenance. Do not move
  those assets merely to rename the resource directory; existing paths are stable.
- Provide meaningful figure captions/alternative descriptions and stable IDs.
  PDF figures preserve aspect ratio and leave room for their captions. HTML
  figures fit their containers without stretching.
- Use semantic tables with units and suitable alignment. Give dense tables
  explicit `tbl-colwidths`, as a caption attribute or on a surrounding Div.
  PDF uses booktabs rules, repeated longtable headers and readable compact type.
  HTML retains Quarto's responsive overflow handling. Do not rasterize a table.
- Use fenced code blocks with language names. Keep actual source characters:
  PDF wraps long lines; HTML supports scrolling/copying. Do not add manual
  continuation characters to executable code for appearance.
- Use `.callout-note`, `.callout-tip`, `.callout-warning`, `.callout-important`
  and `.callout-caution` with descriptive titles. Labels and icons complement
  color; note text remains visible in grayscale. Use Markdown footnotes for
  supporting detail, preserving HTML return links.

## Review the component specimen

Run inside the maintained book environment, from the repository root:

```bash
python tools/design/preview_editorial.py --output-dir labs/build/editorial-template-preview
```

The runner uses the actual book metadata and format configuration and renders
[`design/editorial/specimen.qmd`](../design/editorial/specimen.qmd) as a small
HTML/PDF book, including a synthetic multi-page table. It creates the preview in
isolation and refuses to overwrite an earlier proof. Use a new output directory
for each review. Its numbers and snippets are formatting fixtures, not lab results.
The output includes the generated TeX diagnostic.

Inspect heading hierarchy, running heads, figure proportions, long captions,
numerical alignment, repeated table headers, long code lines, all five callout
types and footnote links. Check desktop/mobile HTML and grayscale PDF. Then run
the full [book builder](../tools/book/README.md) and review the final release:
the small specimen does not establish that every real chapter fits.
