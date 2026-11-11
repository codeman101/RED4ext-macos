# Direct callers (bl / b) of given function offsets: python3 -I callers.py <binary> <fstarts.txt> <hexoff>...
import bisect, re, struct, subprocess, sys
binp, fs, *T = sys.argv[1:]; T = {int(x, 16) for x in T}
d = open(binp, "rb").read()
o = subprocess.run(["otool", "-l", binp], capture_output=True, text=True).stdout
m = re.search(r"sectname __text\n\s+segname __TEXT\n\s+addr 0x([0-9a-f]+)\n\s+size 0x([0-9a-f]+)\n\s+offset (\d+)", o)
tv, tsz, toff = int(m.group(1), 16), int(m.group(2), 16), int(m.group(3))
S = sorted(int(x.split()[0], 16) for x in open(fs).read().split("\n") if x.strip())
W = struct.unpack_from(f"<{tsz // 4}I", d, toff)
base = tv - 0x100000000
for i, w in enumerate(W):
    if w >> 26 in (0x25, 0x5):
        imm = w & 0x3ffffff; imm -= (1 << 26) if imm >> 25 else 0
        a = base + i * 4; t = a + imm * 4
        if t in T:
            f = S[bisect.bisect_right(S, a) - 1]
            print(f"{'bl' if w >> 31 else 'b '} {t:#x} <- {a:#x} (fn {f:#x}, +{a - f:#x})")
