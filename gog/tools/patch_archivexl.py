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
    2885423437: (0x151A118, 0x3EF35A8),  # ResourceDepot_InitializeArchives: 241 insns, 1 caller (like Steam), contains the 'Failed to find any archives in the base data directory' assert
    2509382878: (0x46E03B8, 0x515E35C),  # *candidate* gameIGameSystem_Spawn*: shape 228/13/9 vs Steam 232/14/9, only close match
    2923109755: (0x442D290, 0x252F8D4),  # *candidate*: void(u64,u64) from ExtensionService::OnBootstrap; the only one of 52 shape candidates whose detour fires once, after the depot exists, with the game alive for 120 s
    1250309504: (0x10E7060, 0x41E3ABC),  # ResourceLoader_IssueLoadingRequestByPath: 43 insns, request {1 at +0x19, -1 at +0x20, 0 at +0x28}, x8 out, x0 loader, x1 path (matches the SDK note)
    2365013187: (0x10E710C, 0x41E3B68),  # ResourceLoader_IssueLoadingRequest: next function, same 0xAC distance as in Steam, x8 out, x0 loader, x1 request
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

# Cluster matches by relative layout (all landed on exact function starts with one shift per cluster).
# CharacterCustomization*: 14 functions, shift 0x50E8E8 (CCSystem 5/5 unique match; the rest verified to land on starts).
# The 4 controller virtuals (Genitals OnAttach 0x4BAE148, Hairstyle OnDetach 0x4BAF2C0/CheckState 0x4BB0AC0, Feet CheckState 0x4BB13FC)
# also land on function starts with this shift but are left out: ArchiveXL's handlers crash (component owner at +0x50 null,
# called from the generic component tick), so the GOG targets are probably shared code, not the Steam functions.
for _o in (0x4BBF004, 0x4BBF438, 0x4BBF6F8, 0x4BBF9B8, 0x4BBFC78,
           0x4BBFF38, 0x4BC5098, 0x4BC83A8, 0x4BD3F5C, 0x4BD448C, 0x4BD53AC):
    BY_OFF[_o] = _o + 0x50E8E8
# GarmentAssembler FindState/AddItem/AddCustomItem/RemoveItem + 2 more: 6 exact starts at shift -0xC083C, the only hit near the
# neighbouring TweakXL entries' shift (-0xBE88C); bodies not checked.
for _o in (0x2007BC4, 0x2007DCC, 0x2007EBC, 0x2008310, 0x200857C, 0x200882C):
    BY_OFF[_o] = _o - 0xC083C
# NOT ported: ItemFactory*Request LoadTemplate/LoadAppearance (0x200C940/0x200CD00/0x20133F4) and AppearanceChanger_GetSuffixes (0x201DCC8).
# Shift -0xC0730 gives 4 exact function starts, but with it the game aborts with __stack_chk_fail (call chain 0x1F4BBA8 -> 0x1F4BC10 -> 0x19D5340),
# i.e. the targets are wrong (0x1F4C210...). Still open.
# CMesh: shift -0xE843D8, 6/6 unique; ShouldPreloadAppearances reads forceLoadAllAppearances at +0x6D like the SDK.
for _o in (0x519A58C, 0x519A844, 0x519ADA4, 0x519AEBC, 0x519C4B0, 0x519C6DC, 0x519E118):
    BY_OFF[_o] = _o - 0xE843D8

# ResourceDepot RequestResource / CheckResource: next to InitializeArchives (0x151A118 -> 0x3EF35A8) the Steam layout is kept (-4 each):
# Steam +0x630/+0x914 -> GOG 0x3EF3BD4 (size 0x2E4 = Steam distance 0x151AA2C-0x151A748) and 0x3EF3EB8. Request locks depot+0xE8,
# walks 0x38-byte entries and compares an int32 archive handle with -1; Check is a small wrapper building a temporary and looking up.
BY_OFF[0x151A748] = 0x3EF3BD4
BY_OFF[0x151AA2C] = 0x3EF3EB8

# More neighbours of already-resolved anchors, same Steam distance in GOG (all land on function starts):
# ResourceDepot_LoadArchives = CheckResource + 0x760 (body: loops the DynArray<CString> paths, count +0xC, stride 0x20, stores mode/severity args);
# GarmentAssemblerState ChangeItem/ChangeCustomItem = +0x38 from AddItem/RemoveItem anchors; CharacterCustomizationSystem Initialize/GetResource inside the
# +0x50E8E8 cluster.
BY_OFF[0x151B18C] = 0x3EF4618
BY_OFF[0x20085B4] = 0x1F47D78
BY_OFF[0x2008864] = 0x1F48028
# held back (character menu untested, see notes): BY_OFF[0x4BC779C] = 0x50D6084
# held back (character menu untested, see notes): BY_OFF[0x4BC7B24] = 0x50D640C


def main():
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else src
    data = bytearray(open(src, "rb").read())
    if hashlib.sha256(data).hexdigest() != SHA256:
        sys.exit("input is not the original ArchiveXL 1.27.4 dylib (sha256 mismatch)")
    import patch_codeware  # shares entries (Entity::Reassemble, InitEngine, ...) that ArchiveXL also hooks
    BY_OFF.update(patch_codeware.CW)
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
