# 18 — Linux → driver → DMA/IRQ → dot-product accelerator

This practice has two separately reported execution environments. The main route boots Linux 6.12 on a patched QEMU 8.2.2 `virt` machine, binds a real built-in Linux platform driver, allocates DMA buffers from a reserved pool and runs a userspace application. The advanced route executes the same kernel, driver and application on real pinned Wally RV64 RTL with the original accelerator RTL. Neither route requires an FPGA. Neither route establishes FPGA/ASIC timing or power.

## Contract and platform identity

`manifest.json` records the unchanged accelerator/adapter RTL hashes from Lab 17 and **a new Linux profile**: 256 MiB RAM at `0x80000000`, MMIO registers at `0x10080000–0x1008001f`, PLIC source 20, and a trusted DMA window `[0x88000000,0x88004000)`. QEMU and Wally use the same accelerator address. The entire 4 KiB page at `0x10080000` is free in the pinned Wally map; its native GPIO remains enabled at `0x10060000`. This replaces the bare-metal fixture's small DMA window, which must not be borrowed for Linux. It changes platform parameters; the original physical metrics do not transfer to this new configuration.

The numerical contract remains signed low-16-bit operands in 32-bit words and an exact signed 64-bit result, with lengths 1–256. The driver ABI uses fixed-width fields, copies arrays rather than accepting userspace physical addresses, and exposes only `/dev/dotproduct` mode 0600. No `/dev/mem`, arbitrary DMA pointer or user MMIO mapping is needed.

PLIC source 20 is the hardware ID. `HSD_DRIVER_READY ... irq=13` in the preserved QEMU run is the Linux IRQ-domain number returned to the driver, not a change to the DT's source ID.

The device tree reserves a 16 KiB `shared-dma-pool` with `no-map` and assigns it using `memory-region`. The driver calls `of_reserved_mem_device_init`, sets the 32-bit DMA mask and uses `dma_alloc_coherent`. It checks the returned DMA address against the trusted window. The first 4 KiB allocation holds A, B and the result at offsets 0, 1024 and 2048. The coherent DMA API does not remove the need for memory-ordering barriers: `dma_wmb()` precedes launch and `dma_rmb()` precedes consuming completed data.

One mutex serializes requests; an IRQ handler acknowledges the device and completes the waiter. Polling is an alternative request flag. Lengths, flags and copy errors are checked. The RTL has no abort/reset register. After a timeout, the built-in driver quarantines the device and retains its buffers until reboot, preventing late DMA into reused memory. The driver intentionally has no module unload or sysfs unbind route; production hot removal, reset/recovery and multi-device support are separate work.

## Main experiment: QEMU and a real Linux driver

Build the existing boot image first as documented in Lab 12, then the extra environment:

```sh
docker build --platform linux/amd64 -f labs/18-linux-accelerator/Dockerfile -t from-concept-linux-accelerator:2026.10 .
```

The Dockerfile verifies the QEMU and Linux archive SHA-256 identities, applies guarded changes in private source directories and builds the emulator, kernel, driver and static PID 1/application. APT dependencies remain resolved at image build time. Preserve the image ID and archive the image for the course. Acquisition/build needs network; execution is offline. Kernel and emulator compilation need several GiB RAM and substantial disk space.

Linux/WSL:

```bash
docker run --rm --network none --user "$(id -u):$(id -g)" --env HOME=/tmp \
  --env CASE_IMAGE_ID="$(docker image inspect --format '{{.Id}}' from-concept-linux-accelerator:2026.10)" \
  --mount "type=bind,source=$PWD,target=/work" from-concept-linux-accelerator:2026.10 \
  python3 labs/18-linux-accelerator/run.py --output-dir labs/build/linux-accelerator-run
```

PowerShell:

```powershell
$linuxAccelImage = docker image inspect --format '{{.Id}}' from-concept-linux-accelerator:2026.10
docker run --rm --network none --env HOME=/tmp --env "CASE_IMAGE_ID=$linuxAccelImage" `
  --mount "type=bind,source=${PWD},target=/work" from-concept-linux-accelerator:2026.10 `
  python3 labs/18-linux-accelerator/run.py --output-dir labs/build/linux-accelerator-run
```

The script refuses nonempty output directories. It verifies that the model/driver/application in the image match the current sources. It then runs a qtest-based device test and boots Linux three times:

