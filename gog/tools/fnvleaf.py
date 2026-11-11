# Leaf functions using FNV-1a 64 constants: python3 -I fnvleaf.py <binary> <fstarts.txt> [minsz] [maxsz]
import bisect, collections, re, struct, subprocess, sys
binp, fs = sys.argv[1:3]; lo = int(sys.argv[3]) if len(sys.argv) > 3 else 60; hi = int(sys.argv[4]) if len(sys.argv) > 4 else 160
d = open(binp, "rb").read()
o = subprocess.run(["otool", "-l", binp], capture_output=True, text=True).stdout
m = re.search(r"sectname __text\n\s+segname __TEXT\n\s+addr 0x([0-9a-f]+)\n\s+size 0x([0-9a-f]+)\n\s+offset (\d+)", o)
tv, tsz, toff = int(m.group(1), 16), int(m.group(2), 16), int(m.group(3)); base = tv - 0x100000000
S = sorted(int(x.split()[0], 16) for x in open(fs).read().split("\n") if x.strip())
W = struct.unpack_from(f"<{tsz // 4}I", d, toff)
callers = collections.defaultdict(set); fn = {}
def start(a): return S[bisect.bisect_right(S, a) - 1]
for i, w in enumerate(W):
    a = base + i * 4
    if w >> 26 in (0x25, 0x5):
        imm = w & 0x3ffffff; imm -= (1 << 26) if imm >> 25 else 0
        callers[a + imm * 4].add(start(a))
    # FNV prime low half movz #0x1b3 / basis pieces 0x2325
    if (w & 0x7f800000) == 0x52800000 and (w >> 5) & 0xffff in (0x1b3, 0x2325): fn.setdefault(start(a), set()).add((w >> 5) & 0xffff)
for f, k in sorted(fn.items()):
    if k != {0x1b3, 0x2325}: continue
    nxt = S[bisect.bisect_right(S, f)] if bisect.bisect_right(S, f) < len(S) else f
    n = (nxt - f) // 4
    if lo <= n <= hi:
        bl = sum(1 for j in range(f - base + base - base, 0) ) if False else 0
        print(f"{f:#x} insns={n} callers={len(callers.get(f, ()))}")
