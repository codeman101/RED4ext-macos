module CpAutotest

// The game's per-frame buffer clears (MetalFX Denoiser plugin): "fillstat" groups 60 frames' fillBuffer calls by call
// site, size and value; then A/B/A/B rounds, fills of at least 8 MiB kept and skipped ("fillskip"): two captures of the
// upscaler's output 2 s apart with time frozen, then a 150-frame timeline during a slow synthetic turn (game process
// only). Background, muted: PTRUN_ENV="METALFX_FG_KEEP_UNSHOWN=1" ptrun.sh fills
public func CpRunMenuChecks(scenario: String) -> Void {}

func CpFiMtl(kind: String, name: String) -> Void {
    CpReport("{\"event\":\"MTL\",\"kind\":\"" + kind + "\",\"name\":\"" + name + "\",\"frames\":0}");
}

public func CpRunWorldStep(player: ref<PlayerPuppet>, step: Int32) -> Float {
    let mode = StrLen(CpAutotestTag()) > 0 ? CpAutotestTag() : "current";
    let time = GameInstance.GetTimeSystem(player.GetGame());
    if step == 0 {
        CpReport("{\"event\":\"BENCH_MODE\",\"mode\":\"" + mode + "\",\"settings\":\"fills\"}");
        return 30.0;
    }
    if step == 1 {
        CpFiMtl("fillstat", "60");
        return 6.0;
    }
    let round = (step - 2) / 5;
    let phase = (step - 2) % 5;
    if round < 4 {
        let skip = round % 2 == 1;
        let tag = "s0-" + mode + "-r" + ToString(round) + (skip ? "-skip" : "-keep");
        switch phase {
            case 0:
                CpFiMtl("fillskip", skip ? "8388608" : "off");
                time.SetTimeDilation(n"cpbench", 0.0);
                return 4.0;
            case 1: CpFiMtl("shot", tag + "-a"); return 2.0;
            case 2: CpFiMtl("shot", tag + "-b"); return 1.0;
            case 3:
                time.UnsetTimeDilation(n"cpbench");
                CpReport("{\"event\":\"MOUSE\",\"dx\":2,\"dy\":0,\"steps\":700,\"ms\":8}");
                CpFiMtl("timeline", "150");
                return 7.0;
            default:
                CpReport("{\"event\":\"MOUSE\",\"dx\":-2,\"dy\":0,\"steps\":700,\"ms\":8}");
                return 7.0;
        }
    }
    if round == 4 && phase == 0 {
        CpFiMtl("fillskip", "off");
        return 60.0;
    }
    CpCheck("fills_done", true, mode);
    return -1.0;
}
