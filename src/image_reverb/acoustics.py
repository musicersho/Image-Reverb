"""T-13：聲學參數計算 —— 房間尺寸（T-11）＋逐表面材質（T-12） → 逐頻段 RT60、pre-delay。

**約束 B（Phase 0 實證的硬性需求，HANDOFF 地雷第 8 條）**：RT60 必須逐頻段獨立計算，
不可把六段 α 平均後算單一寬頻 RT60。實證：地毯房間 125Hz RT60=4.093s、4kHz=0.126s
（差 32 倍），平均 α 算出的寬頻值 0.267s 與實測 T30 4.023s 差 15 倍，因為殘響尾巴
完全由低頻決定。本模組的每一步都是「先逐面逐頻段算吸音量，最後才在同一頻段內加總」，
不存在跨頻段或跨表面的 α 平均。

**地雷第 14 條——公式值與量測 IR 的已知落差**：α 高（>0.3）時 Sabine/Eyring 的
125Hz 公式值與量測 IR 的 T30 可以差到 2 倍以上（逐表面 floor=carpet：Sabine 0.348s
vs 實測 0.748s）。本模組只負責公式計算，**不**假裝公式值等於實際聽感；
輸出一律標記 `rt60_source: "formula"` 並附 `rt60_disclaimer`，最終聽感以 T-14
的量測 T30 為準。

本模組只算聲學參數，不碰幾何估計（T-11）、不碰材質辨識（T-12）、不做 IR 合成（T-14）。
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pyroomacoustics as pra

from . import config
from .geometry import RoomEstimate
from .materials import SurfaceMaterials, load_materials

RT60_DISCLAIMER = (
    "rt60_bands_* 是 Sabine/Eyring 公式的理論值，不是量測值。"
    "已實證：吸音係數高（>0.3）時低頻公式值與量測 IR 的 T30 可差到 2 倍以上"
    "（逐表面 floor=carpet 的 125Hz：Sabine 0.348s vs 實測 0.748s）。"
    "最終聽感以 T-14 生成的 IR 實測 T30 為準，不可直接引用本欄位當作實際殘響時間。"
)


def surface_areas_m2(length_m: float, width_m: float, height_m: float) -> dict[str, float]:
    """六個面各自的面積 (m²)，key 與 pyroomacoustics 的 wall_names 一致。

    座標慣例與 T-11 `RoomEstimate` 一致：length = 進深（west/east 面法向）、
    width = 寬度（south/north 面法向）、height = 高度（floor/ceiling 面法向）。
    """
    return {
        "west": width_m * height_m,
        "east": width_m * height_m,
        "south": length_m * height_m,
        "north": length_m * height_m,
        "floor": length_m * width_m,
        "ceiling": length_m * width_m,
    }


def air_absorption_per_m(band_freqs: list[int]) -> list[float]:
    """依 config 的溫濕度，取各頻段的空氣吸收係數 m（1/m）。

    直接沿用 pyroomacoustics 自己的空氣吸收表（`Physics.get_air_absorption()`），
    與 T-01/T-14 實際跑模擬時用的是同一份資料，避免公式估計值與模擬結果
    因為查表來源不同而互相矛盾。
    """
    physics = pra.Physics(temperature=config.AIR_TEMPERATURE_C, humidity=config.AIR_HUMIDITY_PCT)
    info = physics.get_air_absorption()
    freq_to_m = dict(zip(info["center_freqs"], info["coeffs"]))
    missing = [f for f in band_freqs if f not in freq_to_m]
    if missing:
        raise ValueError(
            f"pyroomacoustics 的空氣吸收表缺少頻段 {missing}——"
            f"材質表（data/materials.json）的 band_center_freqs_hz 與空氣吸收表不相容。"
        )
    return [freq_to_m[f] for f in band_freqs]


def rt60_sabine_band(volume_m3: float, total_absorption_m2: float, air_term: float) -> float:
    """單一頻段的 Sabine RT60 = 0.161·V / (Σ Sᵢαᵢ + 4mV)。

    `total_absorption_m2` 必須是「該頻段」逐面面積加權後的 Σ Sᵢαᵢ——
    呼叫端不得先把多面的 α 平均掉才傳進來（約束 B）。
    """
    denom = total_absorption_m2 + air_term
    if denom <= 0.0:
        raise ValueError("總吸音量（含空氣吸收）為 0，RT60 無限大，無法計算")
    return 0.161 * volume_m3 / denom


def rt60_eyring_band(
    volume_m3: float, total_absorption_m2: float, total_surface_m2: float, air_term: float
) -> float:
    """單一頻段的 Eyring RT60 = 0.161·V / (-S·ln(1-ā) + 4mV)，ā = Σ Sᵢαᵢ / S。

    ā 是**面積加權**的平均吸音係數（同一頻段內、跨表面），這是 Eyring 公式本身的
    定義，不是約束 B 禁止的「跨頻段平均 α」——兩者是不同的軸，不要混淆。
    """
    if total_surface_m2 <= 0.0:
        raise ValueError("總表面積為 0，無法計算 Eyring RT60")
    a_bar = min(total_absorption_m2 / total_surface_m2, 1.0 - 1e-9)
    denom = -total_surface_m2 * math.log(1.0 - a_bar) + air_term
    if denom <= 0.0:
        raise ValueError("總吸音量（含空氣吸收）為 0，RT60 無限大，無法計算")
    return 0.161 * volume_m3 / denom


def rt60_mid(band_freqs: list[int], rt60_values: list[float], mid_freqs=(500, 1000)) -> float:
    """單一代表值（顯示用）：從頻段結果本身取平均，不由平均 α 重算（約束 B）。"""
    idxs = [band_freqs.index(f) for f in mid_freqs if f in band_freqs]
    if not idxs:
        raise ValueError(f"band_freqs {band_freqs} 裡找不到 {mid_freqs} 任一頻段")
    return sum(rt60_values[i] for i in idxs) / len(idxs)


def direct_path_distance_m(length_m: float, width_m: float, height_m: float) -> float:
    """聲源到麥克風的直達距離（公尺），位置用 config 的假設比例推算。

    沒有真正的聲源/麥克風位置資訊（照片只給幾何，不給錄音設置），
    所以用房間尺寸的固定比例（`config.PREDELAY_SOURCE_POS_FRAC` / `_MIC_POS_FRAC`）
    當作 MVP 假設，與 `gen_ir_manual.py` 手動 preset 的聲源/麥克風擺位精神一致
    （避免把聲源/麥克風放在同一點或牆角造成退化的直達距離）。
    """
    sl, sw, sh = config.PREDELAY_SOURCE_POS_FRAC
    ml, mw, mh = config.PREDELAY_MIC_POS_FRAC
    source = (sl * length_m, sw * width_m, sh * height_m)
    mic = (ml * length_m, mw * width_m, mh * height_m)
    return math.dist(source, mic)


def compute_predelay_ms(length_m: float, width_m: float, height_m: float) -> float:
    """pre-delay：直達聲距離 / 音速 × 1000。音速依 config 的溫濕度算，與空氣吸收同源。"""
    distance_m = direct_path_distance_m(length_m, width_m, height_m)
    physics = pra.Physics(temperature=config.AIR_TEMPERATURE_C, humidity=config.AIR_HUMIDITY_PCT)
    return distance_m / physics.get_sound_speed() * 1000.0


@dataclass
class AcousticsResult:
    """T-13 輸出：房間尺寸＋逐表面材質 → 逐頻段 RT60、pre-delay。"""

    length_m: float
    width_m: float
    height_m: float
    volume_m3: float
    dims_source: str
    surfaces: dict[str, str]
    band_center_freqs_hz: list[int]
    rt60_bands_sabine: list[float]
    rt60_bands_eyring: list[float]
    rt60_mid_sabine: float
    rt60_mid_eyring: float
    predelay_ms: float
    confidence: str
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "dims": {
                "length_m": round(self.length_m, 3),
                "width_m": round(self.width_m, 3),
                "height_m": round(self.height_m, 3),
            },
            "dims_source": self.dims_source,
            "volume_m3": round(self.volume_m3, 2),
            "surfaces": dict(self.surfaces),
            "band_center_freqs_hz": list(self.band_center_freqs_hz),
            "rt60_bands_sabine": [round(v, 4) for v in self.rt60_bands_sabine],
            "rt60_bands_eyring": [round(v, 4) for v in self.rt60_bands_eyring],
            "rt60_mid_sabine": round(self.rt60_mid_sabine, 4),
            "rt60_mid_eyring": round(self.rt60_mid_eyring, 4),
            "rt60_source": "formula",
            "rt60_disclaimer": RT60_DISCLAIMER,
            "predelay_ms": round(self.predelay_ms, 2),
            "confidence": self.confidence,
            "warnings": list(self.warnings),
        }


def compute_acoustics(
    estimate: RoomEstimate,
    surfaces: SurfaceMaterials,
    materials_data: dict[str, Any] | None = None,
) -> AcousticsResult:
    """主入口：吃 T-11 的 `RoomEstimate` ＋ T-12 的 `SurfaceMaterials` → 聲學參數。"""
    if materials_data is None:
        materials_data = load_materials()
    surfaces.validate(materials_data)

    band_freqs, alpha_table = surfaces.alpha_table(materials_data)
    length_m, width_m, height_m = estimate.length_m, estimate.width_m, estimate.height_m
    volume_m3 = estimate.volume_m3

    areas = surface_areas_m2(length_m, width_m, height_m)
    total_surface_m2 = sum(areas.values())
    air_terms = air_absorption_per_m(band_freqs)

    rt60_sabine: list[float] = []
    rt60_eyring: list[float] = []
    for band_idx in range(len(band_freqs)):
        # 逐面面積加權加總——這是唯一允許的「跨表面合併」方式（約束 A/B 都要求）
        total_absorption = sum(
            areas[name] * alpha_table[name][band_idx] for name in areas
        )
        air_term = 4.0 * air_terms[band_idx] * volume_m3
        rt60_sabine.append(rt60_sabine_band(volume_m3, total_absorption, air_term))
        rt60_eyring.append(
            rt60_eyring_band(volume_m3, total_absorption, total_surface_m2, air_term)
        )

    warnings = list(estimate.notes) + list(surfaces.warnings)

    return AcousticsResult(
        length_m=length_m,
        width_m=width_m,
        height_m=height_m,
        volume_m3=volume_m3,
        dims_source=estimate.dims_source,
        surfaces=surfaces.as_dict(),
        band_center_freqs_hz=list(band_freqs),
        rt60_bands_sabine=rt60_sabine,
        rt60_bands_eyring=rt60_eyring,
        rt60_mid_sabine=rt60_mid(band_freqs, rt60_sabine),
        rt60_mid_eyring=rt60_mid(band_freqs, rt60_eyring),
        predelay_ms=compute_predelay_ms(length_m, width_m, height_m),
        confidence=estimate.confidence,
        warnings=warnings,
    )


def save_acoustics(result: AcousticsResult, out_path: str | Path) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(result.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return out_path
