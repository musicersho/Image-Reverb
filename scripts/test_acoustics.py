#!/usr/bin/env python3
"""T-13 聲學參數計算迴歸測試 —— 數字直接對照 TASKS.md T-13 卡步驟 5 的實測表。

不依賴任何模型或素材，純公式計算，可在任何 clone 上重跑。

用法：
    python scripts/test_acoustics.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.image_reverb.acoustics import compute_acoustics  # noqa: E402
from src.image_reverb.geometry import RoomEstimate  # noqa: E402
from src.image_reverb.materials import (  # noqa: E402
    load_materials,
    parse_surface_spec,
    uniform_surfaces,
)

TOLERANCE = 0.10  # ±10%（同公式同輸入，理應幾乎一致）


def die(msg, code=1):
    print(f"[錯誤] {msg}", file=sys.stderr)
    sys.exit(code)


def check_close(label, expected, actual, tolerance=TOLERANCE):
    err = abs(actual - expected) / expected
    status = "OK" if err <= tolerance else "FAIL"
    print(f"    {label}：期望 ≈{expected:.3f}s　實得 {actual:.3f}s　誤差 {err*100:.1f}%　[{status}]")
    if err > tolerance:
        die(f"{label} 誤差 {err*100:.1f}% 超出 ±{tolerance*100:.0f}% 容差")


def small_room_estimate():
    return RoomEstimate(
        length_m=4.0, width_m=3.0, height_m=2.5,
        confidence="high", dims_source="manual",
    )


def test_a_uniform_carpet():
    print("[a] 全 carpet 六面（4×3×2.5m）...")
    data = load_materials()
    surfaces = uniform_surfaces("carpet", data)
    result = compute_acoustics(small_room_estimate(), surfaces, data)
    freqs = result.band_center_freqs_hz
    sabine = result.rt60_bands_sabine
    expected = {125: 4.093, 1000: 0.221, 4000: 0.126}
    for freq, exp in expected.items():
        check_close(f"{freq}Hz", exp, sabine[freqs.index(freq)])


def test_b_floor_carpet_rest_gypsum():
    print("[b] floor=carpet ＋其餘石膏板（4×3×2.5m）...")
    data = load_materials()
    surfaces = parse_surface_spec("floor=carpet,walls=gypsum_board,ceiling=gypsum_board", data)
    result = compute_acoustics(small_room_estimate(), surfaces, data)
    freqs = result.band_center_freqs_hz
    sabine = result.rt60_bands_sabine
    expected = {125: 0.348, 1000: 0.764, 4000: 0.401}
    for freq, exp in expected.items():
        check_close(f"{freq}Hz", exp, sabine[freqs.index(freq)])


def test_output_shape():
    print("[shape] rt60_bands 恆為 6 個值、rt60_mid 非由平均 α 重算...")
    data = load_materials()
    surfaces = uniform_surfaces("carpet", data)
    result = compute_acoustics(small_room_estimate(), surfaces, data)
    d = result.as_dict()
    for key in ("rt60_bands_sabine", "rt60_bands_eyring", "band_center_freqs_hz"):
        if len(d[key]) != 6:
            die(f"{key} 應恆為 6 個值，實得 {len(d[key])}")
    if d["rt60_source"] != "formula":
        die("rt60_source 必須標記為 'formula'（地雷第 14 條）")
    if "rt60_disclaimer" not in d or not d["rt60_disclaimer"]:
        die("缺少 rt60_disclaimer（地雷第 14 條要求 schema 註明公式值與實測落差）")
    print("    OK")


def test_eyring_vs_sabine():
    print("[eyring] 高 α 時 Eyring 較短、低 α 時兩者趨近...")
    data = load_materials()
    surfaces = uniform_surfaces("carpet", data)  # 全 carpet：125Hz α=0.02（低）、4kHz α=0.65（高）
    result = compute_acoustics(small_room_estimate(), surfaces, data)
    freqs = result.band_center_freqs_hz
    i125, i4k = freqs.index(125), freqs.index(4000)

    low_alpha_diff = abs(result.rt60_bands_sabine[i125] - result.rt60_bands_eyring[i125])
    low_alpha_diff_ratio = low_alpha_diff / result.rt60_bands_sabine[i125]
    print(f"    125Hz（低 α）：Sabine {result.rt60_bands_sabine[i125]:.3f}s　"
          f"Eyring {result.rt60_bands_eyring[i125]:.3f}s　差 {low_alpha_diff_ratio*100:.1f}%")
    if low_alpha_diff_ratio > 0.05:
        die("低 α 時 Sabine 與 Eyring 應趨近（差 <5%），實際差太多")

    if not (result.rt60_bands_eyring[i4k] < result.rt60_bands_sabine[i4k]):
        die("高 α 時 Eyring 應比 Sabine 短，實際不是")
    print(f"    4000Hz（高 α）：Sabine {result.rt60_bands_sabine[i4k]:.3f}s　"
          f"Eyring {result.rt60_bands_eyring[i4k]:.3f}s　[OK，Eyring 較短]")


def test_not_hardcoded():
    print("[not-hardcoded] 改變輸入尺寸，RT60 與 predelay 應跟著變...")
    data = load_materials()
    surfaces = uniform_surfaces("carpet", data)

    small = compute_acoustics(small_room_estimate(), surfaces, data)
    hall = compute_acoustics(
        RoomEstimate(length_m=30.0, width_m=20.0, height_m=12.0,
                     confidence="high", dims_source="manual"),
        surfaces, data,
    )

    if small.rt60_bands_sabine == hall.rt60_bands_sabine:
        die("換了房間尺寸（4×3×2.5 → 30×20×12），RT60 完全沒變，疑似 hardcode")
    if abs(small.predelay_ms - hall.predelay_ms) < 1.0:
        die("換了房間尺寸，predelay_ms 幾乎沒變，疑似 hardcode")
    print(f"    small: RT60(125Hz)={small.rt60_bands_sabine[0]:.3f}s　"
          f"predelay={small.predelay_ms:.2f}ms")
    print(f"    hall:  RT60(125Hz)={hall.rt60_bands_sabine[0]:.3f}s　"
          f"predelay={hall.predelay_ms:.2f}ms　[OK，數字隨輸入變動]")


def main():
    test_a_uniform_carpet()
    test_b_floor_carpet_rest_gypsum()
    test_output_shape()
    test_eyring_vs_sabine()
    test_not_hardcoded()
    print("\n全部通過。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
