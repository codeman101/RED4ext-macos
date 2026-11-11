# distinct referencing functions per __DATA address (adrp + add/ldr/str imm within 4 insns). usage: dataxref.py <bin> lo hi [lo hi ...]
import struct, re, subprocess, sys, bisect, collections
b = sys.argv[1]; rng = [(int(sys.argv[i]), int(sys.argv[i+1])) for i in range(2, len(sys.argv), 2)]
d = open(b, "rb").read()
o = subprocess.run(["otool", "-l", b], capture_output=True, text=True).stdout
m = re.search(r"sectname __text\n\s+segname __TEXT\n\s+addr 0x([0-9a-f]+)\n\s+size 0x([0-9a-f]+)\n\s+offset (\d+)", o)
tv, tsz, toff = int(m[1], 16), int(m[2], 16), int(m[3])
W = struct.unpack_from(f"<{tsz//4}I", d, toff)
S = [int(l, 16) + 0x100000000 for l in open("notes/fstarts.txt")]
D0, D1 = 0x107d34000, 0x107d34000 + 0x1ff8000
refs = collections.defaultdict(set)
for i in range(len(W) - 4):
    w = W[i]
    if w & 0x9F000000 != 0x90000000: continue
    rd = w & 31
    immhi = (w >> 5) & 0x7FFFF; immlo = (w >> 29) & 3
    imm = (immhi << 2) | immlo
    if imm & (1 << 20): imm -= 1 << 21
    page = ((tv + 4*i) & ~0xFFF) + (imm << 12)
    if not D0 <= page < D1 + 0x1000: continue
    for j in range(i + 1, i + 5):
        x = W[j]
        if (x >> 5) & 31 != rd: continue
        if x & 0xFFC00000 == 0x91000000: off = (x >> 10) & 0xFFF      # add xd,xn,#imm
        elif x & 0xFFC00000 == 0xF9400000 or x & 0xFFC00000 == 0xF9000000: off = ((x >> 10) & 0xFFF) * 8  # ldr/str x
        elif x & 0xFFC00000 in (0xB9400000, 0xB9000000): off = ((x >> 10) & 0xFFF) * 4
        else: continue
        t = page + off
        refs[t].add(bisect.bisect_right(S, tv + 4*i))
        break
top = sorted(refs.items(), key=lambda kv: -len(kv[1]))
for t, fs in top[:10]: print('TOP', hex(t - 0x100000000), 'seg3:' + hex(t - D0), len(fs))
print('targets', len(refs))
for t, fs in top:
    n = len(fs)
    if any(lo <= n <= hi for lo, hi in rng): print(hex(t - 0x100000000), "seg3:" + hex(t - D0), n)
