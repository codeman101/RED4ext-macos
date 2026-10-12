module CpAutotest

// The game's per-frame buffer clears, second pass (MetalFX Denoiser plugin): "fillstat" with call sites and buffer
// labels, then a GPU profile of one frame with the clears of at least 8 MiB kept and one with them skipped
// ("fillskip"), time frozen. Background, muted: ptrun.sh fills2
public func CpRunMenuChecks(scenario: String) -> Void {}

func CpF2Mtl(kind: String, name: String) -> Void {
    CpReport("{\"event\":\"MTL\",\"kind\":\"" + kind + "\",\"name\":\"" + name + "\",\"frames\":0}");
}

public func CpRunWorldStep(player: ref<PlayerPuppet>, step: Int32) -> Float {
    let mode = StrLen(CpAutotestTag()) > 0 ? CpAutotestTag() : "current";
    let time = GameInstance.GetTimeSystem(player.GetGame());
    switch step {
        case 0:
            CpReport("{\"event\":\"BENCH_MODE\",\"mode\":\"" + mode + "\",\"settings\":\"fills2\"}");
            return 20.0;
        case 1:
            time.SetTimeDilation(n"cpbench", 0.0);
            CpF2Mtl("fillstat", "30");
            return 4.0;
        case 2: CpF2Mtl("profile", "s0-" + mode + "-keep"); return 8.0;
        case 3: CpF2Mtl("fillskip", "8388608"); return 3.0;
        case 4: CpF2Mtl("profile", "s0-" + mode + "-skip"); return 8.0;
        case 5: CpF2Mtl("fillskip", "off"); return 3.0;
        case 6: CpF2Mtl("profile", "s0-" + mode + "-keep2"); return 8.0;
        case 7: CpF2Mtl("fillskip", "8388608"); return 3.0;
        case 8: CpF2Mtl("profile", "s0-" + mode + "-skip2"); return 8.0;
        default:
            CpF2Mtl("fillskip", "off");
            time.UnsetTimeDilation(n"cpbench");
            CpCheck("fills2_done", true, mode);
            return -1.0;
    }
}
