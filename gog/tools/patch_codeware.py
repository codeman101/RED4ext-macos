#!/usr/bin/env python3
"""Patch Codeware (RED4ext-macos) for the GOG 2.5.0 native build. WORK IN PROGRESS.
Usage: python3 -I patch_codeware.py Codeware.dylib.steam [out.dylib]
Reuses the Steam->GOG map of patch_archivexl.py; entries matched by Steam offset.
Unknown offsets keep Steam values (their hooks fail with Detour error -2)."""
import hashlib, os, struct, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from patch_archivexl import BY_OFF, VAULT

# Codeware-only entries: steam offset -> gog offset
CW = {
    0x4D7EFB8: 0x3C4EE94,  # CBaseEngine_InitEngine: contains 'FAILED - InkSystem'; same shift 0x1130124 as LoadGatheredResources
}
BY_OFF.update(CW)
for _o in [int(x, 16) for x in os.environ.get('CW_DISABLE', '').split(',') if x and x != 'all']:
    BY_OFF[_o] = 0  # debugging: disable a hook (bisecting)
if os.environ.get('CW_DISABLE') == 'all':
    BY_OFF = {k: 0 for k in BY_OFF}

SHA256 = "3907fccf8cceec63c1e9daa04a001d58fd0be9bbfe6db162d090765b400a891d"

def main():
    src = sys.argv[1]; dst = sys.argv[2] if len(sys.argv) > 2 else src
    data = bytearray(open(src, "rb").read())
    if hashlib.sha256(data).hexdigest() != SHA256:
        sys.exit("input is not the original Codeware dylib (sha256 mismatch)")
    n = v = 0
    for off in range(0, len(data) - 15, 4):
        h, z, o, z2 = struct.unpack_from("<IIII", data, off)
        if h > 0xFFFF and z == 0 and z2 == 0 and o in BY_OFF:
            struct.pack_into("<I", data, off + 8, BY_OFF[o]); n += 1
    for off in range(0x41EA00, 0x41EC00, 8):  # vault: 4 groups x 5 allocator RVAs
        q = struct.unpack_from("<Q", data, off)[0]
        if q in VAULT:
            struct.pack_into("<Q", data, off, VAULT[q]); v += 1
    open(dst, "wb").write(data)
    subprocess.run(["codesign", "-f", "-s", "-", dst], check=True)
    print(f"patched {n} table entries, {v} vault slots -> {dst}")

if __name__ == "__main__":
    main()
