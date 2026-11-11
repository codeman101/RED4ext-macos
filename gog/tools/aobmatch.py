# Match Steam functions to GOG ones by normalised instruction shape (relocation-sensitive operands masked).
# usage: aobmatch.py <steam_bin> <gog_bin> 0xSTEAMOFF [...]   (read-only analysis, nothing is executed)
import struct, sys, bisect, collections

def load(path):
    d = open(path, "rb").read()
    ncmds = struct.unpack_from("<I", d, 16)[0]
    p = 32; tv = fs = text = None
    for _ in range(ncmds):
        cmd, sz = struct.unpack_from("<II", d, p)
        if cmd == 0x19:
            nm = d[p+8:p+24].rstrip(b"\0")
            if nm == b"__TEXT":
                tv = struct.unpack_from("<Q", d, p+24)[0]
                nsec = struct.unpack_from("<I", d, p+64)[0]
                q = p + 72
                for _ in range(nsec):
                    sn = d[q:q+16].rstrip(b"\0")
                    if sn == b"__text":
                        text = struct.unpack_from("<QQI", d, q+32)  # addr, size, offset
                    q += 80
        if cmd == 0x26: fs = struct.unpack_from("<II", d, p+8)
        p += sz
    off, size = fs; a = tv; i = off; S = []
    while i < off + size:
        v = 0; sh = 0
        while True:
            c = d[i]; i += 1; v |= (c & 0x7F) << sh; sh += 7
            if not c & 0x80: break
        if v == 0: break
        a += v; S.append(a)
    ta, ts, to = text
    W = struct.unpack_from("<%dI" % (ts // 4), d, to)
    S = [x for x in S if ta <= x < ta + ts]; S.append(ta + ts)
    return tv, ta, W, S

def norm(w):
    t = w & 0xFC000000
    if t in (0x14000000, 0x94000000): return w & 0xFC000000
    if w & 0xFF000010 == 0x54000000: return w & 0xFF00001F
    if w & 0x7E000000 == 0x34000000: return w & 0xFF00001F
    if w & 0x7E000000 == 0x36000000: return w & 0xFFF8001F
    if w & 0x1F000000 == 0x10000000: return w & 0x9F00001F
    if w & 0x3B000000 == 0x18000000: return w & 0xFF00001F
    if w & 0xFF800000 == 0x91000000: return w & 0xFF8003FF
    return w

def shape(w):  # register-free token
    return norm(w) & ~0x3FF

def fn_words(W, ta, S, a):
    k = bisect.bisect_left(S, a)
    assert S[k] == a, hex(a)
    return W[(a - ta)//4:(S[k+1] - ta)//4]

def grams(ws, n=3):
    t = [shape(w) for w in ws]
    return set(tuple(t[i:i+n]) for i in range(len(t) - n + 1))

st = load(sys.argv[1]); gg = load(sys.argv[2])
gS = gg[3]
glen = [(gS[i+1] - gS[i]) // 4 for i in range(len(gS) - 1)]
byl = collections.defaultdict(list)
for i, l in enumerate(glen): byl[l].append(i)
for arg in sys.argv[3:]:
    a = int(arg, 16) + 0x100000000
    try: sw = fn_words(st[2], st[1], st[3], a)
    except AssertionError: print(arg, "not a Steam function start"); continue
    n = len(sw); sg = grams(sw); sx = [norm(w) for w in sw]
    best = []
    lo, hi = int(n * 0.7), int(n * 1.4) + 2
    for l in range(max(lo, 4), hi):
        for i in byl.get(l, ()):
            gw = gg[2][(gS[i] - gg[1])//4:(gS[i+1] - gg[1])//4]
            g2 = grams(gw)
            u = len(sg | g2) or 1
            j = len(sg & g2) / u
            if j > 0.25: best.append((j, i, l))
    best.sort(reverse=True)
    print(arg, "steam insns", n, "|", " ".join("%#x j=%.2f n=%d%s" % (gS[i] - 0x100000000, j, l, " EXACT" if [norm(w) for w in gg[2][(gS[i]-gg[1])//4:(gS[i+1]-gg[1])//4]] == sx else "") for j, i, l in best[:4]))
