# Hardware security: five scoped experiments

Read [Hardware Security](../../chapters/07-advanced-topics/hardware-security.qmd). This is a synthesis lab, not a complete secure Wally implementation. All commands start at the repository/extracted-package root.

## Environments

Build the existing images:

```sh
docker build --platform linux/amd64 -f labs/12-boot/Dockerfile -t from-concept-boot:2026.10 .
docker build -f labs/Dockerfile -t from-concept-labs:2026.10 .
```

Linux/WSL uses the host UID/GID and a writable temporary home:

```sh
docker run --rm --platform linux/amd64 --network none \
  --user "$(id -u):$(id -g)" --env HOME=/tmp \
  --mount "type=bind,source=$PWD,target=/work" from-concept-boot:2026.10 \
  python3 labs/14-security/run.py pmp
docker run --rm --network none --user "$(id -u):$(id -g)" --env HOME=/tmp \
  --mount "type=bind,source=$PWD,target=/work" from-concept-labs:2026.10 \
  python labs/14-security/run.py digital
```

Native PowerShell with Docker Desktop Linux containers:

```powershell
docker run --rm --platform linux/amd64 --network none --env HOME=/tmp `
  --mount "type=bind,source=${PWD},target=/work" from-concept-boot:2026.10 `
  python3 labs/14-security/run.py pmp
docker run --rm --network none --env HOME=/tmp `
  --mount "type=bind,source=${PWD},target=/work" from-concept-labs:2026.10 `
  python labs/14-security/run.py digital
```

The same build commands work in PowerShell. Image building needs network; experiments run offline. Package/tool versions can change despite pinned base digests: preserve the images and reports for a course release.

## Checked scope

| Experiment | Code/evidence | What is established |
|---|---|---|
| PMP isolation | `pmp.S`, `pmp.ld`, `pmp/uart.log` | QEMU U-mode load/store access faults with precise PC/address, unchanged word, ordinary M bypass |
| Unauthorized DMA | Existing dot-product RTL/tests, `dma/report.json` | Real descriptor rejection, no transactions for rejected jobs, address envelope and existing bounded properties |
| Debug locking | `debug_guard.sv`, `tb_debug.sv`, `digital/debug.log` | Teaching admission gate: auth/lifecycle, immediate/sticky lock and production/reset denial |
| Timing channel | `timing.py`, `digital/timing.json` | Deterministic cache observations with assigned hit/miss costs; a uniform-address variant removes this modelled channel |
| Formal property | Guard's assertions, `digital/debug-formal.log` and witness | Twenty-cycle symbolic denial property plus a reachable authorized-development grant |

Reports under `labs/build/security/pmp/` and `digital/` record versions, commands, source/dependency and artifact hashes. The nested DMA run uses `labs/build/security/dma/`; it preserves the main unit report. Compiler/simulator/prover failures, timeouts and missing signatures fail the run. The optional `security` entry is outside `run all` and the publication gate; reused dot-product checks already run in standard CI.

The PMP probe is trusted straight-line assembly and does not isolate every machine stack/metadata object from an arbitrary adversary. Its address `0x80008000` is also inside the separate accelerator lab's allowed window. Combining those policies unchanged would permit device access despite CPU denial. These are separate examples, not an integrated protected memory map.

The debug guard consumes **trusted** lifecycle and authentication decisions. It is not an authentication protocol, permanent fuse lock, JTAG/DM implementation or fault-hardened lifecycle controller. The proof assumes the RTL transition model and records a twenty-cycle bound; it does not prove arbitrary injected internal faults, cryptographic authority or unbounded behavior. The authorized witness prevents an always-deny design from masquerading as a usable policy.

The timing experiment reuses `02-memory/cache_model.py` with 16 direct-mapped sets and 64-byte lines. Costs 1/12 are synthetic. It operates on public teaching traces and dummy secret indexes; it does not attack a host process or claim a Wally hardware leak. Uniform observations in this model do not establish physical constant-time security.

## Extensions and negative controls

In student copies under `labs/work/`, change PMP denial to permission and require the reference probe to fail. Remove the sticky-lock condition while retaining the assertion history and require a SAT counterexample. Extend DMA tests to a separately trusted firewall and reset/ownership conditions. Keep implementation proposals for secure boot, key storage, complete debug integration and physical fault/leakage evaluation distinct from the executed results.

The chapter supplies the threat model, cross-boundary design and secure-boot implementation template. Source/image identity, allowed-path witnesses and residual risks belong in the final project security dossier.
