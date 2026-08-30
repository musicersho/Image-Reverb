#!/usr/bin/env python3
"""T-31 測試：室內陳設等效吸音——資料表驗證＋偵測模組（裁決 T-27-A 執行卡 1/3）。

三部分：
  【A】資料表驗證——頻段一致／α 範圍／source 非空／ade_id 與幾何角色 id 不相交
      （不相交這項自己讀 json＋surfaces 的角色 id 集合算，不透過 load_furnishings()
      是否拋錯來判斷，避免測試對被測程式的實作細節產生依賴）
  【B】合成 detail 夾具——透視單視角、環景六視角平均、cap 觸發（等比壓回＋警告）、
      低於下限忽略、無 class_ratios → None
  【C】id2label 驗證——載入 ADE20K 分割模型的 config（模型已在本機快取），逐項
      斷言 `id2label[ade_id]` 的字串包含 `ade_name`。**不許 try/except 跳過**
      （WORKFLOW.md §5 紅旗 4：try/except 把錯誤吞掉讓程式「看起來」跑完）。

跑法：`python scripts/test_furnishings.py`；全部通過 exit 0，任一失敗 exit 1。
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.image_reverb import config  # noqa: E402
from src.image_reverb.furnishings import (  # noqa: E402
    FurnishingEstimate,
    estimate_furnishings,
    load_furnishings,
)
from src.image_reverb.surfaces import ADE_CEILING_IDS, ADE_FLOOR_IDS, ADE_WALL_IDS  # noqa: E402

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  {'✅' if ok else '❌'} {name}：{detail}")
    if not ok:
        FAILURES.append(name)


def part_a() -> None:
    print("【A】資料表驗證")

    with open(config.FURNISHINGS_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)

    band_freqs = raw["band_center_freqs_hz"]
    check(
        "band_center_freqs_hz 與 materials.json 一致",
        band_freqs == [125, 250, 500, 1000, 2000, 4000],
        f"實際值 {band_freqs}",
    )

    role_ids = set(ADE_FLOOR_IDS) | set(ADE_CEILING_IDS) | set(ADE_WALL_IDS)
    overlap = [
        (item["ade_name"], item["ade_id"])
        for item in raw["furnishings"]
        if item["ade_id"] in role_ids
    ]
    check(
        "所有陳設類別的 ade_id 與幾何角色 id（floor/ceiling/wall）不相交",
        len(overlap) == 0,
        f"重疊清單 = {overlap}" if overlap else "無重疊",
    )

    for item in raw["furnishings"]:
        name = item["ade_name"]
        for freq in band_freqs:
            value = item["alpha"][str(freq)]
            check(
                f"'{name}' 的 {freq}Hz α 在 0–1 之間",
                0.0 <= value <= 1.0,
                f"值 = {value}",
            )
        check(
            f"'{name}' 的 source 非空字串",
            bool(item.get("source", "").strip()),
            f"source = {item.get('source')!r}",
        )
        check(
            f"'{name}' 的 confidence 非空字串",
            bool(item.get("confidence", "").strip()),
            f"confidence = {item.get('confidence')!r}",
        )

    # load_furnishings() 本身要能正常載入且不拋錯（正向案例）
    try:
        data = load_furnishings()
        check("load_furnishings() 正常載入（正向案例）", True, f"{len(data['furnishings'])} 個類別")
    except Exception as e:  # noqa: BLE001
        check("load_furnishings() 正常載入（正向案例）", False, f"意外拋錯：{e}")


def _make_detail(class_ratios: dict) -> dict:
    return {"mode": "test", "views": {}, "warnings": [], "class_ratios": class_ratios}


def part_b() -> None:
    print("【B】合成 detail 夾具")

    data = load_furnishings()
    curtain_id = next(i["ade_id"] for i in data["furnishings"] if i["ade_name"] == "curtain")
    bed_id = next(i["ade_id"] for i in data["furnishings"] if i["ade_name"] == "bed")

    # B1：透視單視角——curtain 佔 10%，其餘為 0
    detail = _make_detail({"single": {curtain_id: 0.10, 3: 0.40}})  # 3=floor，非陳設類別
    est = estimate_furnishings(detail, data)
    check("B1 透視單視角：回傳 FurnishingEstimate", isinstance(est, FurnishingEstimate), f"type={type(est)}")
    if est is not None:
        check(
            "B1 curtain 比例 == 0.10（單視角無平均）",
            "curtain" in est.categories and abs(est.categories["curtain"]["ratio"] - 0.10) < 1e-9,
            f"categories={est.categories}",
        )
        check("B1 沒有觸發 cap 警告", len(est.warnings) == 0, f"warnings={est.warnings}")

    # B2：環景六視角平均——curtain 只在其中一個視角出現 30%，其餘五個視角是 0%
    views = {f"view{i}": {} for i in range(5)}
    views["view5"] = {curtain_id: 0.30}
    detail = _make_detail(views)
    est = estimate_furnishings(detail, data)
    expected_ratio = 0.30 / 6
    check(
        "B2 環景六視角平均：curtain 比例 == 0.30/6",
        est is not None
        and "curtain" in est.categories
        and abs(est.categories["curtain"]["ratio"] - expected_ratio) < 1e-9,
        f"got={est.categories.get('curtain') if est else None}, expected_ratio={expected_ratio}",
    )

    # B3：cap 觸發——curtain 40% + bed 40% = 80% > 50% 上限，需等比壓回且有警告
    detail = _make_detail({"single": {curtain_id: 0.40, bed_id: 0.40}})
    est = estimate_furnishings(detail, data)
    check(
        "B3 total_ratio 被壓回到 cap（0.5）",
        est is not None and abs(est.total_ratio - config.FURNISHING_TOTAL_RATIO_CAP) < 1e-9,
        f"total_ratio={est.total_ratio if est else None}",
    )
    if est is not None:
        ratio_sum = est.categories["curtain"]["ratio"] + est.categories["bed"]["ratio"]
        check(
            "B3 逐類別比例等比例壓回後總和仍為 0.5",
            abs(ratio_sum - config.FURNISHING_TOTAL_RATIO_CAP) < 1e-9,
            f"curtain+bed = {ratio_sum}",
        )
        check(
            "B3 curtain:bed 比例維持 1:1（等比例壓回，不是誰先誰贏）",
            abs(est.categories["curtain"]["ratio"] - est.categories["bed"]["ratio"]) < 1e-9,
            f"curtain={est.categories['curtain']['ratio']}, bed={est.categories['bed']['ratio']}",
        )
        check(
            "B3 warnings 有提到超過上限",
            any("超過上限" in w for w in est.warnings),
            f"warnings={est.warnings}",
        )

    # B4：低於下限忽略——curtain 只有 0.001（< FURNISHING_MIN_CLASS_RATIO=0.005）
    detail = _make_detail({"single": {curtain_id: 0.001}})
    est = estimate_furnishings(detail, data)
    check(
        "B4 低於下限的類別被忽略（不出現在 categories）",
        est is not None and "curtain" not in est.categories,
        f"categories={est.categories if est else None}",
    )

    # B5：無 class_ratios → None
    detail = {"mode": "test", "views": {}, "warnings": []}
    est = estimate_furnishings(detail, data)
    check("B5 無 class_ratios → 回傳 None", est is None, f"got={est}")

    # B5b：class_ratios 是空 dict 也要回傳 None（防呆邊界）
    detail = _make_detail({})
    est = estimate_furnishings(detail, data)
    check("B5b class_ratios 是空 dict → 回傳 None", est is None, f"got={est}")


def part_c() -> None:
    print("【C】id2label 驗證（模型已在本機快取，直接載入 config，不 try/except 跳過）")

    from transformers import SegformerConfig

    seg_config = SegformerConfig.from_pretrained(config.SEGMENTATION_MODEL_ID)
    id2label = seg_config.id2label

    with open(config.FURNISHINGS_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)

    for item in raw["furnishings"]:
        ade_id = item["ade_id"]
        ade_name = item["ade_name"]
        label = id2label.get(ade_id, "<不存在>")
        check(
            f"id2label[{ade_id}]（'{label}'）包含 ade_name '{ade_name}'",
            ade_name in label,
            f"id2label[{ade_id}] = {label!r}",
        )


def main() -> int:
    part_a()
    print()
    part_b()
    print()
    part_c()

    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 項失敗：{'、'.join(FAILURES)}")
        return 1
    print("✅ T-31 陳設等效吸音（資料表＋偵測模組）測試全部通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
