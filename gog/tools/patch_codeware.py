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
    # game::Entity methods, found via stores to Entity.status (+0x156): Initialize=1, Detach 5->2, Uninitialize 6->7, Dispose 6->7, Attach 3->4.
    # Steam->GOG shift 0x13348A0 (Uninit/Detach/Dispose spacing identical to Steam, Assemble/Initialize/Reassemble land on function starts).
    0x19AA048: 0x2CDE8E8,  # Entity::Assemble
    0x19AA7D8: 0x2CDF078,  # Entity::Initialize
    0x19AB2D4: 0x2CDFB74,  # Entity::Uninitialize
    0x19AB4DC: 0x2CDFD7C,  # Entity::Detach
    0x19AB7F8: 0x2CE0098,  # Entity::Dispose
    0x19A7A30: 0x2CDC2D0,  # Entity::Reassemble (layout only)
    0x11E4964: 0x42DB400,  # IScriptable::DestructValueHolder (hash 0x3521331): frees [this+0x38] then nulls it
    0x10B09A4: 0x41AF6C8,  # ISerializable vfuncs block, same shift 0x30FED24 as 0x10B0860 (all GOG fn starts)
    0x10B0B44: 0x41AF868,
    0x10B0B6C: 0x41AF890,  # ISerializable::sub_A0 default (vtable+0xA8, most common GOG target)
    0x10B0C08: 0x41AF92C,
    0x10B0860: 0x41AF584,  # ISerializable default vfunc @vtable+0x48 (hash 2293436409): most common slot-9 target in GOG vtables, shift fits neighbours
    0x11A8F30: 0x42A2A78,  # ScriptValidator::ValidateProperty: ScriptProperty.type@+0xB8, ScriptType.metaType@+0x54 match the GOG body
    0x11A9108: 0x42A2C50,  # ScriptValidator::CompareType: same shift as Validate (gap to ValidateProperty 0x1D8 on both)
    0x111CC00: 0x4216860,  # ScriptBundle::~ScriptBundle: calls Clear (0x4216c70: HashMaps +0x8/+0x38/+0x68) then frees +0x1A0; shift 0x30F9C60 sits between neighbours
    0x11A7E28: 0x42A1970,  # ScriptValidator::Validate (validator,bundle,report): found via 'Validation failed for N types'
    0x529EC50: 0x529CA64,  # Entity::Attach (status 3->4 stores; not shape-verified)
    0x19A8040: 0x2CDC8E0,  # Entity_RequestComponents: Reassemble (0x19A7A30 -> 0x2CDC2D0) + 0x610 in both; body = vtable+0x198 call on the entity, then loops DynArray<Handle<IComponent>> (count +0xC, stride 0x10) with a2
    # Matched with aobmatch.py against the Steam 2.5.0 binary (same normalised instruction sequence, unique in both)
    0x16a5ba8: 0x1a2986c,  # 
    # ink::Layer helpers called by WidgetBuildingService::AttachWidgetTree (unpatched = stack smash at world load with Virtual Atelier)
    0x439c7e8: 0x153f4f0,  # inkWidget::GetLayerNative (hash 0x635f186e), EXACT, shift 0x2E5D2F8
    0x11278: 0x11258,  # unported Codeware entry, aobmatch EXACT unique
    0x15f70: 0x15f50,  # unported Codeware entry, aobmatch EXACT unique
    0x57968: 0x6bca60,  # unported Codeware entry, aobmatch EXACT unique
    0xe665c: 0x74b744,  # unported Codeware entry, aobmatch EXACT unique
    0x142e14: 0x7a7ef4,  # unported Codeware entry, aobmatch EXACT unique
    0x14efd4: 0x7b40b4,  # unported Codeware entry, aobmatch EXACT unique
    0x182e90: 0x7e7f70,  # unported Codeware entry, aobmatch EXACT unique
    0x30a5c8: 0x96f6a8,  # unported Codeware entry, aobmatch EXACT unique
    0x30ae7c: 0x96ff5c,  # unported Codeware entry, aobmatch EXACT unique
    0x315a88: 0x97ab68,  # unported Codeware entry, aobmatch EXACT unique
    0x1067f5c: 0x41697e0,  # unported Codeware entry, aobmatch EXACT unique
    0x1075718: 0x41761e8,  # unported Codeware entry, aobmatch EXACT unique
    0x10c18f4: 0x41bfbe0,  # unported Codeware entry, aobmatch EXACT unique
    0x10c1f6c: 0x41c0258,  # unported Codeware entry, aobmatch EXACT unique
    0x10c2074: 0x41c0360,  # unported Codeware entry, aobmatch EXACT unique
    0x10c37d8: 0x41c1abc,  # unported Codeware entry, aobmatch EXACT unique
    0x10c3934: 0x41c1c18,  # unported Codeware entry, aobmatch EXACT unique
    0x10cf100: 0x41cc974,  # unported Codeware entry, aobmatch EXACT unique
    0x10cf304: 0x41ccb78,  # unported Codeware entry, aobmatch EXACT unique
    0x10cf45c: 0x41cccd0,  # unported Codeware entry, aobmatch EXACT unique
    0x10e4454: 0x41e12a4,  # unported Codeware entry, aobmatch EXACT unique
    0x10e7f6c: 0x41e49c8,  # unported Codeware entry, aobmatch EXACT unique
    0x10ef37c: 0x41eb3e0,  # unported Codeware entry, aobmatch EXACT unique
    0x11e4da0: 0x42db83c,  # unported Codeware entry, aobmatch EXACT unique
    0x1203fa8: 0x42fa33c,  # unported Codeware entry, aobmatch EXACT unique
    0x1209038: 0x42fefd8,  # unported Codeware entry, aobmatch EXACT unique
    0x1215524: 0x430a584,  # unported Codeware entry, aobmatch EXACT unique
    0x1578050: 0x15d3a18,  # unported Codeware entry, aobmatch EXACT unique
    0x1665af4: 0x19ea1f0,  # unported Codeware entry, aobmatch EXACT unique
    0x1665c94: 0x19ea390,  # unported Codeware entry, aobmatch EXACT unique
    0x16f6c90: 0x1a7a5a4,  # unported Codeware entry, aobmatch EXACT unique
    0x16f6f7c: 0x1a7a890,  # unported Codeware entry, aobmatch EXACT unique
    0x19545c8: 0x2c89968,  # unported Codeware entry, aobmatch EXACT unique
    0x197f17c: 0x2cb3f8c,  # unported Codeware entry, aobmatch EXACT unique
    0x199e498: 0x2cd2eac,  # unported Codeware entry, aobmatch EXACT unique
    0x19f2f3c: 0x2d269a4,  # unported Codeware entry, aobmatch EXACT unique
    0x19f6ca8: 0x2d2a710,  # unported Codeware entry, aobmatch EXACT unique
    0x19f6e34: 0x2d2a89c,  # unported Codeware entry, aobmatch EXACT unique
    0x1a2bb60: 0x2d5e7b0,  # unported Codeware entry, aobmatch EXACT unique
    0x1a2bf84: 0x2d5ebd4,  # unported Codeware entry, aobmatch EXACT unique
    0x1a71548: 0x2da0dfc,  # unported Codeware entry, aobmatch EXACT unique
    0x1a71abc: 0x2da1370,  # unported Codeware entry, aobmatch EXACT unique
    0x1a730fc: 0x2da29b0,  # unported Codeware entry, aobmatch EXACT unique
    0x1b17694: 0x3cf3088,  # unported Codeware entry, aobmatch EXACT unique
    0x1e48378: 0x1d8b2a0,  # unported Codeware entry, aobmatch EXACT unique
    0x20a096c: 0x1fdb6d4,  # unported Codeware entry, aobmatch EXACT unique
    0x252c96c: 0x246819c,  # unported Codeware entry, aobmatch EXACT unique
    0x252cc3c: 0x246846c,  # unported Codeware entry, aobmatch EXACT unique
    0x2805874: 0x4ba2cd4,  # unported Codeware entry, aobmatch EXACT unique
    0x280c128: 0x4ba9588,  # unported Codeware entry, aobmatch EXACT unique
    0x280df0c: 0x4bab1a0,  # unported Codeware entry, aobmatch EXACT unique
    0x2aa79a8: 0x1730940,  # unported Codeware entry, aobmatch EXACT unique
    0x2bba088: 0x184caac,  # unported Codeware entry, aobmatch EXACT unique
    0x380f7cc: 0x3e186a8,  # unported Codeware entry, aobmatch EXACT unique
    0x387b840: 0x3e83b90,  # unported Codeware entry, aobmatch EXACT unique
    0x40075e8: 0x189eea4,  # unported Codeware entry, aobmatch EXACT unique
    0x4007b40: 0x189f3fc,  # unported Codeware entry, aobmatch EXACT unique
    0x4126c10: 0x39b1e90,  # unported Codeware entry, aobmatch EXACT unique
    0x4126dbc: 0x39b203c,  # unported Codeware entry, aobmatch EXACT unique
    0x4153d5c: 0x4115a40,  # unported Codeware entry, aobmatch EXACT unique
    0x41abd94: 0x1343160,  # unported Codeware entry, aobmatch EXACT unique
    0x41abea4: 0x1343270,  # unported Codeware entry, aobmatch EXACT unique
    0x432aff4: 0x14c738c,  # unported Codeware entry, aobmatch EXACT unique
    0x4353a7c: 0x14f3160,  # unported Codeware entry, aobmatch EXACT unique
    0x4353d74: 0x14f3458,  # unported Codeware entry, aobmatch EXACT unique
    0x4583398: 0x2e4f48c,  # unported Codeware entry, aobmatch EXACT unique
    0x472c880: 0x48ccde0,  # unported Codeware entry, aobmatch EXACT unique
    0x488518c: 0x402e700,  # unported Codeware entry, aobmatch EXACT unique
    0x48852d8: 0x402e84c,  # unported Codeware entry, aobmatch EXACT unique
    0x4d3fa5c: 0x524dcb8,  # unported Codeware entry, aobmatch EXACT unique
    0x4d74ab0: 0x3c443ec,  # unported Codeware entry, aobmatch EXACT unique
    0x4d74c20: 0x3c4455c,  # unported Codeware entry, aobmatch EXACT unique
    0x4ddf5c0: 0x4099e28,  # unported Codeware entry, aobmatch EXACT unique
    0x4fe0fb8: 0x47c87e0,  # unported Codeware entry, aobmatch EXACT unique
    0x4fe4ca0: 0x47cc4c8,  # unported Codeware entry, aobmatch EXACT unique
    0x41abbf4: 0x1342fc0,  # Raw::inkLogicController::OnInitialize: EXACT, twin 0x14f343c; 0x1342fc0 sits 0x1a0 before OnUninitialize (0x41abd94 -> 0x1343160) like on Steam
    0x78300d8: 0x7BFB050,  # CStack vtable (UniversalRelocVtbl 0x349a0ee1): GOG ctor 0x419c684/0x419c6a8 (EXACT twins of Steam 0x109d37c) store adrp+add 0x7BFB050
    0x43a0288: 0x1542f90,  # inkWidget::GetLayer (hash 0x95ff1902), EXACT, same shift 0x2E5D2F8 as the neighbouring AfterReparent hook
    0x42d3a38: 0x14682a8,  # hash 0x7a3f2670, EXACT x2 in GOG; the twin 0x146d13c crashed (VA PC dropdown, x19 inside it), so this one
    # DISABLED, crashes at start (Codeware+0x2b5040 -> GOG 0x4885324): 0x1578050: 0x15d3a18,  # 
    0x1086858: 0x4186438,  # 
    0x16f3714: 0x1a77028,  # 
    0x3140998: 0x1c63150,  # 
    0x43a7644: 0x154a34c,  # 
    0x43931a0: 0x1535d98,  # 
    0x435402c: 0x14f3710,  # 
    0x435424c: 0x14f3930,  # 
    # DISABLED, crashes when loading the world (ResourceLoader called with a bad loader): 0x4353d74: 0x14f3458,  # 
    0x4368f34: 0x150a1e0,  # 
    0x427028c: 0x1407b34,  # 
    # DISABLED, crashes at start (GOG 0x419a680): 0x1209038: 0x42fefd8,  # 
    0x51d4f30: 0x525f8e0,  # 
    0x12092e0: 0x42ff280,  # 
    0x19b74b0: 0x2cebc74,  # 
    0x19b95f4: 0x2ceddb8,  # 
    0x2b3dac0: 0x17ccc80,  # 
    0xfffcb8: 0x12b02f0,  # 
    0x426c760: 0x1404008,  # near (Jaccard 0.97) 
    0x1b1f1c8: 0x3cfaa4c,  # 
}
BY_OFF.update(CW)
for _o in [int(x, 16) for x in os.environ.get('CW_DISABLE', '').split(',') if x and x != 'all']:
    BY_OFF[_o] = 0  # debugging: disable a hook (bisecting)
