# Reproducible book publishing

Use the commands in [the publication appendix](../../appendices/reproducible-labs.qmd#sec-reproducible-publication) from the full repository root. The laboratory ZIP is not a book source release.

The builder uses Linux/amd64, a digest-pinned Ubuntu base and a digest-pinned BusyBox download stage. `ubuntu-packages.lock` contains the complete set of 134 additional Debian packages resolved on 2026-10-14 from signed Ubuntu repositories against that base. Each line retains APT's URL, filename, byte count and SHA-256. The fetcher verifies SHA-256 before local installation; it does not resolve dependencies from live package indexes. Quarto 1.10.19 has its own fixed download checksum in the Dockerfile.

The image includes Python 3.12, pypdf, LuaLaTeX/TeX Live 2023, DejaVu fonts and librsvg's `rsvg-convert`. Rendering is offline, runs with the caller's UID/GID on Linux, and uses writable temporary font/TeX caches. SVGs are checked and converted to vector PDFs; the original diagrams remain the HTML figures. Build outputs and diagnostics are isolated from old renders.

`test_build.py` checks that failed renders preserve the previous release and that old PDFs cannot satisfy a new build. `build.py` checks all chapter/appendix outputs, the PDF, the lab archive and the HTML download link. Successful builds replace `_book/release` and include `build-manifest.json` with source/output identities and tool/package versions. The GitHub workflow links that manifest to the same workflow run that validated the labs. A local render alone is an artifact check, not laboratory validation.

Toolchain updates are deliberate source changes: resolve a fresh dependency closure using authenticated APT metadata against the chosen base, retain SHA-256 URI records, update any changed base/fetcher/Quarto identities, and run both the regression checks and a full offline book render. Review the lock diff and installed package manifest. Never silently replace an unavailable locked package with a newer version. Preserve the completed image with `docker save` for long-term course archival; the package snapshot is a fallback rather than the primary build service.

GitHub Actions are pinned by commit. `publish.yml` runs the reusable lab workflow, builds the book only after it succeeds, and deploys only a successful `main` release. Pull requests build without publishing. The PDF and manifest are also uploaded as a separate Actions artifact.
