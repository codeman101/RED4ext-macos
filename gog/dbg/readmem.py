# lldb: launch debug copy (no breakpoints), wait CPG_SECS, stop, read qwords at base+0x7d34000+seg3 offsets. env CPG_SEG3="0x..:n,0x..:n"
import os, time, struct
import lldb
HOME = os.path.expanduser("~/cyberpunk-gog-port")
BIN = HOME + "/dbg/game/Cyberpunk2077.app/Contents/MacOS/Cyberpunk2077"

def cpg_read(debugger, command, result, internal):
    import traceback, io, contextlib
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            _read(debugger)
    except Exception:
        buf.write(traceback.format_exc())
    open(HOME + '/notes/readmem.txt', 'w').write(buf.getvalue())

def _read(debugger):
    debugger.SetAsync(False)
    t = debugger.CreateTarget(BIN)
    li = lldb.SBLaunchInfo([]); li.SetLaunchFlags(lldb.eLaunchFlagStopAtEntry | lldb.eLaunchFlagDisableASLR)
    err = lldb.SBError(); p = t.Launch(li, err)
    if not err.Success(): print("launch failed", err); return
    debugger.SetAsync(True); p.Continue(); time.sleep(int(os.environ.get("CPG_SECS", "35"))); p.Stop(); time.sleep(1)
    base = t.GetModuleAtIndex(0).GetObjectFileHeaderAddress().GetLoadAddress(t)
    def rd(a, n):
        e = lldb.SBError(); b = p.ReadMemory(a, n, e); return bytes(b) if e.Success() else None
    for spec in os.environ["CPG_SEG3"].split(","):
        off, n = spec.split(":"); a = base + 0x7d34000 + int(off, 16)
        b = rd(a, int(n) * 8)
        if not b: print(spec, "unreadable"); continue
        print("== seg3:%s" % off)
        for i in range(int(n)):
            v = struct.unpack_from("<Q", b, i * 8)[0]
            tag = ""
            if base <= v < base + 0x775c000: tag = "TEXT+%#x" % (v - base)
            elif v > 0x100000000 and v < 0x400000000000:
                vt = rd(v, 8)
                if vt:
                    vv = struct.unpack("<Q", vt)[0]
                    if base <= vv < base + 0x9d2c000: tag = "heap obj vt=%#x" % (vv - base)
            print("  [%d] %#x %s" % (i, v, tag))
    p.Kill()

def __lldb_init_module(debugger, internal):
    debugger.HandleCommand("command script add -f readmem.cpg_read cpg_read")
