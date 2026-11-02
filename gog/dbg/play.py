# Interactive run with RED4ext injected through lldb (no breakpoints). On crash prints the stop reason and backtrace, then kills.
# usage: lldb -b -o "command script import play.py" -o "cpg_play"   (env PW = max seconds, default 900)
import lldb,os,time
G=os.path.expanduser("~/cyberpunk-gog-port/dbg/game")
BIN=G+"/Cyberpunk2077.app/Contents/MacOS/Cyberpunk2077"
def run(d,c,r,i):
    d.SetAsync(True)
    t=d.CreateTarget(BIN);li=lldb.SBLaunchInfo([])
    li.SetEnvironmentEntries(["DYLD_INSERT_LIBRARIES="+G+"/red4ext/RED4ext.dylib"],True)
    li.SetWorkingDirectory(G);li.SetLaunchFlags(lldb.eLaunchFlagDisableASLR|lldb.eLaunchFlagStopAtEntry)
    e=lldb.SBError();p=t.Launch(li,e)
    if not e.Success(): print(e);return
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
            print("STOPPED",th.GetStopDescription(200),flush=True)
            for f in th.frames[:12]: print(" ",f,flush=True)
            p.Kill();return
    print("TIMEOUT",flush=True);p.Kill()
def __lldb_init_module(d,_):
    d.HandleCommand("command script add -f play.run cpg_play")
