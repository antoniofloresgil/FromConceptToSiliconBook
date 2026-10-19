# Editorial identity: Design Flow

This is the author's approved cover and graphic identity for **From Concept to
Silicon**, by Antonio Flores Gil, applied to the digital PDF and HTML editions.
Existing title, subtitle and author are preserved. The general book identity
takes precedence over its optional institutional teaching adoption.

## Design rationale

The front cover pairs a large, left-aligned title with the exact layered image
selected and supplied by the author: architecture, RTL, physical routing with a
highlighted clock tree, and silicon. The supplied image is copied byte for byte
and embedded at its original aspect ratio, without retouching or cropping.
Its dark background is integrated with a black cover surface. Cyan and amber
accents echo its routing and clock highlights; night blue supports secondary
panels, with a pale reading surface and dark text on the back.
The illustration is a visual metaphor, not GDSII, a processor diagram or
implementation evidence. Its miniature code and geometry are decorative and
must not be read as executable RTL or a technically validated circuit.
The selected image supersedes the earlier generated illustration and its
perspective/routing edits. It is not an unmodified OpenROAD screenshot or a
report of new tool execution. The composition remains an illustration, not a
calibrated projective model. No image-generation call was used to alter the
selected attachment.
The back introduces the book and its three established reading routes. The
identity sheet shows the palette, typography and reusable graphic vocabulary.

`palette.json` owns color and font choices. DejaVu Sans, DejaVu Serif and DejaVu
Sans Mono are used because the existing book container can
render them. Font files are not redistributed here. The serif body-text sample
is used for reading text, with sans-serif headings/navigation and monospaced code.
HTML uses local font-family fallbacks when the preferred fonts are unavailable;
the PDF embeds the container's font subsets without network downloads.
PDF verbatim and highlighted code use the existing `fvextra` package to wrap
long lines with a continuation mark, including long syntax-highlighted tokens.
This is presentation wrapping; maintained/downloadable source files are unchanged.
The PDF-only `tools/book/inline-code.lua` filter also allows long ASCII inline
hashes/paths to break between native code spans; Pandoc retains TeX escaping and
all original characters. HTML inline code is left to its browser presentation.

Use pale text on black/night blue and dark text on the reading surface. Cyan and amber
are accents, not body-text colors on a pale background. Text, boundaries and line
geometry carry meaning independently of hue. See the project's permanent
[accessibility requirements](../../docs/accessibility.md).

## Sources and preview

- `front.svg`, `back.svg`, `identity.svg`: editable SVG compositions. The front
  embeds the raster illustration so the file is self-contained; its typography
  remains vector text.
- `selected-layered-soc.png`: the author's selected 1536 × 1024 attachment.
  `selected-artwork.json` records its identity. The original pixels are preserved;
  the separate grayscale proof applies an SVG filter without modifying the PNG.
- `layered-soc.png`, `artwork-prompt.txt`, `artwork-routing-edit.txt` and
  `artwork-perspective-edit.txt`: superseded generated-art exploration and its
  built-in generation/edit prompts. They are not inputs to the current cover.
- [`identity.py`](../../tools/design/identity.py): deterministic generator; edit
  it and the palette, then regenerate SVGs and `styles/book.scss`/`styles/book.tex`.
- `pdf-layout.json`: authoritative PDF dimensions, margins, text size and
  numbered contents depth. The PDF uses A4 (210 × 297 mm), mirrored inner/outer margins,
  no forced blank chapter versos, and 11 pt body text. The HTML remains responsive.
- [`prepare_book.py`](../../tools/design/prepare_book.py): pre-render verification
  and page-sized cover PDF preparation inside `.quarto/identity/`. Contains the
  complete composition and extends its background without distorting/cropping.
  The PDF includes a front cover, half-title, interior title, credits/license,
  Preface, reduced Contents, Introduction, existing body/appendices and back cover.
  Preliminaries use Roman labels; Arabic numbering starts at Introduction.
