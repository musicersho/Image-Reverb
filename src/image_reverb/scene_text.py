"""T-20：文字場景描述 → 房間參數（F-16）。

不用照片，直接用文字描述場景（「大教堂」「4x3x2.5 的房間，地板鋪地毯」）產生與
照片管線相同的中間表示：`(RoomEstimate, SurfaceMaterials)`，之後接 T-13 → T-14 不變。

**v1 是 preset 庫＋關鍵字比對＋顯式參數抽取，不是自然語言理解**：
- 場景由 `data/scene_presets.json` 的關鍵字選出（最長命中優先）；
- 顯式尺寸（`4x3x2.5`）與材質關鍵字（「地毯」「木地板」…）可覆寫 preset；
- **比不中就報錯並列出全部可用場景，禁止安靜 fallback**（Phase 0 三次實證：
  「安靜地輸出看似合理的錯誤結果」是本專案最危險的失敗型態）；
- 非建築空間（車內/機艙…）明確拒絕，導向照片輸入＋手動覆寫；
- 不接外部 LLM API（SPEC §4 隱私原則：本機執行）。

輸出 `dims_source = "text_description"`；所有假設（preset 選擇、覆寫、近似）
都寫進 notes/warnings，如實透傳到下游 JSON。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import config
from .geometry import RoomEstimate
from .materials import SurfaceMaterials, get_material, load_materials

SCENE_PRESETS_PATH = config.PROJECT_ROOT / "data" / "scene_presets.json"

# 顯式尺寸：4x3x2.5 / 4×3×2.5 / 4*3*2.5（單位公尺）
_DIMS_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s*[x×X\*]\s*(\d+(?:\.\d+)?)\s*[x×X\*]\s*(\d+(?:\.\d+)?)"
)

# 大小修飾詞（刻意用完整詞組，不用單字「大」「小」——否則「大教堂」會被誤判成放大）
_ENLARGE_WORDS = ("很大", "大一點", "大型", "巨大", "寬敞", "spacious", "large ")
_SHRINK_WORDS = ("很小", "小一點", "小型", "狹小", "狹窄", "tiny", "cramped")
_ENLARGE_FACTOR = 1.3
_SHRINK_FACTOR = 0.75

# 材質關鍵字 → (表面, 材質 id)。「窗簾」「玻璃牆」各取一面牆近似（v1 簡化，會記 notes）
_MATERIAL_KEYWORDS: list[tuple[tuple[str, ...], str, str, str]] = [
    # (關鍵字們, 表面, 材質id, 說明)
    (("地毯", "carpet"), "floor", "carpet", "地板覆寫為地毯"),
    (("木地板", "木質地板", "wooden floor"), "floor", "wood_panel", "地板覆寫為木地板"),
    (("磁磚", "大理石", "石地板", "marble", "tile"), "floor", "marble", "地板覆寫為磁磚/大理石（以 marble 近似）"),
    (("窗簾", "布幕", "curtain"), "north", "curtain_fabric", "一面牆（north）覆寫為窗簾/布幕近似"),
    (("吸音板", "acoustic panel"), "ceiling", "acoustic_panel", "天花板覆寫為吸音板"),
    (("玻璃牆", "落地窗", "glass wall"), "south", "glass", "一面牆（south）覆寫為玻璃近似"),
]


@dataclass
class ParsedScene:
    """文字解析結果：與照片管線同型的中間表示＋可追溯的解析紀錄。"""

    estimate: RoomEstimate
    surfaces: SurfaceMaterials
    preset_id: str
    preset_name_zh: str
    parse_notes: list[str] = field(default_factory=list)


def load_scene_presets(path: str | Path | None = None) -> dict[str, Any]:
    path = Path(path) if path is not None else SCENE_PRESETS_PATH
    if not path.exists():
        raise FileNotFoundError(f"找不到場景 preset 庫：{path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"場景 preset 庫 {path} 不是合法的 JSON（第 {e.lineno} 行：{e.msg}）。"
            f"可用 `git checkout data/scene_presets.json` 還原。"
        ) from e
    if "presets" not in data or not data["presets"]:
        raise ValueError(f"場景 preset 庫 {path} 缺少非空的 'presets' 欄位。")
    return data


def available_scenes_text(data: dict[str, Any] | None = None) -> str:
    """給錯誤訊息用：列出全部可用場景與代表關鍵字。"""
    if data is None:
        data = load_scene_presets()
    lines = []
    for p in data["presets"]:
        kws = "、".join(p["keywords_zh"][:3])
        lines.append(f"  {p['id']:<14} {p['name_zh']}（關鍵字：{kws}…）")
    return "\n".join(lines)


def _check_unsupported(text: str, data: dict[str, Any]) -> None:
    """非建築空間明確拒絕（Phase 0 實證不可靠，文字路徑更沒有資訊救它）。"""
    hits = [
        kw
        for kw in data.get("unsupported_keywords_zh", []) + data.get("unsupported_keywords_en", [])
        if kw.lower() in text.lower()
    ]
    if hits:
        raise ValueError(
            f"描述包含「{hits[0]}」——非建築空間不在文字場景的支援範圍。\n"
            f"原因：{data.get('unsupported_reason', '')}"
        )


def _match_preset(text: str, data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """關鍵字比對選 preset：以「命中關鍵字總長度」計分，最長命中優先。

    回傳 (最佳 preset, 其他也命中的 preset 名稱清單——供警示用)。
    比不中 → 拋 ValueError 列出全部可用場景（禁止安靜 fallback）。
    """
    lowered = text.lower()
    scored: list[tuple[int, dict[str, Any]]] = []
    for p in data["presets"]:
        score = sum(
            len(kw)
            for kw in p["keywords_zh"] + [k.lower() for k in p["keywords_en"]]
            if kw and kw.lower() in lowered
        )
        if score > 0:
            scored.append((score, p))
    if not scored:
        raise ValueError(
            "無法從描述辨識出場景類型（不會亂猜——Phase 0 實證安靜 fallback 是最危險的失敗）。\n"
            "可用的場景：\n" + available_scenes_text(data) + "\n"
            "格式範例：「浴室」「4x3x2.5 的房間，地板鋪地毯」「大教堂」"
        )
    scored.sort(key=lambda s: -s[0])
    best = scored[0][1]
    others = [p["name_zh"] for _, p in scored[1:]]
    return best, others


def parse_scene_text(
    text: str,
    presets_data: dict[str, Any] | None = None,
    materials_data: dict[str, Any] | None = None,
) -> ParsedScene:
    """主入口：文字描述 → (RoomEstimate, SurfaceMaterials)。"""
    if not text or not text.strip():
        raise ValueError("場景描述不能是空字串。範例：「浴室」「4x3x2.5 的房間，地板鋪地毯」")
    if presets_data is None:
        presets_data = load_scene_presets()
    if materials_data is None:
        materials_data = load_materials()

    _check_unsupported(text, presets_data)
    preset, other_matches = _match_preset(text, presets_data)

    notes: list[str] = [f"文字場景：採用 preset '{preset['id']}'（{preset['name_zh']}）"]
    if preset.get("note"):
        notes.append(f"preset 近似說明：{preset['note']}")
    warnings: list[str] = []
    if other_matches:
        warnings.append(
            f"描述同時命中其他場景（{'、'.join(other_matches)}），已採用最長命中的"
            f"「{preset['name_zh']}」；若不對請描述得更明確或直接給尺寸/材質"
        )

    # --- 尺寸：preset → 大小修飾詞 → 顯式尺寸（後者覆蓋前者）---
    dims = [float(v) for v in preset["dims_m"]]
    confidence = preset["confidence"]

    for words, factor, label in (
        (_ENLARGE_WORDS, _ENLARGE_FACTOR, "放大"),
        (_SHRINK_WORDS, _SHRINK_FACTOR, "縮小"),
    ):
        hit = next((w for w in words if w in text.lower()), None)
        if hit:
            dims = [d * factor for d in dims]
            notes.append(f"大小修飾詞「{hit.strip()}」：尺寸{label} ×{factor}（近似規則）")
            break

    m = _DIMS_PATTERN.search(text)
    if m:
        dims = [float(m.group(i)) for i in (1, 2, 3)]
        if any(d <= 0 for d in dims):
            raise ValueError(f"顯式尺寸 {m.group(0)} 含零或負值，無法建立房間。")
        confidence = "high"
        notes.append(f"顯式尺寸：{dims[0]}×{dims[1]}×{dims[2]} m（覆寫 preset 典型值，confidence 升 high）")

    # --- 材質：preset 六面 → 材質關鍵字覆寫 ---
    surfaces = SurfaceMaterials(**dict(preset["surfaces"]))
    for name in surfaces.as_dict():
        surfaces.sources[name] = f"text_preset:{preset['id']}"
    for keywords, surface_name, material_id, desc in _MATERIAL_KEYWORDS:
        if any(kw.lower() in text.lower() for kw in keywords):
            get_material(material_id, materials_data)  # 早驗證
            surfaces.set_surface(surface_name, material_id, source="text_keyword")
            notes.append(f"材質關鍵字：{desc}")
    surfaces.validate(materials_data)
    surfaces.warnings.extend(warnings)

    if preset["confidence"] == "low":
        surfaces.warnings.append(
            f"場景「{preset['name_zh']}」的 preset 標為低信心（{preset.get('note', '變異大')}），"
            f"數字僅供參考，建議顯式給尺寸"
        )

    estimate = RoomEstimate(
        length_m=dims[0],
        width_m=dims[1],
        height_m=dims[2],
        confidence=confidence,
        dims_source="text_description",
        notes=notes,
    )
    return ParsedScene(
        estimate=estimate,
        surfaces=surfaces,
        preset_id=preset["id"],
        preset_name_zh=preset["name_zh"],
        parse_notes=notes,
    )
