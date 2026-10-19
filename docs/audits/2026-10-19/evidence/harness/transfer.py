import subprocess
from pathlib import Path
out=Path(__file__).resolve().parent/'exported'
assert not out.exists();out.mkdir()
identifier=subprocess.check_output(['docker','create','--network','none','--mount',
 'type=volume,source=from-concept-audit-results-20261019,target=/results,readonly',
 'from-concept-audit-labs:20261019','true'],text=True).strip()
try:
 subprocess.run(['docker','cp',identifier+':/results/audit-export/.',str(out)],check=True)
finally:subprocess.run(['docker','rm',identifier],check=True)
print('COPIED compact audit evidence')
