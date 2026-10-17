#!/bin/sh
export XDG_RUNTIME_DIR="$(mktemp -d /tmp/hsd-sbt-XXXXXX)"
exec java -Xmx1G -Duser.home="$XDG_RUNTIME_DIR" -Dsbt.server.autostart=false \
  -Dsbt.supershell=false -Dsbt.override.build.repos=true \
  -Dsbt.repository.config=/opt/sbt-repositories -Dsbt.global.base=/opt/sbt-global \
  -Dsbt.boot.directory=/opt/sbt-boot -Dsbt.ivy.home=/opt/ivy \
  -jar /opt/sbt-launch.jar "$@"
