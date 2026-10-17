ARG LINUX_BASE=from-concept-linux-accelerator:2026.10
FROM ${LINUX_BASE}
COPY labs/20-multicore/smp.c /opt/multicore/smp.c
RUN riscv64-linux-gnu-gcc -O2 -static -std=c11 -Wall -Wextra -Werror \
      -Wno-misleading-indentation -I/opt/hsd /opt/multicore/smp.c -o /opt/multicore/init \
    && printf 'dir /dev 0755 0 0\nnod /dev/console 0600 0 0 c 5 1\ndir /proc 0755 0 0\ndir /sys 0755 0 0\nfile /init /opt/multicore/init 0755 0 0\n' >/opt/multicore/initramfs.list \
    && /opt/linux/usr/gen_init_cpio /opt/multicore/initramfs.list >/opt/multicore/rootfs.cpio
WORKDIR /work
CMD ["python3", "labs/20-multicore/run.py"]
