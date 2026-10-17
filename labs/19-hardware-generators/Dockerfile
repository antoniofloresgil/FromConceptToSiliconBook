ARG LABS_BASE=from-concept-labs:2026.10
FROM ${LABS_BASE}
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    openjdk-17-jdk-headless curl && rm -rf /var/lib/apt/lists/*
RUN curl -fL --retry 3 https://repo.maven.apache.org/maven2/org/scala-sbt/sbt-launch/1.10.2/sbt-launch-1.10.2.jar -o /opt/sbt-launch.jar \
    && echo 'cdd6963b622f42690cb2e3154bde3f3257a03839f216e1b5d7420000d6a71817  /opt/sbt-launch.jar' | sha256sum -c -
RUN curl -fL --retry 3 https://github.com/llvm/circt/releases/download/firtool-1.62.0/firrtl-bin-linux-x64.tar.gz -o /tmp/firtool.tar.gz \
    && echo '1aee0d13fea52b504b0f689f4d890cfb7c63f7dc832308ceff9ae3f099e8e800  /tmp/firtool.tar.gz' | sha256sum -c - \
    && mkdir /opt/firtool && tar -xf /tmp/firtool.tar.gz -C /opt/firtool --strip-components=1 \
    && rm /tmp/firtool.tar.gz
COPY labs/19-hardware-generators/sbt.sh /usr/local/bin/hsd-sbt
RUN chmod +x /usr/local/bin/hsd-sbt \
    && printf '[repositories]\nlocal\nmaven-central: https://repo.maven.apache.org/maven2\n' >/opt/sbt-repositories
ENV COURSIER_CACHE=/opt/coursier PATH="/opt/firtool/bin:${PATH}"
COPY labs/19-hardware-generators/build.sbt /opt/generator/build.sbt
COPY labs/19-hardware-generators/project/build.properties /opt/generator/project/build.properties
COPY labs/19-hardware-generators/src /opt/generator/src
WORKDIR /opt/generator
RUN hsd-sbt 'runMain Emit /opt/warmup' writeRuntimeClasspath > /opt/generator-build.txt 2>&1 \
    && cat /opt/generator-build.txt && firtool --version
WORKDIR /work
CMD ["python", "labs/19-hardware-generators/run.py"]
