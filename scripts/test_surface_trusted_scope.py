#!/usr/bin/env python3
"""T-24 迴歸測試：ADE 可信材質分支的計分範圍（REPORT §2.6 缺陷 D）。

背景：`surfaces.py` 的 `trusted_hits` 曾經拿 `segment_roles()` 回傳的**全圖**
`ratios`（`count/total_pixels`）去跟每個角色比對，完全沒被角色 mask 限制。
Opus 執行期重現過：windowpane（語意可信 → glass）全部集中在畫面上半時，
`floor` 與 `ceiling`（都在下半、跟 windowpane 零重疊）的 note 卻雙雙宣稱
「40% 屬語意可信類別」。

本測試構造一張合成 labelmap：上半全是 windowpane（id=8，語意可信類別），
下半左邊是 floor（id=3）、右邊是 ceiling（id=5）——floor/ceiling 的 mask
跟 windowpane 完全不重疊。斷言修好之後 floor 與 ceiling 的 note **不再**
宣稱自己有語意可信類別。

`segment_roles` 與 `classify_region_material` 都用樁（stub）換掉，不下載、
不跑真正的模型，純測計分邏輯。

跑法：`python scripts/test_surface_trusted_scope.py`；全部通過 exit 0，
任一失敗 exit 1。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from src.image_reverb import surfaces  # noqa: E402

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  {'✅' if ok else '❌'} {name}：{detail}")
    if not ok:
        FAILURES.append(name)


def _build_synthetic_labelmap(size: int = 100) -> np.ndarray:
    """上半（size//2 列）全是 windowpane（id=8，語意可信→glass）；
    下半左半是 floor（id=3），右半是 ceiling（id=5）。
    floor / ceiling 的 mask 跟 windowpane 完全不重疊。
    """
    labelmap = np.zeros((size, size), dtype=np.int32)
    half = size // 2
    labelmap[:half, :] = 8  # windowpane（全圖上半）
    labelmap[half:, :half] = 3  # floor（下半左邊）
    labelmap[half:, half:] = 5  # ceiling（下半右邊）
    return labelmap


def _fake_segment_roles(img, processor, model):
    labelmap = _build_synthetic_labelmap()
    total = labelmap.size
    ids, counts = np.unique(labelmap, return_counts=True)
    ratios = {int(i): float(c) / total for i, c in zip(ids, counts)}
    return labelmap, ratios


def _fake_classify_region_material(img, mask, clip_processor, clip_model, threshold):
    # 固定回傳一個高信心 CLIP 結果，method="clip"，不觸發 fallback/out_of_domain
    # 的 note，讓測試只看 trusted_hits 那段邏輯有沒有被角色 mask 限制住。
    return "gypsum_board", 0.9, [("gypsum_board", 0.9)], "clip"


def main() -> int:
    print("【1】計分範圍修好之後：floor / ceiling 不該再宣稱有語意可信類別")

    # 換掉會下載/跑真模型的兩個函式
    real_segment_roles = surfaces.segment_roles
    real_classify = surfaces.classify_region_material
    surfaces.segment_roles = _fake_segment_roles
    surfaces.classify_region_material = _fake_classify_region_material
    try:
        img = Image.new("RGB", (100, 100))
        result = surfaces.analyse_image(
            img, seg=("stub_processor", "stub_model"), clip=("stub_processor", "stub_model")
        )
    finally:
        surfaces.segment_roles = real_segment_roles
        surfaces.classify_region_material = real_classify

    observations = result["observations"]

    for role in ("floor", "ceiling"):
        check(
            f"'{role}' 有被判定出來（synthetic labelmap 有足夠面積）",
            role in observations,
            f"observations keys = {list(observations.keys())}",
        )
        if role not in observations:
            continue
        note = observations[role].note
        check(
            f"'{role}' 的 note 不宣稱擁有語意可信類別（跟 windowpane 完全沒重疊）",
            "語意可信類別" not in note,
            f"note = {note!r}",
        )

    print("【2】windowpane 本身若被判成某個角色，才應該看到可信類別 note")
    # windowpane 是 id=8，不在 ADE_FLOOR_IDS / ADE_CEILING_IDS / ADE_WALL_IDS
    # 任何一個角色 id 集合裡，所以在這張合成圖裡它不會被判成任何角色——
    # 這正是「floor/ceiling 不該被污染」的對照組，此處只需確認 wall 沒被誤判。
    check(
        "'wall' 沒有被判定出來（synthetic labelmap 裡沒有牆類別）",
        "wall" not in observations,
        f"observations keys = {list(observations.keys())}",
    )

    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 項失敗：{'、'.join(FAILURES)}")
        return 1
    print("✅ T-24 ADE 可信材質計分範圍測試全部通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
