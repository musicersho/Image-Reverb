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

import soundfile as sf  # noqa: E402
from src.image_reverb.ir_metrics import band_t30, t30_low_combined  # noqa: E402  （唯讀引用，T-18 既有量測函式，不重新實作）

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
        "note": "實際 ~2m，不 >10m 故不落入域外項；卡片原文「目前只有浴室」明示「≤10m 且有 ground truth」"
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

    fails = [r for r in results if r["verdict"] == "FAIL" and r["v2_category"] == "domain_out"]
    if fails:
        lines.append("\n## 4. 域外誤放根因（程式判定：v2_category=domain_out 且 verdict=FAIL 的每一筆）\n")
        for r in fails:
            no_rule = not r["matched_scope_rules"]
            lines.append(f"### {r['name']}\n")
            lines.append(
                f"實際最大維 {r['known']['actual_max_dim_m']}m（{r['known']['note']}），"
                f"但預設路徑實測 `geometry_confidence={r['geometry_confidence']}`（非 low），"
                f"gate 未印 `--override-dims` 導引。程式重跑 `--force-low-confidence` 版讀出的 "
                f"warnings {'不含' if no_rule else '含'}「超出已驗證量程」字樣"
                f"（觸發規則：{('、'.join(r['matched_scope_rules']) or '無')}）。\n"
            )
            if no_rule and r["dims_source"] == "equirect_multiview":
                lines.append(
                    f"根因（讀 `src/image_reverb/geometry.py` `apply_scope_confidence()` 唯讀確認，"
                    f"本卡未改動該函式）：環景量程規則檢查的是**單一視角的原始牆距**"
                    f"（`wall_distances_m` 逐值比對 `GEOMETRY_SCOPE_MAX_M`），"
                    f"不是相加後的房間全長——這是刻意設計（避免對牆相加把有效上限拉高到約 40m，"
                    f"見該函式 docstring）。但代價是：當房間的實際全長 >10m、"
                    f"卻是由兩側**個別皆 ≤10m** 的視角相加而成時（本例估計 "
                    f"{r['length_m']:.2f}×{r['width_m']:.2f}×{r['height_m']:.2f}m，"
                    f"沒有任何單一視角讀數本身超過 10m），量程規則不會觸發，"
                    f"`geometry_confidence` 停在 medium——這正是 v2 判準想抓的「域外出口誤放」，"
                    f"如實記為 FAIL，不得用附註豁免（WORKFLOW §5.4.1）。\n"
                )
        lines.append("")

    lines.append(
        "\n## 5. 方法\n\n"
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


# ------------------------------------------------------------
# Part B — T-12 判準 v2 量測（合成房間，三條 IR 用既有 scripts/gen_ir_manual.py 重生）
# ------------------------------------------------------------

GEN_IR_SCRIPT = PROJECT_ROOT / "scripts" / "gen_ir_manual.py"
LEGACY_OUTPUT = PROJECT_ROOT / "output"

# 三條 IR 的 gen_ir_manual.py 呼叫方式與輸出檔名，逐字對照 T-12 卡「Opus 驗證結果」
# 表格已記錄的命令（不重打、與 T-12 交接筆記同設定）：
#   per-wall：      --materials floor=carpet,walls=gypsum_board → ir_room_small_surf_carpet.wav
#   六面 gypsum：   --materials floor=gypsum_board              → ir_room_small_surf_gypsum_board.wav
#   六面 carpet：   --material carpet（舊六面同材質模式）        → ir_room_small_carpet.wav
IR_CASES = [
    {
        "case": "per_wall",
        "args": ["small", "--materials", "floor=carpet,walls=gypsum_board"],
        "legacy_name": "ir_room_small_surf_carpet.wav",
        "final_name": "per_wall_floor_carpet.wav",
        "desc": "per-wall：floor=carpet／其餘 gypsum_board（4×3×2.5m）",
    },
    {
        "case": "control_gypsum",
        "args": ["small", "--materials", "floor=gypsum_board"],
        "legacy_name": "ir_room_small_surf_gypsum_board.wav",
        "final_name": "control_six_face_gypsum_board.wav",
        "desc": "對照組：六面 gypsum_board（4×3×2.5m）",
    },
    {
        "case": "control_carpet",
        "args": ["small", "--material", "carpet"],
        "legacy_name": "ir_room_small_carpet.wav",
        "final_name": "control_six_face_carpet.wav",
        "desc": "對照組：六面 carpet（4×3×2.5m，舊六面同材質模式）",
    },
]


def _sabine_125hz_from_stdout(stdout: str) -> float | None:
    m = re.search(r"125 Hz　RT60 ≈ ([\d.]+) 秒", stdout)
    return float(m.group(1)) if m else None


def run_part_b() -> dict:
    dirty = git_status_clean(["src", "data", "scripts"])
    if dirty:
        print("❌ 錯誤：git status --porcelain -- src data scripts 非空，依 T-48 條件 (a) 不得送審：")
        print(dirty)
        sys.exit(1)

    MATERIAL_OUT.mkdir(parents=True, exist_ok=True)
    runs_dir = MATERIAL_OUT / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    cases = {}
    for spec in IR_CASES:
        legacy_path = LEGACY_OUTPUT / spec["legacy_name"]
        pre_sha256 = sha256_file(legacy_path) if legacy_path.exists() else None

        proc = subprocess.run(
            ["python", str(GEN_IR_SCRIPT)] + spec["args"],
            cwd=PROJECT_ROOT, capture_output=True, text=True,
        )
        (runs_dir / f"{spec['case']}.log").write_text(
            proc.stdout + "\n--- stderr ---\n" + proc.stderr, encoding="utf-8"
        )
        if proc.returncode != 0 or not legacy_path.exists():
            print(f"❌ 錯誤：{spec['case']} 生成失敗（exit={proc.returncode}），見 {runs_dir / (spec['case'] + '.log')}")
            sys.exit(1)

        post_sha256 = sha256_file(legacy_path)
        sabine_125hz = _sabine_125hz_from_stdout(proc.stdout)

        # 本卡的交付檔案在 output/material_r2/（紅線：不得重用 output/ 舊 IR）——
        # 把 gen_ir_manual.py 剛剛「本次重新生成」的檔案移到 material_r2/，
        # 移動前後都算過 sha256：post_sha256 就是這次重生的真實 bytes 指紋
        # （若與 pre_sha256 相同，代表模擬本身是確定性的，不代表沒有重新執行——
        # 本次執行的 stdout log 與 exit code 就是「有真的重新跑」的證據）。
        final_path = MATERIAL_OUT / spec["final_name"]
        legacy_path.replace(final_path)
        final_sha256 = sha256_file(final_path)
        assert final_sha256 == post_sha256

        ir, fs = sf.read(str(final_path))
        t30_combined = t30_low_combined(ir, fs)
        t30_125_octave = band_t30(ir, fs, [125])[0]

        cases[spec["case"]] = {
            **spec,
            "final_path": str(final_path.relative_to(PROJECT_ROOT)),
            "pre_sha256": pre_sha256,
            "post_sha256": post_sha256,
            "regenerated": True,
            "sabine_125hz_s": sabine_125hz,
            "t30_low_combined_s": t30_combined,
            "t30_125hz_octave_s": t30_125_octave,
            "fs": fs,
        }
        print(f"{spec['case']}: sabine_125hz={sabine_125hz} t30_combined={t30_combined:.3f}s "
              f"t30_125hz_octave={t30_125_octave:.3f}s sha256={final_sha256[:12]}…")

    return cases


def _pct_diff(a: float, b: float) -> float:
    """(a-b)/b*100，b 為對照基準。"""
    return (a - b) / b * 100.0


def _write_part_b_report(cases: dict) -> None:
    head = git_head()
    dirty_check = git_status_clean(["src", "data", "scripts"])
    pw = cases["per_wall"]
    cg = cases["control_gypsum"]
    cc = cases["control_carpet"]

    # v2-a：per-wall Sabine 125Hz ≈0.348s ±20%
    v2a_target = 0.348
    v2a_error_pct = _pct_diff(pw["sabine_125hz_s"], v2a_target)
    v2a_pass = abs(v2a_error_pct) <= 20.0

    # v2-b：per-wall 聯合帶 T30 與六面 gypsum 對照差異 ≤±20%；六面 carpet 對照 ≥ per-wall 3 倍
    v2b_diff_pct = _pct_diff(pw["t30_low_combined_s"], cg["t30_low_combined_s"])
    v2b_ratio = cc["t30_low_combined_s"] / pw["t30_low_combined_s"]
    v2b_diff_pass = abs(v2b_diff_pct) <= 20.0
    v2b_ratio_pass = v2b_ratio >= 3.0
    v2b_pass = v2b_diff_pass and v2b_ratio_pass

    # v1 字面條件：125Hz 八度 T30 ≈0.35s ±20%（照量照列，預期未達，只記錄不當門檻）
    v1_target = 0.35
    v1_error_pct = _pct_diff(pw["t30_125hz_octave_s"], v1_target)
    v1_pass = abs(v1_error_pct) <= 20.0

    lines = []
    lines.append("# T-48 B 部分 — T-12 判準 v2 量測\n")
    lines.append(f"> 產生日期：{datetime.now(timezone.utc).isoformat()}　"
                 f"git_head：`{head}`　"
                 f"git status --porcelain -- src data scripts：{'(空)' if not dirty_check else dirty_check}\n")
    lines.append(
        "三條 IR 由 `scripts/gen_ir_manual.py`（不改動，逐字沿用 T-12 卡「Opus 驗證結果」表格"
        "已記錄的指令）本次重生，交付到 `output/material_r2/`（紅線：不得重用 `output/` 舊 IR）：\n"
    )
    lines.append("| case | 指令 | 房間 | 交付檔案 | sha256（本次重生） |")
    lines.append("|---|---|---|---|---|")
    for c in cases.values():
        cmd = "python scripts/gen_ir_manual.py " + " ".join(c["args"])
        lines.append(f"| {c['desc']} | `{cmd}` | 4×3×2.5m | `{c['final_path']}` | `{c['post_sha256']}` |")

    lines.append("\n## 0. 結論\n")
    lines.append(
        f"- **v2-a（公式層）**：{'PASS' if v2a_pass else 'FAIL'}——per-wall Sabine 125Hz "
        f"{pw['sabine_125hz_s']:.4f}s，目標 {v2a_target}s ±20%，誤差 {v2a_error_pct:+.1f}%\n"
        f"- **v2-b（IR 實測層，聯合帶 T30）**：{'PASS' if v2b_pass else 'FAIL'}——"
        f"per-wall {pw['t30_low_combined_s']:.4f}s vs 六面 gypsum 對照 {cg['t30_low_combined_s']:.4f}s"
        f"（差異 {v2b_diff_pct:+.1f}%，判準 ≤±20% → {'PASS' if v2b_diff_pass else 'FAIL'}）；"
        f"六面 carpet 對照 {cc['t30_low_combined_s']:.4f}s / per-wall = {v2b_ratio:.2f} 倍"
        f"（判準 ≥3 倍 → {'PASS' if v2b_ratio_pass else 'FAIL'}）\n"
        f"- **v1 字面條件（只記錄不當門檻）**：{'PASS' if v1_pass else '未達'}——per-wall 125Hz 八度 T30 "
        f"{pw['t30_125hz_octave_s']:.4f}s，字面目標 {v1_target}s ±20%，誤差 {v1_error_pct:+.1f}%"
        f"（裁決 B 已證八度量測受鄰帶耦合污染，此數字**不當作判準**，僅照量照列）\n"
    )

    lines.append("\n## 1. 逐案數值（程式量測，未手打）\n")
    lines.append("| case | Sabine 125Hz (s) | 125Hz 八度 T30 (s) | 88.4–353.6Hz 聯合帶 T30 (s) |")
    lines.append("|---|---|---|---|")
    for c in cases.values():
        sab = f"{c['sabine_125hz_s']:.4f}" if c["sabine_125hz_s"] is not None else "—"
        lines.append(f"| {c['desc']} | {sab} | {c['t30_125hz_octave_s']:.4f} | {c['t30_low_combined_s']:.4f} |")

    lines.append(
        "\n## 2. 方法\n\n"
        "1. `scripts/gen_ir_manual.py`（**零改動**）依上表指令重生三條 IR，程式預設寫到 `output/`，"
        "本腳本立即搬到 `output/material_r2/`（sha256 在搬移前後都算過，確認 bytes 未在搬移過程變動）。\n"
        "2. v2-a：Sabine 125Hz 數字讀自 `gen_ir_manual.py` 本次執行的 stdout（程式印出，不手打）。\n"
        "3. v2-b／v1：讀 `src/image_reverb/ir_metrics.py` 既有函式——`t30_low_combined()`（T-18，"
        "88.4–353.6Hz 聯合帶）與 `band_t30(ir, fs, [125])`（單一 125Hz 八度，v1 字面條件用）——"
        "對本次重生的 WAV 直接量測，不重新實作任何頻段濾波／Schroeder 積分邏輯。\n"
        "4. `ir_metrics.py`、`src/`、`data/` 全程零 diff（本卡只呼叫既有函式，不修改）。\n"
    )

    MATERIAL_OUT.mkdir(parents=True, exist_ok=True)
    (MATERIAL_OUT / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"已寫入：{MATERIAL_OUT / 'REPORT.md'}")

    criteria_text = """# T-12 判準 v2（複製自 TASKS.md T-48 卡 §8，供追溯；內容不得與本卡不同）

criteria_version: v2（裁決 T-45-A 於 T-48 卡事前鎖定：v2-a 公式層 Sabine 125Hz＝0.348s ±20%；
v2-b IR 實測層改量 T-18 聯合帶 T30，判準見 T-48 卡）

B 部分——T-12 判準 v2 量測：
1. 用 `scripts/gen_ir_manual.py` 重生三條 IR：per-wall（4×3×2.5m，floor=carpet／其餘
   gypsum_board）、對照組六面 gypsum_board、對照組六面 carpet（與 T-12 交接筆記同設定）；
2. v2-a（公式層）：`compute_acoustics()`／Sabine 125Hz 對 per-wall 房間＝0.348s ±20%
   （重跑確認，預期達成）；
3. v2-b（IR 實測層，聯合帶）：用 T-18 `t30_low_combined()`（88.4–353.6Hz）量三條 IR。
   判準：per-wall IR 的聯合帶 T30 與六面 gypsum 對照組差異 ≤ ±20%，且六面 carpet 對照組
   的聯合帶 T30 ≥ per-wall 的 3 倍；
4. 原 v1 字面條件（125Hz 八度 T30 ≈0.35s ±20%）照量照列，預期仍未達（裁決 B 已證八度
   量測受鄰帶耦合污染），只記錄不當門檻；
5. `output/material_r2/REPORT.md`（程式產表）＋`CRITERIA_T12_v2.md`（本檔）。
"""
    (MATERIAL_OUT / "CRITERIA_T12_v2.md").write_text(criteria_text, encoding="utf-8")
    print(f"已寫入：{MATERIAL_OUT / 'CRITERIA_T12_v2.md'}")

    return {
        "v2a_pass": v2a_pass,
        "v2b_pass": v2b_pass,
        "v1_pass": v1_pass,
    }


def cmd_part_b() -> None:
    cases = run_part_b()
    verdicts = _write_part_b_report(cases)
    print(f"\nPart B 完成：v2-a={'PASS' if verdicts['v2a_pass'] else 'FAIL'} "
          f"v2-b={'PASS' if verdicts['v2b_pass'] else 'FAIL'} "
          f"v1（不當門檻，僅記錄）={'PASS' if verdicts['v1_pass'] else '未達'}")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("manifest", "partA", "partB", "all"):
        print(__doc__)
        sys.exit(2)
    mode = sys.argv[1]
    if mode == "manifest":
        cmd_manifest()
    elif mode == "partA":
        cmd_part_a()
    elif mode == "partB":
        cmd_part_b()
    elif mode == "all":
        cmd_part_a()
        cmd_part_b()
