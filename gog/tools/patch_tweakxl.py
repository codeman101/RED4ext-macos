#!/usr/bin/env python3
"""Patch TweakXL 0.2.0 (RED4ext-macos) for the GOG 2.5.0 native build.

Usage: python3 -I patch_tweakxl.py TweakXL.dylib [out.dylib]

Input must be the unmodified Steam-targeted TweakXL.dylib (sha256 below).
Edits three kinds of Steam offsets inside the plugin:
  1. TABLE: u32 hash -> image offset entries (16 bytes: hash,0,offset,0),
     embedded 21 times (one copy per static initialiser). Offset 0 = no GOG
     address known (entry disabled).
  2. IMM: movz/movk immediates in InitializeAddressTable (old/new 32-bit words).
  3. VAULT: expected allocator RVAs of the memory vault self-check
     (4 pools x 5 slots, u64 at 0x1489a0 + pool*0x60 + 0x10 + slot*8).
Then re-signs ad hoc (codesign -f -s -). All GOG values are UNVERIFIED
candidates (see issue codeman101/RED4ext-macos#1). Not covered: the StatService
hook cluster (still Steam offsets, hook fails cleanly with Detour error -2).
"""
import hashlib, os, struct, subprocess, sys

SHA256 = "3be4622af250b6d66200ab9a7c775134e44892640d858433886cdecd8eee4504"

# hash: (steam offset, gog offset)
TABLE = {
    3778157291: (0x109B16C, 0x419A640),  # ExecuteNative (already found via the CBaseFunction anchor, same shift 0x30FF4D4)
    1652956141: (0x10C352C, 0x41C1810),  # same shift as CClass_CreateInstance (0x30FE2E4), lands on a function start; not body-checked
    1482886888: (0x10C3BC8, 0x41C1EAC),  # idem
    2399343890: (0x10C4C14, 0x41C2EF8),  # idem
    2502822355: (0x11AB310, 0x42A4E58),  # shift 0x30F9B48 of the ScriptValidator cluster; not body-checked
    1585257392: (0x19ACEF8, 0x2CE1798),  # Entity-group shift 0x13348A0; not body-checked
    10488987: (0x4E389D0, 0xF81B84),
    240386859: (0x323A0, 0x32380),
    404169501: (0x1099FBC, 0x4199490),
    838931066: (0x3309CC4, 0x2F5439C),
    859509764: (0x1025DC8, 0x4128D70),
    882511585: (0x78300D8, 0x7BFB050),  # CStack vtable (GOG ctors 0x419c684/0x419c6a8)
    914361828: (0x37CC900, 0x3416FE8),
    961751128: (0x9A5C940, 0x9AAEF30),
    1247874916: (0x10B3CAC, 0x41B2858),
    1409615660: (0x2914C, 0x2912C),
    1518341917: (0x10C36A0, 0x41C1984),
    1613572595: (0x109B8A4, 0x419AD78),
    1704595399: (0x805A7D8, 0x934F518),
    1759447004: (0x4E38940, 0xF81AF4),
    2057311186: (0x28674, 0x28654),
    2065762423: (0x2933C, 0x2931C),
    2920426135: (0x109B974, 0x419AE48),
    3062572522: (0x1EF64C8, 0x1E37C3C),
    3121353053: (0x1025C8C, 0x4128C34),
    3357477547: (0x2CCAC, 0x2CC8C),
    3512345737: (0x37D60CC, 0x3420770),
    3602585178: (0x37CE05C, 0x3418744),
    3649309656: (0x4E38978, 0xF81B2C),
    3689484881: (0x10B0B44, 0x0),
    3791200470: (0x1098FC0, 0x4198494),
    3904113489: (0x2AA74, 0x2AA54),
    4201325776: (0x109BAA8, 0x419AF7C),
    # job system cluster (7/7 relative layout match, shift -0xD45798)
    1862212562: (0x4DE2D7C, 0x409D5E4),
    242552139: (0x4DDF1C4, 0x4099A2C),
    2193429752: (0x4DDEF64, 0x40997CC),
    69014212: (0x4DDF3C4, 0x4099C2C),
    1525942140: (0x4DDF488, 0x4099CF0),
    3651996672: (0x4DDF354, 0x4099BBC),
    2621709954: (0x4DE3088, 0x409D8F0),
    2655521326: (0x4DDF828, 0x409A090),
    2627471740: (0x4DDF868, 0x409A0D0),
    3235774480: (0x4DF0D14, 0x40AB57C),  # same shift, start verified only
    1508445968: (0x9D0E550, 0x9A2E340),  # JobQueue global (&ptr): game loads it with adrp/ldr in the callers of 0x409d8f0
}

