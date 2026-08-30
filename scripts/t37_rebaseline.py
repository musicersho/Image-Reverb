#!/usr/bin/env python3
"""T-37：地雷 #16 修正後的再基線（裁決 T-36-A 執行卡 1/3；共同鐵則 8）。

跑法：`python scripts/t37_rebaseline.py`（每次執行都是**全量重跑**，不讀、不寫任何
可跨次重用的快取——2026-08-31 Fable 補充：本卡時點還沒有 T-40 的快取指紋機制，
沿用任何既有 `detail.json` 會有量到舊碼的風險，所以本腳本刻意不做「快取命中就跳過」
這件事，每次執行都是乾淨的全新量測）。

**只唯讀引用 T-36 的模組與資料，不重新實作任何判定/計分邏輯**：
  - `t36_clip_accuracy.GATE_ITEMS` / `EXPECTED_GATE`——13 張照片清單與 T-28-A 基線
    （唯讀 import，不重打）
  - `t36_analysis.build_accuracy_tables()`——材質正確率計分邏輯（唯讀 import）
  - `data/material_ground_truth.json`——78 面 ground truth（本腳本不改，只讀）

**兩份「before」基線都是既有的凍結產物，本腳本只讀不寫**：
  - 三軸 confidence／gate：`output/material_round/runs/<name>__no_furn/analysis.json`
    （T-33 凍結快取，`--force-low-confidence --no-furnishings` 方法論）
  - 逐面材質判定：`output/clip_accuracy/runs/<name>/detail.json`（T-36 凍結快取）

**「after」由本腳本產生**（全新目錄，不覆蓋任何凍結基線——共同鐵則 4）：
  - `python -m src.image_reverb <photo> --force-low-confidence --no-furnishings --no-viz`
    （方法論與 T-33 `__no_furn` 組完全相同，才能三軸/gate 逐值比較），輸出
    搬到 `output/equirect_fix/runs/<name>/`
  - 輸出的 `surfaces`／`surfaces_sources` 直接餵給 `t36_analysis.build_accuracy_tables()`
    算逐面正確率，與 T-36 的 78 面 ground truth 比對口徑完全一致

驗收邏輯（本卡自我檢查的程式化版本）：
  - 三軸 confidence／gate：**只有 TunnelToHell 允許變**，其餘 12 張逐值不變，
    任何非預期漂移 → 🔴 卡關（sys.exit(1)）
  - 逐面材質判定：**只有 TunnelToHell 的 6 面允許變**，其餘 72 面逐面不變，
    任何非預期漂移 → 🔴 卡關
  - **臥室紅旗**（共同鐵則 7）：`bedroom_ai_generated` 的 materials_confidence／
    overall confidence 若從擋（low）變放，🔴 卡關

輸出：`output/equirect_fix/REPORT.md`、`output/equirect_fix/tables.md`
（含極點列統計量的量測表——地雷 #15：不手打數字）。
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
import pillow_heif  # noqa: E402

pillow_heif.register_heif_opener()

from src.image_reverb import config  # noqa: E402
from src.image_reverb.preprocess import _pole_row_diff_mean  # noqa: E402

from t36_clip_accuracy import GATE_ITEMS, EXPECTED_GATE  # noqa: E402  （唯讀引用）
from t36_analysis import build_accuracy_tables, FACES  # noqa: E402  （唯讀引用）

OUT_DIR = REPO_ROOT / "output" / "equirect_fix"
RUNS_DIR = OUT_DIR / "runs"
GROUND_TRUTH_PATH = REPO_ROOT / "data" / "material_ground_truth.json"
BEFORE_MATERIAL_ROUND = REPO_ROOT / "output" / "material_round" / "runs"
BEFORE_CLIP_ACCURACY_RUNS = REPO_ROOT / "output" / "clip_accuracy" / "runs"

# 現判為環景的 5 張（含地雷 #16 案例 TunnelToHell）——步驟 1 極點列統計量測對象
POLE_STAT_TARGETS = [
    ("CathedralRoom", "assets/reference_irs/cathedral_room_shasta_lake_caverns/CathedralRoom.jpg", True),
    ("DivorceBeach", "assets/reference_irs/divorce_beach/DivorceBeach.jpg", True),
    ("RacquetballCourt4", "assets/reference_irs/racquetball_court_4/RacquetballCourt4.jpg", True),
    ("SteinmanHall", "assets/reference_irs/steinman_hall/SteinmanHall.jpg", True),
    ("TunnelToHell", "assets/reference_irs/tunnel_to_hell/TunnelToHell.jpg", False),
]


def die(msg: str) -> None:
    print(f"🔴 卡關：{msg}", file=sys.stderr)
    sys.exit(1)


# ------------------------------------------------------------------
# 步驟 1：極點列統計量測（程式產出，地雷 #15）
# ------------------------------------------------------------------

def measure_pole_stats() -> list[dict]:
    rows = []
    for name, rel, is_real_equirect in POLE_STAT_TARGETS:
        path = REPO_ROOT / rel
        if not path.is_file():
            die(f"找不到 {path}，無法量測極點列統計量（本卡需要 assets/reference_irs/ 素材）")
        img = Image.open(path).convert("RGB")
        w, h = img.size
        gray = np.asarray(img.convert("L"))
        top_diff = _pole_row_diff_mean(gray[0])
        bottom_diff = _pole_row_diff_mean(gray[-1])
        rows.append({
            "name": name,
            "size": f"{w}x{h}",
            "aspect_ratio": round(w / h, 4),
            "top_diff": round(top_diff, 4),
            "bottom_diff": round(bottom_diff, 4),
            "max_diff": round(max(top_diff, bottom_diff), 4),
            "is_real_equirect": is_real_equirect,
        })
    true_max = max(r["max_diff"] for r in rows if r["is_real_equirect"])
    false_min = min(r["max_diff"] for r in rows if not r["is_real_equirect"])
    return rows, true_max, false_min


# ------------------------------------------------------------------
# 「after」：全新全量重跑 13 張照片（CLI，--force-low-confidence --no-furnishings）
# ------------------------------------------------------------------

def run_cli(photo: Path, name: str) -> dict:
    dst = RUNS_DIR / name
    cmd = [sys.executable, "-m", "src.image_reverb", str(photo),
           "--force-low-confidence", "--no-furnishings", "--no-viz"]
    t0 = time.time()
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=600)
    elapsed = time.time() - t0

    stem = photo.stem
    src_out = REPO_ROOT / "output" / stem
    if proc.returncode != 0 or not src_out.exists():
        die(
            f"{name} 全量重跑失敗：exit={proc.returncode}\ncmd={' '.join(cmd)}\n"
            f"--- stdout（末 40 行）---\n" + "\n".join(proc.stdout.splitlines()[-40:]) + "\n"
            f"--- stderr（末 40 行）---\n" + "\n".join(proc.stderr.splitlines()[-40:])
        )

    if dst.exists():
        shutil.rmtree(dst)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src_out), str(dst))
    aj = json.loads((dst / "analysis.json").read_text(encoding="utf-8"))
    print(f"  ✅ {name} {elapsed:.1f}s")
    return aj


# ------------------------------------------------------------------
# 表 (a)：三軸 confidence／gate before/after 對照
# ------------------------------------------------------------------

def build_gate_comparison(after_by_name: dict) -> tuple[list[dict], list[str]]:
    rows = []
    unexpected_drift = []
    for item in GATE_ITEMS:
        name = item["name"]
        before_path = BEFORE_MATERIAL_ROUND / f"{name}__no_furn" / "analysis.json"
        if not before_path.exists():
            die(f"找不到 T-33 凍結基線 {before_path}")
        before = json.loads(before_path.read_text(encoding="utf-8"))
        after = after_by_name[name]

        row = {
            "name": name,
            "before_dims_source": before["dims_source"],
            "after_dims_source": after["dims_source"],
            "before_geometry": before["geometry_confidence"],
            "after_geometry": after["geometry_confidence"],
            "before_materials": before["materials_confidence"],
            "after_materials": after["materials_confidence"],
            "before_overall": before["confidence"],
            "after_overall": after["confidence"],
        }
        changed = (
            row["before_dims_source"] != row["after_dims_source"]
            or row["before_geometry"] != row["after_geometry"]
            or row["before_materials"] != row["after_materials"]
            or row["before_overall"] != row["after_overall"]
        )
        row["changed"] = changed
        rows.append(row)

        if changed and name != "TunnelToHell":
            unexpected_drift.append(name)

        if name == "bedroom_ai_generated":
            before_blocked = row["before_materials"] == "low" or row["before_overall"] == "low"
            after_blocked = row["after_materials"] == "low" or row["after_overall"] == "low"
            if before_blocked and not after_blocked:
                die(
                    "臥室紅旗（共同鐵則 7）：bedroom_ai_generated 從擋變放！"
                    f"before materials={row['before_materials']} overall={row['before_overall']}；"
                    f"after materials={row['after_materials']} overall={row['after_overall']}"
                )
    return rows, unexpected_drift


# ------------------------------------------------------------------
# 表 (b)：逐面材質正確率再基線（沿用 T-36 ground truth 與計分邏輯）
# ------------------------------------------------------------------

def load_before_all_data() -> dict:
    all_data = {}
    for item in GATE_ITEMS:
        name = item["name"]
        cache_path = BEFORE_CLIP_ACCURACY_RUNS / name / "detail.json"
        if not cache_path.exists():
            die(f"找不到 T-36 凍結快取 {cache_path}")
        all_data[name] = json.loads(cache_path.read_text(encoding="utf-8"))
    return all_data


def after_all_data_from_analysis(after_by_name: dict) -> dict:
    all_data = {}
    for item in GATE_ITEMS:
        name = item["name"]
        aj = after_by_name[name]
        all_data[name] = {"surfaces": aj["surfaces"], "sources": aj["surfaces_sources"]}
    return all_data


def diff_face_rows(rows_before: list[dict], rows_after: list[dict]) -> tuple[list[dict], list[str]]:
    before_by_key = {(r["photo"], r["face"]): r for r in rows_before}
    after_by_key = {(r["photo"], r["face"]): r for r in rows_after}
    diffs = []
    unexpected = []
    for key in before_by_key:
        b = before_by_key[key]
        a = after_by_key[key]
        changed = (b["ai"] != a["ai"]) or (b["source"] != a["source"]) or (b["correct"] != a["correct"])
        if changed:
            photo, face = key
            diffs.append({
                "photo": photo, "face": face,
                "before_ai": b["ai"], "after_ai": a["ai"],
                "before_source": b["source"], "after_source": a["source"],
                "gt": b["gt"], "before_correct": b["correct"], "after_correct": a["correct"],
            })
            if photo != "TunnelToHell":
                unexpected.append(f"{photo}.{face}")
    return diffs, unexpected


# ------------------------------------------------------------------
# 報表輸出
# ------------------------------------------------------------------

def write_tables_md(pole_rows, true_max, false_min, threshold, gate_rows, face_diffs) -> str:
    lines = ["# T-37 再基線表（程式產出，地雷 #15）\n"]

    lines.append("## 表 1：極點列均勻度統計量（步驟 1 量測）\n")
    lines.append("| 照片 | 尺寸 | 長寬比 | 首列 diff | 末列 diff | max(首,末) | 真環景？ |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in pole_rows:
        lines.append(
            f"| {r['name']} | {r['size']} | {r['aspect_ratio']} | {r['top_diff']} | "
            f"{r['bottom_diff']} | {r['max_diff']} | {'是' if r['is_real_equirect'] else '否'} |"
        )
    lines.append(
        f"\n真環景 max(max_diff) = **{true_max}**；TunnelToHell = **{false_min}**；"
        f"門檻 `config.EQUIRECT_POLE_DIFF_THRESHOLD = {threshold}`"
        f"（真環景側餘裕 {round(threshold / true_max, 2)}x、TunnelToHell 側餘裕 "
        f"{round(false_min / threshold, 2)}x）。\n"
    )

    lines.append("## 表 2：13 張三軸 confidence／gate before/after 對照\n")
    lines.append("| 照片 | dims_source (前→後) | geometry (前→後) | materials (前→後) | overall (前→後) | 變動？ |")
    lines.append("|---|---|---|---|---|---|")
    for r in gate_rows:
        mark = "⚠️ 變動" if r["changed"] else "—"
        lines.append(
            f"| {r['name']} | {r['before_dims_source']} → {r['after_dims_source']} | "
            f"{r['before_geometry']} → {r['after_geometry']} | "
            f"{r['before_materials']} → {r['after_materials']} | "
            f"{r['before_overall']} → {r['after_overall']} | {mark} |"
        )

    lines.append("\n## 表 3：逐面材質判定漂移（預期只有 TunnelToHell 6 面）\n")
    if not face_diffs:
        lines.append("（無任何一面變動——與預期不符，應該至少有 TunnelToHell 6 面變動）\n")
    else:
        lines.append("| 照片 | 面 | AI 判定 (前→後) | 來源 (前→後) | ground truth | 正確？ (前→後) |")
        lines.append("|---|---|---|---|---|---|")
        for d in face_diffs:
            lines.append(
                f"| {d['photo']} | {d['face']} | {d['before_ai']} → {d['after_ai']} | "
                f"{d['before_source']} → {d['after_source']} | {d['gt']} | "
                f"{d['before_correct']} → {d['after_correct']} |"
            )

    return "\n".join(lines) + "\n"


def write_report_md(pole_rows, true_max, false_min, threshold, gate_rows, face_diffs) -> str:
    tunnel_gate = next(r for r in gate_rows if r["name"] == "TunnelToHell")
    n_changed_faces = len([d for d in face_diffs if d["photo"] == "TunnelToHell"])

    return f"""# T-37 地雷 #16 修正報告

