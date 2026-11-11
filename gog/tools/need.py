import json, re, struct, subprocess, sys, collections
root, tsv = sys.argv[1], sys.argv[2]
db = json.load(open(f"{root}/red4ext/bin/x64/cyberpunk2077_addresses.json"))["Addresses"]
byhash = {int(a["hash"]): a for a in db}
meta = {}
for l in open(tsv).read().splitlines()[1:]:
    c = l.split("\t")
    meta[int(c[0])] = (c[1], c[4], c[7] if len(c) > 7 else "")
def imms(path):
    out = subprocess.run(["otool", "-l", path], capture_output=True, text=True).stdout
    m = re.search(r"sectname __text\n.*?size 0x([0-9a-f]+)\n\s+offset (\d+)", out, re.S)
    size, off = int(m.group(1), 16), int(m.group(2))
    d = open(path, "rb").read()[off:off + size]
    s, pend = set(), {}
    for i in range(0, len(d) - 3, 4):
        w = struct.unpack_from("<I", d, i)[0]; rd = w & 31; imm = (w >> 5) & 0xFFFF; hw = (w >> 21) & 3
        k = w & 0x7F800000
        if k == 0x52800000 and hw == 0: pend[rd] = imm; s.add(imm)
        elif k == 0x72800000 and hw == 1 and rd in pend: s.add(pend.pop(rd) | (imm << 16))
    return s
targets = {"RED4ext": f"{root}/red4ext/RED4ext.dylib"}
for p in ("ArchiveXL", "TweakXL", "Codeware"): targets[p] = f"{root}/red4ext/plugins/{p}/{p}.dylib"
for n, p in targets.items():
    need = {h for h in imms(p) if h in byhash}
    meths = collections.Counter(meta.get(h, ("?", "?"))[1] for h in need)
    ver = sum(1 for h in need if byhash[h].get("verified"))
    print(f"{n}: {len(need)} address hashes ({ver} verified)  by method: {dict(meths)}")
if len(sys.argv) > 3:
    need = sorted(h for h in imms(targets[sys.argv[3]]) if h in byhash)
    for h in need:
        n, m, note = meta.get(h, ("?", "?", ""))
        print(f"\n{h}\t{n}\t{byhash[h]['offset']}\t{m}\tverified={byhash[h].get('verified', False)}\n   {note[:420]}")
