module CpAutotest

// 4x frame generation in motion (MetalFX Denoiser plugin): during a steady synthetic turn (sent to the game process
// only), every image shown for 4 game frames is saved ("fgshot": fgsNN-1..3 generated, fgsNN-4 the game's frame), first
// with the generated frames' detail from the real frames (fgs00-03), then without it (fgs04-07). Checks: edge and
// noise energy per phase (pulsing at the rendered rate) and the HUD (minimap edge).
// Run (muted, background): PTRUN_ENV="METALFX_FG_MULT=4 METALFX_FG_KEEP_UNSHOWN=1" ptrun.sh fgmotion
public func CpRunMenuChecks(scenario: String) -> Void {}

func CpFmMtl(kind: String, name: String) -> Void {
    CpReport("{\"event\":\"MTL\",\"kind\":\"" + kind + "\",\"name\":\"" + name + "\",\"frames\":0}");
}

func CpFmMouse(dx: Int32, dy: Int32, steps: Int32, ms: Int32) -> Void {
    CpReport("{\"event\":\"MOUSE\",\"dx\":" + ToString(dx) + ",\"dy\":" + ToString(dy) + ",\"steps\":" + ToString(steps)
        + ",\"ms\":" + ToString(ms) + "}");
}

public func CpRunWorldStep(player: ref<PlayerPuppet>, step: Int32) -> Float {
    let mode = StrLen(CpAutotestTag()) > 0 ? CpAutotestTag() : "current";
    switch step {
        case 0:
            CpReport("{\"event\":\"BENCH_MODE\",\"mode\":\"" + mode + "\",\"settings\":\"fgmotion\"}");
            return 30.0;
        case 1:
            CpFmMtl("framegen", "on");
            CpFmMtl("fgdetail", "on");
            return 6.0;
        case 2: CpFmMouse(3, 0, 400, 8); return 1.0;  // a slow steady turn, 3.2 s
        case 3: CpFmMtl("fgshot", "4"); return 3.0;
        case 4: CpFmMouse(-3, 0, 400, 8); return 4.0;
        case 5: CpFmMtl("fgdetail", "off"); return 2.0;
        case 6: CpFmMouse(3, 0, 400, 8); return 1.0;
        case 7: CpFmMtl("fgshot", "4"); return 3.0;
        case 8: CpFmMouse(-3, 0, 400, 8); return 4.0;
        case 9:
            CpFmMtl("fgdetail", "on");
            return 120.0; // the PNGs are written in the background
        default:
            CpCheck("fgmotion_done", true, mode);
            return -1.0;
    }
}
