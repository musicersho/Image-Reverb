#!/usr/bin/env python3
"""T-48：T-11／T-12 判準第二版針對性重驗（量測卡；裁決 T-45-A 執行卡 3/5）。

`src/` 零改動——本腳本只呼叫既有 CLI（`python -m src.image_reverb`）與既有
`scripts/gen_ir_manual.py`／`src.image_reverb.ir_metrics`，不重新實作任何評分邏輯。

13 張照片清單唯一可信來源＝`scripts/t36_clip_accuracy.GATE_ITEMS`（不重打）。

用法：
    python scripts/t48_geometry_material_r2.py manifest             # 只建 DATASET_MANIFEST.json（開跑前置）
    python scripts/t48_geometry_material_r2.py partA                # T-11 域外出口重驗（真跑 CLI）
    python scripts/t48_geometry_material_r2.py partA-report-only    # 只讀既有 runs/ log 重產 REPORT.md，不重跑 CLI
    python scripts/t48_geometry_material_r2.py partB                # T-12 判準 v2 量測（真跑 gen_ir_manual.py）
    python scripts/t48_geometry_material_r2.py partB-report-only    # 只讀既有交付 WAV／log 重產 REPORT.md，不重生 IR
    python scripts/t48_geometry_material_r2.py all                  # A+B（皆真跑）
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
        # 修正輪（Sonnet，2026-09-14）依裁決 T-48-F 第 3 點（Fable）：v2 判準文字本身自相矛盾
        # （「已知實際尺寸」列了車內 ~2m，但誤差判準括號卻寫「目前只有浴室」），只改標籤與說明
        # 文字、不改任何量測數字、不改分類邏輯（v2_category 仍是 not_applicable，只是顯示的
        # verdict 從「不適用」改成 inconclusive，理由見下）。
        "v2_verdict": "inconclusive",
        "note": "v2 判準文字自相矛盾（「已知實際尺寸」列了車內 ~2m，但誤差判準括號卻寫「目前只有浴室」）——"
        "依裁決 T-48-F 第 3 點（Fable，2026-09-14），v2 記 inconclusive（判準文字自相矛盾），"
        "不是 PASS、不是 FAIL，也不是原記的「不適用」。v3（T-55）將車內歸類 domain_out_non_room"
        "（依 T-11 原卡步驟 5「車內與超大空間允許數字不準」，與 >10m 域外同款判準：geometry_confidence "
        "必須 low 且 gate 訊息含 --override-dims 導引；估計誤差只記錄不判）。",
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


def _matched_rules(text: str) -> list[str]:
    tags = []
    for tag, marker in _RULE_MARKERS:
        if marker in text:
            tags.append(tag)
    return tags


# 修正輪（Sonnet，2026-09-14）新增，回應 Opus 驗證紀錄 R7：從 default_log／force_log 的原始文字
# 直接解析（不依賴 analysis.json——blocked 案例的 analysis.json 會被 pipeline 清空／搬進
# output/.archive/，report-only 模式讀不到），一併算出「被哪一軸擋下」與「gate 給的出口」，
# 讓 §1／§4 能誠實列出 R7 指出的缺漏（RacquetballCourt4 被材質軸擋、不是幾何軸）。
def _build_result(name: str, photo: str, known: dict | None, default_log: str, force_log: str,
                   default_exit: int | None, force_exit: int | None) -> dict:
    conf_match = _CONF_LINE_RE.search(default_log)
    dims_match = _DIMS_LINE_RE.search(default_log)
    geometry_confidence = conf_match.group(1) if conf_match else None
    materials_confidence = conf_match.group(2) if conf_match else None
    overall_confidence = conf_match.group(3) if conf_match else None
    blocked = "已擋下輸出" in default_log
    override_dims_guidance = "幾何不可信 → 用 --override-dims" in default_log
    override_material_guidance = "--override-material" in default_log
    low_confidence_faces = sorted(set(re.findall(r"\n\s+(\w+)：目前推測", default_log)))

    blocking_axes = []
    if blocked:
        if geometry_confidence == "low":
            blocking_axes.append("geometry")
        if materials_confidence == "low":
            blocking_axes.append("materials")

    if dims_match:
        length_m, width_m, height_m = (float(dims_match.group(i)) for i in (1, 2, 3))
        dims_source = dims_match.group(4)
    else:
        length_m = width_m = height_m = None
        dims_source = None

    max_dim = max((v for v in (length_m, width_m, height_m) if v is not None), default=None)
    matched_rules = _matched_rules(force_log)

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
        verdict = known.get("v2_verdict", "不適用")
        verdict_detail = known["note"]
    else:
        verdict = "不適用（未知，不列入 v2 判定）"
        verdict_detail = "無已知實際尺寸，僅記錄估計值供參考，不列入 FAIL/PASS 判定。"

    return {
        "name": name,
        "photo": photo,
        "dims_source": dims_source,
        "length_m": length_m,
        "width_m": width_m,
        "height_m": height_m,
        "max_dim_m": max_dim,
        "volume_m3": (length_m or 0) * (width_m or 0) * (height_m or 0),
        "geometry_confidence": geometry_confidence,
        "materials_confidence": materials_confidence,
        "overall_confidence": overall_confidence,
        "blocked": blocked,
        "blocking_axes": blocking_axes,
        "override_dims_guidance": override_dims_guidance,
        "override_material_guidance": override_material_guidance,
        "low_confidence_faces": low_confidence_faces,
        "matched_scope_rules": matched_rules,
        "v2_category": v2_category,
        "known": known,
        "verdict": verdict,
        "verdict_detail": verdict_detail,
        "default_exit": default_exit,
        "force_exit": force_exit,
    }


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

        # 1) force-low-confidence 先跑：只是為了讀 stdout 裡完整的 warnings/notes
        #    （量程規則觸發細節），不影響、不重新計算 gate 判定本身。
        force_exit, force_log = _run_cli(
            photo, ["--force-low-confidence"], runs_dir / name / "force_low_confidence.log"
        )

        # 2) 預設路徑（無旗標）：這才是真正的 production gate 行為，域外判準看這次的輸出。
        default_exit, default_log = _run_cli(
            photo, [], runs_dir / name / "default.log"
        )

        known = KNOWN_DIMENSIONS.get(name)
        r = _build_result(name, photo, known, default_log, force_log, default_exit, force_exit)
        results.append(r)
        print(f"    dims={r['length_m']:.2f}x{r['width_m']:.2f}x{r['height_m']:.2f} "
              f"geometry_confidence={r['geometry_confidence']} materials_confidence={r['materials_confidence']}"
              f" v2_category={r['v2_category']} verdict={r['verdict']}")
    return results


def run_part_a_report_only() -> list[dict]:
    """修正輪（Sonnet，2026-09-14）新增，回應 Opus 修正輪指示第 1 條「Part A 不必重跑」：
    完全讀 output/geometry_r2/runs/<name>/{default,force_low_confidence}.log 這些既有真實 CLI
    輸出（Part A 首跑時已寫入、未曾刪改），不再呼叫任何 subprocess，只用來重產 REPORT.md 的
    文字／表格／欄位（例如本輪新加的 materials_confidence／blocking_axes 欄）。"""
    runs_dir = GEOMETRY_OUT / "runs"
    results = []
    for item in GATE_ITEMS:
        name = item["name"]
        photo = item["photo"]
        default_log_path = runs_dir / name / "default.log"
        force_log_path = runs_dir / name / "force_low_confidence.log"
        if not default_log_path.exists() or not force_log_path.exists():
            print(f"❌ 錯誤：{default_log_path} 或 {force_log_path} 不存在，無法只重產報表——請先跑 partA 一次。")
            sys.exit(1)
        default_log = default_log_path.read_text(encoding="utf-8")
        force_log = force_log_path.read_text(encoding="utf-8")
        known = KNOWN_DIMENSIONS.get(name)
        results.append(_build_result(name, photo, known, default_log, force_log, None, None))
    return results


def _write_part_a_report(results: list[dict], report_only: bool = False) -> None:
    head = git_head()
    dirty_check = git_status_clean(["src", "data", "scripts"])
    lines = []
    lines.append("# T-48 A 部分 — T-11 域外出口無誤放重驗（判準 v2）\n")
    lines.append(f"> 產生日期：{datetime.now(timezone.utc).isoformat()}　"
                 f"git_head：`{head}`　"
                 f"git status --porcelain -- src data scripts：{'(空)' if not dirty_check else dirty_check}\n")
    # 第二修正輪（Sonnet，2026-09-14）回應 Opus 修正輪複驗紀錄 Q2：report-only 模式下
    # git_head 只是「這次重產報表當下」的 commit，不是量測發生的 commit，兩者不寫清楚
    # 會讓讀者誤以為每次重產報表都重新跑了一次 CLI。這裡另外列出真正量測的 commit。
    if report_only:
        lines.append(
            f"> **本報表為 report-only 重產於 `{head}`，未重跑 CLI**——13 張照片的真實 CLI 量測"
            f"（`default`／`force_low_confidence` 兩次執行、寫入 `output/geometry_r2/runs/` 的原始 log）"
            f"實際發生於 **量測 commit `{PART_A_MEASUREMENT_COMMIT}`**（Part A 最終程式版本，見 T-11 "
            f"§8「Opus 更正」）；本次只讀既有 log 重新組字串／表格，數字不會、也不可能因此改變。\n"
        )
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
    lines.append(
        "（修正輪，Sonnet 2026-09-14，回應 Opus 驗證紀錄 R7：新增 `materials_confidence`／`擋在哪軸` 欄——"
        "原表只列 geometry_confidence，讀者無法判斷 gate 是被幾何軸還是材質軸擋下，"
        "RacquetballCourt4 正是被 materials 軸擋、geometry 軸沒擋，見下方 §4。）\n"
    )
    lines.append("| 照片 | 估計 L×W×H (m) | 最大維 | dims_source | geometry_confidence | materials_confidence | 已擋下 | 擋在哪軸 | override-dims 導引 | v2 類別 | 判定 | 細節 |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in results:
        lines.append(
            f"| {r['name']} | {r['length_m']:.2f}×{r['width_m']:.2f}×{r['height_m']:.2f} "
            f"| {r['max_dim_m']:.2f} | {r['dims_source']} | {r['geometry_confidence']} "
            f"| {r['materials_confidence']} | {'是' if r['blocked'] else '否'} "
            f"| {'、'.join(r['blocking_axes']) if r['blocking_axes'] else '—'} "
            f"| {'有' if r['override_dims_guidance'] else '無'} | {r['v2_category']} "
            f"| {r['verdict']} | {r['verdict_detail']} |"
        )

    lines.append("\n## 2. 觸發的量程／場景線索規則（讀自 `--force-low-confidence` 重跑的真實 CLI stdout warnings，"
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
            # 修正輪（Sonnet，2026-09-14）新增，回應 Opus 驗證紀錄 R7：原 REPORT 只寫
            # 「gate 未印 override-dims 導引」，沒說預設路徑其實已經被「材質軸」擋下（不是幾何軸沒擋
            # 就等於 gate 放行），也沒說 gate 給的出口是什麼、使用者照做的後果是什麼——這裡補齊。
            lines.append(
                f"**gate 實際擋在哪一軸**：預設路徑 `blocked={r['blocked']}`"
                f"（`geometry_confidence={r['geometry_confidence']}`、"
                f"`materials_confidence={r['materials_confidence']}`），"
                f"擋下的軸＝{('、'.join(r['blocking_axes']) or '無（本張預設路徑未被擋下）')}。"
            )
            if "materials" in r["blocking_axes"] and "geometry" not in r["blocking_axes"]:
                # 第二修正輪（Sonnet，2026-09-14）回應 Opus 修正輪複驗紀錄 N3（非退回理由，順手處理）：
                # actual_dims_m 原本是 Python list repr（例如 [12.19, 6.1, 6.1]）原樣輸出，改成
                # 與上面估計尺寸同款的 L×W×H(m) 格式，純外觀、不改任何數值。
                known = r["known"] or {}
                if "actual_dims_m" in known:
                    dl, dw, dh = known["actual_dims_m"]
                    actual_dims_str = f"{dl:.2f}×{dw:.2f}×{dh:.2f}m"
                else:
                    actual_dims_str = f"最大維 {known['actual_max_dim_m']}m"
                lines.append(
                    f"即：本張是被**材質軸**擋下，幾何軸維持 medium（未觸發 low），"
                    f"所以 gate 給的出口只有材質覆寫（低信心面：{('、'.join(r['low_confidence_faces']) or '無')}），"
                    f"**沒有**提供 `--override-dims` 這個出口——使用者如果只照 gate 訊息字面操作"
                    f"（覆寫上述材質面），程式不會再擋幾何，會直接用這張的**錯誤估計尺寸**"
                    f"（{r['length_m']:.2f}×{r['width_m']:.2f}×{r['height_m']:.2f}m，"
                    f"實際 {actual_dims_str}）"
                    f"輸出 IR，exit 0。**這一步已由 Opus 驗證紀錄 V5（2026-09-14，驗證時 HEAD "
                    f"`153155b`）實測確認**：對 RacquetballCourt4 加 "
                    f"`--override-material north=gypsum_board --override-material ceiling=wood_panel` 後，"
                    f"`geometry=medium, materials=medium, overall=medium`、exit 0，"
                    f"以 16.10×9.39×5.55m 錯誤幾何（實際 12.19×6.10×6.10m）輸出 IR——"
                    f"即使用者依 gate 導引走完整個「怎麼繼續」流程仍會拿到錯誤空間的 IR。"
                    f"這是本卡交 Fable 的 F1 建議（修 `apply_scope_confidence()` 環景分支，"
                    f"裁決 T-48-F 已開 T-54 執行）的根本原因，本卡本身不改 `geometry.py`。\n"
                )
        lines.append("")

    lines.append(
        "\n## 5. 方法\n\n"
        "每張照片跑兩次真實 CLI（`python -m src.image_reverb <photo> --no-viz`）：\n"
        "1. 先加 `--force-low-confidence` 跑一次，只為了讀該次 stdout 的完整 "
        "`warnings`（量程/場景線索規則的詳細文字），不影響任何判定。\n"
        "2. 再跑一次**不帶任何旗標**（真正的預設 production 路徑），這次的 stdout/stderr 才是 gate 判定"
        "與 `--override-dims`／`--override-material` 導引訊息的真實來源——v2 判準完全依這次輸出判定。\n\n"
        "13 張照片清單與路徑唯一來源：`scripts/t36_clip_accuracy.GATE_ITEMS`（不重打）。"
        "逐張原始 CLI 輸出存於 `output/geometry_r2/runs/<name>/{default,force_low_confidence}.log`"
        "（本卡首跑產生；修正輪 `partA-report-only` 模式只讀這些既有 log 重產本報表文字，"
        "不重新呼叫 CLI，不重跑 Part A——Opus 修正輪指示第 1 條）。\n"
    )

    GEOMETRY_OUT.mkdir(parents=True, exist_ok=True)
    (GEOMETRY_OUT / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"已寫入：{GEOMETRY_OUT / 'REPORT.md'}")


def cmd_part_a() -> None:
    results = run_part_a()
    _write_part_a_report(results)
    fail_count = sum(1 for r in results if r["verdict"] == "FAIL")
    print(f"\nPart A 完成：FAIL 筆數 = {fail_count}")


def cmd_part_a_report_only() -> None:
    results = run_part_a_report_only()
    _write_part_a_report(results, report_only=True)
    fail_count = sum(1 for r in results if r["verdict"] == "FAIL")
    print(f"\nPart A（只重產報表，未重新呼叫 CLI）完成：FAIL 筆數 = {fail_count}")


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


# 修正輪（Sonnet，2026-09-14）新增，回應 Opus 驗證紀錄 R5／裁決 T-48-F F2：v2-b diff 子判準的
# 官方 verdict 是「首跑」（commit d372ad9，本卡 Part B 第一次實作後隨即執行的那次）的結果，
# 不是「本次交付版本」的結果——量測方法已證實非決定性（同指令重跑三次落在門檻兩側），
# 依 WORKFLOW §7.5「舊量測方法被證明無效時，舊結果不能直接改成 PASS」，永久記首跑 verdict。
# 原始 WAV／stdout log 已於本卡執行期間的後續重跑覆蓋，此數字是執行者自述、無殘存產物可複核
# （Opus 驗證紀錄 R3），標示清楚後仍照實引用（不是憑空捏造，三次重跑本身有 commit 時序佐證）。
FIRST_RUN_V2B_DIFF_PCT = -21.1
FIRST_RUN_V2B_VERDICT = "FAIL"
FIRST_RUN_V2B_COMMIT = "d372ad9"

# 第二修正輪（Sonnet，2026-09-14）新增，回應 Opus 修正輪複驗紀錄 Q2（溯源失實）：
# report-only 模式重產 REPORT 時，檔頭的 git_head 只反映「這次重產報表當下」的 commit
# （例如跑 partB-report-only 時的 HEAD），跟「量測實際發生的 commit」是兩回事——不寫清楚
# 會讓讀者誤以為每次重產報表都重新量了一次。這兩個常數記錄「量測本體真正發生」的 commit，
# 供 REPORT 檔頭另外列出，report-only 不改這兩個值。
# A：Part A 最終真跑 CLI 的 commit（13 張 default／force_low_confidence log 的產生時刻；
#    T-11 §8「Opus 更正」已核對 714703d 是 Part A 最終程式版本，469abef 只是初版）。
PART_A_MEASUREMENT_COMMIT = "714703d"
# B：本卡交付 WAV 實際由 gen_ir_manual.py 重生的 commit（三次「官方」重跑中的第三次，也是
#    唯一留存到 output/material_r2/ 的交付版本；前兩次 d372ad9／dd03c0e 的產物已被覆蓋）。
PART_B_MEASUREMENT_COMMIT = "cda6b9b"


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


STABILITY_REPEATS = 4  # 額外重跑次數（附錄用，不影響官方判定）


def run_stability_check() -> dict:
    """pyroomacoustics 的 ray tracing 沒有固定 seed，同一指令重跑 bytes 不同
    （已用 shasum 實測確認）。這裡額外重跑 per_wall／control_gypsum 各
    `STABILITY_REPEATS` 次，寫進 `output/material_r2/stability_check/`（與正式交付檔案
    分開存放，不覆蓋、不算入 §0 官方判定），只為了讓 Opus／Fable 看到量測本身的
    隨機噪聲量級——**不改變本卡官方判定**（判準與流程不因此改動，WORKFLOW §7）。
    """
    stability_dir = MATERIAL_OUT / "stability_check"
    stability_dir.mkdir(parents=True, exist_ok=True)
    repeats = {"per_wall": [], "control_gypsum": []}
    specs_by_case = {s["case"]: s for s in IR_CASES}
    for case in ("per_wall", "control_gypsum"):
        spec = specs_by_case[case]
        legacy_path = LEGACY_OUTPUT / spec["legacy_name"]
        for i in range(STABILITY_REPEATS):
            proc = subprocess.run(
                ["python", str(GEN_IR_SCRIPT)] + spec["args"],
                cwd=PROJECT_ROOT, capture_output=True, text=True,
            )
            if proc.returncode != 0 or not legacy_path.exists():
                continue
            dest = stability_dir / f"{case}_rep{i}.wav"
            legacy_path.replace(dest)
            ir, fs = sf.read(str(dest))
            repeats[case].append(t30_low_combined(ir, fs))
    return repeats


def _write_stability_appendix(cases: dict, repeats: dict) -> list[str]:
    pw_official = cases["per_wall"]["t30_low_combined_s"]
    cg_official = cases["control_gypsum"]["t30_low_combined_s"]
    pw_all = [pw_official] + repeats.get("per_wall", [])
    cg_all = [cg_official] + repeats.get("control_gypsum", [])
    diffs_pct = [
        _pct_diff(pw_v, cg_v)
        for pw_v in pw_all
        for cg_v in cg_all
    ]
    # 修正輪（Sonnet，2026-09-14）回應 Opus 驗證紀錄 R4：official_diff／official_verdict 移到
    # 段落文字組出之前計算，讓下面所有句子都能動態代入，不再有任何手打的 PASS/FAIL 字面值。
    official_diff = _pct_diff(pw_official, cg_official)
    official_verdict = "PASS" if abs(official_diff) <= 20.0 else "FAIL"

    lines = []
    lines.append(
        "\n## 3. 附錄：量測穩定性檢查（不影響上方 §0 官方判定——§0 依裁決 T-48-F F2 記"
        "「首跑 FAIL、方法 inconclusive」，本次交付版本數字僅供參考）\n"
    )
    lines.append(
        "`gen_ir_manual.py` 呼叫的 pyroomacoustics ray tracing **沒有固定 random seed**"
        "（已實測：同一指令重跑兩次，輸出 WAV sha256 不同，樣本點最大絕對差"
        "約 0.099——見本卡交接筆記）。"
        # 第二修正輪（Sonnet，2026-09-14）回應 Opus 修正輪複驗紀錄 Q1（R4 殘留）：這句原本寫
        # 「§0 的官方判定只用每個 case 第一次（也是唯一交付到 output/material_r2/ 的那次）重生
        # 結果」，與 §0「官方 verdict＝首跑 d372ad9、交付檔是第三次 cda6b9b」正面矛盾——
        # d372ad9 那次不是「唯一交付」的那次，交付版是後來的 cda6b9b。改成與 §0 一致的說法。
        f"**§0 的官方 verdict＝首跑（`{FIRST_RUN_V2B_COMMIT}`）；本附錄與 §1 的數字量自 "
        f"`{PART_B_MEASUREMENT_COMMIT}` 生成的交付 WAV**（見上方交付檔案表），不做多次重跑取平均"
        "（判準本身沒有要求，本卡也不得另外發明「取平均」這種未鎖定的判定方式）。\n\n"
        f"為了讓 Opus／Fable 判斷 v2-b 這筆 **{official_verdict}**（本次交付版本，"
        f"{official_diff:+.1f}%）是否落在量測噪聲量級內，"
        f"這裡**額外**重跑 per_wall／control_gypsum 各 {STABILITY_REPEATS} 次"
        "（存於 `output/material_r2/stability_check/`，與正式交付檔案分開，不算入判定）：\n\n"
    )
    lines.append(f"- per_wall 聯合帶 T30 各次量測（含官方那次）：{[round(float(v), 4) for v in pw_all]}\n")
    lines.append(f"- control_gypsum 聯合帶 T30 各次量測（含官方那次）：{[round(float(v), 4) for v in cg_all]}\n")
    lines.append(
        f"- 交叉配對後的 per_wall vs control_gypsum 差異百分比範圍："
        f"{min(diffs_pct):+.1f}% ～ {max(diffs_pct):+.1f}%（判準 ≤±20%；"
        f"官方那次配對＝{official_diff:+.1f}% → {official_verdict}）\n"
    )
    straddles = min(diffs_pct) < -20.0 < max(diffs_pct) or min(diffs_pct) < 20.0 < max(diffs_pct)
    if straddles:
        # 修正輪（Sonnet，2026-09-14）回應 Opus 驗證紀錄 R4：刪除原本「v2-b 的 {official_verdict}
        # 判定本身……站得住腳」與下段「不代表……站得住腳」互相矛盾的句子，改成單一、前後一致的
        # 說法——直接呼應裁決 T-48-F F2 的「首跑 FAIL、方法 inconclusive」結論。
        lines.append(
            f"\n**觀察**：不同次重跑的差異百分比跨越 ±20% 門檻兩側，代表這個判準在目前的量測方法"
            f"（單次生成、無固定 seed）下對隨機重跑結果敏感、鑑別力薄弱——這正是本卡 §0 記"
            f"「v2-b 首跑 FAIL、方法 inconclusive」、不採用本次交付版本 {official_verdict}"
            f"（{official_diff:+.1f}%）當作最終結論的原因（WORKFLOW §7.5：量測方法被證明無效時，"
            f"舊結果不能直接改成 PASS）。是否改進量測方法（例如固定 seed、多次取中位數）已交由 "
            f"T-56（criteria v3，裁決 T-48-F F2）處理，本卡不自行更動判準或判定方式。\n"
        )

    lines.append(
        "\n**本卡執行過程中的官方量測歷史（誠實揭露，非結果篩選；修正輪 R3 更正標示，Sonnet 2026-09-14："
        "前兩筆原始 WAV／log 已於後續重跑覆蓋，數字為執行者自述，無殘存產物可複核）**：本卡執行期間因程式"
        "本身的修正（除錯與格式修正，與量測邏輯／判準無關）重新跑過三次「官方」"
        "per_wall／control_gypsum 生成＋量測，每一次都是當時唯一交付到 "
        "`output/material_r2/` 的版本（前一次的交付檔案在下一次重跑時被覆蓋，"
        "紅線要求不得重用舊 IR，所以每次重跑本來就必須用新生成的檔案）：\n\n"
        "| 官方重跑對應 commit | per_wall vs control_gypsum 差異 | v2-b diff 子判準 | 資料來源 |\n"
        "|---|---|---|---|\n"
        "| `d372ad9`（Part B 首次實作，隨即執行，**首跑 verdict**） | -21.1% | FAIL | "
        "執行者自述、無殘存產物、不可複核（Opus 驗證紀錄 R3） |\n"
        "| `dd03c0e`（新增本附錄後重跑） | -22.3% | FAIL | 執行者自述、無殘存產物、不可複核（同上） |\n"
        f"| `cda6b9b`（修正附錄 numpy 顯示格式後重跑，本次交付版本） | {official_diff:+.1f}% | {official_verdict} | "
        f"可複核：`output/material_r2/` 現存交付 WAV（sha256 見上表） |\n\n"
        "三次都不是為了「重跑到通過為止」而執行——每次重跑的直接原因記在對應 commit "
        "訊息裡（附錄程式碼新增、顯示格式修正），跟 v2-b 的判定方向無關；但三次結果"
        f"本身（-21.1%／-22.3%／{official_diff:+.1f}%）都群聚在 ±20% 門檻附近，"
        "印證上面「觀察」段的結論：這個判準在目前的量測方法下沒有穩定的鑑別力。"
        "**依裁決 T-48-F F2（Fable，2026-09-14）：本卡 §0 官方記錄＝「首跑 FAIL、方法 inconclusive」，"
        "永久保留，不因本次交付版本剛好是 PASS 就回頭改記 PASS**（WORKFLOW §7.5）；"
        "量測方法是否修正（固定 seed／多次取中位數）由 T-56（criteria v3）另行處理，"
        "本卡不自行更動判準或判定方式。\n"
    )
    return lines


def _write_part_b_report(cases: dict, repeats: dict | None = None, report_only: bool = False) -> None:
    head = git_head()
    dirty_check = git_status_clean(["src", "data", "scripts"])
    pw = cases["per_wall"]
    cg = cases["control_gypsum"]
    cc = cases["control_carpet"]

    # 第二修正輪（Sonnet，2026-09-14）回應 Opus 修正輪複驗紀錄 Q2：report-only 模式下所有
    # 「本次重生／本次執行／搬移前後」字句都改指向真正量測發生的 commit（PART_B_MEASUREMENT_COMMIT），
    # 不寫死成「本次」——否則 8bfe262／cbc117b 這種只重產報表沒重生 IR 的 commit，字面上會變成
    # 「本次重生」的假象（Opus 修正輪複驗紀錄 Q2 正是抓到這個）。
    if report_only:
        regen_phrase = f"`{PART_B_MEASUREMENT_COMMIT}` 那次重生"
        regen_stdout_phrase = f"`{PART_B_MEASUREMENT_COMMIT}` 那次執行的 stdout（讀自 `output/material_r2/runs/*.log`，本次未重新呼叫 `gen_ir_manual.py`）"
        move_note = f"（`{PART_B_MEASUREMENT_COMMIT}` 那次生成時搬移前後都算過 sha256；本次 report-only 只讀既有交付 WAV 重新量測與重組文字，未搬移、未重新生成任何檔案）"
    else:
        regen_phrase = "本次重生"
        regen_stdout_phrase = "本次執行的 stdout（程式印出，不手打）"
        move_note = "（sha256 在搬移前後都算過，確認 bytes 未在搬移過程變動）"

    # v2-a：per-wall Sabine 125Hz ≈0.348s ±20%
    v2a_target = 0.348
    v2a_error_pct = _pct_diff(pw["sabine_125hz_s"], v2a_target)
    v2a_pass = abs(v2a_error_pct) <= 20.0

    # v2-b：per-wall 聯合帶 T30 與六面 gypsum 對照差異 ≤±20%；六面 carpet 對照 ≥ per-wall 3 倍
    # 修正輪（Sonnet，2026-09-14）回應 R5／裁決 T-48-F F2：diff 子判準的官方 verdict＝首跑
    # （FIRST_RUN_V2B_VERDICT，見上方常數），本次交付版本的數字（v2b_diff_pct／v2b_diff_pass_delivered）
    # 降為次要參考，不再是 §0 的結論來源。ratio 子判準不受這個問題影響（見 §3 穩定性附錄，
    # per_wall 的隨機變動範圍不足以讓 3.97 倍掉到 3 倍以下），繼續照量照列。
    v2b_diff_pct = _pct_diff(pw["t30_low_combined_s"], cg["t30_low_combined_s"])
    v2b_ratio = cc["t30_low_combined_s"] / pw["t30_low_combined_s"]
    v2b_diff_pass_delivered = abs(v2b_diff_pct) <= 20.0
    v2b_ratio_pass = v2b_ratio >= 3.0
    v2b_verdict_label = (
        "inconclusive（diff 子判準：首跑 FAIL，方法非決定性；ratio 子判準：PASS）"
        if v2b_ratio_pass else
        "inconclusive（diff 子判準：首跑 FAIL，方法非決定性；ratio 子判準：FAIL）"
    )

    # v1 字面條件：125Hz 八度 T30 ≈0.35s ±20%（照量照列，預期未達，只記錄不當門檻）
    v1_target = 0.35
    v1_error_pct = _pct_diff(pw["t30_125hz_octave_s"], v1_target)
    v1_pass = abs(v1_error_pct) <= 20.0

    lines = []
    lines.append("# T-48 B 部分 — T-12 判準 v2 量測\n")
    lines.append(f"> 產生日期：{datetime.now(timezone.utc).isoformat()}　"
                 f"git_head：`{head}`　"
                 f"git status --porcelain -- src data scripts：{'(空)' if not dirty_check else dirty_check}\n")
    if report_only:
        lines.append(
            f"> **本報表為 report-only 重產於 `{head}`，未重跑 CLI／未重生任何 IR**——三條交付 WAV 的"
            f"真實生成（`gen_ir_manual.py` 呼叫）實際發生於 **量測 commit `{PART_B_MEASUREMENT_COMMIT}`**"
            f"（本卡執行期間第三次「官方」重跑，也是唯一留存至今的交付版本）；本次只讀既有 WAV 與 log "
            f"重新量測（`t30_low_combined()`／`band_t30()` 對現存 bytes 直接計算）並重組文字，數字不會、"
            f"也不可能因此改變。\n"
        )
    lines.append(
        f"三條 IR 由 `scripts/gen_ir_manual.py`（不改動，逐字沿用 T-12 卡「Opus 驗證結果」表格"
        f"已記錄的指令）{regen_phrase}，交付到 `output/material_r2/`（紅線：不得重用 `output/` 舊 IR）：\n"
    )
    lines.append(f"| case | 指令 | 房間 | 交付檔案 | sha256（{regen_phrase}） |")
    lines.append("|---|---|---|---|---|")
    for c in cases.values():
        cmd = "python scripts/gen_ir_manual.py " + " ".join(c["args"])
        lines.append(f"| {c['desc']} | `{cmd}` | 4×3×2.5m | `{c['final_path']}` | `{c['post_sha256']}` |")

    lines.append("\n## 0. 結論\n")
    lines.append(
        f"- **v2-a（公式層）**：{'PASS' if v2a_pass else 'FAIL'}——per-wall Sabine 125Hz "
        f"{pw['sabine_125hz_s']:.4f}s，目標 {v2a_target}s ±20%，誤差 {v2a_error_pct:+.1f}%"
        f"（同義反覆：目標值本身就是同一公式的輸出，PASS 鑑別力為零，見裁決 T-48-F F4，只記錄"
        f"作為公式回歸性測試，不構成材質模組正確性證據）\n"
        f"- **v2-b（IR 實測層，聯合帶 T30）**：**{v2b_verdict_label}**——"
        f"**首跑**（`{FIRST_RUN_V2B_COMMIT}`，Part B 首次實作後隨即執行）diff 子判準 "
        f"per-wall vs 六面 gypsum 對照差異 {FIRST_RUN_V2B_DIFF_PCT:+.1f}% → **{FIRST_RUN_V2B_VERDICT}**"
        f"（判準 ≤±20%；原始 WAV／log 已於本卡執行期間的後續重跑覆蓋，此數字為執行者自述、"
        f"無殘存產物可複核，見 §3）。依裁決 T-48-F F2（Fable，2026-09-14）：diff 子判準永久記"
        f"首跑 verdict，量測方法（單次生成、無固定 seed）已證實非決定性，不得因後續重跑改記 PASS"
        f"（WORKFLOW §7.5）。**本次交付版本數字（次要，僅供參考，不是結論）**：per-wall "
        f"{pw['t30_low_combined_s']:.4f}s vs 六面 gypsum 對照 {cg['t30_low_combined_s']:.4f}s"
        f"（差異 {v2b_diff_pct:+.1f}% → {'PASS' if v2b_diff_pass_delivered else 'FAIL'}）。"
        f"ratio 子判準（六面 carpet 對照 {cc['t30_low_combined_s']:.4f}s / per-wall = "
        f"{v2b_ratio:.2f} 倍，判準 ≥3 倍）不受本卡實測到的隨機噪聲量級影響（見 §3）"
        f"→ {'PASS' if v2b_ratio_pass else 'FAIL'}\n"
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
        f"\n## 2. 方法\n\n"
        f"1. `scripts/gen_ir_manual.py`（**零改動**）依上表指令重生三條 IR，程式預設寫到 `output/`，"
        f"本腳本立即搬到 `output/material_r2/`{move_note}。\n"
        f"2. v2-a：Sabine 125Hz 數字讀自 `gen_ir_manual.py` {regen_stdout_phrase}。\n"
        f"3. v2-b／v1：讀 `src/image_reverb/ir_metrics.py` 既有函式——`t30_low_combined()`（T-18，"
        f"88.4–353.6Hz 聯合帶）與 `band_t30(ir, fs, [125])`（單一 125Hz 八度，v1 字面條件用）——"
        f"對 {regen_phrase}的 WAV 直接量測，不重新實作任何頻段濾波／Schroeder 積分邏輯。\n"
        f"4. `ir_metrics.py`、`src/`、`data/` 全程零 diff（本卡只呼叫既有函式，不修改）。\n"
    )

    if repeats is None:
        print("執行量測穩定性附錄（額外重跑，不影響官方判定）…")
        repeats = run_stability_check()
    lines.extend(_write_stability_appendix(cases, repeats))

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
        "v2b_verdict_label": v2b_verdict_label,
        "v1_pass": v1_pass,
    }


def cmd_part_b() -> None:
    cases = run_part_b()
    verdicts = _write_part_b_report(cases)
    print(f"\nPart B 完成：v2-a={'PASS' if verdicts['v2a_pass'] else 'FAIL'} "
          f"v2-b={verdicts['v2b_verdict_label']} "
          f"v1（不當門檻，僅記錄）={'PASS' if verdicts['v1_pass'] else '未達'}")


def cmd_part_b_report_only() -> None:
    """只重新產生 REPORT.md 的文字／表格（例如修正顯示格式），**完全讀已在磁碟上的
    交付 WAV／log，不再呼叫 gen_ir_manual.py**——因為 pyroomacoustics 沒有固定 seed，
    每多跑一次官方生成就是再多一個獨立隨機draw，會製造出看起來像「重跑到滿意為止」
    的觀感。純文字/格式修正時必須走這條路徑，不能重新生成。"""
    cases = {}
    for spec in IR_CASES:
        final_path = MATERIAL_OUT / spec["final_name"]
        log_path = MATERIAL_OUT / "runs" / f"{spec['case']}.log"
        if not final_path.exists() or not log_path.exists():
            print(f"❌ 錯誤：{final_path} 或 {log_path} 不存在，無法只重產報表——請跑 partB 完整流程一次。")
            sys.exit(1)
        stdout = log_path.read_text(encoding="utf-8")
        ir, fs = sf.read(str(final_path))
        cases[spec["case"]] = {
            **spec,
            "final_path": str(final_path.relative_to(PROJECT_ROOT)),
            "pre_sha256": None,
            "post_sha256": sha256_file(final_path),
            "regenerated": True,
            "sabine_125hz_s": _sabine_125hz_from_stdout(stdout),
            "t30_low_combined_s": t30_low_combined(ir, fs),
            "t30_125hz_octave_s": band_t30(ir, fs, [125])[0],
            "fs": fs,
        }

    stability_dir = MATERIAL_OUT / "stability_check"
    repeats = {"per_wall": [], "control_gypsum": []}
    for case in ("per_wall", "control_gypsum"):
        i = 0
        while (p := stability_dir / f"{case}_rep{i}.wav").exists():
            ir, fs = sf.read(str(p))
            repeats[case].append(t30_low_combined(ir, fs))
            i += 1
    if not repeats["per_wall"]:
        print(f"❌ 錯誤：{stability_dir} 底下找不到既有重跑檔，無法只重產報表。")
        sys.exit(1)

    verdicts = _write_part_b_report(cases, repeats=repeats, report_only=True)
    print(f"\nPart B（只重產報表，未重新生成任何 IR）完成："
          f"v2-a={'PASS' if verdicts['v2a_pass'] else 'FAIL'} "
          f"v2-b={verdicts['v2b_verdict_label']} "
          f"v1（不當門檻，僅記錄）={'PASS' if verdicts['v1_pass'] else '未達'}")


if __name__ == "__main__":
    valid_modes = ("manifest", "partA", "partA-report-only", "partB", "partB-report-only", "all")
    if len(sys.argv) < 2 or sys.argv[1] not in valid_modes:
        print(__doc__)
        sys.exit(2)
    mode = sys.argv[1]
    if mode == "manifest":
        cmd_manifest()
    elif mode == "partA":
        cmd_part_a()
    elif mode == "partA-report-only":
        cmd_part_a_report_only()
    elif mode == "partB":
        cmd_part_b()
    elif mode == "partB-report-only":
        cmd_part_b_report_only()
    elif mode == "all":
        cmd_part_a()
        cmd_part_b()
