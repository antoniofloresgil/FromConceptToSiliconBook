# Consultation and print maintenance procedure

Source ownership and navigation decisions are maintained in
[architecture.md](architecture.md#consultation-data-and-generated-pages).
Participation, link and figure requirements are maintained in
[accessibility.md](accessibility.md). The [development guide](development.md)
identifies the source catalogues, contracts and environment instructions.
This page describes how to regenerate and review the affected outputs.

## Update consultation material

Edit the reviewed reference data for terms, destinations and dependency profiles;
edit the learning-path catalogue for activity identities and classifications.
Then run from the repository root:

```sh
python tools/book/learning_paths.py --check
python tools/book/reference.py --write
python tools/book/test_reference.py
```

Review the generated QMD diff. Regenerate activity labels with the learning-path
tool when their authoritative catalogue changes. The pre-render hook and CI check
catalogue coverage and generated-page freshness; the downloadable CSVs are
generated during this process. Consult each tool's `--help` for its options.

Build a fresh HTML/PDF release using the
[pinned publication environment](../tools/book/README.md). Check term and activity
destinations, PDF page references, alphabetic group headings, matrix table breaks,
HTML local navigation and the printed contents. Verify that technical chapter and
appendix numbering remains consistent with the navigation policy.

## Regenerate and check figures

For generated artwork, edit its maintained generator and regenerate the affected
assets and provenance together. The relevant source/generator is identified in
the [figure guide](../tools/figures/README.md) or asset manifest. Example checks:

```sh
python tools/figures/architecture.py --check
python tools/figures/visual_language.py --check
python tools/figures/async_fifo.py --check
python tools/figures/reusable_ip.py --check
python -m unittest discover -s tools/figures -p 'test_*.py'
python tools/figures/print_details.py --check
python tools/figures/print_audit.py --check
```

The source audit inventories embedded Markdown figures and screens vector font
sizes. Apply the review requirements in `accessibility.md` before updating
`tools/figures/print-review.json`; inspect a changed asset rather than merely
refreshing its hash. Review any license/attribution exception in `NOTICE.md` when
working on a derived detail view.

## Produce grayscale inspection artifacts

For the optional proof generator, install `PyMuPDF==1.26.5` and `Pillow==11.3.0`
in a separate environment. They are not dependencies of the ordinary book build
or lab runner. Run:

```sh
python tools/figures/print_audit.py --check \
  --pdf _book/release/From-Concept-to-Silicon.pdf \
  --output labs/build/figure-print-audit
```

Use the actual immutable release path if the builder reports a preserved
`release-<id>` directory. The tool finds caption pages and writes a grayscale
proof PDF, contact sheets, inventories and the input PDF hash under the selected
output directory. Use contact sheets to find layout problems, then inspect the
actual pages at print size and open full-resolution sources for dense details.
These ignored inspection artifacts do not replace the book's original images.

After a substantive review, update the relevant permanent requirements or
decisions only if they have changed. Keep run-specific measurements, hashes and
page counts in the generated audit/release artifacts, rather than copying them
into project-knowledge documents.
