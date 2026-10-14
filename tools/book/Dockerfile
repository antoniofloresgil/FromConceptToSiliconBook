# Linux/amd64 toolchain. Every additional Ubuntu package is hash-locked.
FROM busybox:1.37.0@sha256:bdf57e528e45e4433820e045b29b4597825a1c9e38353532d90a01445013f82e AS fetcher
FROM ubuntu:24.04@sha256:84e77dee7d1bc93fb029a45e3c6cb9d8aa4831ccfcc7103d36e876938d28895b
ENV DEBIAN_FRONTEND=noninteractive PYTHONDONTWRITEBYTECODE=1
COPY --from=fetcher /bin/busybox /usr/local/bin/busybox
COPY tools/book/fetch-debs.sh /opt/fetch-debs.sh
COPY tools/book/ubuntu-packages.lock /opt/ubuntu-packages.lock
RUN sh /opt/fetch-debs.sh /opt/ubuntu-packages.lock \
    && rm -rf /var/cache/apt/archives/*.deb /var/lib/apt/lists/* \
    && rm /usr/local/bin/busybox
RUN curl --fail --location --retry 3 \
      https://github.com/quarto-dev/quarto-cli/releases/download/v1.10.19/quarto-1.10.19-linux-amd64.deb \
      --output /tmp/quarto.deb \
    && echo '7f0c4769e7f0e55f50d922f44b18db5118fb388d2b8fd27291fe1f8beafb43eb  /tmp/quarto.deb' | sha256sum --check \
    && dpkg -i /tmp/quarto.deb \
    && rm /tmp/quarto.deb \
    && dpkg-query -W > /opt/book-packages.tsv
# Quarto loads Font Awesome for callouts even when their icons are disabled.
# Install only the versioned TeX Live archive, rather than a live font bundle.
RUN curl --fail --location --retry 3 \
      https://ftp.math.utah.edu/pub/tex/historic/systems/texlive/2023/tlnet-final/archive/fontawesome5.r63207.tar.xz \
      --output /tmp/fontawesome5.tar.xz \
    && echo '4d85aab86f679d360e7c7c812a055d9c03dd658e31bccfca4a97604497b0cc1c  /tmp/fontawesome5.tar.xz' | sha256sum --check \
    && mkdir -p /usr/local/share/texmf \
    && python -c "import tarfile; tarfile.open('/tmp/fontawesome5.tar.xz', 'r:xz').extractall('/usr/local/share/texmf', filter='data')" \
    && mktexlsr /usr/local/share/texmf \
    && kpsewhich fontawesome5.sty \
    && printf '%s\n' 'fontawesome5 5.15.4 r63207 sha256:4d85aab86f679d360e7c7c812a055d9c03dd658e31bccfca4a97604497b0cc1c' > /opt/book-extra-tex.txt \
    && rm /tmp/fontawesome5.tar.xz
WORKDIR /work
ENV TEXMFVAR=/tmp/book-texmf-var TEXMFCONFIG=/tmp/book-texmf-config XDG_CACHE_HOME=/tmp/book-cache
CMD ["python", "tools/book/build.py"]