| Run | Required evidence |
| --- | --- |
| qtest model | Correct signed result and upper-bit handling, asynchronous busy/DONE, busy descriptor stability, IRQ acknowledgement; zero/excess/misaligned/outside/overlap/wrap descriptors rejected with zero DMA |
| Normal Linux | OpenSBI, Linux, DT binding and driver marker; five lengths with IRQ and polling, exact results, `2*N` reads and two writes; invalid ioctl/user-pointer/length/flag rejections |
| Injected DMA error | Application receives `EIO` and device error code 2 |
| Suppressed IRQ | Application receives timeout; a second request receives `EIO` from quarantine |

`report.json`, exported DTB/DTS, command logs, source/artifact hashes and ten timing rows form the evidence. `bundle/` holds the exact kernel Image/config, initramfs and OpenSBI binary for the advanced route. The harness requires real output markers and normal QEMU exits; simulator errors are not successful negative controls.

### What the QEMU model means

`hsd-dotproduct.c` models the software-visible 32-bit word MMIO contract, address checks, data accesses and interrupt completion. It does not instantiate the accelerator RTL, reproduce AW/W ordering, model AXI stalls or establish RTL equivalence. Busy writes are ignored by this model; software serializes descriptors, and no AXI SLVERR channel is exposed to the guest. The independent RTL protocol tests remain necessary.

Successful commands complete through a timer after **10,000 virtual ns**, a declared teaching latency independent of vector length. Input DMA reads and both output writes occur before DONE/IRQ. Fault injection is a model feature, not an extra public hardware register. Migration, SMP and IOMMU-backed DMA are outside this fixed-machine experiment. `dma-coherent` is used only for the QEMU shared-RAM model, not as a statement about Wally hardware.

The application measures software calculation, end-to-end ioctl and the driver interval. These values include emulator and software effects and **must not be reported as physical accelerator speedup**. Timing after IRQ and polling can illustrate system-call, copying, scheduling and modeled-completion costs. Hardware frequency/energy conclusions need an independently validated implementation/activity model.

`kernel_ns` spans the launch through completion and status/error/result reads. It starts after input-buffer preparation and descriptor writes, and ends before copying the result structure back to userspace. End-to-end ioctl timing includes these additional costs. Neither interval measures the MAC alone.

The preserved [reference report](reference/qemu-report.json) contains ten actual timing rows and passing normal/error/timeout boots. Its companion logs and model transcript are small enough to distribute; kernel images and compiled simulators stay in the generated output directory. Audit the preserved input/output identities offline with `python3 labs/18-linux-accelerator/verify_reference.py`.

## Advanced extension: actual Wally RV64 RTL

Build the ordinary teaching image as in the reproduction appendix, then add Device Tree compilation:

```sh
docker build --platform linux/amd64 -f labs/18-linux-accelerator/Dockerfile.wally -t from-concept-linux-wally:2026.10 .
```

Provide a read-only clone containing Wally revision `3b30ba6b6519bd2c26c1437e6d61f632a35cef6c`, and first complete the QEMU run above. The advanced script exports that revision rather than modifying your clone. It records the original and patched file identities. Its guarded patches add accelerator IRQ source 20 through `wallypipelinedsoc`, `uncore` and the real PLIC, and make the trusted DMA pool uncached in the PMA checker. The CPU pipeline is the real upstream implementation.

Linux/WSL (run the three stages in order, changing the final word):

```bash
docker run --rm --network none --user "$(id -u):$(id -g)" --env HOME=/tmp --env WALLY_ROOT=/cvw \
  --env CASE_IMAGE_ID="$(docker image inspect --format '{{.Id}}' from-concept-linux-wally:2026.10)" \
  --mount "type=bind,source=$PWD,target=/work" \
  --mount "type=bind,source=$(cd ../cvw && pwd),target=/cvw,readonly" from-concept-linux-wally:2026.10 \
  python3 labs/18-linux-accelerator/wally.py prepare --bundle labs/build/linux-accelerator-run/bundle
docker run --rm --network none --user "$(id -u):$(id -g)" --env HOME=/tmp \
  --mount "type=bind,source=$PWD,target=/work" from-concept-linux-wally:2026.10 \
  python3 labs/18-linux-accelerator/wally.py compile
docker run --rm --network none --user "$(id -u):$(id -g)" --env HOME=/tmp \
  --mount "type=bind,source=$PWD,target=/work" from-concept-linux-wally:2026.10 \
  python3 labs/18-linux-accelerator/wally.py run --seconds 3600 --cycles 500000000
```

