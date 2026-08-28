#!/usr/bin/env python3
"""T-14/T-22 閉環迴歸測試：IR 合成引擎（image-source 早期 + shaped-noise 晚期）。

跑法：`python scripts/test_ir_synth.py`（純合成資料＋固定亂數種子，不依賴模型下載，
任何 clone 都能重跑；全部通過 exit 0，任一失敗 exit 1）。

兩層閉環（為什麼要分兩層——執行時的實證，數字見 TASKS.md T-14 卡交接筆記）：

1. **機制閉環（平坦目標）**：六頻段目標 RT60 全部相同時，量測 T30 必須逐頻段
   對目標誤差 ≤20%。這證明「濾波器組＋指數包絡＋crossfade＋獨立量測」整條鏈是對的。

2. **實例閉環（地毯房，有陡峭頻段階梯）**：逐頻段量測對 *Sabine 目標* 會在 125Hz
   差 +100% 左右——這**不是引擎錯**，是八度頻帶量測的混頻物理：250Hz 頻段（目標
   0.885s）與 125Hz 量測頻帶共享 177Hz 邊緣，衰減慢的鄰帶能量會主導量測尾段。
   **pra 完整物理模擬自己也一樣**（T-12 documented 實測 125Hz = 0.748s vs Sabine
   0.348s，+115%；本輪重跑 pra 全模擬 20k rays 多次落在 0.62–0.81s）。
   所以實例閉環的錨點是 **T-12 文件化的物理模擬實測值 0.748s**（同房間、同材質、
   幾乎同收發位置），不是 Sabine 公式值——量測 vs 量測才是同類比較。

T-22（引擎尺度自適應）新增三組（既有 10 項＋新增 13 項＝總計 23 項；
2026-08-28 更正：舊註解寫的「既有 11 項」把收尾那行 `✅ 全部通過` 算進去了）：

3. **零回歸（【6】）**：T-14 交付版的兩條示範 IR（小房間地毯房、hall）與本次
   合成結果 bit-identical（比對 `synthesize_ir()` 回傳陣列的 MD5，不是比對 WAV
   檔案——避開 soundfile 編碼細節，直接驗證數值本身）。這兩個房間的「最短一階
   反射到達時間 + IR_ENERGY_MATCH_MS」都小於 90ms 下限，理論上應該完全走
   `max()` 的左支、早期窗長不變，此測試把這件事釘死成硬證據。

4. **尺度掃描（【7】）**：沿用 Opus 在 T-21 驗證時定位問題的材質組合（巨蛋
   `audience_seating` 六面＋`generic_wall` 天花板），只變尺寸：40×30×15、
   80×60×25、120×100×35、160×130×45（T-21 巨蛋示範場景實際尺寸）、
   200×160×55（T-20 `stadium_dome` preset 尺寸）。**修正前**這組尺寸在
   120×100×35 與 160×130×45 分別是 −75%／−94%（T-21 卡「❌ Opus 退回理由」第 2
   點）；**修正後**全部尺寸 2k/4k 誤差都應 ≤25%，且不觸發能量匹配窗警示。

5. **防禦性警示（【8】）**：人工把早期窗強制設回舊的固定 90ms（monkeypatch
   `simulate_early_ir` 的回傳值），對巨蛋尺寸重跑，確認【7】用來偵測失效的
   「能量匹配窗內幾乎無反射能量」警示真的會被觸發——證明這道縱深防禦不是擺設。
"""

import hashlib
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.image_reverb import config, ir_metrics, ir_synth  # noqa: E402
from src.image_reverb.acoustics import AcousticsResult, compute_acoustics  # noqa: E402
from src.image_reverb.geometry import RoomEstimate  # noqa: E402
from src.image_reverb.materials import (  # noqa: E402
    SurfaceMaterials,
    load_materials,
    parse_surface_spec,
)

# T-12 Opus 驗證時對「floor=carpet＋其餘 gypsum_board、4×3×2.5m」完整 pra 模擬
# （image-source 12 階 + ray tracing）獨立量測的 125Hz T30。
# 出處：TASKS.md T-12 卡交接筆記（2026-08-18 實測，Opus 2026-08-25 複核）。
T12_MEASURED_125HZ_S = 0.748

