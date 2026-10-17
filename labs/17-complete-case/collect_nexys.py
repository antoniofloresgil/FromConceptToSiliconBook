#!/usr/bin/env python3
"""Preserve actual Nexys Video implementation evidence without replacing ECP5."""
import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
from collect import physical,require,write
from run import ROOT,SOURCE,load_manifest,sha


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report',type=Path)
    parser.add_argument('--publish-reference',action='store_true')
    parser.add_argument('--failed-dsp',type=Path,help='Optional author evidence for the initial incompatible DSP route')
    args=parser.parse_args()
    manifest=load_manifest();report=physical(args.report,manifest);run=args.report.parent
    profile=json.loads((SOURCE/'nexys-profile.json').read_text())
    require(report['profile_sha256']==sha(SOURCE/'nexys-profile.json') and report['profile']==profile,'Different Nexys target')
    require(report['recipe_sha256']==sha(SOURCE/'run_nexys.py'),'Changed physical runner')
    timing=json.loads((run/'timing.json').read_text())
    require(len(timing['fmax'])==1,'Review clock scope before extracting Nexys Fmax')
    clock=next(iter(timing['fmax'].values()))
    require('PASS Nexys fixture:' in (run/report['commands'][1]['log']).read_text(),'Missing serial fixture check')
    visual=json.loads((ROOT/'figures/complete-case-nexys.json').read_text())
    require(visual['routed_json_sha256']==report['artifacts']['routed.json'],'Different visual design')
    require(visual['coordinates_sha256']==report['artifacts']['site-coordinates.json'],'Different visual coordinates')
    result={'manifest_sha256':report['manifest_sha256'],'profile_sha256':report['profile_sha256'],
            'part':profile['part'],'scope':profile['scope'],'resources':timing['utilization'],
            'synthesis_resources':json.loads((run/'synthesis-resources.json').read_text()),
            'fmax_mhz':clock['achieved'],'requested_mhz':clock['constraint'],
            'setup_target_met':clock['achieved']>=clock['constraint'],'power_w':None,
            'power_status':'not_estimated: no characterized FPGA power estimator in this flow',
            'board_programming':'not_run','bitstream':'FASM generated; binary .bit conversion not executed',
            'timing_scope':'experimental nextpnr-Xilinx model; no vendor STA/CDC or board validation'}
    design=json.loads((run/'routed.json').read_text())['modules']['top']
    result['packed_lut_types']=dict(Counter(cell['attributes'].get('X_ORIG_TYPE','unknown')
        for cell in design['cells'].values() if cell['type']=='SLICE_LUTX'))
    result['mapped_totals']={scope:{'lut_primitives':sum(n for kind,n in counts.items() if kind.startswith('LUT')),
                                 'ff_primitives':counts.get('FDRE',0),'carry4_primitives':counts.get('CARRY4',0)}
                             for scope,counts in result['synthesis_resources'].items()}
    write(run/'results.json',result)
    if args.publish_reference:
        dest=SOURCE/'reference/nexys';dest.mkdir(exist_ok=True)
        for name in ['report.json','timing.json','synthesis-resources.json','site-coordinates.json','results.json']:
            shutil.copyfile(run/name,dest/name)
        for command in report['commands']:
            shutil.copyfile(run/command['log'],dest/Path(command['log']).with_suffix('.txt').name)
        shutil.copyfile(ROOT/'figures/complete-case-nexys.json',dest/'visual-provenance.json')
        if args.failed_dsp:
            failed=json.loads(args.failed_dsp.read_text())
            require(failed['status']=='failed' and failed['rtl_sha256']==manifest['rtl_sha256'] and
                    failed['manifest_sha256']==sha(SOURCE/'manifest.json'),'Different failed DSP design')
            logname=failed['commands'][-1]['log'];log=args.failed_dsp.parent/logname
            require(sha(log)==failed['artifacts'][logname] and 'MULTSIGNIN' in log.read_text() and
                    'Failed to route arc' in log.read_text(),'Missing actual DSP routing failure')
            shutil.copyfile(args.failed_dsp,dest/'dsp-attempt-report.json')
            shutil.copyfile(log,dest/'dsp-attempt-routing.txt')
        inventory={'manifest_sha256':report['manifest_sha256'],'profile_sha256':report['profile_sha256'],
                   'recipes':{name:sha(SOURCE/name) for name in ['run_nexys.py','collect_nexys.py','nexys_plot.py','Dockerfile.xc7']},
                   'figure_sha256':sha(ROOT/'figures/complete-case-nexys.png'),
                   'files':{p.name:sha(p) for p in sorted(dest.iterdir()) if p.is_file() and p.name!='inventory.json'}}
        write(dest/'inventory.json',inventory)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
