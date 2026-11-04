# bp on ink RTTI wrappers (no callback); when hit, single-step N instrs from main script, log pcs of new functions.
import lldb,os,time,bisect
G=os.path.expanduser("~/cyberpunk-gog-port/dbg/game")
BIN=G+"/Cyberpunk2077.app/Contents/MacOS/Cyberpunk2077"
FS=sorted(int(l.split()[0],16) for l in open(os.path.expanduser('~/RED4ext-macos/gog/notes/fstarts.txt')) if l.strip())
def fn(pc):
    i=bisect.bisect_right(FS,pc)-1;return FS[i]
def run(d,c,r,i):
    d.SetAsync(True)
    t=d.CreateTarget(BIN);li=lldb.SBLaunchInfo([])
    li.SetEnvironmentEntries(["DYLD_INSERT_LIBRARIES="+G+"/red4ext/RED4ext.dylib"],True)
    li.SetWorkingDirectory(G);li.SetLaunchFlags(lldb.eLaunchFlagDisableASLR|lldb.eLaunchFlagStopAtEntry)
    e=lldb.SBError();p=t.Launch(li,e)
    if not e.Success(): print(e);return
    bps=[t.BreakpointCreateByAddress(0x100000000+int(x,16)) for x in os.environ['BP'].split(',')]
    p.Continue();t0=time.time();nh=0
    while time.time()-t0<int(os.environ.get("PW","900")):
        time.sleep(0.5)
        if p.GetState()==lldb.eStateExited: print('EXITED');return
        if p.GetState()!=lldb.eStateStopped: continue
        th=p.GetSelectedThread()
        if th.GetStopReason()!=lldb.eStopReasonBreakpoint: p.Continue();continue
        time.sleep(1)
        pc=th.GetFrameAtIndex(0).GetPC()-0x100000000
        h0=pc;print('HIT',hex(pc),flush=True)
        d.SetAsync(False)
        seen=[];last=None;N=int(os.environ.get('N','5000'))
        for k in range(N):
            th.StepInstruction(False)
            pc=th.GetFrameAtIndex(0).GetPC()-0x100000000
            f=fn(pc)
            if f!=last:
                last=f
                if f not in [s[0] for s in seen]: seen.append((f,k))
            if p.GetState()!=lldb.eStateStopped: break
        print('FUNCS',hex(h0),[(hex(a),b) for a,b in seen],flush=True)
        d.SetAsync(True);nh+=1
        if nh>=int(os.environ.get('NH','30')): p.Kill();return
        p.Continue();continue
    print('TIMEOUT');p.Kill()
def __lldb_init_module(d,_):
    d.HandleCommand("command script add -f step.run cpg_step")
