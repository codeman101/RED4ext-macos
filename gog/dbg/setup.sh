#!/bin/sh
# Builds dbg/game: a debuggable copy of the GOG binary (get-task-allow) beside symlinks to the real install.
# The original game folder is only read. Usage: dbg/setup.sh ["/Applications/Cyberpunk 2077"]
set -eu
R="${1:-/Applications/Cyberpunk 2077}"
H=$(cd "$(dirname "$0")" && pwd)
G="$H/game"
B="$G/Cyberpunk2077.app/Contents/MacOS/Cyberpunk2077"
rm -rf "$G"; mkdir -p "$(dirname "$B")"
cp "$R/Cyberpunk2077.app/Contents/MacOS/Cyberpunk2077" "$B"
codesign -f -s - -o runtime --entitlements "$H/dbg.plist" "$B"
for f in archive engine r6 Contents; do ln -s "$R/$f" "$G/$f"; done
for f in Frameworks Info.plist PkgInfo Resources embedded.provisionprofile; do
    ln -s "$R/Cyberpunk2077.app/Contents/$f" "$G/Cyberpunk2077.app/Contents/$f"
done
echo "ready: $B"
