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
    args = parser.parse_args(argv)

    error = pipeline.check_mutual_exclusion(args.photo, args.text, args.scene)
    if error is not None:
        parser.print_usage(sys.stderr)
        print(f"錯誤：{error}", file=sys.stderr)
        return 2

    photo_only_flags_used = args.override_dims is not None or args.override_material is not None
    if photo_only_flags_used and args.photo is None:
        print("錯誤：--override-dims/--override-material 只能搭配照片輸入使用", file=sys.stderr)
        return 2

    if args.photo is not None:
        return pipeline.run_photo(
            args.photo, args.override_dims, args.override_material, no_viz=args.no_viz
        )
    if args.text is not None:
        return pipeline.run_text(args.text, no_viz=args.no_viz)
    return pipeline.run_scene(args.scene, no_viz=args.no_viz)


if __name__ == "__main__":
    sys.exit(main())
