# exact-size shape search using notes/fstarts.txt. usage: shape2.py <bin> insns callers callees
import struct, re, subprocess, sys, bisect, collections
b = sys.argv[1]; n, nc, ne = map(int, sys.argv[2:5])
d = open(b, "rb").read()
o = subprocess.run(["otool", "-l", b], capture_output=True, text=True).stdout
m = re.search(r"sectname __text\n\s+segname __TEXT\n\s+addr 0x([0-9a-f]+)\n\s+size 0x([0-9a-f]+)\n\s+offset (\d+)", o)
tv, tsz, toff = int(m[1], 16), int(m[2], 16), int(m[3])
W = struct.unpack_from(f"<{tsz//4}I", d, toff)
S = [int(l, 16) + 0x100000000 for l in open("notes/fstarts.txt")]
S = [a for a in S if tv <= a < tv + tsz]; S.append(tv + tsz)
cal = collections.defaultdict(set); ce = collections.defaultdict(set)
for i, w in enumerate(W):
    if w & 0x7C000000 == 0x14000000:
        imm = w & 0x3FFFFFF; t = tv + 4*i + ((imm - (1 << 26) if imm & (1 << 25) else imm) << 2)
        s = tv + 4*i; k = bisect.bisect_right(S, s) - 1
        if S[k] != t and t in set_ if False else True:
            ce[S[k]].add(t); cal[t].add(S[k])
for k in range(len(S) - 1):
    a = S[k]
    if (S[k+1] - a) // 4 == n and len(cal[a]) == nc and len(ce[a]) == ne: print(hex(a - 0x100000000))
