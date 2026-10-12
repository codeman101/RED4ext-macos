module CpAutotest

// Input lag profile (MetalFX Denoiser plugin) at the player's settings (config.toml: 4x frame generation, frame limit,
// render scale): during steady synthetic mouse movement (sent to the game process only), a 300-frame timeline
// ("timeline": per frame mouse, CPU, GPU queue, GPU and display times), a GPU profile of one frame ("profile": per
// encoder GPU time, named passes, the plugin's own included), then the same timeline with frame generation off.
// LAGPROF_CPU markers tell the driver when to sample the game's threads (tools: sample). Background, muted:
//   PTRUN_ENV="METALFX_FG_MULT=4 METALFX_FG_KEEP_UNSHOWN=1" ptrun.sh lagprof
public func CpRunMenuChecks(scenario: String) -> Void {}

func CpLpMtl(kind: String, name: String) -> Void {
    CpReport("{\"event\":\"MTL\",\"kind\":\"" + kind + "\",\"name\":\"" + name + "\",\"frames\":0}");
}

func CpLpMouse(dx: Int32, steps: Int32) -> Void {
    CpReport("{\"event\":\"MOUSE\",\"dx\":" + ToString(dx) + ",\"dy\":0,\"steps\":" + ToString(steps) + ",\"ms\":8}");
}

public func CpRunWorldStep(player: ref<PlayerPuppet>, step: Int32) -> Float {
    let mode = StrLen(CpAutotestTag()) > 0 ? CpAutotestTag() : "current";
    switch step {
        case 0:
            CpReport("{\"event\":\"BENCH_MODE\",\"mode\":\"" + mode + "\",\"settings\":\"lagprof\"}");
            CpLpMtl("framegen", "on");
            return 30.0;
        case 1:
            CpLpMouse(2, 1500);                  // 12 s of slow turning
            CpLpMtl("timeline", "300");
            CpReport("{\"event\":\"LAGPROF_CPU\",\"phase\":\"fg4x\"}");
            return 13.0;
        case 2:
            CpLpMouse(-2, 600);
            CpLpMtl("profile", "s0-" + mode + "-fg4x");
            return 10.0;
        case 3:
            CpLpMtl("framegen", "off");
            return 5.0;
        case 4:
            CpLpMouse(2, 1500);
            CpLpMtl("timeline", "300");
            CpReport("{\"event\":\"LAGPROF_CPU\",\"phase\":\"fgoff\"}");
            return 13.0;
        case 5:
            CpLpMouse(-2, 600);
            CpLpMtl("profile", "s0-" + mode + "-fgoff");
            return 10.0;
        case 6:
            CpLpMtl("framegen", "on");
            return 20.0;
        default:
            CpCheck("lagprof_done", true, mode);
            return -1.0;
    }
}
