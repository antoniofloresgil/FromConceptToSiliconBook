# 17 — Complete case: one dot-product RTL release across all stages

Read [Complete Case Study: From RTL Specification to an Implemented SoC](../../appendices/complete-case-study.qmd). The same maximum-256 AXI/DMA accelerator is tested, integrated with real Wally RTL, placed/routed on ECP5 out of context and on Nexys Video with a serial boundary fixture, and mapped/routed/streamed to Nangate45 GDSII. The **SoC is simulated and the accelerator block is physically implemented**. No physical flow includes the complete Wally system or memory fabric; the Nexys fixture adds its own board IO but has not been programmed/validated on hardware.

## Inspect the supplied results without physical tools

`manifest.json` locks the original IP/adapter and firmware source hashes, trusted window, seed, period and stage profiles. `reference/results.json` joins functional/formal/Wally evidence with actual physical reports. `reference/inventory.json` checks preserved report/figure identities. The chapter shows the real FPGA BEL placement map, ASIC routing, critical path and clock tree.

Run with native Python 3.10+:

```sh
python labs/17-complete-case/run.py check
python labs/17-complete-case/verify_reference.py
python labs/17-complete-case/verify_nexys.py
python labs/17-complete-case/test_collection.py
```

The verifier checks the compact dossier; it does not rerun simulation, physical tools or power analysis. It leaves the FPGA 100 MHz failure, ASIC hold/electrical failures, unestimated FPGA power and unexecuted full-SoC qualification explicit. The practice ZIP contains scripts/reports, with book images read online or regenerated. Large ODB/SPEF/GDS/routed-JSON checkpoints are generated locally, not included in the reference bundle.

## Environments and working directory

### Nexys Video / Artix-7 extension

The Nexys Video target is **`xc7a200tsbg484-1`**, with its real 100 MHz oscillator, reset, four switch pins and LED0. `nexys-profile.json` binds this additional target to the unchanged common manifest. The ECP5 and ASIC reports retain their original identities. The XC7 implementation adds `nexys_video.sv`, a serial boundary fixture that retains all accelerator interface signals while using seven board IOs. It includes a BUFG and synchronized controls. The full design therefore includes fixture resources; the mapped report separates accelerator and fixture primitives before packing. This fixture is not a Wally/DDR memory fabric or a DMA workload generator.

First build `Dockerfile.fpga` using the command below, then add Wally's pinned nextpnr-Xilinx and Artix-7 database:

```sh
docker build --platform linux/amd64 -f labs/17-complete-case/Dockerfile.xc7 -t from-concept-case-xc7:2026.10 .
```

Run from Linux/WSL:

```bash
docker run --rm --network none --user "$(id -u):$(id -g)" --env HOME=/tmp \
  --env CASE_IMAGE_ID="$(docker image inspect --format '{{.Id}}' from-concept-case-xc7:2026.10)" \
  --mount "type=bind,source=$PWD,target=/work" from-concept-case-xc7:2026.10 \
  python labs/17-complete-case/run_nexys.py --output-dir labs/build/case-nexys-run
```

PowerShell:

```powershell
$caseXc7Image = docker image inspect --format '{{.Id}}' from-concept-case-xc7:2026.10
docker run --rm --network none --env HOME=/tmp --env "CASE_IMAGE_ID=$caseXc7Image" `
  --mount "type=bind,source=${PWD},target=/work" from-concept-case-xc7:2026.10 `
  python labs/17-complete-case/run_nexys.py --output-dir labs/build/case-nexys-run
```

The runner executes the serial-fixture simulation (AXI register write/read, serial output and reset), maps the same maximum-256 IP with `-nodsp` as in Wally's board recipe, then places/routes it with seed 2026 and a 100 MHz target. An initial DSP-enabled attempt failed while routing the DSP's `MULTSIGNIN` constant connection; the final profile uses LUT/carry arithmetic and preserves that failed attempt separately. It preserves mapped/routed JSON, timing/utilization JSON, FASM, actual site coordinates, logs and content hashes. Tool completion is separate from meeting timing. FASM-to-`.bit` conversion, physical programming, vendor STA/CDC, switch debouncing and board behavior are unexecuted; the switch assignments are an implementation fixture, not a validated interactive board application. There is no characterized FPGA power estimate.

