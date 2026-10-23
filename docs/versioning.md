# Versioning and editions

How the book, its executable evidence and the tools it names are versioned, and
how a stable edition is offered to a course. Architectural decisions live in
[architecture.md](architecture.md); build and validation commands live in
[development.md](development.md).

## What identifies a version

- **Book revision.** The Git commit recorded in `build-manifest.json` by
  `tools/book/build.py`, together with whether tracked sources were modified. A
  local build with modified sources is a preview, not a published revision.
- **Environment.** Tool images carry a year.month tag (for example
  `from-concept-labs:2026.10`) and a recorded image identity. The validated
  versions of the laboratory tools are in `labs/validated-environment.json`, and
  the publishing toolchain is pinned by `tools/book/Dockerfile` and
  `tools/book/ubuntu-packages.lock`. The pins that several files repeat have one
  source, `tools/environments/environments.json`.
- **Evidence.** Reference results under `labs/*/reference/` belong to the source,
  tool and configuration that produced them. A changed input makes a new
  candidate with its own evidence; reference results are never edited to match.

## Kinds of change

| Change | Examples | What it requires |
| --- | --- | --- |
| Editorial | Tone, typos, clearer explanation | Catalogue checks, a render, and a read-through. No rerun. |
| Contract | A claim, a number, a recipe, a scope boundary | The affected experiment or check is rerun and its evidence regenerated first; then the text follows the evidence. |
| Structural | Splitting or moving chapters, renaming sections | Catalogues and generated indexes regenerated, then every internal link in the rendered HTML checked. Keep existing section identifiers so references and citations keep working. |
| Tool version | A new Verilator, OpenROAD, Yosys, cocotb or base image | See the next section. |

## Tool versions

The versions named in the book (for example Verilator 5.020, Icarus 12.0,
cocotb 2.0.1, Yosys 0.60 and the recorded OpenROAD build) are reproduced baselines,
not a promise about newer releases. A version changes only as a deliberate
source change:

1. State why (a defect, an end of support, a needed feature).
2. Change the value in `tools/environments/environments.json` and run
   `python tools/environments/sync.py write`; it rewrites the Dockerfiles,
   workflows, manifests and lab code that repeat it. Then update the dependency
   record of a pin the manifest does not cover, and rebuild the image.
3. Rerun the affected labs and regenerate the retained evidence. The sync leaves
   recorded evidence as it was, so the old results stay readable until the new
   ones pass.
4. Update every chapter sentence that names the old version or relies on its
   behavior, and the recorded environment. `sync.py write` lists the sentences it
   found for the tools it covers, plus the bibliography entries that still cite
   the old version; reread each one against the new baseline, since a changed
   version can also change the claim and an entry may deliberately keep citing
   the documentation of the version that was validated.
5. Keep the previous baseline's evidence readable until the new one passes.

Review the upstream releases of the tools the book names once a year, before the
course is offered. Adopt a new release only when step 1 applies; staying on a
validated baseline is a normal outcome.

## Editions: the live web edition and the course edition

The **HTML edition is the reference and stays live**: it follows `main`, so a
correction reaches every reader without a download. It is not frozen. What a
course needs fixed is the text it cites, and that is the PDF.

- **Live HTML.** Every page ends with a note naming the revision and build date,
  so a reader always knows which build they are reading; a build from modified
  sources is marked as a preview. Cite sections by their identifiers (`sec-…`),
  which stay stable when text is corrected or moved, and not by page number.
- **Course PDF.** Before a term, choose a validated commit on `main` (all checks
  pass, release built) and tag it `course-YYYY-YY`. Keep that tag for the life of
  the repository. The PDF built from it is the dated edition for that course; its
  build manifest identifies the revision, so a cited page can be matched to a
  version.
- **Corrections during the term.** They reach the live HTML at once. A fix that
  does not change meaning (typo, broken link, a number backed by regenerated
  evidence) can also go into a new build of the course PDF; anything else waits
  for the next edition. Changes that alter an assigned exercise are announced to
  the course.

The tag and the release PDF are made by hand for now; no automation creates them.
There is no separate frozen copy of the HTML: it would need a second deployment
per course, and the revision note and stable identifiers address the same need.
