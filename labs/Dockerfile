FROM ubuntu:24.04@sha256:84e77dee7d1bc93fb029a45e3c6cb9d8aa4831ccfcc7103d36e876938d28895b

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    python3 python3-venv python3-pip iverilog verilator yosys clang lld \
    make g++ git ca-certificates && rm -rf /var/lib/apt/lists/*
# cocotb embeds Python through a shared libpython; the runtime alone is insufficient.
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    python3-dev && rm -rf /var/lib/apt/lists/*
RUN python3 -m venv /opt/labs-venv
ENV PATH="/opt/labs-venv/bin:${PATH}" PYTHONDONTWRITEBYTECODE=1
COPY labs/requirements.txt /tmp/labs-requirements.txt
RUN pip install --no-cache-dir -r /tmp/labs-requirements.txt
WORKDIR /work
CMD ["python", "labs/run.py", "run", "all"]
