#!/bin/sh
# Собирает архив для сдачи: только HEAD, без docs/source.
set -eu

cd "$(dirname "$0")/.."

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "ВНИМАНИЕ: есть незакоммиченные изменения, в архив попадёт только HEAD" >&2
fi

mkdir -p dist
commit=$(git rev-parse --short HEAD)
archive="dist/kontur-${commit}.zip"
git archive --format=zip --prefix=kontur/ -o "$archive" HEAD -- . ':(exclude)docs/source'
echo "$archive"