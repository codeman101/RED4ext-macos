#!/bin/sh
# Play the re-signed debug copy with RED4ext/TweakXL/ArchiveXL/Codeware injected, no lldb. Does not touch the real install.
G="$(cd "$(dirname "$0")" && pwd)/game"
cd "$G" || exit 1
DYLD_INSERT_LIBRARIES="$G/red4ext/RED4ext.dylib" exec "$G/Cyberpunk2077.app/Contents/MacOS/Cyberpunk2077" "$@"
