# Lab 21 — From Timing Violations to a Qualified Implementation

This explicit, optional continuation implements the **same maximum-256 dot-product block** as [Lab 17](../17-complete-case/README.md). It preserves that common release and its failed physical results. No FPGA purchase or fabrication is required. See the [OpenROAD chapter](../../chapters/06-asic-implementation/openroad-study.qmd#sec-physical-closure) and [case-study continuation](../../appendices/complete-case-study.qmd#sec-complete-closure).

`manifest.json` defines three interventions: a 75 MHz target using the original RTL, a registered-product engine at 100 MHz, and electrical/hold repair of the original ASIC at 100 MHz. The new engine is a separate source file; the original sources remain immutable. The physical repair keeps the original SDC budgets, 45% floorplan utilization, technology and synthesis recipe.

A fresh 100 MHz ASIC baseline is included alongside the slow and repaired candidates. All three must have the same `mapped.v` hash. This runner combines the parameter assignments into one Yosys command; the historical runner used separate assignments, producing different generated names and a different mapped-file identity. Keep the historical dossier, but use the fresh baseline for a controlled comparison of physical interventions. The supplied evidence contains nine completed runs, a separate netlist proof and an expected-failure control.

The reference gate is deliberately scoped. ASIC acceptance requires nonnegative extracted setup/hold, no reported electrical violations or unconstrained-path warnings, an empty final detailed-router DRC report, functional mapped/routed equivalence, and nonempty GDS readback. This is a single Nangate45 typical-corner block experiment. Foundry DRC/LVS, multi-corner signoff, a physically integrated Wally SoC and board qualification remain open. FPGA acceptance here means the requested routed clock passes the nextpnr model; it does not include vendor I/O/CDC/hold signoff, board measurements or power estimation.

## Inspect the preserved results without EDA tools

```bash
python3 labs/21-physical-closure/verify_reference.py
```

`reference/results.json` contains the measured comparison; each candidate directory preserves original reports and exact command logs under `.txt` extensions. The inventory binds those files to source hashes. ODB/SPEF/GDS and large routed FPGA JSON files are generated on reproduction, with their hashes retained in `report.json`.

## Environments

Build the existing Lab 17 FPGA images using its README and the ordinary `labs/Dockerfile` image. There is no new tool download requirement for this continuation. The exact ASIC environment is:

```text
openroad/orfs@sha256:fd3e27cf1788815be526e86fbe449310d1114bf256fd6c7af9dced6eaf12c699
```

The two FPGA environments are `from-concept-case-fpga:2026.10` (ECP5) and `from-concept-case-xc7:2026.10` (Nexys Video). Their Lab 17 build recipes pin the suite/chip database revisions; run reports record actual image identities and tool versions. Nexys continues to use `-nodsp` because this experiment preserves the supported open-flow mapping. FPGA geometry and resource counts refer to different targets: ECP5 is an out-of-context IP, while Nexys includes the existing serial boundary fixture and uses XC7A200T.

## Reproduce all candidates

Run from the repository root. Each output directory must be fresh. The examples use prefix `closure-repeat`; change it consistently for another run. All execution is offline after acquiring/building the images.

Linux/WSL:

```bash
for candidate in baseline pipeline; do
  image=from-concept-labs:2026.10
  identity=$(docker image inspect --format '{{.Id}}' "$image")
  docker run --rm --network none --user "$(id -u):$(id -g)" --env HOME=/tmp --env "CASE_IMAGE_ID=$identity" \
    --mount "type=bind,source=$PWD,target=/work" "$image" \
    python3 labs/21-physical-closure/run.py test --candidate "$candidate" \
    --output-dir "labs/build/closure-repeat-test-$candidate"
done

for target in ecp5 nexys; do
  image=from-concept-case-fpga:2026.10
  if [ "$target" = nexys ]; then image=from-concept-case-xc7:2026.10; fi
  identity=$(docker image inspect --format '{{.Id}}' "$image")
  for candidate in slow pipeline; do
    docker run --rm --network none --user "$(id -u):$(id -g)" --env HOME=/tmp --env "CASE_IMAGE_ID=$identity" \
      --mount "type=bind,source=$PWD,target=/work" "$image" \
      python3 labs/21-physical-closure/run.py "$target" --candidate "$candidate" \
      --output-dir "labs/build/closure-repeat-$target-$candidate"
  done
done

asic=openroad/orfs@sha256:fd3e27cf1788815be526e86fbe449310d1114bf256fd6c7af9dced6eaf12c699
identity=$(docker image inspect --format '{{.Id}}' "$asic")
for candidate in baseline slow repair; do
  docker run --rm --network none --user "$(id -u):$(id -g)" --env HOME=/tmp --env "CASE_IMAGE_ID=$identity" \
    --env "CLOSURE_CANDIDATE=$candidate" --mount "type=bind,source=$PWD,target=/work" -w /work "$asic" \
    bash -lc 'source /OpenROAD-flow-scripts/env.sh; python3 labs/21-physical-closure/run.py asic --candidate "$CLOSURE_CANDIDATE" --output-dir "labs/build/closure-repeat-asic-$CLOSURE_CANDIDATE"'
done
```

PowerShell uses the same runner arguments. For example, reproduce the repaired ASIC with:

```powershell
$asic = 'openroad/orfs@sha256:fd3e27cf1788815be526e86fbe449310d1114bf256fd6c7af9dced6eaf12c699'
$identity = docker image inspect --format '{{.Id}}' $asic
docker run --rm --network none --env HOME=/tmp --env "CASE_IMAGE_ID=$identity" `
  --mount "type=bind,source=${PWD},target=/work" -w /work $asic `
  bash -lc 'source /OpenROAD-flow-scripts/env.sh; python3 labs/21-physical-closure/run.py asic --candidate repair --output-dir labs/build/closure-repeat-asic-repair'
```

For the other eight runs, substitute the target/candidate/output and the corresponding image from the Linux examples. FPGA/test images invoke `python3` directly; only the ASIC image needs `source /OpenROAD-flow-scripts/env.sh` through `bash -lc`.

## Verify repair, export its actual geometry, collect

After implementation has completed, run these commands in the same ASIC image with the repository mounted at `/work`, working directory `/work`, `HOME=/tmp` and its tool environment sourced:

```bash
python3 labs/21-physical-closure/verify_netlist.py labs/build/closure-repeat-asic-repair
python3 labs/21-physical-closure/capture.py labs/build/closure-repeat-asic-repair
```

The first command uses Liberty functional cell models and Yosys `equiv_simple`, `equiv_induct -seq 5`, and `equiv_status -assert`. Unsupported functions on unused library cells are skipped; hierarchy and structural checks reject missing models in the actual design. It proves mapped/repaired netlist equivalence under those zero-delay models, not equivalence between baseline and pipelined RTL or extracted LVS. The second command uses the real OpenROAD GUI in Qt offscreen mode and records hashes of its database, constraints, SPEF and exported images.

Run the sign-extension negative control in the ordinary teaching image:

```bash
python3 labs/21-physical-closure/negative.py labs/build/closure-repeat-negative
```

Then, with Python on either host or container:

```bash
python3 labs/21-physical-closure/collect.py --prefix closure-repeat --reference-dir labs/build/closure-repeat-reference
python3 labs/21-physical-closure/verify_reference.py --reference-dir labs/build/closure-repeat-reference
```

The collector never overwrites an existing reference directory. It checks every original run artifact hash before copying compact evidence, extracts metrics from reports, and binds equivalence/captures to the repaired implementation. `--timing-allow-fail` lets the experiment preserve failing FPGA candidates; completion of the tool is separate from the collector's acceptance decision. The supplied ECP5 registered-product candidate is expected to remain below 100 MHz, and the slow ASIC is expected to retain hold/electrical failures.

## Interpret the result

Explain why the unchanged FPGA implementation can meet a revised 75 MHz requirement without meeting 100 MHz; why the slow ASIC still fails hold; why registering the product succeeds on Nexys but moves the worst ECP5 path into descriptor validation; and what the ASIC repair costs in cells and estimated power. Inspect the detailed-router's final report, not transient violations during route optimization.

The new engine is independently tested at seeds 2026 and 2027 for every length 1–256, plus signed wide sums, AXI channel ordering, stalls, descriptor/DMA errors, IRQ/reset and the serial fixture. It adds one serial accumulation cycle per element. Original Wally cycle results and bounded formal results remain associated with the original RTL; no new full-Wally or pipelined equivalence claim is made. Choose a candidate against an application latency requirement as well as its clock target.

This practice remains outside `run all` and the mandatory twelve-week workload. CI audits preserved evidence without requiring a place-and-route run on every book build.