依 [TASKS.md](../../TASKS.md) T-37 卡（裁決 T-36-A 執行卡 1/3）產出。
數字全部由 [scripts/t37_rebaseline.py](../../scripts/t37_rebaseline.py) 產生，
詳表見 [tables.md](tables.md)。

## 問題

`preprocess.is_equirect()` 原本只看長寬比（2.0 ± 5%），`TunnelToHell.jpg`
（2592×1296，`SOURCES.md` 記載為一般透視照）長寬比剛好落在容差內，被靜默誤判成
360° 環景（地雷 #16，`HANDOFF.md` 第 428 行；T-36 REPORT 再現並補上量化證據）。

## 修法

長寬比通過後，加一道**極點列均勻度檢查**：equirect 的第一/最後一列依定義是
天頂/天底被拉伸成整列，相鄰像素幾乎不變；一般透視照即使長寬比巧合為 2:1，
首尾列仍是正常場景內容，相鄰像素差異明顯較大。統計量：灰階首/尾列相鄰像素
絕對差的平均值，兩者取 max，需低於 `config.EQUIRECT_POLE_DIFF_THRESHOLD`。

### 表 1：門檻推導（見 tables.md 表 1）

4 張真環景（CathedralRoom／DivorceBeach／RacquetballCourt4／SteinmanHall）的
max_diff 最大值為 **{true_max}**；TunnelToHell 為 **{false_min}**。取兩者幾何中點
附近的 **{threshold}** 當門檻——真環景側餘裕 {round(threshold / true_max, 2)}x、
TunnelToHell 側餘裕 {round(false_min / threshold, 2)}x，兩側都有充分餘裕。

