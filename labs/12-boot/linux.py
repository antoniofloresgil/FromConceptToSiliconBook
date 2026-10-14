"""Fetch a checksum-pinned kernel, then build and check an offline Linux boot."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
WORK = ROOT / 'labs/work/boot-linux'
OUT = ROOT / 'labs/build/boot-linux'
VERSION = '6.12'
NAME = f'linux-{VERSION}.tar.xz'
URL = 'https://cdn.kernel.org/pub/linux/kernel/v6.x/' + NAME
SHA256 = 'b1a2562be56e42afb3f8489d4c2a7ac472ac23098f1ef1c1e40da601f54625eb'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download', action='store_true', help='Networked acquisition only')
    parser.add_argument('--jobs', type=int, default=4)
    args = parser.parse_args()
    if not 1 <= args.jobs <= 32:
        parser.error('--jobs must be between 1 and 32')
    archive = WORK / NAME
    source = WORK / ('linux-' + VERSION)
    if args.download:
        WORK.mkdir(parents=True, exist_ok=True)
        if not archive.exists():
            temporary = archive.with_suffix('.download')
            urllib.request.urlretrieve(URL, temporary)
            if digest(temporary) != SHA256:
                temporary.unlink()
                raise RuntimeError('Kernel archive checksum mismatch')
            temporary.rename(archive)
        if digest(archive) != SHA256:
            raise RuntimeError('Kernel archive checksum mismatch')
        if source.exists():
            raise RuntimeError('Source already exists; keep it unchanged and run without --download')
        with tarfile.open(archive) as packed:
            packed.extractall(WORK, filter='data')
        print('Acquired checksum-pinned Linux ' + VERSION + '; build can now run offline')
        return
    if not archive.is_file() or not source.is_dir() or digest(archive) != SHA256:
        raise RuntimeError('Run --download first; verified archive and source are required')
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'status': 'failed', 'scope': 'QEMU virt RV64, one hart, Linux kernel and static PID 1',
              'kernel_archive': {'url': URL, 'sha256': SHA256}, 'commands': []}

    def command(args, log, timeout=1800, append=False):
        report['commands'].append([str(arg) for arg in args])
        with (OUT / log).open('ab' if append else 'wb') as stream:
            subprocess.run(args, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                           check=True, timeout=timeout)

    try:
        kernel_build = OUT / 'kernel'
        kernel_build.mkdir(exist_ok=True)
        make = ['make', '-C', str(source), 'O=' + str(kernel_build), 'ARCH=riscv',
                'CROSS_COMPILE=riscv64-linux-gnu-']
        command([*make, 'defconfig'], 'configure.log')
        # Build only Image; no module installation, root mount or host device nodes.
        command([*make, '-j' + str(args.jobs), 'Image'], 'kernel-build.log')
        init = OUT / 'init'
        command(['riscv64-linux-gnu-gcc', '-O2', '-static', str(HERE / 'linux-init.c'),
                 '-o', str(init)], 'init-build.log')
        manifest = OUT / 'initramfs.list'
        manifest.write_text('dir /dev 0755 0 0\nnod /dev/console 0600 0 0 c 5 1\n'
                            'dir /proc 0755 0 0\ndir /sys 0755 0 0\n'
                            f'file /init {init} 0755 0 0\n', encoding='utf-8')
        cpio = OUT / 'rootfs.cpio'
        with cpio.open('wb') as stream:
            subprocess.run([str(kernel_build / 'usr/gen_init_cpio'), str(manifest)],
                           stdout=stream, check=True)
        firmware = Path('/usr/lib/riscv64-linux-gnu/opensbi/generic/fw_dynamic.bin')
        image = kernel_build / 'arch/riscv/boot/Image'
        qemu = ['qemu-system-riscv64', '-machine', 'virt', '-m', '256M', '-smp', '1',
                '-nographic', '-no-reboot', '-bios', str(firmware), '-kernel', str(image),
                '-initrd', str(cpio), '-append',
                'console=ttyS0 earlycon=uart8250,mmio,0x10000000 rdinit=/init']
        report['commands'].append(qemu)
        console = b''
        # PID 1 deliberately remains alive. Stop after evidence, not as a fake shutdown.
        with (OUT / 'uart.log').open('wb') as stream:
            process = subprocess.Popen(qemu, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
            try:
                import time
                deadline = time.monotonic() + 90
                while time.monotonic() < deadline:
                    console = (OUT / 'uart.log').read_bytes()
                    if b'HSD_LINUX_USERSPACE_PASS' in console:
                        break
                    if process.poll() is not None:
                        raise RuntimeError('QEMU exited before userspace success')
                    time.sleep(0.2)
                else:
                    raise RuntimeError('Linux userspace marker missing after 90 seconds')
            finally:
                if process.poll() is None:
                    process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
        if b'Linux version 6.12' not in console or b'Kernel panic' in console:
            raise RuntimeError('Kernel evidence invalid')
        command(['dpkg-query', '-W', '-f=${Package}=${Version}\n', 'opensbi',
                 'qemu-system-misc', 'gcc-riscv64-linux-gnu', 'binutils-riscv64-linux-gnu',
                 'libc6-dev-riscv64-cross'],
                'packages.txt')
        report['packages'] = (OUT / 'packages.txt').read_text()
        report['inputs'] = {str(p): digest(p) for p in [HERE / 'linux-init.c', HERE / 'linux.py',
                           firmware, image, kernel_build / '.config', cpio]}
        report['checks'] = ['Linux 6.12 kernel banner', 'PID 1 entered', '/proc and /sys mounted',
                            'HSD_LINUX_USERSPACE_PASS', 'No kernel panic before marker']
        report['termination'] = 'Emulator stopped by harness after userspace success; no guest shutdown tested'
        report['status'] = 'passed'
        print('PASS OpenSBI -> Linux -> userspace; evidence: labs/build/boot-linux/')
    finally:
        (OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
