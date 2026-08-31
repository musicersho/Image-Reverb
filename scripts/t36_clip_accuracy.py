#!/usr/bin/env python3
"""T-36：CLIP 材質判定準確度診斷（裁決 T-33-A 裁決 B 執行卡 1/n；量測卡）。

跑法：`python scripts/t36_clip_accuracy.py`（預設輸出目錄＝T-36 凍結基線
`output/clip_accuracy/`——**該目錄自 T-40 起視為凍結，不可再被本腳本改寫**，
逐面判定明細快取沒有指紋，預設指令會 hard fail，訊息指向 `--out-dir`）。

治療評測（T-38／T-39 等）請用 `--out-dir <新目錄>` 指到非凍結目錄；該情境下
快取有指紋失效才會自動重跑，並印出哪些指紋項目變了。`--fresh` 語義維持
「強制全部重跑」，但對凍結目錄一律拒絕（見 T-40／`scripts/eval_cache.py`）。

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
- 快取指紋（來源圖片 hash／`preprocess.py`／`surfaces.py`／`config.py` 內容 hash／
  `data/materials.json`／`data/material_ground_truth.json` 內容 hash／模型 id／CLIP
  門檻／評測模式）由 `scripts/eval_cache.py`（T-40）計算與比對，本檔不重新實作。

輸出：`<out_dir>/REPORT.md`、`<out_dir>/tables.md`（表格由本腳本產生，
地雷 #15：不手打數字），以及 `<out_dir>/runs/<name>/detail.json`（逐面判定明細快取，
內含 T-40 起新增的 `fingerprint` 欄位）。`<out_dir>` 預設為 `output/clip_accuracy`。
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

import eval_cache  # noqa: E402  （T-40，唯讀引用，harness 專用模組）

OUT_DIR = REPO_ROOT / "output" / "clip_accuracy"  # T-36 凍結基線，自 T-40 起不可再被本腳本改寫
GROUND_TRUTH_PATH = REPO_ROOT / "data" / "material_ground_truth.json"
MATERIAL_ROUND_RUNS = REPO_ROOT / "output" / "material_round" / "runs"

# T-40 指紋內容 2/3：三個 src 檔內容 hash（檔案內容而非 git HEAD，才抓得到 dirty 工作樹）
FINGERPRINT_CODE_PATHS = [
    REPO_ROOT / "src" / "image_reverb" / "preprocess.py",
    REPO_ROOT / "src" / "image_reverb" / "surfaces.py",
    REPO_ROOT / "src" / "image_reverb" / "config.py",
]
# T-40 指紋內容 3/3：materials.json 與 ground truth 內容 hash
FINGERPRINT_DATA_PATHS = [
    REPO_ROOT / "data" / "materials.json",
    GROUND_TRUTH_PATH,
]

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


def run_or_load(
    item: dict,
    *,
    runs_dir: Path,
    is_frozen: bool,
    force_fresh: bool,
    eval_mode: str = "default",
) -> dict:
    """跑（或讀快取）一張照片的逐面判定明細，回傳 {"is_equirect":bool, "faces": {...}}。

    快取讀寫與失效判斷全部委由 `eval_cache.load_or_run()`（T-40）處理：
    快取內容多包一層 `fingerprint` 欄位，本函式只準備 `run_fn` 與指紋內容。
    """
    name = item["name"]
    run_dir = runs_dir / name
    cache_path = run_dir / "detail.json"
    photo_path = REPO_ROOT / item["photo"]

    def _fingerprint() -> dict:
        # 惰性：只有真的需要比對／寫入指紋時才呼叫（會讀來源圖片 bytes）。
        return eval_cache.compute_fingerprint(
            photo_path=photo_path,
            code_paths=FINGERPRINT_CODE_PATHS,
            data_paths=FINGERPRINT_DATA_PATHS,
            segmentation_model_id=surfaces_mod.config.SEGMENTATION_MODEL_ID,
            clip_model_id=surfaces_mod.config.CLIP_MODEL_ID,
            clip_threshold=THRESHOLD,
            eval_mode=eval_mode,
        )

    def _run() -> dict:
        run_dir.mkdir(parents=True, exist_ok=True)
        prep_summary = preprocess.preprocess_image(photo_path, output_dir=run_dir / "preprocess")
        surfaces_obj, detail = surfaces_mod.surfaces_from_preprocess(prep_summary)
        is_equirect = bool(prep_summary["is_equirect"])
        faces = _flatten_equirect(detail) if is_equirect else _flatten_perspective(detail)
        return {
            "is_equirect": is_equirect,
            "surfaces": surfaces_obj.as_dict(),
            "sources": surfaces_obj.sources,
            "warnings": surfaces_obj.warnings,
            "faces": faces,
        }

    payload, was_rerun, reasons = eval_cache.load_or_run(
        cache_path=cache_path,
        fingerprint_fn=_fingerprint,
        run_fn=_run,
        is_frozen=is_frozen,
        force_fresh=force_fresh,
    )
    if was_rerun and reasons:
        print(f"  ↻ {name}：快取失效，已重跑（原因：{'; '.join(reasons)}）")
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


def parse_args(argv: list[str]) -> tuple[Path, bool]:
    """回傳 (out_dir, force_fresh)。--out-dir 未指定時預設為凍結基線 OUT_DIR。"""
    force_fresh = "--fresh" in argv
    out_dir = OUT_DIR
    if "--out-dir" in argv:
        idx = argv.index("--out-dir")
        if idx + 1 >= len(argv):
            raise SystemExit("🔴 卡關：--out-dir 需要接一個路徑參數。")
        raw = Path(argv[idx + 1])
        out_dir = raw if raw.is_absolute() else (REPO_ROOT / raw)
    return out_dir.resolve(), force_fresh


def main() -> int:
    out_dir, force_fresh = parse_args(sys.argv[1:])
    is_frozen = out_dir == OUT_DIR.resolve()
    runs_dir = out_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    if is_frozen:
        print(f"（輸出目錄 {out_dir} 為 T-36 凍結基線，快取指紋不符將 hard fail，不會自動重跑。）")
    else:
        print(f"（輸出目錄 {out_dir} 為非凍結目錄，快取指紋不符會自動重跑。）")

    if not GROUND_TRUTH_PATH.exists():
        print(f"🔴 卡關：找不到 {GROUND_TRUTH_PATH}，這份檔案必須先由使用者逐面確認產生。")
        return 1
    ground_truth = json.loads(GROUND_TRUTH_PATH.read_text(encoding="utf-8"))
    gt_photos = ground_truth["photos"]

    all_data: dict[str, dict] = {}
    print("=== 逐面判定明細（跑或讀快取）與三軸基準交叉驗證 ===")
    try:
        for item in GATE_ITEMS:
            name = item["name"]
            payload = run_or_load(
                item, runs_dir=runs_dir, is_frozen=is_frozen, force_fresh=force_fresh
            )
            cross_check_against_frozen_baseline(name, payload)
            all_data[name] = payload
            print(f"✓ {name}（{'equirect' if payload['is_equirect'] else 'perspective'}）")
    except eval_cache.FrozenBaselineError as exc:
        print(f"🔴 卡關：{exc}")
        return 1
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
    sensitivity = build_threshold_sensitivity(GATE_ITEMS, all_data, gt_photos, OOD_PREFIX, THRESHOLD)
    simulation = build_ceiling_simulation(GATE_ITEMS, all_data, gt_photos, surfaces_mod, EXPECTED_GATE)

    out_dir.mkdir(parents=True, exist_ok=True)
    write_report(out_dir, accuracy, error_types, sensitivity, simulation, ground_truth)

    print(f"\n完成。報告：{out_dir / 'REPORT.md'}")
    print(f"表格：{out_dir / 'tables.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
