"""Check the retirement comparator and the stand-in model against the recorded Spike log (no Spike needed)."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import compare_retirement as compare  # noqa: E402

START = 0x80000000
ELF_OPTION = []  # set from the command line by the lab runner, which passes the check.elf it built


def line(pc, insn, effect=""):
    return f"core   0: 3 0x{pc:016x} (0x{insn:08x}){effect}"


def items(*lines):
    return [compare.parse(text) for text in lines]


class ComparatorTest(unittest.TestCase):
    def test_boot_rom_instructions_before_the_start_pc_are_skipped(self):
        reference = items(line(0x1000, 0x297, " x5  0x0000000000001000"), line(START, 0x1C00293, " x5  0x000000000000001c"))
        dut = items(line(START, 0x1C00293, " x5  0x000000000000001c"))
        self.assertEqual(compare.compare(reference, dut, START)["status"], "identical")

    def test_first_differing_value_is_reported_with_its_fields(self):
        base = [line(START, 0x1C00293, " x5  0x000000000000001c"), line(START + 4, 0x12A613, " x12 0x0000000000000001")]
        bad = [base[0], line(START + 4, 0x12A613, " x12 0x0000000000000000")]
        result = compare.compare(items(*base), items(*bad), START)
        self.assertEqual((result["status"], result["index"], result["fields"]), ("divergence", 1, ["value"]))
        self.assertIn("FIRST DIVERGENCE at retired instruction #1", compare.describe(result))

    def test_a_different_pc_is_a_divergence_of_the_pc(self):
        reference = items(line(START, 0x6F), )
        dut = items(line(START + 4, 0x13))
        with self.assertRaises(ValueError):
            compare.compare(reference, dut, START)  # the dut never retires at the start pc
        reference = items(line(START, 0x13), line(START + 4, 0x13))
        dut = items(line(START, 0x13), line(START + 8, 0x13))
        self.assertEqual(compare.compare(reference, dut, START)["fields"], ["pc"])

    def test_logs_are_cut_at_the_first_self_jump(self):
        reference = items(line(START, 0x13), line(START + 4, 0x6F), line(START + 4, 0x6F))
        dut = items(line(START, 0x13), line(START + 4, 0x6F))
        self.assertEqual(compare.compare(reference, dut, START)["status"], "identical")

    def test_a_log_that_ends_early_is_not_reported_as_identical(self):
        reference = items(line(START, 0x13), line(START + 4, 0x13), line(START + 8, 0x6F))
        dut = items(line(START, 0x13))
        result = compare.compare(reference, dut, START)
        self.assertEqual((result["status"], result["shorter"]), ("length", "dut"))


class RecordedReferenceTest(unittest.TestCase):
    def test_recorded_log_matches_its_manifest(self):
        manifest = json.loads((HERE / "reference/spike-run.json").read_text(encoding="utf-8"))
        log = (HERE / "reference/spike-check.commit.log").read_bytes()
        self.assertEqual(hashlib.sha256(log).hexdigest(), manifest["log_sha256"])

    def test_demo_finds_the_seeded_fault_with_the_recorded_log(self):
        with tempfile.TemporaryDirectory() as directory:
            done = subprocess.run([sys.executable, str(HERE / "divergence_demo.py"), directory, *ELF_OPTION],
                                  capture_output=True, text=True)
            self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
            self.assertIn("FIRST DIVERGENCE at retired instruction #25", done.stdout)
            self.assertIn("pc 0x0000000080000028", done.stdout)


if __name__ == "__main__":
    if len(sys.argv) == 2 and not sys.argv[1].startswith("-"):
        ELF_OPTION[:] = ["--elf", sys.argv.pop(1)]
    unittest.main()
