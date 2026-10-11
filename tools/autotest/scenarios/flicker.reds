module CpAutotest

// Still-image noise flicker of MetalFX's denoised scaler (MetalFX Denoiser plugin): at the save's position with time
// frozen and frame generation off, four rounds (render scale 3, 2.5, 3, 2.5 with sharpening 0; sharpening and auto
// exposure were measured the same way). For each, 3 s to settle, then three captures of the upscaler's output (the
// plugin's "shot" request, saved under metal/) 2 s apart. The flicker is their difference (higher PSNR = steadier):
// compare s0-<mode>-r<round>-<variant>-still-a with -still-b and -still-b with -still-c (scripts/imgdiff.swift).
// Run through tools/rtbench: CP_RESOLUTION=3456x2160 RTBENCH_PRESET=Performance@3 RTBENCH_DENOISE=fx \
//   RTBENCH_CVARS=MFX/OverrideEnable=1,MFX/Quality=4 RTBENCH_SCENARIO=flicker tools/rtbench pt
public func CpRunMenuChecks(scenario: String) -> Void {}

func CpFlMtl(kind: String, name: String) -> Void {
    CpReport("{\"event\":\"MTL\",\"kind\":\"" + kind + "\",\"name\":\"" + name + "\",\"frames\":0}");
}

func CpFlVariant(i: Int32) -> String {
    return i % 2 == 1 ? "2.5" : "3";
}

public func CpRunWorldStep(player: ref<PlayerPuppet>, step: Int32) -> Float {
    let mode = StrLen(CpAutotestTag()) > 0 ? CpAutotestTag() : "current";
    let time = GameInstance.GetTimeSystem(player.GetGame());
    if step == 0 {
        CpReport("{\"event\":\"BENCH_MODE\",\"mode\":\"" + mode + "\",\"settings\":\"flicker\"}");
        return 10.0;
    }
    if step == 1 {
        CpFlMtl("framegen", "off");
        time.SetTimeDilation(n"cpbench", 0.0);
        return 3.0;
    }
    // Four rounds, render scale 3, 2.5, 3, 2.5 (interleaved against drift):
    // [set, screenshots a, b, c] (two pairs per round).
    let round = (step - 2) / 4;
    let phase = (step - 2) % 4;
    if round < 4 {
        let tag = "s0-" + mode + "-r" + ToString(round) + "-scale" + CpFlVariant(round);
        switch phase {
            case 0:
                CpFlMtl("sharpen", "0");
                CpFlMtl("ultrascale", CpFlVariant(round));
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
    if round == 4 && phase == 0 {
        CpFlMtl("ultrascale", "3");
        time.UnsetTimeDilation(n"cpbench");
        return 30.0; // the captures are written in the background
    }
    CpCheck("flicker_done", true, mode);
    return -1.0;
}
