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
import re
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


# ------------------------------------------------------------
# Part A — T-11 域外出口重驗（跑真實 CLI，讀真實 gate 輸出，不重新實作評分邏輯）
# ------------------------------------------------------------

CLI_MODULE = ["python", "-m", "src.image_reverb"]

_CONF_LINE_RE = re.compile(
    r"confidence：geometry=(\w+), materials=(\w+), overall=(\w+)"
)
_DIMS_LINE_RE = re.compile(
    r"房間尺寸：([\d.]+)×([\d.]+)×([\d.]+) m（dims_source=(\w+)）"
)

_RULE_MARKERS = [
    ("scope_max_10m", "超出已驗證量程"),
    ("floor_visibility", "地板可見度"),
    ("person_ratio", "人群佔畫面"),
    ("out_of_domain_material", "這不是一個可以用 ShoeBox 房間模型描述的空間"),
    ("unknown_dims_source", "不在量程規則認得的類型"),
]


def _run_cli(photo: str, extra_args: list[str], log_path: Path) -> tuple[int, str]:
    proc = subprocess.run(
        CLI_MODULE + [photo, "--no-viz"] + extra_args,
        cwd=PROJECT_ROOT, capture_output=True, text=True,
    )
    combined = proc.stdout + "\n--- stderr ---\n" + proc.stderr
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(combined, encoding="utf-8")
    return proc.returncode, combined


def _matched_rules(warnings: list[str]) -> list[str]:
    tags = []
    for tag, marker in _RULE_MARKERS:
        if any(marker in w for w in warnings):
            tags.append(tag)
    return tags


def run_part_a() -> list[dict]:
    dirty = git_status_clean(["src", "data", "scripts"])
    if dirty:
        print("❌ 錯誤：git status --porcelain -- src data scripts 非空，依 T-48 條件 (a) 不得送審：")
        print(dirty)
        sys.exit(1)

    runs_dir = GEOMETRY_OUT / "runs"
    results = []
    for item in GATE_ITEMS:
        name = item["name"]
        photo = item["photo"]
        print(f"=== {name} ===", flush=True)

        # 1) force-low-confidence 先跑：只是為了讀 analysis.json 裡完整的 warnings/notes
        #    （量程規則觸發細節），不影響、不重新計算 gate 判定本身。
        force_exit, force_log = _run_cli(
            photo, ["--force-low-confidence"], runs_dir / name / "force_low_confidence.log"
        )
        analysis_path = PROJECT_ROOT / "output" / Path(photo).stem / "analysis.json"
        analysis = json.loads(analysis_path.read_text(encoding="utf-8")) if analysis_path.exists() else {}

        # 2) 預設路徑（無旗標）：這才是真正的 production gate 行為，域外判準看這次的輸出。
        default_exit, default_log = _run_cli(
            photo, [], runs_dir / name / "default.log"
        )
        conf_match = _CONF_LINE_RE.search(default_log)
        dims_match = _DIMS_LINE_RE.search(default_log)
        geometry_confidence = conf_match.group(1) if conf_match else analysis.get("geometry_confidence")
        overall_confidence = conf_match.group(3) if conf_match else None
        blocked = "已擋下輸出" in default_log
        override_dims_guidance = "幾何不可信 → 用 --override-dims" in default_log

        if dims_match:
            length_m, width_m, height_m = (float(dims_match.group(i)) for i in (1, 2, 3))
            dims_source = dims_match.group(4)
        else:
            dims_m = analysis.get("dims_m", {})
            length_m = dims_m.get("length")
            width_m = dims_m.get("width")
            height_m = dims_m.get("height")
            dims_source = analysis.get("dims_source")

        max_dim = max(v for v in (length_m, width_m, height_m) if v is not None)
        warnings_list = analysis.get("warnings", [])
        matched_rules = _matched_rules(warnings_list)

        known = KNOWN_DIMENSIONS.get(name)
        v2_category = known["v2_category"] if known else "unknown_no_ground_truth"

        verdict = None
        verdict_detail = ""
        if v2_category == "domain_out":
            ok = (geometry_confidence == "low") and override_dims_guidance
            verdict = "PASS" if ok else "FAIL"
            verdict_detail = (
                f"實際最大維 {known['actual_max_dim_m']}m >10m，要求 geometry_confidence=low 且"
                f" gate 訊息含 --override-dims 導引；實測 geometry_confidence={geometry_confidence}，"
                f"override-dims 導引={'有' if override_dims_guidance else '無'}"
            )
        elif v2_category == "domain_in_with_ground_truth":
            actual = known["actual_depth_point_m"]
            error_pct = (length_m - actual) / actual * 100.0 if length_m is not None else None
            ok = error_pct is not None and abs(error_pct) <= 30.0
            verdict = "PASS" if ok else "FAIL"
            verdict_detail = (
                f"實際進深 {actual}m（範圍 {known['actual_depth_range_m']}），估計進深 {length_m:.2f}m，"
                f"誤差 {error_pct:+.1f}%（判準 ≤±30%）"
            )
        elif v2_category == "not_applicable":
            verdict = "不適用"
            verdict_detail = known["note"]
        else:
            verdict = "不適用（未知，不列入 v2 判定）"
            verdict_detail = "無已知實際尺寸，僅記錄估計值供參考，不列入 FAIL/PASS 判定。"

        results.append({
            "name": name,
            "photo": photo,
            "dims_source": dims_source,
            "length_m": length_m,
            "width_m": width_m,
            "height_m": height_m,
            "max_dim_m": max_dim,
            "volume_m3": (length_m or 0) * (width_m or 0) * (height_m or 0),
            "geometry_confidence": geometry_confidence,
            "overall_confidence": overall_confidence,
            "blocked": blocked,
            "override_dims_guidance": override_dims_guidance,
            "matched_scope_rules": matched_rules,
            "v2_category": v2_category,
            "known": known,
            "verdict": verdict,
            "verdict_detail": verdict_detail,
            "default_exit": default_exit,
            "force_exit": force_exit,
        })
        print(f"    dims={length_m:.2f}x{width_m:.2f}x{height_m:.2f} geometry_confidence={geometry_confidence}"
              f" v2_category={v2_category} verdict={verdict}")
    return results


