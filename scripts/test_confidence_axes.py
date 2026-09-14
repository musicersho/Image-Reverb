#!/usr/bin/env python3
"""T-25 迴歸測試：confidence 拆成幾何／材質／overall 三軸（REPORT §2.5 缺陷 B）。

背景：舊行為（`pipeline.py` 舊版 `run_photo`）把輸出的 `confidence` 直接設成
`est.confidence`——只反映幾何，材質是不是用猜的（fallback／out_of_domain／
六面全部退化成同一種）完全沒有訊號透出去。T-17 §7-1 的臥室因此被標成
`medium`，但地板其實是 fallback（沒判到）；五個 `--override-dims` 的 run
也全部拿到 `high`，材質同樣是猜的。

本測試分兩部分：
  A. `pipeline._overall_confidence()`——兩軸取較低者的合併邏輯
  B. `surfaces.compute_materials_confidence()`——材質信心的四條判定規則
（純資料測試，不下載模型，跑起來快。）

跑法：`python scripts/test_confidence_axes.py`；
全部通過 exit 0，任一失敗 exit 1。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.image_reverb.materials import SURFACE_NAMES, SurfaceMaterials  # noqa: E402
from src.image_reverb.pipeline import _overall_confidence  # noqa: E402
from src.image_reverb.surfaces import compute_materials_confidence  # noqa: E402

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  {'✅' if ok else '❌'} {name}：{detail}")
    if not ok:
        FAILURES.append(name)


# 六種不同材質，讓 SurfaceMaterials 不是「六面同材質」的退化狀態
_DISTINCT = dict(
    floor="carpet", ceiling="gypsum_board", west="brick",
    east="concrete", south="wood_panel", north="glass",
)


def _surf_with_sources(sources_by_face: dict[str, str], warnings: list[str] | None = None) -> SurfaceMaterials:
    """建一個六面材質互不相同的 SurfaceMaterials，逐面套用指定的 source。"""
    surf = SurfaceMaterials(**_DISTINCT)
    for name in SURFACE_NAMES:
        surf.sources[name] = sources_by_face.get(name, "clip")
    if warnings:
        surf.warnings.extend(warnings)
    return surf


def _surf_with_scope(
    sources_by_face: dict[str, str],
    scope_by_face: dict[str, str] | None = None,
    warnings: list[str] | None = None,
) -> SurfaceMaterials:
    """T-52【C】R1b 測試用：在 `_surf_with_sources()` 之上再逐面套用 `candidate_scope`
    （未指定的面預設 `"global"`）。用 `hasattr` 探測而不是直接賦值——對舊碼（T-52 之前，
    `SurfaceMaterials` 沒有 `candidate_scope` 欄位）跑本測試時，這裡會靜默跳過設定
    （效果等同舊碼從不知道 role scope 這回事），讓測試能同時對新舊碼跑同一份斷言，
    而不是在舊碼上因為 AttributeError 整批崩潰。"""
    surf = _surf_with_sources(sources_by_face, warnings)
    if hasattr(surf, "candidate_scope"):
        scope_by_face = scope_by_face or {}
        for name in SURFACE_NAMES:
            surf.candidate_scope[name] = scope_by_face.get(name, "global")
    return surf


def main() -> int:
    print("【A】pipeline._overall_confidence()：overall = 兩軸取較低者（卡片指定的三個案例）")
    check(
        "幾何 high ＋ 材質 low → overall low",
        _overall_confidence("high", "low") == "low",
        f"實際={_overall_confidence('high', 'low')!r}",
    )
    check(
        "兩者皆 medium → overall medium",
        _overall_confidence("medium", "medium") == "medium",
        f"實際={_overall_confidence('medium', 'medium')!r}",
    )
    check(
        "幾何 low ＋ 材質 high → overall low",
        _overall_confidence("low", "high") == "low",
        f"實際={_overall_confidence('low', 'high')!r}",
    )
    # 補兩個邊界案例：同值不變、反過來（材質較高）也要取較低者，確認不是只挑第一個參數
    check(
        "兩者皆 high → overall high",
        _overall_confidence("high", "high") == "high",
        f"實際={_overall_confidence('high', 'high')!r}",
    )
    check(
        "幾何 medium ＋ 材質 high → overall medium（取較低者，不是永遠回傳第一個參數）",
        _overall_confidence("medium", "high") == "medium",
        f"實際={_overall_confidence('medium', 'high')!r}",
    )

    print("【B】surfaces.compute_materials_confidence()：材質信心四條判定規則")

    surf_high = _surf_with_sources({n: "clip" for n in SURFACE_NAMES})
    check(
        "六面皆 clip 且無警示 → high",
        compute_materials_confidence(surf_high) == "high",
        f"實際={compute_materials_confidence(surf_high)!r}",
    )

    surf_medium = _surf_with_sources(
        {n: "clip" for n in SURFACE_NAMES},
        warnings=["單張透視照看不到背後的牆，四面牆共用同一個材質判定值。"],
    )
    check(
        "六面皆 clip 但有警示 → medium（不是 high）",
        compute_materials_confidence(surf_medium) == "medium",
        f"實際={compute_materials_confidence(surf_medium)!r}",
    )

    surf_override = _surf_with_sources({n: "manual_override" for n in SURFACE_NAMES})
    check(
        "六面皆手動覆寫、材質互不相同、無警示 → medium（非 clip 就不給 high，也非 fallback/退化不給 low）",
        compute_materials_confidence(surf_override) == "medium",
        f"實際={compute_materials_confidence(surf_override)!r}",
    )

    surf_fallback = _surf_with_sources({**{n: "clip" for n in SURFACE_NAMES}, "floor": "fallback"})
    check(
        "任一面 source 是 fallback → low（即使其餘五面都是 clip）",
        compute_materials_confidence(surf_fallback) == "low",
        f"實際={compute_materials_confidence(surf_fallback)!r}",
    )

    surf_ood = _surf_with_sources({**{n: "clip" for n in SURFACE_NAMES}, "west": "out_of_domain"})
    check(
        "任一面 source 是 out_of_domain → low",
        compute_materials_confidence(surf_ood) == "low",
        f"實際={compute_materials_confidence(surf_ood)!r}",
    )

    surf_uniform = SurfaceMaterials()  # 預設六面都是 config.DEFAULT_WALL_MATERIAL，退化案例
    for n in SURFACE_NAMES:
        surf_uniform.sources[n] = "clip"
    check(
        "六面材質全部相同（退化）→ low，即使來源全是 clip 且無額外警示",
        compute_materials_confidence(surf_uniform) == "low",
        f"實際={compute_materials_confidence(surf_uniform)!r}（六面材質：{surf_uniform.unique_ids()}）",
    )

    print(
        "【C】T-52 R1b（裁決 T-47-A 選項乙，gate v2）："
        "role_aware 收窄候選集的 clip 面不計入放行"
    )
    _SINGLE_PERSPECTIVE_NOTE = "單張透視照看不到背後的牆，四面牆共用同一個材質判定值。"

    # (a) role_aware、floor 為 clip 且 candidate_scope["floor"]="role:floor"（收窄，6<12）→ low
    surf_r1b_a = _surf_with_scope(
        {n: "clip" for n in SURFACE_NAMES},
        {"floor": "role:floor"},
        warnings=[_SINGLE_PERSPECTIVE_NOTE],
    )
    result_a = compute_materials_confidence(surf_r1b_a)
    check(
        "(a) role_aware、floor clip 且候選集收窄（role:floor，6<12）→ low",
        result_a == "low",
        f"實際={result_a!r}",
    )
    check(
        "(a) R1b 觸發時 warnings 有記一條含面名稱／role_aware／T-47-A 的未校準警示",
        any("floor" in w and "role_aware" in w and "T-47-A" in w for w in surf_r1b_a.warnings),
        f"warnings={surf_r1b_a.warnings}",
    )

    # (b) 同一組 sources，但 scope 全部 "global"（等同 default 模式）→ medium，不受影響
    surf_r1b_b = _surf_with_scope(
        {n: "clip" for n in SURFACE_NAMES},
        {},
        warnings=[_SINGLE_PERSPECTIVE_NOTE],
    )
    result_b = compute_materials_confidence(surf_r1b_b)
    check(
        "(b) 同一組 sources、scope 全 global（default 模式等效）→ medium（不受 R1b 影響）",
        result_b == "medium",
        f"實際={result_b!r}",
    )

    # (c) 六面 manual_override（覆寫是出口）→ medium，即使殘留 scope 仍標記收窄
    surf_r1b_c = _surf_with_scope(
        {n: "manual_override" for n in SURFACE_NAMES},
        {"floor": "role:floor"},
    )
    result_c = compute_materials_confidence(surf_r1b_c)
    check(
        "(c) 六面 manual_override（覆寫是出口，R1b 只看 source=='clip'）→ medium",
        result_c == "medium",
        f"實際={result_c!r}",
    )

    # (d) role_aware、wall 為 clip 且 candidate_scope="role:wall"（12=12，不收窄）→ 不觸發 R1b
    surf_r1b_d = _surf_with_scope(
        {n: "clip" for n in SURFACE_NAMES},
        {name: "role:wall" for name in ("west", "east", "south", "north")},
    )
    result_d = compute_materials_confidence(surf_r1b_d)
    check(
        "(d) role_aware、wall clip 且候選集不收窄（role:wall，12=12）→ 不觸發 R1b，"
        "六面 clip 無警示 → high",
        result_d == "high",
        f"實際={result_d!r}；warnings={surf_r1b_d.warnings}",
    )

    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 項失敗：{'、'.join(FAILURES)}")
        return 1
    print("✅ T-25 confidence 三軸測試全部通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
