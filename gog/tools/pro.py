import json, struct, sys, random
db, binp = sys.argv[1], sys.argv[2]
data = open(binp, "rb").read()
rows = [int(a["offset"].split(":")[1], 16) for a in json.load(open(db))["Addresses"] if a.get("verified")]
def prologue(o):
    if o + 4 > len(data): return False
    w = struct.unpack_from("<I", data, o)[0]
    return (w == 0xd503237f                     # pacibsp
        or (w & 0xffc003e0) == 0xa98003e0 and ((w >> 10) & 0x1f) == 30   # stp xN,x30,[sp,#-i]!
        or (w & 0xffc003ff) == 0xd10003ff       # sub sp,sp,#imm
        or (w & 0xffc07fff) == 0xa9007bfd)      # stp x29,x30,[sp,#i]
n = sum(prologue(o) for o in rows)
random.seed(1)
base = [random.randrange(0x100000, max(rows)) & ~3 for _ in range(5000)]
b = sum(prologue(o) for o in base)
print(f"table offsets at a prologue: {n}/{len(rows)} ({100*n//len(rows)}%)")
print(f"random aligned offsets at a prologue: {b}/5000 ({100*b//5000}%)")
