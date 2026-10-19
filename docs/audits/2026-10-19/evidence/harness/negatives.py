import hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path('/work');OUT=ROOT/'labs/build';records=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def probe(name,argv,marker,protected):
    before={str(p):sha(p) for p in protected}
    r=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True,timeout=120)
    log=OUT/('audit-negative-'+mode+'-'+name+'.txt');log.write_text(r.stdout+r.stderr)
    after={str(p):sha(p) for p in protected}
    result=dict(name=name,argv=argv,exit_code=r.returncode,marker=marker,log=log.name,log_sha256=sha(log),
        protected_sha256=before,protected_unchanged=before==after,expected_rejection=r.returncode!=0 and marker in r.stdout+r.stderr)
    records.append(result)
    (OUT/('audit-negative-controls-'+mode+'.json')).write_text(json.dumps(records,indent=2)+'\n')
    assert result['expected_rejection'] and result['protected_unchanged'],result
    print('PASS intended rejection:',name,'exit',r.returncode,flush=True)
mode=sys.argv[1]
if mode.startswith('closure'):
    repair=OUT/'audit-asic-repair'
    protected=[repair/'report.json',repair/'routed-limits.rpt',repair/'equivalence.json']
    probe('existing-asic-output',[sys.executable,str(ROOT/'labs/21-physical-closure/run.py'),'asic','--candidate','repair','--output-dir','labs/build/audit-asic-repair'],'Use a fresh directory',protected)
    probe('reference-overwrite',[sys.executable,str(ROOT/'labs/21-physical-closure/collect.py')],'Preserve reference',[ROOT/'labs/21-physical-closure/reference/results.json'])
    copied=OUT/('audit-tampered-asic-'+mode);shutil.copytree(repair,copied)
    with (copied/'routed-limits.rpt').open('a') as f:f.write('\nDeliberately altered audit copy\n')
    probe('tampered-physical-gate',[sys.executable,str(ROOT/'labs/25-hardware-ci/physical_gate.py'),str(copied)],'changed artifact',protected)
    probe('tampered-integrity',[sys.executable,'/audit-tools/verify.py','report','closure',str(copied/'report.json')],'Checksum mismatch',protected)
elif mode=='linux':
    # Separate output from the closure control set.
    probe('existing-linux-output',[sys.executable,str(ROOT/'labs/18-linux-accelerator/run.py'),'--output-dir','labs/build/audit-linux'],'Preserve evidence',[OUT/'audit-linux/report.json'])
elif mode=='fpga':
    probe('existing-fpga-output',[sys.executable,str(ROOT/'labs/21-physical-closure/run.py'),'ecp5','--candidate','pipeline','--output-dir','labs/build/audit-ecp5-pipeline'],'Use a fresh directory',[OUT/'audit-ecp5-pipeline/report.json'])
(OUT/('audit-negative-controls-'+mode+'.json')).write_text(json.dumps(records,indent=2)+'\n')
