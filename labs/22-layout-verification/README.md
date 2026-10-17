# Lab 22 — Actual GDS DRC/LVS and power/body finishing

This optional continuation checks the **actual Nangate45 GDS from Lab 21**, not an RTL surrogate. It retains the original block, diagnoses its physical failures and finishes a separate candidate without changing functional cells, placements or signal connectivity. It uses the pinned OpenROAD/FreePDK45 environment already acquired for [Lab 17](../17-complete-case/README.md). No FPGA is needed.

## What was found in the Wally environment

The existing Wally development container contains an ORFS checkout under `/home/cad/openroad-study/orfs`, revision `8b5e62fbba91fda9680d117caf05373fac9dbd44`, with FreePDK45/Nangate45 layouts, CDL and DRC rules. Its Nangate GDS hash is `7fdbd7f4e46283fdd9b9a369e1cae1a7f6f742c8e75cfe943c17f451626fe8e8`, identical to the library layout in the case study's pinned ORFS image. Its DRC/CDL revisions differ, so this continuation keeps the pinned image's actual technology hashes instead of mixing revisions. The configured LVS path in that image points to a missing file; the upstream extraction example retained in `vendor/` supplies the documented starting point for the adapter.

Wally also has synthesis-library installation/configuration scripts for other technologies. A synthesis Liberty library or a path to a commercial library is not a complete fabrication PDK. FreePDK45 is a reference technology. Passing these public reference checks is useful physical evidence, but does not certify foundry acceptance.

## Diagnosis and repair

The original GDS passes the 129 reported categories in the available DRC deck, but fails transistor-level LVS. The OpenDB audit finds **1,408 unconnected POWER/GROUND ITerms**, introduced by CTS/resizer cells after the original early `global_connect`. There are also 56 deliberately unused auxiliary signal outputs from clock loading; these are distinct from the missing power connections.

`finish.tcl` records the original CDL and a full functional-cell/placement/signal-net snapshot, runs `global_connect` again, and inserts **29,821 physical cells** using `TAPCELL_X1` plus one-site `FILLCELL_X1` where needed. It reconnects the new power pins, checks placement, and requires zero remaining unconnected POWER/GROUND ITerms. This dense teaching finish fills free sites with well contacts; it is deliberately conservative and is not an optimized tap-pitch or density/fill strategy. These are physical-only cells, not a change to the accelerator microarchitecture. Do not interpret their count as extra functional logic or a calibrated power estimate.

The after-snapshot must be byte-identical to the before-snapshot. The flow re-extracts SPEF and checks setup, hold, electrical limits and constraint coverage on the finished database before streaming it to a **new GDS**. The original Lab 21 artifacts and its earlier, narrower acceptance record remain unchanged.

## What the extraction checks

`lvs.lvs` reads the GDS polygons, extracts four-terminal MOS devices, follows contacts and all ten metal layers through their vias, flattens both extracted and reference circuits and normalizes parallel devices on both sides. The reference is OpenROAD's CDL from the corresponding database concatenated with the actual Nangate cell CDL. Transistor connectivity and primary MOS dimensions are compared; this is independent of the earlier digital netlist equivalence check.

The adapter handles specific, checked library conventions:

- The cell CDL uses `NMOS_VTL` and `PMOS_VTL`; the library GDS lacks VT-flavour marker layers. The preflight rejects designs containing those other marker layers rather than guessing their models.
- The supplied `TAPCELL_X1` GDS contains active/contact/well geometry without implant-marker shapes. Unmarked active is accepted **only in this known master**. Its non-channel active regions are extracted as well contacts. Every other master with unmarked active is rejected.
- Well contacts are connected through **actual geometry**. The deck introduces no `connect_global`, `connect_implicit`, `connect_explicit` or black-boxing shortcut to join VDD/VSS or bypass body connections. Chip-top extraction checks are enabled.
- Top-level pins are made before flattening, so unused internal clock-load outputs are not accidentally promoted to top-level ports. Unused RTL input bits and floating auxiliary outputs are normalized consistently by the two netlist simplifiers.

