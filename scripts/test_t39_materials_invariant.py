#!/usr/bin/env python3
"""T-39 迴歸測試：候選材質集擴充不得動到既有 12 種材質／12 條提示詞字串。

背景：T-38B 已實證「改既有候選字串」有害無益（見 output/clip_treatment/
rounds/round7~10）；T-39 的範圍紅線明文規定既有 12 條 CLIP_MATERIAL_PROMPTS
字串與既有 12 種材質的 alpha 逐位元不變。本測試把 T-39 之前的 12 種材質
alpha 與 12 條提示詞字串**逐位元寫死**成期望值（修 bug 類的測試，對照
data/materials.json 與 src/image_reverb/surfaces.py 的既有 12 條）；同時驗證
T-39 新增的 3 種材質／3 條提示詞確實存在且數值與出處對應。

跑法：`python scripts/test_t39_materials_invariant.py`（純資料，不依賴模型
下載）；全部通過 exit 0，任一失敗 exit 1。

**對舊碼（T-39 之前）必然 fail**：舊碼的 materials.json 沒有 vinyl_panel／
rubber_flooring／metal_roof_deck 三筆，舊碼的 surfaces.py 沒有對應三條
CLIP_MATERIAL_PROMPTS——【3】【4】會直接 KeyError／assert fail。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.image_reverb.materials import load_materials, get_material  # noqa: E402
from src.image_reverb import surfaces  # noqa: E402

FAILURES: list[str] = []

# T-39 之前既有的 12 種材質 alpha（逐位元寫死，來源：T-03 data/materials.json，
# T-39 開工前用 `git show HEAD~1:data/materials.json` 核對過的既有內容）
FROZEN_ALPHA = {
    "concrete": {"125": 0.01, "250": 0.01, "500": 0.02, "1000": 0.02, "2000": 0.02, "4000": 0.03},
    "brick": {"125": 0.03, "250": 0.03, "500": 0.03, "1000": 0.04, "2000": 0.05, "4000": 0.07},
    "wood_panel": {"125": 0.28, "250": 0.22, "500": 0.17, "1000": 0.09, "2000": 0.1, "4000": 0.11},
    "gypsum_board": {"125": 0.29, "250": 0.1, "500": 0.05, "1000": 0.04, "2000": 0.07, "4000": 0.09},
    "glass": {"125": 0.35, "250": 0.25, "500": 0.18, "1000": 0.12, "2000": 0.07, "4000": 0.04},
    "marble": {"125": 0.01, "250": 0.01, "500": 0.01, "1000": 0.01, "2000": 0.02, "4000": 0.02},
    "carpet": {"125": 0.02, "250": 0.06, "500": 0.14, "1000": 0.37, "2000": 0.6, "4000": 0.65},
    "curtain_fabric": {"125": 0.14, "250": 0.35, "500": 0.55, "1000": 0.72, "2000": 0.7, "4000": 0.65},
    "acoustic_panel": {"125": 0.08, "250": 0.25, "500": 0.65, "1000": 0.85, "2000": 0.95, "4000": 0.9},
    "audience_seating": {"125": 0.6, "250": 0.74, "500": 0.88, "1000": 0.96, "2000": 0.93, "4000": 0.85},
    "grass_soil": {"125": 0.11, "250": 0.26, "500": 0.6, "1000": 0.69, "2000": 0.92, "4000": 0.99},
    "generic_wall": {"125": 0.013, "250": 0.015, "500": 0.02, "1000": 0.03, "2000": 0.04, "4000": 0.05},
}

# T-39 之前既有的 12 條 CLIP_MATERIAL_PROMPTS 字串（逐位元寫死）
FROZEN_PROMPTS = {
    "concrete": "a smooth poured concrete surface",
    "brick": "a bare unglazed brick surface",
    "wood_panel": "a wooden panel or wood plank surface",
    "gypsum_board": "a painted plasterboard drywall surface",
    "glass": "a pane of clear glass or a window",
    "marble": "a polished marble or ceramic tile surface",
    "carpet": "a thick carpet or textile floor covering",
    "curtain_fabric": "a heavy fabric curtain or drape",
    "acoustic_panel": "a fibrous acoustic absorption panel",
    "audience_seating": "rows of upholstered seats with an audience",
    "grass_soil": "natural grass or bare soil ground",
    "generic_wall": "a plain smooth plastered wall",
}

# T-39 新增的 3 種材質 alpha（出處見 data/materials.json 各自 source 欄位）
NEW_ALPHA = {
    "vinyl_panel": {"125": 0.02, "250": 0.02, "500": 0.03, "1000": 0.04, "2000": 0.04, "4000": 0.05},
    "rubber_flooring": {"125": 0.05, "250": 0.05, "500": 0.1, "1000": 0.1, "2000": 0.05, "4000": 0.05},
    "metal_roof_deck": {"125": 0.13, "250": 0.09, "500": 0.08, "1000": 0.09, "2000": 0.11, "4000": 0.11},
}

NEW_PROMPTS = {
    "vinyl_panel": "a smooth glossy plastic or vinyl panel surface, non-porous",
    "rubber_flooring": "a dark rubber or vinyl composition floor mat with a matte non-porous surface",
    "metal_roof_deck": (
        "a rigid painted sheet metal surface with visible corrugated or ribbed"
        " ridges and a dull metallic sheen, not fabric or cloth"
    ),
}


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  {'✅' if ok else '❌'} {name}：{detail}")
    if not ok:
        FAILURES.append(name)


def main() -> int:
    data = load_materials()

    print("【1】既有 12 種材質的 alpha 逐位元不變")
    for mid, expected in FROZEN_ALPHA.items():
        mat = get_material(mid, data)
        check(f"{mid}.alpha", mat["alpha"] == expected, f"{mat['alpha']} == {expected}")

    print("【2】既有 12 條 CLIP_MATERIAL_PROMPTS 字串逐位元不變")
    for mid, expected in FROZEN_PROMPTS.items():
        actual = surfaces.CLIP_MATERIAL_PROMPTS.get(mid)
        check(f"CLIP_MATERIAL_PROMPTS['{mid}']", actual == expected, f"{actual!r} == {expected!r}")

    print("【3】T-39 新增的 3 種材質 alpha 與出處存在")
    for mid, expected in NEW_ALPHA.items():
        mat = get_material(mid, data)
        check(f"{mid}.alpha", mat["alpha"] == expected, f"{mat['alpha']} == {expected}")
        check(f"{mid}.source 非空", bool(mat.get("source", "").strip()), f"source 長度 {len(mat.get('source', ''))}")

    print("【4】T-39 新增的 3 條 CLIP_MATERIAL_PROMPTS 字串存在")
    for mid, expected in NEW_PROMPTS.items():
        actual = surfaces.CLIP_MATERIAL_PROMPTS.get(mid)
        check(f"CLIP_MATERIAL_PROMPTS['{mid}']", actual == expected, f"{actual!r} == {expected!r}")

    print("【5】CLIP_OOD_PROMPTS 與門檻 0.4 零改動（T-39 範圍紅線）")
    from src.image_reverb import config
    check(
        "CLIP_OOD_PROMPTS 仍是 4 個域外候選",
        set(surfaces.CLIP_OOD_PROMPTS.keys())
        == {"__vehicle_interior", "__outdoor_scene", "__object_closeup", "__person"},
        f"{list(surfaces.CLIP_OOD_PROMPTS.keys())}",
    )
    check(
        "CLIP_CONFIDENCE_THRESHOLD 仍是 0.4",
        config.CLIP_CONFIDENCE_THRESHOLD == 0.4,
        f"實際值 {config.CLIP_CONFIDENCE_THRESHOLD}",
    )

    print("【6】materials.json 恰好 15 種材質（12 舊 + 3 新，無多無少）")
    all_ids = {m["id"] for m in data["materials"]}
    expected_ids = set(FROZEN_ALPHA) | set(NEW_ALPHA)
    check("材質 id 集合完全相符", all_ids == expected_ids, f"{sorted(all_ids)}")

    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 項失敗：{'、'.join(FAILURES)}")
        return 1
    print("✅ T-39 材質不變性測試全部通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
