#!/bin/sh
# Rebuilds a mobforge creature; bakes both skins in parallel: ./bake.sh eye_of_cthulhu [servant_of_cthulhu ...]
cd "$(dirname "$0")"
for name in "$@"; do
  python tools/mobforge/build.py "$name" --meta
  python tools/mobforge/build.py "$name" --phase 2 > /tmp/bake_p2.log 2>&1 &
  python tools/mobforge/build.py "$name" --phase 1 > /tmp/bake_p1.log 2>&1
  wait
  cat /tmp/bake_p1.log /tmp/bake_p2.log
done
