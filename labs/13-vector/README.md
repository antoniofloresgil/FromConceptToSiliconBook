# RVV 1.0: portable dot product and masked stores

Read [RISC-V Vector Processing](../../chapters/07-advanced-topics/vector-processing.qmd). This optional practice uses the existing boot toolchain container and works from the full repository or extracted lab ZIP.

Linux/WSL, from the repository/package root:

```sh
docker build --platform linux/amd64 -f labs/12-boot/Dockerfile -t from-concept-boot:2026.10 .
docker run --rm --platform linux/amd64 --network none \
  --user "$(id -u):$(id -g)" --env HOME=/tmp \
  --mount "type=bind,source=$PWD,target=/work" from-concept-boot:2026.10 \
  python3 labs/13-vector/run.py
```

Native Windows PowerShell, Docker Desktop Linux containers:

```powershell
docker build --platform linux/amd64 -f labs/12-boot/Dockerfile -t from-concept-boot:2026.10 .
docker run --rm --platform linux/amd64 --network none --env HOME=/tmp `
  --mount "type=bind,source=${PWD},target=/work" from-concept-boot:2026.10 `
  python3 labs/13-vector/run.py
```

Build with network access; run offline. The Ubuntu base is pinned, while installed package versions can change. Record the report and archive the image with `docker save` for a course release. The tested environment uses Clang/LLD 18.1.3 and QEMU 8.2.2. A native environment needs Python 3, those tools and equivalent QEMU CPU properties.

## Checked boundary

`run.py` compiles the C oracle without vector instructions or auto-vectorization, assembles RVV kernels, then links one ELF. It runs that identical ELF with full V 1.0, ELEN=64 and VLEN=128,256,512. `start.S` enters in M-mode, installs a diagnostic trap handler and enables `mstatus.VS`. QEMU loads the ELF with `-bios none`; no OpenSBI or Linux guest is needed for this integer functional experiment.

`dot_rvv` accepts signed int16 arrays and returns their exact signed int64 sum of products. It strip-mines using the returned `vl`, widens multiplication to 32 bits and reduction to 64 bits. `positive_copy_rvv` stores only positive input values, leaving other memory unchanged. The scalar oracle and guarded output checks cover all lengths 0–257, larger boundaries through 1025, signed extremes, alternating extremes, deterministic data and zeros. Empty calls use invalid pointers to verify that no memory access is attempted.

UART logs, source/tool identities, exact commands, one ELF hash and per-VLEN results go to `labs/build/vector/`. A timeout, nonzero emulator exit, failure marker or missing success marker fails the script. Normal success uses QEMU `virt`'s test-device write; this is not a Wally hardware shutdown mechanism.

This practice is explicit, outside `python labs/run.py run all` and the current publication gate. It checks integer functional behavior; it does not measure hardware cycles, implement a Wally vector unit, validate all RVV instructions or exercise Linux vector context switching. The book's pinned Wally configurations do not advertise V. Keep student variants in `labs/work/` or another branch, preserving package integrity checks.

## Follow-on comparison

The course's AXI/DMA dot-product IP transfers **32-bit memory words** and uses the signed low **16 bits** for arithmetic. This RVV reference instead uses packed int16 arrays. Align memory layout, legal lengths and overflow semantics before comparing them. Do not report QEMU host runtime as a speedup over Wally RTL/FPGA. Add an explicitly defined timing/hardware experiment before making performance, resource or energy claims.
