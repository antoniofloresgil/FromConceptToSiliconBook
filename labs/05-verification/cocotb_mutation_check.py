#!/usr/bin/env python3
"""Mutation check for the book's cocotb accumulator test (standard library only).

Runs the same faulty accumulators that mutation_check.py builds for Verilator against
examples/cocotb/test_accumulator.py, as supplied and with three directed vectors added,
and compares every outcome with the one the chapter reports.
Usage: python labs/05-verification/cocotb_mutation_check.py BUILD_DIRECTORY
"""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples/cocotb"
CHAPTER = ROOT / "chapters/03-simulation-verification/cocotb.qmd"

# Same fault list as the Verilator check, so the two environments can be compared.
SPEC = importlib.util.spec_from_file_location("mutation_check", Path(__file__).with_name("mutation_check.py"))
mutation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mutation)

LAST_DIRECTED = "        (1, 0, 1, 3),\n"
EXTENSION = [
    "        (0, 0, 1, 40000),",
    "        (0, 0, 0, 40000),",
    "        (0, 0, 1, 0),",
]

# outcome with the supplied test, outcome with three added directed vectors
EXPECTED = {
    "overflow_at_max": ("fail", "fail"),
    "overflow_sticky": ("fail", "fail"),
    "overflow_ungated": ("fail", "fail"),
    "valid_needs_operand": ("pass", "fail"),
    "clear_ignored": ("fail", "fail"),
}


def extended_test(text):
    if text.count(LAST_DIRECTED) != 1:
        raise SystemExit("The cocotb test no longer matches the chapter listing; update EXTENSION.")
    return text.replace(LAST_DIRECTED, "\n".join(EXTENSION) + "\n" + LAST_DIRECTED)


def check_chapter_shows_extension():
    if not CHAPTER.exists():  # the extracted practice package carries no book text
        return
    text = CHAPTER.read_text(encoding="utf-8")
    for line in EXTENSION:
        if line.strip() not in text:
            raise SystemExit(f"The chapter does not show the added vector: {line.strip()}")


def run(directory, rtl_text, test_text):
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)
    (directory / "accumulator.sv").write_text(rtl_text, encoding="utf-8", newline="\n")
    (directory / "test_accumulator.py").write_text(test_text, encoding="utf-8", newline="\n")
    shutil.copy(EXAMPLE / "Makefile", directory / "Makefile")
    done = subprocess.run(
        ["make", "-C", str(directory), "SIM=icarus",
         f"VERILOG_SOURCES={directory / 'accumulator.sv'}", "SIM_BUILD=sim_build",
         "COCOTB_RESULTS_FILE=results.xml"],
        capture_output=True, text=True, errors="replace", timeout=600)
    (directory / "run.log").write_text(done.stdout + done.stderr, encoding="utf-8")
    result = directory / "results.xml"
    if not result.exists():
        return {"outcome": "error", "detail": "no results.xml"}
    cases = ET.parse(result).getroot().findall(".//testcase")
    if not cases:
        return {"outcome": "error", "detail": "no test cases"}
    log = (directory / "run.log").read_text(encoding="utf-8")
    for case in cases:
        failure = case.find("failure")
        if failure is not None:
            lines = [line.strip() for line in log.splitlines() if line.strip().startswith("AssertionError:")]
            return {"outcome": "fail", "detail": lines[0] if lines else ""}
        if case.find("error") is not None or case.find("skipped") is not None:
            return {"outcome": "error", "detail": "test errored or was skipped"}
    return {"outcome": "pass", "detail": ""}


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    work = Path(sys.argv[1]).resolve()
    check_chapter_shows_extension()
    rtl = mutation.RTL.read_text(encoding="utf-8")
    test = (EXAMPLE / "test_accumulator.py").read_text(encoding="utf-8")
    longer = extended_test(test)

    rows, mismatches = [], []
    healthy = run(work / "healthy-extended", rtl, longer)
    rows.append({"name": "healthy", "description": "unmodified RTL, three added vectors",
                 "supplied": "pass", "extended": healthy["outcome"], "detail": healthy["detail"]})
    if healthy["outcome"] != "pass":
        mismatches.append(("healthy", "extended", "pass", healthy["outcome"]))

    for name, description, old, new, _verilator14, _verilator17 in mutation.MUTANTS:
        mutated = rtl.replace(old, new, 1)
        got = (run(work / f"{name}-supplied", mutated, test), run(work / f"{name}-extended", mutated, longer))
        rows.append({"name": name, "description": description, "supplied": got[0]["outcome"],
                     "extended": got[1]["outcome"], "detail": got[0]["detail"]})
        for label, expected, result in zip(("supplied", "extended"), EXPECTED[name], got):
            if result["outcome"] != expected:
                mismatches.append((name, label, expected, result["outcome"]))

    (work / "cocotb-mutation-report.json").write_text(
        json.dumps({"rtl": mutation.RTL.relative_to(ROOT).as_posix(), "results": rows}, indent=2) + "\n",
        encoding="utf-8")
    width = max(len(row["name"]) for row in rows)
    print(f"{'mutant':<{width}}  supplied  +3 vectors")
    for row in rows:
        print(f"{row['name']:<{width}}  {row['supplied']:<8}  {row['extended']:<10}")
    if mismatches:
        for name, label, expected, got in mismatches:
            print(f"MISMATCH {name} ({label}): expected {expected}, got {got}")
        raise SystemExit(1)
    print("PASS cocotb mutation check: every outcome matches the chapter")


if __name__ == "__main__":
    main()
