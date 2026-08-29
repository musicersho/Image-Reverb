#!/usr/bin/env python3
"""T-18 校驗：低頻聯合帶 T30（`ir_metrics.t30_low_combined()`，88.4–353.6Hz）。

跑法：`python scripts/test_t30_low_combined.py`（純合成資料＋固定亂數種子，
不依賴模型下載，任何 clone 都能重跑；全部通過 exit 0，任一失敗 exit 1）。

兩段校驗（比照 Opus 驗證 T-14 時的手法，避免循環論證）：

1. **合成構造校驗**：白噪聲先帶通濾波到 88.4–353.6Hz，再乘上**直接按定義構造**
   的指數衰減包絡（envelope(t) = 10^(-3t/T60)，T60 秒後衰減 60dB，是解析定義，
   不是拿 `t30_low_combined` 自己量出來的值當真值）。分別做 0.5s／2.5s 兩組，
   要求 `t30_low_combined` 量測誤差 ≤10%。
2. **地毯房參考量測**：對 T-14/T-22 交付版的地毯房 IR（4×3×2.5m，
   floor=carpet／walls=gypsum_board——與 `test_ir_synth.py`【2】【6】同一組
   構造參數）量一次聯合帶 T30，記錄數值；只檢查落在合理區間 0.1–12s 內，
   並印出與 125Hz 物理模擬錨點 0.748s（T-12 文件化實測）、250Hz Sabine 目標
   的鄰近程度供人工參考——這步是記錄，不是硬性通過/失敗判準（見 TASKS.md T-18 卡）。
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scipy.signal import butter, sosfiltfilt  # noqa: E402

from src.image_reverb import config, ir_metrics, ir_synth  # noqa: E402
from src.image_reverb.acoustics import compute_acoustics  # noqa: E402
from src.image_reverb.geometry import RoomEstimate  # noqa: E402
from src.image_reverb.materials import load_materials, parse_surface_spec  # noqa: E402

# T-12 物理模擬實測錨點（TASKS.md T-12 卡交接筆記，2026-08-18 實測、Opus 2026-08-25 複核）
T12_MEASURED_125HZ_S = 0.748

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  {'✅' if ok else '❌'} {name}：{detail}")
    if not ok:
        FAILURES.append(name)


def _synthetic_low_band_decay(target_rt60_s: float, fs: int, seed: int) -> np.ndarray:
    """構造已知 RT60 的 88.4–353.6Hz 帶內衰減噪音（獨立於 ir_metrics 的測試用濾波器）。

    做法：白噪聲先帶通到目標頻段，再乘上**解析定義**的指數衰減包絡
    （envelope(t) = 10^(-3t/T60)，T60 秒衰減 60dB，直接按定義構造，
    不是用 ir_metrics 量出來的值反推）。
    """
    duration_s = 2.0 * target_rt60_s + 0.2
    n = int(duration_s * fs)
    rng = np.random.RandomState(seed)
    white = rng.standard_normal(n)

    nyq = fs / 2.0
    lo_hz = 125.0 / np.sqrt(2.0)
    hi_hz = 250.0 * np.sqrt(2.0)
    sos = butter(3, [lo_hz / nyq, hi_hz / nyq], btype="bandpass", output="sos")
    band_limited = sosfiltfilt(sos, white)

    t = np.arange(n) / fs
    envelope = 10.0 ** (-3.0 * t / target_rt60_s)
    return band_limited * envelope


def main() -> int:
    fs = config.IR_SAMPLE_RATE

    # ---------- 1. 合成構造校驗：已知 RT60 → 量測誤差 ≤10% ----------
    print("【1】合成構造校驗（88.4–353.6Hz 帶內衰減噪音，解析包絡定義已知 RT60）")
    for seed, target in ((1001, 0.5), (1002, 2.5)):
        signal = _synthetic_low_band_decay(target, fs, seed)
        measured = ir_metrics.t30_low_combined(signal, fs)
        error = (measured - target) / target
        check(
            f"目標 RT60={target}s 聯合帶量測誤差 ≤10%",
            abs(error) <= 0.10,
            f"量測 {measured:.4f}s，誤差 {error * 100:+.1f}%",
        )

    # ---------- 2. 地毯房參考量測（記錄用，非硬性判準）----------
    print("【2】地毯房參考量測（4×3×2.5m，floor=carpet／walls=gypsum_board）")
    data = load_materials()
    est = RoomEstimate(4.0, 3.0, 2.5, confidence="high", dims_source="manual")
    surf = parse_surface_spec("floor=carpet,walls=gypsum_board", data)
    ac = compute_acoustics(est, surf, data)
    res = ir_synth.synthesize_ir(ac, data)
    combined = ir_metrics.t30_low_combined(res.ir, res.sample_rate)

    idx_250 = ac.band_center_freqs_hz.index(250)
    target_250 = ac.rt60_bands_sabine[idx_250]
    print(
        f"      聯合帶量測 T30 = {combined:.4f}s"
        f"（參考：125Hz 物理模擬錨點 {T12_MEASURED_125HZ_S:.3f}s、"
        f"250Hz Sabine 目標 {target_250:.3f}s）"
    )
    check(
        "聯合帶量測落在合理區間 0.1–12s（WORKFLOW §5）",
        0.1 <= combined <= 12.0,
        f"{combined:.4f}s",
    )

    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 項失敗：{'、'.join(FAILURES)}")
        return 1
    print("✅ T-18 t30_low_combined 校驗全部通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
