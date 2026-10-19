# Accessibility requirements

## Access to learning and compute

The teaching adoption must be completable without buying or borrowing an FPGA.
Retain physical-board activities alongside explicit simulation/report-analysis
alternatives, with the same learning outcomes and rubric opportunities. Board
ownership is not an assessment criterion. An instructor-provided implementation
report illustrates its identified source/target; it does not qualify a student's
modified RTL. Keep unexecuted board/physical checks visible in the dossier.
The maintained activity-by-activity alternatives are in
[labs/NO-FPGA.md](../labs/NO-FPGA.md).

Board access and tool/compute access are separate. A route without a board can
still require a target database, PDK or provisioned workstation. The instructor
provisions the real-Wally firmware/DMA/IRQ fixture for the Core integration
milestone; a small AXI harness prepares that work without silently replacing it.

Keep activity roles, compute classes and board requirements separately visible.
C0–C3 are qualitative provisioning classes, not measured runtime or minimum-RAM
guarantees. Support review of identified physical reports when a rerun is outside
the chosen route's resources. Definitions and selection guidance remain in
[learning-paths.qmd](../learning-paths.qmd); do not maintain a second cost taxonomy.

## Consultation and links

Provide descriptive links to the glossary, term index, lab index and experiment
matrix from the entry material. Preserve source URLs and stable activity IDs.
The term index must offer both explanation links and resolved print page
references. Keep alphabetical headings separate from adjacent Markdown lists.
Expose the matrix as CSV for filtering outside the rendered book.

Use headings and meaningful captions/alternative descriptions so the material
can be navigated without depending on a figure's visual appearance. Keep HTML
local heading navigation while avoiding hundreds of redundant PDF contents rows.

The HTML reading column must shrink on narrow screens. Contain horizontal
scrolling within wide tables and code blocks rather than clipping ordinary prose.
Preserve visible keyboard focus, descriptive callout titles and footnote return
links. Review the maintained editorial specimen in desktop and narrow layouts;
its recipe lives in [the template guide](../styles/README.md).

## Figures and grayscale printing

- Meaning must survive loss of hue: use explicit labels, shapes, containment,
  arrow direction, line styles or ordered lightness. A color name alone is not
  a sufficient legend for a categorical distinction.
- Review lettering at the actual PDF print scale, including dense diagrams,
  legends and captions. Larger text must still fit its boxes. The source audit's
  nominal 7 pt screening threshold is a warning mechanism, not evidence of
  readability or a substitute for visual inspection.
- Provide enlarged detail views for dense diagrams whose signal names cannot
  be read in the orientation view. Retain context and explain crop overlap.
- Preserve actual physical captures and their provenance. Geometry/topology
  overviews do not guarantee that layer colors or tiny GUI labels remain readable
  in grayscale. Supply named reports, numeric tables and full-resolution sources
  for those details, and state that boundary in the reading guidance.
- Inspect all embedded figure placements in grayscale, with full-page proof
  images for layout and larger views where necessary. Digital proofs do not
  validate a particular printer or paper.

Run `python tools/figures/print_audit.py --check` for inventory, font screening and
reviewed-asset hashes. New or changed assets need a fresh visual review and an
update to `tools/figures/print-review.json`; do not update hashes as a substitute
for that review. The sole small-label exception is the dense pipeline orientation
view, conditional on its three overlapping enlarged details. Procedures and
optional proof-tool dependencies are in
[consultation-and-print.md](consultation-and-print.md).
