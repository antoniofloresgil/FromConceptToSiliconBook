#!/usr/bin/env python3
"""Find the first divergent instruction between a reference log and a faulty stand-in (standard library only).

Runs the book's RV64I program through the stand-in model twice, without and with a seeded fault, compares each
retirement log with the Spike reference log, and compares the signature words too. By default the reference is the
recorded Spike log in labs/06-isa/reference/. With --spike PATH the reference is produced live (and --record
refreshes the recorded log, which then needs its manifest updated).
Usage: python labs/06-isa/divergence_demo.py BUILD_DIRECTORY [--spike spike] [--record]
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ELF = ROOT / "examples/reference-models/check.elf"
EXPECTED = ROOT / "examples/reference-models/expected.signature"
RECORDED = HERE / "reference/spike-check.commit.log"
START = 0x80000000
EXPECTED_DIVERGENCE_PC = 0x80000028  # slti a2,t0,1

sys.path.insert(0, str(HERE))
import compare_retirement as compare  # noqa: E402


def trimmed(text):
    """Keep a Spike log up to its first self-jump, so the recorded evidence stays small."""
    kept = []
    for line in text.splitlines():
        kept.append(line)
        item = compare.parse(line)
        if item and item["insn"] == compare.SELF_JUMP:
            break
    return "\n".join(kept) + "\n"


def run_model(work, name, fault):
    log, signature = work / f"{name}.log", work / f"{name}.sig"
    subprocess.run([sys.executable, str(HERE / "retire_model.py"), str(ELF), "--log", str(log),
                    "--signature", str(signature), "--fault", fault], check=True)
    return log, signature


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("build")
    parser.add_argument("--spike")
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args()
    work = Path(args.build).resolve()
    work.mkdir(parents=True, exist_ok=True)

    reference = RECORDED
    if args.spike:
        live = work / "spike.log"
        subprocess.run([args.spike, "--isa=rv64i", "--log-commits", f"--log={live}", str(ELF)], check=True)
        reference = work / "spike-trimmed.log"
        reference.write_text(trimmed(live.read_text(encoding="utf-8")), encoding="utf-8")
        if args.record:
            RECORDED.parent.mkdir(exist_ok=True)
            RECORDED.write_text(reference.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    ref_items = compare.retired(reference)

    report = {"reference": "spike" if args.spike else RECORDED.relative_to(ROOT).as_posix()}
    healthy_log, healthy_sig = run_model(work, "healthy", "none")
    faulty_log, faulty_sig = run_model(work, "faulty", "slt-unsigned")

    healthy = compare.compare(ref_items, compare.retired(healthy_log), START)
    print("healthy stand-in:", compare.describe(healthy))
    faulty = compare.compare(ref_items, compare.retired(faulty_log), START)
    print("faulty stand-in:")
    print(compare.describe(faulty))

    expected = EXPECTED.read_text(encoding="utf-8").split()
    for name, sig in (("healthy", healthy_sig), ("faulty", faulty_sig)):
        words = sig.read_text(encoding="utf-8").split()
        report[f"{name}_signature_matches"] = words == expected
        print(f"{name} signature:", "matches expected.signature" if words == expected else
              "differs at word(s) " + ", ".join(str(i + 1) for i, (a, b) in enumerate(zip(words, expected)) if a != b))

    ok = (healthy["status"] == "identical"
          and faulty["status"] == "divergence" and faulty["reference"]["pc"] == EXPECTED_DIVERGENCE_PC
          and faulty["fields"] == ["value"] and report["healthy_signature_matches"]
          and not report["faulty_signature_matches"])
    report.update({"healthy_status": healthy["status"], "healthy_compared": healthy["compared"],
                   "faulty_status": faulty["status"], "faulty_index": faulty.get("index"),
                   "faulty_pc": hex(faulty["reference"]["pc"]) if faulty["status"] == "divergence" else None,
                   "reference_sha256": hashlib.sha256(Path(reference).read_bytes()).hexdigest()})
    (work / "divergence-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not ok:
        raise SystemExit("The outcomes differ from the ones the chapter reports")
    print("PASS divergence demo: the healthy model matches Spike and the seeded fault is found at the first differing instruction")


if __name__ == "__main__":
    main()
