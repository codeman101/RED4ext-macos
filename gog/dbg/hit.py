import lldb,os,time
G=os.path.expanduser("~/cyberpunk-gog-port/dbg/game")
BIN=G+"/Cyberpunk2077.app/Contents/MacOS/Cyberpunk2077"
ST={"n":0,"bp":0}
def cb_hit(f,bp,ex,i):
    ST["n"]+=1;print("AXLHIT",ST["n"],flush=True);return False
def cb_ret(f,bp,ex,i):
    t=f.GetThread().GetProcess().GetTarget()
    for m in t.module_iter():
        if "ArchiveXL.dylib" in str(m.GetFileSpec()):
            b=m.GetObjectFileHeaderAddress().GetLoadAddress(t)
            x=t.BreakpointCreateByAddress(b+0x68f78);x.SetScriptCallbackFunction("hit.cb_hit");ST["bp"]=1
            print("AXLBP set",hex(b+0x68f78),flush=True)
    return False
def cb_open(f,bp,ex,i):
    pr=f.GetThread().GetProcess();t=pr.GetTarget();er=lldb.SBError()
    s=pr.ReadCStringFromMemory(f.FindRegister("x0").GetValueAsUnsigned(),300,er)
    if er.Success() and "ArchiveXL.dylib" in s:
        b=t.BreakpointCreateByAddress(f.FindRegister("x30").GetValueAsUnsigned());b.SetOneShot(True);b.SetScriptCallbackFunction("hit.cb_ret")
    return False
def run(d,c,r,i):
    d.SetAsync(True)
    t=d.CreateTarget(BIN);li=lldb.SBLaunchInfo([])
    li.SetEnvironmentEntries(["DYLD_INSERT_LIBRARIES="+G+"/red4ext/RED4ext.dylib"],True)
    li.SetWorkingDirectory(G);li.SetLaunchFlags(lldb.eLaunchFlagDisableASLR|lldb.eLaunchFlagStopAtEntry)
    e=lldb.SBError();p=t.Launch(li,e)
    if not e.Success(): print(e);return
    bo=t.BreakpointCreateByName("dlopen");bo.SetScriptCallbackFunction("hit.cb_open")
    p.Continue()
    for _ in range(int(os.environ.get("HW","45"))):
        time.sleep(1)
        if p.GetState() in (lldb.eStateExited,lldb.eStateCrashed): break
    print("FINAL state",p.GetState(),"hits",ST["n"],"bp",ST["bp"],flush=True)
    dump(p,t);dump2(p,t)
    if p.GetState()==lldb.eStateStopped:
        th=p.GetSelectedThread();print("STOPDESC",th.GetStopDescription(200),flush=True)
    p.Kill()
def __lldb_init_module(d,i): d.HandleCommand("command script add -f hit.run cpg_hit")
def dump(p,t):
    er=lldb.SBError()
    base=[m for m in t.module_iter() if "MacOS/Cyberpunk2077" in str(m.GetFileSpec())][0].GetObjectFileHeaderAddress().GetLoadAddress(t)
    ax=[m for m in t.module_iter() if "ArchiveXL.dylib" in str(m.GetFileSpec())][0].GetObjectFileHeaderAddress().GetLoadAddress(t)
    print("DEPOT hash",hex(p.ReadUnsignedFromMemory(ax+0x1a0d98,4,er)),"cache",hex(p.ReadPointerFromMemory(ax+0x1a0da0,er)),"flag",p.ReadUnsignedFromMemory(ax+0x1a0da8,1,er),"gogglobal",hex(p.ReadPointerFromMemory(base+0x934f518,er)),flush=True)

def dump2(p,t):
    er=lldb.SBError()
    base=[m for m in t.module_iter() if "MacOS/Cyberpunk2077" in str(m.GetFileSpec())][0].GetObjectFileHeaderAddress().GetLoadAddress(t)
    d=p.ReadPointerFromMemory(base+0x934f518,er)
    if d: print("DEPOTOBJ vt",hex(p.ReadPointerFromMemory(d,er)),"+0x10",hex(p.ReadPointerFromMemory(d+0x10,er)),"cnt+0x1c",p.ReadUnsignedFromMemory(d+0x1c,4,er),flush=True)
