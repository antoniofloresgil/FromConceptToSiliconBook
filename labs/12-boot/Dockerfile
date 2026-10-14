FROM ubuntu:24.04@sha256:84e77dee7d1bc93fb029a45e3c6cb9d8aa4831ccfcc7103d36e876938d28895b

# Separate optional environment: the nine-unit-lab baseline is unchanged.
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    python3 clang lld qemu-system-misc opensbi device-tree-compiler \
    build-essential git bc bison flex libssl-dev libelf-dev \
    gcc-riscv64-linux-gnu binutils-riscv64-linux-gnu gzip curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
# GCC's cross C library headers are recommendations, omitted by the flag above.
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    libc6-dev-riscv64-cross && rm -rf /var/lib/apt/lists/*
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /work
CMD ["python3", "labs/12-boot/run.py"]
