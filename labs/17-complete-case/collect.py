#!/usr/bin/env python3
"""Join actual unit, Wally, FPGA and ASIC evidence for the locked IP release."""
import argparse
import csv
import json
from pathlib import Path
import re
import shutil
from run import ROOT, SOURCE, load_manifest, sha


def write(path, value):
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def functional(path, lab, manifest):
    report=json.loads(path.read_text())
    case=report['labs'][lab]
    require(case['status']=='pass' and case['seed']==manifest['seed'], 'Unsuccessful/mismatched functional run')
    for name,expected in {**manifest['rtl_sha256'],**manifest['firmware_sha256']}.items():
        require(report['sources'].get(name)==expected, 'Functional source mismatch: '+name)
    for name,expected in case['artifacts'].items():
        p=(ROOT/name).resolve()
        require(p.is_relative_to(ROOT) and p.is_file() and sha(p)==expected, 'Stale functional artifact: '+name)
    text=''
    for command in case['commands']:
        require(command['returncode']==0,'Failed functional command')
        text+=(ROOT/command['log']).read_text(errors='replace')+'\n'
    return report,text


def physical(path, manifest):
    report=json.loads(path.read_text())
    require(report['status']=='completed','Incomplete physical flow')
    require(report['manifest_sha256']==sha(SOURCE/'manifest.json'),'Different physical configuration manifest')
    require(report['rtl_sha256']==manifest['rtl_sha256'],'Different physical RTL revision')
    require(report['parameters']==manifest['parameters'],'Different physical parameter configuration')
    for name,expected in report['artifacts'].items():
        require(sha(path.parent/name)==expected,'Stale physical artifact: '+name)
    require(all(c['exit_code']==0 for c in report['commands']),'Failed physical command')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--unit',type=Path,required=True)
    parser.add_argument('--system',type=Path,required=True)
    parser.add_argument('--fpga',type=Path,required=True)
    parser.add_argument('--asic',type=Path,required=True)
    parser.add_argument('--negative',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,default=Path('labs/build/complete-case-dossier'))
    parser.add_argument('--publish-reference',action='store_true')
    args=parser.parse_args()
    manifest=load_manifest()
    unit,unitlog=functional(args.unit,'dotproduct',manifest)
    system,systemlog=functional(args.system,'dotproduct-wally',manifest)
    for marker in ['PASS dotproduct: 256 lengths','PASS dotproduct: 16 lengths',
                   'PASS bounded control checks: 20 cycles','reachable DONE witness saved']:
        require(marker in unitlog,'Missing unit/formal checker: '+marker)
    require('PASS real Wally: five polling jobs, IRQ handler, invalid descriptor' in systemlog,'Missing firmware completion')
    negative=json.loads(args.negative.read_text())
    require(negative['unsigned']['simulation']=='expected failure' and
            negative['early-done']['simulation']=='expected failure' and
            negative['early-done']['formal']=='expected failure with counterexample',
            'Missing arithmetic/completion negative controls')
    identity=ROOT/next(n for n in system['labs']['dotproduct-wally']['artifacts'] if n.endswith('vendor/source-identity.json'))
    require(json.loads(identity.read_text())['revision']==manifest['platform']['revision'],'Wrong Wally revision')
    fpga=physical(args.fpga,manifest)
    asic=physical(args.asic,manifest)
    fpga_dir=args.fpga.parent; asic_dir=args.asic.parent
    timing=json.loads((fpga_dir/'timing.json').read_text())
    sta=json.loads((asic_dir/'routed-metrics.json').read_text())
    power=(asic_dir/'power.rpt').read_text()
    match=re.search(r'^Total\s+([\deE.+-]+)\s+([\deE.+-]+)\s+([\deE.+-]+)\s+([\deE.+-]+)',power,re.M)
    require(match is not None and 'Watts' in power,'Unknown power-report units/schema')
    metrics=[{'length':int(n),'software_cycles':int(sw),'accelerator_cycles':int(hw),
              'cycle_speedup':int(sw)/int(hw)} for n,sw,hw in
             re.findall(r'METRIC N=(\d+) software_cycles=(\d+) accelerator_total_cycles=(\d+)',systemlog)]
    require([m['length'] for m in metrics]==[1,8,32,128,256],'Incomplete shared-workload measurements')
    gds=json.loads((asic_dir/'gds-readback.json').read_text())
    require(gds['top']==manifest['component'] and gds['empty_cells']==[],'Incomplete GDS readback')
    limits=(asic_dir/'routed-limits.rpt').read_text()
    result={'release':manifest['release'],'manifest_sha256':sha(SOURCE/'manifest.json'),
            'rtl_sha256':manifest['rtl_sha256'],'parameters':manifest['parameters'],
            'functional':{'unit':'pass','system':'pass','formal':'bounded only','negative_controls':negative,
                          'wally_revision':manifest['platform']['revision'],'cycles':metrics},
            'fpga':{'scope':manifest['profiles']['fpga']['scope'],'tool_versions':fpga['tools'],
                    'resources':timing['utilization'],'fmax_mhz':timing['fmax']['clk']['achieved'],
                    'requested_mhz':timing['fmax']['clk']['constraint'],
                    'setup_target_met':timing['fmax']['clk']['achieved']>=timing['fmax']['clk']['constraint'],
                    'power_w':None,'power_status':'not_estimated: no characterized FPGA power model/estimator in this flow',
                    'programming':'not_run; out-of-context IP has no board IO or programmable bitstream'},
            'asic':{'scope':manifest['profiles']['asic']['scope'],'tool_versions':asic['tools'],
                    'cell_area_um2':float(re.search(r'Design area ([\d.]+)',(asic_dir/'routed-area.rpt').read_text())[1]),
                    'core_area_um2':sta['core_um2'],'setup_slack_ns':sta['setup_ns'],
                    'hold_slack_ns':sta['hold_ns'],'setup_derived_limit_mhz':1000/(manifest['clock_period_ns']-sta['setup_ns']),
                    'setup_limit_scope':'fixed-budget, single-corner STA estimate; hold/electrical failures prevent validation as an operating Fmax',
                    'electrical_violations':('VIOLATED' in limits),
                    'router_drc_report_empty':(asic_dir/'route-drc.rpt').stat().st_size==0,
                    'power_w':dict(zip(['internal','switching','leakage','total'],map(float,match.groups()))),
                    'power_model':manifest['profiles']['asic']['activity_source'],
                    'power_clock_mhz':1000/manifest['clock_period_ns'],
                    'power_activity_command':'set_power_activity -global -activity 0.1',
                    'gds_sha256':sha(asic_dir/'dotproduct_axi.gds'),'gds_readback':gds},
            'unclosed':['complete-SoC physical implementation','FPGA board IO/programming',
                        'RTL-to-mapped-netlist equivalence','ASIC hold/electrical closure',
                        'foundry DRC/LVS and multi-corner signoff','workload-annotated power and measured energy']}
    out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    write(out/'results.json',result)
    with (out/'cycles.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(metrics[0]),lineterminator='\n');writer.writeheader();writer.writerows(metrics)
    print(json.dumps(result,indent=2))
    if args.publish_reference:
        target=SOURCE/'reference';target.mkdir(exist_ok=True)
        for stage,path in [('unit',args.unit),('system',args.system),('fpga',args.fpga),('asic',args.asic)]:
            destination=target/stage;destination.mkdir(exist_ok=True)
            shutil.copyfile(path,destination/'report.json')
            if stage in {'unit','system'}:
                for c in json.loads(path.read_text())['labs']['dotproduct' if stage=='unit' else 'dotproduct-wally']['commands']:
                    p=ROOT/c['log'];shutil.copyfile(p,destination/p.with_suffix('.txt').name)
            else:
                for p in path.parent.iterdir():
                    if p.suffix in {'.rpt','.log','.json'} and p.name not in {'mapped.json','routed.json','report.json'}:
                        name=p.with_suffix('.txt').name if p.suffix=='.log' else p.name
                        shutil.copyfile(p,destination/name)
        for name in ['results.json','cycles.csv']:
            shutil.copyfile(out/name,target/name)
        shutil.copyfile(args.negative,target/'negative-results.json')
        shutil.copyfile(fpga_dir/'implementation.json',target/'fpga/visual-provenance.json')
        write(target/'asic/visual-provenance.json',{
            'odb_sha256':sha(asic_dir/'routed.odb'),'sdc_sha256':sha(asic_dir/'routed.sdc'),
            'spef_sha256':sha(asic_dir/'routed.spef'),'script_sha256':sha(SOURCE/'asic-images.tcl')})
        for src,name in [(fpga_dir/'implementation.png','complete-case-fpga.png'),
                         (asic_dir/'implementation.png','complete-case-asic.png'),
                         (asic_dir/'critical-path.png','complete-case-asic-critical.png'),
                         (asic_dir/'clocktree.png','complete-case-clocktree.png')]:
            require(src.is_file(),'Missing actual physical-flow visual: '+str(src))
            shutil.copyfile(src,ROOT/'figures'/name)
        inventory={'manifest_sha256':sha(SOURCE/'manifest.json'),
                   'collector_sha256':sha(Path(__file__)),
                   'visual_scripts':{p.name:sha(p) for p in [SOURCE/'fpga_plot.py',SOURCE/'asic-images.tcl']},
                   'files':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(target.rglob('*'))
                            if p.is_file() and p.name!='inventory.json'},
                   'figures':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted((ROOT/'figures').glob('complete-case-*.png'))}}
        write(target/'inventory.json',inventory)


if __name__=='__main__':
    main()
