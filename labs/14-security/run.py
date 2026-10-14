"""Two explicit environments: QEMU PMP, then digital security with RTL/SAT."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('part', choices=['pmp', 'digital'])
    args = parser.parse_args()
    out = ROOT / 'labs/build/security' / args.part
    out.mkdir(parents=True, exist_ok=True)
    report = {'status': 'failed', 'part': args.part, 'commands': [],
              'sources': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in HERE.iterdir() if p.suffix in {'.py', '.sv', '.S', '.ld'}}}
    report['dependencies'] = {'labs/02-memory/cache_model.py': hashlib.sha256(
        (ROOT / 'labs/02-memory/cache_model.py').read_bytes()).hexdigest()}

    def execute(command, log, env=None, timeout=300):
        report['commands'].append([str(item) for item in command])
        try:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, timeout=timeout)
        except subprocess.TimeoutExpired as error:
            (out / log).write_bytes(error.stdout or b'')
            raise RuntimeError('Timed out: ' + log) from error
        (out / log).write_bytes(result.stdout)
        if result.returncode:
            raise RuntimeError(f'{log}: exit {result.returncode}')
        return result.stdout.decode('utf-8', errors='replace')

    try:
        tools = ['clang', 'qemu-system-riscv64'] if args.part == 'pmp' else ['iverilog', 'yosys']
        report['tools'] = {}
        for tool in tools:
            version = subprocess.run([tool, '-V' if tool == 'iverilog' else '--version'],
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
            report['tools'][tool] = version.stdout.decode().splitlines()[0]
        if args.part == 'pmp':
            elf = out / 'pmp.elf'
            execute(['clang', '--target=riscv64-unknown-elf', '-march=rv64imac_zicsr',
                     '-mabi=lp64', '-mcmodel=medany', '-nostdlib', '-fuse-ld=lld',
                     '-Wl,--no-relax', '-Wl,-T,' + str(HERE / 'pmp.ld'),
                     str(HERE / 'pmp.S'), '-o', str(elf)], 'compile.log')
            console = execute(['qemu-system-riscv64', '-machine', 'virt', '-m', '128M',
                               '-smp', '1', '-nographic', '-no-reboot', '-bios', 'none',
                               '-kernel', str(elf)], 'uart.log', timeout=45)
            if 'PMP_PASS:' not in console or 'FAIL' in console:
                raise RuntimeError('Missing PMP signature')
            report['scope'] = 'Trusted U-mode probe; QEMU PMP faults and M-mode unchanged-memory observation'
        else:
            env = {**os.environ, 'LAB_BUILD_DIR': str(ROOT / 'labs/build/security/dma')}
            execute([sys.executable, 'labs/run.py', 'run', 'dotproduct', '--seed', '2026'],
                    'dma.log', env=env, timeout=600)
            report['dma_report'] = 'labs/build/security/dma/report.json'
            execute(['iverilog', '-g2012', '-s', 'tb_debug', '-o', str(out / 'debug.vvp'),
                     str(HERE / 'debug_guard.sv'), str(HERE / 'tb_debug.sv')], 'debug-compile.log')
            console = execute(['vvp', str(out / 'debug.vvp')], 'debug.log')
            if 'PASS debug admission:' not in console:
                raise RuntimeError('Missing debug admission signature')
            from timing import experiment
            timing = experiment()
            (out / 'timing.json').write_text(json.dumps(timing, indent=2) + '\n', encoding='utf-8')
            prefix = (f'read_verilog -formal -sv "{(HERE / "debug_guard.sv").as_posix()}"; '
                      'prep -top debug_guard -flatten; opt_clean; ')
            proof = ('sat -seq 20 -set-init-zero -set-at 1 reset 1 -prove-asserts -verify '
                     '-dump_vcd ' + (out / 'debug-counterexample.vcd').as_posix())
            execute(['yosys', '-Q', '-T', '-p', prefix + proof], 'debug-formal.log')
            witness = ('sat -seq 2 -set-init-zero -set-at 1 reset 1 '
                       '-set-at 2 reset 0 -set-at 2 lifecycle 1 -set-at 2 authenticated 1 '
                       '-set-at 2 lock_request 0 -set-at 2 halt_request 1 -set-at 2 halt_grant 1 '
                       '-show-inputs -show-outputs -dump_vcd ' + (out / 'debug-open-witness.vcd').as_posix())
            log = execute(['yosys', '-Q', '-T', '-p', prefix + witness], 'debug-witness.log')
            if 'SAT solving finished - model found:' not in log:
                raise RuntimeError('Authorized debug path has no reachable witness')
            report['scope'] = ('Real AXI/DMA reference RTL; teaching debug admission RTL/SAT 20 cycles; '
                               'synthetic cache timing; no secure Wally SoC or physical qualification')
        report['status'] = 'passed'
        print('PASS security ' + args.part + '; evidence: ' + str(out.relative_to(ROOT)))
    finally:
        report['artifacts'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in out.iterdir() if p.is_file() and p.name != 'report.json'}
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