def _write_part_a_report(results: list[dict]) -> None:
    head = git_head()
    dirty_check = git_status_clean(["src", "data", "scripts"])
    lines = []
    lines.append("# T-48 A 部分 — T-11 域外出口無誤放重驗（判準 v2）\n")
    lines.append(f"> 產生日期：{datetime.now(timezone.utc).isoformat()}　"
                 f"git_head：`{head}`　"
                 f"git status --porcelain -- src data scripts：{'(空)' if not dirty_check else dirty_check}\n")
    lines.append(
        "判準 v2（事前鎖定，見 TASKS.md T-48 卡 §8）：實際最大維 >10m 的照片，"
        "`geometry_confidence` 必須為 low 且 gate 訊息含 `--override-dims` 導引；"
        "實際 ≤10m 且有 ground truth 的照片誤差 ≤ ±30%（目前只有浴室）。"
        "任一域外照片拿到 medium／high＝域外出口誤放，記 FAIL。\n"
    )

    fail_count = sum(1 for r in results if r["verdict"] == "FAIL")
    lines.append(f"## 0. 結論\n\n**{'FAIL——有域外誤放或浴室誤差超標' if fail_count else 'PASS——13 張皆符合 v2 判準（含不適用/未知項）'}**"
                 f"（FAIL 筆數：{fail_count}）\n")

    lines.append("## 1. 逐張結果（全部 13 張，沒有只挑好看的）\n")
    lines.append("| 照片 | 估計 L×W×H (m) | 最大維 | dims_source | geometry_confidence | override-dims 導引 | v2 類別 | 判定 | 細節 |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for r in results:
        lines.append(
            f"| {r['name']} | {r['length_m']:.2f}×{r['width_m']:.2f}×{r['height_m']:.2f} "
            f"| {r['max_dim_m']:.2f} | {r['dims_source']} | {r['geometry_confidence']} "
            f"| {'有' if r['override_dims_guidance'] else '無'} | {r['v2_category']} "
            f"| {r['verdict']} | {r['verdict_detail']} |"
        )

    lines.append("\n## 2. 觸發的量程／場景線索規則（讀自 `--force-low-confidence` 重跑的 analysis.json warnings，"
                 "只為了印出「觸發哪條規則」的細節，不影響／不重算 gate 判定本身——判定一律依上表的預設路徑真實 CLI 輸出）\n")
    lines.append("| 照片 | 觸發規則 |")
    lines.append("|---|---|")
    for r in results:
        tags = "、".join(r["matched_scope_rules"]) if r["matched_scope_rules"] else "（無，或全部規則皆未觸發 low）"
        lines.append(f"| {r['name']} | {tags} |")

    lines.append("\n## 3. 已知實際尺寸對照表\n")
    lines.append("| 照片 | 已知實際尺寸 | v2 類別 | 說明 |")
    lines.append("|---|---|---|---|")
    for r in results:
        known = r["known"]
        if known is None:
            lines.append(f"| {r['name']} | 未知 | {r['v2_category']} | 無已知實際尺寸，僅記錄估計值供參考 |")
        else:
            known_desc = known.get("actual_depth_range_m") or known.get("actual_dims_m") \
                or known.get("actual_wall_distances_m") or known.get("actual_max_dim_m")
            lines.append(f"| {r['name']} | {known_desc} | {r['v2_category']} | {known['note']} |")

    lines.append(
        "\n## 4. 方法\n\n"
        "每張照片跑兩次真實 CLI（`python -m src.image_reverb <photo> --no-viz`）：\n"
        "1. 先加 `--force-low-confidence` 跑一次，只為了讀 `output/<stem>/analysis.json` 的完整 "
        "`warnings`（量程/場景線索規則的詳細文字），不影響任何判定。\n"
        "2. 再跑一次**不帶任何旗標**（真正的預設 production 路徑），這次的 stdout/stderr 才是 gate 判定"
        "與 `--override-dims` 導引訊息的真實來源——v2 判準完全依這次輸出判定。\n\n"
        "13 張照片清單與路徑唯一來源：`scripts/t36_clip_accuracy.GATE_ITEMS`（不重打）。"
        "逐張原始 CLI 輸出存於 `output/geometry_r2/runs/<name>/{default,force_low_confidence}.log`。\n"
    )

    GEOMETRY_OUT.mkdir(parents=True, exist_ok=True)
    (GEOMETRY_OUT / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"已寫入：{GEOMETRY_OUT / 'REPORT.md'}")


def cmd_part_a() -> None:
    results = run_part_a()
    _write_part_a_report(results)
    fail_count = sum(1 for r in results if r["verdict"] == "FAIL")
    print(f"\nPart A 完成：FAIL 筆數 = {fail_count}")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("manifest", "partA", "partB", "all"):
        print(__doc__)
        sys.exit(2)
    mode = sys.argv[1]
    if mode == "manifest":
        cmd_manifest()
    elif mode == "partA":
        cmd_part_a()
    else:
        print(f"模式 {mode} 尚未實作於本次呼叫（分階段開發中）")
        sys.exit(2)
