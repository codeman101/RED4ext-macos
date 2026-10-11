module CpAutotest

// Still-image noise flicker of MetalFX's denoised scaler (MetalFX Denoiser plugin): at the save's position with time
// frozen and frame generation off, rounds over the variants below, interleaved (v0 v1 v2 v3 v0 v1 v2 v3) against drift.
// For each round, 3 s to settle, then three captures of the upscaler's output (the plugin's "shot" request, saved under
// metal/) 2 s apart. The flicker is their difference (higher PSNR = steadier): compare
// s0-<mode>-r<round>-<variant>-still-a with -still-b and -still-b with -still-c (scripts/imgdiff.swift).
// Earlier variants (2026-10-10): render scale 3 vs 2.5, sharpening 0.4 vs 0, MetalFX auto exposure.
// Now (2026-10-11): render scale 2.75, sharpening 0; the game's CAS after the denoiser, and the specular hit distance.
// Run through tools/rtbench: CP_RESOLUTION=3456x2160 RTBENCH_PRESET=Performance@3 RTBENCH_DENOISE=fx \
//   RTBENCH_CVARS=MFX/OverrideEnable=1,MFX/Quality=4 RTBENCH_SCENARIO=flicker tools/rtbench pt
public func CpRunMenuChecks(scenario: String) -> Void {}

func CpFlMtl(kind: String, name: String) -> Void {
    CpReport("{\"event\":\"MTL\",\"kind\":\"" + kind + "\",\"name\":\"" + name + "\",\"frames\":0}");
}

func CpFlVariants() -> Int32 {
    return 4;
}

func CpFlVariant(i: Int32) -> String {
    switch i % CpFlVariants() {
        case 0: return "base";
        case 1: return "nocas";
        case 2: return "hit0";
        default: return "hit1";
    }
}

func CpFlApply(i: Int32) -> Void {
    let v = i % CpFlVariants();
    CpFlMtl("cvar", "Developer/FeatureToggles/ConstrastAdaptiveSharpening=" + (v == 1 ? "0" : "1"));
    CpFlMtl("denoisehit", v == 2 ? "0" : (v == 3 ? "1" : "off"));
}

public func CpRunWorldStep(player: ref<PlayerPuppet>, step: Int32) -> Float {
    let mode = StrLen(CpAutotestTag()) > 0 ? CpAutotestTag() : "current";
    let time = GameInstance.GetTimeSystem(player.GetGame());
    let rounds = 2 * CpFlVariants();
    if step == 0 {
        CpReport("{\"event\":\"BENCH_MODE\",\"mode\":\"" + mode + "\",\"settings\":\"flicker\"}");
        return 10.0;
    }
    if step == 1 {
        CpFlMtl("framegen", "off");
        CpFlMtl("sharpen", "0");
        CpFlMtl("ultrascale", "2.75");
        time.SetTimeDilation(n"cpbench", 0.0);
        return 3.0;
    }
    // Per round: [set, screenshots a, b, c] (two pairs per round).
    let round = (step - 2) / 4;
    let phase = (step - 2) % 4;
    if round < rounds {
        let tag = "s0-" + mode + "-r" + ToString(round) + "-" + CpFlVariant(round);
        switch phase {
            case 0:
                CpFlApply(round);
                return 3.0;
            case 1:
                CpFlMtl("shot", tag + "-still-a");
                return 2.0;
            case 2:
                CpFlMtl("shot", tag + "-still-b");
                return 2.0;
            default:
                CpFlMtl("shot", tag + "-still-c");
                return 2.0;
        }
    }
    if round == rounds && phase == 0 {
        CpFlApply(0);
        time.UnsetTimeDilation(n"cpbench");
        return 30.0; // the captures are written in the background
    }
    CpCheck("flicker_done", true, mode);
    return -1.0;
}