The input chain contains 101 bits, shifted MSB first; a rising `apply` transfers the complete snapshot to the live accelerator inputs. `capture` loads 206 output bits, read LSB first while shifting. `nexys-port-map.json` specifies every field offset. Switches SW0–SW3 drive data/tick/apply/capture, and LED0 shows the output bit. External controls/data must be stable for synchronization; switch bounce is not filtered. The accelerator continues clocking between snapshots, so this interface does not implement automatic AXI handshakes.

For optional figure regeneration, use the Matplotlib environment documented below:

```sh
python labs/17-complete-case/nexys_plot.py labs/build/case-nexys-run figures/complete-case-nexys.png
python labs/17-complete-case/collect_nexys.py labs/build/case-nexys-run/report.json
```

`collect_nexys.py --publish-reference` is the author operation for preserving the compact reference dossier. The ordinary collector and the ECP5 comparison remain available separately.

Start from the repository or extracted-package root. Build the ordinary unit-lab image following the reproduction appendix. Obtain the pinned Wally fork as in [Lab 10](../10-dotproduct/README.md). Build the extra FPGA image and acquire the recorded ASIC image once with network access:

```sh
docker build --platform linux/amd64 -f labs/17-complete-case/Dockerfile.fpga -t from-concept-case-fpga:2026.10 .
docker pull openroad/orfs@sha256:fd3e27cf1788815be526e86fbe449310d1114bf256fd6c7af9dced6eaf12c699
```

The FPGA Dockerfile verifies the official OSS CAD Suite 2026-10-14 archive SHA-256. Its Ubuntu base is pinned; APT support packages remain resolved at build time. Preserve the resulting image ID and archive the image for a course release. The checked tools are Yosys `0.70+16` and nextpnr `0.11.1-63-g44a6c739`. The ASIC image supplies Yosys 0.60, OpenROAD `24Q3-11382-g61879bec53`, KLayout and the matching Nangate45 teaching views. Its image and technology hashes are recorded.

No FPGA, privileged container, USB device, PDK download beyond this reference image or fabricated ASIC is needed. Tool execution below is offline. Only image acquisition/build and optional figure-dependency installation require network.

## Functional/formal and real-Wally stages

Linux/WSL uses the invoking user's UID/GID:

```bash
docker run --rm --network none --user "$(id -u):$(id -g)" --env HOME=/tmp \
  --mount "type=bind,source=$PWD,target=/work" from-concept-labs:2026.10 \
  python labs/17-complete-case/functional.py unit --output-dir labs/build/case-run
docker run --rm --network none --user "$(id -u):$(id -g)" --env HOME=/tmp --env WALLY_ROOT=/cvw \
  --mount "type=bind,source=$PWD,target=/work" \
  --mount "type=bind,source=$(cd ../cvw && pwd),target=/cvw,readonly" from-concept-labs:2026.10 \
  python labs/17-complete-case/functional.py system --output-dir labs/build/case-run
docker run --rm --network none --user "$(id -u):$(id -g)" --env HOME=/tmp \
  --mount "type=bind,source=$PWD,target=/work" from-concept-labs:2026.10 \
  python labs/10-dotproduct/verify_negative.py /work/labs/build/case-run/negative
```

PowerShell (replace the Wally clone location if necessary):

```powershell
docker run --rm --network none --env HOME=/tmp `
  --mount "type=bind,source=${PWD},target=/work" from-concept-labs:2026.10 `
  python labs/17-complete-case/functional.py unit --output-dir labs/build/case-run
docker run --rm --network none --env HOME=/tmp --env WALLY_ROOT=/cvw `
  --mount "type=bind,source=${PWD},target=/work" `
  --mount "type=bind,source=D:\Repos\cvw,target=/cvw,readonly" from-concept-labs:2026.10 `
  python labs/17-complete-case/functional.py system --output-dir labs/build/case-run
