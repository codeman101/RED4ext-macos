module CpAutotest

// Does the game's MetalFX sharpening (MetalFX_Sharpness) reach the final image with the Apple denoiser? Time frozen,
// 4x frame generation on: the upscaler's output ("shot", before the game's post-processing) and every image shown for
// one frame ("fgshot", as presented). Run twice with CP_SETTINGS .../graphics/presets:MetalFX_Sharpness=0.5 and =0.
public func CpRunMenuChecks(scenario: String) -> Void {}

func CpShMtl(kind: String, name: String) -> Void {
    CpReport("{\"event\":\"MTL\",\"kind\":\"" + kind + "\",\"name\":\"" + name + "\",\"frames\":0}");
}

public func CpRunWorldStep(player: ref<PlayerPuppet>, step: Int32) -> Float {
    let mode = StrLen(CpAutotestTag()) > 0 ? CpAutotestTag() : "current";
    let time = GameInstance.GetTimeSystem(player.GetGame());
    switch step {
        case 0:
            CpReport("{\"event\":\"BENCH_MODE\",\"mode\":\"" + mode + "\",\"settings\":\"sharp\"}");
            CpShMtl("framegen", "on");
            time.SetTimeDilation(n"cpbench", 0.0);
            return 25.0;
        case 1: CpShMtl("shot", "s0-" + mode + "-scaler"); return 1.0;
        case 2: CpShMtl("fgshot", "1"); return 60.0;
        default:
            time.UnsetTimeDilation(n"cpbench");
            CpCheck("sharp_done", true, mode);
            return -1.0;
    }
}
