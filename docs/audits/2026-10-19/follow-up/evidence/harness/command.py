import datetime,hashlib,json,subprocess,sys,time
from pathlib import Path
base=Path(__file__).resolve().parent
name,seconds,cwd=sys.argv[1:4];argv=sys.argv[4:]
record=dict(name=name,argv=argv,cwd=cwd,started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
log=base/(name+'.log');started=time.monotonic()
try:
 with log.open('wb') as stream:r=subprocess.run(argv,cwd=cwd,stdout=stream,stderr=subprocess.STDOUT,timeout=int(seconds))
 record.update(exit_code=r.returncode,status='pass' if r.returncode==0 else 'fail')
except Exception as error:record.update(exit_code=None,status='error',error=str(error))
record.update(seconds=round(time.monotonic()-started,3),log=log.name,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
(base/(name+'.json')).write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record));sys.exit(0 if record['status']=='pass' else 1)
