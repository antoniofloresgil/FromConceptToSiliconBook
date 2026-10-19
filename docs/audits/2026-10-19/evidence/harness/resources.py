import datetime,json,os
from pathlib import Path
records=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit() or int(p.name)==os.getpid():continue
 try:
  c=(p/'cmdline').read_bytes()
  if not (b'bbaexport.py\0--device' in c or b'build/bba/bbasm\0--l' in c):continue
  values=dict(line.split(':',1) for line in (p/'status').read_text().splitlines() if ':' in line)
  stat=(p/'stat').read_text().split()
  records.append(dict(pid=p.name,command=c.replace(b'\0',b' ').decode(),
   status={k:values.get(k,'').strip() for k in ['Name','State','VmRSS','VmSwap','Threads']},
   user_ticks=int(stat[13]),system_ticks=int(stat[14]),clock_ticks=os.sysconf('SC_CLK_TCK')))
 except (OSError,PermissionError):pass
print(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),processes=records),indent=2))
