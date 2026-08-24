"""Image Reverb CLI 入口。

T-10：前處理（裁黑邊 / 環景判定 / equirect 投影六視角）
T-11：--geometry 幾何估計（metric depth → 房間尺寸），--override-dims 手動覆寫
T-12：--materials-detect 逐表面材質辨識（ADE20K 幾何角色 + CLIP 材質分類）

用法：
    python -m src.image_reverb <photo>
    python -m src.image_reverb <photo> --geometry
    python -m src.image_reverb <photo> --geometry --override-dims 4x3x2.5
    python -m src.image_reverb <photo> --geometry --materials-detect
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import UnidentifiedImageError

from . import config
from .preprocess import preprocess_image


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Image Reverb：照片 → 空間幾何與材質分析",
    )
    parser.add_argument("photo", help="輸入照片路徑（JPG/PNG/HEIC）")
    parser.add_argument(
        "--geometry",
        action="store_true",
        help="跑 T-11 幾何估計（metric depth → 房間長寬高/體積）",
    )
    parser.add_argument(
        "--override-dims",
        default=None,
        metavar="LxWxH",
        help="手動指定房間尺寸（公尺），例如 4x3x2.5。"
        "指定後**完全不跑深度模型**，下游一律用這個值，輸出標記 dims_source=manual（F-09）",
    )
    parser.add_argument(
        "--materials-detect",
        action="store_true",
        help="跑 T-12 逐表面材質辨識（ADE20K 取幾何角色 + CLIP 判材質）",
    )
    args = parser.parse_args(argv)

    photo_path = Path(args.photo)
    if photo_path.is_dir():
        print(f"錯誤：{photo_path} 是資料夾，請指定單一圖片檔", file=sys.stderr)
        return 2
    if not photo_path.is_file():
        print(f"錯誤：找不到檔案 {photo_path}", file=sys.stderr)
        return 2

    # --override-dims 的格式錯誤要在跑任何模型之前就攔下來
    override = None
    if args.override_dims is not None:
        from .geometry import parse_override_dims

        try:
            override = parse_override_dims(args.override_dims)
        except ValueError as e:
            print(f"錯誤：{e}", file=sys.stderr)
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
        + ("　※環景，依定義跳過裁切" if b.get("skipped_equirect") else "")
    )
    print(f"環景判定：{'是' if summary['is_equirect'] else '否'}")
    if summary["is_equirect"]:
        print(f"已輸出 {len(summary['views'])} 個透視視角：")
        for name, v in summary["views"].items():
            print(f"  {name}: 方位角 {v['azimuth_deg']}° 仰角 {v['elevation_deg']}° → {v['path']}")
    else:
        print(f"非環景，僅裁切通過：{summary['cropped']}")
    print(f"中間結果 meta：{summary['meta_path']}")

    # ---------------- T-12：逐表面材質辨識 ----------------
    scene_cues: dict[str, float] = {}
    if args.materials_detect:
        from PIL import Image

        from . import surfaces as S

        print("\n=== T-12 逐表面材質辨識 ===")
        surf, detail = S.surfaces_from_preprocess(summary)
        for name, mid in surf.as_dict().items():
            print(f"  {name:<8} → {mid:<16}（來源：{surf.sources.get(name, '-')}）")
        if surf.warnings:
            print("  ⚠️ 警示：")
            for w in surf.warnings:
                print(f"    - {w}")
        out = S.save_detail(
            detail, surf, config.SURFACES_OUTPUT_DIR / photo_path.stem / "surfaces.json"
        )
        print(f"  明細已存：{out}")

        # 給 T-11 當場景線索（域外偵測 = 不是建築空間 → 幾何也不該有信心）
        if not summary["is_equirect"]:
            img = Image.open(summary["cropped"]).convert("RGB")
            _, ratios = S.segment_roles(img, *S._load_segmenter())
            ood = [
                v for v in detail["views"].get("single", {}).values()
                if v.get("method") == "out_of_domain"
            ]
            scene_cues = {
                "floor_pixel_ratio": ratios.get(3, 0.0) + ratios.get(28, 0.0),
                "person_pixel_ratio": ratios.get(12, 0.0),
                "out_of_domain": bool(ood),
                "out_of_domain_label": (
                    ood[0]["top3"][0][0].lstrip("_") if ood and ood[0].get("top3") else ""
                ),
            }

    # ---------------- T-11：幾何估計 ----------------
    if args.geometry or override is not None:
        from . import geometry as G

        print("\n=== T-11 幾何估計 ===")
        if override is not None:
            print(f"（--override-dims 已指定，跳過深度模型）")
        est = G.estimate_room(summary, override_dims=override, scene_cues=scene_cues or None)
        d = est.as_dict()
        print(f"  房間尺寸：{d['length_m']}×{d['width_m']}×{d['height_m']} m"
              f"（體積 {d['volume_m3']} m³）")
        print(f"  信心：{d['confidence']}　尺寸來源：{d['dims_source']}")
        if d["depth_stats"].get("p95_m") is not None:
            s_ = d["depth_stats"]
            print(f"  深度統計（公尺）：p5={s_['p5_m']} p50={s_['p50_m']} p95={s_['p95_m']}")
        for n in d["notes"]:
            print(f"  - {n}")
        if d["confidence"] == "low":
            print("  ⚠️ confidence: low —— 這組尺寸不可信，請用 --override-dims 手動指定（F-09）。")
        out = G.save_estimate(est, config.GEOMETRY_OUTPUT_DIR / photo_path.stem / "geometry.json")
        print(f"  結果已存：{out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
