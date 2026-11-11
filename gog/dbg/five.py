# lldb: break on candidate offsets (env CPG_OFFS="0x..,0x.."), log hit order + x0..x2. Usage: lldb -b -o "command script import dbg/five.py" -o cpg_five
import os, time
import lldb
HOME = os.path.expanduser("~/cyberpunk-gog-port")
BIN = HOME + "/dbg/game/Cyberpunk2077.app/Contents/MacOS/Cyberpunk2077"
SECS = int(os.environ.get("CPG_SECS", "45"))
log = []

def cb(frame, bp_loc, extra, internal):
    try:
        r = [frame.FindRegister(x).GetValueAsUnsigned() for x in ("x0", "x1", "x2", "x30")]
        log.append((time.time(), bp_loc.GetAddress().GetLoadAddress(frame.GetThread().GetProcess().GetTarget()) - 0x100000000, r))
    except Exception:
        pass
    return False

def cpg_five(debugger, command, result, internal):
    offs = [int(x, 16) for x in os.environ["CPG_OFFS"].split(",")]
    debugger.SetAsync(False)
    t = debugger.CreateTarget(BIN)
    li = lldb.SBLaunchInfo([])
    li.SetLaunchFlags(lldb.eLaunchFlagStopAtEntry | lldb.eLaunchFlagDisableASLR)
    err = lldb.SBError()
    p = t.Launch(li, err)
    if not err.Success():
        print("launch failed", err); return
    base = t.GetModuleAtIndex(0).GetObjectFileHeaderAddress().GetLoadAddress(t)
    for o in offs:
        t.BreakpointCreateByAddress(base + o).SetScriptCallbackFunction("five.cb")
    debugger.SetAsync(True)
    p.Continue()
    time.sleep(SECS)
    p.Stop(); time.sleep(1)
    import collections
    cnt = collections.Counter(o for _, o, _ in log)
    first = {}
    for ts, o, r in log: first.setdefault(o, ts - log[0][0])
    for o, n in cnt.most_common(30):
        print("HITS %#x n=%d first=%.1fs" % (o, n, first[o]))
    print("total hits", len(log))
    p.Kill()

def __lldb_init_module(debugger, internal):
    debugger.HandleCommand("command script add -f five.cpg_five cpg_five")
