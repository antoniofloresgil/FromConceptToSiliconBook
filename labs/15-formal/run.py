#!/usr/bin/env python3
"""Checked FIFO BMC, induction/equivalence, witnesses and defect regression."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).resolve().parent
OUT = ROOT / 'labs/build/formal'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'schema_version': 1, 'status': 'running', 'jobs': [],
              'scope': '8-bit, depth-two, single-clock FIFO; reset and producer contract',
              'sources': {p.relative_to(ROOT).as_posix(): sha(p)
                          for p in sorted(SOURCE.iterdir()) if p.suffix in {'.py', '.sv'}},
              'tools': {}}

    def save():
        (OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n')

    def command(name, args, marker, expected_exit=0):
        job = {'name': name, 'command': args, 'cwd': OUT.relative_to(ROOT).as_posix(),
               'expected_exit': expected_exit, 'required_marker': marker, 'status': 'running'}
        report['jobs'].append(job)
        save()
        result = subprocess.run(args, cwd=OUT, capture_output=True, text=True, timeout=120)
        log = OUT / (name + '.log')
        log.write_text(result.stdout + result.stderr)
        job.update(exit_code=result.returncode, log=log.relative_to(ROOT).as_posix())
        ok_exit = result.returncode == 0 if expected_exit == 0 else result.returncode != 0
        job['status'] = 'pass' if ok_exit and marker in log.read_text() else 'fail'
        save()
        if job['status'] != 'pass':
            raise RuntimeError(f'{name}: unexpected result; inspect {log}')
        print('PASS', name, flush=True)

    def sat(name, parameters, options, marker, witness=False):
        artifact = OUT / (name + '.vcd')
        artifact.unlink(missing_ok=True)
        files = ' '.join('"' + (SOURCE / p).as_posix() + '"'
                         for p in ['fifo2.sv', 'shift_fifo2.sv', 'harness.sv'])
        # cover() is represented by goal; native SAT cannot import $cover cells.
        script = (f'read_verilog -formal -sv {files}; {parameters} '
                  'prep -top harness -flatten; chformal -cover -remove; opt_clean; '
                  f'sat -set-assumes -show-ports {options} -dump_vcd {artifact.name}')
        command(name, ['yosys', '-Q', '-T', '-p', script], marker)
        if witness and (not artifact.is_file() or artifact.stat().st_size == 0):
            raise RuntimeError(f'{name}: missing witness')

    save()
    try:
        for tool, flag in [('yosys', '-V'), ('iverilog', '-V')]:
            result = subprocess.run([tool, flag], capture_output=True, text=True, timeout=20)
            if result.returncode:
                raise RuntimeError(f'{tool}: version query failed')
            report['tools'][tool] = (result.stdout + result.stderr).splitlines()[0]
        sat('bmc', '', '-seq 12 -prove-asserts -verify',
            'SAT proof finished - no model found: SUCCESS!')
        sat('induction-equivalence', '',
            '-seq 2 -tempinduct -maxsteps 12 -prove-asserts -verify',
            'Induction step proven: SUCCESS!')
        sat('traffic-witness', '', '-seq 12 -set-at 12 goal 1',
            'SAT solving finished - model found:', witness=True)
        sat('drain-proof', 'chparam -set DRAIN 1 harness;',
            '-seq 2 -tempinduct -maxsteps 12 -prove-asserts -verify',
            'Induction step proven: SUCCESS!')
        sat('drain-witness', 'chparam -set DRAIN 1 harness;',
            '-seq 12 -set-at 12 goal 1',
            'SAT solving finished - model found:', witness=True)
        sat('fault-counterexample', 'chparam -set BUG 1 harness;',
            '-seq 6 -prove-asserts -falsify',
            'SAT proof finished - model found: FAIL!', witness=True)
        sat('vacuous-proof', 'chparam -set QUIET 1 harness;',
            '-seq 12 -prove-asserts -verify',
            'SAT proof finished - no model found: SUCCESS!')
        sat('unreachable-traffic', 'chparam -set QUIET 1 harness;',
            '-seq 12 -set-at 12 goal 1', 'SAT solving finished - no model found.')
        for faulty in [False, True]:
            name = 'faulty-regression' if faulty else 'repaired-regression'
            executable = OUT / (name + '.vvp')
            args = ['iverilog', '-g2012', '-s', 'tb_regression', '-o', str(executable)]
            if faulty:
                args.append('-DFAULTY')
            args += [str(SOURCE / 'fifo2.sv'), str(SOURCE / 'tb_regression.sv')]
            command(name + '-compile', args, '')
            command(name, ['vvp', str(executable)],
                    'phantom item' if faulty else 'PASS FIFO regression',
                    expected_exit=1 if faulty else 0)
        report['status'] = 'pass'
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        report.update(status='fail', error=str(error))
        raise
    finally:
        report['artifacts'] = {
            p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(OUT.iterdir())
            if p.is_file() and p.suffix in {'.log', '.vcd', '.vvp'}}
        save()


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        print('FAIL:', error, file=sys.stderr)
        sys.exit(1)
