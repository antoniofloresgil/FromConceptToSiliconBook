import json
from pathlib import Path
import subprocess

tools={}
for executable in ['python3','clang','gcc','verilator','dtc']:
    r=subprocess.run([executable,'--version'],capture_output=True,text=True,timeout=60)
    assert r.returncode==0,(executable,r.stderr)
    tools[executable]=r.stdout+r.stderr
packages=subprocess.check_output(['dpkg-query','-W'],text=True)
Path('/work/labs/build/audit-wally-environment.json').write_text(json.dumps(dict(tools=tools,packages=packages),indent=2)+'\n')
print('RECORDED Wally compiler, simulator, Device Tree and package versions')
