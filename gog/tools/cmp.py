import json, subprocess, sys
db, binp = sys.argv[1], sys.argv[2]
syms = {}
for l in subprocess.run(["nm", "-n", binp], capture_output=True, text=True).stdout.splitlines():
    p = l.split(None, 2)
    if len(p) == 3 and p[1] in "tT":
        syms.setdefault(int(p[0], 16), p[2])
rows = [a for a in json.load(open(db))["Addresses"] if a.get("verified")]
hit = [a for a in rows if 0x100000000 + int(a["offset"].split(":")[1], 16) in syms]
print("verified:", len(rows), "symbol exactly at offset:", len(hit), f"({100*len(hit)//len(rows)}%)")
print("total text symbols:", len(syms))
for a in hit[:8]:
    print(a["offset"], syms[0x100000000 + int(a["offset"].split(":")[1], 16)][:90])
