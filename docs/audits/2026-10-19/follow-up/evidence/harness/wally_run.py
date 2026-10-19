import subprocess,sys
from pathlib import Path
base=Path(__file__).resolve().parent
name,seconds=sys.argv[1:3];image='from-concept-audit-wally:20261019'
identity=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',image],text=True).strip()
args=['docker','run','--rm','--network','none','--user','1000:1000','--env','HOME=/tmp',
 '--env','PYTHONDONTWRITEBYTECODE=1','--env','CASE_IMAGE_ID='+identity,'--env','WALLY_ROOT=/cvw',
 '--mount','type=volume,source=from-concept-audit-source-20261019,target=/work,readonly',
 '--mount','type=volume,source=from-concept-audit-results-20261019,target=/work/labs/build',
 '--mount','type=volume,source=from-concept-audit-wally-source-20261019,target=/cvw,readonly',
 '--mount','type=bind,source='+str(base)+',target=/audit,readonly',
 '--mount','type=bind,source='+str(base.parents[2]/'tools/reproducibility')+',target=/audit-tools,readonly',
 '--workdir','/work',image,*sys.argv[3:]]
raise SystemExit(subprocess.call([sys.executable,str(base/'command.py'),name,seconds,str(base.parents[2]),*args]))
