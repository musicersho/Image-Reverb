#!/usr/bin/env python3
"""T-57：T-17-R2 五支薄包裝腳本共用常數與小工具（`t17r2_*.py` 專用）。

拆出這支檔案是為了讓「held-out 五類 stem／8 場地 GT 鍵名對照／表 4 手動尺寸」
只寫一份——五支腳本各自 import，不各自抄一份常數表，避免像 SHUFFLE_SEED
那種「兩處各自維護、改一邊漏一邊」的地雷（地雷 #15 的常見成因）。

本檔**不跑模型、不寫檔案**，純常數與純函式，`test_t17r2_tools.py` 可以直接
import 呼叫 `classify_domain()`／`find_photo()` 驗證邏輯，不需要隔離 git repo。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.image_reverb import config  # noqa: E402

# T-17 的 `t17_blind_test.SHUFFLE_SEED` 是 20260830；R2 換一個新種子（規格明定
# 寫死在原始碼），確保打亂順序與 T-17 不同——沿用舊種子會讓「同一組照片」
# 剛好又用同一個順序，看起來像沒換過素材。
SHUFFLE_SEED = 20260916

# 五類 held-out 空間（拍攝規格見 TASKS.md T-17-R2 卡「🔮 Fable 落地」§1）。
# 順序與中文類別名稱沿用 `t17_blind_test.SPACES`（只 import 不改），stem 換成
# `heldout_*`——檔名不得與 output/ 既有子目錄同名（CLI 用檔名 stem 當輸出目錄）。
HELDOUT_SPACES: list[tuple[str, str]] = [
    ("浴室", "heldout_bathroom"),
    ("客廳／臥室（住宅尺度）", "heldout_living"),
    ("教堂／大空間", "heldout_hall"),
    ("走廊／樓梯間", "heldout_corridor"),
    ("車內", "heldout_car"),
]

HELDOUT_PHOTOS_DIR = REPO_ROOT / "assets" / "photos_heldout"
LEGACY_PHOTOS_DIR = REPO_ROOT / "assets" / "photos"
GROUND_TRUTH_HELDOUT_FILENAME = "ground_truth_heldout.json"

OUT_DIR = REPO_ROOT / "output" / "mvp_acceptance_r2"
DEFAULT_MANIFEST_PATH = OUT_DIR / "DATASET_MANIFEST.json"
DEFAULT_DRY_PATH = REPO_ROOT / "assets" / "dry" / "clap_synth.wav"

# 固定副檔名優先序——找照片一律用「逐一檢查是否存在」而不是 glob，
# 避免檔案系統列舉順序造成同一份輸入在不同機器上得到不同結果（可重現性）。
PHOTO_EXTENSIONS = (".jpg", ".jpeg", ".png", ".heic")

# 表 4（`output/mvp_acceptance/tables.md`，T-17）逐字抄——5 組（不含
# `t17_diag_racquetball_hard`：尺寸與 racquetball 相同、是診斷 run 不是獨立場地）。
# 要改這裡的數字，先去改 T-17 表 4，不得反過來另立一份。
MANUAL_DIMS: dict[str, dict[str, float]] = {
    "department_store": {"length": 35.00, "width": 25.00, "height": 3.20},
    "gym": {"length": 9.00, "width": 6.00, "height": 2.90},
    "restaurant": {"length": 14.00, "width": 9.00, "height": 3.20},
    "racquetball": {"length": 12.19, "width": 6.10, "height": 6.10},
    "steinman": {"length": 20.00, "width": 18.00, "height": 7.50},
}

# `t17_rt60_table.VENUES` 的 8 場地 `key`（小寫底線）→
# `t36_clip_accuracy.GATE_ITEMS` 的 `name`（`data/material_ground_truth.json`
# 用這組鍵）。兩套命名系統各自獨立演化，這是唯一對照表。
VENUE_KEY_TO_GT_NAME: dict[str, str] = {
    "cathedral_room_shasta_lake_caverns": "CathedralRoom",
    "divorce_beach": "DivorceBeach",
    "mit_department_store": "site_photo_department_store",
    "mit_gym": "site_photo_gym",
    "mit_restaurant": "site_photo_restaurant",
    "racquetball_court_4": "RacquetballCourt4",
    "steinman_hall": "SteinmanHall",
    "tunnel_to_hell": "TunnelToHell",
}

# T-17-R2 卡「in-domain 場地事前定義」（結果出來後不得改）：8 場地只有 mit_gym
# 是 in-domain（T-17 表 4 估 9×6×2.9m，其餘皆 >10m 或非房間）。
IN_DOMAIN_VENUE_KEYS = {"mit_gym"}

# `t17_rt60_table.VENUES` 的 8 場地 `key` → `MANUAL_DIMS` 的鍵（只有這 5 個場地
# 有 T-17 表 4 手動尺寸；cathedral／divorce_beach／tunnel_to_hell 沒有手動組）。
VENUE_KEY_TO_MANUAL_KEY: dict[str, str] = {
    "mit_department_store": "department_store",
    "mit_gym": "gym",
    "mit_restaurant": "restaurant",
    "racquetball_court_4": "racquetball",
    "steinman_hall": "steinman",
}

CAR_CATEGORY_LABEL = "車內"


def classify_domain(*, is_car: bool, dims_m: dict[str, float] | None) -> str:
    """一張 held-out／legacy 照片的 domain 分類。

    車內固定 `non_room`（不看尺寸）；其餘依最大邊是否 ≤`config.GEOMETRY_SCOPE_MAX_M`
    （沿用既有全域門檻常數，不另立數字）分 `in`／`out`；沒有尺寸資料 → `unknown`。
    """
    if is_car:
        return "non_room"
    if not dims_m:
        return "unknown"
    edges = [dims_m.get("length"), dims_m.get("width"), dims_m.get("height")]
    edges = [float(e) for e in edges if e is not None]
    if not edges:
        return "unknown"
    return "in" if max(edges) <= config.GEOMETRY_SCOPE_MAX_M else "out"


def find_photo(directory: Path, stem: str) -> Path | None:
    """依 `PHOTO_EXTENSIONS` 固定優先序找 `<stem>.<ext>`（含副檔名大寫變體）。

    找到第一個存在的就回傳；都沒有回傳 `None`。刻意不用 `glob()`——glob 的
    結果順序在不同檔案系統上不保證一致，用來決定「用哪個候選檔」會讓同一份
    輸入資料在不同機器上得到不同的 manifest（違反鎖定資料集的可重現性要求）。
    """
    for ext in PHOTO_EXTENSIONS:
        for variant in (ext, ext.upper()):
            p = directory / f"{stem}{variant}"
            if p.exists():
                return p
    return None


def load_ground_truth_heldout(photos_dir: Path) -> dict:
    """讀 `<photos_dir>/ground_truth_heldout.json`；不存在就回傳空 dict
    （held-out 照片尚未拍攝／GT 尚未填寫時的合法狀態，呼叫端逐項標記缺項，
    不得因此整支腳本失敗）。
    """
    path = photos_dir / GROUND_TRUTH_HELDOUT_FILENAME
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
