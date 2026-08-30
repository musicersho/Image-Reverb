#!/usr/bin/env python3
"""T-36：CLIP 材質判定準確度診斷（裁決 T-33-A 裁決 B 執行卡 1/n；量測卡）。

跑法：`python scripts/t36_clip_accuracy.py`（可重跑；已產生的逐面判定明細會被快取在
`output/clip_accuracy/runs/<name>/detail.json`，加 `--fresh` 強制全部重跑模型）。

**這是量測卡的量測驅動程式**：只唯讀 import `src/image_reverb`
（`preprocess.preprocess_image()` / `surfaces.surfaces_from_preprocess()` /
`surfaces.compute_materials_confidence()`），`src/` 全程只讀不寫，一行不改。

- 13 張照片的清單與裁決 T-28-A 複驗基準（`GATE_ITEMS` / `EXPECTED_GATE`）照抄自
  `scripts/t33_material_round_tables.py`（唯一可信來源），不重打。
- ground truth 讀 `data/material_ground_truth.json`（使用者逐面確認，`confirmed_by` 全為
  `"user"`，本腳本不得也沒有自己填寫這份檔案）。
- 逐面判定明細（含 CLIP 原始 top3，含 fallback/out_of_domain 被覆寫前的真實候選）用
  `surfaces.surfaces_from_preprocess()` 的回傳值直接讀，不重新實作任何評分邏輯。
- 「判定全對」天花板模擬只唯讀呼叫 `surfaces.compute_materials_confidence()`，規則零改動。

輸出：`output/clip_accuracy/REPORT.md`、`output/clip_accuracy/tables.md`（表格由本腳本產生，
地雷 #15：不手打數字），以及 `output/clip_accuracy/runs/<name>/detail.json`（逐面判定明細快取）。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from src.image_reverb import preprocess  # noqa: E402
from src.image_reverb import surfaces as surfaces_mod  # noqa: E402
from src.image_reverb import materials as materials_mod  # noqa: E402
from src.image_reverb.materials import SURFACE_NAMES  # noqa: E402

OUT_DIR = REPO_ROOT / "output" / "clip_accuracy"
RUNS_DIR = OUT_DIR / "runs"
GROUND_TRUTH_PATH = REPO_ROOT / "data" / "material_ground_truth.json"
MATERIAL_ROUND_RUNS = REPO_ROOT / "output" / "material_round" / "runs"

# ------------------------------------------------------------------
# 13 張照片與裁決 T-28-A 複驗基準——照抄自 scripts/t33_material_round_tables.py
# 第 61–124 行（EXPECTED_GATE 起於 61、GATE_ITEMS 起於 78），不重打。
# ------------------------------------------------------------------
EXPECTED_GATE = {
    "bathroom_tiled": ("medium", "low"),
    "bedroom_ai_generated": ("medium", "low"),
    "stairwell_tiled": ("medium", "low"),
    "arena_ntsu_linkou": ("low", "low"),
    "car_interior_suv": ("low", "low"),
    "CathedralRoom": ("medium", "low"),
    "DivorceBeach": ("low", "medium"),
    "site_photo_department_store": ("medium", "low"),
    "site_photo_gym": ("low", "low"),
    "site_photo_restaurant": ("low", "low"),
    "RacquetballCourt4": ("medium", "low"),
    "SteinmanHall": ("low", "low"),
    "TunnelToHell": ("medium", "low"),
}

GATE_ITEMS = [
    {"name": "bathroom_tiled", "photo": "assets/photos/bathroom_tiled.png"},
    {"name": "bedroom_ai_generated", "photo": "assets/photos/bedroom_ai_generated.png"},
    {"name": "stairwell_tiled", "photo": "assets/photos/stairwell_tiled.png"},
    {"name": "arena_ntsu_linkou", "photo": "assets/photos/arena_ntsu_linkou.png"},
    {"name": "car_interior_suv", "photo": "assets/photos/car_interior_suv.png"},
    {"name": "CathedralRoom", "photo": "assets/reference_irs/cathedral_room_shasta_lake_caverns/CathedralRoom.jpg"},
    {"name": "DivorceBeach", "photo": "assets/reference_irs/divorce_beach/DivorceBeach.jpg"},
    {"name": "site_photo_department_store", "photo": "assets/reference_irs/mit_department_store/site_photo_department_store.png"},
    {"name": "site_photo_gym", "photo": "assets/reference_irs/mit_gym/site_photo_gym.png"},
    {"name": "site_photo_restaurant", "photo": "assets/reference_irs/mit_restaurant/site_photo_restaurant.png"},
    {"name": "RacquetballCourt4", "photo": "assets/reference_irs/racquetball_court_4/RacquetballCourt4.jpg"},
    {"name": "SteinmanHall", "photo": "assets/reference_irs/steinman_hall/SteinmanHall.jpg"},
    {"name": "TunnelToHell", "photo": "assets/reference_irs/tunnel_to_hell/TunnelToHell.jpg"},
]

OOD_PREFIX = surfaces_mod.OOD_PREFIX
THRESHOLD = surfaces_mod.config.CLIP_CONFIDENCE_THRESHOLD


# ------------------------------------------------------------------
# 逐面判定明細：跑（或讀快取）surfaces_from_preprocess()，攤平成 {face: {...}}
# ------------------------------------------------------------------

def _flatten_perspective(detail: dict) -> dict[str, dict]:
    """單張透視照：single 底下 floor/ceiling/wall 三個角色，wall 複製到四面牆。"""
    single = detail["views"].get("single", {})
    flat: dict[str, dict] = {}
    for role in ("floor", "ceiling"):
        if role in single:
            flat[role] = single[role]
    if "wall" in single:
        for name in ("west", "east", "south", "north"):
            flat[name] = single["wall"]
    return flat


def _flatten_equirect(detail: dict) -> dict[str, dict]:
    """環景：views 底下每個視角對應一個面（VIEW_TO_SURFACE）。"""
    flat: dict[str, dict] = {}
    for view_name, view_detail in detail["views"].items():
        face = view_detail.get("surface")
        if face:
            flat[face] = view_detail
    return flat


def run_or_load(item: dict, fresh: bool) -> dict:
    """跑（或讀快取）一張照片的逐面判定明細，回傳 {"is_equirect":bool, "faces": {...}}。"""
    name = item["name"]
    run_dir = RUNS_DIR / name
    cache_path = run_dir / "detail.json"
    if cache_path.exists() and not fresh:
        return json.loads(cache_path.read_text(encoding="utf-8"))

    run_dir.mkdir(parents=True, exist_ok=True)
    photo_path = REPO_ROOT / item["photo"]
    prep_summary = preprocess.preprocess_image(photo_path, output_dir=run_dir / "preprocess")
    surfaces_obj, detail = surfaces_mod.surfaces_from_preprocess(prep_summary)

    is_equirect = bool(prep_summary["is_equirect"])
    faces = _flatten_equirect(detail) if is_equirect else _flatten_perspective(detail)

    payload = {
        "is_equirect": is_equirect,
        "surfaces": surfaces_obj.as_dict(),
        "sources": surfaces_obj.sources,
        "warnings": surfaces_obj.warnings,
        "faces": faces,
    }
    cache_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def cross_check_against_frozen_baseline(name: str, payload: dict) -> None:
    """對照 T-33 凍結快取（output/material_round/runs/<name>__no_furn/analysis.json），
    確認本腳本重跑（或讀自己快取）的 surfaces/sources 與三軸基準完全一致——
    這是紅線 #6（13 張三軸 confidence 與裁決 T-28-A 基線不符卻沒觸發🔴停）的守門檢查。
    """
    frozen_path = MATERIAL_ROUND_RUNS / f"{name}__no_furn" / "analysis.json"
    if not frozen_path.exists():
        print(f"🔴 卡關：找不到 T-33 凍結快取 {frozen_path}，無法交叉驗證基準。")
        sys.exit(1)
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))

    if payload["surfaces"] != frozen["surfaces"]:
        print(f"🔴 卡關：{name} 的 surfaces 與 T-33 凍結快取不一致！")
        print(f"   本次：{payload['surfaces']}")
        print(f"   凍結：{frozen['surfaces']}")
        sys.exit(1)
    if payload["sources"] != frozen.get("surfaces_sources", {}):
        print(f"🔴 卡關：{name} 的 surfaces_sources 與 T-33 凍結快取不一致！")
        print(f"   本次：{payload['sources']}")
        print(f"   凍結：{frozen.get('surfaces_sources')}")
        sys.exit(1)

    expected_geo, expected_mat = EXPECTED_GATE[name]
    if frozen["geometry_confidence"] != expected_geo or frozen["materials_confidence"] != expected_mat:
        print(f"🔴 卡關：{name} 的凍結快取三軸 confidence 與裁決 T-28-A 基線不符！")
        print(f"   凍結：geometry={frozen['geometry_confidence']}, materials={frozen['materials_confidence']}")
        print(f"   基線：geometry={expected_geo}, materials={expected_mat}")
        sys.exit(1)

    # 唯讀重算一次 materials_confidence，跟凍結快取記錄的值也要一致
    surf_obj = materials_mod.SurfaceMaterials(**payload["surfaces"])
    surf_obj.sources = dict(payload["sources"])
    surf_obj.warnings = list(payload["warnings"])
    recomputed = surfaces_mod.compute_materials_confidence(surf_obj)
    if recomputed != expected_mat:
        print(f"🔴 卡關：{name} 用 compute_materials_confidence() 唯讀重算得到 {recomputed}，"
              f"與基線 {expected_mat} 不符！")
        sys.exit(1)


def main() -> int:
    fresh = "--fresh" in sys.argv
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    if not GROUND_TRUTH_PATH.exists():
        print(f"🔴 卡關：找不到 {GROUND_TRUTH_PATH}，這份檔案必須先由使用者逐面確認產生。")
        return 1
    ground_truth = json.loads(GROUND_TRUTH_PATH.read_text(encoding="utf-8"))
    gt_photos = ground_truth["photos"]

    all_data: dict[str, dict] = {}
    print("=== 逐面判定明細（跑或讀快取）與三軸基準交叉驗證 ===")
    for item in GATE_ITEMS:
        name = item["name"]
        payload = run_or_load(item, fresh)
        cross_check_against_frozen_baseline(name, payload)
        all_data[name] = payload
        print(f"✓ {name}（{'equirect' if payload['is_equirect'] else 'perspective'}）")
    print("✅ 13 張照片三軸 confidence 與裁決 T-28-A 基線完全相同（含本腳本唯讀重算）。\n")

    from t36_analysis import (  # noqa: E402  (放同目錄，避免這支主檔案過長)
        build_accuracy_tables,
        build_error_type_tables,
        build_threshold_sensitivity,
        build_ceiling_simulation,
        write_report,
    )

    accuracy = build_accuracy_tables(GATE_ITEMS, all_data, gt_photos)
    error_types = build_error_type_tables(GATE_ITEMS, all_data, gt_photos, OOD_PREFIX)
    sensitivity = build_threshold_sensitivity(GATE_ITEMS, all_data, gt_photos, OOD_PREFIX)
    simulation = build_ceiling_simulation(GATE_ITEMS, all_data, gt_photos, surfaces_mod, EXPECTED_GATE)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_report(OUT_DIR, accuracy, error_types, sensitivity, simulation, ground_truth)

    print(f"\n完成。報告：{OUT_DIR / 'REPORT.md'}")
    print(f"表格：{OUT_DIR / 'tables.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
