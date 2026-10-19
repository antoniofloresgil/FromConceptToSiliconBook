import datetime,hashlib,json,subprocess,sys,time
from pathlib import Path
root=Path(__file__).resolve().parent
name=sys.argv[1];timeout=int(sys.argv[2]);argv=sys.argv[3:]
record=dict(name=name,argv=argv,cwd=str(root/'source'),started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
log=root/(name+'.log');receipt=root/(name+'.json')
started=time.monotonic()
try:
    with log.open('wb') as f:
        result=subprocess.run(argv,cwd=root/'source',stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
    record.update(exit_code=result.returncode,status='pass' if result.returncode==0 else 'fail')
except Exception as e:
    record.update(exit_code=None,status='error',error=str(e))
finally:
    record.update(seconds=round(time.monotonic()-started,3),log=log.name,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
    receipt.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record),flush=True)
sys.exit(0 if record['status']=='pass' else 1)
