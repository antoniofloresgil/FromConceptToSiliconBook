#!/usr/bin/env python3
"""Run inside the recorded ORFS image; a failed implementation stays failed."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).resolve().parent
OUT = ROOT / 'labs/build/openroad-study'
PLATFORM = Path('/OpenROAD-flow-scripts/flow/platforms/nangate45')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execute(args, log, env=None):
    with log.open('w') as stream:
        result = subprocess.run(args, stdout=stream, stderr=subprocess.STDOUT,
                                env=env, timeout=600)
    if result.returncode:
        raise RuntimeError(f'Command failed ({result.returncode}); inspect {log}')


def main():
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workers', type=int, choices=[1, 2], default=1)
    parser.add_argument('--probe', action='store_true', help='Only 1 ns / 55 percent')
    parser.add_argument('--output-dir', default='labs/build/openroad-study')
    args = parser.parse_args()
    OUT = (ROOT / args.output_dir).resolve()
    if not OUT.is_relative_to(ROOT / 'labs/build'):
        raise ValueError('Output directory must stay inside labs/build')
    if OUT.exists() and any(OUT.iterdir()):
        raise ValueError(f'{OUT} is not empty; select a fresh --output-dir')
    OUT.mkdir(parents=True, exist_ok=True)
    liberty = PLATFORM / 'lib/NangateOpenCellLibrary_typical.lib'
    rtl = ROOT / 'labs/07-implementation/rtl/accumulator.sv'
    netlist = OUT / 'mapped.v'
    script = (f'read_verilog -sv {rtl}; synth -top accumulator; '
              f'dfflibmap -liberty {liberty}; abc -liberty {liberty}; '
              f'clean; write_verilog -noattr -noexpr {netlist}')
    execute(['yosys', '-Q', '-T', '-p', script], OUT / 'synthesis.log')
    versions = {tool: subprocess.check_output([tool, flag], text=True).strip()
                for tool, flag in [('yosys', '-V'), ('openroad', '-version')]}
    inputs = [rtl, SOURCE/'flow.tcl', SOURCE/'constraints.sdc', SOURCE/'run.py',
              liberty, PLATFORM/'lef/NangateOpenCellLibrary.tech.lef',
              PLATFORM/'lef/NangateOpenCellLibrary.macro.mod.lef',
              PLATFORM/'setRC.tcl', PLATFORM/'make_tracks.tcl',
              PLATFORM/'rcx_patterns.rules',
              PLATFORM.parent.parent/'designs/nangate45/gcd/grid_strategy-M1-M4-M7.tcl']
    manifest = {'schema_version': 1, 'tools': versions,
                'image': os.environ.get('STUDY_IMAGE_ID', 'unrecorded'),
                'inputs': {str(p): digest(p) for p in inputs},
                'netlist_sha256': digest(netlist), 'cases': []}
    cases = [(1.0, 55)] if args.probe else [
        (p, u) for u in [45, 65, 80] for p in [0.85, 1.0, 1.15]] + [(0.91, 55), (1.0, 55)]

    def run_case(case):
        period, util = case
        name = f'u{util}-p{period:.2f}'
        folder = OUT / name
        # Do not accept old checkpoints as evidence for an unsuccessful rerun.
        if folder.exists():
            raise RuntimeError(f'{folder} already exists; use a fresh output workspace')
        folder.mkdir()
        env = {**os.environ, 'STUDY_OUT': str(folder), 'STUDY_PERIOD': str(period),
               'STUDY_UTIL': str(util), 'STUDY_NETLIST': str(netlist),
               'STUDY_SDC': str(SOURCE/'constraints.sdc')}
        command = ['openroad', '-no_init', '-exit', '-threads', '2', str(SOURCE/'flow.tcl')]
        record = {'name': name, 'period_ns': period, 'target_util_pct': util,
                  'command': command, 'environment': {k:v for k,v in env.items() if k.startswith('STUDY_')},
                  'status': 'running'}
        started = time.monotonic()
        try:
            execute(command, folder/'flow.log', env)
            stages = {}
            for stage in ['placed', 'cts', 'global', 'routed']:
                metrics = dict(line.split(maxsplit=1) for line in
                               (folder/(stage+'-metrics.txt')).read_text().splitlines())
                stages[stage] = {k: (v if k == 'model' else float(v)) for k,v in metrics.items()}
            record.update(status='completed', stages=stages,
                          router_drc_report_bytes=(folder/'route-drc.rpt').stat().st_size)
        except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
            record.update(status='failed', error=str(error))
        record['elapsed_s'] = round(time.monotonic()-started, 2)
        record['artifacts'] = {p.name: digest(p) for p in sorted(folder.iterdir()) if p.is_file()}
        (folder/'case.json').write_text(json.dumps(record, indent=2)+'\n')
        print(name, record['status'], flush=True)
        return record

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for record in pool.map(run_case, cases):
            manifest['cases'].append(record)
            (OUT/'study.json').write_text(json.dumps(manifest, indent=2)+'\n')
    if any(c['status'] != 'completed' for c in manifest['cases']):
        raise SystemExit('One or more implementation cases failed; inspect study.json')


if __name__ == '__main__':
    main()