- `styles/before-body.tex` and `styles/toc.tex`: maintained Quarto template
  partials, not generated outputs. `tools/book/pdf-structure.lua` places contents
  after Preface. The two numbered contents levels are chapters and main sections;
  parts remain structural dividers. Deeper content remains in the PDF body and
  HTML navigation. The collapsed PDF outline has the same reduced depth.
- [`preview.py`](../../tools/design/preview.py): color and luminance-based
  grayscale SVG/PNG/PDF proofs, followed by a six-page review PDF.

Generate SVG sources with Python's standard library:

```powershell
python tools/design/identity.py
```

Render proofs using the existing book environment (`rsvg-convert` and `pypdf`):

```powershell
docker run --rm --network none --mount "type=bind,source=$($PWD.Path),target=/work" from-concept-book:2026.10 python tools/design/preview.py --output-dir _book/identity-selected
```

The same command can use the locally rebuilt audit book image. See the
[book environment guide](../../tools/book/README.md) to build the environment;
this directory adds no font downloads or new container dependencies.

Open `_book/identity-selected/identity-study.pdf`: front, back and identity sheet
in color, then the same three pages in grayscale. Generated proof files stay
outside version control. SVG font substitution may occur on other machines;
use the rendered PDF to review the intended typography.
Choose a new `--output-dir` if an earlier PDF is open and locked by a viewer;
the earlier proof can remain open and unchanged.

## Production boundary

The 800 × 1100 cover canvas is the editable composition master. The digital book
uses A4 (210 × 297 mm) pages, superseding Letter. Print preparation extends the canvas
to that aspect ratio and preserves the complete master composition. The identity
sheet uses a wider presentation canvas. Mirrored margins provide an inside gutter
without shrinking dense architectural figures to a small paperback format.
This is not a press-ready wraparound cover: production trim, bleed, spine width,
paper, binding, printer color profile and any ISBN/barcode remain outside this
digital edition. The back supplies a
readable, clickable book URL; no placeholder QR code or ISBN is used. A QR code
can be added after final size and destination review.

Validate title legibility at thumbnail size and all text at actual print size.
Color/grayscale digital proofs are not printer or PDF accessibility certification.
The Markdown figure audit covers chapter illustrations; cover inspection is an
additional release check. The pale-background HTML link color is a darker blue
for text contrast; cyan and amber are reserved for dark surfaces and accents.

## Prototype verification

The six-page PDF was rendered locally in the rebuilt audit book container.
Color and grayscale proofs of all three compositions were visually inspected;
the PDF embeds subsets of the three specified font families. SVG parsing and
byte-identical source regeneration passed. The selected text/background pairs
(paper, muted, cyan and amber on night; paper and muted on black; ink on paper)
have calculated sRGB contrast ratios of at least 9.18:1. This check applies to those solid text pairs,
not translucent decorative tracks or a physical print process. Bound-print
production still requires a separate typographic and printer proof review.
The selected PNG's SHA-256 and byte-for-byte equality with the supplied
attachment were verified. Its named blocks and miniature code remain part of
the illustration, not substitutes for the book's maintained technical diagrams.
The grayscale front proof desaturates the embedded illustration as well as the
surrounding vector palette. These digital proofs preserve the decorative nature
of the image; no miniature code needs to be read to understand the cover.

Original artwork and explanatory prose: CC BY-SA 4.0. Generator and rendering
code: MIT, under the project's [licensing scope](../../LICENSE.md).

PDF-only figure preparation limits percentage-width illustrations to 85% of the
text height when no explicit height is supplied, reserving room for headings and
captions. Explicit image heights and HTML sizing are preserved. The page bottom
is not stretched to fill short pages.

## Editorial template sources

The generator reads `styles/templates/book.tex.in`, `book.scss.in` and
`frontmatter.tex.in`. Edit those rules and regenerate their includes rather than
embedding typography in `_quarto.yml` or chapter QMD. Covers and preliminaries
are isolated from the main PDF style. The [template guide](../../styles/README.md)
owns the component conventions and small HTML/PDF preview recipe.
