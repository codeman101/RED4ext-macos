import lldb,os,time
HOME=os.path.expanduser("~/cyberpunk-gog-port")
G=HOME+"/dbg/game"
BIN=G+"/Cyberpunk2077.app/Contents/MacOS/Cyberpunk2077"
hits=[]
ST={}
def cb_open(frame,bp,ex,i):
    pr=frame.GetThread().GetProcess();t=pr.GetTarget()
    er=lldb.SBError();s=pr.ReadCStringFromMemory(frame.FindRegister("x0").GetValueAsUnsigned(),300,er)
    print("DLOPEN",s,flush=True)
    if er.Success() and "TweakXL.dylib" in s:
        lr=frame.FindRegister("x30").GetValueAsUnsigned()
        b=t.BreakpointCreateByAddress(lr);b.SetOneShot(True);b.SetScriptCallbackFunction("crash.cb_ret")
    return False
NAMES={0x32380:"main",0x41B2858:"RTTI_Get",0x1E37C3C:"Init",0x3418744:"Load",0x3420770:"TryLoad",0x2F5439C:"CreateRecord",0x3416FE8:"TweakDB_Get",0x2CC8C:"ctor_str",0x2931C:"ctor_span",0x2AA54:"copy",0x2912C:"dtor",0x28654:"Realloc",0xF81AF4:"CNameGet",0xF81B84:"AddCstr",0xF81B2C:"AddPair",0x4128D70:"DecWeak",0x41C1984:"CreateInst",0x4199490:"InternalExec",0x4198494:"ExecScripted",0x4128C34:"Handle_ctor"}
def cbn(frame,bp,ex,i):
    try: return cbn2(frame,bp,ex,i)
    except Exception as e: print('CBNERR',e,flush=True);return False
def cbn2(frame,bp,ex,i):
    pc=frame.GetPC();ST.setdefault("seq",[]).append((pc,frame.FindRegister("x30").GetValueAsUnsigned()))
    return False
def cbg(frame,bp,ex,i):
    lr=frame.FindRegister("x30").GetValueAsUnsigned()
    t=frame.GetThread().GetProcess().GetTarget();m=t.ResolveLoadAddress(lr).GetModule().GetFileSpec().GetFilename()
    
    if m!="Cyberpunk2077": print("RTTIGET from",m,hex(lr),"x0ret?",flush=True)
    return False
def cb_fp(frame,bp,ex,i):
    try: return cb_fp2(frame,bp,ex,i)
    except Exception as e: print('CBERR',e,flush=True);return False
def cb_fp2(frame,bp,ex,i):
    ST['n']=ST.get('n',0)+1
    t=frame.GetThread().GetProcess().GetTarget()
    if "tw" in ST: return False
    for m in t.module_iter():
        if "TweakXL.dylib" in str(m.GetFileSpec()):
            ST["tw"]=m.GetObjectFileHeaderAddress().GetLoadAddress(t)
            bb=t.BreakpointCreateByAddress(ST["tw"]+0xa1664);bb.SetOneShot(True)
            bp.SetEnabled(False)
    return False
def cb_ret(frame,bp,ex,i):
    t=frame.GetThread().GetProcess().GetTarget()
    for m in t.module_iter():
        if "TweakXL.dylib" in str(m.GetFileSpec()):
            ST["tw"]=m.GetObjectFileHeaderAddress().GetLoadAddress(t)
            bb=t.BreakpointCreateByAddress(ST["tw"]+0xa1664);bb.SetOneShot(True)
            ST["bb"]=1
    return False
def cb(frame,bp,ex,i):
    hits.append((frame.FindRegister("x0").GetValueAsUnsigned(),frame.FindRegister("x1").GetValueAsUnsigned()));return False
