"""T-16：分析視覺化 —— 三種輸入各自的拼版 PNG（F-08）。

**只讀 `analysis.json`（及其同目錄的 `ir_mono.json`）已比對過的欄位畫圖，不重算任何
目標值/量測值**（地雷 #15 通則、T-16 卡 🔮 2026-08-30 記錄）：PNG 上出現的每一個
數字（尺寸、體積、confidence、pre-delay、RT60 target/measured、warnings 文字）都是
直接從這兩份既有 JSON 讀出來的，不在本檔重新計算。

唯一的例外是**像素圖**（分割疊色圖、深度圖）：`analysis.json` 沒有存原始的
labelmap/深度陣列，這兩張圖需要重新跑一次 T-11 的深度模型與 T-12 的 ADE20K
分割模型才能拿到像素資料——這是「為了畫圖重跑模型」，不是「為了改數字重算」，
重跑的結果只拿來上色/疊圖，PNG 上的文字標籤（材質名、α@1kHz）仍然是從
`analysis.json['surfaces']` 查 `data/materials.json` 得到的既定材質 id，
不是從這次重跑的分割結果反推。`pipeline.py` 的 `run_photo()` 本來就會為了場景線索
（`scene_cues`）重跑一次 `segment_roles()`，這裡的作法與既有模式一致。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from . import config
from .materials import get_material, load_materials

# macOS 內建的中文字型（依序嘗試，找不到就退回 matplotlib 預設，中文會變成方框但不會壞掉）
_CJK_FONTS = ["PingFang HK", "Heiti TC", "STHeiti", "Arial Unicode MS", "Songti SC", "sans-serif"]

_WARN_COLOR = "#c0392b"
_OK_COLOR = "#2e7d32"
_TARGET_COLOR = "#5b8def"
_MEASURED_OK_COLOR = "#e67e22"

_ROLE_COLORS = {
    "floor": np.array([0.15, 0.45, 0.90]),
    "ceiling": np.array([0.20, 0.75, 0.35]),
    "wall": np.array([0.95, 0.55, 0.10]),
}


def _setup_fonts() -> None:
    plt.rcParams["font.sans-serif"] = _CJK_FONTS
    # `family="monospace"` 預設會選到 DejaVu Sans Mono（沒有 CJK 字形，中文變空白方框）；
    # 把中文字型也塞進 monospace 候選清單，數字/英文仍走等寬字，中文借用 sans 字型渲染。
    plt.rcParams["font.monospace"] = _CJK_FONTS + ["DejaVu Sans Mono"]
    plt.rcParams["axes.unicode_minus"] = False


def _alpha_at(material_id: str, materials_data: dict[str, Any], freq_hz: int = 1000) -> float | None:
    mat = get_material(material_id, materials_data)
    return mat["alpha"].get(str(freq_hz))


def _material_label(role: str, material_id: str | None, materials_data: dict[str, Any]) -> str:
    if not material_id:
        return role
    mat = get_material(material_id, materials_data)
    a1k = _alpha_at(material_id, materials_data)
    return f"{role}\n{mat['name_zh']}\nα@1kHz={a1k}"


def _rt60_bar_ax(
    ax,
    band_freqs: list[int],
    target: list[float],
    measured: list[float] | None = None,
    within: list[bool] | None = None,
    title: str = "六頻段 RT60（Sabine 目標）",
) -> None:
    """畫六頻段 RT60 長條圖；有 measured 就 target/measured 並排，超差頻段標紅。"""
    x = np.arange(len(band_freqs))
    labels = [str(f) for f in band_freqs]

    if measured is None:
        ax.bar(x, target, color=_TARGET_COLOR, width=0.55)
        for i, v in enumerate(target):
            ax.text(x[i], v, f"{v:.2f}", ha="center", va="bottom", fontsize=7)
    else:
        w = 0.35
        ax.bar(x - w / 2, target, width=w, color=_TARGET_COLOR, label="target (Sabine)")
        colors = [
            _MEASURED_OK_COLOR if (within is None or within[i]) else _WARN_COLOR
            for i in range(len(measured))
        ]
        ax.bar(x + w / 2, measured, width=w, color=colors, label="measured (T30)")
        for i, v in enumerate(target):
            ax.text(x[i] - w / 2, v, f"{v:.2f}", ha="center", va="bottom", fontsize=6.5)
        for i, v in enumerate(measured):
            ax.text(x[i] + w / 2, v, f"{v:.2f}", ha="center", va="bottom", fontsize=6.5)
        ax.legend(fontsize=7, loc="upper right")

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_xlabel("頻率 (Hz)", fontsize=8)
    ax.set_ylabel("RT60 (s)", fontsize=8)
    ax.set_title(title, fontsize=9)
    ax.tick_params(labelsize=7)


def _warnings_ax(ax, warnings: list[str]) -> None:
    ax.axis("off")
    if warnings:
        lines = ["[!] warnings（真警示，非解析紀錄）："] + [f"  • {w}" for w in warnings]
        color = _WARN_COLOR
    else:
        lines = ["[OK] 無警示（warnings 為空）"]
        color = _OK_COLOR
    ax.text(
        0, 1, "\n".join(lines), va="top", ha="left", fontsize=7.5, color=color,
        transform=ax.transAxes, wrap=True,
    )


# ------------------------------------------------------------
# 照片路徑：重跑 T-10 前處理（無模型）＋ T-11 深度／T-12 分割（純為了畫圖的像素資料）
# ------------------------------------------------------------


def _photo_pixel_panels(
    photo_path: Path, surfaces_dict: dict[str, str]
) -> tuple[Image.Image, np.ndarray, dict[str, np.ndarray], dict[str, str], str | None]:
    from . import geometry, preprocess
    from . import surfaces as surfaces_mod

    summary = preprocess.preprocess_image(photo_path)

    if summary["is_equirect"]:
        primary_name = config.PERSPECTIVE_VIEWS[0]["name"]  # az000_el00
        img_path = summary["views"][primary_name]["path"]
        wall_face = surfaces_mod.VIEW_TO_SURFACE[primary_name]
        view_note = f"環景已展開為 {len(summary['views'])} 視角，此處顯示主視角（{primary_name} → {wall_face}）"
    else:
        img_path = summary["cropped"]
        wall_face = "west"  # 單張透視四面牆共用同一材質判定值，取一面代表
        view_note = None

    img = Image.open(img_path).convert("RGB")

    seg_processor, seg_model = surfaces_mod._load_segmenter()
    labelmap, _ratios = surfaces_mod.segment_roles(img, seg_processor, seg_model)

    depth_pipe = geometry.load_depth_model()
    depth = geometry.estimate_depth_map(img, depth_pipe)

    role_masks = {
        "floor": np.isin(labelmap, list(surfaces_mod.ADE_FLOOR_IDS.keys())),
        "ceiling": np.isin(labelmap, list(surfaces_mod.ADE_CEILING_IDS.keys())),
        "wall": np.isin(labelmap, list(surfaces_mod.ADE_WALL_IDS.keys())),
    }
    role_material = {
        "floor": surfaces_dict.get("floor"),
        "ceiling": surfaces_dict.get("ceiling"),
        "wall": surfaces_dict.get(wall_face),
    }
    return img, depth, role_masks, role_material, view_note


def _render_segmentation_overlay(
    ax, img: Image.Image, role_masks: dict[str, np.ndarray],
    role_material: dict[str, str], materials_data: dict[str, Any],
) -> None:
    arr = np.asarray(img).astype(np.float64) / 255.0
    overlay = arr.copy()
    for role, mask in role_masks.items():
        if not mask.any():
            continue
        overlay[mask] = overlay[mask] * 0.45 + _ROLE_COLORS[role] * 0.55
    ax.imshow(overlay)

    for role, mask in role_masks.items():
        if not mask.any():
            continue
        ys, xs = np.nonzero(mask)
        cy, cx = int(ys.mean()), int(xs.mean())
        label = _material_label(role, role_material.get(role), materials_data)
        ax.text(
            cx, cy, label, color="white", fontsize=6.5, ha="center", va="center",
            bbox=dict(boxstyle="round", fc="black", alpha=0.6, ec="none"),
        )
    ax.set_title("表面分割疊色圖（材質＋α@1kHz）", fontsize=9)
    ax.axis("off")


def _render_depth_map(ax, depth: np.ndarray) -> None:
    clipped = np.clip(depth, config.DEPTH_CLAMP_MIN_M, config.DEPTH_CLAMP_MAX_M)
    im = ax.imshow(clipped, cmap="viridis")
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="公尺")
    ax.set_title("Metric Depth（clamp 後）", fontsize=9)
    ax.axis("off")


def _render_photo(analysis: dict[str, Any], out_dir: Path) -> Path:
    _setup_fonts()
    materials_data = load_materials()
    band_freqs = analysis["band_center_freqs_hz"]
    surfaces_dict = analysis["surfaces"]
    photo_path = Path(analysis["input"])

    img, depth, role_masks, role_material, view_note = _photo_pixel_panels(photo_path, surfaces_dict)

    predelay_ms = None
    ir_mono_json = out_dir / "ir_mono.json"
    if ir_mono_json.exists():
        predelay_ms = json.loads(ir_mono_json.read_text(encoding="utf-8")).get(
            "predelay_ms_from_acoustics"
        )

    dims = analysis["dims_m"]
    info_lines = [
        f"尺寸：{dims['length']:.2f} × {dims['width']:.2f} × {dims['height']:.2f} m",
        f"體積：{analysis['volume_m3']:.2f} m³",
        f"confidence：{analysis['confidence']}（dims_source={analysis['dims_source']}）",
    ]
    if predelay_ms is not None:
        info_lines.append(f"pre-delay：{predelay_ms:.2f} ms")

    fig = plt.figure(figsize=(15, 10))
    gs = fig.add_gridspec(3, 3, height_ratios=[1.2, 1.0, 0.8], hspace=0.4, wspace=0.25)

    ax_img = fig.add_subplot(gs[0, 0])
    ax_img.imshow(np.asarray(img))
    title = "原圖（前處理後）"
    if view_note:
        title += f"\n{view_note}"
    ax_img.set_title(title, fontsize=9)
    ax_img.axis("off")

    ax_seg = fig.add_subplot(gs[0, 1])
    _render_segmentation_overlay(ax_seg, img, role_masks, role_material, materials_data)

    ax_depth = fig.add_subplot(gs[0, 2])
    _render_depth_map(ax_depth, depth)

    ax_rt60 = fig.add_subplot(gs[1, :2])
    closed_loop = analysis["closed_loop"]
    target = [b["rt60_target_s"] for b in closed_loop["bands"]]
    measured = [b["t30_measured_s"] for b in closed_loop["bands"]]
    within = [b["within_tolerance"] for b in closed_loop["bands"]]
    _rt60_bar_ax(ax_rt60, band_freqs, target, measured, within)

    ax_info = fig.add_subplot(gs[1, 2])
    ax_info.axis("off")
    ax_info.text(0, 1, "\n".join(info_lines), va="top", fontsize=9.5, transform=ax_info.transAxes)

    ax_warn = fig.add_subplot(gs[2, :])
    _warnings_ax(ax_warn, analysis["warnings"])

    fig.suptitle(f"Image Reverb 分析報告 — 照片：{photo_path.name}", fontsize=13)
    out_path = out_dir / "analysis.png"
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return out_path


# ------------------------------------------------------------
# 文字場景路徑
# ------------------------------------------------------------


def _render_text(analysis: dict[str, Any], out_dir: Path) -> Path:
    _setup_fonts()
    materials_data = load_materials()
    band_freqs = analysis["band_center_freqs_hz"]
    surfaces_dict = analysis["surfaces"]

    fig = plt.figure(figsize=(13, 8))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 0.8], hspace=0.4, wspace=0.3)

    ax_preset = fig.add_subplot(gs[0, 0])
    ax_preset.axis("off")
    dims = analysis["dims_m"]
    preset_lines = [
        f"輸入：「{analysis['input']}」",
        f"採用 preset：{analysis['preset_id']}（{analysis['preset_name_zh']}）",
        f"尺寸：{dims['length']:.2f} × {dims['width']:.2f} × {dims['height']:.2f} m",
        f"體積：{analysis['volume_m3']:.2f} m³",
        f"confidence：{analysis['confidence']}（dims_source={analysis['dims_source']}）",
        "",
        "全部假設值（notes）：",
    ] + [f"  • {n}" for n in analysis["notes"]]
    ax_preset.text(0, 1, "\n".join(preset_lines), va="top", fontsize=8.5, transform=ax_preset.transAxes)
    ax_preset.set_title("採用的 preset 與全部假設值", fontsize=9.5, loc="left")

    ax_mat = fig.add_subplot(gs[0, 1])
    ax_mat.axis("off")
    mat_lines = ["六面材質表："]
    for face, mid in surfaces_dict.items():
        mat = get_material(mid, materials_data)
        a1k = _alpha_at(mid, materials_data)
        mat_lines.append(f"  {face:<8} {mat['name_zh']}（{mid}）α@1kHz={a1k}")
    ax_mat.text(0, 1, "\n".join(mat_lines), va="top", fontsize=8.5, family="monospace", transform=ax_mat.transAxes)
    ax_mat.set_title("六面材質表", fontsize=9.5, loc="left")

    ax_rt60 = fig.add_subplot(gs[1, 0])
    closed_loop = analysis["closed_loop"]
    target = [b["rt60_target_s"] for b in closed_loop["bands"]]
    measured = [b["t30_measured_s"] for b in closed_loop["bands"]]
    within = [b["within_tolerance"] for b in closed_loop["bands"]]
    _rt60_bar_ax(ax_rt60, band_freqs, target, measured, within)

    ax_warn = fig.add_subplot(gs[1, 1])
    _warnings_ax(ax_warn, analysis["warnings"])

    fig.suptitle(f"Image Reverb 分析報告 — 文字場景：{analysis['input']}", fontsize=13)
    out_path = out_dir / "analysis.png"
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return out_path


# ------------------------------------------------------------
# 複合場景路徑
# ------------------------------------------------------------


def _render_scene(analysis: dict[str, Any], out_dir: Path) -> Path:
    _setup_fonts()
    band_freqs = analysis["band_center_freqs_hz"]
    rooms = analysis["rooms"]
    n_rooms = len(rooms)

    fig = plt.figure(figsize=(14, 3.2 * n_rooms + 3.5))
    gs = fig.add_gridspec(
        n_rooms + 2, 1, height_ratios=[1.0] * n_rooms + [0.9, 0.8], hspace=0.6
    )

    for i, room in enumerate(rooms):
        ax = fig.add_subplot(gs[i, 0])
        cl = room["closed_loop"]
        target = [b["rt60_target_s"] for b in cl["bands"]]
        measured = [b["t30_measured_s"] for b in cl["bands"]]
        within = [b["within_tolerance"] for b in cl["bands"]]
        dims = room["dims_m"]
        _rt60_bar_ax(
            ax, band_freqs, target, measured, within,
            title=f"[{room['role']}] {room['name']}（{dims[0]}×{dims[1]}×{dims[2]} m）",
        )

    ax_paths = fig.add_subplot(gs[n_rooms, 0])
    ax_paths.axis("off")
    path_lines = ["路徑列表（類型 / gain / delay / TL 構造）："]
    for p in analysis["paths"]:
        via = f"，經 {p['via_room']}" if p.get("via_room") else ""
        path_lines.append(f"  [{p['index']}] {p['name_zh']}（{p['type']}）× tl_times={p['tl_times']}{via}")
        path_lines.append(
            f"      gain={p['gain_db']}dB, extra_delay={p['extra_delay_ms']}ms, "
            f"TL(6段)={p['tl_db_per_band']}dB, confidence={p['tl_confidence']}"
        )
    ax_paths.text(0, 1, "\n".join(path_lines), va="top", fontsize=7.5, family="monospace", transform=ax_paths.transAxes)
    ax_paths.set_title("路徑列表", fontsize=9.5, loc="left")

    ax_warn = fig.add_subplot(gs[n_rooms + 1, 0])
    _warnings_ax(ax_warn, analysis["warnings"])

    fig.suptitle(f"Image Reverb 分析報告 — 複合場景：{analysis['scene_name']}", fontsize=13)
    out_path = out_dir / "analysis.png"
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return out_path


# ------------------------------------------------------------
# 統一入口
# ------------------------------------------------------------


def render_analysis_png(analysis: dict[str, Any], out_dir: str | Path) -> Path:
    """依 `analysis['input_type']` 分派到對應拼版，輸出 `<out_dir>/analysis.png`。"""
    out_dir = Path(out_dir)
    input_type = analysis.get("input_type")
    if input_type == "photo":
        return _render_photo(analysis, out_dir)
    if input_type == "text":
        return _render_text(analysis, out_dir)
    if input_type == "scene":
        return _render_scene(analysis, out_dir)
    raise ValueError(f"未知的 input_type '{input_type}'，visualize 只認得 photo/text/scene")
