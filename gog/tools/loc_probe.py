# Hit probe: BP=hex,hex image offsets; prints each hit with caller offset and x0..x3. usage: BP=... PW=90 lldb -b -o "command script import loc.py" -o "cpg_loc"
import lldb,os,time
G=os.path.expanduser("~/cyberpunk-gog-port/dbg/game")
BIN=G+"/Cyberpunk2077.app/Contents/MacOS/Cyberpunk2077"
N={}
HS=[int(x,16) for x in os.environ.get("HASH","").split(",") if x]
def cb(f,bp,ex,i):
    a=bp.GetLoadAddress()-0x100000000;N[a]=N.get(a,0)+1
    if HS:
        pr=f.GetThread().GetProcess();e=lldb.SBError();hit=[]
        for r in range(8):
            v=f.FindRegister("x%d"%r).GetValueAsUnsigned()
            if v in HS: hit.append("x%d"%r)
            elif v>0x10000:
                for o in (0,8,0x10,0x18):
                    w=pr.ReadUnsignedFromMemory(v+o,8,e)
                    if e.Success() and w in HS: hit.append("x%d+%x"%(r,o))
        if hit:
            th=f.GetThread();print("HASHHIT",hex(a),hit,"FR"," ".join(hex(th.frames[j].GetPC()-0x100000000) for j in range(1,min(12,th.GetNumFrames()))),flush=True)
        return False
    if N[a]<=4: print("LOCHIT",hex(a),"lr",hex(f.FindRegister("x30").GetValueAsUnsigned()-0x100000000),[hex(f.FindRegister("x%d"%r).GetValueAsUnsigned()) for r in range(4)],flush=True)
    return False
def run(d,c,r,i):
    d.SetAsync(True)
    t=d.CreateTarget(BIN);li=lldb.SBLaunchInfo([])
    li.SetEnvironmentEntries(["DYLD_INSERT_LIBRARIES="+G+"/red4ext/RED4ext.dylib"],True)
    li.SetWorkingDirectory(G);li.SetLaunchFlags(lldb.eLaunchFlagDisableASLR|lldb.eLaunchFlagStopAtEntry)
    e=lldb.SBError();p=t.Launch(li,e)
    if not e.Success(): print(e);return
    for x in [v for v in os.environ.get("BP","").split(",") if v]:
        b=t.BreakpointCreateByAddress(0x100000000+int(x,16));b.SetScriptCallbackFunction("loc.cb")
    p.Continue()
    t0=time.time()
    while time.time()-t0<int(os.environ.get("PW","90")):
        time.sleep(1)
        if p.GetState()==lldb.eStateExited: print("EXITED",flush=True);return
    print("COUNTS",{hex(k):v for k,v in N.items()},flush=True)
    p.Kill()
def __lldb_init_module(d,_):
    d.HandleCommand("command script add -f loc.run cpg_loc")