# T-14 交付版兩條示範 IR 的 MD5（`synthesize_ir()` 回傳陣列的原始 bytes，
# 與 `scripts/gen_t14_listen.py` 的 CASES 完全一致）。T-22 修改引擎後兩者必須
# 維持 bit-identical（零回歸判準）——出處：本檔在 T-22 修正前後分別重跑比對，
# 且與 `output/ir_synth/T14_*.wav` 的檔案 MD5 交叉核對一致。
T14_DELIVERED_MD5 = {
    "small_surf_carpet": "f3a763bed13cf4d6f49dbacddee6313f",
    "hall": "f24353b5dbecf0f6073ca65a7be44ad3",
}

# T-21 巨蛋示範場景（`assets/scenes/stadium_corridor.json` source_room）的材質組合：
# 六面 audience_seating、天花板 generic_wall——Opus 在 T-21 驗證時定位 −94% 靜默
# 錯誤所用的同一組材質，尺度掃描沿用它才是同類比較。
STADIUM_MATERIAL_SURFACES = SurfaceMaterials(
    floor="audience_seating",
    ceiling="generic_wall",
    west="audience_seating",
    east="audience_seating",
    south="audience_seating",
    north="audience_seating",
)

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  {'✅' if ok else '❌'} {name}：{detail}")
    if not ok:
        FAILURES.append(name)


def flat_acoustics(rt60_s: float, bands: list[int]) -> AcousticsResult:
    """合成一個「六頻段目標全部相同」的假 AcousticsResult（機制閉環專用）。"""
    return AcousticsResult(
        length_m=4.0,
        width_m=3.0,
        height_m=2.5,
        volume_m3=30.0,
        dims_source="manual",
        surfaces={name: "gypsum_board" for name in ir_synth.SURFACE_NAMES},
        band_center_freqs_hz=list(bands),
        rt60_bands_sabine=[rt60_s] * len(bands),
        rt60_bands_eyring=[rt60_s] * len(bands),
        rt60_mid_sabine=rt60_s,
        rt60_mid_eyring=rt60_s,
        predelay_ms=6.6,
        confidence="high",
        warnings=[],
    )


