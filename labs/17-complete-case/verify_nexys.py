#!/usr/bin/env python3
"""Audit the independently bound Nexys Video extension of the common release."""
import json
from run import ROOT,SOURCE,load_manifest,sha


def require(condition,message):
    if not condition:raise ValueError(message)


def main():
    manifest=load_manifest();dest=SOURCE/'reference/nexys'
    inventory=json.loads((dest/'inventory.json').read_text())
    profile=json.loads((SOURCE/'nexys-profile.json').read_text())
    require(inventory['manifest_sha256']==profile['common_manifest_sha256']==sha(SOURCE/'manifest.json'),'Different common release')
    require(inventory['profile_sha256']==sha(SOURCE/'nexys-profile.json'),'Different Nexys profile')
    require(profile['part']=='xc7a200tsbg484-1','Different board device')
    for name,digest in profile['inputs'].items():require(sha(SOURCE/name)==digest,'Changed board fixture: '+name)
    for name,digest in inventory['recipes'].items():require(sha(SOURCE/name)==digest,'Changed implementation recipe: '+name)
    for name,digest in inventory['files'].items():require(sha(dest/name)==digest,'Changed Nexys evidence: '+name)
    report=json.loads((dest/'report.json').read_text());result=json.loads((dest/'results.json').read_text())
    timing=json.loads((dest/'timing.json').read_text());visual=json.loads((dest/'visual-provenance.json').read_text())
    require(report['status']=='completed' and all(c['exit_code']==0 for c in report['commands']),'Failed implementation')
    require(report['manifest_sha256']==inventory['manifest_sha256'],'Different report release')
    require(report['rtl_sha256']==manifest['rtl_sha256'] and report['parameters']==manifest['parameters'],'Different core source/configuration')
    require(report['profile_sha256']==inventory['profile_sha256'] and report['profile']==profile,'Different physical target')
    require(report['recipe_sha256']==sha(SOURCE/'run_nexys.py') and report['nextpnr_revision']==profile['nextpnr_revision'],'Different implementation recipe/tool')
    clock=next(iter(timing['fmax'].values()))
    require(len(timing['fmax'])==1 and result['fmax_mhz']==clock['achieved'] and result['requested_mhz']==clock['constraint'],'Different timing extraction')
    require(result['resources']==timing['utilization'] and result['power_w'] is None,'Different resources/power claim')
    require(result['setup_target_met']==(clock['achieved']>=clock['constraint']),'Incorrect timing acceptance')
    require(visual['routed_json_sha256']==report['artifacts']['routed.json'] and visual['coordinates_sha256']==report['artifacts']['site-coordinates.json'],'Different physical visual')
    for resource,count in visual['resource_counts'].items():
        require(result['resources'][resource]['used']==count,'Visual/resource mismatch')
    extracted=(ROOT/'LAB-PROVENANCE.json').is_file() and not (ROOT/'chapters').exists()
    if not extracted:require(sha(ROOT/'figures/complete-case-nexys.png')==inventory['figure_sha256'],'Changed Nexys visual')
    print('PASS Nexys Video: same locked accelerator, separate board fixture/profile, actual implementation and visual')


if __name__=='__main__':main()
