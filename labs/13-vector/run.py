"""Check one RVV 1.0 ELF at three architectural register lengths."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'labs/build/vector'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'status': 'failed', 'scope': 'RVV integer functional checks in QEMU; no Wally or cycle model',
              'commands': [], 'runs': [], 'sources': {}}

    def execute(args, name):
        report['commands'].append([str(arg) for arg in args])
        try:
            result = subprocess.run(args, cwd=ROOT, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, timeout=45)
        except subprocess.TimeoutExpired as error:
            (OUT / name).write_bytes(error.stdout or b'')
            raise RuntimeError('Timed out: ' + name) from error
        (OUT / name).write_bytes(result.stdout)
        if result.returncode:
            raise RuntimeError(f'{name}: exit {result.returncode}')
        return result.stdout.decode('utf-8', errors='replace')

    try:
        report['tools'] = {tool: subprocess.check_output([tool, '--version'], text=True).splitlines()[0]
                           for tool in ['clang', 'ld.lld', 'qemu-system-riscv64']}
        sources = ['main.c', 'start.S', 'kernels.S', 'link.ld', 'run.py']
        report['sources'] = {name: sha(HERE / name) for name in sources}
        common = ['clang', '--target=riscv64-unknown-elf', '-mabi=lp64', '-mcmodel=medany',
                  '-ffreestanding', '-fno-stack-protector', '-fno-pic']
        execute([*common, '-march=rv64imac_zicsr', '-O2', '-fno-vectorize', '-fno-slp-vectorize',
                 '-c', str(HERE / 'main.c'), '-o', str(OUT / 'main.o')], 'compile-scalar.log')
        for name in ['start', 'kernels']:
            execute([*common, '-march=rv64gcv', '-c', str(HERE / (name + '.S')),
                     '-o', str(OUT / (name + '.o'))], 'compile-' + name + '.log')
        elf = OUT / 'vector.elf'
        execute([*common, '-march=rv64gcv', '-nostdlib', '-fuse-ld=lld', '-Wl,--no-relax',
                 '-Wl,-T,' + str(HERE / 'link.ld'), '-Wl,-Map,' + str(OUT / 'vector.map'),
                 *[str(OUT / (name + '.o')) for name in ['main', 'start', 'kernels']],
                 '-o', str(elf)], 'link.log')
        report['elf_sha256'] = sha(elf)
        for vlen in [128, 256, 512]:
            console = execute(['qemu-system-riscv64', '-machine', 'virt', '-m', '128M',
                               '-smp', '1', '-nographic', '-no-reboot', '-bios', 'none',
                               '-cpu', f'rv64,v=true,vlen={vlen},elen=64,vext_spec=v1.0',
                               '-kernel', str(elf)], f'uart-{vlen}.log')
            if 'FAIL' in console or 'RVV_PASS' not in console or f'{vlen:016x}' not in console:
                raise RuntimeError(f'Incomplete vector evidence at VLEN={vlen}')
            report['runs'].append({'vlen': vlen, 'elen': 64, 'status': 'passed'})
        report['status'] = 'passed'
        print('PASS one ELF at VLEN=128,256,512; evidence: labs/build/vector/')
    finally:
        report['artifacts'] = {p.name: sha(p) for p in OUT.iterdir() if p.is_file() and p.name != 'report.json'}
        (OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
