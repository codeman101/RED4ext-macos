module CpAutotest

// Low-latency pacing (MetalFX Denoiser plugin, request "lowlatency"): 300-frame timelines during steady synthetic mouse
// movement (to the game process only) at the player's settings, A/B/A/B: 4x with low-latency pacing off, on, off, on;
// then on with frame generation off. scripts/timeline_report.py compares mouse read to frame done on the GPU.
// lowlat2: the same with 2x frame generation (fgmult 2): off/on/off/on, then frame generation off with pacing off.
// Background, muted: PTRUN_ENV="METALFX_FG_MULT=4 METALFX_FG_KEEP_UNSHOWN=1" ptrun.sh lowlat2
public func CpRunMenuChecks(scenario: String) -> Void {}

func CpL2Mtl(kind: String, name: String) -> Void {
    CpReport("{\"event\":\"MTL\",\"kind\":\"" + kind + "\",\"name\":\"" + name + "\",\"frames\":0}");
}

func CpL2Round(on: Bool) -> Void {
    CpL2Mtl("lowlatency", on ? "on" : "off");
    CpReport("{\"event\":\"MOUSE\",\"dx\":2,\"dy\":0,\"steps\":1500,\"ms\":8}");
    CpL2Mtl("timeline", "300");
}

public func CpRunWorldStep(player: ref<PlayerPuppet>, step: Int32) -> Float {
    let mode = StrLen(CpAutotestTag()) > 0 ? CpAutotestTag() : "current";
    switch step {
        case 0:
            CpReport("{\"event\":\"BENCH_MODE\",\"mode\":\"" + mode + "\",\"settings\":\"lowlat2\"}");
            CpL2Mtl("framegen", "on");
            CpL2Mtl("fgmult", "2");
            return 30.0;
        case 1: CpL2Round(false); return 14.0;
        case 2: CpReport("{\"event\":\"MOUSE\",\"dx\":-2,\"dy\":0,\"steps\":1500,\"ms\":8}"); return 13.0;
        case 3: CpL2Round(true); return 14.0;
        case 4: CpReport("{\"event\":\"MOUSE\",\"dx\":-2,\"dy\":0,\"steps\":1500,\"ms\":8}"); return 13.0;
        case 5: CpL2Round(false); return 14.0;
        case 6: CpReport("{\"event\":\"MOUSE\",\"dx\":-2,\"dy\":0,\"steps\":1500,\"ms\":8}"); return 13.0;
        case 7: CpL2Round(true); return 14.0;
        case 8:
            CpL2Mtl("framegen", "off");
            return 4.0;
        case 9: CpL2Round(false); return 14.0;
        case 10:
            CpL2Mtl("framegen", "on");
            CpL2Mtl("fgmult", "4");
            CpL2Mtl("lowlatency", "off");
            return 5.0;
        default:
            CpCheck("lowlat2_done", true, mode);
            return -1.0;
    }
}
