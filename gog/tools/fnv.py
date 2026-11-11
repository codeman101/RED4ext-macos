import re, struct, subprocess, sys, bisect
binp = sys.argv[1]
d = open(binp, "rb").read()
o = subprocess.run(["otool", "-l", binp], capture_output=True, text=True).stdout
m = re.search(r"sectname __text\n\s+segname __TEXT\n\s+addr 0x([0-9a-f]+)\n\s+size 0x([0-9a-f]+)\n\s+offset (\d+)", o)
tv, tsz, toff = int(m.group(1), 16), int(m.group(2), 16), int(m.group(3))
W = struct.unpack_from(f"<{tsz // 4}I", d, toff)
def mov(i, hw, imm, k):  # movz(hw0)/movk
    w = W[i]; return (w & 0x7F800000) == k and ((w >> 21) & 3) == hw and ((w >> 5) & 0xFFFF) == imm
syms = sorted(int(l.split()[0], 16) for l in open(sys.argv[2]) if len(l.split()) == 3 and l.split()[1] in "tT")
def func(pc):
    j = bisect.bisect_right(syms, pc) - 1
    return syms[j] if j >= 0 else None
# basis 0xcbf29ce484222325 as movz #0x2325; movk 0x8422<<16; movk 0x9ce4<<32; movk 0xcbf2<<48 (any order near)
hits = []
for i in range(len(W) - 8):
    if mov(i, 0, 0x2325, 0x52800000 | 0x20000000 | 0x80000000) or True:
        pass
    w = W[i]
    if (w & 0x7F800000) in (0x52800000, 0x72800000) and (w >> 31) and ((w >> 21) & 3) == 0 and ((w >> 5) & 0xFFFF) == 0x2325:
        rd = w & 31; found = {1: 0x8422, 2: 0x9ce4, 3: 0xcbf2}; ok = set()
        for j in range(i + 1, i + 8):
            x = W[j]
            if (x & 0x7F800000) == 0x72800000 and (x >> 31) and (x & 31) == rd and ((x >> 5) & 0xFFFF) == found.get((x >> 21) & 3, -1):
                ok.add((x >> 21) & 3)
        if ok == {1, 2, 3}: hits.append(tv + 4 * i)
print("FNV-1a-64 basis loads:", len(hits))
fns = sorted({func(h) for h in hits if func(h)})
print("distinct nm-anchored functions:", len(fns))
for h in hits[:40]: print(hex(h), "fn~", hex(func(h)) if func(h) else None)
print("--- CNamePool pair search")
hs = set(hits)
cands = []
for i in range(len(W) - 2):
    if W[i] == 0xf9400000 and (W[i + 1] & 0xFC000000) == 0x14000000:  # ldr x0,[x0]; b
        pc = tv + 4 * i
        near = [h for h in hits if pc + 0x40 <= h <= pc + 0x400]
        if near: cands.append((pc, near[0]))
print("ldr x0,[x0]; b  followed by FNV basis within 0x40..0x400:", len(cands))
for pc, h in cands[:15]: print(hex(pc), "-> FNV at", hex(h), f"(+{h-pc:#x})")
# Steam relation: Get=0x4E38940, wrapper 0x4E38948, AddCstr=0x4E389D0 -> AddCstr-Get=0x90
print("with AddCstr start at Get+0x90 (+/-0x10):", [hex(pc) for pc, h in cands if pc + 0x80 <= h <= pc + 0xC0])
