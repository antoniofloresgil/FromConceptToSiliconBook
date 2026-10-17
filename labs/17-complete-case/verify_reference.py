#!/usr/bin/env python3
"""Audit the compact joined dossier, not a replacement for executing its tools."""
import json
from pathlib import Path
from run import ROOT, SOURCE, load_manifest, sha


def require(condition, message):
    if not condition: raise ValueError(message)


def main():
    manifest=load_manifest()
    reference=SOURCE/'reference'
    inventory=json.loads((reference/'inventory.json').read_text())
    digest=sha(SOURCE/'manifest.json')
    require(inventory['manifest_sha256']==digest,'Different common release')
    require(inventory['collector_sha256']==sha(SOURCE/'collect.py'),'Collector recipe changed')
    for name,expected in inventory['files'].items():
        p=(ROOT/name).resolve()
        require(p.is_relative_to(ROOT) and p.is_file() and sha(p)==expected,'Modified/missing dossier: '+name)
    for name,expected in inventory['visual_scripts'].items():
        require(sha(SOURCE/name)==expected,'Visual-generation recipe changed')
    extracted=(ROOT/'LAB-PROVENANCE.json').is_file() and not (ROOT/'chapters').exists()
    if not extracted:
        for name,expected in inventory['figures'].items():
            require((ROOT/name).is_file() and sha(ROOT/name)==expected,'Modified/missing physical visual: '+name)
    result=json.loads((reference/'results.json').read_text())
    require(result['manifest_sha256']==digest and result['rtl_sha256']==manifest['rtl_sha256'],'Different result RTL/manifest')
    for stage,lab in [('unit','dotproduct'),('system','dotproduct-wally')]:
        report=json.loads((reference/stage/'report.json').read_text())
        require(report['labs'][lab]['status']=='pass','Failed functional stage')
        for name,expected in {**manifest['rtl_sha256'],**manifest['firmware_sha256']}.items():
            require(report['sources'][name]==expected,'Functional stage used different source')
    for stage in ['fpga','asic']:
        report=json.loads((reference/stage/'report.json').read_text())
        require(report['status']=='completed' and report['manifest_sha256']==digest,'Incomplete/mismatched physical stage')
        require(report['rtl_sha256']==manifest['rtl_sha256'] and report['parameters']==manifest['parameters'],'Physical parameter/source drift')
    require(result['fpga']['power_w'] is None,'FPGA power must not acquire an invented estimate')
    require(not result['fpga']['setup_target_met'],'Recorded FPGA timing failure must remain visible')
    require(result['asic']['hold_slack_ns']<0 and result['asic']['electrical_violations'],'Unclosed ASIC timing/electrical conditions changed')
    require(result['asic']['gds_readback']['empty_cells']==[],'Incomplete GDS cell geometry')
    visual=json.loads((reference/'fpga/visual-provenance.json').read_text())
    report=json.loads((reference/'fpga/report.json').read_text())
    require(visual['source_json_sha256']==report['artifacts']['routed.json'],'FPGA visual from another physical design')
    for resource,count in visual['resource_counts'].items():
        require(result['fpga']['resources'][resource]['used']==count,'Visual/resource-count mismatch')
    print('PASS complete-case dossier: same locked RTL/firmware, functional/formal/Wally evidence, '
          'FPGA/ASIC results and explicit failed obligations; '+('book figures omitted from ZIP' if extracted else '4 physical visuals'))


if __name__=='__main__': main()
