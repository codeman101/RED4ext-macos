# find functions by (insns, distinct callers, distinct callees). usage: shape.py <bin> insns callers callees
import struct, re, subprocess, sys, bisect, collections
b = sys.argv[1]; n, nc, ne = map(int, sys.argv[2:5])
d = open(b, "rb").read()
o = subprocess.run(["otool", "-l", b], capture_output=True, text=True).stdout
m = re.search(r"sectname __text\n\s+segname __TEXT\n\s+addr 0x([0-9a-f]+)\n\s+size 0x([0-9a-f]+)\n\s+offset (\d+)", o)
tv, tsz, toff = int(m[1], 16), int(m[2], 16), int(m[3])
W = struct.unpack_from(f"<{tsz//4}I", d, toff)
def tgt(i, w):
    imm = w & 0x3FFFFFF
    return tv + 4*i + ((imm - (1 << 26) if imm & (1 << 25) else imm) << 2)
calls = []  # (site, target, is_bl)
for i, w in enumerate(W):
    op = w & 0xFC000000
    if op in (0x94000000, 0x14000000):
        t = tgt(i, w)
        if tv <= t < tv + tsz: calls.append((tv + 4*i, t, op == 0x94000000))
starts = sorted({t for s, t, bl in calls if bl})
callers = collections.defaultdict(set)
for s, t, bl in calls:
    if bl or t in set(): pass
for s, t, bl in calls:
    if bl or True:
        k = bisect.bisect_right(starts, s) - 1
        if k >= 0 and starts[k] != t: callers[t].add(starts[k])
for k, st in enumerate(starts[:-1]):
    sz = (starts[k+1] - st) // 4
    if sz != n or len(callers[st]) != nc: continue
    ce = {t for s, t, bl in calls if st <= s < starts[k+1] and t != st}
    if len(ce) == ne: print(hex(st - 0x100000000), sz, len(callers[st]), len(ce))
