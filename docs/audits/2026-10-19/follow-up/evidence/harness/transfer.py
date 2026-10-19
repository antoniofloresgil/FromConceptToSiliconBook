from pathlib import Path
import subprocess

out=Path(__file__).resolve().parent/'exported'
assert not out.exists();out.mkdir()
identifier=subprocess.check_output(['docker','create','--network','none','--mount',
    'type=volume,source=from-concept-audit-results-20261019,target=/results,readonly',
    'from-concept-audit-wally:20261019','true'],text=True).strip()
try:subprocess.run(['docker','cp',identifier+':/results/audit-followup-export/.',str(out)],check=True)
finally:subprocess.run(['docker','rm',identifier],check=True)
print('COPIED compact Wally follow-up evidence')
