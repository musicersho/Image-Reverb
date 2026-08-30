#!/usr/bin/env python3
"""T-23 迴歸測試：fallback 材質的單一事實來源。

背景：`data/materials.json` 曾寫 `generic_wall`，但 `config.py` 卻寫死
`gypsum_board`，兩處說法不一致、`surfaces.py` docstring 又講第三種說法。
本測試斷言 `config.DEFAULT_WALL_MATERIAL` 是**從 materials.json 動態讀出**的
`fallback_id`，而不是任何地方寫死的字面值——只要兩邊再度分歧，這支測試就會 fail。

跑法：`python scripts/test_material_fallback.py`（純資料，不依賴模型下載）；
全部通過 exit 0，任一失敗 exit 1。
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.image_reverb import config  # noqa: E402
from src.image_reverb.materials import load_materials  # noqa: E402

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  {'✅' if ok else '❌'} {name}：{detail}")
    if not ok:
        FAILURES.append(name)


def main() -> int:
    print("【1】config.DEFAULT_WALL_MATERIAL 與 materials.json 的 fallback_id 一致")

    # 直接讀原始 JSON（不透過 config，避免測試跟被測程式共用同一條讀取路徑
    # 而失去診斷力）
    with open(config.MATERIALS_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)
    fallback_id = raw["fallback_id"]

    check(
        "config.DEFAULT_WALL_MATERIAL == materials.json['fallback_id']",
        config.DEFAULT_WALL_MATERIAL == fallback_id,
        f"config={config.DEFAULT_WALL_MATERIAL!r}，json={fallback_id!r}",
    )

    print("【2】fallback_id 必須是材質表裡真的存在的材質")
    materials = load_materials()
    known_ids = {m["id"] for m in materials["materials"]}
    check(
        f"'{fallback_id}' 存在於 materials.json 的 materials 清單",
        fallback_id in known_ids,
        f"materials 清單有 {len(known_ids)} 筆",
    )

    print("【3】現行實際行為值（REPORT §2.6 缺陷 F 的裁決）")
    check(
        "fallback_id == 'gypsum_board'（不是曾誤寫的 'generic_wall'）",
        fallback_id == "gypsum_board",
        f"實際值 {fallback_id!r}",
    )

    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 項失敗：{'、'.join(FAILURES)}")
        return 1
    print("✅ T-23 fallback 材質單一事實來源測試全部通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
