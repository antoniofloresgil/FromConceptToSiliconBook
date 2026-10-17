#!/usr/bin/env python3
"""Actual GDS DRC/LVS and a physical finishing continuation; pinned Nangate45."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PDK=Path('/OpenROAD-flow-scripts/flow/platforms/nangate45')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def drc_metrics(path):
    e=ET.parse(path).getroot()
    return dict(categories=len(e.findall('.//categories/category')),markers=len(e.findall('.//items/item')),
                by_category=dict(Counter(x.findtext('category') for x in e.findall('.//items/item'))))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input-dir',default='labs/build/closure-final-asic-repair')
    p.add_argument('--output-dir',required=True)
    a=p.parse_args()
    src=(ROOT/a.input_dir).resolve();out=(ROOT/a.output_dir).resolve()
    if not src.is_relative_to(ROOT/'labs/build') or not out.is_relative_to(ROOT/'labs/build') or out.exists():raise ValueError('Use existing input and fresh output under labs/build')
    old=json.loads((src/'report.json').read_text())
    if old['status']!='completed' or old['candidate']!='repair' or old['target']!='asic':raise ValueError('Expected completed ASIC repair')
    for n in ['routed.odb','routed.sdc','routed.def','dotproduct_axi.gds']:
        if sha(src/n)!=old['artifacts'][n]:raise ValueError('Altered input '+n)
    out.mkdir(parents=True)
    inputs=[HERE/'run.py',HERE/'finish.tcl',HERE/'lvs.lvs',HERE/'layout.py',ROOT/'labs/17-complete-case/streamout.py']
    record=dict(status='running',image=os.environ.get('CASE_IMAGE_ID','unrecorded'),
                input_report_sha256=sha(src/'report.json'),
                sources={f.relative_to(ROOT).as_posix():sha(f) for f in inputs},
                input_artifacts={n:sha(src/n) for n in ['routed.odb','routed.sdc','routed.def','dotproduct_axi.gds']},
                technology={str(f.relative_to(PDK)):sha(f) for f in [PDK/'drc/FreePDK45.lydrc',PDK/'cdl/NangateOpenCellLibrary.cdl',PDK/'gds/NangateOpenCellLibrary.gds',PDK/'rcx_patterns.rules',PDK/'lib/NangateOpenCellLibrary_typical.lib',PDK/'lef/NangateOpenCellLibrary.macro.mod.lef']},
                tools={},commands=[],manufacturing_qualified=False)
    def save():(out/'report.json').write_text(json.dumps(record,indent=2)+'\n')
    def run(argv,timeout=900):
        name=f'command-{len(record["commands"])+1:02d}.txt'
        item={'argv':list(map(str,argv)),'log':name};record['commands'].append(item);save()
        with (out/name).open('w') as f:
            result=subprocess.run(item['argv'],cwd=out,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
        item['exit_code']=result.returncode;save()
        if result.returncode or '[ERROR ' in (out/name).read_text():raise RuntimeError('Inspect '+name)
    save()
    try:
        record['tools']['openroad']=subprocess.check_output(['openroad','-version'],text=True).strip()
        record['tools']['klayout']=subprocess.check_output(['klayout','-v'],text=True).strip()
        # Flatten execution avoids pathological deep-boolean performance here;
        # no rule or FEOL/BEOL/OFFGRID/ANTENNA group is disabled.
        text=(PDK/'drc/FreePDK45.lydrc').read_text()
        if text.count('\ndeep\n')!=1:raise ValueError('Review changed DRC deck')
        (out/'flat.lydrc').write_text(text.replace('\ndeep\n','\n# Flat execution; same rules\n'))
        os.environ.update(VERIFY_INPUT=str(src),VERIFY_OUT=str(out))
        run(['openroad','-no_init','-exit','-threads','2',HERE/'finish.tcl'])
        if sha(out/'functional-before.txt')!=sha(out/'functional-after.txt'):raise ValueError('Functional cells, placement or signal connectivity changed')
        run(['klayout','-zz','-rd',f'out={out}','-rm',ROOT/'labs/17-complete-case/streamout.py'])
        run(['klayout','-zz','-rd',f'out={out}','-rd',f'source={out}/dotproduct_axi.gds','-rm',HERE/'layout.py'])
        cell_cdl=(PDK/'cdl/NangateOpenCellLibrary.cdl').read_text()
        if set(re.findall(r'\b[NP]MOS_[A-Z]+\b',cell_cdl))!={'NMOS_VTL','PMOS_VTL'}:raise ValueError('Unsupported cell flavour')
        for state in ['baseline','reconnected','finished']:
            (out/(state+'-reference.cdl')).write_text((out/(state+'.cdl')).read_text()+cell_cdl)
        def drc(label,gds):
            run(['klayout','-zz','-rd',f'in_gds={gds}','-rd',f'report_file={out}/{label}.lyrdb','-r',out/'flat.lydrc'])
            return drc_metrics(out/(label+'.lyrdb'))
        def lvs(label,gds,reference):
            run(['klayout','-b','-rd',f'in_gds={gds}','-rd',f'cdl_file={reference}',
                 '-rd',f'report_file={out}/{label}.lvsdb','-rd',f'l2n_file={out}/{label}.l2n',
                 '-rd',f'extracted_file={out}/{label}.cir','-rd',f'summary_file={out}/{label}.json','-r',HERE/'lvs.lvs'])
            return json.loads((out/(label+'.json')).read_text())
        result={}
        result['baseline_drc']=drc('baseline-drc',src/'dotproduct_axi.gds')
        result['baseline_lvs']=lvs('baseline-lvs',src/'dotproduct_axi.gds',out/'baseline-reference.cdl')
        result['finished_drc']=drc('finished-drc',out/'dotproduct_axi.gds')
        result['finished_lvs']=lvs('finished-lvs',out/'dotproduct_axi.gds',out/'finished-reference.cdl')
        result['negative_drc']=drc('negative-drc',out/'bad-drc.gds')
        result['negative_lvs']=lvs('negative-lvs',out/'bad-lvs.gds',out/'finished-reference.cdl')
        result['pg']=json.loads((out/'power-connectivity.json').read_text())
        result['timing']=json.loads((out/'timing.json').read_text())
        result['electrical_violations']=(out/'limits.rpt').read_text().count('(VIOLATED)')
        result['unconstrained_report_empty']=not (out/'constraints.rpt').read_text().strip()
        result['functional_snapshot_equal']=True
        result['reference_gate_pass']=bool(result['finished_drc']['markers']==0 and result['finished_lvs']['match'] and result['pg']['missing_pg_finished']==0 and min(result['timing'].values())>=0 and result['electrical_violations']==0 and result['unconstrained_report_empty'])
        result['manufacturing_qualified']=False
        if not result['negative_drc']['markers'] or result['negative_lvs']['match']:raise ValueError('Checker negative control failed')
        if sum(result['finished_lvs']['layout']['devices'].values())<10000:raise ValueError('Vacuous transistor extraction')
        (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
        record['status']='completed'
        for name,d in record['sources'].items():
            if sha(ROOT/name)!=d:raise ValueError('Source changed during run')
    except Exception as e:
        record.update(status='failed',error=str(e));raise
    finally:
        record['artifacts']={f.name:sha(f) for f in out.iterdir() if f.is_file() and f.name!='report.json'}
        save()
    print('COMPLETED actual reference DRC/LVS; gate=',result['reference_gate_pass'],'; no foundry qualification')

if __name__=='__main__':main()
