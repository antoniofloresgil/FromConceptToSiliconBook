# 16 — OpenROAD: measured clock/utilization study

Read [Physical Design with OpenROAD](../../chapters/06-asic-implementation/openroad.qmd#sec-openroad-study). This practice runs the book's uppercase-`Clk`/`Reset`, two-input accumulator through a direct Tcl flow using the Nangate45 teaching platform bundled in a separate ORFS image. It needs no fabricated ASIC or FPGA board. The unit-lab image does not contain these physical tools.

## Recorded environment and scope

The checked image is `openroad/orfs@sha256:fd3e27cf1788815be526e86fbe449310d1114bf256fd6c7af9dced6eaf12c699`, containing OpenROAD `24Q3-11382-g61879bec53` and Yosys 0.60. Nangate45 is a reference technology, not a fabrication PDK. `reference/manifest.json` records tool, input, technology-file, extraction-rule and report/image identities. No vendor technology views are copied into this practice.

The flow synthesizes one common netlist and holds it fixed across eleven cases: 45/65/80% requested core utilization at 0.85/1.00/1.15 ns, plus 55% at 0.91/1.00 ns. It deliberately omits setup/hold repair to expose the differences between placement estimates, clock-tree insertion, global-route estimates and extracted post-route timing. This is a sensitivity study, not an optimizing PPA sweep. Clock frequency in the table is requested, never measured on silicon.

The 80% cases fail at placement and retain their logs. All completed routed cases still have hold violations; the reference also retains a control-net capacitance violation. An empty router DRC report does not establish foundry DRC/LVS, multi-corner timing, IR/EM, package or manufacturing qualification. There is no GDS/tapeout claim.

## Run from the repository or extracted-package root

Acquire the image once with network access. Linux/WSL:

```bash
study_image=openroad/orfs@sha256:fd3e27cf1788815be526e86fbe449310d1114bf256fd6c7af9dced6eaf12c699
docker pull "$study_image"
docker run --rm --network none --user "$(id -u):$(id -g)" --env HOME=/tmp \
  --env "STUDY_IMAGE_ID=$study_image" --mount "type=bind,source=$PWD,target=/work" -w /work \
  "$study_image" bash -lc 'source /OpenROAD-flow-scripts/env.sh; python3 labs/16-openroad-study/run.py --probe --output-dir labs/build/openroad-probe'
```

For the full campaign, select a fresh output directory:

```bash
docker run --rm --network none --user "$(id -u):$(id -g)" --env HOME=/tmp \
  --env "STUDY_IMAGE_ID=$study_image" --mount "type=bind,source=$PWD,target=/work" -w /work \
  "$study_image" bash -lc 'source /OpenROAD-flow-scripts/env.sh; python3 labs/16-openroad-study/run.py --workers 2 --output-dir labs/build/openroad-campaign'
```

Native Windows PowerShell with Docker Desktop Linux containers:

```powershell
$studyImage = 'openroad/orfs@sha256:fd3e27cf1788815be526e86fbe449310d1114bf256fd6c7af9dced6eaf12c699'
docker pull $studyImage
docker run --rm --network none --env HOME=/tmp --env "STUDY_IMAGE_ID=$studyImage" `
  --mount "type=bind,source=${PWD},target=/work" -w /work $studyImage `
  bash -lc 'source /OpenROAD-flow-scripts/env.sh; python3 labs/16-openroad-study/run.py --probe --output-dir labs/build/openroad-probe'
docker run --rm --network none --env HOME=/tmp --env "STUDY_IMAGE_ID=$studyImage" `
  --mount "type=bind,source=${PWD},target=/work" -w /work $studyImage `
  bash -lc 'source /OpenROAD-flow-scripts/env.sh; python3 labs/16-openroad-study/run.py --workers 2 --output-dir labs/build/openroad-campaign'
```

The baseline should complete tool execution, while exposing its negative hold/electrical results. The complete campaign intentionally exits **nonzero** when any case fails, including the recorded `GPL-0301` 80% rejections. Inspect all case statuses in `study.json`; the runner does not label failed placement as a routed result. Unexpected tool/timeout failures also remain failures. Summarization does not turn them into passes.

Each physical case uses two OpenROAD threads and has a 600-second timeout. `--workers 2` runs two cases concurrently; omit it to use one worker when memory is limited. Commands refuse a nonempty output directory before synthesis. Use a new `--output-dir` inside `labs/build/` for another experiment; preserve previous evidence. The checked local campaign used `labs/build/openroad-study-final`, which appears in its recorded absolute `/work` paths.

## Capture actual placement, CTS, routing and critical paths

After the full campaign, use the same container. Linux/WSL:

```bash
docker run --rm --network none --user "$(id -u):$(id -g)" --env HOME=/tmp \
  --mount "type=bind,source=$PWD,target=/work" -w /work "$study_image" \
  bash -lc 'source /OpenROAD-flow-scripts/env.sh; python3 labs/16-openroad-study/render.py labs/build/openroad-campaign'
docker run --rm --network none --user "$(id -u):$(id -g)" --env HOME=/tmp \
  --mount "type=bind,source=$PWD,target=/work" -w /work "$study_image" \
  bash -lc 'source /OpenROAD-flow-scripts/env.sh; python3 labs/16-openroad-study/summarize.py labs/build/openroad-campaign'
```

PowerShell:

```powershell
docker run --rm --network none --env HOME=/tmp `
  --mount "type=bind,source=${PWD},target=/work" -w /work $studyImage `
  bash -lc 'source /OpenROAD-flow-scripts/env.sh; python3 labs/16-openroad-study/render.py labs/build/openroad-campaign'
docker run --rm --network none --env HOME=/tmp `
  --mount "type=bind,source=${PWD},target=/work" -w /work $studyImage `
  bash -lc 'source /OpenROAD-flow-scripts/env.sh; python3 labs/16-openroad-study/summarize.py labs/build/openroad-campaign'
```

`render.py` sets Qt's offscreen platform, reopens actual ODB/SDC checkpoints and uses the corresponding parasitic model. It exports seven images: two placement comparisons and the diagnostic case's placement, CTS placement, clock-tree topology, routing and highlighted worst setup path. `images.json` ties the exports to ODB/SDC/SPEF and script hashes. No screen, USB device, browser or graphical host session is needed. The Tcl script's explicit die area prevents an uninitialized viewport from producing an empty layout image. A GUI error or absent image fails the exporter.

`summarize.py` verifies the original recorded artifact hashes before emitting CSV/JSON. The optional `--publish-reference` is a **book-author operation** requiring the full repository, all seven GUI exports and `figures/`; it copies measured reports into `reference/` and the exports into the book figures. Students should retain their own output directories instead of replacing the reference.

## Evidence and interpretation

`flow.tcl` retains four ODB/SDC checkpoints, setup/hold paths, constraint/electrical checks, area reports, a CTS report, detailed-route DRC output, SPEF, DEF and routed netlist. It explicitly runs `read_spef` before the final timing report; merely generating SPEF would not replace the earlier STA estimate in this recipe. `study.json` records source/technology hashes, image identity, exact commands, per-case environments/status, elapsed time and artifact hashes.

The [reference summary](reference/summary.csv), [structured summary](reference/summary.json) and [manifest](reference/manifest.json) accompany this package. Case folders under `reference/` retain reports and raw logs renamed to `.txt` so packaging preserves them. The full ODB/SPEF/DEF checkpoints are generated by reproduction and are not included as tracked reference artifacts. `reference/study.json` retains their original hashes; this does not reconstruct missing checkpoint files.

Run `python labs/16-openroad-study/verify_reference.py` with native Python 3.10+ to check the supplied bundle. This verifies hashes and measured/reference consistency without running OpenROAD. In the extracted ZIP, the figures are omitted with the book's other artwork; use the chapter HTML/PDF to inspect them, or regenerate them locally.

For the 55%, 0.91 ns case, compare post-CTS setup of +6.17 ps with extracted post-route setup of −1.46 ps. The worst path is `A[1]` to `_389_/D` (`Overflow`), with 17 combinational arcs. Compare data arrival **and** capture required time; capacitance changes can slow cell arcs as well as wires. The short `Enable` path still fails hold, and `_199_/ZN` combines `Clear`/`Reset` and exceeds its capacitance limit. Increasing the clock period is not a hold/capacitance repair.

## Coursework and follow-up

This explicit practice is outside the nine automatic `run all` entries. `python labs/run.py run physical-study` points here. CI verifies the preserved report bundle without downloading/rerunning a physical tool image. The image and full physical campaign are separate from the standard teaching environment.

For P5 without local physical tools, analyse these identified reports and captures alongside your own generic synthesis as in [Lab 07](../07-implementation/README.md#without-a-physical-board). These are results for the reference accumulator, not timing closure for student-modified IP. Owning or fabricating an ASIC is not needed.

Submit a one-change hypothesis, constraint inventory, labelled stage captures, setup/hold budget calculations, the identified bottleneck and an RTL/physical follow-up plan. A proposed pre-add pipeline changes latency and needs valid/reset/clear handling and a new checker; a register inserted blindly into the feedback changes the recurrence. An alternative carry structure requires functional/equivalence checks and a new mapped/physical run. Keep a proposed improvement distinct from an actually measured repair. The chapter provides detailed questions and decision criteria.
