#!/usr/bin/env python3
"""離線卷積試聽工具：乾聲 + IR → 濕聲 WAV。

用法：
    python scripts/convolve.py <dry.wav> <ir.wav> <out.wav> [--mix 0.5]

說明：
    --mix 控制乾濕比，0 = 全乾、1 = 全濕，預設 0.5。
    取樣率不同時會自動重採樣對齊，mono / stereo 也會自動處理。
    輸出峰值正規化到 -1 dBFS 防爆音。
"""

import argparse
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import fftconvolve, resample_poly

# 目標峰值：-1 dBFS
TARGET_PEAK = 10.0 ** (-1.0 / 20.0)


def load_audio(path):
    """讀取音訊檔，一律回傳 (frames, channels) 的 float64 陣列與取樣率。"""
    # soundfile 對「檔案不存在」拋的是泛用的 LibsndfileError（System error），
    # 訊息看不出是路徑打錯，所以先自己判斷存在性再交給 sf.read。
    if not Path(path).exists():
        print(f"❌ 錯誤：找不到檔案「{path}」")
        sys.exit(1)

    try:
        data, samplerate = sf.read(path, always_2d=True, dtype="float64")
    except sf.LibsndfileError as e:  # 檔案存在但讀取失敗，要讓使用者看到真正的原因
        print(f"❌ 錯誤：無法讀取「{path}」（{e}）")
        sys.exit(1)

    if data.shape[0] == 0:
        print(f"❌ 錯誤：「{path}」沒有任何取樣點")
        sys.exit(1)

    return data, samplerate


def resample_to(data, src_rate, dst_rate):
    """把 (frames, channels) 的音訊重採樣到目標取樣率。"""
    if src_rate == dst_rate:
        return data

    ratio = Fraction(dst_rate, src_rate).limit_denominator(1000)
    up, down = ratio.numerator, ratio.denominator
    # resample_poly 沿著 axis=0（時間軸）處理，各聲道獨立
    resampled = resample_poly(data, up, down, axis=0)
    print(f"🔄 重採樣：{src_rate} Hz → {dst_rate} Hz（up={up}, down={down}）")
    return resampled


def match_channels(dry, ir):
    """對齊乾聲與 IR 的聲道數，回傳 (dry, ir, 輸出聲道數)。"""
    dry_ch = dry.shape[1]
    ir_ch = ir.shape[1]
    out_ch = max(dry_ch, ir_ch)

    # 單聲道複製成多聲道；聲道數不一致又都 >1 時，取平均後再複製
    def expand(x, name):
        ch = x.shape[1]
        if ch == out_ch:
            return x
        if ch == 1:
            print(f"🔀 {name}：mono → {out_ch} 聲道（複製）")
            return np.repeat(x, out_ch, axis=1)
        print(f"🔀 {name}：{ch} 聲道 → {out_ch} 聲道（先混成 mono 再複製）")
        mono = x.mean(axis=1, keepdims=True)
        return np.repeat(mono, out_ch, axis=1)

    return expand(dry, "乾聲"), expand(ir, "IR"), out_ch


def convolve_signals(dry, ir):
    """逐聲道做 FFT 卷積，回傳 (frames, channels) 的濕聲。"""
    out_len = dry.shape[0] + ir.shape[0] - 1
    wet = np.zeros((out_len, dry.shape[1]), dtype="float64")
    for ch in range(dry.shape[1]):
        wet[:, ch] = fftconvolve(dry[:, ch], ir[:, ch], mode="full")
    return wet


def normalize_peak(data, target=TARGET_PEAK):
    """峰值正規化到目標值（預設 -1 dBFS）。全靜音時原樣回傳。"""
    peak = float(np.max(np.abs(data)))
    if peak <= 0.0:
        print("⚠️ 訊號全為零，略過正規化")
        return data
    return data * (target / peak)


def main():
    parser = argparse.ArgumentParser(
        description="離線卷積試聽工具：乾聲 + IR → 濕聲 WAV"
    )
    parser.add_argument("dry", help="乾聲 WAV 檔路徑")
    parser.add_argument("ir", help="Impulse Response WAV 檔路徑")
    parser.add_argument("out", help="輸出 WAV 檔路徑")
    parser.add_argument(
        "--mix",
        type=float,
        default=0.5,
        help="乾濕比：0 = 全乾、1 = 全濕（預設 0.5）",
    )
    args = parser.parse_args()

    if not 0.0 <= args.mix <= 1.0:
        print(f"❌ 錯誤：--mix 必須在 0 到 1 之間，收到 {args.mix}")
        sys.exit(1)

    dry, dry_sr = load_audio(args.dry)
    ir, ir_sr = load_audio(args.ir)
    print(f"乾聲：{args.dry}（{dry_sr} Hz, {dry.shape[1]} ch, {dry.shape[0]} samples）")
    print(f"IR  ：{args.ir}（{ir_sr} Hz, {ir.shape[1]} ch, {ir.shape[0]} samples）")

    # 取樣率對齊：一律以較高的取樣率為準，避免降頻損失高頻
    target_sr = max(dry_sr, ir_sr)
    dry = resample_to(dry, dry_sr, target_sr)
    ir = resample_to(ir, ir_sr, target_sr)

    # 聲道對齊
    dry, ir, out_ch = match_channels(dry, ir)

    # 卷積
    wet = convolve_signals(dry, ir)

    # 乾聲補零到與濕聲同長，才能逐點混音
    dry_padded = np.zeros_like(wet)
    dry_padded[: dry.shape[0], :] = dry

    # 乾濕混音後正規化
    mixed = (1.0 - args.mix) * dry_padded + args.mix * wet
    mixed = normalize_peak(mixed)

    sf.write(args.out, mixed, target_sr, subtype="PCM_24")

    duration = mixed.shape[0] / target_sr
    peak = float(np.max(np.abs(mixed)))
    rms = float(np.sqrt(np.mean(np.square(mixed))))
    print(f"✅ 已輸出：{args.out}")
    print(
        f"   取樣率 {target_sr} Hz、{out_ch} 聲道、長度 {duration:.3f} 秒、"
        f"mix={args.mix}"
    )
    print(f"   峰值 {peak:.6f}（{20 * np.log10(peak):.2f} dBFS）、RMS {rms:.6f}")


if __name__ == "__main__":
    main()
