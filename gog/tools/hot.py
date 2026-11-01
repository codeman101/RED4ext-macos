# Lists BL targets by caller count: python3 -I hot.py <binary> [min] [max] > hot.tsv
import re, struct, subprocess, sys, collections
binp = sys.argv[1]; lo = int(sys.argv[2]) if len(sys.argv) > 2 else 300; hi = int(sys.argv[3]) if len(sys.argv) > 3 else 100000
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
        if i + n - 1 >= len(W): return None
        if (W[i + n - 1] & 0xFFFFFC1F) == 0xd65f0000: return n
    return None
print("offset\tcallers\tinsns")
for a, c in sorted(callers.items(), key=lambda x: -x[1]):
    if lo <= c <= hi and tv <= a < tv + tsz: print(f"{a - 0x100000000:#x}\t{c}\t{insns(a)}")