# (file offset, old word, new word)
IMM = [
    (0xB7B6C, 0x52847408, 0x52847008),
    (0xB7BA0, 0x528C9917, 0x528F8797),
    (0xB7BA4, 0x72A03DF7, 0x72A03C77),
    (0xB7C00, 0x529C0B97, 0x5290E897),
    (0xB7C04, 0x72A06F97, 0x72A06837),
    (0xB7C60, 0x528C1997, 0x5280EE17),
    (0xB7C64, 0x72A06FB7, 0x72A06857),
    (0xB7CC0, 0x52939888, 0x52887388),
    (0xB7CC4, 0x72A06608, 0x72A05EA8),
    (0xB7CF4, 0x52992008, 0x528DFD08),
    (0xB7CF8, 0x72A06F88, 0x72A06828),
    (0xB7D28, 0x52879588, 0x52850B08),
    (0xB7D2C, 0x72A02168, 0x72A08368),
    (0xB7D5C, 0x52999588, 0x52999188),
    (0xB7D90, 0x5290CE97, 0x5290CA97),
    (0xB7DC8, 0x52954E88, 0x52954A88),
    (0xB7E58, 0x52912817, 0x52835E97),
    (0xB7E5C, 0x72A09C77, 0x72A01F17),
    (0xB7EF0, 0x528B9197, 0x52918697),
    (0xB7EF4, 0x72A02057, 0x72A08257),
    (0xB7F28, 0x5294FB08, 0x52800008),
    (0xB7F2C, 0x72A100A8, 0x72A00008),
    (0xB7F5C, 0x5286D408, 0x52833088),
    (0xB7F60, 0x72A02188, 0x72A08388),
    (0xB7F90, 0x5291F818, 0x52909298),
    (0xB7F94, 0x72A02138, 0x72A08338),
    (0xB7FC8, 0x52801B08, 0x52800008),
    (0xB7FCC, 0x72A0F068, 0x72A00008),
    (0xB7FFC, 0x52816888, 0x52800008),
    (0xB8000, 0x72A02168, 0x72A00008),
]

# (file offset, old u64, new u64)
VAULT = [
    (0x1489B0, 0x10A1FA4, 0x41A0CC8),
    (0x1489B8, 0x10A20C0, 0x41A0DE4),
    (0x1489C0, 0x10A21EC, 0x41A0F10),
    (0x1489C8, 0x10A2324, 0x41A1048),
    (0x1489D0, 0x10A2408, 0x41A112C),
    (0x148A10, 0x10A268C, 0x41A13B0),
    (0x148A18, 0x10A27A8, 0x41A14CC),
    (0x148A20, 0x10A28D4, 0x41A15F8),
    (0x148A28, 0x10A2A0C, 0x41A1730),
    (0x148A30, 0x10A2AF0, 0x41A1814),
    (0x148A70, 0x10A2D74, 0x41A1A98),
    (0x148A78, 0x10A2E90, 0x41A1BB4),
    (0x148A80, 0x10A2FBC, 0x41A1CE0),
    (0x148A88, 0x10A30F4, 0x41A1E18),
    (0x148A90, 0x10A31D8, 0x41A1EFC),
    (0x148AD0, 0x4E33A00, 0xF7CB58),
    (0x148AD8, 0x4E33B1C, 0xF7CC74),
    (0x148AE0, 0x4E33C48, 0xF7CDA0),
    (0x148AE8, 0x4E33D80, 0xF7CED8),
    (0x148AF0, 0x4E33E64, 0xF7CFBC),
]


def main():
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else src
    data = bytearray(open(src, "rb").read())
    if hashlib.sha256(data).hexdigest() != SHA256:
        sys.exit("input is not the original TweakXL 0.2.0 dylib (sha256 mismatch)")
    n = 0
    for off in range(0, len(data) - 15, 4):
        h, z, o, z2 = struct.unpack_from("<IIII", data, off)
        if h in TABLE and z == 0 and z2 == 0 and o == TABLE[h][0]:
            struct.pack_into("<I", data, off + 8, TABLE[h][1])
            n += 1
    assert n == 21 * len(TABLE), f"table entries patched: {n}, expected {21 * len(TABLE)}"
    for off, old, new in IMM:
        assert struct.unpack_from("<I", data, off)[0] == old, hex(off)
        struct.pack_into("<I", data, off, new)
    for off, old, new in VAULT:
        assert struct.unpack_from("<Q", data, off)[0] == old, hex(off)
        struct.pack_into("<Q", data, off, new)
    if os.environ.get("TWEAKXL_NO_SCRIPT_TWEAKS"):
        # TweakExecutor::ExecuteTweaks -> ret. Script tweaks call CBaseFunction::ExecuteScripted
        # (GOG 0x4198494), which crashes on GOG (CStack vtable reads as 0). YAML/xl tweaks unaffected.
        assert struct.unpack_from("<I", data, 0x61940)[0] == 0xD10303FF
        struct.pack_into("<I", data, 0x61940, 0xD65F03C0)
        print("script tweaks disabled")
    open(dst, "wb").write(data)
    subprocess.run(["codesign", "-f", "-s", "-", dst], check=True)
    print(f"patched {n} table entries, {len(IMM)} immediates, {len(VAULT)} vault slots -> {dst}")


if __name__ == "__main__":
    main()