if os.environ.get('CW_DISABLE') == 'all':
    BY_OFF = {k: 0 for k in BY_OFF}

# Hard-coded rva of the R30 script-loader wrapper (movz/movk pair in Mac::V1::InstallScriptLoadedHook).
# Codeware memcmp()s 32 bytes of prologue there; GOG 0x3C4A334 has the identical prologue and is called from InitEngine.
WRAPPER_STEAM, WRAPPER_GOG = 0x4D7A9F8, 0x3C4A334

def patch_wrapper_rva(data, WRAPPER_STEAM=WRAPPER_STEAM, WRAPPER_GOG=WRAPPER_GOG):
    n = 0
    for off in range(0, len(data) - 15, 4):
        a, = struct.unpack_from("<I", data, off)
        if a & 0xFFE00000 != 0xD2800000 or (a >> 5) & 0xFFFF != WRAPPER_STEAM & 0xFFFF:
            continue
        rd = a & 31
        for k in (4, 8, 12):  # movk may be a few instructions later
            b, = struct.unpack_from("<I", data, off + k)
            if b == 0xF2A00000 | ((WRAPPER_STEAM >> 16) << 5) | rd:
                struct.pack_into("<I", data, off, 0xD2800000 | ((WRAPPER_GOG & 0xFFFF) << 5) | rd)
                struct.pack_into("<I", data, off + k, 0xF2A00000 | ((WRAPPER_GOG >> 16) << 5) | rd)
                n += 1; break
    return n

