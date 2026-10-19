import subprocess,sys
from pathlib import Path
name,image,seconds=sys.argv[1:4];command=sys.argv[4:]
identity=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',image],text=True).strip()
results_volume='from-concept-audit-faults-20261019' if name=='missing-tools' else 'from-concept-audit-results-20261019'
argv=['docker','run','--rm','--network','none','--user','1000:1000','--env','HOME=/tmp','--env','PYTHONDONTWRITEBYTECODE=1',
      '--env','CASE_IMAGE_ID='+identity,'--env','LAB_IMAGE_ID='+identity,
      '--mount','type=volume,source=from-concept-audit-source-20261019,target=/work,readonly',
      '--mount','type=volume,source='+results_volume+',target=/work/labs/build',
      '--mount','type=volume,source=from-concept-audit-downloads-20261019,target=/work/downloads',
      '--mount','type=bind,source='+str(Path(__file__).resolve().parents[3]/'tools/reproducibility')+',target=/audit-tools,readonly',
      '--mount','type=bind,source='+str(Path(__file__).resolve().parent)+',target=/audit,readonly',
      '--workdir','/work',image,*command]
raise SystemExit(subprocess.call([sys.executable,str(Path(__file__).with_name('command.py')),name,seconds,*argv]))
