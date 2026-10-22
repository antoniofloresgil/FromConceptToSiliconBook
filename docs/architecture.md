# Maintained architectural decisions

## Book and teaching adoption

The English-language book is a general open-SoC reference. Foundations, Complete
SoC and ASIC Design are technical entry routes. Core/Advanced activity roles and
P0–P5 milestones describe the optional twelve-week teaching adoption, whose
institutional outcomes and assessment details live in Appendix D. Keep these
identities separate without maintaining different versions of the technical RTL.

SystemVerilog remains the primary implementation language, with CORE-V Wally as
the main processor/SoC case. Chisel/FIRRTL/CIRCT is a supplemental generator
comparison, not a replacement for the main RTL flow or a claim of automatic
equivalence. Formal verification has its own chapter in Part III; required
course work uses small IP properties and explicit reachability obligations.
Whole-processor formal verification is an advanced extension.

Multicore integration is advanced material in Part VII, between accelerators and
architectural exploration. RVV, deeper PMU/security studies, larger Linux/RTL
campaigns and extended physical closure are selections for the Advanced Reference
Path. Basic formal verification and security evaluation remain part of the Core
adoption. New extensions must not silently increase its compulsory workload.
The approved course identity and the proposed workload/rubric implementation are
distinguished in [Appendix D](../appendices/hsd-coursework.qmd); do not restate
the proposal as an independently approved institutional policy.

Hardware access and provisioning requirements are maintained in
[accessibility.md](accessibility.md). The general routes and Core/Advanced views
share one complete body of technical content.

## Accelerator and platform boundaries

The AXI/DMA dot-product accelerator is the cross-book component. The complete
case study follows a common RTL/firmware/configuration manifest across reference
models, independent tests, formal checks, Wally integration and physical flows.
Lock source identities within a comparison; a changed microarchitecture needs
its own candidate identity, regression and implementation results. Keep failed
baselines and later repairs as separate evidence rather than overwriting history.

The Linux extension has two distinct validation environments: a QEMU device model
for the software-facing path, and advanced Wally RTL integration. Neither stands
in for the other. MMIO, Device Tree, driver, DMA buffers, interrupt handling and
the user application must agree within the selected platform. Emulator timings
do not establish RTL or hardware performance. See
[Lab 18](../labs/18-linux-accelerator/README.md).

The Lab 18 Linux/Wally accelerator uses the dedicated MMIO page at `0x10080000`;
preserve GPIO at `0x10060000`. Check overlap against the selected Wally
configuration, including the complete reserved page, and keep RTL decode,
firmware/driver, Device Tree and map tests synchronized. This is a platform
mapping, not an absolute-address requirement for the reusable IP or every older
fixture. The recorded map is
[`wally-address-map.json`](../labs/18-linux-accelerator/reference/wally-address-map.json).

The Nexys Video implementation target is Artix-7 `xc7a200tsbg484-1`.
The complete-case serial boundary fixture and the full Wally/LiteDRAM FPGA
platform are different designs. ECP5 remains a separately identified target;
do not normalize their resource counts as if they had identical boundaries.
The case study simulates the SoC and physically implements the accelerator
boundary specified by each target profile. Board operation requires its own
evidence. Use the [common manifest](../labs/17-complete-case/manifest.json) and
[Nexys profile](../labs/17-complete-case/nexys-profile.json) for exact inputs.

## Reusable IP and clock-domain contracts

The reusable release separates accelerator RTL from platform adapters, Wally
collateral and physical deliverables. Generate register views from one schema;
declare supported parameters, interface/ABI versions and dependencies. Qualify
the same immutable RTL in the AXI harness and real-Wally integration. Keep build
results outside the release tree; a changed IP is a new release. The authoritative
packaging and qualification contract is [Lab 23](../labs/23-reusable-ip/README.md).

The asynchronous FIFO transfers ownership through registered Gray pointers and
receiving synchronizer stages. Its implemented contract uses a common reset
epoch and a fall-through read memory model. Independent side-only resets or a
synchronous BRAM substitution are not drop-in supported configurations. Legal
parameters and tested configurations are specified in
[Lab 24](../labs/24-async-fifo/README.md). Simulation and synthesized structure
reviews do not establish physical CDC/RDC signoff.

## Reference edition

The HTML edition is the reference edition and stays live; it follows `main` and
shows its revision and build date on every page. The PDF is a dated companion
that readers download for printing and offline use, and it is the form a course
fixes by tagging a commit. Table and figure design is therefore done for the
screen first; PDF legibility is checked against a checklist and does not dictate
how text is written. Do not maintain a separate frozen HTML copy per course. See
[versioning.md](versioning.md).

## Editorial identity

The approved Design Flow identity uses the author's selected, unmodified layered
SoC illustration, a black cover, night blue, cyan and amber accents, and a pale
reading surface. `design/identity/palette.json` owns colors and the DejaVu
Serif/Sans/Sans Mono font choices; `tools/design/identity.py` generates the
editable covers and PDF/HTML styles. Preserve the selected artwork's recorded
identity rather than silently regenerating or retouching it. The illustration
is conceptual cover art, not a validated SoC diagram or implementation capture.

The editorial PDF uses the standard A4 (210 × 297 mm) format, superseding Letter.
`design/identity/pdf-layout.json` owns page dimensions, mirrored margins, text
size and numbered contents depth. An 11 pt body and mirrored 26/24 mm inner/outer
margins preserve a comfortable reading width for RTL and architectural artwork.
Chapter openings need not force empty verso pages. Prepare cover PDFs offline inside the isolated source snapshot,
extending the canvas without distorting or cropping the artwork.

