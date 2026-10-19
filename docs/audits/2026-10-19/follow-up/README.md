# Follow-up: Wally RTL Linux and complete book publication

Both checks requested after the [initial audit](../README.md) completed
successfully. Codex executed this follow-up on 19 October 2026; it remains an
agent-executed container audit, not an independent human review.

## Source and environment boundaries

The RTL experiment uses the unchanged public book revision
`ee1fc8ed9e9d132247846379fb634be16377b559` from the initial audit's read-only
source volume. Wally was acquired separately from the public fork at
`3b30ba6b6519bd2c26c1437e6d61f632a35cef6c`, in a fresh read-only checkout.
The existing user Wally checkout/container was not used or modified.

The Wally lab image was built without cached layers on the lab base already
rebuilt in the initial cold audit, using the documented `LAB_BASE` override.
The book image was rebuilt with `--no-cache --pull` from its digest-pinned bases
and checksum-locked dependencies. Actual image identities, commands, exit codes
and full logs are in [the receipts](evidence/commands.json). Execution/rendering
ran without network access.

Publication checks use the current working-tree book, including the initial
audit's editorial changes. The build manifest explicitly records a dirty tree;
this is a checked local preview, not a deployment or a claim that these edits
already belong to the public commit. Its source hashes were verified before
adding this follow-up record and updating the repository audit protocol.

## Actual Wally RTL Linux result

Preparation, RTL compilation, the separate GPIO/MMIO/DMA preflight, Linux boot
and the userspace regression all pass. The run requires actual CPU/UART
checkpoints, including `HSD_LINUX_ACCEL_PASS` and `WALLY_LINUX_ACCEL_PASS`.
IRQ and polling each pass lengths 1, 8, 32, 128 and 256, with exact arithmetic,
DMA traffic and invalid-argument checks. The run command took approximately
26.7 minutes on this shared host; that is an observation, not a resource or
performance guarantee.

The Linux run completed **99,358,876 cycles from reset**, including firmware,
kernel and the entire application regression. The preflight is a separate reset
run. The software bundle matches the fresh passing QEMU run byte for byte.
The collector verified the bundle, compiled simulator/source identities,
private patches, boot inputs and address map without publishing references.

The original and patched Wally RTL/configuration inventories match the
historical reference exactly. The newly rebuilt kernel and initramfs do not
match the historical binary hashes, as established in the initial audit;
kernel configuration and OpenSBI do match. Historical boot completion was
99,362,109 cycles, and the new measurement rows also differ. This follow-up
therefore establishes functional reproduction with the freshly built bundle,
not identical historical boot performance. No reference value or acceptance
threshold was replaced.

All 992 tracked upstream file/symlink entries remain unchanged; ten unpopulated
gitlinks are recorded by commit and were not used by the RTL export. All 237
exported original files were checked against the fresh checkout. The original
1,312 book source files, including its 899 retained references, also remain
unchanged. The five platform-map regressions pass, including rejection of the
native GPIO address collision and source/profile drift.

This executes real Wally RV64/Sv39 RTL with D-cache enabled, the declared uncached
DMA pool and behavioral shared RAM. QEMU-only fault injection is not an RTL
fault-recovery result; neither environment qualifies an implemented FPGA/DDR
memory fabric or physical timing/power.

## Complete HTML/PDF result

The fresh environment passes 17 publisher/navigation unit tests and listing
provenance checks. The complete offline render produces 47 HTML documents and a
**782-page PDF**, dated 2026-10-19. The verified release is locally at
`_book/release-ebdd44c5be/`. The previous PDF was open, so the publisher used its
documented alternate-directory behavior and preserved the previous edition.

The [publication review](evidence/publication-final-review.json) confirms:

- All 283 output hashes and 1,577 captured source hashes match their actual files
  at validation time.
- All 8,495 local HTML `href`/`src` references checked have existing targets and,
  for HTML fragments, valid anchors.
- The PDF's 3,320 link annotations contain no invalid internal page destinations.
  External URLs were not fetched; browser JavaScript behavior was not tested.
- Glossary, term/lab indexes, experiment matrix and the new audit section appear
  in the PDF. No unresolved printed `p.??` page reference was found.

Grayscale proofs locate all 46 figure placements across 46 pages, covering
44 assets. All six contact sheets and eight full-page samples were visually
inspected. The samples include cover, contents, consultation indexes, appendix C,
CDC and an enlarged pipeline view. No clipping or missing diagrams was apparent
in those inspections; contents entries `24.10` and `24.11` retain proper spacing.
The declared small-label exception for the dense Wally overview remains, with
its three enlarged detail views. Physical GUI captures remain geometry overviews
supported by numerical reports. This is not an independent human print or full
accessibility certification. See [visual notes](evidence/visual-review-notes.json).

## Corrections and retained evidence

The first render correctly failed its pre-render label check: an earlier
Windows edit in the initial audit had damaged two Unicode lines in appendix C.
The encoding was corrected, the canonical 229-activity label check passed, and
the complete render was rerun successfully. This required no RTL, laboratory
reference, dependency-lock or activity-classification change.

The initial audit preparation helper also had CRLF shell lines and tried to
inventory uninitialized gitlinks as ordinary files. Its preliminary checks were
not accepted even though its last shell command returned zero. A corrected
Python helper inventories external file/symlink entries and gitlink IDs
separately, then runs the unchanged lab stages in a fresh output directory.
The initial compile attempt correctly rejected the mismatched output path.
Failed/invalid attempts are retained with their
[successful replacements identified](evidence/command-dispositions.json).

Key evidence:

- [Wally final acceptance](evidence/raw/audit-wally-final-checks.json),
  [combined QEMU/Wally collection](evidence/raw/audit-wally-collection.json),
  [raw Wally report](evidence/raw/audit-wally-rtl/report.json),
  [UART](evidence/raw/audit-wally-rtl/uart.txt) and
  [preflight](evidence/raw/audit-wally-rtl/smoke.txt).
- [Book build manifest](evidence/book-build-manifest.json),
  [publication checks](evidence/publication-final-review.json),
  [figure inventory](evidence/figure-inventory.json) and
  [visual sample pages](evidence/visual-sample-pages.json).
- [Command receipts](evidence/commands.json), logs under `evidence/commands/`,
  [raw export index](evidence/raw/raw-index.json) and
  [retained-file hash inventory](evidence/inventory.json).

Large binaries, boot hex files, simulator builds and generated book/proof images
are deliberately not versioned here. Their identities were checked before
export; the compact evidence cannot alone rerun all binary integrity checks.
Full Wally results remain in the original results volume under
`labs/build/audit-wally-rtl/`, and its external checkout is in
`from-concept-audit-wally-source-20261019`. Local harness/logs and grayscale proofs
remain under ignored `labs/build/repro-followup-20261019/`.

The maintained audit protocol now includes the optional advanced Wally and
publication boundaries and documents the gitlink inventory limit. Run-specific
measurements remain in these audit records; no architectural decision or
accessibility requirement changed. Physical boards, fabrication qualification,
bit-identical Linux rebuilding, the other guided extensions and independent
human review remain outside this follow-up.
