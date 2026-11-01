# functions (size 40-90 insns) storing at +0xf0 and +0xf8 (str/stp), with <=4 distinct bl callees. usage: ctors.py <bin>
import struct, re, subprocess, sys, bisect
b = sys.argv[1]
d = open(b, "rb").read()
o = subprocess.run(["otool", "-l", b], capture_output=True, text=True).stdout
m = re.search(r"sectname __text\n\s+segname __TEXT\n\s+addr 0x([0-9a-f]+)\n\s+size 0x([0-9a-f]+)\n\s+offset (\d+)", o)
tv, tsz, toff = int(m[1], 16), int(m[2], 16), int(m[3])
W = struct.unpack_from(f"<{tsz//4}I", d, toff)
def tgt(i, w):
    imm = w & 0x3FFFFFF
    return tv + 4*i + ((imm - (1 << 26) if imm & (1 << 25) else imm) << 2)
S = sorted({tgt(i, w) for i, w in enumerate(W) if w & 0xFC000000 == 0x94000000})
for k in range(len(S) - 1):
    a, e = S[k], S[k+1]
    n = (e - a) // 4
    if not 40 <= n <= 90: continue
    ws = W[(a - tv)//4:(e - tv)//4]
    s0 = s8 = False; cal = set()
    for w in ws:
        if w & 0xFFC00000 == 0xF9000000:
            imm = (w >> 10) & 0xFFF
            s0 |= imm == 30; s8 |= imm == 31
        elif w & 0xFFC00000 == 0xA9000000:
            imm = (w >> 15) & 0x7F
            s0 |= imm == 30; s8 |= imm in (30, 31) and imm == 30 or imm == 31
        if w & 0xFC000000 == 0x94000000: cal.add(tgt(0, w) if False else w)
    ncal = sum(1 for w in ws if w & 0xFC000000 == 0x94000000)
    if s0 and s8 and ncal <= 5: print(hex(a - 0x100000000), n, ncal)
