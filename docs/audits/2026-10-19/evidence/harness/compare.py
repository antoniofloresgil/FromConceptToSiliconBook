import hashlib,importlib.util,json
from pathlib import Path
root=Path('/work');out=root/'labs/build'
spec=importlib.util.spec_from_file_location('closure',root/'labs/21-physical-closure/collect.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
reference=json.loads((root/'labs/21-physical-closure/reference/results.json').read_text())
results={}
for name in ['test-baseline','test-pipeline','asic-baseline','asic-slow','asic-repair','ecp5-slow','ecp5-pipeline','nexys-slow','nexys-pipeline']:
    folder=out/('audit-'+name)
    if not (folder/'report.json').exists():continue
    r=json.loads((folder/'report.json').read_text());assert r['status']=='completed',name
    actual=module.summarize(folder,r);expected=reference[name]
    keys=(['accepted','checked_lengths','seeds','fixture'] if name.startswith('test') else ['setup_ns','hold_ns','cell_um2','electrical_violations','power_w','router_drc_empty','unconstrained_report_empty','timing_electrical_pass']
          if name.startswith('asic') else ['requested_mhz','achieved_mhz','accepted','utilization','critical_logic_ns','critical_route_ns'])
    equal={k:actual[k]==expected[k] for k in keys}
    preserved=json.loads((root/f'labs/21-physical-closure/reference/{name}/report.json').read_text())
    mapped='mapped.v' if name.startswith('asic') else 'mapped.json'
    results[name]=dict(metrics={k:actual[k] for k in keys},reference_metrics_equal=equal,
        exact_mapped_netlist=(r['artifacts'][mapped]==preserved['artifacts'][mapped]) if not name.startswith('test') else None,
        tools_equal=r['tools']==preserved['tools'],
        technology_equal=r.get('technology_sha256',r.get('chipdb_sha256'))==preserved.get('technology_sha256',preserved.get('chipdb_sha256')))
    assert all(equal.values()),(name,equal)
    if not name.startswith('test'):assert results[name]['exact_mapped_netlist'],(name,'mapped netlist changed')
    assert results[name]['tools_equal'] and results[name]['technology_equal'],name
baseline=out/'audit-asic-baseline/mapped.v';repair=out/'audit-asic-repair/mapped.v'
if baseline.exists() and repair.exists():assert baseline.read_bytes()==repair.read_bytes(),'ASIC candidates start from different netlists'
(out/'audit-comparison.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
