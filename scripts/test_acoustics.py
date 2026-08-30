#!/usr/bin/env python3
"""T-13 聲學參數計算迴歸測試 —— 數字直接對照 TASKS.md T-13 卡步驟 5 的實測表。

不依賴任何模型或素材，純公式計算，可在任何 clone 上重跑。

用法：
    python scripts/test_acoustics.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.image_reverb.acoustics import (  # noqa: E402
    air_absorption_per_m,
    compute_acoustics,
    rt60_sabine_band,
    surface_areas_m2,
)
from src.image_reverb.furnishings import (  # noqa: E402
    FurnishingEstimate,
    estimate_furnishings,
    load_furnishings,
)
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


def _synthetic_furnishings(categories: dict) -> FurnishingEstimate:
    total_ratio = sum(v["ratio"] for v in categories.values())
    return FurnishingEstimate(categories=categories, total_ratio=total_ratio, warnings=[], notes=[])


def test_f1_none_identical():
    print("[F1] furnishings=None 與不帶參數呼叫完全相等，as_dict() 無 furnishings 鍵...")
    data = load_materials()
    surfaces = uniform_surfaces("carpet", data)
    est = small_room_estimate()
    result_default = compute_acoustics(est, surfaces, data)
    result_explicit_none = compute_acoustics(est, surfaces, data, furnishings=None)
    if result_default.as_dict() != result_explicit_none.as_dict():
        die("furnishings=None 與不帶參數呼叫的結果不相等")
    if "furnishings" in result_default.as_dict():
        die("furnishings=None 時 as_dict() 不應該有 'furnishings' 鍵")
    print("    OK")


def test_f2_hand_calc():
    print("[F2] 手算對照：加入陳設後 rt60_bands_sabine 應等於手算值（誤差 <1e-9）...")
    data = load_materials()
    surfaces = uniform_surfaces("carpet", data)
    est = small_room_estimate()

    band_freqs, alpha_table = surfaces.alpha_table(data)
    areas = surface_areas_m2(est.length_m, est.width_m, est.height_m)
    total_surface = sum(areas.values())
    air_terms = air_absorption_per_m(band_freqs)

    bed_alpha = [0.30, 0.50, 0.65, 0.75, 0.80, 0.80]  # 裁決 T-27-A 表格的 bed 值
    bed_ratio = 0.12
    furnishings = _synthetic_furnishings({"bed": {"ratio": bed_ratio, "alpha": bed_alpha}})

    result = compute_acoustics(est, surfaces, data, furnishings=furnishings)

    for i, freq in enumerate(band_freqs):
        surfaces_absorption = sum(areas[name] * alpha_table[name][i] for name in areas)
        a_extra = bed_ratio * total_surface * bed_alpha[i]
        air_term = 4.0 * air_terms[i] * est.volume_m3
        expected = rt60_sabine_band(est.volume_m3, surfaces_absorption + a_extra, air_term)
        actual = result.rt60_bands_sabine[i]
        err = abs(actual - expected)
        print(f"    {freq}Hz：手算 {expected:.6f}s　實得 {actual:.6f}s　差 {err:.2e}")
        if err > 1e-9:
            die(f"{freq}Hz 手算與 compute_acoustics() 不符（差 {err:.2e} > 1e-9）")
    print("    OK")


def test_f3_monotonic():
    print("[F3] 加入陳設後六頻段 Sabine／Eyring RT60 全部嚴格下降...")
    data = load_materials()
    surfaces = uniform_surfaces("carpet", data)
    est = small_room_estimate()
    furnishings = _synthetic_furnishings(
        {
            "sofa": {"ratio": 0.08, "alpha": [0.35, 0.50, 0.60, 0.70, 0.70, 0.65]},
            "curtain": {"ratio": 0.05, "alpha": [0.07, 0.31, 0.49, 0.75, 0.70, 0.60]},
        }
    )
    without = compute_acoustics(est, surfaces, data)
    with_furn = compute_acoustics(est, surfaces, data, furnishings=furnishings)
    for i, freq in enumerate(without.band_center_freqs_hz):
        if not (with_furn.rt60_bands_sabine[i] < without.rt60_bands_sabine[i]):
            die(f"{freq}Hz Sabine RT60 加陳設後沒有下降")
        if not (with_furn.rt60_bands_eyring[i] < without.rt60_bands_eyring[i]):
            die(f"{freq}Hz Eyring RT60 加陳設後沒有下降")
    print("    OK（六頻段 Sabine／Eyring 全部嚴格下降）")


def test_f4_cap_scales_down():
    print("[F4] cap 壓回後 A_extra 對應縮小（真實 estimate_furnishings() 整合測試）...")
    data = load_materials()
    surfaces = uniform_surfaces("carpet", data)
    est = small_room_estimate()
    furn_data = load_furnishings()

    # bed(7)=0.30 + sofa(23)=0.30 + curtain(18)=0.20 = 0.80，超過 cap 0.5
    raw_ratios = {7: 0.30, 23: 0.30, 18: 0.20}
    detail = {"class_ratios": {"single": dict(raw_ratios)}}
    furn = estimate_furnishings(detail, furn_data)
    if furn is None:
        die("estimate_furnishings() 不應該回傳 None")
    if abs(furn.total_ratio - 0.5) > 1e-9:
        die(f"cap 應把 total_ratio 壓到 0.5，實得 {furn.total_ratio}")
    if not furn.warnings:
        die("cap 觸發時 FurnishingEstimate.warnings 應該非空")

    result = compute_acoustics(est, surfaces, data, furnishings=furn)
    if result.furnishings is None:
        die("compute_acoustics() 的 furnishings 欄位不應該是 None")
    if not result.furnishings["cap_applied"]:
        die("furnishings['cap_applied'] 應該是 True")

    scale = 0.5 / sum(raw_ratios.values())
    for item in furn_data["furnishings"]:
        if item["ade_id"] not in raw_ratios:
            continue
        expected_ratio = raw_ratios[item["ade_id"]] * scale
        actual_ratio = furn.categories[item["ade_name"]]["ratio"]
        if abs(actual_ratio - expected_ratio) > 1e-9:
            die(
                f"{item['ade_name']} 壓回後 ratio 不符：期望 {expected_ratio}，"
                f"實得 {actual_ratio}"
            )
    print("    OK（總比例 0.80 → 壓回 0.50，cap_applied=True，逐類別 ratio 等比縮小）")


def main():
    test_a_uniform_carpet()
    test_b_floor_carpet_rest_gypsum()
    test_output_shape()
    test_eyring_vs_sabine()
    test_not_hardcoded()
    test_f1_none_identical()
    test_f2_hand_calc()
    test_f3_monotonic()
    test_f4_cap_scales_down()
    print("\n全部通過。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
