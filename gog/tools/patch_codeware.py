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
    w = patch_wrapper_rva(data) + patch_wrapper_rva(data, HANDLERS_STEAM, HANDLERS_GOG)
    open(dst, "wb").write(data)
    subprocess.run(["codesign", "-f", "-s", "-", dst], check=True)
    print(f"patched {n} table entries, {v} vault slots, {w} wrapper rva -> {dst}")

if __name__ == "__main__":
    main()
