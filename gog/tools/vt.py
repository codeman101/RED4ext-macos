import re, bisect, collections, sys
syms=[]
for l in open('gog_nm.txt'):
    p=l.split(None,2)
    if len(p)<3 or p[1] not in 'tTsS': continue
    syms.append((int(p[0],16)-0x100000000,p[2].strip()))
syms.sort(); addrs=[s[0] for s in syms]
def sym(o):
    i=bisect.bisect_right(addrs,o)-1
    return syms[i][1] if i>=0 else '?'
def cls(name):
    m=re.match(r'__ZN(?:K)?(\d+)(.*)',name)
    if not m: return None
    n=int(m.group(1)); return m.group(2)[:n]
rows=[]
for l in open('probe/probe2.log'):
    if not l.startswith('G '): continue
    t=l.split()
    g=int(t[1],16); vt=int(t[3][3:],16)
    es=[int(x,16) for x in t[5:]]
    cs=[cls(sym(e)) for e in es if e]
    c=collections.Counter(x for x in cs if x).most_common(1)
    rows.append((g,vt,c[0][0] if c else None,[sym(e) for e in es if e][:2]))
byc=collections.defaultdict(list)
for g,vt,c,s in rows: byc[c].append((g,vt,s))
print(len(rows),'rows',len(byc),'classes; unresolved',len(byc[None]))
pat=re.compile(sys.argv[1],re.I) if len(sys.argv)>1 else None
for c,v in sorted(byc.items(),key=lambda x:-len(x[1])):
    if c and (not pat or pat.search(c)):
        print(c,len(v),' '.join('g=%#x/vt=%#x'%(a,b) for a,b,_ in v[:3]))
