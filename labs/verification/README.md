# Verification plans and scoped evidence

Read the book's [methodology chapter](../../chapters/03-simulation-verification/verification-methodology.qmd).
`project-plan.json` maps the existing dot-product tests to requirements; it also
keeps unexecuted equivalence, measured coverage, physical and production-test
obligations visible. `plan-template.json` starts a different reviewed plan.

The [complete-case dossier](../17-complete-case/README.md) separately joins the
same dot-product source lock to actual ECP5 IP PnR and Nangate45 IP GDSII,
extracted timing and a vectorless power estimate. Its FPGA target and ASIC
hold/electrical failures remain explicit. The board, equivalence and foundry
qualification rows in this plan stay open; the ordinary collector does not
automatically absorb or qualify the external physical dossier.

The [formal FIFO practice](../15-formal/README.md) supplies a separate executable
induction/equivalence lesson and its own report. Its two-implementation proof
does not close this project's `DP-EQUIV`, which requires an actual
accelerator RTL-to-transformed-netlist correspondence and completed checks.

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

For the [route without an FPGA](../NO-FPGA.md), retain `DP-FPGA` as `not_run`
with a no-board rationale in the reviewed student plan. Keep `DP-TIMING` and
other physical obligations unexecuted unless their actual results are available.
The replacement simulation, synthesis and provided-report analysis can satisfy
the coursework scope without closing physical qualification. Index supplied
reports with their original design/tool/constraint identities separately from
the collector's checked reference evidence. The collector does not automatically
validate a supplied physical report or a live board result.
