module CpAutotest

// Low-latency pacing (MetalFX Denoiser plugin, request "lowlatency"): 300-frame timelines during steady synthetic mouse
// movement (to the game process only) at the player's settings, A/B/A/B: 4x with low-latency pacing off, on, off, on;
// then on with frame generation off. scripts/timeline_report.py compares mouse read to frame done on the GPU.
// Background, muted: PTRUN_ENV="METALFX_FG_MULT=4 METALFX_FG_KEEP_UNSHOWN=1" ptrun.sh lowlat
public func CpRunMenuChecks(scenario: String) -> Void {}

func CpLlMtl(kind: String, name: String) -> Void {
    CpReport("{\"event\":\"MTL\",\"kind\":\"" + kind + "\",\"name\":\"" + name + "\",\"frames\":0}");
}

func CpLlRound(on: Bool) -> Void {
    CpLlMtl("lowlatency", on ? "on" : "off");
    CpReport("{\"event\":\"MOUSE\",\"dx\":2,\"dy\":0,\"steps\":1500,\"ms\":8}");
    CpLlMtl("timeline", "300");
}

public func CpRunWorldStep(player: ref<PlayerPuppet>, step: Int32) -> Float {
    let mode = StrLen(CpAutotestTag()) > 0 ? CpAutotestTag() : "current";
    switch step {
        case 0:
            CpReport("{\"event\":\"BENCH_MODE\",\"mode\":\"" + mode + "\",\"settings\":\"lowlat\"}");
            CpLlMtl("framegen", "on");
            return 30.0;
        case 1: CpLlRound(false); return 14.0;
        case 2: CpReport("{\"event\":\"MOUSE\",\"dx\":-2,\"dy\":0,\"steps\":1500,\"ms\":8}"); return 13.0;
        case 3: CpLlRound(true); return 14.0;
        case 4: CpReport("{\"event\":\"MOUSE\",\"dx\":-2,\"dy\":0,\"steps\":1500,\"ms\":8}"); return 13.0;
        case 5: CpLlRound(false); return 14.0;
        case 6: CpReport("{\"event\":\"MOUSE\",\"dx\":-2,\"dy\":0,\"steps\":1500,\"ms\":8}"); return 13.0;
        case 7: CpLlRound(true); return 14.0;
        case 8:
            CpLlMtl("framegen", "off");
            return 4.0;
        case 9: CpLlRound(true); return 14.0;
        case 10:
            CpLlMtl("framegen", "on");
            CpLlMtl("lowlatency", "off");
            return 5.0;
        default:
            CpCheck("lowlat_done", true, mode);
            return -1.0;
    }
}
