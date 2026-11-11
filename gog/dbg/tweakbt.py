# lldb: break on file-open style libc calls, print backtrace (image offsets) when the path mentions tweakdb.
# Usage: lldb -b -o "command script import dbg/tweakbt.py" -o cpg_tweak
import os, time
import lldb
HOME = os.path.expanduser("~/cyberpunk-gog-port")
BIN = HOME + "/dbg/game/Cyberpunk2077.app/Contents/MacOS/Cyberpunk2077"
SECS = int(os.environ.get("CPG_SECS", "50"))
NAMES = ["open", "__open", "__open_nocancel", "openat", "fopen", "stat", "stat64", "lstat", "access", "__open_extended"]
out = []
base = [0]

def path_at(proc, addr):
    if addr < 0x10000:
        return None
    err = lldb.SBError()
    b = proc.ReadMemory(addr, 200, err)
    if not err.Success() or not b:
        return None
    return bytes(b).split(b"\0")[0].decode("latin1")

def cb(frame, bp_loc, extra, internal):
    try:
        th = frame.GetThread(); proc = th.GetProcess()
        for r in ("x0", "x1"):
            s = path_at(proc, frame.FindRegister(r).GetValueAsUnsigned())
            if s and "tweakdb" in s.lower():
                bt = []
                for f in th:
                    pc = f.GetPC() - base[0]
                    bt.append(hex(pc) if 0 <= pc < 0x9800000 else "ext")
                out.append((bp_loc.GetBreakpoint().GetID(), frame.GetFunctionName(), s, bt[:14]))
                break
    except Exception as e:
        out.append(("err", str(e), "", []))
    return False

def cpg_tweak(debugger, command, result, internal):
    debugger.SetAsync(False)
    t = debugger.CreateTarget(BIN)
    li = lldb.SBLaunchInfo([])
    li.SetLaunchFlags(lldb.eLaunchFlagStopAtEntry | lldb.eLaunchFlagDisableASLR)
    err = lldb.SBError()
    p = t.Launch(li, err)
    if not err.Success():
        print("launch failed", err); return
    base[0] = t.GetModuleAtIndex(0).GetObjectFileHeaderAddress().GetLoadAddress(t)
    for n in NAMES:
        t.BreakpointCreateByName(n).SetScriptCallbackFunction("tweakbt.cb")
    debugger.SetAsync(True)
    p.Continue(); time.sleep(SECS); p.Stop(); time.sleep(1)
    with open(HOME + "/notes/tweakbt.txt", "w") as f:
        for o in out: f.write(repr(o) + "\n")
    print("events", len(out)); p.Kill()

def __lldb_init_module(debugger, internal):
    debugger.HandleCommand("command script add -f tweakbt.cpg_tweak cpg_tweak")