# Mac::PatchScriptOpCodes hard-codes the script opcode handler table rva (Steam 0x9A5C940) in two places and
# writes New/Cast handlers through it; on GOG that stomped unrelated memory (Character menu crash in ScriptOpCodeNew).
HANDLERS_STEAM, HANDLERS_GOG = 0x9A5C940, 0x9AAEF30

SHA256 = {"3907fccf8cceec63c1e9daa04a001d58fd0be9bbfe6db162d090765b400a891d",  # Codeware 1.20.4 (RED4ext-macos 0.2.x)
          "e9b99654e95c19d38809afc460f2d54a4df6a1e88ec56e7e90dbcf35d709ed84"}  # Codeware 1.21.2 (RED4ext-macos 0.3.0)

def patch_movz(data, old, new):
    n = 0
    for off in range(0, len(data) - 3, 4):
        a, = struct.unpack_from("<I", data, off)
        if a & 0xFFE00000 == 0xD2800000 and (a >> 5) & 0xFFFF == old:
            struct.pack_into("<I", data, off, (a & ~(0xFFFF << 5)) | (new << 5)); n += 1
    return n

def main():
    src = sys.argv[1]; dst = sys.argv[2] if len(sys.argv) > 2 else src
    data = bytearray(open(src, "rb").read())
    if hashlib.sha256(data).hexdigest() not in SHA256:
        sys.exit("input is not the original Codeware dylib (sha256 mismatch)")
    n = v = 0
    for off in range(0, len(data) - 15, 4):
        h, z, o, z2 = struct.unpack_from("<IIII", data, off)
        if h > 0xFFFF and z == 0 and z2 == 0 and o in BY_OFF:
            struct.pack_into("<I", data, off + 8, BY_OFF[o]); n += 1
    # vault: 4 groups x 5 allocator RVAs; its place moves between Codeware builds, so take the VAULT hits that sit in a cluster
    hits = [off for off in range(0, len(data) - 7, 8) if struct.unpack_from("<Q", data, off)[0] in VAULT]
    for off in hits:
        if any(o != off and abs(o - off) <= 0x40 for o in hits):
            q = struct.unpack_from("<Q", data, off)[0]
            struct.pack_into("<Q", data, off, VAULT[q]); v += 1
    w = patch_wrapper_rva(data) + patch_wrapper_rva(data, HANDLERS_STEAM, HANDLERS_GOG)
    # Mac::MonotonicNs-style clock getter (cached mach_timebase_info): Codeware calls MacGameBase()+0x4B5C, GOG has it at 0x4B3C
    w += patch_movz(data, 0x4B5C, 0x4B3C)
    open(dst, "wb").write(data)
    subprocess.run(["codesign", "-f", "-s", "-", dst], check=True)
    print(f"patched {n} table entries, {v} vault slots, {w} wrapper rva -> {dst}")

if __name__ == "__main__":
    main()
