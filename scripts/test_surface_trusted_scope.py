#!/usr/bin/env python3
"""T-24 迴歸測試：ADE 可信材質死碼移除後的不變量（裁決 T-24-A，REPORT §2.6 缺陷 D）。

背景：`surfaces.py` 曾有一段「語意可信類別」（mirror、windowpane、curtain 等）
計分邏輯 `ADE_TRUSTED_MATERIAL`，想在角色 mask 內統計這些類別佔比、額外加註 note。
規劃者裁決 T-24-A 認定它在構造上不可達——ADE20K 每個像素只有一個 label，
可信類別 id 與 floor/ceiling/wall 三個角色的 id 集合**互不相交**，
在角色 mask 內恆量不到任何像素——並裁定移除，可信類別清單搬去 T-27 當設計輸入。

本測試斷言移除後的兩個不變量：
  1. `surfaces` 模組**不再有** `ADE_TRUSTED_MATERIAL` 這個屬性
  2. `analyse_image` 的輸出 note **不含**「語意可信」字樣（樁掉 segmenter 與
     `classify_region_material`，不下載、不跑真模型，構造一張刻意塞滿舊可信類別
     id 的合成 labelmap，確認就算像素在圖上出現，也不會被算進任何角色的 note）

跑法：`python scripts/test_surface_trusted_scope.py`；全部通過 exit 0，
任一失敗 exit 1。

診斷力：這支測試在移除前的舊碼上必須 fail（模組仍有 `ADE_TRUSTED_MATERIAL`
屬性）——自我檢查已用 `git stash` 實測並附輸出。
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


# 舊 ADE_TRUSTED_MATERIAL 表用過的 id（8 windowpane、18 curtain、23 sofa……）——
# 測試自己保留這份清單，不從 surfaces 模組匯入（模組移除後已經沒有這個常數了）。
_OLD_TRUSTED_IDS = [8, 9, 12, 18, 23, 27, 30, 31, 147]


def _build_synthetic_labelmap(size: int = 100) -> np.ndarray:
    """上半塞滿舊可信類別 id（逐列輪流塞入 `_OLD_TRUSTED_IDS`）；
    下半左半是 floor（id=3），右半是 ceiling（id=5）。
    floor / ceiling 的 mask 跟這些舊可信類別 id 完全不重疊。
    """
    labelmap = np.zeros((size, size), dtype=np.int32)
    half = size // 2
    for row in range(half):
        labelmap[row, :] = _OLD_TRUSTED_IDS[row % len(_OLD_TRUSTED_IDS)]
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
    # 的 note，讓測試只看有沒有殘留可信類別相關的 note 文字。
    return "gypsum_board", 0.9, [("gypsum_board", 0.9)], "clip"


def main() -> int:
    print("【1】surfaces 模組不再有 ADE_TRUSTED_MATERIAL 屬性")
    check(
        "hasattr(surfaces, 'ADE_TRUSTED_MATERIAL') 為 False",
        not hasattr(surfaces, "ADE_TRUSTED_MATERIAL"),
        f"hasattr = {hasattr(surfaces, 'ADE_TRUSTED_MATERIAL')}",
    )

    print("【2】analyse_image 的輸出 note 不含「語意可信」字樣")

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
            f"'{role}' 的 note 不含「語意可信」字樣",
            "語意可信" not in note,
            f"note = {note!r}",
        )

    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 項失敗：{'、'.join(FAILURES)}")
        return 1
    print("✅ T-24 死碼移除不變量測試全部通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
