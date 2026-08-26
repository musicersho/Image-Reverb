"""T-11：幾何估計 —— metric depth → ShoeBox 房間尺寸/體積。

**為什麼是 metric depth 而不是相對深度**（T-05 實證，見 `output/depth/REPORT.md` §7）：
Depth Anything V2 的相對版輸出的是每張圖各自正規化的 disparity，不是距離。實測 9 張照片，
深度動態範圍與實際空間大小**沒有單調關係**（SUV 車內 91.5x vs 體育館 11.7x，車內比體育館
小好幾個數量級卻大 8 倍）。用 `距離 = k/disparity` 換算也會壞：走廊消失點推出 374 萬公尺。
**T-08 決策一：改用 metric depth 模型（輸出單位是公尺）。禁止退回相對深度模型。**

本模組只做幾何，不碰材質（材質在 T-12）、不算 RT60（在 T-13）。
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from . import config

# 35mm 全片幅的感光元件寬度（mm），用來把 EXIF 的 35mm 等效焦距換算成水平 FOV
FULL_FRAME_WIDTH_MM = 36.0


@dataclass
class RoomEstimate:
    """房間尺寸估計結果。

    `confidence` 只有三種值：high / medium / low。
    **低信心時絕不給自信的數字**——這是 T-11 卡的通過條件之一，
    也是 HANDOFF §2 洞二「模型會安靜地輸出看似合理的錯誤結果」的直接對策。
    """

    length_m: float  # 進深（相機視線方向）
    width_m: float
    height_m: float
    confidence: str
    dims_source: str  # "metric_depth" / "manual" / "equirect_multiview"
    notes: list[str] = field(default_factory=list)
    depth_stats: dict[str, Any] = field(default_factory=dict)

    @property
    def volume_m3(self) -> float:
        return self.length_m * self.width_m * self.height_m

    def as_dict(self) -> dict[str, Any]:
        return {
            "length_m": round(self.length_m, 3),
            "width_m": round(self.width_m, 3),
            "height_m": round(self.height_m, 3),
            "volume_m3": round(self.volume_m3, 2),
            "confidence": self.confidence,
            "dims_source": self.dims_source,
            "notes": self.notes,
            "depth_stats": self.depth_stats,
        }


def load_depth_model():
    """載入 metric depth 模型（transformers depth-estimation pipeline）。

    ⚠️ 模型 id 固定在 config.METRIC_DEPTH_MODEL_ID，必須是 **Metric** 版本。
    這裡刻意檢查一次 id：如果有人把它換回相對深度版（T-05 已否定的路線），
    直接拋錯而不是安靜地跑出無意義的數字。
    """
    from transformers import pipeline

    model_id = config.METRIC_DEPTH_MODEL_ID
    if "Metric" not in model_id:
        raise ValueError(
            f"config.METRIC_DEPTH_MODEL_ID = '{model_id}' 看起來不是 metric depth 模型。\n"
            f"       T-05 已實證否定相對深度路線（相對 disparity 與實際空間大小無單調關係），\n"
            f"       T-08 決策一明訂改用 metric 模型。禁止退回相對深度模型。"
        )
    return pipeline("depth-estimation", model=model_id)


def hfov_from_exif(img: Image.Image) -> tuple[float, str]:
    """從 EXIF 的 35mm 等效焦距換算水平 FOV；讀不到就回傳預設值。

    回傳 (hfov_deg, 來源說明)。
    """
    try:
        exif = img.getexif()
    except Exception:
        exif = None

    if exif:
        # 41989 = FocalLengthIn35mmFilm
        f35 = exif.get(41989)
        if f35:
            try:
                f35 = float(f35)
                if f35 > 0:
                    hfov = 2.0 * math.degrees(math.atan(FULL_FRAME_WIDTH_MM / (2.0 * f35)))
                    return hfov, f"EXIF 35mm 等效焦距 {f35:.0f}mm"
            except (TypeError, ValueError):
                pass

    return config.DEFAULT_HFOV_DEG, f"EXIF 無焦距資訊，用預設 {config.DEFAULT_HFOV_DEG:.0f}°"


def estimate_depth_map(img: Image.Image, depth_pipe) -> np.ndarray:
    """跑 metric depth，回傳單位為公尺的 2D 陣列。"""
    result = depth_pipe(img)
    # transformers 的 depth-estimation pipeline：predicted_depth 是 tensor（公尺）
    depth = result["predicted_depth"]
    arr = depth.squeeze().cpu().numpy().astype(np.float64) if hasattr(depth, "cpu") else np.asarray(depth, dtype=np.float64)
    return arr


def depth_statistics(depth: np.ndarray) -> dict[str, Any]:
    """深度的 robust 統計，含 T-05 REPORT §7.3 的防呆。

    防呆內容：窗外／天空／走廊消失點會給出荒謬的遠距離，直接參與統計會把房間
    尺寸整個拉爆（T-05 實測走廊消失點推出 374 萬公尺），所以先 clamp 掉再取百分位。
    """
    flat = depth.reshape(-1)
    finite = flat[np.isfinite(flat)]
    if finite.size == 0:
        raise ValueError("深度圖全為 NaN/Inf，模型輸出無效")

    n_total = finite.size
    too_far = int((finite > config.DEPTH_CLAMP_MAX_M).sum())
    too_near = int((finite < config.DEPTH_CLAMP_MIN_M).sum())
    kept = finite[
        (finite >= config.DEPTH_CLAMP_MIN_M) & (finite <= config.DEPTH_CLAMP_MAX_M)
    ]
    if kept.size == 0:
        raise ValueError(
            f"深度全部落在 clamp 範圍外（{config.DEPTH_CLAMP_MIN_M}–"
            f"{config.DEPTH_CLAMP_MAX_M} m），這張圖的 metric 深度不可用"
        )

    p_lo, p_mid, p_hi = np.percentile(kept, config.DEPTH_PERCENTILES)
    return {
        "p5_m": round(float(p_lo), 3),
        "p50_m": round(float(p_mid), 3),
        "p95_m": round(float(p_hi), 3),
        "min_m": round(float(kept.min()), 3),
        "max_m": round(float(kept.max()), 3),
        "clamped_far_ratio": round(too_far / n_total, 4),
        "clamped_near_ratio": round(too_near / n_total, 4),
        "clamp_range_m": [config.DEPTH_CLAMP_MIN_M, config.DEPTH_CLAMP_MAX_M],
    }


def _clamped_median(depth: np.ndarray, center_frac: float = 0.5) -> float:
    """取影像中央區域的 clamp 後中位數深度（拿來當「這個方向的牆有多遠」）。"""
    h, w = depth.shape
    ch, cw = int(h * center_frac), int(w * center_frac)
    y0, x0 = (h - ch) // 2, (w - cw) // 2
    region = depth[y0 : y0 + ch, x0 : x0 + cw].reshape(-1)
    region = region[np.isfinite(region)]
    region = region[
        (region >= config.DEPTH_CLAMP_MIN_M) & (region <= config.DEPTH_CLAMP_MAX_M)
    ]
    if region.size == 0:
        return float("nan")
    return float(np.median(region))


def apply_scene_cue_confidence(estimate: RoomEstimate, cues: dict[str, float]) -> RoomEstimate:
    """用分割提供的場景線索把「深度看不出來的失敗」降為低信心。

    **為什麼需要這一層**（2026-08-18 實測，見 output/geometry/REPORT.md）：
    體育館那張（實際進深 ~150m）metric 深度**全圖最大只有 3.61m**，估出 3.33m、
    誤差 -98%，但深度統計本身完全正常（沒有逼近 clamp 上限、沒有大量遠端像素），
    所以**深度數字裡沒有任何訊號能發現它錯了**。這正是 HANDOFF §2 洞二
    「模型會安靜地輸出看似合理的錯誤結果」。

    可用的訊號來自分割（T-12 的 `surfaces.segment_roles`）：
    - **地板可見度 0%**：看不到地面就無法建立空間範圍，深度只量到最近的遮蔽物。
      實測 arena=0.0%、cgi_cavern=0.0%（都是超大空間）vs bathroom=6.8%、corridor=20.6%。
    - **人群佔比高**：人是強吸音體也是強遮蔽物，深度量到的是人而不是牆。
      實測 cgi_cavern=53.0%、livehouse=36.0%。

    這兩條都在說同一件事：**估到的是「看得見的範圍」，不是「房間的範圍」**。
    """
    floor_ratio = cues.get("floor_pixel_ratio")
    person_ratio = cues.get("person_pixel_ratio")

    if floor_ratio is not None and floor_ratio < 0.02:
        estimate.confidence = "low"
        estimate.notes.append(
            f"地板可見度只有 {floor_ratio*100:.1f}%（門檻 2%）——看不到地面就無法建立空間範圍，"
            f"深度只量到最近的遮蔽物，估出的尺寸是**下限**而非實際房間大小 → confidence: low。"
        )
    if person_ratio is not None and person_ratio > 0.20:
        estimate.confidence = "low"
        estimate.notes.append(
            f"人群佔畫面 {person_ratio*100:.1f}%（門檻 20%）——深度量到的是人而不是牆面，"
            f"空間尺寸不可信 → confidence: low。"
        )
    # T-12 的 CLIP 域外偵測說「這不是建築表面」→ 那它也不是一個可以估尺寸的房間。
    # 實測：SUV 車內被判為 __vehicle_interior（機率 0.735）；ADE20K 沒有任何車輛
    # 內裝類別（HANDOFF §2 洞二），光靠分割與深度都發現不了，只有這個訊號抓得到。
    if cues.get("out_of_domain"):
        estimate.confidence = "low"
        estimate.notes.append(
            f"T-12 的材質分類判定這不是建築表面"
            f"（{cues.get('out_of_domain_label', '域外')}）——"
            f"這不是一個可以用 ShoeBox 房間模型描述的空間，尺寸數字不可信 → confidence: low。"
        )
    estimate.depth_stats["scene_cues"] = {
        k: (round(v, 4) if isinstance(v, float) else v) for k, v in cues.items()
    }
    return estimate


def apply_scope_confidence(estimate: RoomEstimate) -> RoomEstimate:
    """量程規則（T-11 決策補丁步驟 7，Fable 2026-08-25 定案）。

    **為什麼需要這一層**：metric depth 模型量程實證天花板約 20m，且量程壓縮在
    天花板之前就開始（走廊實際 30m 被壓成 12.8m）——估值一旦超過
    `config.GEOMETRY_SCOPE_MAX_M`，就無法區分「真的 10–20m」與「被壓縮的 30m+」，
    這個區間的數字不可信。範圍外不是失敗，是正式行為分支：`confidence: low` ＋
    可操作警示，出口是 `--override-dims`（F-09）或改用環景輸入。

    判定對象：
    - 透視照（`dims_source == "metric_depth"`）：**任一維**（長/寬/高）超過門檻；
    - 環景（`dims_source == "equirect_multiview"`）：**單面牆距**超過門檻——
      不是相加後的總長，因為對牆相加會讓有效上限拉高到約 40m，用相加值判斷
      會漏掉真正超量程的單面牆。

    與既有三條場景線索規則（`apply_scene_cue_confidence`）並存：兩者都只會把
    confidence 往下修（不會把 low 改回 medium/high），先跑哪個都一樣，取最嚴。
    """
    max_m = config.GEOMETRY_SCOPE_MAX_M
    over: dict[str, float] = {}

    if estimate.dims_source == "equirect_multiview":
        wall_distances = estimate.depth_stats.get("wall_distances_m", {})
        over = {k: v for k, v in wall_distances.items() if v is not None and v > max_m}
    elif estimate.dims_source == "metric_depth":
        dims = {
            "length_m": estimate.length_m,
            "width_m": estimate.width_m,
            "height_m": estimate.height_m,
        }
        over = {k: v for k, v in dims.items() if v > max_m}

    if over:
        estimate.confidence = "low"
        detail = "、".join(f"{k}={v:.1f}m" for k, v in over.items())
        estimate.notes.append(
            f"超出已驗證量程（適用範圍 ≤{max_m:.0f}m；{detail}）——metric depth 模型實證"
            f"天花板約 20m，且量程壓縮在天花板之前就開始（走廊實際 30m 被壓成 12.8m），"
            f"超過此門檻的估值無法區分「真的 10–20m」與「被壓縮的 30m+」，數字不可信 → "
            f"confidence: low。建議用 --override-dims 指定實際尺寸，或改用 360° 環景照片輸入。"
        )
    return estimate


def estimate_from_perspective(
    img: Image.Image, depth_pipe, hfov_deg: float | None = None
) -> RoomEstimate:
    """單張透視照 → ShoeBox 尺寸。

    幾何假設（MVP，刻意寫清楚而不藏在程式裡）：
    - 相機在房間內、大致水平朝向遠牆；
    - 進深 L ≈ clamp 後的 p95 深度（最遠可見表面）；
    - 遠牆處的視野寬度 W = 2·L·tan(hFOV/2)、高度 H = 2·L·tan(vFOV/2)；
    - **相機背後的空間看不到**，所以 L 是低估（SPEC §8 已知風險，環景才解得掉）。
    """
    notes: list[str] = []
    if hfov_deg is None:
        hfov_deg, fov_note = hfov_from_exif(img)
        notes.append(f"水平 FOV：{hfov_deg:.1f}°（{fov_note}）")
    else:
        notes.append(f"水平 FOV：{hfov_deg:.1f}°（呼叫端指定）")

    depth = estimate_depth_map(img, depth_pipe)
    stats = depth_statistics(depth)

    far = stats["p95_m"]
    w_img, h_img = img.size
    aspect = h_img / w_img
    hfov_rad = math.radians(hfov_deg)
    # 垂直 FOV 由水平 FOV 與長寬比推得（針孔模型）
    vfov_rad = 2.0 * math.atan(math.tan(hfov_rad / 2.0) * aspect)

    length = far
    width = 2.0 * far * math.tan(hfov_rad / 2.0)
    height = 2.0 * far * math.tan(vfov_rad / 2.0)

    confidence = "medium"

    # --- 信心判定：把「模型可能在胡說」的訊號變成低信心，而不是自信的數字 ---
    if stats["clamped_far_ratio"] > 0.10:
        confidence = "low"
        notes.append(
            f"有 {stats['clamped_far_ratio']*100:.1f}% 的像素深度超過 "
            f"{config.DEPTH_CLAMP_MAX_M}m 上限被 clamp 掉（窗外/天空/消失點），"
            f"這通常表示空間開放或模型在猜，尺寸不可信。"
        )
    if far >= config.DEPTH_CLAMP_MAX_M * 0.9:
        confidence = "low"
        notes.append(
            f"p95 深度 {far:.1f}m 已逼近 clamp 上限 {config.DEPTH_CLAMP_MAX_M}m，"
            f"真實距離可能遠超這個值（超大空間），數字只能當下限看。"
        )
    if height < config.ROOM_HEIGHT_MIN_M or height > config.ROOM_HEIGHT_MAX_M:
        notes.append(
            f"由 FOV 推出的高度 {height:.2f}m 超出合理範圍 "
            f"[{config.ROOM_HEIGHT_MIN_M}, {config.ROOM_HEIGHT_MAX_M}]m，已 clamp；"
            f"單張照片推高度本來就很弱（相機仰角未知）。"
        )
        height = float(np.clip(height, config.ROOM_HEIGHT_MIN_M, config.ROOM_HEIGHT_MAX_M))
        if confidence != "low":
            confidence = "low"
    if stats["p95_m"] < 1.0:
        confidence = "low"
        notes.append(f"p95 深度只有 {stats['p95_m']:.2f}m，像是特寫或被前景遮住，不像一個空間。")

    notes.append("進深只涵蓋相機看得到的範圍，相機背後的空間未計入（SPEC §8 已知風險；環景可解）。")

    return RoomEstimate(
        length_m=length, width_m=width, height_m=height,
        confidence=confidence, dims_source="metric_depth",
        notes=notes, depth_stats=stats,
    )


def estimate_from_equirect_views(
    view_paths: dict[str, str], depth_pipe
) -> RoomEstimate:
    """環景六視角 → ShoeBox 尺寸（比單張照片可靠，因為沒有「視野外」）。

    幾何：
    - 四個水平視角（方位角 0/90/180/270）各取中央區域中位數深度＝該方向的牆距，
      **對面兩牆相加**才是房間該軸的全長（這正是環景比單張照片強的地方）；
    - 上下視角在仰角 ±45°，中心射線打到天花板/地板的斜距 d 換算垂直距離 h = d·sin45°。
    """
    notes: list[str] = []
    wall_dist: dict[str, float] = {}

    for view_name, path in view_paths.items():
        img = Image.open(path).convert("RGB")
        depth = estimate_depth_map(img, depth_pipe)
        d = _clamped_median(depth)
        wall_dist[view_name] = d

    def pair(a: str, b: str, axis: str) -> float:
        da, db = wall_dist.get(a, float("nan")), wall_dist.get(b, float("nan"))
        if not np.isfinite(da) or not np.isfinite(db):
            notes.append(f"{axis} 軸缺少可用深度（{a}={da}, {b}={db}）")
            return float("nan")
        return da + db

    length = pair("az000_el00", "az180_el00", "進深")
    width = pair("az090_el00", "az270_el00", "寬度")

    sin45 = math.sin(math.radians(45.0))
    up, down = wall_dist.get("el+45", float("nan")), wall_dist.get("el-45", float("nan"))
    height = (up + down) * sin45 if np.isfinite(up) and np.isfinite(down) else float("nan")

    stats = {
        "wall_distances_m": {k: (round(v, 3) if np.isfinite(v) else None)
                             for k, v in wall_dist.items()},
        "method": "四個水平視角對牆相加；上下視角斜距 × sin45° 換算高度",
    }

    confidence = "medium"
    for label, val in (("進深", length), ("寬度", width), ("高度", height)):
        if not np.isfinite(val):
            confidence = "low"
            notes.append(f"{label}無法估計，已用 fallback 值")

    length = length if np.isfinite(length) else 5.0
    width = width if np.isfinite(width) else 5.0
    if not np.isfinite(height):
        height = 3.0
    if height < config.ROOM_HEIGHT_MIN_M or height > config.ROOM_HEIGHT_MAX_M:
        notes.append(f"推得高度 {height:.2f}m 超出合理範圍，已 clamp")
        height = float(np.clip(height, config.ROOM_HEIGHT_MIN_M, config.ROOM_HEIGHT_MAX_M))
        confidence = "low"

    near_cap = [k for k, v in wall_dist.items()
                if np.isfinite(v) and v >= config.DEPTH_CLAMP_MAX_M * 0.9]
    if near_cap:
        confidence = "low"
        notes.append(
            f"視角 {', '.join(near_cap)} 的深度逼近 clamp 上限 "
            f"{config.DEPTH_CLAMP_MAX_M}m，真實距離可能更遠，數字只能當下限看。"
        )

    notes.append("環景沒有「視野外」問題，對牆相加得到的是完整跨距（提前解掉 SPEC §8 風險）。")

    return RoomEstimate(
        length_m=length, width_m=width, height_m=height,
        confidence=confidence, dims_source="equirect_multiview",
        notes=notes, depth_stats=stats,
    )


def door_scale_check(
    estimate: RoomEstimate,
    img: Image.Image,
    door_pixel_ratio: float,
    door_height_px: float | None,
) -> RoomEstimate:
    """尺度校驗（**不是主路線**，只用來標低信心）。

    若畫面裡有門，用門高 ~2.0m 反推尺度，與 metric 深度推出的高度比對；
    偏差超過 ±50% 就把 confidence 降到 low 並記警示。
    """
    if door_pixel_ratio <= 0.005 or not door_height_px:
        estimate.notes.append("畫面中沒有足夠大的門，跳過尺度校驗（這是可選校驗，不影響主路線）。")
        return estimate

    img_h = img.size[1]
    # 門佔畫面高度的比例 → 用門高 2.0m 反推「整個畫面高度對應多少公尺」
    implied_frame_height_m = config.DOOR_HEIGHT_M * (img_h / door_height_px)
    ratio = implied_frame_height_m / estimate.height_m if estimate.height_m > 0 else float("inf")

    estimate.depth_stats["door_scale_check"] = {
        "door_pixel_ratio": round(door_pixel_ratio, 4),
        "door_height_px": round(float(door_height_px), 1),
        "implied_frame_height_m": round(implied_frame_height_m, 2),
        "estimated_height_m": round(estimate.height_m, 2),
        "ratio": round(ratio, 3),
    }

    if abs(ratio - 1.0) > config.SCALE_CHECK_WARN_RATIO:
        estimate.confidence = "low"
        estimate.notes.append(
            f"尺度校驗不一致：用門高 {config.DOOR_HEIGHT_M}m 反推畫面高度約 "
            f"{implied_frame_height_m:.1f}m，但 metric 深度推出 {estimate.height_m:.1f}m"
            f"（比值 {ratio:.2f}，偏差超過 ±{config.SCALE_CHECK_WARN_RATIO*100:.0f}%）→ confidence: low。"
        )
    else:
        estimate.notes.append(
            f"尺度校驗通過：門高反推與 metric 深度的比值 {ratio:.2f}（在 ±"
            f"{config.SCALE_CHECK_WARN_RATIO*100:.0f}% 內）。"
        )
    return estimate


def parse_override_dims(spec: str) -> tuple[float, float, float]:
    """解析 `--override-dims 4x3x2.5`（公尺）。"""
    parts = spec.lower().replace("×", "x").split("x")
    if len(parts) != 3:
        raise ValueError(f"--override-dims 要寫成 長x寬x高（公尺），例如 4x3x2.5；收到 '{spec}'")
    try:
        dims = tuple(float(p) for p in parts)
    except ValueError as e:
        raise ValueError(f"--override-dims 的數值不是數字：'{spec}'") from e
    if any(d <= 0 for d in dims):
        raise ValueError(f"--override-dims 的三個數值都必須大於 0；收到 '{spec}'")
    if any(d > 500 for d in dims):
        raise ValueError(f"--override-dims 的數值看起來不合理（>500m）：'{spec}'")
    return dims  # type: ignore[return-value]


def manual_estimate(dims: tuple[float, float, float]) -> RoomEstimate:
    """手動覆寫的尺寸。覆寫後下游一律用這個值，且標記 dims_source = "manual"。"""
    return RoomEstimate(
        length_m=dims[0], width_m=dims[1], height_m=dims[2],
        confidence="high", dims_source="manual",
        notes=["尺寸由使用者手動指定（--override-dims），未使用深度模型估計。"],
        depth_stats={},
    )


def estimate_room(
    preprocess_summary: dict[str, Any],
    depth_pipe=None,
    override_dims: tuple[float, float, float] | None = None,
    scene_cues: dict[str, float] | None = None,
) -> RoomEstimate:
    """主入口：吃 T-10 前處理輸出 → 房間尺寸。

    - `override_dims` 有值就直接回傳手動尺寸（F-09），**不跑模型**。
    - 環景走多視角路徑，一般照片走單張透視路徑。
    """
    if override_dims is not None:
        return manual_estimate(override_dims)

    if depth_pipe is None:
        depth_pipe = load_depth_model()

    if preprocess_summary.get("is_equirect"):
        view_paths = {k: v["path"] for k, v in preprocess_summary["views"].items()}
        est = estimate_from_equirect_views(view_paths, depth_pipe)
    else:
        img = Image.open(preprocess_summary["cropped"]).convert("RGB")
        est = estimate_from_perspective(img, depth_pipe)

    est = apply_scope_confidence(est)
    if scene_cues:
        est = apply_scene_cue_confidence(est, scene_cues)
    return est


def save_estimate(estimate: RoomEstimate, out_path: str | Path) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(estimate.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return out_path
