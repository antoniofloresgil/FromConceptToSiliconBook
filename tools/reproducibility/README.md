# Clean-environment reproducibility audit

This is a reproduction protocol, separate from checking the preserved reference
reports. It uses the public repository, documented Dockerfiles and per-lab
commands. The optional integrity helper needs Python 3.10+; snapshot modes also
need Git. It can run on the host or inside an appropriate documented container.
It does not execute HDL/EDA tools or establish functional or physical signoff.

## Start from the reader's entry point

1. Follow the root [README](../../README.md), clone the public repository into a
   new directory and detach the exact revision being audited. Do not copy an
   existing `labs/build`, `labs/work`, installed tool directory or cached kernel.
2. Record Docker's platform/resources and the source revision. Use fresh output
   directories. For Linux containers, arrange ownership before switching to the
   invoking UID/GID; a root-owned clone can trigger Git's ownership protection.
3. Build the selected environments with `docker build --no-cache --pull` for
   Dockerfiles using public bases. Build dependent images only after their
   parent image succeeds. When using isolated local parent tags, set the
   Dockerfile's `BOOT_BASE` or `FPGA_BASE` build argument and omit `--pull` on the
   dependent build. Never silently fall back to an old image after build failure.
   On memory-constrained hosts, build the heavyweight Linux and XC7 environments
   sequentially; concurrent cold builds are not required by this protocol.
4. Acquire the ASIC image by the exact digest documented in Lab 17. Creating a
   fresh container from that published image follows its recipe; rebuilding the
   third-party ORFS distribution from source is a different audit scope.
5. Record actual image IDs and tool/package versions. Some lab images resolve
   APT/Python support dependencies at build time, as their READMEs explain;
   successful rebuilding does not make those dependency sets immutable. Archive
   the completed images when long-term environment repeatability is required.

The publication image and lab images have different locking policies. Consult
their own Dockerfiles and manifests rather than extrapolating the book image's
package locks to every laboratory.

## Select and execute representative work

| Boundary | Maintained recipe | Evidence to require |
| --- | --- | --- |
| Formal | [Lab 15](../../labs/15-formal/README.md) | BMC, induction/equivalence, reachable witnesses, vacuity example, counterexample and repaired/faulty simulations |
| Linux/QEMU | [Lab 18](../../labs/18-linux-accelerator/README.md) | Newly built emulator/kernel/driver/application; qtest and normal, DMA-error and suppressed-IRQ boots |
| FPGA | [Labs 17](../../labs/17-complete-case/README.md) and [21](../../labs/21-physical-closure/README.md) | Actual synthesis/place/route, selected part/database, requested/achieved clock, resources and declared fixture boundary |
| ASIC closure | [Lab 21](../../labs/21-physical-closure/README.md) | Fresh baseline/repair, common mapped netlist, extracted setup/hold, electrical reports, routing, GDS readback and netlist equivalence |
| Layout checks | [Lab 22](../../labs/22-layout-verification/README.md) | Actual geometry/extraction, passing finished reference checks and rejected defective layouts |
| Advanced Wally Linux, when selected | [Lab 18 advanced route](../../labs/18-linux-accelerator/README.md#advanced-extension-actual-wally-rv64-rtl) | Fresh pinned Wally checkout; the exact passing QEMU software bundle; separate prepare/compile/preflight/Linux application evidence |
| Book publication, when selected | [Publisher guide](../book/README.md) | Pinned environment; fresh complete HTML/PDF render, manifest hashes, local navigation and representative visual review; no implied deployment |

Choose scope explicitly: a representative subset is not the full curriculum,
advanced Wally Linux boot, a programmed board or foundry qualification. A verifier
of old evidence is not an execution of any row above. The normal `run all` and
package tests can supplement this selection using the root README.

Use acquisition/network access only for documented builds/downloads; execute the
labs offline. Mount the clean source read-only where feasible, with fresh writable
`labs/build` and `downloads` directories/volumes. Keep the full raw logs, including
failed stages. Do not update `reference/` or run collectors against its existing
paths merely to make a comparison pass.

## Check source and artifact integrity

Create a snapshot before execution and compare it afterward. Choose a fresh
snapshot filename outside the tracked source set:

```sh
python tools/reproducibility/verify.py snapshot labs/build/audit-before.json
python tools/reproducibility/verify.py unchanged labs/build/audit-before.json
```

The snapshot covers tracked file bytes and the revision, including retained
reference artifacts. Read-only mounts additionally prevent creating untracked
replacement references. These checks are integrity evidence, not a signature or
an independent proof that the original source is correct.

The snapshot helper expects tracked files; it does not traverse uninitialized
Git submodules. For an external Wally checkout, record its pinned revision and
the runner's original, patched and compiled source inventories. A separate
checkout inventory can record gitlinks by their commit IDs, but that does not
verify unpopulated submodule contents. The Lab 18 RTL export selects its documented
source/configuration paths without using those addins. Audit any additional
dependency separately if a different experiment actually uses it.

For an older revision that predates this helper, invoke it from a separate
current tools checkout, set `--root` to the audited clone, and use absolute
snapshot/report paths. The helper is audit instrumentation; do not patch it into
the historical lab sources or confuse its revision with the audited revision.

Check each raw report against its source and artifact hashes, before moving or
discarding large outputs. For example:

```sh
python tools/reproducibility/verify.py report formal labs/build/formal/report.json
python tools/reproducibility/verify.py report linux labs/build/audit-linux/report.json
python tools/reproducibility/verify.py report closure labs/build/audit-asic-repair/report.json
python tools/reproducibility/verify.py report layout labs/build/audit-layout/report.json
python tools/reproducibility/test_verify.py
```

The helper rejects incomplete report status, missing/changed files, escaped
paths, failed commands, and formal defect exits without their required marker.
Then run the experiment-specific acceptance checks: notably Lab 21's netlist
proof and Lab 25's `physical_gate.py` for a repaired ASIC. Hash agreement alone
does not approve timing, DRC/LVS or any other design requirement.

Compare newly measured outcomes with the corresponding reference configuration.
Separate exact source/technology hashes, hashes of this run's artifacts, and
semantic/numeric agreement with historical results. Build timestamps, absolute
paths and emulator wall times can prevent byte-identical output. Record such
differences explicitly; do not disguise changed functionality or missing evidence
as timestamp noise. Any numeric tolerance must be declared and justified.

## Test rejection paths and report limitations

Test at least an existing output-directory refusal, an attempt to overwrite a
retained reference, a missing tool or failing command, and a corrupted artifact.
Use separate disposable outputs for these controls. Require a nonzero exit plus
the intended diagnostic, and verify that existing evidence bytes survive. A tool
crash is not a successful assertion counterexample or defective-layout rejection.

Some teaching physical runners deliberately retain timing failures with
`--timing-allow-fail` and label their status `completed`. That exit means the
experiment completed, not that its clock requirement passed. Check the explicit
acceptance result, and retain expected failing baselines alongside repaired
candidates. Leave unsupported or unavailable stages unexecuted with a reason.

The audit record should identify its executor, revision, clean-source and
environment setup, exact commands, exit codes, logs, result comparisons, source
immutability check and remaining limitations. An agent-executed clean-container
audit must not be described as an independent human review or a fresh physical
machine. Keep run-specific results in an audit record; update permanent project
knowledge only for confirmed changes to rules or maintenance procedures.