The PDF order is exterior cover, half-title, interior title, credits/license,
Preface, reduced Contents, Introduction and the existing chapter sequence, ending
with the back cover. Preliminaries use Roman page labels; Arabic numbering starts
at Introduction. The contents and collapsed PDF outline retain chapters and main
sections under the parts; all deeper headings and their link destinations remain
in the body. The HTML retains its detailed navigation and uses the same cover and
palette. The PDF-only structure filter relocates the contents without moving or
duplicating the Preface/Introduction source chapters.
Production bleed, spine and press qualification are outside this digital book
edition. Source ownership and preview commands live in
[the identity guide](../design/identity/README.md).

The editorial runtime has three layers: `_quarto.yml` owns metadata, structure,
references and output wiring; `styles/book.tex` owns PDF typography and furniture;
`styles/book.scss` owns the equivalent HTML identity. Their editable rules live
in `styles/templates/`; the identity generator substitutes the shared configuration.
`styles/frontmatter.tex` separately owns covers and preliminaries. Original SVGs
remain in `figures/`, and measured captures retain their lab provenance paths.
A cover change must not require chapter edits. The maintained component specimen
and authoring conventions are described in [styles/README.md](../styles/README.md).

## Consultation data and generated pages

- `tools/book/learning-paths.json` owns stable activity IDs, roles and compute
  classes. Chapter labels are generated and checked against that catalogue.
- `tools/book/reference-data.json` owns glossary definitions, selected term
  destinations, lab dependency profiles and related project requirement IDs.
  `tools/book/reference.py` generates the four consultation QMD pages and matrix
  CSV. Update the source data and regenerate; do not hand edit generated pages.
- Consultation chapters are unnumbered. Preserve technical chapter/appendix
  numbers and existing section URLs when adding reference destinations. Use
  unique extra anchors for repeated headings. PDF references resolve through
  TeX labels; never maintain fixed page numbers manually.
- DP requirement identifiers refer to `labs/verification/project-plan.json`.
  A pedagogical correspondence does not assert completed verification coverage.

## Evidence and publication boundaries

Distinguish analytical examples, model execution, RTL simulation, bounded checks,
unbounded proofs, synthesis, routing, board observations and manufacturing
qualification. Keep assumptions, negative controls, counterexamples and residual
obligations visible. An integrity verifier checks recorded evidence; it does not
rerun the underlying experiment. Document generated scripts, adaptation templates
and student exercises according to their actual completeness.

ASIC timing qualification includes extracted setup **and** hold, electrical
limits and constraint coverage under stated corners and interface budgets.
A lower requested frequency is a revised requirement, and does not by itself
repair hold or electrical failures. DRC/LVS checks apply to the actual layout,
reference netlist and selected decks; FreePDK45/Nangate45 reference results are
not foundry qualification. Lab 22's retained implementation uses KLayout-based
geometry/extraction checks. See the separate contracts in
[Lab 21](../labs/21-physical-closure/README.md) and
[Lab 22](../labs/22-layout-verification/README.md).

Report area, frequency and power with units, technology, boundary, constraints
and measurement/estimation method. Preserve `null` or an explicit unestimated
status where a characterized FPGA power model or measurement is unavailable.
LUT/generic-cell counts are not watts or technology-normalized silicon area.
Vectorless ASIC block power and virtual SoC cycle counts do not establish
whole-system energy per job.

The book builder renders a source snapshot in isolation and preserves validated
immutable releases under `_book/`. Generated source-folder HTML must not satisfy
release validation. Rendering prose does not execute hardware experiments.

The standalone practice ZIP contains executable practices and provenance, not the
book's chapter text or illustrations. Links to omitted QMD documents must target
the published HTML book. Keep that behavior covered by extracted-package tests.

Physical captures and measured reports retain their source identities. An edited
diagram or a grayscale proof is not new implementation evidence. Original
architectural artwork uses editable SVG and maintained generators where present;
special third-party attribution and license exceptions remain in `NOTICE.md`.

Continuous hardware verification uses
`Lint → Elaboration → Simulation → Formal → Synthesis → Reports` as a fast gate.
Contract violations, failed assertions, incomplete stages and unjustified metric
regressions reject a candidate; do not silently loosen warning policies or
thresholds. A source/tool change requires reviewed baselines and fresh evidence.
Full physical regression is a separate, explicitly invoked campaign tied to the
same candidate revision. Publication depends on both the hardware gate and the
broader laboratory workflow. Workflow definitions alone do not demonstrate a
hosted run or enable branch protection. The policies and boundaries live in
[Lab 25](../labs/25-hardware-ci/README.md) and the
[workflow files](../.github/workflows/).

For navigation maintenance and visual-review procedures, see
[consultation-and-print.md](consultation-and-print.md). Accessibility requirements
are maintained separately in [accessibility.md](accessibility.md).

Original schematic figures share labelled, monochrome-readable component marks
from the architectural drawing primitive. Conceptual diagrams, retained-trace
visualizations and experimental captures have distinct evidence categories.
Capture reading panels preserve original image bytes and link to full resolution;
all embedded figures require unique IDs and automatic prose references. Source
ownership and the detailed rules live in [illustrations.md](illustrations.md).
