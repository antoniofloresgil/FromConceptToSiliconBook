import json,platform,shutil,subprocess,sys
from pathlib import Path
def output(argv):
    r=subprocess.run(argv,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
    return dict(argv=argv,exit_code=r.returncode,text=r.stdout)
tools={}
for exe,arg in [('python3','--version'),('yosys','-V'),('iverilog','-V'),('verilator','--version'),
                ('nextpnr-ecp5','--version'),('nextpnr-xilinx','--version'),('openroad','-version'),
                ('klayout','-v'),('qemu-system-riscv64','--version'),('riscv64-linux-gnu-gcc','--version')]:
    if shutil.which(exe):tools[exe]=output([exe,'-zz',arg] if exe=='klayout' else [exe,arg])
data=dict(kind=sys.argv[1],python=sys.version,platform=platform.platform(),tools=tools,
          debian_packages=output(['dpkg-query','-W']))
for python in ['/opt/labs-venv/bin/python','/opt/xray-python/bin/python']:
    if Path(python).exists():data[python]=output([python,'-m','pip','freeze'])
out=Path('/work/labs/build')/('audit-environment-'+sys.argv[1]+'.json')
out.write_text(json.dumps(data,indent=2)+'\n');print('RECORDED environment',sys.argv[1])