docker run --rm --network none --env HOME=/tmp `
  --mount "type=bind,source=${PWD},target=/work" from-concept-labs:2026.10 `
  python labs/10-dotproduct/verify_negative.py /work/labs/build/case-run/negative
```

`functional.py` checks the common source lock before/after execution, derives the seed from it, invokes the existing lab runner and records a manifest/report attestation. Unit output stays under `case-run/unit/`; real Wally stays under `case-run/system/`. The unit run includes the 256/16 reuse configurations and existing bounded formal tasks; the manifest names their reduced scopes. Negative tests reject unsigned arithmetic and early DONE, including a formal counterexample for the latter. The full pinned Wally clone remains an external dependency.

## FPGA and ASIC physical stages

Use a fresh physical output directory; the scripts refuse existing stage results. Linux/WSL:

```bash
fpga_id=$(docker image inspect --format '{{.Id}}' from-concept-case-fpga:2026.10)
asic_image=openroad/orfs@sha256:fd3e27cf1788815be526e86fbe449310d1114bf256fd6c7af9dced6eaf12c699
docker run --rm --network none --user "$(id -u):$(id -g)" --env HOME=/tmp --env "CASE_IMAGE_ID=$fpga_id" \
  --mount "type=bind,source=$PWD,target=/work" from-concept-case-fpga:2026.10 \
  python3 labs/17-complete-case/run.py fpga --output-dir labs/build/case-run
docker run --rm --network none --user "$(id -u):$(id -g)" --env HOME=/tmp --env "CASE_IMAGE_ID=$asic_image" \
  --mount "type=bind,source=$PWD,target=/work" -w /work "$asic_image" \
  bash -lc 'source /OpenROAD-flow-scripts/env.sh; python3 labs/17-complete-case/run.py asic --output-dir labs/build/case-run'
```

PowerShell:

```powershell
$fpgaId = docker image inspect --format '{{.Id}}' from-concept-case-fpga:2026.10
$asicImage = 'openroad/orfs@sha256:fd3e27cf1788815be526e86fbe449310d1114bf256fd6c7af9dced6eaf12c699'
docker run --rm --network none --env HOME=/tmp --env "CASE_IMAGE_ID=$fpgaId" `
  --mount "type=bind,source=${PWD},target=/work" from-concept-case-fpga:2026.10 `
  python3 labs/17-complete-case/run.py fpga --output-dir labs/build/case-run
docker run --rm --network none --env HOME=/tmp --env "CASE_IMAGE_ID=$asicImage" `
  --mount "type=bind,source=${PWD},target=/work" -w /work $asicImage `
  bash -lc 'source /OpenROAD-flow-scripts/env.sh; python3 labs/17-complete-case/run.py asic --output-dir labs/build/case-run'
