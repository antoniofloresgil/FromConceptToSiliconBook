import importlib.util,json,subprocess
from pathlib import Path
root=Path('/work');base=root/'labs/build'
spec=importlib.util.spec_from_file_location('integrity','/audit-tools/verify.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
checks={}
for name in ['test-baseline','test-pipeline','asic-baseline','asic-slow','asic-repair','ecp5-slow','ecp5-pipeline','nexys-slow','nexys-pipeline']:
 checks[name]=v.report(root,base/('audit-'+name)/'report.json','closure')
for name,kind,path in [('formal','formal','formal'),('linux','linux','audit-linux'),('layout','layout','audit-layout')]:
 checks[name]=v.report(root,base/path/'report.json',kind)
comparison=json.loads((base/'audit-comparison.json').read_text());assert len(comparison)==9
netlists=[(base/('audit-asic-'+x)/'mapped.v').read_bytes() for x in ['baseline','slow','repair']]
assert netlists[0]==netlists[1]==netlists[2]
before=json.loads((base/'audit-source-before.json').read_text())
after=v.snapshot(root)
assert before['revision']==after['revision'] and before['files']==after['files']
v.compare_snapshot(root,json.loads((base/'audit-tool-snapshot.json').read_text()))
(base/'audit-source-after.json').write_text(json.dumps(after,indent=2)+'\n')
result=dict(status='pass',revision=after['revision'],integrity=checks,closure_comparison_cases=len(comparison),
 tracked_files=len(after['files']),retained_reference_files=sum('/reference/' in n for n in after['files']),
 unchanged_sources_and_references=True,identical_three_asic_mapped_netlists=True)
(base/'audit-final-checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