PowerShell (replace the clone path if necessary):

```powershell
$linuxWallyImage = docker image inspect --format '{{.Id}}' from-concept-linux-wally:2026.10
docker run --rm --network none --env HOME=/tmp --env WALLY_ROOT=/cvw `
  --env "CASE_IMAGE_ID=$linuxWallyImage" `
  --mount "type=bind,source=${PWD},target=/work" `
  --mount "type=bind,source=D:\Repos\cvw,target=/cvw,readonly" from-concept-linux-wally:2026.10 `
  python3 labs/18-linux-accelerator/wally.py prepare --bundle labs/build/linux-accelerator-run/bundle
docker run --rm --network none --env HOME=/tmp `
  --mount "type=bind,source=${PWD},target=/work" from-concept-linux-wally:2026.10 `
  python3 labs/18-linux-accelerator/wally.py compile
docker run --rm --network none --env HOME=/tmp `
  --mount "type=bind,source=${PWD},target=/work" from-concept-linux-wally:2026.10 `
  python3 labs/18-linux-accelerator/wally.py run --seconds 3600 --cycles 500000000
```

Output is separate, under `labs/build/linux-wally/`. Preparation and compilation are explicitly **not Linux boot success**. The `run` stage requires actual OpenSBI, Linux, driver, application and `WALLY_LINUX_ACCEL_PASS` markers from real CPU bus activity. A cycle/wall timeout or missing checkpoint fails and preserves the latest UART evidence. Increasing a limit does not convert an incomplete run into a pass.

The Wally run executes the normal IRQ/polling and invalid-argument regression. The injected DMA-error and suppressed-IRQ boots are QEMU model experiments; their results do not establish the RTL platform's fault recovery.

Expect tens of minutes for a full RTL boot on a desktop, depending on the host. `progress.txt` records the PC and bus state every 100,000 cycles. Both environments pass the manifest's `pty.legacy_count=0` argument: the shared kernel supports 256 legacy PTYs, but the experiment does not need their device nodes. A useful advanced experiment is to vary this boot argument or reduce the kernel configuration, revalidate QEMU, and use that exact bundle/profile on Wally. Do not silently compare different kernels or arguments.

Both also pass `initcall_blacklist=plist_test,debug_vm_pgtable`. The pinned kernel has these unrelated kernel debug self-tests enabled; this profile omits their boot-time execution, using Linux's built-in initcall control and symbol support. It establishes accelerator integration, not kernel self-test qualification. All supplied model, driver, arithmetic, IRQ/polling and fault tests remain enabled. Omitting these arguments creates a different, substantially longer boot workload.

### Advanced hardware and boot boundaries

The upstream GPIO occupies `0x10060000–0x100600ff` and remains enabled. An earlier integration at that address exposed stale register values because the SoC combined two peripherals' responses. The Linux accelerator now occupies the free page at `0x10080000`, with a 32-byte decoded aperture. Preparation audits all enabled regions in the pinned RV64gc configuration, including the declared RAM override, and preserves `address-map.json`. It rejects a collision anywhere in the whole 4 KiB mapping page. `test_platform_map.py` checks the old collision, page sharing and source/manifest drift. A one-hot assertion checks all active AHB transfers during execution. The historical bare-metal and physical dossiers retain their recorded platform profiles.

Before Linux, the run stage executes `boot-smoke.S` on the same compiled CPU/RTL in a separate reset run. It writes and reads the native GPIO output-value register while leaving its output enables at zero, then checks accelerator descriptor readback on both 32-bit lanes, DONE/error registers and the DMA result of `(-32768) * (-32768)`. GPIO state must remain intact after accelerator traffic. The bounded test must emit `WALLY_MMIO_SMOKE_PASS`; this marker establishes the preflight only. The subsequent Linux run starts from reset with the normal firmware/kernel/rootfs and must emit its own application and RTL markers. `smoke.txt` preserves the short regression independently of the Linux UART log. This checks GPIO register isolation; it does not exercise a Linux GPIO driver or external pins.

