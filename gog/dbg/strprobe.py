# lldb: breakpoint every offset in notes/hot.tsv, record which ones receive ASCII strings in x0/x1.
# Usage: lldb -b -o "command script import dbg/strprobe.py" -o cpg_run
import json
import os
import time

import lldb

HOME = os.path.expanduser("~/cyberpunk-gog-port")
BIN = HOME + "/dbg/game/Cyberpunk2077.app/Contents/MacOS/Cyberpunk2077"
SECS = int(os.environ.get("CPG_SECS", "45"))
LIMIT = 200
res = {}  # bp id -> {"off", "x0", "x1", "n"}


def text_at(proc, addr):
    if addr < 0x10000:
        return None
    err = lldb.SBError()
    b = proc.ReadMemory(addr, 80, err)
    if not err.Success() or not b:
        return None
    b = bytes(b).split(b"\0")[0]
    if len(b) >= 3 and all(32 <= c < 127 for c in b):
        return b.decode()
    return None


def cb(frame, bp_loc, extra, internal):
    try:
        return cb2(frame, bp_loc)
    except Exception:
        return False


def cb2(frame, bp_loc):
    bp = bp_loc.GetBreakpoint()
    r = res[bp.GetID()]
    proc = frame.GetThread().GetProcess()
    for reg in ("x0", "x1"):
        s = text_at(proc, frame.FindRegister(reg).GetValueAsUnsigned())
        if s is not None:
            r["n_" + reg] += 1
            if len(r[reg]) < 6 and s not in r[reg]:
                r[reg].append(s)
    r["n"] += 1
    if r["n"] >= LIMIT:
        bp.SetEnabled(False)
    return False


def cpg_run(debugger, command, result, internal):
    offs = [int(l.split("\t")[0], 16) for l in open(HOME + "/notes/hot.tsv").read().splitlines()[1:]]
    debugger.SetAsync(False)
    target = debugger.CreateTarget(BIN)
    li = lldb.SBLaunchInfo([])
    li.SetLaunchFlags(lldb.eLaunchFlagStopAtEntry | lldb.eLaunchFlagDisableASLR)
    err = lldb.SBError()
    proc = target.Launch(li, err)
    if not err.Success():
        print("launch failed:", err)
        return
    base = target.GetModuleAtIndex(0).GetObjectFileHeaderAddress().GetLoadAddress(target)
    print("base", hex(base), "bps", len(offs))
    for off in offs:
        bp = target.BreakpointCreateByAddress(base + off)
        res[bp.GetID()] = {"off": hex(off), "x0": [], "x1": [], "n_x0": 0, "n_x1": 0, "n": 0}
        bp.SetScriptCallbackFunction("strprobe.cb")
    debugger.SetAsync(True)
    proc.Continue()
    time.sleep(SECS)
    proc.Stop()
    time.sleep(1)
    json.dump(sorted(res.values(), key=lambda r: -(r["n_x0"] + r["n_x1"])), open(HOME + "/notes/strprobe.json", "w"), indent=1)
    proc.Kill()
    print("done")


def __lldb_init_module(debugger, internal):
    debugger.HandleCommand("command script add -f strprobe.cpg_run cpg_run")
