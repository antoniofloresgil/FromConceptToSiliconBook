# Clean-container reproduction audit — 19 October 2026

This audit was executed by Codex at the repository owner's request. It is a
clean-container reproduction of a representative selection, **not an independent
human review**, a fresh physical machine, or a claim that every lab was rerun.

The subsequent [Wally RTL Linux and complete publication follow-up](follow-up/README.md)
closes those two initially excluded execution checks and preserves separate evidence.

**Outcome:** the selected workflows reproduce their declared functional and
physical outcomes, including the expected failing timing baselines. Source and
reference bytes remain unchanged. Linux rebuilding is functionally successful
but is not bit-identical for the kernel and initramfs; see the limits below.

The audited public revision is
`ee1fc8ed9e9d132247846379fb634be16377b559`. Acquisition began on 18 October UTC
(19 October in Europe/Madrid). The unmodified historical source was cloned from
the public repository into a new Linux volume. It was mounted read-only for lab
execution, with separate fresh writable output/download volumes. Lab executions
ran offline as UID/GID 1000. The existing Wally installation and its running
container were not used or modified.

## Environment and method

The labs, boot and FPGA base images were rebuilt with `--no-cache --pull`.
Linux/QEMU and XC7 images were built without cached layers on these newly built
parents, using the documented `BOOT_BASE` and `FPGA_BASE` overrides. The ASIC
environment was acquired by its published ORFS digest:
`sha256:fd3e27cf1788815be526e86fbe449310d1114bf256fd6c7af9dced6eaf12c699`.
That follows the lab's published-image recipe; ORFS itself was not rebuilt.

The host was Windows 11 with Docker Desktop, Linux x86-64/WSL2, 12 logical CPUs
and 7.65 GiB available to the daemon. Resources were shared with an unrelated
running container. Build durations are therefore observations, not resource or
performance guarantees. Supporting APT/Python packages resolve at build time;
recording the resolved versions does not make future dependency resolution
immutable.

The Linux and XC7 cold builds overlapped. During database generation, the XC7
exporter alone was observed using approximately 5.3–6.0 GiB resident memory plus
swap. These are observed samples, not a minimum-memory specification. Sequential
heavy builds are preferable on a memory-constrained host.

The initial inventory hashes all 1,312 tracked files, including 899 files under
`reference/`. Raw reports are checked against their source and artifact hashes
before compact evidence is exported. Historical comparison distinguishes exact
tool/technology/netlist hashes and numerical results from timestamps and runtime
measurements. No timing threshold or numerical tolerance was relaxed.

The integrity helper was supplied separately as audit instrumentation because
the historical revision predates it. It was not added to the audited source.
Its source and the one-off execution harness accompany the evidence. The
[maintained protocol](../../../tools/reproducibility/README.md) describes how to
repeat the review.

## Executed results

| Selection | Fresh execution outcome |
| --- | --- |
| Automatic suite | All nine labs pass with seed 2026. |
| Extracted practice ZIP | All six packaging tests pass, including source provenance and execution without book chapters. |
| Lab 15 formal | All 12 jobs pass their expectations, including proof/equivalence, reachable covers, vacuity, the intended counterexample and simulation regression. |
| Lab 18 Linux/QEMU | qtest and normal, DMA-error and timeout-quarantine boots pass; ten IRQ/polling cases pass. Raw report and bundle hashes validate. |
| Lab 25 fast CI | All six stages pass; four mutations are rejected at their intended contract/simulation/formal/metric stages. |
| Lab 21 functional variants | Baseline and pipeline pass lengths 1–256 with seeds 2026 and 2027, including the Nexys fixture tests. |
| Lab 21 ECP5 | Reduced-frequency variant achieves 86.9943 MHz for 75 MHz requested. Pipeline achieves 98.1932 MHz and remains rejected against 100 MHz. |
| Lab 21 Nexys Video | Reduced-frequency variant achieves 85.4190 MHz for 75 MHz requested. Pipeline achieves 102.1346 MHz and passes 100 MHz. |
| Lab 21 ASIC | Baseline and reduced-frequency cases retain negative hold and 48 electrical violations. Repair passes setup/hold and electrical checks, netlist equivalence and the scoped physical gate. |
| Lab 22 layout | Actual reference DRC/LVS finishing campaign passes its gate; defective-layout controls are rejected and all 293 top-port names match. |

The freshly mapped ASIC netlist is identical across the baseline, reduced-clock
and repaired candidates: physical optimization, rather than an RTL change,
resolves this example. At 100 MHz, repair reproduces setup slack
`5.204097744481942 ns`, hold slack `0.029677428021741278 ns`, cell area
`7811 µm²`, zero electrical violations and estimated vectorless power
`0.000860 W`. The failing baseline retains hold slack
`-0.01844807692158239 ns`. These are experiment-specific outcomes, not general
qualification guarantees.

All nine Lab 21 cases match the historical reference metrics exactly, including
FPGA utilization and critical logic/route delays and ASIC area, timing, electrical
and power values. Tool/technology identities and the mapped ASIC/FPGA netlist
hashes also match. This does not claim that every generated database, image or
timestamped report is byte-identical.

