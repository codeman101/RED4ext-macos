# Interactive run with RED4ext injected through lldb (no breakpoints). On crash prints the stop reason and backtrace, then kills.
# usage: lldb -b -o "command script import play.py" -o "cpg_play"   (env PW = max seconds, default 900)
import lldb,os,time
G=os.path.expanduser("~/cyberpunk-gog-port/dbg/game")
HITS={}
def cb(f,bp,ex,i):
    a=bp.GetLoadAddress()-0x100000000;HITS[a]=HITS.get(a,0)+1;return False
BIN=G+"/Cyberpunk2077.app/Contents/MacOS/Cyberpunk2077"
def run(d,c,r,i):
    d.SetAsync(True)
    t=d.CreateTarget(BIN);li=lldb.SBLaunchInfo([])
    li.SetEnvironmentEntries(["DYLD_INSERT_LIBRARIES="+G+"/red4ext/RED4ext.dylib"],True)
    li.SetWorkingDirectory(G);li.SetLaunchFlags(lldb.eLaunchFlagDisableASLR|lldb.eLaunchFlagStopAtEntry)
    e=lldb.SBError();p=t.Launch(li,e)
    if not e.Success(): print(e);return
    for x in [v for v in os.environ.get('BP','').split(',') if v]:
        b=t.BreakpointCreateByAddress(0x100000000+int(x,16));b.SetScriptCallbackFunction('play.cb')
    p.Continue()
    for _ in range(100):
        if p.GetState()==lldb.eStateRunning: break
        time.sleep(0.1)
    time.sleep(2)
    t0=time.time()
    while time.time()-t0<int(os.environ.get("PW","900")):
        time.sleep(1)
        s=p.GetState()
        if s==lldb.eStateExited: print("EXITED",p.GetExitStatus(),flush=True);return
        if s==lldb.eStateStopped:
            th=p.GetSelectedThread()
            if 'SIGSTOP' in th.GetStopDescription(200) and th.frames[0].GetModule().GetFileSpec().GetFilename()=='dyld':
                p.Continue();continue
            if th.GetStopDescription(200).strip()=='' or th.GetStopReason()==lldb.eStopReasonNone: p.Continue();continue
            print("STOPPED",th.GetStopDescription(200),flush=True)
            for f in th.frames[:12]: print(" ",f,flush=True)
            fr=th.frames[0]
            lr=fr.FindRegister('lr').GetValueAsUnsigned(); print("  LR",hex(lr),p.GetTarget().ResolveLoadAddress(lr),flush=True)
            sp=fr.FindRegister('sp').GetValueAsUnsigned(); err=lldb.SBError()
            for k in range(0,48):
                v=p.ReadUnsignedFromMemory(sp+8*k,8,err)
                a=p.GetTarget().ResolveLoadAddress(v)
                if a.GetModule().IsValid() and a.GetSection().IsValid() and 'TEXT' in a.GetSection().GetName()+a.GetSection().GetParent().GetName() if a.GetSection().IsValid() and a.GetSection().GetParent().IsValid() else False: print("  stk",k,hex(v),a,flush=True)
            p.Kill();return
    print("TIMEOUT",{hex(k):v for k,v in HITS.items()},flush=True);p.Kill()
def __lldb_init_module(d,_):
    d.HandleCommand("command script add -f play.run cpg_play")
