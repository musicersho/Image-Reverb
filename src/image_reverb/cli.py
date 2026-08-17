"""T-10：CLI 入口 —— 目前只跑前處理（裁黑邊 / 環景判定 / equirect 投影）。

用法：
    python -m src.image_reverb <photo>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import UnidentifiedImageError

from .preprocess import preprocess_image


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Image Reverb 前處理（T-10）：裁黑邊、判環景、equirect 投影六視角",
    )
    parser.add_argument("photo", help="輸入照片路徑（JPG/PNG/HEIC）")
    args = parser.parse_args(argv)

    photo_path = Path(args.photo)
    if not photo_path.is_file():
        print(f"錯誤：找不到檔案 {photo_path}", file=sys.stderr)
        return 2

    try:
        summary = preprocess_image(photo_path)
    except UnidentifiedImageError:
        print(f"錯誤：無法辨識為圖片檔 {photo_path}", file=sys.stderr)
        return 2

    print(f"輸入：{summary['input']}")
    b = summary["border_crop"]
    print(
        f"黑邊裁切：原始 {b['original_size']} → 裁後 {b['cropped_size']}"
        f"（左{b['crop_left_px']} 右{b['crop_right_px']} 上{b['crop_top_px']} 下{b['crop_bottom_px']} px）"
    )
    print(f"環景判定：{'是' if summary['is_equirect'] else '否'}")
    if summary["is_equirect"]:
        print(f"已輸出 {len(summary['views'])} 個透視視角：")
        for name, v in summary["views"].items():
            print(f"  {name}: 方位角 {v['azimuth_deg']}° 仰角 {v['elevation_deg']}° → {v['path']}")
    else:
        print(f"非環景，僅裁切通過：{summary['cropped']}")
    print(f"中間結果 meta：{summary['meta_path']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
