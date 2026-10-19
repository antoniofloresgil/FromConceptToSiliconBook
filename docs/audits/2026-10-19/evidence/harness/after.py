import json,subprocess,sys,time
from pathlib import Path
root=Path(__file__).resolve().parent
deadline=time.monotonic()+7500
for dependency in sys.argv[1].split(','):
    path=root/(dependency+'.json')
    while not path.is_file():
        if time.monotonic()>deadline:raise SystemExit('Dependency did not finish: '+dependency)
        time.sleep(2)
    result=json.loads(path.read_text())
    if result['status']!='pass':raise SystemExit('Dependency failed: '+dependency)
raise SystemExit(subprocess.call(sys.argv[2:]))
