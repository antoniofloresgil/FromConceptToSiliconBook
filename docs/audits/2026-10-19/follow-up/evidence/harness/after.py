import json,subprocess,sys,time
from pathlib import Path
base=Path(__file__).resolve().parent
for name in sys.argv[1].split(','):
 path=base/(name+'.json');deadline=time.monotonic()+10000
 while not path.exists():
  if time.monotonic()>deadline:raise SystemExit('Dependency timeout: '+name)
  time.sleep(2)
 assert json.loads(path.read_text())['status']=='pass','Failed dependency '+name
raise SystemExit(subprocess.call(sys.argv[2:]))