`is_equirect()` 函式簽章與呼叫點不變（新增的 `pole_diff_threshold` 參數有預設值，
既有呼叫點沿用預設值不必修改）。EXIF/XMP 全景標記維持**不實作**——本卡的極點列
均勻度統計量本身餘裕已足夠大（>2x），不需要疊加更弱的輔助訊號（地雷 #16 已記載
EXIF/XMP 較弱：EchoThief 這批照片已被 Photoshop 重存，中繼資料未必還在）。

## 再基線結果（表 2／表 3，見 tables.md）

**三軸 confidence／gate**：TunnelToHell `dims_source` 從 `equirect_multiview` →
`{tunnel_gate['after_dims_source']}`，`geometry_confidence` 從
`{tunnel_gate['before_geometry']}` → `{tunnel_gate['after_geometry']}`
（{"未比原本更自信，符合卡片驗收要求" if tunnel_gate['after_geometry'] != 'high' and tunnel_gate['before_geometry'] in ('medium', 'high') else "見驗收檢查"}）；
其餘 12 張三軸 confidence／gate **逐值不變**（表 2 已程式化核對）。

**逐面材質判定**：TunnelToHell 的 {n_changed_faces} 面判定變動（走透視路徑後，
四面牆改為共用單一判定值——這是單張透視照的既有架構限制，不是本卡引入的新行為）；
其餘 72 面**逐面不變**（表 3 已程式化核對）。

