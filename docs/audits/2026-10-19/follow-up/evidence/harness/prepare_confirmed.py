import json,subprocess,sys
from pathlib import Path
from external import snapshot
before=Path('/work/labs/build/audit-wally-external-before.json');assert not before.exists()
data=snapshot();assert data['revision']=='3b30ba6b6519bd2c26c1437e6d61f632a35cef6c'
before.write_text(json.dumps(data,indent=2)+'\n')
subprocess.run([sys.executable,'/audit-tools/verify.py','unchanged','/work/labs/build/audit-tool-snapshot.json'],check=True)
subprocess.run([sys.executable,'labs/18-linux-accelerator/wally.py','prepare','--bundle','labs/build/audit-linux/bundle','--output-dir','labs/build/audit-wally-rtl'],check=True)
