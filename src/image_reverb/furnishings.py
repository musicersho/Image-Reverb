"""T-31：室內陳設等效吸音 —— 資料表讀取 + 從分割結果估算陳設比例（裁決 T-27-A 執行卡 1/3）。

**為什麼要做這個**（裁決 T-27-A，見 TASKS.md T-27 卡）：ShoeBox 六面模型表達不了
床、沙發、窗簾這類室內陳設（地雷 #22），但它們的吸音量不可忽略。裁決採**逐頻段
等效吸音面積**：`A_extra[band] = Σ_c ratio_c × S_total × α_c[band]`，直接加進
`compute_acoustics()` 的 Sabine／Eyring 吸音項——換算成 m² 需要 S_total，那是
T-32 的事，本模組只算「陳設佔全圖多少比例、對應什麼 α」。

**本模組不碰幾何、不碰聲學計算、不動 gate**（Phase 1.7 共同鐵則：陳設資料不得
餵進任何信心軸；`compute_materials_confidence()` 與 `run_photo()` 的 gate 判定
一行都不能受本模組影響）。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import config
from .materials import load_materials
from .surfaces import ADE_CEILING_IDS, ADE_FLOOR_IDS, ADE_WALL_IDS


def load_furnishings(path: str | Path | None = None) -> dict[str, Any]:
    """讀取 furnishings.json 整份 dict，並做結構與不變量驗證。

    驗證項目（違反直接拋錯，不是只靠測試——T-31 卡步驟 3 明文要求）：
      - 頻段（`band_center_freqs_hz`）與 materials.json 完全一致
      - 每個類別的 α 六頻段都在 [0, 1]
      - 每個類別的 `source` 非空字串
      - 每個類別的 `ade_id` 與 `ADE_FLOOR_IDS`／`ADE_CEILING_IDS`／`ADE_WALL_IDS`
        的 keys 不相交（陳設類別不可能同時是幾何角色，構造上就該不相交）
    """
    path = Path(path) if path is not None else config.FURNISHINGS_PATH
    if not path.exists():
        raise FileNotFoundError(f"找不到陳設吸音表：{path}（T-31 的 data/furnishings.json）")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"陳設吸音表 {path} 不是合法的 JSON（第 {e.lineno} 行第 {e.colno} 欄：{e.msg}）。\n"
            f"       這個檔案可能被編輯壞了；可用 `git checkout data/furnishings.json` 還原。"
        ) from e
    except UnicodeDecodeError as e:
        raise ValueError(f"陳設吸音表 {path} 不是 UTF-8 編碼的文字檔（{e.reason}）。") from e

    for key in ("furnishings", "band_center_freqs_hz"):
        if key not in data:
            raise ValueError(f"陳設吸音表 {path} 缺少必要欄位 '{key}'，格式不符 T-31 的規格。")
    if not isinstance(data["furnishings"], list) or not data["furnishings"]:
        raise ValueError(f"陳設吸音表 {path} 的 'furnishings' 必須是非空的清單。")

    materials_data = load_materials()
    if data["band_center_freqs_hz"] != materials_data["band_center_freqs_hz"]:
        raise ValueError(
            f"陳設吸音表的頻段 {data['band_center_freqs_hz']} 與材質表 "
            f"materials.json 的頻段 {materials_data['band_center_freqs_hz']} 不一致——"
            f"兩表必須用同一組頻段，否則沒辦法逐頻段相加。"
        )
    band_freqs = data["band_center_freqs_hz"]

    role_ids = set(ADE_FLOOR_IDS) | set(ADE_CEILING_IDS) | set(ADE_WALL_IDS)

    for item in data["furnishings"]:
        name = item.get("ade_name", item.get("ade_id", "<未知>"))

        ade_id = item.get("ade_id")
        if ade_id in role_ids:
            raise ValueError(
                f"陳設類別 '{name}'（ade_id={ade_id}）與幾何角色 id 集合"
                f"（ADE_FLOOR_IDS／ADE_CEILING_IDS／ADE_WALL_IDS）重疊——"
                f"陳設類別不可以同時是地板/天花板/牆的角色 id。"
            )

        alpha = item.get("alpha", {})
        for freq in band_freqs:
            key = str(freq)
            if key not in alpha:
                raise ValueError(f"陳設類別 '{name}' 缺少 {key} Hz 的吸音係數")
            value = alpha[key]
            if not (0.0 <= value <= 1.0):
                raise ValueError(
                    f"陳設類別 '{name}' 的 {key} Hz 吸音係數 {value} 不在 0–1 之間"
                )

        if not item.get("source", "").strip():
            raise ValueError(f"陳設類別 '{name}' 的 'source' 欄位不能是空字串")

    return data


def alpha_list(item: dict[str, Any], band_freqs: list[int]) -> list[float]:
    """把陳設類別的 alpha dict 依頻段順序轉成 list[float]。缺頻段就拋錯，不補零。"""
    alphas = []
    for freq in band_freqs:
        key = str(freq)
        if key not in item["alpha"]:
            raise KeyError(f"陳設類別 '{item.get('ade_name', '?')}' 缺少 {key} Hz 的吸音係數")
        alphas.append(float(item["alpha"][key]))
    return alphas


@dataclass
class FurnishingEstimate:
    """單張照片（或單一環景）的陳設偵測結果。

    `categories` 的 key 是 `ade_name`（furnishings.json 的類別英文名，天然唯一），
    value 是 `{"ratio": 佔全圖像素比例（已套用 cap）, "alpha": [六頻段 α]}`。
    這裡**不換算成 m²**——需要 `S_total`（表面積總和）才能換算，那是 T-32 在
    `compute_acoustics()` 裡做的事（本模組不碰幾何）。
    """

    categories: dict[str, dict[str, Any]]
    total_ratio: float
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "categories": {
                name: {"ratio": round(v["ratio"], 5), "alpha": v["alpha"]}
                for name, v in self.categories.items()
            },
            "total_ratio": round(self.total_ratio, 5),
            "warnings": self.warnings,
            "notes": self.notes,
        }


def estimate_furnishings(
    detail: dict[str, Any], data: dict[str, Any] | None = None
) -> FurnishingEstimate | None:
    """從 `surfaces_from_preprocess()` 回傳的 `detail` 估算陳設比例。

    `detail["class_ratios"]`：透視照是 `{"single": {ade_id: ratio}}`；
    環景是 `{view_name: {ade_id: ratio}}`（六視角各一份）——**取平均**
    （環景没有哪一面陳設比較「代表全屋」，六視角平均是唯一不偏袒單一視角的作法）。

    `detail` 沒有 `class_ratios`（例如舊版 detail、或呼叫端沒跑
    `surfaces_from_preprocess()`）→ 回傳 `None`，不拋錯（防呆）。
    """
    class_ratios = detail.get("class_ratios")
    if not class_ratios:
        return None

    if data is None:
        data = load_furnishings()
    band_freqs = data["band_center_freqs_hz"]

    view_ratio_dicts = list(class_ratios.values())
    n_views = len(view_ratio_dicts)
    if n_views == 0:
        return None

    def averaged_ratio(ade_id: int) -> float:
        total = sum(view_ratios.get(ade_id, 0.0) for view_ratios in view_ratio_dicts)
        return total / n_views

    categories: dict[str, dict[str, Any]] = {}
    for item in data["furnishings"]:
        ratio = averaged_ratio(item["ade_id"])
        if ratio < config.FURNISHING_MIN_CLASS_RATIO:
            continue
        categories[item["ade_name"]] = {"ratio": ratio, "alpha": alpha_list(item, band_freqs)}

    warnings: list[str] = []
    notes: list[str] = []

    total_ratio = sum(v["ratio"] for v in categories.values())
    if total_ratio > config.FURNISHING_TOTAL_RATIO_CAP:
        scale = config.FURNISHING_TOTAL_RATIO_CAP / total_ratio
        for v in categories.values():
            v["ratio"] *= scale
        warnings.append(
            f"陳設佔比 {total_ratio * 100:.1f}% 超過上限 "
            f"{config.FURNISHING_TOTAL_RATIO_CAP * 100:.0f}%——"
            f"可能是近拍或分割失敗，已等比例壓回。"
        )
        total_ratio = config.FURNISHING_TOTAL_RATIO_CAP

    notes.append(
        f"陳設比例取自 {n_views} 個視角平均" if n_views > 1 else "陳設比例取自單一透視視角"
    )

    return FurnishingEstimate(
        categories=categories, total_ratio=total_ratio, warnings=warnings, notes=notes
    )
