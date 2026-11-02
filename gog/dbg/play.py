# Interactive run with RED4ext injected through lldb (no breakpoints). On crash prints the stop reason and backtrace, then kills.
# usage: lldb -b -o "command script import play.py" -o "cpg_play"   (env PW = max seconds, default 900)
import lldb,os,time
G=os.path.expanduser("~/cyberpunk-gog-port/dbg/game")
HITS={}
def cb(f,bp,ex,i):
    pr=f.GetThread().GetProcess();a=bp.GetLoadAddress()-0x100000000
    if a==0x42dd9cc:
        e=lldb.SBError();x20=f.FindRegister('x20').GetValueAsUnsigned();vt=pr.ReadUnsignedFromMemory(x20,8,e);fn=pr.ReadUnsignedFromMemory(vt+0x10,8,e);print('SINK',hex(fn-0x100000000),flush=True)
    if a==0x42a2388:
        e=lldb.SBError();x28=f.FindRegister('x28').GetValueAsUnsigned();b=pr.ReadMemory(x28+0xd0,4,e);print('CLS',hex(f.FindRegister('x8').GetValueAsUnsigned()&0xffff),b.hex() if e.Success() else 'err',flush=True)
    if a==0x42dbf78:
        e=lldb.SBError();x8=f.FindRegister('x8').GetValueAsUnsigned();print('TGT',hex(x8),pr.ReadMemory(x8,0x30,e).hex() if e.Success() else 'err',flush=True)
    if a==0x3c4639c:
        e=lldb.SBError();x28=f.FindRegister('x28').GetValueAsUnsigned();print('X28',hex(x28),pr.ReadMemory(x28+0xc0,0x28,e).hex() if e.Success() else e,flush=True)
        e=lldb.SBError();print('LR',hex(f.FindRegister('lr').GetValueAsUnsigned()-0x100000000),'MSG',pr.ReadCStringFromMemory(f.FindRegister('x1').GetValueAsUnsigned(),300,e),flush=True)
    r=f.FindRegister('x0').GetValueAsUnsigned();print('BPHIT',hex(a),'x0=',hex(r),'x8=',hex(f.FindRegister('x8').GetValueAsUnsigned()-0x100000000),'x1=',hex(f.FindRegister('x1').GetValueAsUnsigned()),flush=True);HITS[a]=HITS.get(a,0)+1;return False
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
            x19=fr.FindRegister('x19').GetValueAsUnsigned();e2=lldb.SBError();print('X19',hex(x19),p.ReadMemory(x19,0x60,e2).hex() if True else '',flush=True);ri=lldb.SBMemoryRegionInfo();p.GetMemoryRegionInfo(x19,ri);print('REGION',hex(ri.GetRegionBase()),hex(ri.GetRegionEnd()),ri.IsReadable(),ri.IsWritable(),flush=True)
            for k in (1,2,3): print('F%d'%k,[hex(th.frames[k].FindRegister('x%d'%r).GetValueAsUnsigned()) for r in (19,20,21)],flush=True)
            lr=fr.FindRegister('lr').GetValueAsUnsigned(); print("  LR",hex(lr),p.GetTarget().ResolveLoadAddress(lr),flush=True)
            sp=fr.FindRegister('sp').GetValueAsUnsigned(); err=lldb.SBError()
            for k in range(0,48):
                v=p.ReadUnsignedFromMemory(sp+8*k,8,err)
                a=p.GetTarget().ResolveLoadAddress(v)
                if a.GetModule().IsValid() and a.GetSection().IsValid() and 'TEXT' in a.GetSection().GetName()+a.GetSection().GetParent().GetName() if a.GetSection().IsValid() and a.GetSection().GetParent().IsValid() else False: print("  stk",k,hex(v),a,flush=True)
            print("HITS",{hex(k):v for k,v in HITS.items()},flush=True)
            p.Kill();return
    print("TIMEOUT",{hex(k):v for k,v in HITS.items()},flush=True);p.Kill()
def __lldb_init_module(d,_):
    d.HandleCommand("command script add -f play.run cpg_play")