These library conventions, the deck's implemented rule coverage and its commented-out upstream rules are material limits. There is no foundry-approved rule deck, complete density/ERC/IR/EM/soft-connection signoff, wafer/pad/package validation or fabrication certification in this experiment. The PDK remains educational even when reference DRC and LVS pass.

## Reproduce

First reproduce the repaired ASIC in [Lab 21](../21-physical-closure/README.md). The following uses its historical raw output directory; if you used another prefix, substitute the input directory and matching `--input-report` consistently. Output directories must be fresh.

Linux/WSL:

```bash
image=openroad/orfs@sha256:fd3e27cf1788815be526e86fbe449310d1114bf256fd6c7af9dced6eaf12c699
identity=$(docker image inspect --format '{{.Id}}' "$image")
docker run --rm --network none --user "$(id -u):$(id -g)" --env HOME=/tmp --env "CASE_IMAGE_ID=$identity" \
  --mount "type=bind,source=$PWD,target=/work" -w /work "$image" \
  bash -lc 'source /OpenROAD-flow-scripts/env.sh; python3 labs/22-layout-verification/run.py --input-dir labs/build/closure-final-asic-repair --output-dir labs/build/layout-repeat'
```

PowerShell:

```powershell
$image = 'openroad/orfs@sha256:fd3e27cf1788815be526e86fbe449310d1114bf256fd6c7af9dced6eaf12c699'
$identity = docker image inspect --format '{{.Id}}' $image
docker run --rm --network none --env HOME=/tmp --env "CASE_IMAGE_ID=$identity" `
  --mount "type=bind,source=${PWD},target=/work" -w /work $image `
  bash -lc 'source /OpenROAD-flow-scripts/env.sh; python3 labs/22-layout-verification/run.py --input-dir labs/build/closure-final-asic-repair --output-dir labs/build/layout-repeat'
```

The runner records every command, input hash, tool/image identity and output hash. DRC runs in flat mode to avoid pathological deep-boolean performance on this layout, with the same FEOL/BEOL/OFFGRID/ANTENNA groups enabled and no additional rule waiver. A tool's successful exit is not a DRC/LVS PASS: the actual marker count and the LVS comparison boolean determine the result.

The same run also checks two deliberately faulty layouts: a 1 nm wide M2 sliver must produce DRC markers, and a geometrical metal bridge between actual VDD/VSS rails must fail LVS. Device-count checks prevent an empty extraction from being called a successful proof. The supply-short comparison is more expensive than the passing comparison; allow it to finish within the runner's bounded command timeout.

After completion, run the port-identity audit in the same ASIC container/environment, substituting your output directory:

```bash
klayout -zz -rd out=/work/labs/build/layout-repeat -rm /work/labs/22-layout-verification/audit_ports.py
```

This reads the actual LVS cross-reference and requires all matched top-port names to agree, accounting for the SPICE reader's case normalization. It neither forces a net match nor bypasses topology checking. The supplied result verifies all **293** retained interface pins.

With ordinary Python, collect and audit the new result:

```bash
python3 labs/22-layout-verification/collect.py labs/build/layout-repeat --input-report labs/build/closure-final-asic-repair/report.json --reference-dir labs/build/layout-repeat-reference
python3 labs/22-layout-verification/verify_reference.py --reference-dir labs/build/layout-repeat-reference
```

For the supplied compact dossier:

```bash
python3 labs/22-layout-verification/verify_reference.py
```

The compact reference keeps DRC databases, transistor-count/comparison summaries, diagnostics, timing/PG/preflight reports and exact command logs. Large GDS/ODB/SPEF/CDL/LVS cross-probing databases remain hashed reproduction outputs under `labs/build/`. Open a generated `.lyrdb` in KLayout's Marker Database Browser or `.lvsdb` in its Netlist Browser to inspect actual geometry and mismatches. The original, pre-finishing layout is intentionally retained as the failed LVS case.

The complete public-technology result and its limits are discussed in the [case-study continuation](../../appendices/complete-case-study.qmd#sec-layout-verification). This practice remains outside `run all` and the mandatory twelve-week workload. GPL extraction/deck notices are identified in [NOTICE.md](../../NOTICE.md) and `vendor/`.
