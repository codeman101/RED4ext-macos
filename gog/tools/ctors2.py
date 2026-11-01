# exact-size ctor search. usage: ctors2.py <bin> <sizes comma>  (needs notes/fstarts.txt)
import struct, re, subprocess, sys
b = sys.argv[1]; sizes = set(map(int, sys.argv[2].split(",")))
d = open(b, "rb").read()
o = subprocess.run(["otool", "-l", b], capture_output=True, text=True).stdout
m = re.search(r"sectname __text\n\s+segname __TEXT\n\s+addr 0x([0-9a-f]+)\n\s+size 0x([0-9a-f]+)\n\s+offset (\d+)", o)
tv, tsz, toff = int(m[1], 16), int(m[2], 16), int(m[3])
W = struct.unpack_from(f"<{tsz//4}I", d, toff)
S = [int(l, 16) + 0x100000000 for l in open("notes/fstarts.txt")] + [tv + tsz]
for k in range(len(S) - 1):
    n = (S[k+1] - S[k]) // 4
    if n not in sizes: continue
    ws = W[(S[k] - tv)//4:(S[k+1] - tv)//4]
    imms = set()
    for w in ws:
        if w & 0xFFC00000 == 0xF9000000: imms.add((w >> 10) & 0xFFF)          # str xt,[xn,#imm*8]
        elif w & 0xFFC00000 == 0xA9000000: imms.add((w >> 15) & 0x7F); imms.add(((w >> 15) & 0x7F) + 1)  # stp
    if 30 in imms and 31 in imms:
        print(hex(S[k] - 0x100000000), n, sum(1 for w in ws if w & 0xFC000000 == 0x94000000))
