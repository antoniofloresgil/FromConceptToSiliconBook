# Illustration conventions

## Read the evidence category first

| Category | Meaning and preservation rule |
| --- | --- |
| Conceptual SVG | Original explanatory organization or protocol example; it does not establish a particular implementation's timing or performance |
| Attributed datapath/detail | Preserve the imported source geometry, attribution and licensing exception; provide overlapping readable detail views |
| Experimental capture with editorial notes | Embed the original image bytes unchanged inside an SVG reading panel; keep a direct original-resolution link and source identity |
| Retained counterexample | Derive displayed values from the identified retained trace and distinguish observed values from deductions; drawing it is not another proof execution |

`tools/figures/print_audit.py` inventories categories, figure IDs, source paths,
captions and image hashes. `figures/visual-manifest.json` binds the new diagrams,
capture inputs and retained-trace source. Historical lab evidence and the selected
cover illustration remain separate from this editorial work.

## Shared schematic vocabulary

The executable primitives live in `Drawing` in `tools/figures/architecture.py`.
`Drawing.box(kind=...)` adds monochrome-readable marks to a labelled block:

- CPU/core: double outline.
- Cache: three short rules; memory: two short rules.
- Interconnect: a heavy top spine.
- Peripheral: edge ports; accelerator: paired compute chevrons.

The legend `figures/visual-component-language.svg` appears in the Wally chapter.
Detailed RTL symbols, protocol waveforms and attributed datapaths retain their
appropriate notation; they must not be repainted as generic CPU boxes.
Containment denotes ownership, not physical distance. Solid arrows carry the
stated data/request direction; dashed arrows carry explicitly labelled events,
controls or dependencies. State a different local convention in the caption.
Color complements labels and shape marks, never establishes coherence, trust,
privilege or acceptance by itself. Shared schematics use DejaVu Sans with a
960-unit canvas and source labels generally at least 18 units high.

## Captions, references and reading guidance

Every embedded figure needs a unique `#fig-...` identifier, a descriptive caption
and an automatic `@fig-...` prose reference. Explain the scope, what to follow,
and any omitted details or evidence boundary. Do not hard-code figure numbers.
Keep raw image and report links descriptive and usable in both HTML and PDF.

Capture reading panels use numbered observations outside the untouched image.
They guide attention to topology, free space, scale, path context or the report
needed to interpret the view. They do not invent pixel-level net identities,
manufacturing qualification or new timing/power results. Dense physical views
remain overviews; exact endpoints, constraints and values belong to the linked
reports and original-resolution files.

## Maintenance

Edit the relevant generator, regenerate the SVG and manifest, inspect the changed
assets, then update their reviewed hashes. In addition to the existing generators:

```sh
python tools/figures/visual_language.py
python tools/figures/visual_language.py --check
python tools/figures/async_fifo.py --check
python tools/figures/reusable_ip.py --check
python -m unittest discover -s tools/figures -p 'test_*.py'
python tools/figures/print_audit.py --check
```

The navigation check rejects missing/duplicate IDs and absent automatic prose
references. Source checks alone do not establish print readability: follow the
[final-page and grayscale procedure](consultation-and-print.md), preserving the
pipeline overview's existing conditional small-label exception. Do not update a
review hash as a substitute for inspection.
