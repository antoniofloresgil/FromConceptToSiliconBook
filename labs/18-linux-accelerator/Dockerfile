ARG BOOT_BASE=from-concept-boot:2026.10
FROM ${BOOT_BASE}
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    pkg-config libglib2.0-dev libpixman-1-dev libfdt-dev zlib1g-dev \
    meson ninja-build python3-venv python3-tomli \
    && rm -rf /var/lib/apt/lists/*
RUN curl -fL --retry 3 https://download.qemu.org/qemu-8.2.2.tar.xz -o /tmp/qemu.tar.xz \
    && echo '847346c1b82c1a54b2c38f6edbd85549edeb17430b7d4d3da12620e2962bc4f3  /tmp/qemu.tar.xz' | sha256sum -c - \
    && mkdir /opt/qemu && tar -xf /tmp/qemu.tar.xz -C /opt/qemu --strip-components=1 \
    && rm /tmp/qemu.tar.xz
RUN curl -fL --retry 3 https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.12.tar.xz -o /tmp/linux.tar.xz \
    && echo 'b1a2562be56e42afb3f8489d4c2a7ac472ac23098f1ef1c1e40da601f54625eb  /tmp/linux.tar.xz' | sha256sum -c - \
    && mkdir /opt/linux && tar -xf /tmp/linux.tar.xz -C /opt/linux --strip-components=1 \
    && rm /tmp/linux.tar.xz
COPY labs/18-linux-accelerator/hsd-dotproduct.c labs/18-linux-accelerator/hsd-dotproduct.h labs/18-linux-accelerator/prepare.py /opt/hsd/
RUN python3 /opt/hsd/prepare.py
RUN mkdir /opt/qemu-build && cd /opt/qemu-build \
    && /opt/qemu/configure --target-list=riscv64-softmmu --disable-docs --disable-werror \
       --disable-gtk --disable-sdl --disable-vnc --disable-tools --disable-user --enable-fdt \
    && ninja -j4 qemu-system-riscv64
COPY labs/18-linux-accelerator/dotproduct-driver.c labs/18-linux-accelerator/dotproduct-uapi.h /opt/hsd/
RUN python3 /opt/hsd/prepare.py --kernel
RUN cd /opt/linux && make ARCH=riscv CROSS_COMPILE=riscv64-linux-gnu- defconfig \
    && scripts/config -d DRM -d SOUND -d WIRELESS -d WLAN -d NET -d SCSI -d USB_SUPPORT \
       -d PCI -d INPUT -d HWMON -d MEDIA_SUPPORT -d DEBUG_INFO -d ACPI -d BPF_SYSCALL \
       -d DMADEVICES -d EXT4_FS -d BTRFS_FS -d SQUASHFS -d VIRTIO_MENU \
       -e DEVTMPFS -e DMA_DECLARE_COHERENT -e OF_RESERVED_MEM -e HIGH_RES_TIMERS \
    && make ARCH=riscv CROSS_COMPILE=riscv64-linux-gnu- olddefconfig \
    && make -j4 ARCH=riscv CROSS_COMPILE=riscv64-linux-gnu- Image
COPY labs/18-linux-accelerator/linux-app.c /opt/hsd/
RUN riscv64-linux-gnu-gcc -O2 -static -Wall /opt/hsd/linux-app.c -o /opt/hsd/init \
    && printf 'dir /dev 0755 0 0\nnod /dev/console 0600 0 0 c 5 1\ndir /proc 0755 0 0\ndir /sys 0755 0 0\nfile /init /opt/hsd/init 0755 0 0\n' >/opt/hsd/initramfs.list \
    && /opt/linux/usr/gen_init_cpio /opt/hsd/initramfs.list >/opt/hsd/rootfs.cpio
ENV PATH="/opt/qemu-build:${PATH}"
WORKDIR /work
CMD ["python3", "labs/18-linux-accelerator/run.py"]
