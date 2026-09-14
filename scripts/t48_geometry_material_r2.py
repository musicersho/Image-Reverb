#!/usr/bin/env python3
"""T-48：T-11／T-12 判準第二版針對性重驗（量測卡；裁決 T-45-A 執行卡 3/5）。

`src/` 零改動——本腳本只呼叫既有 CLI（`python -m src.image_reverb`）與既有
`scripts/gen_ir_manual.py`／`src.image_reverb.ir_metrics`，不重新實作任何評分邏輯。

13 張照片清單唯一可信來源＝`scripts/t36_clip_accuracy.GATE_ITEMS`（不重打）。

用法：
    python scripts/t48_geometry_material_r2.py manifest   # 只建 DATASET_MANIFEST.json（開跑前置）
    python scripts/t48_geometry_material_r2.py partA       # T-11 域外出口重驗
    python scripts/t48_geometry_material_r2.py partB       # T-12 判準 v2 量測
    python scripts/t48_geometry_material_r2.py all         # A+B
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from t36_clip_accuracy import GATE_ITEMS  # noqa: E402  （唯讀引用，13 張清單，唯一可信來源）

GEOMETRY_OUT = PROJECT_ROOT / "output" / "geometry_r2"
MATERIAL_OUT = PROJECT_ROOT / "output" / "material_r2"
GEOMETRY_SCOPE_MAX_M = 10.0  # 與 src/image_reverb/config.py 的 GEOMETRY_SCOPE_MAX_M 對照用（唯讀常數，不 import 以免誤會成 src 依賴；本卡自我檢查另有 grep 核對兩邊一致）

# 已知實際尺寸（裁決 T-45-A 於 T-48 卡事前鎖定「有的才填」清單；只涵蓋現行 13 張
# 照片清單裡確實有的部分——「走廊 ~30m」在原 T-11 9 張清單中，現行 13 張canonical
# 清單（T-36 起沿用至今）已不含 corridor_hotel_carpet，此項因此無對應照片可填）。
KNOWN_DIMENSIONS = {
    "bathroom_tiled": {
        "actual_depth_range_m": [2.5, 3.5],
        "actual_depth_point_m": 3.0,
        "actual_max_dim_m": 3.5,
        "v2_category": "domain_in_with_ground_truth",
        "note": "唯一落入 v2「≤10m 且有 ground truth」誤差 ±30% 判準的照片（卡片原文「目前只有浴室」）。",
    },
    "car_interior_suv": {
        "actual_max_dim_m": 2.0,
        "v2_category": "not_applicable",
        "note": "實際 ~2m，不 >10m 故不落入域外項；卡片原文「目前只有浴室」明示 ≤10m+ground truth"
        "誤差判準只適用浴室一張，車內不在兩類別判準內——僅記錄估計值供參考，不列入 FAIL/PASS 判定。",
    },
    "arena_ntsu_linkou": {
        "actual_max_dim_m": 150.0,
        "v2_category": "domain_out",
        "note": "體育館，實際最大維 ~150m，落入 v2 域外項（>10m 必須 low＋override-dims 導引）。",
    },
    "RacquetballCourt4": {
        "actual_dims_m": [12.19, 6.10, 6.10],
        "actual_max_dim_m": 12.19,
        "v2_category": "domain_out",
        "note": "壁球場，實際 12.19×6.10×6.10m，最大維 12.19m >10m，落入 v2 域外項。",
    },
    "SteinmanHall": {
        "actual_wall_distances_m": [12.2, 10.4, 5.25, 11.1],
        "actual_max_dim_m": 12.2,
        "v2_category": "domain_out",
        "note": "環景音樂廳，實測牆距 12.2/10.4/5.25/11.1m，最大單面牆距 12.2m >10m，"
        "落入 v2 域外項（環景走單面牆距判定，見 geometry.py apply_scope_confidence）。",
    },
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def git_status_clean(paths: list[str]) -> str:
    out = subprocess.run(
        ["git", "status", "--porcelain", "--"] + paths,
        cwd=PROJECT_ROOT, capture_output=True, text=True, check=True,
    ).stdout
    return out


def build_manifest() -> dict:
    photos = []
    for item in GATE_ITEMS:
        p = PROJECT_ROOT / item["photo"]
        if not p.exists():
            raise FileNotFoundError(f"照片不存在：{p}")
        photos.append({
            "name": item["name"],
            "path": item["photo"],
            "sha256": sha256_file(p),
        })
    manifest = {
        "task": "T-48",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_head_at_manifest_time": git_head(),
        "photo_list_source": "scripts/t36_clip_accuracy.GATE_ITEMS（唯一可信來源，13 張，不重打）",
        "photo_count": len(photos),
        "photos": photos,
        "known_dimensions": KNOWN_DIMENSIONS,
        "material_r2_synthetic_room": {
            "note": "B 部分為合成房間，非本清單管的照片資料；三條重生 IR 的 sha256 另記於 "
            "output/material_r2/REPORT.md 檔頭（見 T-48 卡§8 dataset_manifest_sha256 說明）。",
            "dimensions_m": [4.0, 3.0, 2.5],
            "per_wall": "floor=carpet／其餘 gypsum_board",
            "control_a": "六面 gypsum_board",
            "control_b": "六面 carpet",
        },
    }
    return manifest


def cmd_manifest() -> None:
    # 本步驟只讀 13 張照片 bytes 建 manifest，不跑任何量測；量測腳本本身（本檔）
    # 尚未 commit 屬正常過程（鐵則 14：manifest 與本腳本會在同一個「開跑前」commit
    # 一起送出）。真正的 dirty 檢查（含 scripts/）在 partA／partB 開跑前執行，
    # 屆時本腳本已隨開跑前 commit 進版控。
    dirty = git_status_clean(["src", "data"])
    if dirty:
        print("❌ 錯誤：git status --porcelain -- src data 非空，依 T-48 條件 (a) 不得送審：")
        print(dirty)
        sys.exit(1)
    manifest = build_manifest()
    GEOMETRY_OUT.mkdir(parents=True, exist_ok=True)
    out_path = GEOMETRY_OUT / "DATASET_MANIFEST.json"
    text = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    out_path.write_text(text, encoding="utf-8")
    digest = sha256_bytes(text.encode("utf-8"))
    print(f"已寫入：{out_path}")
    print(f"dataset_manifest_sha256: {digest}")
    print(f"git_head_at_manifest_time: {manifest['git_head_at_manifest_time']}")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("manifest", "partA", "partB", "all"):
        print(__doc__)
        sys.exit(2)
    mode = sys.argv[1]
    if mode == "manifest":
        cmd_manifest()
    else:
        print(f"模式 {mode} 尚未實作於本次呼叫（分階段開發中）")
        sys.exit(2)
