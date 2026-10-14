# Boot and software-stack practice

See [Booting a RISC-V SoC](../../chapters/04-soc-architecture/boot-software-stack.qmd) for the reset/firmware/kernel contract and Linux boot. Run from the repository or extracted-practice-package root.

## Checked recipe: OpenSBI supervisor handoff

This optional environment is separate from `from-concept-labs:2026.10`. It does not change the nine automatic unit labs or claim Linux/Wally boot coverage.

Linux or WSL:

```sh
docker build --platform linux/amd64 -f labs/12-boot/Dockerfile -t from-concept-boot:2026.10 .
docker run --rm --platform linux/amd64 --network none \
  --user "$(id -u):$(id -g)" --env HOME=/tmp \
  --mount "type=bind,source=$PWD,target=/work" from-concept-boot:2026.10
```

Native Windows PowerShell, Docker Desktop Linux containers:

```powershell
docker build --platform linux/amd64 -f labs/12-boot/Dockerfile -t from-concept-boot:2026.10 .
docker run --rm --platform linux/amd64 --network none --env HOME=/tmp `
  --mount "type=bind,source=${PWD},target=/work" from-concept-boot:2026.10
```

The build downloads Ubuntu packages. Execution is offline and bounded by a 45-second emulator timeout. The Ubuntu base digest is pinned; package versions are recorded at execution, rather than locked to an immutable archive. Preserve the image for a course release with `docker save from-concept-boot:2026.10 -o boot-environment.tar`.

`run.py` compiles an RV64 freestanding ELF using Clang/LLD, links at `0x80200000`, exports QEMU `virt`'s generated DTB, and boots through the explicitly named Ubuntu OpenSBI dynamic firmware. The one-hart payload checks disabled translation, aligned DTB/magic, SBI BASE, TIME disarming and unsupported-EID rejection. It requests normal shutdown through SRST. Missing markers, failures, timeouts and nonzero emulator exits fail the recipe.

Evidence goes to `labs/build/boot/`: `report.json`, tool/package versions, firmware/source/artifact hashes, exact commands, ELF, linker map, DTB/DTS and UART log. A checked handoff does not test timer interrupt delivery, a complete DT parser, SMP, Linux, the accelerator, Wally RTL or physical FPGA IO. The boot practice runs explicitly outside `python labs/run.py run all` and the existing publication checks.

For a native Ubuntu environment with `python3 clang lld qemu-system-misc opensbi device-tree-compiler` installed, run `python3 labs/12-boot/run.py`. The script deliberately requires the documented Ubuntu firmware path and package manager; another distribution needs adaptation.

## Linux userspace boot

`linux-init.c` is a minimal Linux userspace PID 1. It is built separately with `riscv64-linux-gnu-gcc -static`, placed in a cpio initramfs and run with a separately built kernel. The optional boot container includes the Linux build dependencies. This program does not replace the freestanding supervisor payload.

After building the image, Linux/WSL users run:

```sh
docker run --rm --platform linux/amd64 \
  --user "$(id -u):$(id -g)" --env HOME=/tmp \
  --mount "type=bind,source=$PWD,target=/work" from-concept-boot:2026.10 \
  python3 labs/12-boot/linux.py --download
docker run --rm --platform linux/amd64 --network none \
  --user "$(id -u):$(id -g)" --env HOME=/tmp \
  --mount "type=bind,source=$PWD,target=/work" from-concept-boot:2026.10 \
  python3 labs/12-boot/linux.py --jobs 4
```

PowerShell users use:

```powershell
docker run --rm --platform linux/amd64 --env HOME=/tmp `
  --mount "type=bind,source=${PWD},target=/work" from-concept-boot:2026.10 `
  python3 labs/12-boot/linux.py --download
docker run --rm --platform linux/amd64 --network none --env HOME=/tmp `
  --mount "type=bind,source=${PWD},target=/work" from-concept-boot:2026.10 `
  python3 labs/12-boot/linux.py --jobs 4
```

Acquisition verifies Linux 6.12 against its published kernel.org SHA-256 and extracts to `labs/work/boot-linux/linux-6.12`. It refuses to overwrite an existing source tree. Keep that reference tree unchanged. Compilation uses separate output directories, constructs `/dev/console` in a cpio manifest without host root/device nodes, and boots OpenSBI → Linux → static PID 1. Evidence goes to `labs/build/boot-linux/`, separately from the supervisor test. The harness stops QEMU after the userspace marker; no guest shutdown is tested. This optional experiment is outside `run all` and the publication gate. Linux builds require substantially more storage and time than the tiny supervisor payload.

Student evidence should identify the source pins, memory layout, privilege transitions, DTB and firmware versions, console output and the earliest failing checkpoint. Keep Linux/Wally evidence separate from the checked QEMU payload report.
