# Reusable IP Design and Packaging

Checked optional RA6 practice accompanying [Appendix E](../../appendices/executable-project.qmd#sec-reusable-ip).
No FPGA or physical tools are required. It uses the ordinary lab image, outside
the nine automatic entries in `run all`.

`package.py` creates an autonomous `dotproduct_ip` 1.1.0 / register ABI 1.0
release. One schema generates endpoint decode addresses, C/assembly headers,
SV checker constants and a register table. The backend fixes field positions
and behavior explicitly; it is not a general register compiler. MAC and engine
remain byte-identical to the locked Lab 10 sources. No historical source or
physical dossier is rewritten.

## Create the release

From the full repository or extracted practice-package root, using Python 3.10+:

```sh
python labs/23-reusable-ip/package.py --output labs/build/ip-release/dotproduct_ip
python labs/build/ip-release/dotproduct_ip/manifest/verify.py
```

Choose new paths for repeats. The generator refuses to overwrite existing
releases. The delivered tree has `rtl/`, `sim/`, `formal/`, `sw/`, `constraints/`,
`docs/`, `synthesis/` and `manifest/`. Only the three manifest-listed `rtl/`
files belong to the accelerator. The AHB adapter and Wally files are platform
collateral. Build results must remain outside this tree.

## Qualify the autonomous release

Build/acquire `from-concept-labs:2026.10` as described in the
[shared guide](../README.md). The recorded image ID is
`sha256:995529592338d24ea28263345ce2ac981c46da21a7a0e82664ffe3361f9a923c`;
archive that image to reproduce the installation. Wally is separately acquired
from `https://github.com/antoniofloresgil/cvw`, revision
`3b30ba6b6519bd2c26c1437e6d61f632a35cef6c`.

On Linux/WSL, create a host-owned results directory and qualify both AXI profiles:

```sh
mkdir -p labs/build/ip-results
docker run --rm --network none --user "$(id -u):$(id -g)" \
  --env HOME=/tmp --env PYTHONDONTWRITEBYTECODE=1 \
  --mount "type=bind,source=$PWD/labs/build/ip-release/dotproduct_ip,target=/ip,readonly" \
  --mount "type=bind,source=$PWD/labs/build/ip-results,target=/results" \
  --workdir /ip --entrypoint python from-concept-labs:2026.10 \
  sim/run.py --platform axi --profile course --output /results/axi-course
docker run --rm --network none --user "$(id -u):$(id -g)" \
  --env HOME=/tmp --env PYTHONDONTWRITEBYTECODE=1 \
  --mount "type=bind,source=$PWD/labs/build/ip-release/dotproduct_ip,target=/ip,readonly" \
  --mount "type=bind,source=$PWD/labs/build/ip-results,target=/results" \
  --workdir /ip --entrypoint python from-concept-labs:2026.10 \
  sim/run.py --platform axi --profile compact --output /results/axi-compact
```

Run the actual Wally platform with a read-only clone containing the pinned commit:

```sh
docker run --rm --network none --user "$(id -u):$(id -g)" \
  --env HOME=/tmp --env PYTHONDONTWRITEBYTECODE=1 \
  --mount "type=bind,source=$PWD/labs/build/ip-release/dotproduct_ip,target=/ip,readonly" \
  --mount "type=bind,source=$PWD/labs/build/ip-results,target=/results" \
  --mount "type=bind,source=$(cd ../cvw && pwd),target=/cvw,readonly" \
  --workdir /ip --entrypoint python from-concept-labs:2026.10 \
  sim/run.py --platform wally --wally-root /cvw --output /results/wally
```

On native Windows PowerShell, use Windows mount access controls:

```powershell
New-Item -ItemType Directory -Path labs/build/ip-results -Force | Out-Null
docker run --rm --network none --env HOME=/tmp --env PYTHONDONTWRITEBYTECODE=1 `
  --mount "type=bind,source=${PWD}/labs/build/ip-release/dotproduct_ip,target=/ip,readonly" `
  --mount "type=bind,source=${PWD}/labs/build/ip-results,target=/results" `
  --workdir /ip --entrypoint python from-concept-labs:2026.10 `
  sim/run.py --platform axi --profile course --output /results/axi-course
docker run --rm --network none --env HOME=/tmp --env PYTHONDONTWRITEBYTECODE=1 `
  --mount "type=bind,source=${PWD}/labs/build/ip-release/dotproduct_ip,target=/ip,readonly" `
  --mount "type=bind,source=${PWD}/labs/build/ip-results,target=/results" `
  --workdir /ip --entrypoint python from-concept-labs:2026.10 `
  sim/run.py --platform axi --profile compact --output /results/axi-compact
docker run --rm --network none --env HOME=/tmp --env PYTHONDONTWRITEBYTECODE=1 `
  --mount "type=bind,source=${PWD}/labs/build/ip-release/dotproduct_ip,target=/ip,readonly" `
  --mount "type=bind,source=${PWD}/labs/build/ip-results,target=/results" `
  --mount "type=bind,source=D:/Repos/cvw,target=/cvw,readonly" `
  --workdir /ip --entrypoint python from-concept-labs:2026.10 `
  sim/run.py --platform wally --wally-root /cvw --output /results/wally
```

Replace the Wally clone path as needed. The containers see the autonomous IP,
results and external dependency only; the book checkout is absent. Reports and
generic synthesis output are written under the stated results directory.

## Checked results and boundaries

The [portable reference release](reference/dotproduct_ip/manifest/release.json)
contains 28 supplied files. Its SHA-256 is
`3c0151ee34537ab69eee3300afafe7efe82bcfb2f5587c1fce8f7384f593e516`.
All three reports use this exact release and the same three RTL hashes.

- AXI course: 256 job lengths, protocol/strobe/error/reset tests, generic synthesis.
- AXI compact: 16 job lengths, the same boundary tests, generic synthesis.
- Both AXI runs execute the bounded control/engine checks and reachable DONE witness.
- Real RV32 Wally: five polling lengths, one IRQ job, rejected zero-length descriptor;
  [53,153 simulated cycles](reference/wally/command-05.txt) to the mailbox.
- [Four negative controls](reference/negative.json) reject duplicate offsets,
  unsupported field layout, an altered RTL file and unsupported Wally/compact pairing.

The [first relocation failure](reference/relocation-failure/command-05.txt) records
`mcause=7`. Correct integration requires the processor's decoded/PMA range and
assembly ACK address as well as the C driver. The final Wally fixture uses
`0x10080000`, keeps GPIO's `0x10060000`, and adapts only an exported core's PMA
policy. Its report records original/adapted PMA hashes; the clone stays unchanged.

This compares an AXI bus-functional subsystem and a real-Wally RTL firmware
fixture, not two complete processor SoCs. There is no full uncore/PLIC, coherence,
DDR, FPGA deployment or newly implemented ASIC view. The contract and formal
bounds are retained in `reference/dotproduct_ip/docs/contract.md`. The generated
1.1.0 endpoint has no inherited timing/power/DRC/LVS result from Labs 17/21/22.

## Negative tests and evidence audit

```sh
python labs/23-reusable-ip/negative.py labs/build/ip-release/dotproduct_ip labs/build/ip-negative
python labs/23-reusable-ip/verify_reference.py
```

The compact reference is already collected. A fresh collection may retain the
supplied historical failure without recreating a broken integration:

```sh
python labs/23-reusable-ip/collect.py \
  labs/build/ip-release/dotproduct_ip labs/build/ip-results \
  --negative labs/build/ip-negative/negative.json \
  --relocation-failure labs/23-reusable-ip/reference/relocation-failure \
  --image-id sha256:995529592338d24ea28263345ce2ac981c46da21a7a0e82664ffe3361f9a923c \
  --reference-dir labs/build/ip-collected-reference
python labs/23-reusable-ip/verify_reference.py --reference-dir labs/build/ip-collected-reference
```

Use the actual ID of the image used for that run. The historical failure is
diagnostic evidence, not an additional failing step in successful qualification.
`collect.py --help` describes all arguments. The verifier checks
current recipes, baseline source locks, portable release inventory, all shared
RTL identities, successful commands and the retained defect controls.

The release's checksums establish integrity relative to a trusted manifest hash;
they do not authenticate an untrusted replacement manifest. Original executable
sources use MIT. Wally is externally exported with its own license and headers.
