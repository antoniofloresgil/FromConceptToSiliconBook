# 15 — Formal RTL: FIFO properties, induction and equivalence

Read [Formal Verification of RTL: Properties, Proofs, and Counterexamples](../../chapters/03-simulation-verification/formal-verification.qmd). This explicit practice uses the existing teaching image; no FPGA, external Wally clone, PDK, SymbiYosys installation or SMT solver is needed. The backend is Yosys's built-in SAT engine, checked with Yosys 0.33, plus Icarus for the directed regression. Native execution needs Python 3.10+, `yosys`, `iverilog` and `vvp` on PATH.

From the repository or extracted-package root, build once with network access:

```sh
docker build -f labs/Dockerfile -t from-concept-labs:2026.10 .
```

Run offline on Linux/WSL:

```bash
docker run --rm --network none --user "$(id -u):$(id -g)" --env HOME=/tmp \
  --mount "type=bind,source=$PWD,target=/work" from-concept-labs:2026.10 \
  python labs/15-formal/run.py
```

Native Windows PowerShell with Docker Desktop Linux containers:

```powershell
docker run --rm --network none --env HOME=/tmp `
  --mount "type=bind,source=${PWD},target=/work" from-concept-labs:2026.10 `
  python labs/15-formal/run.py
```

The equivalent native command is `python labs/15-formal/run.py`. Building does not freeze mutable Ubuntu package repositories: retain the actual tool versions/report and archive the image for a course release.

## Files and contract

- `fifo2.sv`: ring FIFO, eight-bit data in this harness, capacity two; `BUG=1` selects the deliberately faulty simultaneous-transfer count update.
- `shift_fifo2.sv`: separate shift-register implementation of the same observable queue contract.
- `harness.sv`: symbolic producer/consumer, reset and retained-input assumptions, ordering/state invariants, output stability, bounded drain and equivalence assertions, plus a traffic cover goal.
- `tb_regression.sv`: reset, enqueue, simultaneous replacement and drain; rejects a phantom item in the faulty revision.
- `run.py`: task orchestration, expected-result checks, command/log/source/artifact provenance and a nonzero exit on unexpected outcomes or timeout.

Both implementations mask ready/valid during reset, have no empty bypass and refuse input when full even if a pop will occur on that edge. Initial payload contents are unconstrained; data is compared only when occupied/valid. Reset empties the queue on a sampled edge. The first edge must reset; later resets and sink backpressure remain symbolic. A pending producer request must retain validity/data until accepted or reset. The formal observation ports expose internal state only under `FORMAL`.

## Expected tasks

| Task | Required outcome | Meaning |
| --- | --- | --- |
| `bmc` | No assertion violation through 12 steps | Bounded safety and representation/interface comparisons |
| `induction-equivalence` | Completed base and induction step, max length 12 | Unbounded modeled safety and cycle-level equivalence; the checked baseline closes at length 2 |
| `traffic-witness` | Model plus VCD at depth 12 | Full occupancy, simultaneous transfer and a later empty observation occur in one reset epoch |
| `drain-proof` | Completed induction | Same obligations with an explicit source-stops/sink-ready drain scenario |
| `drain-witness` | Model plus VCD at depth 12 | The drain assumptions still admit useful traffic |
| `fault-counterexample` | Assertion failure plus VCD within 6 steps | The real `BUG=1` implementation violates the count/state relation |
| `vacuous-proof` | No violation through 12 steps | Deliberately overconstrained `QUIET=1` prohibits input |
| `unreachable-traffic` | No model at depth 12 | The same quiet environment cannot witness useful traffic |
| `repaired-regression` | Successful simulation | Correct simultaneous update and final empty state |
| `faulty-regression` | Nonzero simulation exit with phantom-item diagnostic | Unchanged regression detects the defect |

`run.py` prints PASS when the expected result in the table occurs, including expected negative results. It also checks both regression compilations. It does not silently accept a solver error as a counterexample: formal negative tasks use `-falsify`/result markers and require a nonempty witness. A failed proof, unexpectedly successful mutation, missing witness/tool or 120-second command timeout fails the practice.

Native Yosys SAT cannot directly import `$cover` cells. The harness contains `cover(goal)`; the script removes the cells and explicitly asks for the same sticky `goal=1` at step 12. The goal circuitry remains, and proof tasks independently establish assertions for the repaired RTL. An unreachable bounded goal does not generally establish impossibility at all depths; the quiet control has the independently clear no-input explanation.

The drain assumptions apply after full occupancy has been observed: the source must stop presenting new items and the sink remains ready outside reset. This is a deliberately restricted traffic phase, not a general fairness proof. The per-edge drain invariant plus the capacity bound implies empty within two consecutive non-reset ready/no-new-input edges. Reset ends the pending obligation. No claim of unbounded liveness under intermittent readiness is made.

## Evidence and student work

Output stays in `labs/build/formal/`, separate from `labs/build/report.json` and the Wally system report. `report.json` records source hashes, versions, exact commands, expected/actual outcomes and artifact hashes. Preserve the logs, traffic/drain witnesses, fault counterexample and regression results. VCD initial values before reset may be arbitrary, and immediate clocked assertions report sampled checks after the responsible RTL update; follow the chapter's trace interpretation.

This is an explicit practice outside the nine automatic `run all` entries. `python labs/run.py run formal` points here. CI runs the script separately and retains its dossier. It does not alter the existing project's `DP-EQUIV` status: this proof compares these two FIFO implementations, not the accelerator's transformed netlist.

For P4, reproduce the experiment, explain the assumptions and one real counterexample, then transfer a small meaningful property plus antecedent witness to your own IP. This fits the existing P4 budget; formal verification of a complete processor is an advanced extension. Submit the contract, state relation, completed proof/witness logs, diagnosed defect, repair, unchanged regression and limits. Keep student variants in a separate Git branch or copy the complete folder into `labs/work/`; when copying, adapt `ROOT`/output paths in your local runner and retain explicit variant identity. The supplied runner deliberately verifies its local source folder, with no implied proof transfer to edited copies.
