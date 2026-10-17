# Hardware Design Practice Package

This download contains executable practices and their guides, not the book source. Read the [HTML book](https://antoniofloresgil.github.io/FromConceptToSiliconBook/) and obtain its complete PDF separately from the book sidebar. See [labs/README.md](labs/README.md) for the activity catalog, student variants and external dependencies.

Extract the ZIP and run every command from this directory, which contains `labs/run.py`. Install Docker; Windows users need Docker Desktop in Linux-container mode. Building needs network access. Reference execution is offline. No native HDL tools, Quarto, LaTeX or Python installation is required for these container commands.

You can complete the online course without a physical FPGA. Follow [the alternative activity and evidence map](labs/NO-FPGA.md), included in this download. Board programming remains an additional activity; the alternative uses RTL/architectural simulation, synthesis and implementation-report analysis, with physical qualification gaps recorded explicitly.

Build the teaching environment (PowerShell or Linux/WSL):

```sh
docker build --platform linux/amd64 -f labs/Dockerfile -t from-concept-labs:2026.10 .
```

On Linux/WSL:

```bash
docker run --rm --platform linux/amd64 --network none \
  --user "$(id -u):$(id -g)" --env HOME=/tmp \
  --mount "type=bind,source=$PWD,target=/work" \
  from-concept-labs:2026.10 python labs/run.py check
docker run --rm --platform linux/amd64 --network none \
  --user "$(id -u):$(id -g)" --env HOME=/tmp \
  --mount "type=bind,source=$PWD,target=/work" \
  from-concept-labs:2026.10 python labs/run.py run all --seed 2026
```

On Windows PowerShell:

```powershell
docker run --rm --platform linux/amd64 --network none --env HOME=/tmp `
  --mount "type=bind,source=$PWD,target=/work" `
  from-concept-labs:2026.10 python labs/run.py check
docker run --rm --platform linux/amd64 --network none --env HOME=/tmp `
  --mount "type=bind,source=$PWD,target=/work" `
  from-concept-labs:2026.10 python labs/run.py run all --seed 2026
```

`all` runs nine automatic practices; results and logs are in `labs/build/`, with `report.json` as the run index. Replace `check` with `list` or `doctor` to inspect activities or tools. Real Wally integration, FPGA/ASIC work and other guided activities require the dependencies identified in their guides. The Wally clone must contain the pinned commit documented in [the accelerator guide](labs/10-dotproduct/README.md).

The [boot practice](labs/12-boot/README.md) uses a separate optional QEMU/OpenSBI container. It checks an RV64 supervisor handoff offline and includes a Linux PID 1 source for the guided kernel/initramfs extension. Follow its guide; this environment is outside `run all`.

The [vector practice](labs/13-vector/README.md) reuses that environment for a bare-metal RVV integer dot product and masked stores. The same executable is checked at three register lengths; emulator runtime is not a hardware performance measurement.

The [security practice](labs/14-security/README.md) combines a QEMU PMP probe with the real DMA reference, a teaching debug gate, a synthetic cache observation and a bounded formal property. Follow its two-environment guide and retain the limits of each claim.

The [formal FIFO practice](labs/15-formal/README.md) uses the standard teaching image for BMC, induction/equivalence, useful-traffic and vacuity checks, a real counterexample and repair/regression. Run its explicit script; it is separate from the nine automatic entries and requires no physical board or extra solver installation.

The [OpenROAD physical study](labs/16-openroad-study/README.md) uses a separate digest-pinned ORFS image for an accumulator period/utilization sweep. Its supplied CSV/JSON and raw timing/failure reports can be analysed without running the tools. Actual placement, CTS, routing and critical-path captures appear in the book; its scripts can regenerate them. No fabrication or FPGA board is needed, and the recorded failures remain explicit.

The [complete case](labs/17-complete-case/README.md) follows one locked dot-product RTL release through independent tests/bounded formal checks, real Wally firmware, ECP5 FPGA placement/routing and a Nangate45 ASIC block through GDSII. Its shared manifest, scripts and compact dossier include actual cycle/resource/area/timing, a clearly scoped ASIC power estimate and visual-generation recipes. The book contains the physical visuals. The complete SoC remains a simulation boundary; board/foundry, timing and power gaps remain explicit.

The [Linux continuation](labs/18-linux-accelerator/README.md) supplies a QEMU device, Device Tree, built-in kernel driver, reserved DMA pool, IRQ/polling, userspace reference tests and fault injection. Its separate advanced route boots the same software bundle on real Wally RV64 RTL with the original accelerator. The Linux profile changes the DMA aperture and CPU/interrupt configuration; earlier physical metrics do not transfer. Preserved execution status and emulator timing limitations accompany the recipes.

`LAB-PROVENANCE.json` records the source repository/commit, preview status, source chapters, listing selectors and file/chapter SHA-256 identities. `SHA256SUMS.json` checks package integrity before reference execution. These checks detect changed/missing files; the archive is not a cryptographically signed release. The full repository checks chapter/code equality before packaging. You do not need chapter files to run the downloaded practices.

Keep student variants in `labs/work/` and use `--rtl-dir` as described in the lab guide. Changing packaged reference files makes integrity checks fail. `sync` and `pack` are authoring commands that require the full book repository; they do not reconstruct chapters from this download.

Original software uses MIT; documentation prose uses CC BY-SA 4.0. [License scope](LICENSE.md), [third-party notices](NOTICE.md) and the full license texts in `LICENSES/` accompany this package. External dependencies retain their own licenses. Textbook figures and the book's chapter/appendix text are not bundled.