## 自我檢查程式化守門

本腳本執行時會對以下任一項不符直接 `sys.exit(1)`（🔴 卡關，不會靜默通過）：

- 除 TunnelToHell 外，任何一張三軸 confidence／gate 有變動
- 除 TunnelToHell 外，任何一面材質判定有變動
- `bedroom_ai_generated` 的 materials_confidence／overall confidence 從 low 變成非 low
  （臥室紅旗，共同鐵則 7）

本次執行**全部通過**，未觸發任何卡關。

## 快取策略（Fable 補充事項）

本腳本**每次執行都是全量重跑**：不讀取、不寫入任何跨次重用的快取——
`output/clip_accuracy/runs/`（T-36 凍結基線）與 `output/material_round/runs/`
（T-33 凍結基線）只被唯讀取用當「before」比較基準，`output/equirect_fix/runs/`
是本次「after」的全新輸出，下次重跑會整個覆蓋重寫，不做增量快取判斷。
理由：T-40（評測快取指紋）排在本卡之後，本卡時點的快取無從辨識新舊碼，
靜默沿用會讓再基線量到修正前的行為。
"""


def main() -> int:
    if not GROUND_TRUTH_PATH.exists():
        die(f"找不到 {GROUND_TRUTH_PATH}")

    print("=== 步驟 1：極點列統計量測 ===")
    pole_rows, true_max, false_min = measure_pole_stats()
    threshold = config.EQUIRECT_POLE_DIFF_THRESHOLD
    if not (true_max < threshold < false_min):
        die(
            f"門檻 {threshold} 沒有把真環景（max={true_max}）與 TunnelToHell"
            f"（max={false_min}）分開！"
        )
    print(f"  真環景 max={true_max}，TunnelToHell={false_min}，門檻={threshold}（餘裕足夠）")

    print("\n=== 步驟 2：13 張照片全量重跑（--force-low-confidence --no-furnishings） ===")
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    after_by_name = {}
    for item in GATE_ITEMS:
        photo = REPO_ROOT / item["photo"]
        after_by_name[item["name"]] = run_cli(photo, item["name"])

    print("\n=== 步驟 3：三軸 confidence／gate before/after 對照 ===")
    gate_rows, unexpected_gate_drift = build_gate_comparison(after_by_name)
    if unexpected_gate_drift:
        die(f"非預期的三軸 confidence／gate 漂移（TunnelToHell 以外）：{unexpected_gate_drift}")
    print("  ✅ 除 TunnelToHell 外，其餘 12 張三軸 confidence／gate 逐值不變")

    print("\n=== 步驟 4：逐面材質判定再基線（沿用 T-36 ground truth 與計分邏輯） ===")
    ground_truth = json.loads(GROUND_TRUTH_PATH.read_text(encoding="utf-8"))
    gt_photos = ground_truth["photos"]

    all_data_before = load_before_all_data()
    all_data_after = after_all_data_from_analysis(after_by_name)

    rows_before = build_accuracy_tables(GATE_ITEMS, all_data_before, gt_photos)["rows"]
    rows_after = build_accuracy_tables(GATE_ITEMS, all_data_after, gt_photos)["rows"]

    face_diffs, unexpected_face_drift = diff_face_rows(rows_before, rows_after)
    if unexpected_face_drift:
        die(f"非預期的逐面材質判定漂移（TunnelToHell 以外）：{unexpected_face_drift}")
    if not any(d["photo"] == "TunnelToHell" for d in face_diffs):
        die("TunnelToHell 應該至少有一面材質判定變動（走透視路徑後架構改變），但一面都沒變——不符合預期")
    print(f"  ✅ 除 TunnelToHell 外，其餘 72 面逐面不變；TunnelToHell 有 "
          f"{len([d for d in face_diffs if d['photo'] == 'TunnelToHell'])} 面變動")

    print("\n=== 步驟 5：寫出報表 ===")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "tables.md").write_text(
        write_tables_md(pole_rows, true_max, false_min, threshold, gate_rows, face_diffs),
        encoding="utf-8",
    )
    (OUT_DIR / "REPORT.md").write_text(
        write_report_md(pole_rows, true_max, false_min, threshold, gate_rows, face_diffs),
        encoding="utf-8",
    )
    print(f"完成。報告：{OUT_DIR / 'REPORT.md'}")
    print(f"表格：{OUT_DIR / 'tables.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