def main() -> int:
    data = load_materials()
    bands = data["band_center_freqs_hz"]

    # ---------- 1. 機制閉環：平坦目標，量測必須跟上 ----------
    print("【1】機制閉環（平坦目標，無頻段階梯）")
    for rt in (0.5, 2.5):
        res = ir_synth.synthesize_ir(flat_acoustics(rt, bands), data)
        measured = ir_metrics.band_t30(res.ir, res.sample_rate, bands)
        worst = max(abs(m - rt) / rt for m in measured)
        detail = "  ".join(
            f"{f}Hz {(m - rt) / rt * 100:+.1f}%" for f, m in zip(bands, measured)
        )
        check(f"平坦 {rt}s 全頻段 ≤20%", worst <= 0.20, detail)

    # ---------- 2. 實例閉環：地毯房（陡峭階梯的代表案例）----------
    print("【2】實例閉環（floor=carpet＋gypsum_board，4×3×2.5m）")
    est = RoomEstimate(4.0, 3.0, 2.5, confidence="high", dims_source="manual")
    surf = parse_surface_spec("floor=carpet,walls=gypsum_board", data)
    ac = compute_acoustics(est, surf, data)
    res = ir_synth.synthesize_ir(ac, data)
    measured = ir_metrics.band_t30(res.ir, res.sample_rate, bands)

    print("      逐頻段（誠實列出，含對 Sabine 目標的已知混頻偏差——地雷 #14）：")
    for f, tar, m in zip(bands, ac.rt60_bands_sabine, measured):
        print(
            f"        {f:>5} Hz  Sabine 目標 {tar:.3f}s  量測 {m:.3f}s  "
            f"({(m - tar) / tar * 100:+.1f}%)"
        )

    err_vs_t12 = (measured[0] - T12_MEASURED_125HZ_S) / T12_MEASURED_125HZ_S
    check(
        "125Hz 量測 vs T-12 物理模擬實測錨點 0.748s ≤20%",
        abs(err_vs_t12) <= 0.20,
        f"量測 {measured[0]:.3f}s，誤差 {err_vs_t12 * 100:+.1f}%",
    )

    tilt = measured[0] / measured[-1]
    check(
        "無鐵筒子傾斜（125Hz/4kHz 量測比 < 5；鐵筒子缺陷時是 ~49 倍）",
        tilt < 5.0,
        f"比值 {tilt:.2f}",
    )

    # ---------- 3. 輸出健全性 ----------
    print("【3】輸出健全性")
    fs = res.sample_rate
    min_len = max(ac.rt60_bands_sabine) * 1.2
    check(
        "IR 長度 ≥ max(目標 RT60) × 1.2（T-03 截尾的坑）",
        len(res.ir) / fs >= min_len,
        f"{len(res.ir) / fs:.3f}s ≥ {min_len:.3f}s",
    )

    n_tail = len(res.ir) // 10
    rms_all = float(np.sqrt(np.mean(res.ir**2)))
    rms_tail = float(np.sqrt(np.mean(res.ir[-n_tail:] ** 2)))
    check(
        "尾端無突然截斷（最後 10% RMS < 整體 RMS 的 10%）",
        rms_tail < 0.1 * rms_all,
        f"尾端 {rms_tail:.2e} vs 整體 {rms_all:.2e}",
    )

    peak_dbfs = 20.0 * np.log10(float(np.max(np.abs(res.ir))))
    check("峰值正規化 -3dBFS（±0.1dB）", abs(peak_dbfs + 3.0) < 0.1, f"{peak_dbfs:.2f} dBFS")

    # ---------- 4. 決定性與敏感性 ----------
    print("【4】決定性與敏感性")
    res2 = ir_synth.synthesize_ir(ac, data)
    check(
        "同輸入同 seed → bit-identical（可供 Opus 乾淨重跑比對）",
        bool(np.array_equal(res.ir, res2.ir)),
        f"兩次合成 {len(res.ir)} 樣本逐點相同" if np.array_equal(res.ir, res2.ir) else "不相同",
    )

    est_bigger = RoomEstimate(8.0, 6.0, 5.0, confidence="high", dims_source="manual")
    ac_bigger = compute_acoustics(est_bigger, surf, data)
    res_bigger = ir_synth.synthesize_ir(ac_bigger, data)
    check(
        "換房間尺寸 → IR 改變（非 hardcode）",
        len(res_bigger.ir) != len(res.ir)
        or not np.array_equal(res_bigger.ir[: len(res.ir)], res.ir),
        f"4×3×2.5 → {len(res.ir)} 樣本；8×6×5 → {len(res_bigger.ir)} 樣本",
    )

    # ---------- 5. 合理區間警示（T-13 Opus 建議 2）----------
    print("【5】合理區間警示")
    res_bad = ir_synth.synthesize_ir(flat_acoustics(0.05, bands), data)
    has_warning = any("合理區間" in w for w in res_bad.warnings)
    check(
        "目標 RT60 超出 0.1–12s → 有警示（不安靜通過）",
        has_warning,
        res_bad.warnings[0] if has_warning else "沒有任何警示",
    )

    # ---------- 6. T-22 零回歸：T-14 交付版兩條 IR 必須 bit-identical ----------
    print("【6】T-22 零回歸（T-14 交付版 IR 不得因引擎修正而改變）")
    t14_cases = [
        ("small_surf_carpet", (4.0, 3.0, 2.5), "floor=carpet,walls=gypsum_board"),
        ("hall", (30.0, 20.0, 12.0), "floor=wood_panel,walls=concrete,ceiling=gypsum_board"),
    ]
    for case_name, dims, spec in t14_cases:
        est_t14 = RoomEstimate(*dims, confidence="high", dims_source="manual")
        surf_t14 = parse_surface_spec(spec, data)
        ac_t14 = compute_acoustics(est_t14, surf_t14, data)
        res_t14 = ir_synth.synthesize_ir(ac_t14, data)
        md5_actual = hashlib.md5(res_t14.ir.tobytes()).hexdigest()
        md5_expected = T14_DELIVERED_MD5[case_name]
        check(
            f"{case_name}（{dims[0]}×{dims[1]}×{dims[2]}m）MD5 與 T-14 交付版相同",
            md5_actual == md5_expected,
            f"early_ms={res_t14.early_ms:.1f}（下限 {config.IR_EARLY_MIN_MS}）"
            f"  {md5_actual}" + ("" if md5_actual == md5_expected else f" ≠ {md5_expected}"),
        )

    # ---------- 7. T-22 尺度掃描：早期窗/匹配窗尺度自適應 ----------
    print("【7】T-22 尺度掃描（同材質＝巨蛋 audience_seating，只變尺寸）")
    scale_dims = [
        (40.0, 30.0, 15.0),
        (80.0, 60.0, 25.0),
        (120.0, 100.0, 35.0),
        (160.0, 130.0, 45.0),  # T-21 巨蛋示範場景實際尺寸
        (200.0, 160.0, 55.0),  # T-20 stadium_dome preset 尺寸
    ]
    for dims in scale_dims:
        est_s = RoomEstimate(*dims, confidence="high", dims_source="manual")
        ac_s = compute_acoustics(est_s, STADIUM_MATERIAL_SURFACES, data)
        res_s = ir_synth.synthesize_ir(ac_s, data)
        measured_s = ir_metrics.band_t30(res_s.ir, res_s.sample_rate, bands)
        errs = [
            (m - t) / t for m, t in zip(measured_s, ac_s.rt60_bands_sabine)
        ]
        worst_hf = max(abs(errs[-2]), abs(errs[-1]))  # 2k/4k：T-21 崩壞的頻段
        check(
            f"{dims[0]:.0f}×{dims[1]:.0f}×{dims[2]:.0f}m  2k/4k 對 Sabine 目標 ≤25%",
            worst_hf <= 0.25,
            f"early_ms={res_s.early_ms:.1f}  2k {errs[-2] * 100:+.1f}%  4k {errs[-1] * 100:+.1f}%",
        )
        no_energy_warning = not any("幾乎無反射能量" in w for w in res_s.warnings)
        check(
            f"{dims[0]:.0f}×{dims[1]:.0f}×{dims[2]:.0f}m 不觸發能量匹配窗警示",
            no_energy_warning,
            "無警示" if no_energy_warning else res_s.warnings,
        )

    # ---------- 8. 防禦性警示真的能被觸發（縱深防禦不是擺設）----------
    print("【8】防禦性警示觸發測試（人工把早期窗強制退回固定 90ms）")
    est_dome = RoomEstimate(160.0, 130.0, 45.0, confidence="high", dims_source="manual")
    ac_dome = compute_acoustics(est_dome, STADIUM_MATERIAL_SURFACES, data)

    original_simulate = ir_synth.simulate_early_ir

    def _forced_fixed_window(acoustics, surfaces, materials_data):
        ir_raw, onset_s, _dynamic_early_ms = original_simulate(
            acoustics, surfaces, materials_data
        )
        return ir_raw, onset_s, config.IR_EARLY_MIN_MS

    ir_synth.simulate_early_ir = _forced_fixed_window
    try:
        res_forced = ir_synth.synthesize_ir(ac_dome, data)
    finally:
        ir_synth.simulate_early_ir = original_simulate

    triggered = any("幾乎無反射能量" in w for w in res_forced.warnings)
    check(
        "強制固定 90ms 窗（巨蛋尺寸）→ 能量匹配窗警示真的會出現",
        triggered,
        res_forced.warnings if triggered else "沒有任何警示（防禦機制擺設）",
    )

    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 項失敗：{'、'.join(FAILURES)}")
        return 1
    print("✅ T-14/T-22 閉環迴歸測試全部通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
