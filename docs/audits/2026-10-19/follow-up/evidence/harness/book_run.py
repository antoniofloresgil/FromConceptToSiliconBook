import subprocess,sys
from pathlib import Path
base=Path(__file__).resolve().parent;root=base.parents[2]
name,seconds=sys.argv[1:3];image='from-concept-audit-book:20261019'
identity=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',image],text=True).strip()
args=['docker','run','--rm','--platform','linux/amd64','--network','none','--user','1000:1000',
 '--env','HOME=/tmp','--env','BOOK_IMAGE_ID='+identity,'--mount','type=bind,source='+str(root)+',target=/work',
 '--mount','type=bind,source='+str(base)+',target=/audit,readonly','--workdir','/work',image,*sys.argv[3:]]
raise SystemExit(subprocess.call([sys.executable,str(base/'command.py'),name,seconds,str(root),*args]))
