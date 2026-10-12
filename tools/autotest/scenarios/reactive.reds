module CpAutotest

// MetalFX Denoiser's reactive mask (the transparencies composited into the scene: smoke, exhaust, particles) at the
// save's position (cars with exhaust and tyre smoke ahead), time running, frame generation off. Rounds alternate the
// mask off and on (request "denoisereactive"); each takes two captures of the upscaler's output 0.5 s apart after 4 s
// to settle, and the "on" rounds also save the mask (reactive PNG). Compare the smoke around the exhaust.
// Run (muted, background): RTBENCH_PRESET=Performance@3 RTBENCH_DENOISE=fx RTBENCH_SCENARIO=reactive
//   RTBENCH_CVARS=MFX/OverrideEnable=1,MFX/Quality=4 CP_RESOLUTION=3456x2160 tools/rtbench pt
public func CpRunMenuChecks(scenario: String) -> Void {}

func CpRxMtl(kind: String, name: String) -> Void {
    CpReport("{\"event\":\"MTL\",\"kind\":\"" + kind + "\",\"name\":\"" + name + "\",\"frames\":0}");
}

public func CpRunWorldStep(player: ref<PlayerPuppet>, step: Int32) -> Float {
    let mode = StrLen(CpAutotestTag()) > 0 ? CpAutotestTag() : "current";
    if step == 0 {
        CpReport("{\"event\":\"BENCH_MODE\",\"mode\":\"" + mode + "\",\"settings\":\"reactive\"}");
        return 10.0;
    }
    if step == 1 {
        CpRxMtl("framegen", "off");
        CpRxMtl("sharpen", "0");
        CpRxMtl("ultrascale", "2.75");
        return 3.0;
    }
    let round = (step - 2) / 4;
    let phase = (step - 2) % 4;
    if round < 4 {
        let on = round % 2 == 1;
        let tag = "s0-" + mode + "-r" + ToString(round) + (on ? "-on" : "-off");
        switch phase {
            case 0:
                CpRxMtl("denoisereactive", on ? "on" : "off");
                return 4.0;
            case 1:
                CpRxMtl("shot", tag + "-a");
                return 0.5;
            case 2:
                CpRxMtl("shot", tag + "-b");
                return 0.5;
            default:
                if on {
                    CpRxMtl("denoisereactive", "save");
                }
                return 1.0;
        }
    }
    if round == 4 && phase == 0 {
        CpRxMtl("denoisereactive", "on");
        return 90.0; // the captures are written in the background
    }
    CpCheck("reactive_done", true, mode);
    return -1.0;
}
