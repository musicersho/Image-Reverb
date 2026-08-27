#!/usr/bin/env python3
"""T-14 閉環迴歸測試：IR 合成引擎（image-source 早期 + shaped-noise 晚期）。

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
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.image_reverb import ir_metrics, ir_synth  # noqa: E402
from src.image_reverb.acoustics import AcousticsResult, compute_acoustics  # noqa: E402
from src.image_reverb.geometry import RoomEstimate  # noqa: E402
from src.image_reverb.materials import load_materials, parse_surface_spec  # noqa: E402

# T-12 Opus 驗證時對「floor=carpet＋其餘 gypsum_board、4×3×2.5m」完整 pra 模擬
# （image-source 12 階 + ray tracing）獨立量測的 125Hz T30。
# 出處：TASKS.md T-12 卡交接筆記（2026-08-18 實測，Opus 2026-08-25 複核）。
T12_MEASURED_125HZ_S = 0.748

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

    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 項失敗：{'、'.join(FAILURES)}")
        return 1
    print("✅ T-14 閉環迴歸測試全部通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
