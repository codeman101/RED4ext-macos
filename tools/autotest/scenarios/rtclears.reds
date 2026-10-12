module CpAutotest

// Path tracing's per-frame buffer clears skipped (MetalFX Denoiser plugin, request "rtclears skip|keep"): same-view
// captures with time frozen (kept a, b; skipped a, b; kept c: the skip should differ from kept no more than kept a from
// kept b), then a 6-minute soak with the clears skipped and the player's frame generation, time running, synthetic
// turns (game process only), with GPU errors logged by the plugin. Background, muted: ptrun.sh rtclears
public func CpRunMenuChecks(scenario: String) -> Void {}

func CpRcMtl(kind: String, name: String) -> Void {
    CpReport("{\"event\":\"MTL\",\"kind\":\"" + kind + "\",\"name\":\"" + name + "\",\"frames\":0}");
}

public func CpRunWorldStep(player: ref<PlayerPuppet>, step: Int32) -> Float {
    let mode = StrLen(CpAutotestTag()) > 0 ? CpAutotestTag() : "current";
    let time = GameInstance.GetTimeSystem(player.GetGame());
    if step == 0 {
        CpReport("{\"event\":\"BENCH_MODE\",\"mode\":\"" + mode + "\",\"settings\":\"rtclears\"}");
        CpRcMtl("rtclears", "keep");
        time.SetTimeDilation(n"cpbench", 0.0);
        return 20.0;
    }
    switch step {
        case 1: CpRcMtl("shot", "s0-keep-a"); return 2.0;
        case 2: CpRcMtl("shot", "s0-keep-b"); return 1.0;
        case 3: CpRcMtl("rtclears", "skip"); return 3.0;
        case 4: CpRcMtl("shot", "s0-skip-a"); return 2.0;
        case 5: CpRcMtl("shot", "s0-skip-b"); return 1.0;
        case 6: CpRcMtl("rtclears", "keep"); return 3.0;
        case 7: CpRcMtl("shot", "s0-keep-c"); return 1.0;
        case 8:
            CpRcMtl("rtclears", "skip");
            time.UnsetTimeDilation(n"cpbench");
            return 2.0;
    }
    if step < 8 + 36 { // 36 x 10 s: turns right and back
        CpReport("{\"event\":\"MOUSE\",\"dx\":" + (step % 2 == 0 ? "4" : "-4") + ",\"dy\":0,\"steps\":600,\"ms\":8}");
        if step % 12 == 0 {
            CpRcMtl("timeline", "150");
        }
        return 10.0;
    }
    if step == 8 + 36 {
        time.SetTimeDilation(n"cpbench", 0.0);
        return 3.0;
    }
    if step == 8 + 37 {
        CpRcMtl("shot", "s0-soak-end");
        CpRcMtl("rtclears", "keep");
        return 60.0;
    }
    time.UnsetTimeDilation(n"cpbench");
    CpCheck("rtclears_done", true, mode);
    return -1.0;
}