def run(d,c,r,i):
    d.SetAsync(False)
    t=d.CreateTarget(BIN);li=lldb.SBLaunchInfo([])
    li.SetEnvironmentEntries(["DYLD_INSERT_LIBRARIES="+G+"/red4ext/RED4ext.dylib"]+[x for x in os.environ.get("CPG_ENV","").split() if x],True)
    li.SetWorkingDirectory(G)
    li.SetLaunchFlags(lldb.eLaunchFlagDisableASLR|lldb.eLaunchFlagStopAtEntry)
    e=lldb.SBError();p=t.Launch(li,e)
    if not e.Success(): print(e);return
    base=[m for m in t.module_iter() if "MacOS/Cyberpunk2077" in str(m.GetFileSpec())][0].GetObjectFileHeaderAddress().GetLoadAddress(t)
    bo=t.BreakpointCreateByName("dlopen");bo.SetScriptCallbackFunction("crash.cb_open")
    tw=None
    bo=t.BreakpointCreateByName('fprintf');bo.SetScriptCallbackFunction('crash.cb_fp')
    p.Continue()
    th=p.GetSelectedThread();tw=ST.get("tw");print("TW",tw,flush=True)
    if tw and os.environ.get("CPG_NOSTEP"):
        t.DeleteAllBreakpoints();p.Continue()
    elif tw:
        for n in range(60):
            f=th.GetFrameAtIndex(0);pc=f.GetPC()
            ins=t.ReadInstructions(f.GetPCAddress(),1)[0]
            print("S",n,hex(pc-base) if base<=pc<base+0x8000000 else hex(pc-tw)+"tw",ins.GetMnemonic(t),ins.GetOperands(t),"x0=",hex(f.FindRegister("x0").GetValueAsUnsigned()),flush=True)
            th.StepInstruction(False)
            if th.GetStopReason()==lldb.eStopReasonException or p.GetState()!=lldb.eStateStopped: break
    print("getcalls",len(ST.get("g",[])),[x for x in ST.get("g",[]) if x[0]!="Cyberpunk2077"][:5])
    tw=ST.get('tw')
    th=p.GetSelectedThread()
    pc=th.GetFrameAtIndex(0).GetPC()
    print("at",hex(pc-(tw or 0)))
    if tw and pc==tw+0xa1664:
        for n in range(120):
            f=th.GetFrameAtIndex(0);pc=f.GetPC()
            ins=t.ReadInstructions(f.GetPCAddress(),1)[0]
            print("S",n,hex(pc-tw) if tw<=pc<tw+0x200000 else hex(pc),ins.GetMnemonic(t),ins.GetOperands(t))
            th.StepInstruction(True)
            if p.GetState()!=lldb.eStateStopped: break
            if th.GetStopReason()==lldb.eStopReasonException: break
    th=p.GetSelectedThread();print("state",p.GetState(),"stop",th.GetStopDescription(200),"hits25",hits)
    for k in range(0,10):
        f=th.GetFrameAtIndex(k);print(k,hex(f.GetPC()),hex(f.GetPC()-base),f.GetModule().GetFileSpec().GetFilename(),f.GetFunctionName())
    f=th.GetFrameAtIndex(0)
    print({n:hex(f.FindRegister(n).GetValueAsUnsigned()) for n in ["x0","x1","x8","x19","x20","x29","x30","sp","pc"]})
    sp=f.FindRegister("sp").GetValueAsUnsigned();er=lldb.SBError()
    for k in range(0,0x600,8):
        v=p.ReadPointerFromMemory(sp+k,er)
        a=t.ResolveLoadAddress(v)
        m=a.GetModule()
        if m.IsValid() and m.GetFileSpec().GetFilename()!="Cyberpunk2077" or (m.IsValid() and 0<v-base<0x7800000 and (v&3)==0):
            sy=a.GetSymbol();print("stk+%#x"%k,m.GetFileSpec().GetFilename(),hex(v-m.GetObjectFileHeaderAddress().GetLoadAddress(t)),sy.GetName() if sy.IsValid() else "")
    for m in t.module_iter():
        if "TweakXL.dylib" in str(m.GetFileSpec()):
            tb=m.GetObjectFileHeaderAddress().GetLoadAddress(t);er=lldb.SBError()
            print("ALLOCHASH",p.ReadUnsignedFromMemory(tb+0x148b48,4,er),hex(p.ReadUnsignedFromMemory(tb+0x148b50,8,er)))
    p.Kill()
def __lldb_init_module(d,i): d.HandleCommand("command script add -f crash.run cpg_crash")
