# Verification plans and scoped evidence

Read the book's [methodology chapter](../../chapters/03-simulation-verification/verification-methodology.qmd).
`project-plan.json` maps the existing dot-product tests to requirements; it also
keeps unexecuted equivalence, measured coverage, physical and production-test
obligations visible. `plan-template.json` starts a different reviewed plan.

After running `all` (or `dotproduct`) and the external `dotproduct-wally` entry:

```sh
python labs/verification/evidence.py \
  --unit-report labs/build/report.json \
  --system-report labs/build/wally-platform/report.json \
  --output labs/build/verification-evidence.json
```

The generator checks referenced sources, recorded artifacts/logs, command exit
codes and expected completion markers. It records environment, seed, input-plan
and report hashes with requirement-level statuses. A missing required system
report, stale source/artifact or failed check returns nonzero. Unknown/unrun
checks are not converted into passes. The tool itself does not run simulation,
formal, STA or physical checkers. A trusted report's artifact paths are relative
to the extracted package/repository; `/work` in recorded commands denotes the
container environment. Do not execute recorded shell commands automatically.

Reference plans require reference RTL. Student overrides need a reviewed plan
and explicit variant identity; they cannot be accepted under this reference
claim merely by using the same top-module name. Preserve original evidence for
each run; overwriting build artifacts invalidates old report hashes.

Coverage entries describe obligations and test boundaries. They do not report
measured functional bin/cross coverage, an ISA retirement comparison, a full
formal proof or a fabrication qualification. N/A records require a scoped
reason. Physical and DFT checks require their actual tools, decks/models and
input artifacts; the simulation container cannot supply those results.