Existing FPGA/ASIC/Linux output directories and retained-reference overwrite
attempts return nonzero exits with the intended diagnostics and unchanged
protected files. Deliberately corrupted artifacts are rejected by both the
physical gate and integrity helper. Removing Yosys from `PATH` returns exit 1 and
a formal report with `status: fail` and the specific missing-tool error. These
controls are separate from the intentionally faulty teaching designs, whose
expected failures require their own completion/defect markers.

The final source comparison verifies all 1,312 tracked files and all 899 retained
reference files unchanged against the pre-execution inventory. It also verifies
the current raw source/artifact hashes of all nine closure cases, formal,
Linux/QEMU and layout reports.

## Retained evidence

- [Command receipts](evidence/commands.json): exact arguments, image IDs, UTC
  starts, elapsed times, exit codes and log hashes. Corresponding full command
  logs are under `evidence/commands/`.
- [Failure dispositions](evidence/command-dispositions.json): expected rejection
  versus corrected audit-harness setup, with the successful confirming command.
- [Final checks](evidence/raw/audit-final-checks.json),
  [all-nine historical comparison](evidence/raw/audit-comparison.json) and
  [Linux comparison](evidence/raw/audit-linux-comparison.json).
- [Initial source inventory](evidence/raw/audit-source-before.json) and
  [final inventory](evidence/raw/audit-source-after.json).
- [Host](evidence/host.json) and resolved image tool/package inventories in
  `evidence/raw/audit-environment-*.json`.
- [Compact raw evidence index](evidence/raw-index.json): retained raw reports,
  timing/electrical reports, command logs and waveforms, plus explicit omissions.
  [Bundle inventory](evidence/inventory.json) hashes the retained evidence files.

The compact bundle intentionally omits large netlists/databases, kernel images,
GDSII and other binary outputs. Their raw-report hashes were verified **before**
export; the compact subset alone cannot rerun full raw-artifact integrity checks.
Complete local outputs remain in Docker volumes
`from-concept-audit-results-20261019` and
`from-concept-audit-downloads-20261019`; the unchanged source volume is
`from-concept-audit-source-20261019`. Local wrapper/build logs and the public
checkout remain under ignored `labs/build/repro-audit-20261019/`.

The one-off harness is retained for provenance, not installed as a generic lab
runner. Its host paths, audit tags and volume names describe this execution; use
the maintained protocol and lab READMEs for a new review. `.gitattributes`
preserves exact retained-evidence bytes across platforms.

## Findings and maintenance changes

No laboratory source or retained reference was changed to make an execution pass.
The audit exposed documentation inaccuracies, corrected in the current working
tree:

- The selected formal exercises use Yosys's built-in SAT engine; an external SMT
  solver is not a dependency of these recipes. Lab 15 also uses Icarus Verilog.
- Lab 22's reference layout checks use KLayout and OpenROAD with FreePDK45 and
  Nangate45. Magic/Netgen were incorrectly listed in the consultation catalogue.
- Packaging checks exported-listing equality and builds the ZIP; it does not
  silently regenerate reference sources. Explicit `labs/run.py sync` is the
  authoring operation that rewrites exported listings.

The authoritative navigation catalogue and its generated indexes were updated.
A cold-audit protocol, source/report integrity helper and regression tests were
added, with the small helper tests included in the existing fast CI workflow.
The development guide links the protocol; run-specific measurements stay here.

Three audit-harness setup mistakes are preserved in the command evidence rather
than erased: an initial Git ownership refusal before lab execution, a corruption
probe initially given a directory instead of `report.json`, and a graphical
KLayout version query that timed out. These were corrected respectively by
setting fresh-volume ownership, using the report filename, and querying KLayout
headlessly. They are distinct from the deliberately rejected lab inputs and from
the successful subsequent lab executions.

### Remaining repeatability limits

The Linux run reproduces all three boot outcomes, ten IRQ/polling measurement
cases, source/manifest identities and the QEMU version. Its `kernel.config` and
OpenSBI binary hashes equal the historical reference. Its rebuilt kernel `Image`
and `rootfs.cpio` hashes differ. The Dockerfile does not fix kernel build identity
and timestamp variables or all input-file times used by the initramfs generator;
supporting packages also resolve at build time. Historical binaries are not
retained here for a byte-level difference analysis, so this audit does not
attribute every differing byte to timestamps or establish bit-identical Linux
binary rebuilding. The new bundle's own manifest hashes do match its actual
files. No historical bundle hash was replaced.

Linux wall-time measurements also differ from the historical samples. The same
modes and lengths pass, but these emulator/software-overhead observations are not
deterministic hardware timing targets. They are preserved without a fabricated
equality claim or a newly introduced performance tolerance.

## Boundaries

Linux/QEMU tests exercise the accelerator's software-visible device model, not
the Wally RTL platform. Emulator timings, including the configured 10,000 ns
device delay, cannot establish physical accelerator speedup. Advanced Wally Linux
boot was not rerun in this initial selection; it was subsequently checked in
the linked follow-up.

FPGA results describe the documented ECP5 out-of-context and Nexys Video XC7
fixtures, not a complete Wally/DDR implementation or a programmed board. ASIC
power is a vectorless estimate. FreePDK45/Nangate45 DRC/LVS checks are reference
technology checks, not foundry qualification or fabrication signoff. No full
book HTML/PDF publication rebuild was part of this initial lab selection;
the linked follow-up checks publication separately.
