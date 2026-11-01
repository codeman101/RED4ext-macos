import re, struct, subprocess, sys
binp = sys.argv[1]
d = open(binp, "rb").read()
o = subprocess.run(["otool", "-l", binp], capture_output=True, text=True).stdout
ep = int(re.search(r"LC_MAIN.*?entryoff (\d+)", o, re.S).group(1))
print("main() at", hex(0x100000000 + ep))
def bl_targets(start, n=120):
    out = []
    for i in range(n):
        w = struct.unpack_from("<I", d, start + 4 * i)[0]
        if (w & 0xFC000000) == 0x94000000:
            imm = w & 0x3FFFFFF
            off = (imm - (1 << 26) if imm & (1 << 25) else imm) << 2
            out.append((hex(0x100000000 + start + 4 * i), hex(0x100000000 + start + 4 * i + off)))
        if w == 0xd65f03c0: print("ret at +", hex(4 * i)); break
    return out
for pc, t in bl_targets(ep): print("bl", pc, "->", t)
