"""T-14：IR 量測模組 —— 逐頻段 T30（Schroeder 積分）。

**這個檔案刻意與合成程式碼（ir_synth.py）分離**，是 T-14 卡明列的 Opus 紅旗對策：
量測函式必須自己從 IR 波形量出衰減時間，不得讀取、參考或回傳合成端的目標值。
本模組 import 不到任何合成端的東西（只用 numpy/scipy），也不吃 AcousticsResult。

量測方法（與 T-12 Opus 驗證時獨立實作的方法一致）：
1. 對 IR 做八度頻段 Butterworth 帶通濾波（零相位 sosfiltfilt，避免濾波器群延遲偏移衰減曲線）
2. Schroeder 反向積分：E(t) = Σ_{τ≥t} x²(τ)，取 dB
3. 在 -5 dB → -35 dB 區間做線性迴歸，斜率外推到 60 dB 衰減 → T30
"""

from __future__ import annotations

import math

import numpy as np
from scipy.signal import butter, sosfiltfilt

# T30 迴歸的衰減區間（dB，相對於 Schroeder 曲線起點）
_FIT_START_DB = -5.0
_FIT_END_DB = -35.0


def _bandpass_sos(center_hz: float, fs: int, order: int = 3) -> np.ndarray:
    """單一八度頻段的 Butterworth 帶通（頻寬 = 中心頻率 ×/÷ √2）。"""
    lo = center_hz / math.sqrt(2.0)
    hi = center_hz * math.sqrt(2.0)
    nyq = fs / 2.0
    if hi >= nyq:
        hi = nyq * 0.98  # 頻段上緣貼到 Nyquist 時往內收，避免濾波器設計失敗
    return butter(order, [lo / nyq, hi / nyq], btype="bandpass", output="sos")


def schroeder_curve_db(band_signal: np.ndarray) -> np.ndarray:
    """Schroeder 反向積分衰減曲線（dB，0 dB = 曲線起點）。"""
    energy = np.cumsum(band_signal[::-1] ** 2)[::-1]
    total = energy[0]
    if total <= 0.0:
        raise ValueError("頻段訊號能量為 0，無法計算衰減曲線")
    with np.errstate(divide="ignore"):
        curve = 10.0 * np.log10(energy / total)
    return curve


def t30_from_curve(curve_db: np.ndarray, fs: int) -> float:
    """在 -5 → -35 dB 區間做線性迴歸，外推 60 dB 衰減時間（T30 定義）。"""
    idx = np.where((curve_db <= _FIT_START_DB) & (curve_db >= _FIT_END_DB))[0]
    if len(idx) < 8:
        raise ValueError(
            f"衰減曲線在 {_FIT_START_DB}→{_FIT_END_DB} dB 區間只有 {len(idx)} 個樣本，"
            f"IR 太短或被截尾，T30 不可量測"
        )
    t = idx / fs
    slope, _ = np.polyfit(t, curve_db[idx], 1)
    if slope >= 0.0:
        raise ValueError("衰減曲線斜率非負（訊號沒有在衰減），T30 不可量測")
    return -60.0 / slope


def band_t30(ir: np.ndarray, fs: int, band_freqs: list[int]) -> list[float]:
    """對整條 IR 量各頻段 T30（秒）。

    **對整條 IR 做**，不裁掉早期——T-14 卡明列的紅旗：不得為了讓閉環誤差過關
    而把量測窗調到只量晚期尾巴。
    """
    ir = np.asarray(ir, dtype=np.float64)
    if ir.ndim != 1:
        raise ValueError(f"只支援 mono IR（收到 shape={ir.shape}）")
    results = []
    for freq in band_freqs:
        sos = _bandpass_sos(float(freq), fs)
        band_signal = sosfiltfilt(sos, ir)
        curve = schroeder_curve_db(band_signal)
        results.append(t30_from_curve(curve, fs))
    return results


def closed_loop_report(
    ir: np.ndarray,
    fs: int,
    band_freqs: list[int],
    rt60_targets: list[float],
    tolerance: float = 0.20,
    plausible_min_s: float = 0.1,
    plausible_max_s: float = 12.0,
) -> dict:
    """閉環驗證報告：量測 T30 vs 目標值，逐頻段誤差與合理區間警示。

    回傳 dict 給合成端寫進 JSON。誤差 = (量測 − 目標) / 目標。
    """
    measured = band_t30(ir, fs, band_freqs)
    bands = []
    warnings: list[str] = []
    all_within = True
    for freq, target, meas in zip(band_freqs, rt60_targets, measured):
        # 統一轉回 Python 原生型別——numpy 的 float64/bool_ 進不了 json.dumps
        target = float(target)
        meas = float(meas)
        error = (meas - target) / target
        within = bool(abs(error) <= tolerance)
        all_within = all_within and within
        bands.append(
            {
                "freq_hz": int(freq),
                "rt60_target_s": round(target, 4),
                "t30_measured_s": round(meas, 4),
                "error_pct": round(error * 100.0, 1),
                "within_tolerance": within,
            }
        )
        if not within:
            warnings.append(
                f"{freq} Hz 量測 T30 {meas:.3f}s 與目標 {target:.3f}s 誤差 "
                f"{error * 100.0:+.1f}%，超出 ±{tolerance * 100.0:.0f}%"
            )
        if not (plausible_min_s <= meas <= plausible_max_s):
            warnings.append(
                f"{freq} Hz 量測 T30 {meas:.3f}s 超出合理區間 "
                f"{plausible_min_s}–{plausible_max_s}s（WORKFLOW §5），結果可疑，請人工確認"
            )
    return {
        "tolerance_pct": tolerance * 100.0,
        "all_within_tolerance": all_within,
        "bands": bands,
        "warnings": warnings,
    }
