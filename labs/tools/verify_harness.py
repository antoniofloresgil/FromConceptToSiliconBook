"""Demonstrate that a FIFO losing accepted items fails the reference checks."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

root=Path(__file__).resolve().parents[2]
build=root/"labs/build/fault-injection"
build.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix="mutant-",dir=build) as temporary:
    rtl=Path(temporary)/"rtl"
    shutil.copytree(root/"labs/03-transport/rtl",rtl)
    source=rtl/"transport_fifo.sv"
    text=source.read_text()
    correct="2'b10: count <= count + 1'b1;"
    assert text.count(correct)==1,"mutation target changed; review the test"
    source.write_text(text.replace(correct,"2'b10: count <= count; // deliberately lose occupancy"))
    env=os.environ.copy();env["LAB_BUILD_DIR"]=str(build)
    result=subprocess.run([sys.executable,str(root/"labs/run.py"),"run","transport",
                           "--rtl-dir",str(rtl)],cwd=root,env=env,capture_output=True,text=True,timeout=120)
    report=json.loads((build/"report.json").read_text())
    entry=report["labs"]["transport"]
    commands=entry["commands"]
    assert result.returncode!=0 and entry["status"]=="fail", "incorrect RTL was accepted"
    assert commands and Path(commands[-1]["argv"][0]).name=="vvp", "failure happened before simulation"
    assert "FATAL" in (root/commands[-1]["log"]).read_text(), "no failing HDL assertion"
print("PASS harness: reference tests reject FIFO transaction loss")
