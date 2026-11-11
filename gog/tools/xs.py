import re, struct, subprocess, sys
binp, *names = sys.argv[1:]
d = open(binp, "rb").read()
o = subprocess.run(["otool", "-l", binp], capture_output=True, text=True).stdout
m = re.search(r"sectname __text\n\s+segname __TEXT\n\s+addr 0x([0-9a-f]+)\n\s+size 0x([0-9a-f]+)\n\s+offset (\d+)", o)
tv, tsz, toff = int(m.group(1), 16), int(m.group(2), 16), int(m.group(3))
words = struct.unpack_from(f"<{tsz // 4}I", d, toff)
strs = {}
for n in names:
    for mm in re.finditer(re.escape(n.encode()) + b"\0", d):
        if mm.start() == 0 or d[mm.start() - 1] == 0:  # whole string
            strs[0x100000000 + mm.start()] = n
print("strings:", {hex(k): v for k, v in strs.items()})
pages = {a & ~0xFFF: a for a in strs}
hits = {}
for i, w in enumerate(words):
    if (w & 0x9F000000) != 0x90000000: continue
    pc = tv + 4 * i
    imm = ((w >> 29) & 3) | (((w >> 5) & 0x7FFFF) << 2)
    page = (pc & ~0xFFF) + ((imm - (1 << 21) if imm & (1 << 20) else imm) << 12)
    if page not in pages: continue
    rd = w & 31
    for n in words[i + 1:i + 4]:
        if ((n >> 5) & 31) == rd and (n & 0xFFC00000) == 0x91000000:
            full = page + ((n >> 10) & 0xFFF)
            if full in strs: hits.setdefault(strs[full], []).append(hex(pc))
            break
for k, v in hits.items(): print(k, v)
