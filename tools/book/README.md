# Reproducible book publishing

Use the commands in [the publication appendix](../../appendices/reproducible-labs.qmd#sec-reproducible-publication) from the full repository root. The laboratory ZIP is not a book source release.

The builder uses Linux/amd64, a digest-pinned Ubuntu base and a digest-pinned BusyBox download stage. `ubuntu-packages.lock` contains the complete set of 134 additional Debian packages resolved on 2026-10-14 from signed Ubuntu repositories against that base. Each line retains APT's URL, filename, byte count and SHA-256. The fetcher verifies SHA-256 before local installation; it does not resolve dependencies from live package indexes. Quarto 1.10.19 has its own fixed download checksum in the Dockerfile.

The image includes Python 3.12, pypdf, LuaLaTeX/TeX Live 2023, DejaVu fonts and librsvg's `rsvg-convert`. Rendering is offline, runs with the caller's UID/GID on Linux, and uses writable temporary font/TeX caches. SVGs are checked and converted to vector PDFs; the original diagrams remain the HTML figures. Build outputs and diagnostics are isolated from old renders.

The [editorial identity](../../design/identity/README.md) supplies the HTML cover,
palette and type hierarchy, plus PDF front/back covers and DejaVu fonts. The
pre-render hook verifies the selected artwork and generated-source freshness,
then creates page-sized cover PDFs under the snapshot's `.quarto/identity/`.
No network font or image generation is needed. The PDF retains its interior
title page and adds a half-title and licensing page. The Preface precedes the
reduced contents; Roman preliminaries switch to Arabic labels at Introduction.
Page dimensions/margins and numbered contents depth come from
`design/identity/pdf-layout.json`. PDF template partials suppress the automatic
title/contents placement; `pdf-structure.lua` inserts the contents in the source
chapter sequence without changing HTML navigation. Release validation checks
front/back cover text, dimensions and preliminary ordering/page labels.
The [template guide](../../styles/README.md) documents the separate PDF/HTML
rule templates, independent front matter and component preview.
Run `python tools/design/identity.py` after editing its templates, palette or generator;
`--check` rejects stale generated SVG/SCSS/TeX. Cover preparation does not edit
the source attachment. New styles require a fresh HTML/PDF and grayscale review.

The repeated **Wally Connection** callouts also require Font Awesome in Quarto's PDF template, even with icons disabled. The image installs Font Awesome 5.15.4 from the versioned TeX Live 2023 archive `fontawesome5.r63207.tar.xz`, verifying SHA-256 `4d85aab86f679d360e7c7c812a055d9c03dd658e31bccfca4a97604497b0cc1c`. This additional TeX package is recorded under `extra_tex_packages` in the build manifest. Its fonts/package retain their upstream licenses; rendering needs no live TeX downloads.

For an independently managed native TeX installation, ensure the `fontawesome5` package is present before PDF rendering (`tlmgr install fontawesome5` for a compatible TeX Live/TinyTeX installation, or the MiKTeX package manager). This is an installation template; the pinned container remains the recorded publication environment.

`test_build.py` checks that failed renders preserve the previous release and that old PDFs cannot satisfy a new build. `build.py` checks all chapter/appendix outputs, the PDF, the lab archive and the HTML download link. Successful builds publish `_book/release` and preserve the previous edition in a separate directory. If an open Windows PDF prevents renaming the previous directory, the builder publishes a complete `release-<id>` instead and prints its path. `test_publish.py` checks previous-edition preservation, locked-PDF fallback and rollback. Each release includes `build-manifest.json` with source/output identities and tool/package versions. The GitHub workflow links that manifest to the same workflow run that validated the labs. A local render alone is an artifact check, not laboratory validation.

Toolchain updates are deliberate source changes: resolve a fresh dependency closure using authenticated APT metadata against the chosen base, retain SHA-256 URI records, update any changed base/fetcher/Quarto identities, and run both the regression checks and a full offline book render. Review the lock diff and installed package manifest. Never silently replace an unavailable locked package with a newer version. Preserve the completed image with `docker save` for long-term course archival; the package snapshot is a fallback rather than the primary build service.

GitHub Actions are pinned by commit. `publish.yml` runs the reusable lab workflow, builds the book only after it succeeds, and deploys only a successful `main` release. Pull requests build without publishing. The PDF and manifest are also uploaded as a separate Actions artifact.

The source snapshot ordinarily excludes generated waveforms. The exact files in
`tools/book/retained-resources.json` are explicit, reviewed exceptions for retained
publication inputs. The formal counterexample SVG rereads its immutable audit VCD,
and the release supplies that trace as a download. Undeclared simulation outputs
remain excluded; a missing declared input fails the build. Source identities remain
in the build manifest, and rendering the illustration does not rerun the proof.
