# bp at handler entries (set time window) + blr sites; print blr target offsets seen inside window. callbacks only read regs.
import lldb,os,time
G=os.path.expanduser("~/cyberpunk-gog-port/dbg/game");BIN=G+"/Cyberpunk2077.app/Contents/MacOS/Cyberpunk2077"
W={'t':0,'h':0};SEEN={}
def cb(f,bp,ex,i):
    a=bp.GetLoadAddress()-0x100000000;t=time.time()
    if a in (0x133cec0,0x133d45c,0x133cc48,0x133d184): W['t']=t;W['h']=a;return False
    if t-W['t']>0.5: return False
    reg=os.environ.get('REG','x8');v=f.FindRegister(reg).GetValueAsUnsigned()-0x100000000
    k=(hex(W['h']),hex(a),hex(v))
    if k not in SEEN: SEEN[k]=1;print('BLR',*k,'x0',hex(f.FindRegister('x0').GetValueAsUnsigned()),flush=True)
    return False
def run(d,c,r,i):
    d.SetAsync(True);t=d.CreateTarget(BIN);li=lldb.SBLaunchInfo([])
    li.SetEnvironmentEntries(["DYLD_INSERT_LIBRARIES="+G+"/red4ext/RED4ext.dylib"],True)
    li.SetWorkingDirectory(G);li.SetLaunchFlags(lldb.eLaunchFlagDisableASLR|lldb.eLaunchFlagStopAtEntry)
    e=lldb.SBError();p=t.Launch(li,e)
    if not e.Success(): print(e);return
    for x in os.environ['BP'].split(','):
        b=t.BreakpointCreateByAddress(0x100000000+int(x,16));b.SetScriptCallbackFunction('blr.cb')
    p.Continue();t0=time.time()
    while time.time()-t0<int(os.environ.get('PW','900')):
        time.sleep(1);s=p.GetState()
        if s==lldb.eStateExited: print('EXITED');return
        if s==lldb.eStateStopped:
            th=p.GetSelectedThread()
            if th.GetStopReason()==lldb.eStopReasonBreakpoint or th.GetStopReason()==lldb.eStopReasonNone or 'SIGSTOP' in th.GetStopDescription(100): p.Continue();continue
            print('STOPPED',th.GetStopDescription(100),flush=True);p.Kill();return
    p.Kill()
def __lldb_init_module(d,_): d.HandleCommand("command script add -f blr.run cpg_blr")
