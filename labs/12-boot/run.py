"""Compile and check the real QEMU -> OpenSBI -> RV64 supervisor handoff."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'labs/build/boot'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'status': 'failed', 'scope': 'QEMU virt, RV64, one hart; no Linux or Wally validation',
              'commands': [], 'sources': {}, 'tools': {}}
    firmware = Path('/usr/lib/riscv64-linux-gnu/opensbi/generic/fw_dynamic.bin')

    def execute(args, log, timeout=45):
        report['commands'].append([str(arg) for arg in args])
        try:
            result = subprocess.run(args, cwd=ROOT, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, timeout=timeout)
        except subprocess.TimeoutExpired as error:
            (OUT / log).write_bytes(error.stdout or b'')
            raise RuntimeError(f'{log}: timed out; no completed boot') from error
        (OUT / log).write_bytes(result.stdout)
        if result.returncode:
            raise RuntimeError(f'{log}: exit {result.returncode}')
        return result.stdout.decode('utf-8', errors='replace')

    try:
        for tool in ['clang', 'ld.lld', 'qemu-system-riscv64', 'dtc']:
            result = subprocess.run([tool, '--version'], stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, check=True)
            report['tools'][tool] = result.stdout.decode().splitlines()[0]
        if not firmware.is_file():
            raise RuntimeError('Install the Ubuntu opensbi package; explicit firmware file missing')
        report['firmware'] = {'path': str(firmware), 'sha256': sha(firmware)}
        report['packages'] = execute(['dpkg-query', '-W', '-f=${Package}=${Version}\n',
                                      'opensbi', 'qemu-system-misc', 'clang', 'lld',
                                      'device-tree-compiler'], 'packages.txt')
        sources = [HERE / name for name in ['start.S', 'main.c', 'link.ld', 'run.py', 'Dockerfile']]
        report['sources'] = {str(path.relative_to(ROOT)): sha(path) for path in sources}
        elf = OUT / 'payload.elf'
        execute(['clang', '--target=riscv64-unknown-elf', '-march=rv64imac_zicsr',
                 '-mabi=lp64', '-mcmodel=medany', '-O2', '-ffreestanding',
                 '-fno-stack-protector', '-fno-pic', '-nostdlib', '-fuse-ld=lld',
                 '-Wl,--no-relax', '-Wl,-T,' + str(HERE / 'link.ld'),
                 '-Wl,-Map,' + str(OUT / 'payload.map'),
                 str(HERE / 'start.S'), str(HERE / 'main.c'), '-o', str(elf)], 'compile.log')
        base = ['qemu-system-riscv64', '-machine', 'virt', '-m', '128M', '-smp', '1',
                '-nographic', '-no-reboot', '-bios', str(firmware)]
        execute([*base, '-kernel', str(elf), '-machine',
                 'dumpdtb=' + str(OUT / 'virt.dtb')], 'dumpdtb.log')
        execute(['dtc', '-I', 'dtb', '-O', 'dts', '-o', str(OUT / 'virt.dts'),
                 str(OUT / 'virt.dtb')], 'dtc.log')
        console = execute([*base, '-kernel', str(elf)], 'uart.log')
        markers = ['HSD supervisor payload', 'PASS handoff: satp=0, aligned FDT magic',
                   'PASS SBI base: OpenSBI implementation', 'PASS TIME: timer disarmed',
                   'PASS unsupported extension: -2', 'BOOT_PASS']
        if 'FAIL' in console or any(marker not in console for marker in markers):
            raise RuntimeError('UART evidence incomplete; inspect uart.log')
        if not re.search(r'Domain0 Next Mode\s*:\s*S-mode', console):
            raise RuntimeError('OpenSBI banner does not confirm an S-mode next stage')
        report['checks'] = markers + ['OpenSBI S-mode handoff', 'QEMU normal shutdown']
        report['status'] = 'passed'
        print('PASS QEMU/OpenSBI supervisor boot; evidence: labs/build/boot/')
    finally:
        report['artifacts'] = {p.name: sha(p) for p in OUT.iterdir()
                               if p.is_file() and p.name != 'report.json'}
        (OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
