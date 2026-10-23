#!/usr/bin/env python3
"""Mutation check for the book's Verilator accumulator example (standard library only).

Builds deliberately faulty copies of examples/verilator/accumulator.sv, runs them
against the book's 14-vector harness and against the same harness extended with
three vectors, and compares every outcome with the one the chapter reports.
Usage: python labs/05-verification/mutation_check.py BUILD_DIRECTORY
"""
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
RTL = ROOT / "examples/verilator/accumulator.sv"
HARNESS = ROOT / "examples/verilator/sim_main.cpp"
CHAPTER = ROOT / "chapters/03-simulation-verification/verilator.qmd"

OVERFLOW = "Overflow <= Enable && ExtendedSum[16];"
VALID = "Valid    <= Enable;"
RESET = "if (reset || Clear) begin"

# The three vectors the chapter adds after the 14 original ones.
LAST_ORIGINAL = "        {true,  false, true,      3}  // Reset nonzero/overflow state."
EXTENSION = [
    "        {false, false, true,  40000}, // Sum becomes nonzero.",
    "        {false, false, false, 40000}, // Disabled: a carry here must not report overflow.",
    "        {false, false, true,      0}, // Enabled zero operand is still a valid addition.",
]

# name, description, old text, new text, outcome with 14 vectors, outcome with 17 vectors
MUTANTS = [
    ("overflow_at_max", "overflow also at exactly 65535", OVERFLOW,
     "Overflow <= Enable && (ExtendedSum >= 17'd65535);", "fail", "fail"),
    ("overflow_sticky", "overflow never clears", OVERFLOW,
     "Overflow <= Overflow | (Enable && ExtendedSum[16]);", "fail", "fail"),
    ("overflow_ungated", "overflow ignores Enable", OVERFLOW,
     "Overflow <= ExtendedSum[16];", "pass", "fail"),
    ("valid_needs_operand", "Valid requires a nonzero operand", VALID,
     "Valid    <= Enable && (Operand != 0);", "pass", "fail"),
    ("clear_ignored", "Clear no longer clears", RESET,
     "if (reset) begin", "lint", "lint"),
]


def extended_harness(text):
    if text.count(LAST_ORIGINAL) != 1 or "std::array<Stimulus, 14>" not in text:
        raise SystemExit("The harness no longer matches the chapter listing; update EXTENSION.")
    text = text.replace("std::array<Stimulus, 14>", "std::array<Stimulus, 17>")
    return text.replace(LAST_ORIGINAL, "\n".join(EXTENSION) + "\n" + LAST_ORIGINAL)


def check_chapter_shows_extension():
    if not CHAPTER.exists():  # the extracted practice package carries no book text
        return
    text = CHAPTER.read_text(encoding="utf-8")
    for line in EXTENSION:
        if line.strip() not in text:
            raise SystemExit(f"The chapter does not show the added vector: {line.strip()}")


def build_and_run(directory, rtl_text, harness_text):
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)
    (directory / "accumulator.sv").write_text(rtl_text, encoding="utf-8", newline="\n")
    (directory / "sim_main.cpp").write_text(harness_text, encoding="utf-8", newline="\n")
    build = subprocess.run(
        ["verilator", "--cc", "--exe", "--build", "-j", "2", "-Wall", "--trace",
         "--top-module", "accumulator", "-CFLAGS", "-std=c++17",
         "--Mdir", "obj_dir", "sim_main.cpp", "accumulator.sv"],
        cwd=directory, capture_output=True, text=True, errors="replace", timeout=600)
    log = build.stdout + build.stderr
    (directory / "build.log").write_text(log, encoding="utf-8")
    warning = re.search(r"%(?:Warning|Error)-([A-Z]+):", log)
    if build.returncode:
        return {"outcome": "lint" if warning else "build-error",
                "code": warning[1] if warning else None}
    run = subprocess.run([str(directory / "obj_dir/Vaccumulator")], cwd=directory,
                         capture_output=True, text=True, errors="replace", timeout=60)
    output = (run.stdout + run.stderr).strip().splitlines()
    return {"outcome": "pass" if run.returncode == 0 else "fail",
            "first_line": output[0] if output else ""}


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    work = Path(sys.argv[1]).resolve()
    check_chapter_shows_extension()
    rtl = RTL.read_text(encoding="utf-8")
    harness = HARNESS.read_text(encoding="utf-8")
    longer = extended_harness(harness)
    for old in {m[2] for m in MUTANTS}:
        if rtl.count(old) != 1:
            raise SystemExit(f"Mutation site is not unique in the RTL: {old}")

    rows, mismatches = [], []
    healthy = build_and_run(work / "healthy-17", rtl, longer)
    rows.append({"name": "healthy", "description": "unmodified RTL, 17 vectors",
                 "14": "pass", "17": healthy["outcome"], "detail": healthy.get("first_line")})
    if healthy["outcome"] != "pass":
        mismatches.append(("healthy", "17", "pass", healthy["outcome"]))

    for name, description, old, new, expect14, expect17 in MUTANTS:
        mutated = rtl.replace(old, new, 1)
        got14 = build_and_run(work / f"{name}-14", mutated, harness)
        got17 = got14 if expect14 == "lint" else build_and_run(work / f"{name}-17", mutated, longer)
        rows.append({"name": name, "description": description,
                     "14": got14["outcome"], "17": got17["outcome"],
                     "detail": got14.get("first_line") or got14.get("code")})
        for vectors, expected, got in (("14", expect14, got14), ("17", expect17, got17)):
            if got["outcome"] != expected:
                mismatches.append((name, vectors, expected, got["outcome"]))

    (work / "mutation-report.json").write_text(
        json.dumps({"rtl": RTL.relative_to(ROOT).as_posix(), "results": rows}, indent=2) + "\n", encoding="utf-8")
    width = max(len(row["name"]) for row in rows)
    print(f"{'mutant':<{width}}  14 vectors  17 vectors")
    for row in rows:
        print(f"{row['name']:<{width}}  {row['14']:<10}  {row['17']:<10}")
    if mismatches:
        for name, vectors, expected, got in mismatches:
            print(f"MISMATCH {name} with {vectors} vectors: expected {expected}, got {got}")
        raise SystemExit(1)
    print("PASS mutation check: every outcome matches the chapter")


if __name__ == "__main__":
    main()
