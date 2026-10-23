#!/usr/bin/env python3
"""Check the synthesis results the Yosys chapter reports for its small diagnosis modules (standard library only).

Each module in labs/07-implementation/surprises/ is synthesized with Yosys and its outcome is compared with the
chapter: logic that disappears, block RAM versus LUT RAM, and a latch that is rejected or quietly built.
Usage: python labs/07-implementation/synthesis_surprises.py BUILD_DIRECTORY
"""
import json
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
SOURCES = HERE / "surprises"
CHAPTER = HERE.parents[1] / "chapters/05-fpga-implementation/yosys.qmd"

# name, flow, expected resources (cell type -> count; "flops" and "cells" are totals)
RESOURCE_CASES = [
    ("counter_unobserved", "synth", {"cells": 8, "flops": 8}),
    ("counter_observed", "synth", {"cells": 62, "flops": 24}),
    ("ram_async", "xc7", {"RAM256X1S": 32, "RAMB18E1": 0, "cells": 73}),
    ("ram_sync", "xc7", {"RAM256X1S": 0, "RAMB18E1": 1, "cells": 30}),
]
FLOWS = {"synth": "synth -top {top}", "xc7": "synth_xilinx -family xc7 -top {top}"}
GATE = "hierarchy -check -top {top}; proc; opt; check -assert; select -assert-none t:$dlatch"
# name, must the gate fail, text the log has to contain
LATCH_CASES = [
    ("latch_comb", True, "Latch inferred for signal `\latch_comb.\q' from always_comb process"),
    ("latch_star", True, "Assertion failed: selection is not empty: t:$dlatch"),
    ("latch_fixed", False, None),
]


def yosys(script, directory):
    done = subprocess.run(["yosys", "-p", script], cwd=directory, capture_output=True, text=True, errors="replace", timeout=300)
    return done.returncode, done.stdout + done.stderr


def resources(stat):
    block = stat.split("Number of cells:", 1)[1]
    counts = {name: int(count) for name, count in re.findall(r"^\s+(\S+)\s+(\d+)\s*$", block, re.M)}
    total = int(re.match(r"\s*(\d+)", block)[1])
    return {**counts, "cells": total, "flops": sum(n for name, n in counts.items() if "DFF" in name)}


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    work = Path(sys.argv[1]).resolve()
    work.mkdir(parents=True, exist_ok=True)
    version = subprocess.run(["yosys", "-V"], capture_output=True, text=True).stdout.strip() or "unknown"
    report, problems = {"yosys": version, "resources": {}, "latches": {}}, []
    for name, flow, expected in RESOURCE_CASES:
        source = SOURCES / f"{name}.sv"
        stat = work / f"{name}.stat"
        code, log = yosys(f'read_verilog -sv "{source}"; {FLOWS[flow].format(top=name)}; tee -q -o {stat} stat', work)
        if code:
            problems.append(f"{name}: yosys failed\n{log[-800:]}")
            continue
        got = resources(stat.read_text(encoding="utf-8"))
        report["resources"][name] = got
        for key, value in expected.items():
            if got.get(key, 0) != value:
                problems.append(f"{name}: {key} is {got.get(key, 0)}, the chapter reports {value}")
    for name, must_fail, text in LATCH_CASES:
        code, log = yosys(f'read_verilog -sv "{SOURCES / (name + ".sv")}"; ' + GATE.format(top=name), work)
        report["latches"][name] = {"gate_failed": bool(code), "message": text}
        if bool(code) != must_fail:
            problems.append(f"{name}: gate {'failed' if code else 'passed'}, expected {'failure' if must_fail else 'a pass'}")
        if text and text not in log:
            problems.append(f"{name}: the log does not contain: {text}")
    if CHAPTER.exists():
        chapter = CHAPTER.read_text(encoding="utf-8")
        for name in [case[0] for case in RESOURCE_CASES] + [case[0] for case in LATCH_CASES]:
            if f"module {name}" not in chapter:
                problems.append(f"the chapter does not show module {name}")
    (work / "synthesis-surprises.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for name, got in report["resources"].items():
        print(f"{name:20s} cells={got['cells']:3d} flops={got['flops']:3d}")
    for name, got in report["latches"].items():
        print(f"{name:20s} latch gate {'fails' if got['gate_failed'] else 'passes'}")
    if problems:
        raise SystemExit("MISMATCH\n" + "\n".join(problems))
    print(f"PASS synthesis surprises with {version}: every outcome matches the chapter")


if __name__ == "__main__":
    main()
