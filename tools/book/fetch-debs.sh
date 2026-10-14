#!/bin/sh
# The committed lock was resolved using authenticated Ubuntu APT metadata.
# No live package resolution or unverified download occurs during this build.
set -eu
/usr/local/bin/busybox awk '/^\047/ {gsub(/\047/, "", $1); print $1, $2, $4}' "$1" \
  | /usr/local/bin/busybox xargs -r -P 8 -n 3 sh -ec '
    uri=$1
    file=/var/cache/apt/archives/$2
    checksum=${3#SHA256:}
    test "$checksum" != "$3"
    archived=$(printf "%s" "$uri" | /usr/local/bin/busybox sed "s@http://[^/]*/ubuntu/@https://snapshot.ubuntu.com/ubuntu/20261014T150000Z/@")
    /usr/local/bin/busybox wget -q "$uri" -O "$file" \
      || /usr/local/bin/busybox wget -q "$archived" -O "$file"
    printf "%s  %s\n" "$checksum" "$file" | sha256sum --check
  ' book-fetch
apt-get --yes --no-download --no-install-recommends install /var/cache/apt/archives/*.deb
