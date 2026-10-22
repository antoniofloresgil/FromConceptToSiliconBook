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
  `tools/book/ubuntu-packages.lock`.
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
2. Update the image pin and its dependency record, and rebuild the image.
3. Rerun the affected labs and regenerate the retained evidence.
4. Update every chapter sentence that names the old version or relies on its
   behavior, and the recorded environment.
5. Keep the previous baseline's evidence readable until the new one passes.

Review the upstream releases of the tools the book names once a year, before the
course is offered. Adopt a new release only when step 1 applies; staying on a
validated baseline is a normal outcome.

## Course editions

Students need text that does not shift during the term. The following is the
adopted policy; the automation it mentions is not yet built.

- **Freeze.** Before a term, choose a validated commit on `main` (all checks
  pass, release built) and tag it `course-YYYY-YY`. Keep that tag for the life
  of the repository.
- **Offer.** The PDF built from the tagged commit is the stable download for that
  course. Its build manifest identifies the revision, so a page number a student
  cites can be matched to a version.
- **Corrections during the term.** Only fixes that do not change meaning (typos,
  broken links, a wrong number backed by regenerated evidence) go into the
  frozen edition. Anything else waits for the next edition.
- **The live HTML.** The published site follows `main`. Until an
  edition-specific site exists, it may differ from the tagged PDF. Tell students
  which one the course uses, and cite section identifiers (`sec-…`) rather than
  page numbers when pointing at the HTML.

### Open decision

Serving the HTML of a tagged edition separately from `main` needs a second
deployment target and has not been decided. Until it is, the tagged PDF and the
release archive are the only stable form of an edition.
