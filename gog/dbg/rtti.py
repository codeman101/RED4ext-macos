
import lldb,time,os
HOME=os.path.expanduser("~/cyberpunk-gog-port")
BIN=HOME+"/dbg/game/Cyberpunk2077.app/Contents/MacOS/Cyberpunk2077"
def run(debugger,c,r,i):
    debugger.SetAsync(False)
    t=debugger.CreateTarget(BIN);li=lldb.SBLaunchInfo([]);li.SetLaunchFlags(lldb.eLaunchFlagStopAtEntry|lldb.eLaunchFlagDisableASLR)
    e=lldb.SBError();p=t.Launch(li,e)
    base=t.GetModuleAtIndex(0).GetObjectFileHeaderAddress().GetLoadAddress(t)
    bp=t.BreakpointCreateByAddress(base+0x41B2858)
    p.Continue()
    th=p.GetSelectedThread()
    print("stopped",p.GetState(),hex(th.GetFrameAtIndex(0).GetPC()-base))
    th.StepOutOfFrame(th.GetFrameAtIndex(0)) if False else None
    # run to return: set temp bp at lr
    lr=th.GetFrameAtIndex(0).FindRegister("x30").GetValueAsUnsigned()
    b2=t.BreakpointCreateByAddress(lr);b2.SetOneShot(True);bp.SetEnabled(False)
    p.Continue()
    x0=p.GetSelectedThread().GetFrameAtIndex(0).FindRegister("x0").GetValueAsUnsigned()
    print("ret obj",hex(x0))
    er=lldb.SBError();vt=p.ReadPointerFromMemory(x0,er);print("vtable",hex(vt),hex(vt-base))
    for k in range(14,40):
        v=p.ReadPointerFromMemory(vt+8*k,er);print(k,hex(v-base) if base<=v<base+0x7800000 else hex(v))
    p.Kill()
def __lldb_init_module(d,i): d.HandleCommand("command script add -f rtti.run cpg_rtti")
