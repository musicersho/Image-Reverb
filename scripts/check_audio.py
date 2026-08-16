#!/usr/bin/env python3
"""檢查音訊檔的基本資訊：取樣率、長度、聲道數、RMS、峰值。"""

import sys
from pathlib import Path

import numpy as np
import soundfile as sf


def check_audio(path):
    # soundfile 對「檔案不存在」拋的是泛用的 LibsndfileError（System error），
    # 訊息看不出是路徑打錯，所以先自己判斷存在性再交給 sf.read。
    if not Path(path).exists():
        print(f"❌ 錯誤：找不到檔案「{path}」")
        sys.exit(1)

    try:
        data, samplerate = sf.read(path, always_2d=True)
    except sf.LibsndfileError as e:
        # 檔案存在但讀不了（例如不是音訊格式、格式不支援）：印出真正的原因
        print(f"❌ 錯誤：無法讀取「{path}」（{e}）")
        sys.exit(1)

    frames, channels = data.shape
    duration = frames / samplerate
    rms = float(np.sqrt(np.mean(np.square(data))))
    peak = float(np.max(np.abs(data)))

    print(f"檔案：{path}")
    print(f"取樣率：{samplerate} Hz")
    print(f"長度：{duration:.3f} 秒")
    print(f"聲道數：{channels}")
    print(f"RMS：{rms:.6f}")
    print(f"峰值：{peak:.6f}")

    if rms < 0.0001:
        print("⚠️ 近乎靜音")


def main():
    if len(sys.argv) != 2:
        print("用法：python scripts/check_audio.py <音訊檔路徑>")
        sys.exit(0)

    check_audio(sys.argv[1])


if __name__ == "__main__":
    main()
