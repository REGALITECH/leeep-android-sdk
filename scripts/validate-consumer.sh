#!/bin/bash
set -euo pipefail

# Builds scripts/release-consumer as a release app (R8 enabled) that depends on the SDK through its POM,
# as a customer app does. Run it with JDK 17 and an Android SDK (ANDROID_HOME).
# --local publishes this checkout with the same Gradle publication JitPack runs (jitpack.yml) into a
# temporary Maven repository, so a pull request is validated before any tag exists and without JitPack.
# x.y.z consumes that version from JitPack. Versions JitPack has not built successfully are refused,
# because requesting one would start a JitPack build of a tag nobody has approved for release.
usage='Usage: scripts/validate-consumer.sh (--local | x.y.z)'
root=$(cd "$(dirname "$0")/.." && pwd)
target=${1:?$usage}
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

if [[ "$target" == --local ]]; then
  repository=local
  version=0.0.0-local
  "$root/gradlew" -p "$root" --no-daemon publishToMavenLocal \
    -Pversion="$version" -Dmaven.repo.local="$work/m2"
else
  [[ "$target" =~ ^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$ ]] || {
    echo 'Version must be x.y.z without a v prefix or leading zeroes.' >&2; exit 1;
  }
  repository=jitpack
  version=$target
  status=$(curl -fsS --max-time 30 "https://jitpack.io/api/builds/com.github.REGALITECH/leeep-android-sdk/$version" |
    python3 -c 'import json, sys; print(json.load(sys.stdin).get("status"))') || status=
  [[ "$status" == ok ]] || {
    echo "JitPack has not built $version successfully; refusing to request it." >&2; exit 1;
  }
fi

mkdir -p "$work/app/gradle"
cp -R "$root/scripts/release-consumer/." "$work/app/"
cp "$root/gradle/libs.versions.toml" "$work/app/gradle/"
"$root/gradlew" -p "$work/app" --no-daemon :app:assembleRelease \
  -PleeepSdkRepository="$repository" -PleeepSdkVersion="$version" -Dmaven.repo.local="$work/m2"
printf 'Built a release app with the SDK from %s (%s)\n' "$repository" "$version"
