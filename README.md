# From Concept to Silicon

An English-language reference for open-source hardware system design, from reusable SystemVerilog RTL and RISC-V architecture to verification, FPGA implementation and ASIC implementation. **CORE-V Wally** is the main processor case study. Students, instructors and independent engineers can follow the Foundations, Complete SoC or ASIC Design route.

The [learning-path guide](learning-paths.qmd) distinguishes the bounded Core Learning Path from Advanced Reference activities and labels experiments by role and compute cost. The separate [Hardware System Design adoption](appendices/hsd-coursework.qmd) preserves its 6 ECTS, twelve-week schedule, RA5–RA8 outcomes and assessment proposals. A Wally-controlled AXI/DMA dot-product accelerator connects the reference material across routes.

## Read and navigate

- [Read the published HTML book](https://antoniofloresgil.github.io/FromConceptToSiliconBook/). The sidebar offers the complete PDF when a validated release has been published.
- [Choose a route and experiment budget](learning-paths.qmd): technical routes, Core/Advanced selection and compute classes C0–C3.
- Consult the [glossary](glossary.qmd), [term index](term-index.qmd), [laboratory index](lab-index.qmd) or [experiment/tool/requirement matrix](experiment-index.qmd); the matrix also downloads as CSV.
- [Coursework and assessment guide](appendices/hsd-coursework.qmd): P0–P5 activities, 12-week workload, review milestones and rubrics.
- [Executable project](appendices/executable-project.qmd) and [reference source guide](labs/10-dotproduct/README.md): arithmetic IP, AXI4-Lite control, bounded AXI4 DMA and real Wally firmware.
- [Complete case study](appendices/complete-case-study.qmd): the same locked RTL through verification, Wally simulation, FPGA placement and routing, and ASIC GDSII, with measured results and physical views.
- [Reproduction appendix](appendices/reproducible-labs.qmd): detailed environments, external repositories and guided physical flows.
- [Boot and software stack](chapters/04-soc-architecture/boot-software-stack.qmd): reset to Linux, with an [optional executable QEMU/OpenSBI practice](labs/12-boot/README.md).
- [Vector processing](chapters/07-advanced-topics/vector-processing.qmd): RVV concepts and an [executable dot-product/mask practice](labs/13-vector/README.md), before choosing custom ISA or AXI/DMA acceleration.
- [Hardware security](chapters/07-advanced-topics/hardware-security.qmd): a system threat model and [five scoped protection experiments](labs/14-security/README.md), connecting boot, CPU isolation, DMA, debug and physical risks.
- [Final project review](summary.qmd): expected evidence, release decisions and defence questions.

Read the blocks in order: Foundations; RISC-V Cores; Simulation and Verification; SoC Architecture; FPGA Implementation; ASIC Implementation; Advanced Topics. Each technical chapter separates Concepts, Implementation and Hands-on Experiments. **Checked recipes**, **adaptation templates** and **exercises** describe different levels of completeness; simulation, synthesis and physical qualification are distinct claims.

## Download and prepare the environment

Install [Git](https://git-scm.com/downloads) and [Docker](https://docs.docker.com/get-started/get-docker/). On Windows, use Docker Desktop with **Linux containers**, then choose either PowerShell with a Windows checkout or a Linux shell with a WSL checkout. Use the command block for that shell consistently. Linux users need access to the Docker daemon with their normal account.

Clone the repository and run all commands below from its root:

```sh
git clone https://github.com/antoniofloresgil/FromConceptToSiliconBook.git
cd FromConceptToSiliconBook
git rev-parse HEAD
docker version
```

Record the commit for your submission. To reproduce an archived course release, check out the exact commit assigned by the instructor. A GitHub source ZIP can build the book but cannot provide Git revision metadata. The smaller laboratory ZIP contains only practices, executable examples, guides, licenses and integrity/provenance manifests: it omits chapter/appendix text, book figures, bibliography and publishing tools. Its root README explains standalone execution; read the HTML/PDF book separately.

Two separate Linux/amd64 environments are provided. Building images requires network access, several gigabytes of available storage and several minutes on a fresh machine. The reference runs and book rendering below execute without network access. Native Quarto, LaTeX, `rsvg-convert`, HDL simulators and Python are not required when using these containers. An optional native Python 3.10+ installation supports authoring utilities; it does not replace the hardware toolchain.

| Image | Purpose | Version/evidence boundary |
| --- | --- | --- |
| `from-concept-book:2026.10` | HTML/PDF publication, vector figures and lab ZIP | Digest-pinned bases, hash-locked Ubuntu packages and Quarto 1.10.19; [builder details](tools/book/README.md) |
| `from-concept-labs:2026.10` | Nine automatic simulation, synthesis and bounded-check reference labs | Tool baseline in [validated-environment.json](labs/validated-environment.json); record your actual image/tool identities |

Build the images you need. These commands work in PowerShell and Linux shells:

```sh
docker build --platform linux/amd64 -f tools/book/Dockerfile -t from-concept-book:2026.10 .
docker build --platform linux/amd64 -f labs/Dockerfile -t from-concept-labs:2026.10 .
```

## Build and read the complete book locally

On Linux or WSL, match the host UID/GID so generated files remain writable by your account:

```bash
image_id=$(docker image inspect --format '{{.Id}}' from-concept-book:2026.10)
docker run --rm --platform linux/amd64 --network none \
  --user "$(id -u):$(id -g)" --env HOME=/tmp --env BOOK_IMAGE_ID="$image_id" \
  --mount "type=bind,source=$PWD,target=/work" from-concept-book:2026.10
```

On Windows PowerShell, the bind mount uses Windows access controls:

```powershell
$imageId = docker image inspect --format '{{.Id}}' from-concept-book:2026.10
docker run --rm --platform linux/amd64 --network none --env HOME=/tmp `
  --env "BOOK_IMAGE_ID=$imageId" `
  --mount "type=bind,source=$PWD,target=/work" from-concept-book:2026.10
```

The builder checks the complete HTML/PDF output and publishes local files only after rendering succeeds. Outputs are `_book/release/index.html`, `_book/release/From-Concept-to-Silicon.pdf`, `_book/release/downloads/hardware-design-labs.zip` and `_book/release/build-manifest.json`. The manifest records sources, outputs and environment identities; local modified sources are identified as a preview. Old renders are excluded from build inputs. PDF metadata timestamps need not be byte-identical between builds.

Open the PDF directly. To read HTML with working navigation/search, serve the generated site on your machine. The following single-line command works in PowerShell and Linux shells; the mount is read-only, and only the loopback interface is published:

```sh
docker run --rm --platform linux/amd64 --publish 127.0.0.1:8000:8000 --env HOME=/tmp --mount "type=bind,source=${PWD},target=/work,readonly" from-concept-book:2026.10 python -m http.server 8000 --bind 0.0.0.0 --directory /work/_book/release
```

Visit <http://localhost:8000/> and stop the server with Ctrl+C.

## Run the reference practices

On Linux or WSL:

```bash
docker run --rm --platform linux/amd64 --network none \
  --user "$(id -u):$(id -g)" --env HOME=/tmp \
  --mount "type=bind,source=$PWD,target=/work" \
  from-concept-labs:2026.10 python labs/run.py run all --seed 2026
```

On Windows PowerShell:

```powershell
docker run --rm --platform linux/amd64 --network none --env HOME=/tmp `
  --mount "type=bind,source=$PWD,target=/work" `
  from-concept-labs:2026.10 python labs/run.py run all --seed 2026
```

`all` runs nine automatic entries, including the standalone dot-product IP. Its result is `labs/build/report.json`, with per-lab logs/artifacts underneath `labs/build/`. Missing tools, failed assertions, timeouts and failing commands return a nonzero status. Replace `run all --seed 2026` with `list`, `doctor` or `check` to inspect the catalog, tools or source-listing consistency; use `run dotproduct --seed 2026` for the standalone final-project reference.

The real Wally run requires a clone of antoniofloresgil/cvw (the fork containing the validated commit, rather than upstream openhwgroup/cvw) containing commit `3b30ba6b6519bd2c26c1437e6d61f632a35cef6c` and a read-only `/cvw` mount. Follow the [project guide](labs/10-dotproduct/README.md), preserving the separate `labs/build/wally-platform/report.json`. It boots firmware on actual Wally RTL; the core uses AHB control accesses through an AXI4-Lite adapter, while the accelerator supplies AXI4 DMA. The reference disables caches and uses a simplified direct interrupt route. A complete PLIC, cached DMA integration and physical implementation need additional evidence.

FPGA boards, device databases, PDKs, OpenROAD/LibreLane installations and Spike/Sail are separate guided dependencies, not automatic-suite prerequisites. See the [lab catalog](labs/README.md), [DSE guide](labs/11-dse/README.md) and reproduction appendix for their exact scopes. Keep student RTL in `labs/work/` or a separate branch; `labs/run.py sync` and book packaging regenerate exported reference listings.

## Repository map and publication

| Path | Role |
| --- | --- |
| `_quarto.yml`, `index.qmd`, `intro.qmd`, `learning-paths.qmd`, `summary.qmd` | Book structure, technical routes, experiment budgets and final review |
| `chapters/`, `appendices/`, `references.bib` | Teaching text, coursework, technical appendices and bibliography |
| `figures/`, `examples/` | Vector illustrations and standalone chapter examples |
| `labs/` | Runnable references, tests, formal harnesses, firmware and evidence tools |
| `tools/book/`, `.github/workflows/` | Publishing environment and validation/build/deployment chain |
| `_book/`, `downloads/`, `labs/build/`, `labs/work/` | Local generated outputs or student variants; excluded from commits |

Pushes to `main` publish only after the reusable lab workflow and offline book build succeed for the same commit. Pull requests validate/build without deploying; manual publication does not bypass the gate. Configure GitHub Pages to use **GitHub Actions**. Actions retains lab evidence and a PDF/build-manifest artifact; the published site includes the PDF and practice download. The course's guided physical/manufacturing obligations remain explicit even when automatic CI is green.

If a command fails, inspect its exit status and logs before continuing. For missing Docker/daemon access, resolve installation first. For Linux root-owned outputs, use the narrowly scoped repair in the reproduction appendix; changing the whole checkout's ownership is unnecessary. For an unavailable locked package, preserve the failing URL/checksum and review the builder rather than silently selecting a different version. If port 8000 is occupied, change the host side of `--publish` and the browser URL together. See the appendix for paths containing spaces, image archival and external-tool recipes.

## Reuse and contributions

Original book text and original figures use **CC BY-SA 4.0**; original software and executable code listings use **MIT**. See [LICENSE.md](LICENSE.md), the full texts in `LICENSES/` and [third-party notices](NOTICE.md). The Harris Figure 7.13 asset and external projects retain their own rights; citation does not relicense them.

For corrections or contributions, identify the affected chapter/requirement, describe the change and attach relevant reproducible evidence. Preserve source attributions and distinguish measured results from illustrative data. Changes to chapter-exported RTL must keep reference listings and tests consistent; new physical or performance claims need their own configuration and result records.
