"""T-12：材質模組 —— 材質表讀取 + 逐表面材質資料結構。

**約束 A（Phase 0 實證的硬性需求）**：材質必須逐表面指定，不可全域套單一材質。
實證：全鋪地毯 vs 只有地板鋪地毯，125 Hz RT60 差 11.8 倍（4.093s vs 0.348s），
使用者試聽形容全 carpet 版本「像用手拍鐵筒子」。根因是地毯低頻 α 只有 0.02，
套到六面等於連天花板牆壁都鋪地毯；真實房間的牆是石膏板，125 Hz 的 α = 0.29
（板共振吸音體專吃低頻）。

本模組只負責「材質資料」，不做任何聲學計算（RT60 在 T-13）。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import config

# pyroomacoustics ShoeBox 的六個面名稱（順序與 pra.ShoeBox.wall_names 一致，不要改）
SURFACE_NAMES = ("west", "east", "south", "north", "floor", "ceiling")

# 四面牆（不含地板天花板），給「walls=xxx」這種批次指定用
WALL_NAMES = ("west", "east", "south", "north")


def load_materials(path: str | Path | None = None) -> dict[str, Any]:
    """讀取 materials.json 整份 dict。

    沿用 T-03 `scripts/show_materials.py` 的介面語意（找不到檔案就拋錯，不做靜默 fallback），
    另外補上 T-03 交接筆記提到的坑：**JSON 存在但內容損毀時要有清楚訊息**，
    不能讓使用者只看到 json 模組的 `Expecting value: line 1 column 1`。
    """
    path = Path(path) if path is not None else config.MATERIALS_PATH
    if not path.exists():
        raise FileNotFoundError(f"找不到材質表：{path}（T-03 的 data/materials.json）")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"材質表 {path} 不是合法的 JSON（第 {e.lineno} 行第 {e.colno} 欄：{e.msg}）。\n"
            f"       這個檔案可能被編輯壞了；可用 `git checkout data/materials.json` 還原。"
        ) from e
    except UnicodeDecodeError as e:
        raise ValueError(
            f"材質表 {path} 不是 UTF-8 編碼的文字檔（{e.reason}）。"
        ) from e

    # 結構檢查：缺了這兩個 key，後面每個呼叫端都會炸在不同地方，不如在這裡講清楚
    for key in ("materials", "band_center_freqs_hz"):
        if key not in data:
            raise ValueError(f"材質表 {path} 缺少必要欄位 '{key}'，格式不符 T-03 的規格。")
    if not isinstance(data["materials"], list) or not data["materials"]:
        raise ValueError(f"材質表 {path} 的 'materials' 必須是非空的清單。")

    return data


def get_material(material_id: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    """依 id 取出單一材質；找不到就拋 KeyError 並列出所有可用 id。"""
    if data is None:
        data = load_materials()
    for mat in data["materials"]:
        if mat["id"] == material_id:
            return mat
    available = ", ".join(m["id"] for m in data["materials"])
    raise KeyError(f"材質表裡沒有 id '{material_id}'。可用的 id：{available}")


def alpha_list(material: dict[str, Any], band_freqs: list[int]) -> list[float]:
    """把材質的 alpha dict 依頻段順序轉成 list[float]。缺頻段就拋錯，不補零。"""
    alphas = []
    for freq in band_freqs:
        key = str(freq)
        if key not in material["alpha"]:
            raise KeyError(f"材質 '{material['id']}' 缺少 {key} Hz 的吸音係數")
        alphas.append(float(material["alpha"][key]))
    return alphas


@dataclass
class SurfaceMaterials:
    """六個面各自的材質 id（約束 A 的資料結構）。

    刻意讓六個面是六個獨立欄位而不是「一個材質 + 例外清單」——
    後者很容易在某個分支退化成全域單一材質，那正是要避免的失敗模式。

    未指定的面預設 `DEFAULT_WALL_MATERIAL`（石膏板類牆面），
    **不是**複製地板材質。這是刻意的：真實房間的牆本來就不會跟地板同材質。
    """

    floor: str = config.DEFAULT_WALL_MATERIAL
    ceiling: str = config.DEFAULT_WALL_MATERIAL
    west: str = config.DEFAULT_WALL_MATERIAL
    east: str = config.DEFAULT_WALL_MATERIAL
    south: str = config.DEFAULT_WALL_MATERIAL
    north: str = config.DEFAULT_WALL_MATERIAL

    # 每個面的材質是怎麼來的（"manual" / "clip" / "segmentation" / "default"），
    # 以及低信心警示。下游 JSON 輸出要如實帶出去，不能把猜的當成量到的。
    sources: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, str]:
        """回傳 {面名稱: 材質 id}，key 順序與 pyroomacoustics 的 wall_names 一致。"""
        return {name: getattr(self, name) for name in SURFACE_NAMES}

    def unique_ids(self) -> list[str]:
        """這組表面實際用到的材質 id（去重、保持出現順序）。"""
        seen: list[str] = []
        for mid in self.as_dict().values():
            if mid not in seen:
                seen.append(mid)
        return seen

    def is_uniform(self) -> bool:
        """六個面是不是同一種材質（= 退化成約束 A 禁止的不現實模型）。"""
        return len(self.unique_ids()) == 1

    def set_walls(self, material_id: str, source: str = "manual") -> None:
        """一次設定四面牆（不動地板與天花板）。"""
        for name in WALL_NAMES:
            setattr(self, name, material_id)
            self.sources[name] = source

    def set_surface(self, name: str, material_id: str, source: str = "manual") -> None:
        """設定單一面；面名稱打錯要立刻報錯，不要安靜忽略。"""
        if name not in SURFACE_NAMES:
            raise KeyError(
                f"未知的表面名稱 '{name}'。可用：{', '.join(SURFACE_NAMES)}，"
                f"或用 'walls' 一次指定四面牆。"
            )
        setattr(self, name, material_id)
        self.sources[name] = source

    def validate(self, data: dict[str, Any] | None = None) -> None:
        """確認六個面的材質 id 都真的存在於材質表（早失敗，不要拖到模擬時才炸）。"""
        if data is None:
            data = load_materials()
        for name, mid in self.as_dict().items():
            try:
                get_material(mid, data)
            except KeyError as e:
                raise KeyError(f"表面 '{name}' 的{e.args[0]}") from e

    def alpha_table(
        self, data: dict[str, Any] | None = None
    ) -> tuple[list[int], dict[str, list[float]]]:
        """回傳 (頻段中心頻率, {面名稱: 六頻段 α})。

        **不做任何跨面平均**——把六個面的 α 平均掉就等於繞過約束 A，
        是 T-12 卡明列的 Opus 紅旗。
        """
        if data is None:
            data = load_materials()
        band_freqs = data["band_center_freqs_hz"]
        table = {
            name: alpha_list(get_material(mid, data), band_freqs)
            for name, mid in self.as_dict().items()
        }
        return band_freqs, table


def parse_surface_spec(spec: str, data: dict[str, Any] | None = None) -> SurfaceMaterials:
    """解析 CLI 的 `--materials floor=carpet,ceiling=gypsum_board,walls=gypsum_board`。

    - `walls=xxx` 是四面牆的批次寫法；也可以逐面寫 `north=glass`。
    - 同時出現 `walls=` 與單面設定時，**後寫的覆蓋先寫的**（由左到右套用），
      所以 `walls=gypsum_board,north=glass` 的意思是「牆是石膏板，但北牆是玻璃」。
    - 沒提到的面留在預設（石膏板類牆面），不會複製地板材質。
    """
    if data is None:
        data = load_materials()

    surfaces = SurfaceMaterials()
    for name in SURFACE_NAMES:
        surfaces.sources[name] = "default"

    if not spec or not spec.strip():
        raise ValueError(
            "--materials 不能是空字串。格式範例："
            "floor=carpet,ceiling=gypsum_board,walls=gypsum_board"
        )

    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "=" not in chunk:
            raise ValueError(
                f"--materials 的 '{chunk}' 格式不對，要寫成 面=材質id。"
                f"可用的面：{', '.join(SURFACE_NAMES)}, walls（四面牆）"
            )
        key, value = (part.strip() for part in chunk.split("=", 1))
        if not value:
            raise ValueError(f"--materials 的 '{chunk}' 沒有給材質 id。")
        # 材質 id 先驗過再套用，避免一半設好一半失敗
        get_material(value, data)
        if key == "walls":
            surfaces.set_walls(value)
        else:
            surfaces.set_surface(key, value)

    return surfaces


def uniform_surfaces(material_id: str, data: dict[str, Any] | None = None) -> SurfaceMaterials:
    """六面同材質（= 舊 `--material` 的行為）。

    保留這個函式只為了向下相容 T-01/T-03 的舊介面。**這是不現實的模型**
    （地雷第 9 條），呼叫端有義務印警告；本函式自己也把警示寫進 warnings。
    """
    if data is None:
        data = load_materials()
    get_material(material_id, data)
    surfaces = SurfaceMaterials(
        floor=material_id,
        ceiling=material_id,
        west=material_id,
        east=material_id,
        south=material_id,
        north=material_id,
    )
    for name in SURFACE_NAMES:
        surfaces.sources[name] = "uniform_legacy"
    surfaces.warnings.append(
        f"六個面全部套用 '{material_id}' 是不現實的模型（T-03 地雷第 9 條）："
        f"真實房間的牆不會與地板同材質。"
    )
    return surfaces
