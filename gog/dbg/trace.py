import lldb,os,time,json
HOME=os.path.expanduser("~/cyberpunk-gog-port")
G=HOME+"/dbg/game"
BIN=G+"/Cyberpunk2077.app/Contents/MacOS/Cyberpunk2077"
LOG=[]; CNT={}; ENG=set()
def cb(frame,bp,ex,i):
    try:
        a=frame.GetPC(); k=bp.GetID()
        CNT[k]=CNT.get(k,0)+1
        pr=frame.GetThread().GetProcess();er=lldb.SBError()
        eng=pr.ReadPointerFromMemory(0x100000000+0x7D34000+0x1FEF9A8,er)
        if frame.FindRegister("x0").GetValueAsUnsigned()==eng and eng: ENG.add(k)
        if CNT[k]<=3:
            LOG.append((time.time(),k,frame.FindRegister("x0").GetValueAsUnsigned(),frame.FindRegister("x1").GetValueAsUnsigned(),frame.FindRegister("x30").GetValueAsUnsigned()))
        else: bp.SetEnabled(False)
    except Exception as e: print("CBERR",e,flush=True)
    return False
def run(d,c,r,i):
    files=os.environ.get("CPG_CANDS","").split(",")
    wait=int(os.environ.get("CPG_WAIT","80"))
    d.SetAsync(True)
    t=d.CreateTarget(BIN);li=lldb.SBLaunchInfo([])
    li.SetWorkingDirectory(G)
    li.SetLaunchFlags(lldb.eLaunchFlagDisableASLR|lldb.eLaunchFlagStopAtEntry)
    e=lldb.SBError();p=t.Launch(li,e)
    if not e.Success(): print(e);return
    for _ in range(100):
        if p.GetState()==lldb.eStateStopped: break
        time.sleep(0.2)
    base=[m for m in t.module_iter() if "MacOS/Cyberpunk2077" in str(m.GetFileSpec())][0].GetObjectFileHeaderAddress().GetLoadAddress(t)
    names={}
    for f in files:
        for l in open(f):
            o=int(l.split()[0],16);b=t.BreakpointCreateByAddress(base+o);b.SetScriptCallbackFunction("trace.cb");names[b.GetID()]=(os.path.basename(f),o)
    print("bps",len(names),"base",hex(base),flush=True)
    t0=time.time();p.Continue()
    while time.time()-t0<wait and p.GetState() in (lldb.eStateRunning,lldb.eStateStepping): time.sleep(1)
    st=p.GetState();print("state",st,flush=True)
    if st==lldb.eStateStopped:
        th=p.GetSelectedThread();print("STOP",th.GetStopReason(),th.GetStopDescription(200),hex(th.GetFrameAtIndex(0).GetPC()-base),flush=True)
    er=lldb.SBError();print("ENGPTR",hex(p.ReadPointerFromMemory(base+0x7D34000+0x1FEF9A8,er)),er.Success(),flush=True)
    print('ENGHITS',[hex(names[a][1]) for a in ENG],'CNT',{hex(names[a][1]):n for a,n in CNT.items()},flush=True)
    try:
        if st==lldb.eStateRunning: p.SendAsyncInterrupt();time.sleep(2)
    except Exception as e: print('ERR',e)
    for ts,a,x0,x1,lr in LOG:
        f,o=names[a];print("HIT %s 0x%x t+%.1f x0=%x x1=%x lr=%x"%(f,o,ts-t0,x0,x1,lr-base),flush=True)
    print("ENGHITS",[hex(names[a][1]) for a in ENG],flush=True)
    print("counts",{hex(names[a][1]):n for a,n in CNT.items() if n>3},flush=True)
    p.Kill()
def __lldb_init_module(d,i): d.HandleCommand("command script add -f trace.run cpg_trace")
