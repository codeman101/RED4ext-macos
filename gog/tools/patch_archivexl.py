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
# Localization: found by the en-us onscreens/subtitles path hashes in x0 (lldb, dbg/loc.py); 0x214 apart like Steam
BY_OFF[0x1C2B6DC] = 0x4020160  # Localization_LoadOnScreens
BY_OFF[0x1C2B4C8] = 0x401FF4C  # Localization_LoadSubtitles
BY_OFF[0x20085B4] = 0x1F47D78
BY_OFF[0x2008864] = 0x1F48028
BY_OFF[0x4BC779C] = 0x50D6084
BY_OFF[0x4BC7B24] = 0x50D640C
BY_OFF[0x200C940] = 0x1F4C210   # ItemFactoryAppearanceChangeRequest_LoadTemplate
BY_OFF[0x200CD00] = 0x1F4C5D0   # ItemFactoryAppearanceChangeRequest_LoadAppearance
BY_OFF[0x20133F4] = 0x1F52CC4   # ItemFactoryRequest_LoadAppearance
# Matched with aobmatch.py against the Steam 2.5.0 binary (same normalised instruction sequence, unique in both binaries)
BY_OFF[0x12090b0] = 0x42ff050  # ResourceSerializer_OnDependenciesReady
BY_OFF[0x19c6380] = 0x2cfac8c  # EntityTemplate_OnLoad
BY_OFF[0x51ca1a4] = 0x434614c  # MorphTargetMesh_PostLoad
BY_OFF[0x19b3e70] = 0x2ce8634  # EntityBuilder_ScheduleExtractComponentsJob
# DISABLED, null deref in the detour (x0=0) after ~20 min, same site as the G0 bisect crashes: BY_OFF[0x2d0d090] = 0x1bbb1e0  # PersistencySystem_SetPersistentStateData
BY_OFF[0x19d50c8] = 0x2d09908  # FactoryIndex_LoadFactoryAsync
BY_OFF[0x3f2bd00] = 0x38626ac  # Localization_LoadLipsyncs
BY_OFF[0x52360b4] = 0x34f66cc  # ?
BY_OFF[0x520854c] = 0x34c8118  # JournalRootFolderEntry_Initialize
BY_OFF[0x30fb9f0] = 0x1c1ad1c  # MappinSystem_OnStreamingWorldLoaded
BY_OFF[0x18a5174] = 0x2bdd3c0  # AnimatedComponent_InitializeAnimations
BY_OFF[0x1e05eec] = 0x1d493cc  # AttachmentSlots_InitializeSlots
BY_OFF[0x1e0dadc] = 0x1d50fbc  # AttachmentSlots_IsSlotSpawning
BY_OFF[0x1ea5b54] = 0x1de8e28  # TPPRepresentationComponent_OnItemEquipped
BY_OFF[0x1ea50bc] = 0x1de8390  # TPPRepresentationComponent_OnItemUnequipped
# DISABLED, crashes at runtime (SIGSEGV 32 s after start): BY_OFF[0x4bb13fc] = 0x50bfce4  # CharacterCustomizationFeetController_CheckState
BY_OFF[0x1a59e30] = 0x2d89eb8  # AppearanceChangeSystem_ChangeAppearance1
BY_OFF[0x1a5c6e0] = 0x2d8c768  # AppearanceChangeSystem_ChangeAppearance2
BY_OFF[0x19c4808] = 0x2cf9114  # EntityTemplate_FindAppearance
BY_OFF[0x17dd6c0] = 0x2b1a79c  # AppearanceResource_FindAppearanceDefinition
# DISABLED, crashes at the intro video skip (bad pointer in the detour, ArchiveXL+0x8c734): BY_OFF[0x2605214] = 0x253ed1c  # AppearanceNameVisualTagsPreset_GetVisualTags
# DISABLED, crashes in-game (bad pointer in the detour, ArchiveXL+0x8c734), sibling of 0x2605214: BY_OFF[0x26050f8] = 0x253ec00  # ?
BY_OFF[0x17ebff0] = 0x2b29150  # GarmentAssembler_ProcessGarment
BY_OFF[0x17eb4ac] = 0x2b2860c  # GarmentAssembler_ProcessSkinnedMesh
BY_OFF[0x17ebc80] = 0x2b28de0  # GarmentAssembler_ProcessMorphedMesh
BY_OFF[0x2030d18] = 0x1f70c70  # GarmentAssembler_OnGameDetach
BY_OFF[0x19e7bc0] = 0x2d1b770  # AppearanceChanger_RegisterPart
BY_OFF[0x2020a80] = 0x1f6091c  # AppearanceChanger_ComputePlayerGarment
# DISABLED, crashes at runtime (SIGSEGV in the detour): BY_OFF[0x4bae148] = 0x50bca30  # CharacterCustomizationGenitalsController_OnAttach
BY_OFF[0x4baf2c0] = 0x50bdba8  # CharacterCustomizationHairstyleController_OnDetach
BY_OFF[0x29e8c48] = 0x4d81044  # QuestLoader_ProcessPhaseResource
BY_OFF[0x2a0b26c] = 0x4da2d9c  # QuestsSystem_OnGameRestored
BY_OFF[0x2811df0] = 0x4bae968  # QuestRootInstance_Start
BY_OFF[0x1c05360] = 0x3ddbb60  # StreamingSector_PostLoad
BY_OFF[0x267f100] = 0x25bf6b0  # AIWorkspotManager_RegisterSpots
# Same, but the match is not instruction-for-instruction (Jaccard 0.90-0.99 on 3-gram shapes)
BY_OFF[0x17df10c] = 0x2b1c1e8  # AppearanceResource_PostLoad (near)
BY_OFF[0x17d3158] = 0x2b10db4  # AppearanceDefinition_ExtractPartComponents (near)
# DISABLED, near match is wrong (ResourceLoader null loader crash): BY_OFF[0x1207588] = 0x42fd5dc  # ResourceSerializer_Load (near)
BY_OFF[0x3fe6c94] = 0x4041efc  # Localization_LoadVoiceOvers (near)
BY_OFF[0x201dcc8] = 0x1f5d598  # AppearanceChanger_GetSuffixes (near)
BY_OFF[0x2043b04] = 0x1f83b58  # AppearanceChanger_SelectAppearanceName (near)
# DISABLED, crashes when equipping a cap (SIGSEGV in the detour, ArchiveXL+0x2c0d4), near match, sibling of 0x4bb13fc: BY_OFF[0x4bb0ac0] = 0x50bf3a8  # CharacterCustomizationHairstyleController_CheckState (near)
for _o in [int(x, 16) for x in os.environ.get('AXL_DISABLE', '').split(',') if x]:
    BY_OFF[_o] = 0  # debugging: disable a hook (bisecting), Steam offsets


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
