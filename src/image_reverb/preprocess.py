"""T-10：影像前處理 —— 黑邊裁切、環景偵測、equirect → 多視角透視投影。

三件事都是純幾何/影像處理，不涉及任何 AI 模型。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pillow_heif
from PIL import Image

from . import config

# 讓 PIL.Image.open 認得 HEIC（F-01 要求支援 JPG/PNG/HEIC）
pillow_heif.register_heif_opener()


def load_image(path: str | Path) -> Image.Image:
    """讀圖並轉成 RGB（含 HEIC，靠上面註冊的 opener）。"""
    return Image.open(path).convert("RGB")


def _row_col_spread(line: np.ndarray) -> float:
    """一列/欄像素亮度的 p90-p10，越接近 0 代表越接近純色（=可能是邊框）。"""
    p10, p90 = np.percentile(line, [10, 90])
    return float(p90 - p10)


def detect_and_crop_border(
    img: Image.Image,
    spread_threshold: float = config.BORDER_SPREAD_THRESHOLD,
    max_crop_ratio: float = config.BORDER_MAX_CROP_RATIO,
) -> tuple[Image.Image, dict[str, Any]]:
    """偵測並裁掉四邊的純色邊框（letterbox/UI 黑邊，不限黑色）。

    地雷第 4 條：判定用「這一列/欄夠不夠純色」（p90-p10 亮度分佈範圍），
    不是「這一列/欄夠不夠暗」——否則會誤裁四周偏暗但有紋理的正常照片
    （例如洞穴照片邊緣：暗但不均勻，p90-p10 明顯偏高，不會被裁）。
    """
    gray = np.asarray(img.convert("L"), dtype=np.float64)
    h, w = gray.shape

    max_left_right = int(w * max_crop_ratio)
    max_top_bottom = int(h * max_crop_ratio)

    left = 0
    while left < max_left_right and _row_col_spread(gray[:, left]) < spread_threshold:
        left += 1

    right = w - 1
    while (w - 1 - right) < max_left_right and _row_col_spread(gray[:, right]) < spread_threshold:
        right -= 1

    top = 0
    while top < max_top_bottom and _row_col_spread(gray[top, :]) < spread_threshold:
        top += 1

    bottom = h - 1
    while (h - 1 - bottom) < max_top_bottom and _row_col_spread(gray[bottom, :]) < spread_threshold:
        bottom -= 1

    crop_box = (left, top, right + 1, bottom + 1)  # PIL box: (left, upper, right, lower)
    cropped = img.crop(crop_box)

    info = {
        "original_size": [w, h],
        "cropped_size": list(cropped.size),
        "crop_left_px": left,
        "crop_right_px": w - 1 - right,
        "crop_top_px": top,
        "crop_bottom_px": h - 1 - bottom,
        "spread_threshold": spread_threshold,
    }
    return cropped, info


def is_equirect(
    img: Image.Image,
    aspect_ratio: float = config.EQUIRECT_ASPECT_RATIO,
    tolerance: float = config.EQUIRECT_ASPECT_TOLERANCE,
) -> bool:
    """只看長寬比是否 ≈ 2:1（容差 ±5%），不看檔名。"""
    w, h = img.size
    ratio = w / h
    return abs(ratio - aspect_ratio) <= aspect_ratio * tolerance


def project_equirect_to_perspectives(
    img: Image.Image,
    views: list[dict] = config.PERSPECTIVE_VIEWS,
    fov_deg: float = config.PERSPECTIVE_FOV_DEG,
    out_size: tuple[int, int] = config.PERSPECTIVE_OUT_SIZE,
) -> dict[str, Image.Image]:
    """equirect → 多視角透視投影（py360convert.e2p，純幾何球面重投影）。"""
    import py360convert

    e_img = np.asarray(img)
    out_w, out_h = out_size

    views_out: dict[str, Image.Image] = {}
    for view in views:
        persp = py360convert.e2p(
            e_img,
            fov_deg=fov_deg,
            u_deg=view["azimuth_deg"],
            v_deg=view["elevation_deg"],
            out_hw=(out_h, out_w),
        )
        views_out[view["name"]] = Image.fromarray(persp.astype(np.uint8))
    return views_out


def preprocess_image(path: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    """跑完整前處理：判環景 → 環景跳過黑邊裁切／非環景才裁 → (環景才)投影六視角。

    地雷第 11 條：equirect 的第一列/最後一列是天頂/天底被拉伸成整列，依定義完全
    均勻，若先裁黑邊會把極點誤判成純色邊框裁掉，靜默破壞投影幾何。因此環景判定
    一律用**原圖**；一旦判定為環景，完全跳過黑邊裁切（equirect 是完整球面渲染，
    本來就不會有 letterbox）。
    """
    path = Path(path)
    output_dir = Path(output_dir) if output_dir is not None else config.OUTPUT_DIR
    stem_dir = output_dir / path.stem
    stem_dir.mkdir(parents=True, exist_ok=True)

    img = load_image(path)
    equirect = is_equirect(img)

    if equirect:
        cropped = img
        w, h = img.size
        border_info: dict[str, Any] = {
            "original_size": [w, h],
            "cropped_size": [w, h],
            "crop_left_px": 0,
            "crop_right_px": 0,
            "crop_top_px": 0,
            "crop_bottom_px": 0,
            "spread_threshold": config.BORDER_SPREAD_THRESHOLD,
            "skipped_equirect": True,
        }
    else:
        cropped, border_info = detect_and_crop_border(img)

    summary: dict[str, Any] = {
        "input": str(path),
        "border_crop": border_info,
        "is_equirect": equirect,
    }

    if equirect:
        cropped_path = stem_dir / "cropped_equirect.png"
        cropped.save(cropped_path)
        views = project_equirect_to_perspectives(cropped)
        view_files = {}
        for view_meta in config.PERSPECTIVE_VIEWS:
            name = view_meta["name"]
            out_path = stem_dir / f"view_{name}.png"
            views[name].save(out_path)
            view_files[name] = {
                "path": str(out_path),
                "azimuth_deg": view_meta["azimuth_deg"],
                "elevation_deg": view_meta["elevation_deg"],
                "fov_deg": config.PERSPECTIVE_FOV_DEG,
            }
        summary["cropped_equirect"] = str(cropped_path)
        summary["views"] = view_files
    else:
        cropped_path = stem_dir / "cropped.png"
        cropped.save(cropped_path)
        summary["cropped"] = str(cropped_path)

    meta_path = stem_dir / "meta.json"
    meta_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    summary["meta_path"] = str(meta_path)

    return summary
