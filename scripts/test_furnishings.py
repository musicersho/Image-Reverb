#!/usr/bin/env python3
"""T-31 測試：室內陳設等效吸音——資料表驗證＋偵測模組（裁決 T-27-A 執行卡 1/3）。
T-35（裁決 T-33-A 裁決 A）新增【D】：陳設改預設觀測模式的 pipeline 層接線測試。

四部分：
  【A】資料表驗證——頻段一致／α 範圍／source 非空／ade_id 與幾何角色 id 不相交
      （不相交這項自己讀 json＋surfaces 的角色 id 集合算，不透過 load_furnishings()
      是否拋錯來判斷，避免測試對被測程式的實作細節產生依賴）
  【B】合成 detail 夾具——透視單視角、環景六視角平均、cap 觸發（等比壓回＋警告）、
      低於下限忽略、無 class_ratios → None
  【C】id2label 驗證——載入 ADE20K 分割模型的 config（模型已在本機快取），逐項
      斷言 `id2label[ade_id]` 的字串包含 `ade_name`。**不許 try/except 跳過**
      （WORKFLOW.md §5 紅旗 4：try/except 把錯誤吞掉讓程式「看起來」跑完）。
  【D】pipeline 層陳設三態（T-35）：比照 `test_output_gate.py` 的樁法，樁掉
      `preprocess.preprocess_image()`／`surfaces.surfaces_from_preprocess()`，
      並捕捉 `pipeline.compute_acoustics()` 實際收到的 `furnishings` 參數——
      (i) 預設 → 收到 None，analysis.json 的 furnishings.applied==False 且偵測
      欄位存在；(ii) `--furnishings` → 收到非 None，applied==True；(iii)
      `--no-furnishings` → analysis.json 的 furnishings 為 null；(iv) 兩旗並用
      → exit 2（CLI 層接線，subprocess）。

跑法：`python scripts/test_furnishings.py`；全部通過 exit 0，任一失敗 exit 1。
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.image_reverb import config  # noqa: E402
from src.image_reverb import pipeline as pipeline_mod  # noqa: E402
from src.image_reverb import preprocess as preprocess_mod  # noqa: E402
from src.image_reverb import surfaces as surfaces_mod  # noqa: E402
from src.image_reverb.furnishings import (  # noqa: E402
    FurnishingEstimate,
    estimate_furnishings,
    load_furnishings,
)
from src.image_reverb.materials import SURFACE_NAMES, SurfaceMaterials  # noqa: E402
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


def _install_stubs_d(surf: SurfaceMaterials, detail: dict):
    """比照 `test_output_gate.py` 的樁法：樁掉 `run_photo()` 區域 import 的
    `preprocess_image`／`surfaces_from_preprocess`，額外樁 `pipeline.compute_acoustics`
    （模組層級 import，捕捉呼叫參數後轉呼叫真正的實作，不影響實際計算）。
    """

    def fake_preprocess_image(path, output_dir=None):
        return {"is_equirect": True}

    def fake_surfaces_from_preprocess(preprocess_summary, threshold=None):
        return surf, detail

    orig_preprocess = preprocess_mod.preprocess_image
    orig_surfaces = surfaces_mod.surfaces_from_preprocess
    orig_compute_acoustics = pipeline_mod.compute_acoustics
    preprocess_mod.preprocess_image = fake_preprocess_image
    surfaces_mod.surfaces_from_preprocess = fake_surfaces_from_preprocess
    return orig_preprocess, orig_surfaces, orig_compute_acoustics


def _restore_stubs_d(orig_preprocess, orig_surfaces, orig_compute_acoustics) -> None:
    preprocess_mod.preprocess_image = orig_preprocess
    surfaces_mod.surfaces_from_preprocess = orig_surfaces
    pipeline_mod.compute_acoustics = orig_compute_acoustics


def part_d() -> None:
    print("【D】pipeline 層陳設三態接線（T-35，裁決 T-33-A 裁決 A）")

    data = load_furnishings()
    curtain_id = next(i["ade_id"] for i in data["furnishings"] if i["ade_name"] == "curtain")
    bed_id = next(i["ade_id"] for i in data["furnishings"] if i["ade_name"] == "bed")

    # 六面互不相同、來源全 clip → materials_confidence=high（規則 3），
    # 搭配 --override-dims（confidence=high）讓 overall=high，不觸發 T-26 gate
    # ——本卡要測的是陳設三態接線，不是 gate（Phase 1.8 共同鐵則 6：gate 一行不動）。
    surf = SurfaceMaterials(
        floor="carpet", ceiling="gypsum_board", west="brick",
        east="concrete", south="wood_panel", north="glass",
    )
    for name in SURFACE_NAMES:
        surf.sources[name] = "clip"
    detail = {
        "mode": "test",
        "views": {},
        "warnings": [],
        "class_ratios": {"single": {curtain_id: 0.10, bed_id: 0.15}},
    }

    real_compute_acoustics = pipeline_mod.compute_acoustics
    captured: dict = {}

    def capturing_compute_acoustics(estimate, surfaces, materials_data=None, furnishings=None):
        captured["furnishings"] = furnishings
        return real_compute_acoustics(estimate, surfaces, materials_data, furnishings=furnishings)

    with tempfile.TemporaryDirectory() as tmp:
        photo = Path(tmp) / "_test_t35_furn.png"
        photo.write_bytes(b"")
        out_dir = config.PROJECT_ROOT / "output" / photo.stem
        if out_dir.exists():
            shutil.rmtree(out_dir)

        def run(**kwargs):
            orig = _install_stubs_d(surf, detail)
            pipeline_mod.compute_acoustics = capturing_compute_acoustics
            captured.clear()
            try:
                return pipeline_mod.run_photo(str(photo), override_dims="4x3x2.5", no_viz=True, **kwargs)
            finally:
                _restore_stubs_d(*orig)

        # (i) 預設：觀測模式 —— compute_acoustics 收到 furnishings=None，
        # analysis.json 的 furnishings.applied==False 且偵測欄位存在
        rc = run()
        check("(i) 預設 exit 0", rc == 0, f"rc={rc}")
        check(
            "(i) compute_acoustics 收到 furnishings=None（預設不套用）",
            captured.get("furnishings") is None,
            f"captured={captured}",
        )
        analysis = json.loads((out_dir / "analysis.json").read_text(encoding="utf-8"))
        furn_json = analysis.get("furnishings")
        check(
            "(i) analysis.furnishings.applied == False",
            isinstance(furn_json, dict) and furn_json.get("applied") is False,
            f"furnishings={furn_json}",
        )
        check(
            "(i) analysis.furnishings 偵測欄位存在（categories 非空）",
            isinstance(furn_json, dict) and bool(furn_json.get("categories")),
            f"furnishings={furn_json}",
        )
        check(
            "(i) analysis.furnishings 不含聲學換算欄位（A_by_band，地雷 #15 精神）",
            isinstance(furn_json, dict) and "A_by_band" not in json.dumps(furn_json),
            f"furnishings={furn_json}",
        )
        shutil.rmtree(out_dir)

        # (ii) --furnishings：套用 —— compute_acoustics 收到非 None，applied==True
        rc = run(furnishings=True)
        check("(ii) --furnishings exit 0", rc == 0, f"rc={rc}")
        check(
            "(ii) compute_acoustics 收到非 None 的 furnishings（已套用）",
            captured.get("furnishings") is not None,
            f"captured={captured}",
        )
        analysis = json.loads((out_dir / "analysis.json").read_text(encoding="utf-8"))
        furn_json = analysis.get("furnishings")
        check(
            "(ii) analysis.furnishings.applied == True",
            isinstance(furn_json, dict) and furn_json.get("applied") is True,
            f"furnishings={furn_json}",
        )
        check(
            "(ii) analysis.furnishings 含聲學換算欄位（A_by_band，現行完整結構）",
            isinstance(furn_json, dict)
            and all("A_by_band" in cat for cat in furn_json.get("categories", {}).values()),
            f"furnishings={furn_json}",
        )
        shutil.rmtree(out_dir)

        # (iii) --no-furnishings：完全不偵測 —— furnishings 鍵為 null
        rc = run(no_furnishings=True)
        check("(iii) --no-furnishings exit 0", rc == 0, f"rc={rc}")
        check(
            "(iii) compute_acoustics 收到 furnishings=None",
            captured.get("furnishings") is None,
            f"captured={captured}",
        )
        analysis = json.loads((out_dir / "analysis.json").read_text(encoding="utf-8"))
        check(
            "(iii) analysis.furnishings 為 null",
            analysis.get("furnishings") is None,
            f"furnishings={analysis.get('furnishings')}",
        )
        shutil.rmtree(out_dir)

    # (iv) 兩旗並用 → exit 2（CLI 層互斥檢查，subprocess，不跑模型）
    proc = subprocess.run(
        [
            sys.executable, "-m", "src.image_reverb",
            "--text", "測試", "--furnishings", "--no-furnishings",
        ],
        cwd=config.PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    check(
        "(iv) --furnishings 與 --no-furnishings 並用 → exit 2",
        proc.returncode == 2,
        f"returncode={proc.returncode}, stderr={proc.stderr.strip()!r}",
    )
    check(
        "(iv) 錯誤訊息點名兩個互斥旗標",
        "--furnishings" in proc.stderr and "--no-furnishings" in proc.stderr,
        f"stderr={proc.stderr.strip()!r}",
    )


def main() -> int:
    part_a()
    print()
    part_b()
    print()
    part_c()
    print()
    part_d()

    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 項失敗：{'、'.join(FAILURES)}")
        return 1
    print("✅ T-31/T-35 陳設等效吸音（資料表＋偵測模組＋三態接線）測試全部通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
