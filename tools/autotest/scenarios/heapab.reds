module CpAutotest

// The MetalFX Denoiser plugin's per-thread cache in front of the engine's medium heaps (request "heapcache"): A/B/A/B
// during steady synthetic turns (game process only) at the player's settings, each with a 300-frame timeline, and the
// first two with a 10 s CPU sample (LAGPROF_CPU markers, sampled by the driver), plus the cache's hit counts.
// Background, muted: PTRUN_ENV="METALFX_FG_MULT=4 METALFX_FG_KEEP_UNSHOWN=1" ptrun.sh heapab, with cpusample.sh running.
public func CpRunMenuChecks(scenario: String) -> Void {}

func CpHaMtl(kind: String, name: String) -> Void {
    CpReport("{\"event\":\"MTL\",\"kind\":\"" + kind + "\",\"name\":\"" + name + "\",\"frames\":0}");
}

func CpHaRound(on: Bool, sample: Bool) -> Void {
    CpHaMtl("heapcache", on ? "on" : "off");
    CpReport("{\"event\":\"MOUSE\",\"dx\":2,\"dy\":0,\"steps\":1500,\"ms\":8}");
    CpHaMtl("timeline", "300");
    if sample {
        CpReport("{\"event\":\"LAGPROF_CPU\",\"phase\":\"" + (on ? "cacheon" : "cacheoff") + "\"}");
    }
}

public func CpRunWorldStep(player: ref<PlayerPuppet>, step: Int32) -> Float {
    let mode = StrLen(CpAutotestTag()) > 0 ? CpAutotestTag() : "current";
    switch step {
        case 0:
            CpReport("{\"event\":\"BENCH_MODE\",\"mode\":\"" + mode + "\",\"settings\":\"heapab\"}");
            CpHaMtl("framegen", "on");
            return 30.0;
        case 1: CpHaRound(false, true); return 14.0;
        case 2: CpReport("{\"event\":\"MOUSE\",\"dx\":-2,\"dy\":0,\"steps\":1500,\"ms\":8}"); return 13.0;
        case 3: CpHaRound(true, true); return 14.0;
        case 4: CpHaMtl("heapcache", "stats"); CpReport("{\"event\":\"MOUSE\",\"dx\":-2,\"dy\":0,\"steps\":1500,\"ms\":8}"); return 13.0;
        case 5: CpHaRound(false, false); return 14.0;
        case 6: CpReport("{\"event\":\"MOUSE\",\"dx\":-2,\"dy\":0,\"steps\":1500,\"ms\":8}"); return 13.0;
        case 7: CpHaRound(true, false); return 14.0;
        case 8: CpHaMtl("heapcache", "stats"); return 4.0;
        default:
            CpHaMtl("heapcache", "off");
            CpCheck("heapab_done", true, mode);
            return -1.0;
    }
}
