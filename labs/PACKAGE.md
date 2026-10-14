# Hardware Design Practice Package

This download contains executable practices and their guides, not the book source. Read the [HTML book](https://antoniofloresgil.github.io/FromConceptToSiliconBook/) and obtain its complete PDF separately from the book sidebar. See [labs/README.md](labs/README.md) for the activity catalog, student variants and external dependencies.

Extract the ZIP and run every command from this directory, which contains `labs/run.py`. Install Docker; Windows users need Docker Desktop in Linux-container mode. Building needs network access. Reference execution is offline. No native HDL tools, Quarto, LaTeX or Python installation is required for these container commands.

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

`LAB-PROVENANCE.json` records the source repository/commit, preview status, source chapters, listing selectors and file/chapter SHA-256 identities. `SHA256SUMS.json` checks package integrity before reference execution. These checks detect changed/missing files; the archive is not a cryptographically signed release. The full repository checks chapter/code equality before packaging. You do not need chapter files to run the downloaded practices.

Keep student variants in `labs/work/` and use `--rtl-dir` as described in the lab guide. Changing packaged reference files makes integrity checks fail. `sync` and `pack` are authoring commands that require the full book repository; they do not reconstruct chapters from this download.

Original software uses MIT; documentation prose uses CC BY-SA 4.0. [License scope](LICENSE.md), [third-party notices](NOTICE.md) and the full license texts in `LICENSES/` accompany this package. External dependencies retain their own licenses. Textbook figures and the book's chapter/appendix text are not bundled.
