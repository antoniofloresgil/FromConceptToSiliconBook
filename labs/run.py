#!/usr/bin/env python3
"""Portable lab entry point; Python 3.10+, standard library only."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
import zipfile

from tools.catalog import LABS, SOURCES
from tools.package import EXAMPLES, MANIFEST, build_package, check_package

ROOT = Path(__file__).resolve().parent.parent
BUILD = Path(os.environ.get("LAB_BUILD_DIR", ROOT / "labs" / "build")).resolve()
if not BUILD.is_relative_to(ROOT / "labs" / "build"):
    raise RuntimeError("LAB_BUILD_DIR must stay inside labs/build")
ENV = os.environ.copy()
ENV["PYTHONDONTWRITEBYTECODE"] = "1"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_text(item):
    text = (ROOT / item["chapter"]).read_text(encoding="utf-8")
    blocks = re.findall(r"^```" + re.escape(item["language"]) + r"\s*\n(.*?)^```", text, re.M | re.S)
    selected = []
    for start in item["starts"]:
        found = [block for block in blocks if block.startswith(start)]
        if len(found) != 1:
            raise RuntimeError(f"Expected one listing {start!r} in {item['chapter']}, found {len(found)}")
        selected.append(found[0].rstrip() + "\n")
    return "\n".join(selected)


def sync(write=False):
    if (ROOT / MANIFEST).exists() and not (ROOT / 'chapters').exists():
        if write:
            raise RuntimeError('sync requires the full book repository; downloaded reference files are immutable')
        check_package(ROOT, SOURCES)
        return
    for item in SOURCES:
        path = ROOT / item["file"]
        expected = source_text(item)
        if write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8", newline="\n")
        elif not path.exists() or path.read_text(encoding="utf-8") != expected:
            raise RuntimeError(f"Chapter/listing mismatch: {item['file']}. Review the edit before using 'sync'.")
    # Existing runnable simulation examples also remain aligned with their chapters.
    for item in EXAMPLES:
        if source_text(item).strip() != (ROOT / item['file']).read_text(encoding="utf-8").strip():
            raise RuntimeError(f"Existing example differs from chapter: {item['file']}")
    print(f"PASS source provenance: {len(SOURCES)} exported files and 3 existing examples")


def check_archive_sources():
    index = ROOT / "SHA256SUMS.json"
    if index.exists():
        for name, expected in json.loads(index.read_text(encoding="utf-8")).items():
            path = (ROOT / name).resolve()
            if not path.is_relative_to(ROOT) or not path.is_file() or digest(path) != expected:
                raise RuntimeError(f"Downloaded package checksum mismatch: {name}")
        print("PASS downloaded package checksums")


def tool_info():
    result = {"python": sys.version.split()[0], "platform": platform.platform()}
    if (ROOT / MANIFEST).exists():
        provenance = json.loads((ROOT / MANIFEST).read_text(encoding='utf-8'))
        result['practice_package_source'] = provenance['source']
        result['practice_provenance_sha256'] = digest(ROOT / MANIFEST)
    for tool, flag in [("iverilog", "-V"), ("vvp", "-V"), ("verilator", "--version"),
                       ("yosys", "-V"), ("clang", "--version"), ("ld.lld", "--version"),
                       ("make", "--version"), ("g++", "--version")]:
        command = shutil.which(tool)
        if command:
            probe = subprocess.run([command, flag], capture_output=True, text=True, errors="replace", timeout=20)
            lines = (probe.stdout + probe.stderr).strip().splitlines()
            result[tool] = {"path": command, "version": lines[0] if lines else "unknown"}
        else:
            result[tool] = None
    try:
        result["cocotb"] = importlib.metadata.version("cocotb")
    except importlib.metadata.PackageNotFoundError:
        result["cocotb"] = None
    git = shutil.which("git")
    if git and (ROOT / ".git").exists():
        prefix = [git, "-c", f"safe.directory={ROOT}"]
        result["git_revision"] = subprocess.check_output([*prefix, "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        result["git_dirty"] = bool(subprocess.check_output([*prefix, "status", "--porcelain"], cwd=ROOT, text=True).strip())
    return result


class Session:
    def __init__(self, name, seed, override=None):
        self.name = name
        self.seed = seed
        self.override = override
        self.directory = BUILD / name
        self.directory.mkdir(parents=True, exist_ok=True)
        self.commands = []

    def execute(self, args, cwd=None, timeout=300):
        args = [str(arg) for arg in args]
        if not shutil.which(args[0]) and not Path(args[0]).is_file():
            raise RuntimeError(f"Missing tool: {args[0]}. See labs/README.md and the online reproduction appendix.")
        log = self.directory / f"command-{len(self.commands)+1:02d}.log"
        started = time.monotonic()
        entry = {"argv": args, "cwd": str(cwd or self.directory), "log": str(log.relative_to(ROOT))}
        self.commands.append(entry)
        with log.open("w", encoding="utf-8") as output:
            try:
                proc = subprocess.run(args, cwd=cwd or self.directory, env=ENV,
                                      stdout=output, stderr=subprocess.STDOUT, timeout=timeout)
                entry["returncode"] = proc.returncode
            except subprocess.TimeoutExpired as error:
                entry["returncode"] = "timeout"
                raise RuntimeError(f"Timed out: {args[0]}; see {log}") from error
            finally:
                entry["seconds"] = round(time.monotonic() - started, 3)
        if proc.returncode:
            print(log.read_text(encoding="utf-8", errors="replace")[-6000:])
            raise RuntimeError(f"Command failed ({proc.returncode}); see {log}")

    def sv(self, top, sources, defines=()):
        executable = self.directory / (top + "-" + "-".join(defines) + ".vvp")
        self.execute(["iverilog", "-g2012", "-s", top, *["-D"+value for value in defines],
                      "-o", executable, *sources])
        self.execute(["vvp", executable, f"+SEED={self.seed}"])


def rtl(folder, session=None):
    base = session.override if session and session.override and folder == LABS[session.name]["folder"] else ROOT / "labs" / folder / "rtl"
    files = sorted(base.glob("*.sv"))
    if not files:
        raise RuntimeError(f"No RTL sources: {base}")
    return files


def run_lab(name, session):
    folder = ROOT / "labs" / LABS[name]["folder"]
    if name == "foundations":
        session.execute([sys.executable, folder / "vectors.py", session.directory, "--seed", session.seed])
        session.sv("tb_foundations", [*rtl("01-foundations", session), folder / "tb_foundations.sv"])
        for width in (1, 8, 32):
            session.sv("tb_product", [*rtl("01-foundations", session), folder / "tb_product.sv"], [f"TEST_WIDTH={width}"])
        session.sv("tb_basics", [*rtl("01-foundations", session), folder / "tb_basics.sv"])
    elif name == "memory":
        session.sv("tb_memory", [*rtl("02-memory", session), folder / "tb_memory.sv"])
        session.execute([sys.executable, folder / "test_cache.py", "--seed", session.seed])
    elif name == "transport":
        for depth in (2, 3, 8):
            session.sv("tb_transport", [*rtl("03-transport", session), folder / "tb_transport.sv"], [f"TEST_DEPTH={depth}"])
    elif name == "mmio":
        for top in ("tb_apb", "tb_axil", "tb_fifo_pwm"):
            session.sv(top, [*rtl("04-mmio", session), folder / (top+".sv")])
        session.execute(["clang", "--target=riscv32", "-march=rv32im", "-mabi=ilp32", "-ffreestanding",
                         "-Wall", "-Wextra", "-Werror", "-c", folder / "mmio_drivers.c", "-o", session.directory / "mmio_drivers.o"])
    elif name == "isa":
        session.execute(["clang", "--target=riscv32", "-march=rv32i", "-mabi=ilp32", "-c", folder / "isa_demo.S", "-o", session.directory / "isa_demo.o"])
        session.execute(["ld.lld", "-m", "elf32lriscv", "--no-relax", "-T", folder / "isa_demo.ld",
                         session.directory / "isa_demo.o", "-o", session.directory / "isa_demo.elf"])
        session.execute([sys.executable, folder / "check_signature.py", session.directory / "isa_demo.elf"])
    elif name == "verilator":
        objects = session.directory / "obj_dir"
        session.execute(["verilator", "--cc", "--exe", "--build", "--trace", "-Wall",
                         "--top-module", "accumulator", "--Mdir", objects,
                         ROOT / "examples/verilator/accumulator.sv", ROOT / "examples/verilator/sim_main.cpp"])
        session.execute([objects / "Vaccumulator"])
        session.execute([sys.executable, folder / "mutation_check.py", session.directory / "mutation"], timeout=900)
    elif name == "cocotb":
        if importlib.metadata.version("cocotb") != "2.0.1":
            raise RuntimeError("This baseline requires cocotb==2.0.1; install labs/requirements.txt")
        result = session.directory / "results.xml"
        if result.exists():
            result.unlink()
        session.execute(["make", "-C", ROOT / "examples/cocotb", "SIM=icarus",
                         f"SIM_BUILD={session.directory / 'sim_build'}", f"COCOTB_RESULTS_FILE={result}"])
        cases = ET.parse(result).getroot().findall(".//testcase")
        if not cases or any(case.find("failure") is not None or case.find("error") is not None or case.find("skipped") is not None for case in cases):
            raise RuntimeError("cocotb produced no successful complete test suite")
    elif name == "dotproduct":
        session.execute([sys.executable, folder / "vectors.py", session.directory, session.seed])
        for maximum in (256, 16):
            session.execute(["iverilog", "-g2012", "-I", folder, "-s", "tb_dotproduct",
                             f"-DTEST_MAX_LENGTH={maximum}", "-o", session.directory / "dotproduct.vvp",
                             *rtl("10-dotproduct", session), folder / "axi_ram_model.sv", folder / "tb_dotproduct.sv"])
            session.execute(["vvp", session.directory / "dotproduct.vvp", f"+SEED={session.seed}"])
        session.execute(["iverilog", "-g2012", "-I", folder, "-s", "tb_bridge",
                         "-o", session.directory / "bridge.vvp", *rtl("10-dotproduct", session),
                         folder / "axi_ram_model.sv", folder / "tb_bridge.sv"])
        session.execute(["vvp", session.directory / "bridge.vvp"])
        files = " ".join('"'+p.as_posix()+'"' for p in rtl("10-dotproduct", session))
        session.execute(["yosys", "-Q", "-T", "-p", f'read_verilog -sv {files}; synth -top dotproduct_axi; check -assert; select -assert-none t:$dlatch; stat; write_json dotproduct.json'])
        session.execute([sys.executable, folder / "formal/check.py", session.directory,
                         session.override or folder / "rtl"], timeout=600)
    elif name == "dotproduct-wally":
        wally = os.environ.get("WALLY_ROOT")
        if not wally:
            raise RuntimeError("Set WALLY_ROOT to a clone containing the pinned Wally revision; see labs/10-dotproduct/README.md")
        vendor = session.directory / "vendor"
        session.execute([sys.executable, folder / "prepare_wally.py", "export", wally, vendor])
        firmware = folder / "firmware"
        elf = session.directory / "firmware.elf"
        session.execute(["clang", "--target=riscv32", "-march=rv32im_zicsr", "-mabi=ilp32",
                         "-O2", "-ffreestanding", "-fno-builtin", "-fno-stack-protector",
                         "-msmall-data-limit=0", "-Wall", "-Wextra", "-Werror", "-nostdlib",
                         "-fuse-ld=lld", "-Wl,--no-relax", "-Wl,-T,"+str(firmware / "link.ld"),
                         firmware / "start.S", firmware / "main.c", "-o", elf])
        session.execute([sys.executable, folder / "prepare_wally.py", "hex", elf, session.directory / "firmware.hex"])
        package = vendor / "src/cvw.sv"
        sources = [package, *[p for p in sorted((vendor / "src").rglob("*.sv")) if p != package]]
        objects = session.directory / "obj_dir"
        session.execute(["verilator", "--binary", "--timing", "-j", "2", "-Wno-fatal",
                         "--top-module", "tb_wally_dotproduct", "--Mdir", objects,
                         "-I"+str(vendor / "config/rv32imc"), "-I"+str(vendor / "config/shared"),
                         "-I"+str(folder), *sources, *rtl("10-dotproduct", session),
                         folder / "axi_ram_model.sv", folder / "tb_wally_dotproduct.sv"], timeout=600)
        session.execute([objects / "Vtb_wally_dotproduct", f"+SEED={session.seed}"], timeout=300)
    elif name == "synthesis":
        session.sv("tb_implementation", [*rtl("07-implementation", session), folder / "tb_implementation.sv"])
        for source in [*rtl("01-foundations"), *rtl("02-memory"), *rtl("03-transport"), *rtl("04-mmio"), *rtl("07-implementation", session)]:
            top = source.stem
            files = " ".join('"'+p.as_posix()+'"' for p in sorted(source.parent.glob("*.sv")))
            script = f'read_verilog -sv {files}; hierarchy -check -top {top}; proc; opt; check -assert; select -assert-none t:$dlatch; stat'
            session.execute(["yosys", "-Q", "-T", "-p", script])
        source = (session.override or folder / "rtl") / "accumulator.sv"
        script = f'read_verilog -sv "{source.as_posix()}"; synth -top accumulator; check -assert; stat; write_json accumulator.json; write_verilog accumulator-netlist.v'
        session.execute(["yosys", "-Q", "-T", "-p", script])
    else:
        raise RuntimeError(f"{name} is {LABS[name]['mode']}: follow labs/{LABS[name]['folder']}/README.md")


def run(names, seed, override=None):
    sync()
    check_archive_sources()
    BUILD.mkdir(parents=True, exist_ok=True)
    report = {"seed": seed, "environment": tool_info(), "sources": {}, "labs": {}}
    for base in ("labs", "examples"):
        for path in (ROOT / base).rglob("*"):
            if path.is_file() and not path.is_symlink() and not any(part in {"build", "work", "__pycache__", ".venv", "sim_build", "obj_dir", "runs"} for part in path.relative_to(ROOT).parts):
                report["sources"][path.relative_to(ROOT).as_posix()] = digest(path)
    failed = False
    for name in names:
        actual_seed = 2026 if name in {"verilator", "cocotb"} else seed
        session = Session(name, actual_seed, override)
        record = {"mode": LABS[name]["mode"], "seed": actual_seed, "commands": session.commands}
        if override:
            record["student_rtl"] = {str(path): digest(path) for path in override.glob("*.sv")}
        report["labs"][name] = record
        try:
            run_lab(name, session)
            record["status"] = "pass"
            print(f"PASS {name}")
        except (RuntimeError, OSError, ET.ParseError, importlib.metadata.PackageNotFoundError) as error:
            failed = True
            record.update(status="fail", error=str(error))
            print(f"FAIL {name}: {error}", file=sys.stderr)
        record["artifacts"] = {str(path.relative_to(ROOT)): digest(path) for path in session.directory.rglob("*") if path.is_file()}
    report_path = BUILD / "report.json"
    report_path.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(f"Report: {report_path}")
    return 1 if failed else 0


def pack():
    if not (ROOT / 'chapters').is_dir():
        raise RuntimeError('pack requires the full book repository')
    sync()
    build_package(ROOT, SOURCES)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["list", "doctor", "check", "sync", "run", "pack"])
    parser.add_argument("lab", nargs="?", default="all", choices=["all", *LABS])
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--rtl-dir", type=Path, help="Student RTL override for one unit lab; keeps reference sources intact")
    args = parser.parse_args()
    if args.command == "list":
        for name, lab in LABS.items():
            print(f"{name:14} {lab['mode']:10} {lab['goal']}")
    elif args.command == "doctor":
        print(json.dumps(tool_info(), indent=2))
    elif args.command in {"check", "sync"}:
        sync(write=args.command == "sync")
        if args.command == "check":
            check_archive_sources()
    elif args.command == "pack":
        pack()
    elif args.command == "run":
        if args.rtl_dir and args.lab not in {"foundations", "memory", "transport", "mmio", "synthesis", "dotproduct", "dotproduct-wally"}:
            parser.error("--rtl-dir requires one specific RTL unit lab, not 'all'")
        names = [name for name, lab in LABS.items() if lab["mode"] == "automatic"] if args.lab == "all" else [args.lab]
        return run(names, args.seed, args.rtl_dir.resolve() if args.rtl_dir else None)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
