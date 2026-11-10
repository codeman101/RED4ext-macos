#!/bin/sh
# Builds GogFixes.dylib against the RED4ext SDK in deps/ and signs it ad hoc. Usage: gog/plugin/build.sh [out_dir]
set -eu
H=$(cd "$(dirname "$0")" && pwd)
OUT="${1:-$H/out}"
mkdir -p "$OUT"
clang++ -std=c++20 -O2 -dynamiclib -fvisibility=hidden -o "$OUT/GogFixes.dylib" "$H/GogFixes.cpp" \
    -I "$H/../../deps/red4ext.sdk/include"
codesign -f -s - "$OUT/GogFixes.dylib"
