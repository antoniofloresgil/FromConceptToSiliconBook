# Development conventions

Architectural decisions live in [architecture.md](architecture.md); participation,
navigation and visual requirements live in [accessibility.md](accessibility.md).
This guide identifies source ownership and maintenance procedures rather than
duplicating those decisions or the executable recipes.

## Authoritative sources

| Change | Source to inspect or update |
| --- | --- |
| Book order, formats, resources, date and PDF download | [`_quarto.yml`](../_quarto.yml); retain `date: today` and the HTML PDF-download entry |
| Activity IDs, visible role/compute labels and activity CSV | [`learning-paths.json`](../tools/book/learning-paths.json) and [`learning_paths.py`](../tools/book/learning_paths.py) |
| Glossary, term/lab indexes and experiment matrix | [`reference-data.json`](../tools/book/reference-data.json) and [`reference.py`](../tools/book/reference.py) |
| Runnable chapter listings and lab catalogue | [`catalog.py`](../labs/tools/catalog.py), referenced QMD listings and lab source files |
| Shell recipes, simulation/implementation interfaces and output namespaces | [`recipe-contracts.json`](../labs/recipe-contracts.json) and [`check_recipes.py`](../labs/tools/check_recipes.py) |
| Required project evidence and completeness | [`project-plan.json`](../labs/verification/project-plan.json) and the evidence collector in that directory |
| Fast hardware interface, lint/tool policy and synthesis budget | Lab 25's [`contract.json`](../labs/25-hardware-ci/contract.json), [`policy.json`](../labs/25-hardware-ci/policy.json), runner and README |
| Figure source, provenance and visual review | SVG/generators, [`print-review.json`](../tools/figures/print-review.json), `NOTICE.md` and the [review procedure](consultation-and-print.md) |
| Publication environment | [`tools/book/Dockerfile`](../tools/book/Dockerfile), package lock and [publisher guide](../tools/book/README.md) |

Do not duplicate tool pins, release hashes, report metrics, lab counts or page
numbers in project-knowledge files. Read the corresponding manifest, catalogue
or reference report. A lab README and executable recipe resolve tool-specific
details; do not infer its actual tools from a broad book discussion.

## Editing and execution

- Use UTF-8 and LF according to `.editorconfig`/`.gitattributes`; Windows command
  scripts have their declared CRLF exception. `labs/** -text` preserves exact
  source/evidence bytes for hashes across Windows and Linux. Do not normalize
  these files as an incidental formatting change.
- Keep chapter listings and executable references synchronized. Review the
  authoritative edit before using `labs/run.py sync`; never use synchronization
  to conceal a mismatch. Student variants belong under `labs/work/`.
- The simulation and implementation accumulators have different interfaces.
  Respect each RTL top's clock/reset/data ports and matching constraints; inspect
  the recipe contract before reusing a testbench or physical configuration.
- Run documented recipes from the repository or extracted-package root as
  specified. Use shell-specific commands: Bash/WSL UID/GID options are not native
  PowerShell syntax. On Linux, match output ownership and provide a writable
  container home. Reference execution/rendering is offline after acquisition.
- External Wally sources, technology views and optional tool environments have
  their own identities and licenses. Use the documented pinned acquisition and
  isolated build directories rather than silently substituting a local checkout
  or repurposing another platform's fixture.
- Read `LICENSE.md` and `NOTICE.md` when adding or deriving assets. Original
  educational prose/figures and software have different license scopes; imported
  assets retain their stated exceptions.

## Validation and publication

Use checks appropriate to the changed inputs. For listings or recipes, run
`python labs/run.py check` and `python labs/tools/check_recipes.py`, then the
affected simulations/proofs/synthesis or platform regression. For consultation
and figure changes, follow [consultation-and-print.md](consultation-and-print.md).
When packaging changes, run `python labs/tools/test_package.py` to test the actual
extracted ZIP without chapter sources. A report verifier alone is not a rerun.

For publication changes, use the pinned book environment and its builder/tests
as documented in [tools/book/README.md](../tools/book/README.md). Review a fresh
HTML/PDF release, local links, reference destinations and relevant visual pages.
Preserve previous/open PDFs and failure rollback. Toolchain updates require
reviewed dependency locks, environment identity and fresh applicable validation.

Keep generated HTML/PDF, `downloads/`, `_book/` and local build/work outputs out of
commits. Retained, deliberately versioned `labs/*/reference/` evidence is a
different category: update it through its documented collection/integrity process.
Preserve unrelated working-tree changes, including existing untracked renders.
The current automatic lab set, CI tiers and separate output directories are
defined by the catalogue/contracts/workflows, not by an assumed `run all` scope.
