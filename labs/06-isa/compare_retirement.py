#!/usr/bin/env python3
"""Compare two retirement logs and report the first divergent instruction (standard library only).

Both logs use the shape of Spike's --log-commits output:
    core   0: 3 0x0000000080000028 (0x0012a613) x12 0x0000000000000001
The reference log may start in a boot ROM, so both logs are aligned at the first retirement of the
start PC (the ELF entry) and cut at the first self-jump, which marks completion in the test program.

Usage: python compare_retirement.py REFERENCE.log DUT.log --start 0x80000000
Exit status: 0 identical, 1 divergence, 2 one log ends before the other.
"""
import argparse
from pathlib import Path
import re
import sys

LINE = re.compile(r"^core\s+\d+:\s+\d+\s+0x([0-9a-f]+)\s+\(0x([0-9a-f]+)\)(.*)$")
REG = re.compile(r"\bx(\d+)\s+0x([0-9a-f]+)")
MEM = re.compile(r"\bmem\s+0x([0-9a-f]+)(?:\s+0x([0-9a-f]+))?")
SELF_JUMP = 0x0000006F  # jal x0, 0


def parse(line):
    """Return the architectural effect of one retirement line, or None for other text."""
    match = LINE.match(line.strip())
    if not match:
        return None
    pc, insn, rest = int(match[1], 16), int(match[2], 16), match[3]
    reg = REG.search(rest)
    mem = MEM.search(rest)
    return {
        "pc": pc,
        "insn": insn,
        "rd": int(reg[1]) if reg else None,
        "value": int(reg[2], 16) if reg else None,
        "mem_addr": int(mem[1], 16) if mem else None,
        "mem_value": int(mem[2], 16) if mem and mem[2] else None,
        "text": line.strip(),
    }


def retired(path):
    return [item for item in (parse(line) for line in Path(path).read_text(encoding="utf-8").splitlines()) if item]


def align(items, start):
    """Drop everything before the first retirement at `start` and after the first self-jump."""
    for index, item in enumerate(items):
        if item["pc"] == start:
            items = items[index:]
            break
    else:
        raise ValueError(f"start pc 0x{start:x} never retires")
    for index, item in enumerate(items):
        if item["insn"] == SELF_JUMP:
            return items[:index + 1]
    return items


FIELDS = ("pc", "insn", "rd", "value", "mem_addr", "mem_value")
NAMES = {"pc": "pc", "insn": "encoding", "rd": "destination register", "value": "destination value",
         "mem_addr": "memory address", "mem_value": "memory value"}


def compare(reference, dut, start):
    ref, got = align(reference, start), align(dut, start)
    for index, (a, b) in enumerate(zip(ref, got)):
        different = [name for name in FIELDS if a[name] != b[name]]
        if different:
            return {"status": "divergence", "index": index, "compared": index, "reference": a, "dut": b,
                    "fields": different, "context": ref[max(0, index - 3):index]}
    if len(ref) != len(got):
        shorter = "dut" if len(got) < len(ref) else "reference"
        return {"status": "length", "compared": min(len(ref), len(got)), "shorter": shorter,
                "reference_length": len(ref), "dut_length": len(got)}
    return {"status": "identical", "compared": len(ref)}


def describe(result):
    if result["status"] == "identical":
        return f"identical: {result['compared']} retired instructions compared"
    if result["status"] == "length":
        return (f"one log ends early: the {result['shorter']} stops after {result['compared']} retired "
                f"instructions (reference {result['reference_length']}, dut {result['dut_length']})")
    a, b = result["reference"], result["dut"]
    lines = [f"FIRST DIVERGENCE at retired instruction #{result['index']} "
             f"(counting from the start pc), pc 0x{a['pc']:016x}, encoding 0x{a['insn']:08x}",
             "  differing: " + ", ".join(NAMES[name] for name in result["fields"]),
             "  reference: " + a["text"],
             "  dut:       " + b["text"]]
    if result["context"]:
        lines.append("  last matching instructions:")
        lines += ["    " + item["text"] for item in result["context"]]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("reference")
    parser.add_argument("dut")
    parser.add_argument("--start", type=lambda text: int(text, 0), required=True)
    args = parser.parse_args()
    result = compare(retired(args.reference), retired(args.dut), args.start)
    print(describe(result))
    sys.exit({"identical": 0, "divergence": 1, "length": 2}[result["status"]])


if __name__ == "__main__":
    main()