```

Both physical stages read the common manifest and explicitly set `MAX_LENGTH`, `DMA_BASE` and the widened `DMA_LIMIT`. They use exactly the three component RTL paths listed there. The AHB adapter is part of system integration, outside the physical IP top. This runner checks the documented baseline; new parameters/architectures require a reviewed new release and matching test/firmware contracts.

The FPGA flow produces mapped/routed JSON, raw placement SVG and `timing.json`. Out-of-context mode excludes board IO and normal clock promotion, and does not produce a programmable bitstream. `--timing-allow-fail` retains the routed result even when 100 MHz fails; the result collector explicitly records `setup_target_met=false`. Never treat a completed tool command as timing acceptance.

The ASIC flow produces per-stage reports/ODB/SDC, extracted SPEF, DEF/netlist, power report and `dotproduct_axi.gds`. KLayout merges the routed DEF with the actual matching cell GDS, rejects unresolved empty cells and reopens the result. GDS readback is not LVS or foundry DRC. The power report uses vectorless `set_power_activity -global -activity 0.1` at 100 MHz, not firmware activity. FPGA power remains unestimated; there is no characterized FPGA power model in this flow.

## Join and validate the evidence

Run with native Python, or use the same unit-lab container command/mount policy:

```sh
python labs/17-complete-case/collect.py --unit labs/build/case-run/unit/report.json --system labs/build/case-run/system/report.json --fpga labs/build/case-run/fpga/report.json --asic labs/build/case-run/asic/report.json --negative labs/build/case-run/negative/negative-results.json --output-dir labs/build/case-run/dossier
```

The collector validates source/manifest/parameter identity, seeds, commands, recorded artifact freshness, expected checker completions and the pinned Wally identity. It extracts five cycle comparisons, physical resource/area/timing, ASIC power components and GDS readback. It rejects failed/mismatched/stale evidence. Its successful completion means **the dossier was collected**, while timing/electrical failures and missing power/qualification remain explicit data.

The supplied reference was collected from `complete-case-unit/`, `complete-case-system/`, `complete-case-fpga-final/fpga/`, `complete-case-asic-final/asic/` and `complete-case-negative/` under `labs/build/`. The recorded `/work` paths identify that environment. The common release/RTL identities match despite these separate output namespaces.

`--publish-reference` is a book-author operation requiring the complete repository and physical images. It copies compact reports into `reference/`, renames raw logs to `.txt` for package inclusion, copies book figures and writes the report/figure inventory. Students should keep their own dossier instead of replacing the reference.

## Regenerate physical visuals

The raw FPGA `placed.svg` is automatically generated. For the clearer occupied-BEL coordinate map used in the book, install `requirements-figures.txt` into a separate Python virtual environment and run `fpga_plot.py` against the final routed JSON. This optional author/analysis dependency does not affect synthesis or timing.

Linux/WSL example:

```bash
python3 -m venv labs/build/case-figures-env
labs/build/case-figures-env/bin/python -m pip install -r labs/17-complete-case/requirements-figures.txt
labs/build/case-figures-env/bin/python labs/17-complete-case/fpga_plot.py labs/build/case-run/fpga/routed.json labs/build/case-run/fpga/implementation.png
docker run --rm --network none --user "$(id -u):$(id -g)" --env HOME=/tmp --env QT_QPA_PLATFORM=offscreen \
  --env CASE_OUT=/work/labs/build/case-run/asic --mount "type=bind,source=$PWD,target=/work" -w /work "$asic_image" \
  bash -lc 'source /OpenROAD-flow-scripts/env.sh; openroad -gui -no_init -exit labs/17-complete-case/asic-images.tcl'
```

PowerShell:

```powershell
python -m venv labs/build/case-figures-env
& labs/build/case-figures-env/Scripts/python.exe -m pip install -r labs/17-complete-case/requirements-figures.txt
& labs/build/case-figures-env/Scripts/python.exe labs/17-complete-case/fpga_plot.py labs/build/case-run/fpga/routed.json labs/build/case-run/fpga/implementation.png
docker run --rm --network none --env HOME=/tmp --env QT_QPA_PLATFORM=offscreen `
  --env CASE_OUT=/work/labs/build/case-run/asic --mount "type=bind,source=${PWD},target=/work" -w /work $asicImage `
  bash -lc 'source /OpenROAD-flow-scripts/env.sh; openroad -gui -no_init -exit labs/17-complete-case/asic-images.tcl'
```

The FPGA map uses actual `NEXTPNR_BEL` coordinates and distinguishes the DSP anchor from tile occupancy. It is not an invented floorplan or routing screenshot. OpenROAD directly exports the real routed ASIC database, highlighted worst setup path and clock tree; no host display or physical board is needed.

## Deliverable and limits

This explicit complete case is outside the nine automatic entries; `python labs/run.py run complete-case` points here. CI audits the preserved dossier and collector rejection gates without downloading/running physical tools. P1–P5 reuse their existing workload and rubric; full-processor proof and complete-SoC physical integration are extensions.

Use the case-study tables to explain why the functional IP is an accepted baseline while the 100 MHz FPGA and timing-qualified ASIC releases are not accepted. Distinguish cycle speedup from implemented system time, LUT/carry units from ASIC area, setup-only frequency estimates from qualified Fmax, and modeled power from measured consumption. A proposed RTL repair needs a new manifest/checker and new implementation results. Preserve project-specific equivalence, board/foundry checks and calibrated full-system energy as unclosed obligations.
