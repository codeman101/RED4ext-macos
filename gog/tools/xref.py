# string/address xrefs via adrp+add pairs in __text. usage: xref.py <bin> 0xVMOFF...  (offset from image base)
import struct, re, subprocess, sys, bisect
b = sys.argv[1]; T = [int(x, 16) for x in sys.argv[2:]]
d = open(b, "rb").read()
o = subprocess.run(["otool", "-l", b], capture_output=True, text=True).stdout
m = re.search(r"sectname __text\n\s+segname __TEXT\n\s+addr 0x([0-9a-f]+)\n\s+size 0x([0-9a-f]+)\n\s+offset (\d+)", o)
tv, tsz, toff = int(m[1], 16), int(m[2], 16), int(m[3])
W = struct.unpack_from(f"<{tsz//4}I", d, toff)
S = sorted(int(l, 16) for l in open("notes/fstarts.txt"))
tg = {t: [] for t in T}
adrp = {}
for i, w in enumerate(W):
    pc = tv + 4*i - 0x100000000
    if w & 0x9F000000 == 0x90000000:
        imm = ((w >> 5) & 0x7FFFF) << 2 | ((w >> 29) & 3)
        if imm & 0x100000: imm -= 0x200000
        adrp[w & 31] = ((pc & ~0xFFF) + (imm << 12), i)
    elif w & 0xFF800000 == 0x91000000:
        rn = (w >> 5) & 31
        if rn in adrp and i - adrp[rn][1] < 8:
            a = adrp[rn][0] + ((w >> 10) & 0xFFF)
            if a in tg:
                k = bisect.bisect_right(S, pc) - 1
                tg[a].append((hex(S[k]), hex(pc)))
for t, v in tg.items(): print(hex(t), v[:8])
