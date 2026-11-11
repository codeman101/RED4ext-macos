# exact function starts from LC_FUNCTION_STARTS. usage: fstarts.py <bin>  -> prints hex offsets (from image base) one per line
import struct, sys
d = open(sys.argv[1], "rb").read()
ncmds = struct.unpack_from("<I", d, 16)[0]
p = 32; tv = None; fs = None
for _ in range(ncmds):
    cmd, sz = struct.unpack_from("<II", d, p)
    if cmd == 0x19 and d[p+8:p+14] == b"__TEXT": tv = struct.unpack_from("<Q", d, p+24)[0]
    if cmd == 0x26: fs = struct.unpack_from("<II", d, p+8)
    p += sz
off, size = fs
a = tv; i = off
while i < off + size:
    v = 0; sh = 0
    while True:
        c = d[i]; i += 1; v |= (c & 0x7F) << sh; sh += 7
        if not c & 0x80: break
    if v == 0: break
    a += v; print(hex(a - 0x100000000))
