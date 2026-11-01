#!/usr/bin/env python3
"""Patch ArchiveXL 1.27.4 (RED4ext-macos) for the GOG 2.5.0 native build. WORK IN PROGRESS.

Usage: python3 -I patch_archivexl.py ArchiveXL.dylib [out.dylib]

Reuses the hash -> GOG offset map of patch_tweakxl.py (same Steam 2.5 offsets) and adds
ArchiveXL-only hashes. Entries are 16 bytes (hash, 0, offset, 0), embedded in many copies; matched by offset.
Hashes without a known GOG address keep their Steam offset (their hooks fail with
Detour error -2). All GOG values are UNVERIFIED candidates.
"""
import hashlib, os, struct, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from patch_tweakxl import TABLE as CORE, VAULT as TW_VAULT

SHA256 = "1d0b2c254a138fb789c96c59521f4b82ec5c841792736aad372045f454eeeb29"

# hash: (steam offset, gog offset)
EXTRA = {
    3998356057: (0x106C8C4, 0x416DDE0),  # ResourcePath_Create*: 107 insns (= Steam), FNV-1a 64 leaf, strips quotes and leading slashes
    3729789488: (0x4D7FBA8, 0x3C4FA84),  # CBaseEngine_LoadGatheredResources*: bool(CBaseEngine&), vcall +0x100, assert string
    2923109755: (0x442D290, 0x252F8D4),  # *candidate*: void(u64,u64) from ExtensionService::OnBootstrap; the only one of 52 shape candidates whose detour fires once, after the depot exists, with the game alive for 120 s
}
TABLE = {**CORE, **EXTRA}
# memory-vault expected allocator RVAs: same 20 values as TweakXL, stored as u64 in __data
VAULT = {old: new for _, old, new in TW_VAULT}
# PoolEngine / PoolRefCount / PoolDefault allocators sit in the early region: GOG = Steam - 0x20 (checked against nm)
for _o in (0x1f7d4, 0x1f8f0, 0x1fa1c, 0x1fb54, 0x1fc38, 0x1febc, 0x1ffd8, 0x20104, 0x2023c, 0x20320,
           0x222dc, 0x224a4, 0x22674, 0x22848, 0x2292c):
    VAULT[_o] = _o - 0x20
VAULT_RANGE = (0x1A0600, 0x1A0980)
# ArchiveXL also lists some functions under other hashes with the same Steam offset,
# so entries are matched by Steam offset, not by hash.
BY_OFF = {old: new for old, new in TABLE.values()}


def main():
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else src
    data = bytearray(open(src, "rb").read())
    if hashlib.sha256(data).hexdigest() != SHA256:
        sys.exit("input is not the original ArchiveXL 1.27.4 dylib (sha256 mismatch)")
    n = 0
    for off in range(0, len(data) - 15, 4):
        h, z, o, z2 = struct.unpack_from("<IIII", data, off)
        if h > 0xFFFF and z == 0 and z2 == 0 and o in BY_OFF:
            struct.pack_into("<I", data, off + 8, BY_OFF[o])
            n += 1
    v = 0
    for off in range(VAULT_RANGE[0], VAULT_RANGE[1], 8):
        q = struct.unpack_from("<Q", data, off)[0]
        if q in VAULT:
            struct.pack_into("<Q", data, off, VAULT[q])
            v += 1
    assert v == len(VAULT), f"vault slots patched: {v}, expected {len(VAULT)}"
    open(dst, "wb").write(data)
    subprocess.run(["codesign", "-f", "-s", "-", dst], check=True)
    print(f"patched {n} table entries, {v} vault slots -> {dst}")


if __name__ == "__main__":
    main()
