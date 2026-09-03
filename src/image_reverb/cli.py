"""Image Reverb CLI 入口（T-15：三條管線的統一入口）。

三種輸入互斥：
    python -m src.image_reverb <photo>
    python -m src.image_reverb --text "場景描述"
    python -m src.image_reverb --scene <場景.json>

照片路徑額外支援手動覆寫（F-09）：
    python -m src.image_reverb <photo> --override-dims 4x3x2.5
    python -m src.image_reverb <photo> --override-material floor=carpet --override-material walls=gypsum_board

輸出到 `output/<name>/`：`ir_mono.wav`、`ir_stereo.wav`（複合場景 v1 只出 mono）、
`analysis.json`（統一 schema）、`wet_preview.wav`（照片/文字 mix=0.6，複合場景 mix=1.0）、
`analysis.png`（T-16 視覺化拼版，預設產生，`--no-viz` 可關）。

三條管線各自的核心邏輯（T-10~T-14、T-20 `scene_text.py`、T-21 `coupled.py`）完全不動，
本檔與 `pipeline.py` 只負責路由與統一輸出格式，詳見 `pipeline.py` 模組說明。
"""

from __future__ import annotations

import argparse
import sys

from . import pipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Image Reverb：照片／文字／複合場景 → IR + 分析報告（三種輸入互斥）",
    )
    parser.add_argument(
        "photo", nargs="?", default=None, help="輸入照片路徑（JPG/PNG/HEIC；與 --text/--scene 互斥）"
    )
    parser.add_argument(
        "--text", default=None, metavar="描述", help="文字場景描述（F-16；與 photo/--scene 互斥）"
    )
    parser.add_argument(
        "--scene", default=None, metavar="JSON", help="複合場景 JSON 檔路徑（F-17；與 photo/--text 互斥）"
    )
    parser.add_argument(
        "--override-dims",
        default=None,
        metavar="LxWxH",
        help="（僅照片輸入）手動指定房間尺寸（公尺），例如 4x3x2.5，完全不跑深度模型（F-09）",
    )
    parser.add_argument(
        "--override-material",
        action="append",
        default=None,
        metavar="面=材質id",
        help="（僅照片輸入）覆寫單一面的材質，可重複給多次，例如 "
        "--override-material floor=carpet --override-material walls=gypsum_board（F-09）",
    )
    parser.add_argument(
        "--no-viz",
        action="store_true",
        help="不產生 analysis.png（T-16；預設會產生）",
    )
    parser.add_argument(
        "--force-low-confidence",
        action="store_true",
        help="（僅照片輸入）overall confidence 為 low 時預設會擋下輸出（T-26），"
        "加這個旗標可強制照樣輸出，結果會在 analysis.json 標記"
        "forced_low_confidence=true 並留下警告",
    )
    parser.add_argument(
        "--furnishings",
        action="store_true",
        help="（僅照片輸入）預設只偵測室內陳設（床/沙發/窗簾等）並寫進 "
        "analysis.json（applied=false，不套用聲學計算）——T-33 實測套用對 "
        "§7-2 達標率淨效果為負（見 output/material_round/REPORT.md §4.2），"
        "裁決 T-33-A 改為 opt-in；加這個旗標才會把偵測結果換算成等效吸音面積"
        "算進聲學計算（T-32，裁決 T-27-A 的原始行為）。與 --no-furnishings 互斥",
    )
    parser.add_argument(
        "--no-furnishings",
        action="store_true",
        help="（僅照片輸入）連室內陳設偵測都跳過（預設仍會偵測，只是不套用），"
        "用於 A/B 對照或陳設偵測結果有問題時的退路。與 --furnishings 互斥",
    )
    parser.add_argument(
        "--role-aware",
        action="store_true",
        help="實驗性：T-44 role-aware 候選子集，產品採用暫停（裁決 T-45-A）；預設關閉",
    )
    args = parser.parse_args(argv)

    error = pipeline.check_mutual_exclusion(args.photo, args.text, args.scene)
    if error is not None:
        parser.print_usage(sys.stderr)
        print(f"錯誤：{error}", file=sys.stderr)
        return 2

    if args.furnishings and args.no_furnishings:
        print(
            "錯誤：--furnishings 與 --no-furnishings 互斥，不能同時使用",
            file=sys.stderr,
        )
        return 2

    photo_only_flags_used = (
        args.override_dims is not None
        or args.override_material is not None
        or args.force_low_confidence
        or args.furnishings
        or args.no_furnishings
        or args.role_aware
    )
    if photo_only_flags_used and args.photo is None:
        print(
            "錯誤：--override-dims/--override-material/--force-low-confidence/"
            "--furnishings/--no-furnishings/--role-aware 只能搭配照片輸入使用",
            file=sys.stderr,
        )
        return 2

    if args.photo is not None:
        return pipeline.run_photo(
            args.photo,
            args.override_dims,
            args.override_material,
            no_viz=args.no_viz,
            force_low_confidence=args.force_low_confidence,
            furnishings=args.furnishings,
            no_furnishings=args.no_furnishings,
            role_aware=args.role_aware,
        )
    if args.text is not None:
        return pipeline.run_text(args.text, no_viz=args.no_viz)
    return pipeline.run_scene(args.scene, no_viz=args.no_viz)


if __name__ == "__main__":
    sys.exit(main())