`tb_wally_linux.sv` instantiates real `wallypipelinedsoc` with RV64 privilege/Sv39 support and the original three accelerator modules plus the AHB adapter. The profile disables the upstream configuration's optional Sv48/Sv57 modes and recomputes the derived VPN width to match its Sv39 DT. A lane selector adapts the 64-bit CPU bus to 32-bit register accesses, and the existing CLINT and patched PLIC serve the kernel. D-cache is enabled for ordinary RAM. A guarded PMA override makes `[0x88000000,0x88004000)` uncached; the page-aligned, cache-line-aligned pool also has `no-map` in DT. It also marks the accelerator's MMIO aperture uncached/non-idempotent and rejects atomic accesses and instruction fetch there: the upstream external-memory region would otherwise be cacheable. The driver uses its coherent allocation from the reserved pool, and the existing barriers still order launch and result consumption. This is an explicit uncached DMA policy, not cache-coherent DMA or a general snooping interconnect.

The source window is the reserved pool above, not arbitrary kernel memory. CPU and accelerator share the SoC's **behavioral RAM array**; the DMA fixture provides a second simulated access port. This is not a synthesizable multi-master memory fabric, DRAM controller or arbiter. Physical implementation must replace it and revalidate the memory and coherence contract. UART output is observed from accepted writes of the real CPU; it is not generated by a behavioral CPU model.

The reset vector is `0x1000`. `boot-wally.S` supplies the dynamic-firmware handoff; OpenSBI is loaded at `0x80000000`, Linux at `0x80200000`, initramfs at `0x84000000`, and the Wally-specific DTB at `0x87000000`. The script constructs little-endian memory files and records hashes. The DT names only the implemented CPU, UART, CLINT, PLIC and accelerator; it does not copy QEMU's optional devices. The simulated clock/timebase and UART input clock are 100 MHz, unrelated to the failing Nexys physical timing result. A 6,250,000-baud console (divisor 1) reduces UART waiting in simulation; both firmware and kernel receive that setting. This is a simulation profile, not a board serial configuration. Guest power-off and physical board behavior remain separate obligations.

The preserved advanced reference passed the preflight, the complete Linux IRQ/polling regression and invalid-argument checks at 99,362,109 cycles from reset. See the [RTL Linux log](reference/wally-uart.txt), [short preflight](reference/wally-smoke.txt) and [combined results](reference/results.json). The QEMU and Wally reports identify the same firmware/kernel/config/initramfs bundle. The cycle total includes boot and the entire application, and the reported intervals describe the behavioral RAM fixture rather than implemented FPGA/DDR performance.

The [relocation dossier](reference/migration-report.json) records the completed baseline regression before moving the device, the new QEMU/Wally executions and the old-address rejection against the pinned native map. The [preserved map audit](reference/wally-address-map.json) lists the enabled regions checked for the relocated Linux page.

## Coursework and extensions

The main QEMU experiment is outside the nine automatic labs and is suitable for a prepared P4/P5 software-integration task. Students analyse a supplied model/environment, complete a small driver change and explain a failure. Building an emulator, booting Linux RTL, implementing cache maintenance and synthesizing the memory fabric are advanced extensions, not additional compulsory work in the 6 ECTS course.

Submit both source/profile identities, DT bindings, buffer ownership and timeout policy, logs and interpreted measurements. For advanced work, state the last completed RTL boot checkpoint. Keep QEMU software correctness, Wally RTL correctness and physical FPGA qualification as separate conclusions. Buildroot can later package this same driver/application; the executable baseline uses the minimal initramfs to keep bring-up small.

In a private variant, attempt to place the accelerator back at `0x10060000`, keeping GPIO enabled. Identify which source/manifest consistency check or pinned-map overlap audit rejects the change before RTL compilation. Explain why a correct DMA result and additional memory barriers cannot compensate for two peripherals responding to the same MMIO address.

`linux-app.c` deliberately combines PID 1 setup and the regression. For Buildroot, split its mount/shutdown steps into the init system and retain the reference/ioctl tests as an ordinary application; do not mount already mounted filesystems from the benchmark.

`collect.py --qemu <output>/report.json --wally <advanced-output>/report.json --publish-reference` validates fresh reports and preserves a compact dossier. Omit `--wally` when only QEMU was run. A prepared or compiled Wally platform must retain that status; only real boot and application checkpoints justify `pass`. The optional `Linux accelerator integration` GitHub Actions workflow rebuilds and runs QEMU; select its Wally input for the advanced RTL run. The ordinary lab workflow only audits the compact reference identities.
