import re, struct, subprocess, sys, collections
binp = sys.argv[1]
d = open(binp, "rb").read()
o = subprocess.run(["otool", "-l", binp], capture_output=True, text=True).stdout
m = re.search(r"sectname __text\n\s+segname __TEXT\n\s+addr 0x([0-9a-f]+)\n\s+size 0x([0-9a-f]+)\n\s+offset (\d+)", o)
tv, tsz, toff = int(m.group(1), 16), int(m.group(2), 16), int(m.group(3))
W = struct.unpack_from(f"<{tsz // 4}I", d, toff)
callers = collections.Counter()
for i, w in enumerate(W):
    if (w & 0xFC000000) == 0x94000000:
        imm = w & 0x3FFFFFF
        callers[tv + 4 * i + ((imm - (1 << 26) if imm & (1 << 25) else imm) << 2)] += 1
def insns(a):
    i = (a - tv) // 4
    for n in range(1, 400):
        if (W[i + n - 1] & 0xFFFFFC1F) == 0xd65f0000: return n
    return None
# name, steam offset, expected insns (2.5), expected callers (2.5)
T = [("Handle_DecWeakRef", 0x1025DC8, 21, 19913), ("DynArray_Realloc", 0x28674, 130, 8262),
     ("CString_ctor_str", 0x2CCAC, 52, 1944), ("CString_dtor", 0x2914C, 14, None), ("CString_copy", 0x2AA74, 65, None)]
for name, so, ei, ec in T:
    print(f"== {name}  steam {so:#x} expect insns~{ei} callers~{ec}")
    best = []
    for a, c in callers.items():
        off = a - 0x100000000
        if abs(off - so) > 0x3000: continue
        n = insns(a)
        if n is None or abs(n - ei) > 3: continue
        if ec and abs(c - ec) > ec * 0.03: continue
        best.append((abs(off - so), off, n, c))
    for _, off, n, c in sorted(best)[:6]: print(f"  cand {off:#x} (delta {off - so:+#x}) insns={n} callers={c}")
