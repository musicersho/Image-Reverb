#!/usr/bin/env python3
"""T-41：SegFormer 重複載入去重後的基線變化表（共同鐵則 8；純去重，零容忍漂移）。

跑法：`python scripts/t41_rebaseline.py`（每次執行都是**全量重跑**13 張，不做任何
跨次快取——本卡是純去重，任何一格數值都不許動，快取命中與否不影響驗收結論，
乾脆全量重跑最單純）。

**「before」是唯讀的既有基線，本腳本只讀不寫**：
  - 三軸 confidence／gate／六面材質／`dims_m`／`volume_m3`：
    `output/equirect_fix/runs/<name>/analysis.json`（T-37 用
    `--force-low-confidence --no-furnishings --no-viz` 建立的最新基線，本卡是
    T-37 之後第一張動 `src/` 的卡，方法論必須完全相同才能逐值比較）。

**「after」由本腳本產生**（全新目錄，不覆蓋任何既有基線——共同鐵則 4）：
  - 同方法論 CLI 全量重跑 13 張，輸出搬到 `output/pipeline_dedup/runs/<name>/`。

**scene_cues 四鍵零漂移是「analysis.json 不落盤 scene_cues」這件事的直證**
（陷阱 1）：analysis.json 從來沒有記錄過 scene_cues，所以沒辦法只比對 JSON
就證明它没變。本腳本改為對 13 張裡目前判定為透視照的每一張，直接呼叫
`surfaces_from_preprocess()`（新路）與 `segment_roles(..., *_load_segmenter())`
（舊路，pipeline.py 修正前的做法）各算一次 ratios，重用
`test_pipeline_dedup._build_scene_cues()` 的公式各組一份 scene_cues 逐鍵比對
——與 `scripts/test_pipeline_dedup.py` part B 是同一套邏輯，這裡只是把它跑成
報表的一部分。

驗收邏輯（本卡自我檢查的程式化版本，共同鐵則 8：本卡零容忍，沒有「預期內漂移」）：
  - 13 張三軸 confidence／gate／六面材質／`dims_m`／`volume_m3` **逐值不變**，
    任何一格漂移 → 🔴 卡關（`sys.exit(1)`）
  - scene_cues 四鍵（9 張透視照）**逐值 bit-identical**，任何一鍵不同 → 🔴 卡關
  - **臥室紅旗**（共同鐵則 7）：`bedroom_ai_generated` 的 materials_confidence／
    overall confidence 若從擋（low）變放 → 🔴 卡關

輸出：`output/pipeline_dedup/REPORT.md`、`output/pipeline_dedup/tables.md`
（含耗時對照——地雷 #15：不手打數字，直接讀 `analysis.json` 的 `elapsed_s`）。
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from src.image_reverb.preprocess import preprocess_image  # noqa: E402
from src.image_reverb.surfaces import (  # noqa: E402
    _load_segmenter,
    segment_roles,
    surfaces_from_preprocess,
)

from t36_clip_accuracy import GATE_ITEMS  # noqa: E402  （唯讀引用，13 張清單）
from test_pipeline_dedup import _build_scene_cues  # noqa: E402  （唯讀引用，公式單一事實來源）

OUT_DIR = REPO_ROOT / "output" / "pipeline_dedup"
RUNS_DIR = OUT_DIR / "runs"
SCENE_CUES_PREPROCESS_DIR = OUT_DIR / "_scene_cues_preprocess"
BEFORE_RUNS = REPO_ROOT / "output" / "equirect_fix" / "runs"

# 13 張逐值比對的欄位（zero-tolerance）
COMPARE_KEYS = [
    "dims_source", "geometry_confidence", "materials_confidence", "confidence",
    "dims_m", "volume_m3", "surfaces", "surfaces_sources",
]


def die(msg: str) -> None:
    print(f"🔴 卡關：{msg}", file=sys.stderr)
    sys.exit(1)


# ------------------------------------------------------------------
# 「after」：CLI 全量重跑 13 張（與 output/equirect_fix 相同方法論）
# ------------------------------------------------------------------

def run_cli(photo: Path, name: str) -> tuple[dict, str]:
    dst = RUNS_DIR / name
    cmd = [sys.executable, "-m", "src.image_reverb", str(photo),
           "--force-low-confidence", "--no-furnishings", "--no-viz"]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=600)

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
    print(f"  ✅ {name}（elapsed_s={aj.get('elapsed_s')}）")
    return aj, " ".join(cmd)


# ------------------------------------------------------------------
# 表 1：13 張三軸 confidence／gate／六面材質／dims_m／volume_m3 逐值比對
# ------------------------------------------------------------------

def build_comparison(after_by_name: dict) -> tuple[list[dict], list[str]]:
    rows = []
    drifted: list[str] = []
    for item in GATE_ITEMS:
        name = item["name"]
        before_path = BEFORE_RUNS / name / "analysis.json"
        if not before_path.exists():
            die(f"找不到 T-37 基線 {before_path}")
        before = json.loads(before_path.read_text(encoding="utf-8"))
        after = after_by_name[name]

        row = {"name": name}
        changed_keys = []
        for key in COMPARE_KEYS:
            b, a = before.get(key), after.get(key)
            row[f"before_{key}"] = b
            row[f"after_{key}"] = a
            if b != a:
                changed_keys.append(key)
        row["changed_keys"] = changed_keys
        rows.append(row)

        if changed_keys:
            drifted.append(f"{name}（{', '.join(changed_keys)}）")

        if name == "bedroom_ai_generated":
            before_blocked = before["materials_confidence"] == "low" or before["confidence"] == "low"
            after_blocked = after["materials_confidence"] == "low" or after["confidence"] == "low"
            if before_blocked and not after_blocked:
                die(
                    "臥室紅旗（共同鐵則 7）：bedroom_ai_generated 從擋變放！"
                    f"before materials={before['materials_confidence']} overall={before['confidence']}；"
                    f"after materials={after['materials_confidence']} overall={after['confidence']}"
                )
    return rows, drifted


# ------------------------------------------------------------------
# 表 2：scene_cues 四鍵新舊路 bit-identical（陷阱 1 直證，9 張透視照）
# ------------------------------------------------------------------

def build_scene_cues_table() -> tuple[list[dict], list[str]]:
    seg = _load_segmenter()  # 舊路共用同一個已載入模型（重複載入不影響推論結果）
    rows = []
    mismatches: list[str] = []

    for item in GATE_ITEMS:
        name = item["name"]
        photo_path = REPO_ROOT / item["photo"]
        summary = preprocess_image(photo_path, output_dir=SCENE_CUES_PREPROCESS_DIR / name)
        if summary["is_equirect"]:
            continue  # 環景路徑本來就不算 scene_cues

        _surf, detail = surfaces_from_preprocess(summary)
        new_ratios = detail["class_ratios"]["single"]

        from PIL import Image

        img = Image.open(summary["cropped"]).convert("RGB")
        _, old_ratios = segment_roles(img, *seg)

        old_cues = _build_scene_cues(old_ratios, detail)
        new_cues = _build_scene_cues(new_ratios, detail)

        row = {"name": name}
        row_mismatch = []
        for key in ("floor_pixel_ratio", "person_pixel_ratio", "out_of_domain", "out_of_domain_label"):
            row[f"old_{key}"] = old_cues[key]
            row[f"new_{key}"] = new_cues[key]
            if old_cues[key] != new_cues[key]:
                row_mismatch.append(key)
        row["mismatch"] = row_mismatch
        rows.append(row)
        if row_mismatch:
            mismatches.append(f"{name}（{', '.join(row_mismatch)}）")

    shutil.rmtree(SCENE_CUES_PREPROCESS_DIR, ignore_errors=True)
    return rows, mismatches


# ------------------------------------------------------------------
# 報表輸出
# ------------------------------------------------------------------

def _fmt_pair(before, after) -> str:
    return "同" if before == after else f"{before}→{after}"


def write_tables_md(compare_rows, scene_cues_rows, timing_rows, cli_cmd) -> str:
    lines = ["# T-41 基線變化表（程式產出，地雷 #15）\n"]

    lines.append("## 表 1：13 張三軸 confidence／gate／六面材質／dims_m／volume_m3 before/after\n")
    lines.append("| 照片 | dims_source | geometry | materials | overall | dims_m/volume_m3 | surfaces/sources | 變動？ |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for r in compare_rows:
        mark = f"⚠️ {', '.join(r['changed_keys'])}" if r["changed_keys"] else "—"

        def same(k, r=r):
            return _fmt_pair(r[f"before_{k}"], r[f"after_{k}"])

        lines.append(
            f"| {r['name']} | {same('dims_source')} | {same('geometry_confidence')} | "
            f"{same('materials_confidence')} | {same('confidence')} | "
            f"{same('dims_m')} / {same('volume_m3')} | "
            f"{same('surfaces')} / {same('surfaces_sources')} | {mark} |"
        )

    lines.append("\n## 表 2：scene_cues 四鍵新舊路 bit-identical（9 張透視照，陷阱 1 直證）\n")
    lines.append("| 照片 | floor_pixel_ratio | person_pixel_ratio | out_of_domain | out_of_domain_label | 不同？ |")
    lines.append("|---|---|---|---|---|---|")
    for r in scene_cues_rows:
        mark = f"⚠️ {', '.join(r['mismatch'])}" if r["mismatch"] else "—"
        lines.append(
            f"| {r['name']} | "
            f"{_fmt_pair(r['old_floor_pixel_ratio'], r['new_floor_pixel_ratio'])} | "
            f"{_fmt_pair(r['old_person_pixel_ratio'], r['new_person_pixel_ratio'])} | "
            f"{_fmt_pair(r['old_out_of_domain'], r['new_out_of_domain'])} | "
            f"{_fmt_pair(r['old_out_of_domain_label'], r['new_out_of_domain_label'])} | "
            f"{mark} |"
        )

    lines.append("\n## 表 3：單張耗時對照（`analysis.json` 的 `elapsed_s`，地雷 #15：非手打）\n")
    lines.append(f"重跑指令：`{cli_cmd}`（對每張照片的 `<photo>` 部分替換）\n")
    lines.append("| 照片 | 型態 | before elapsed_s | after elapsed_s | 差 |")
    lines.append("|---|---|---|---|---|")
    for r in timing_rows:
        diff = round(r["after"] - r["before"], 2)
        lines.append(f"| {r['name']} | {r['kind']} | {r['before']} | {r['after']} | {diff:+.2f}s |")

    return "\n".join(lines) + "\n"


def write_report_md(compare_rows, scene_cues_rows, timing_rows) -> str:
    n_perspective = len(scene_cues_rows)
    perspective_timing = [r for r in timing_rows if r["kind"] == "透視"]
    improved = sum(1 for r in perspective_timing if r["after"] <= r["before"])

    return f"""# T-41 透視照 SegFormer 重複載入去重報告

依 [TASKS.md](../../TASKS.md) T-41 卡（插卡 2/4）產出。數字全部由
[scripts/t41_rebaseline.py](../../scripts/t41_rebaseline.py) 產生，詳表見
[tables.md](tables.md)。

## 問題

`run_photo()` 對一張透視照會載入 SegFormer 兩次、完整推論兩次：
`surfaces_from_preprocess()` 已跑過一次 `_load_segmenter()`＋`segment_roles()`
並把結果存進 `detail["class_ratios"]["single"]`；`pipeline.py` 的 scene_cues 段
舊碼又對同一張 `cropped` 圖重新跑一次，只為取 `floor_pixel_ratio`／
`person_pixel_ratio`。`_load_segmenter()` 無 cache，第二次是完整
from_pretrained 載入＋完整推論，時間與記憶體峰值雙倍付費。

## 修法

scene_cues 段直接重用 `surfaces_from_preprocess()` 已經算好的
`detail["class_ratios"]["single"]`，刪掉第二次 `_load_segmenter()`／
`segment_roles()`。`floor_pixel_ratio`／`person_pixel_ratio`／`out_of_domain`／
`out_of_domain_label` 四鍵的計算式與鍵名一個字不改。

## 基線變化表（表 1，共同鐵則 8：本卡零容忍）

13 張三軸 confidence／gate／六面材質／`dims_m`／`volume_m3` **逐值不變**
（表 1 已程式化核對，任何一格漂移本腳本會直接卡關退出，不會靜默通過）。

## scene_cues 四鍵零漂移直證（表 2，陷阱 1）

`analysis.json` 從不記錄 scene_cues，單比對 JSON 證明不了數值沒變。本表對
{n_perspective} 張透視照各用新舊兩條路各算一次 scene_cues 並逐鍵比對，
**全部 bit-identical**（與 `scripts/test_pipeline_dedup.py` part B 同一套邏輯）。

## 耗時對照（表 3）

{n_perspective} 張透視照裡有 {improved}／{len(perspective_timing)} 張耗時持平或改善
（環景路徑本來就不受本卡影響，僅供參照，不計入改善統計）。卡片未設定量門檻，
只要求「只允許改善」——本表逐張列出 before/after `elapsed_s` 供人工核對。

## 自我檢查程式化守門

本腳本執行時對以下任一項不符會直接 `sys.exit(1)`（🔴 卡關，不會靜默通過）：

- 13 張裡任何一張三軸 confidence／gate／六面材質／`dims_m`／`volume_m3` 有變動
- 任一張透視照的 scene_cues 四鍵新舊路不一致
- `bedroom_ai_generated` 的 materials_confidence／overall confidence 從 low 變成非 low
  （臥室紅旗，共同鐵則 7）

本次執行**全部通過**，未觸發任何卡關。
"""


def main() -> int:
    print("=== 步驟 1：13 張照片全量重跑（--force-low-confidence --no-furnishings --no-viz） ===")
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    after_by_name = {}
    cli_cmd = ""
    for item in GATE_ITEMS:
        photo = REPO_ROOT / item["photo"]
        after_by_name[item["name"]], cli_cmd = run_cli(photo, item["name"])

    print("\n=== 步驟 2：13 張三軸 confidence／gate／六面材質／dims_m／volume_m3 比對 ===")
    compare_rows, drifted = build_comparison(after_by_name)
    if drifted:
        die(f"非預期漂移（本卡零容忍）：{drifted}")
    print("  ✅ 13 張逐值不變")

    print("\n=== 步驟 3：scene_cues 四鍵新舊路直證（9 張透視照） ===")
    scene_cues_rows, mismatches = build_scene_cues_table()
    if mismatches:
        die(f"scene_cues 新舊路不一致：{mismatches}")
    print(f"  ✅ {len(scene_cues_rows)} 張透視照 scene_cues 四鍵 bit-identical")

    print("\n=== 步驟 4：單張耗時對照 ===")
    timing_rows = []
    equirect_names = {r["name"] for r in scene_cues_rows}  # 有出現在表 2 的都是透視照
    for item in GATE_ITEMS:
        name = item["name"]
        before_path = BEFORE_RUNS / name / "analysis.json"
        before = json.loads(before_path.read_text(encoding="utf-8"))
        after = after_by_name[name]
        kind = "透視" if name in equirect_names else "環景"
        timing_rows.append({
            "name": name, "kind": kind,
            "before": before.get("elapsed_s"), "after": after.get("elapsed_s"),
        })
    print("  ✅ 已從 analysis.json 讀出 elapsed_s（非手打）")

    print("\n=== 步驟 5：寫出報表 ===")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "tables.md").write_text(
        write_tables_md(compare_rows, scene_cues_rows, timing_rows, cli_cmd), encoding="utf-8",
    )
    (OUT_DIR / "REPORT.md").write_text(
        write_report_md(compare_rows, scene_cues_rows, timing_rows), encoding="utf-8",
    )
    print(f"完成。報告：{OUT_DIR / 'REPORT.md'}")
    print(f"表格：{OUT_DIR / 'tables.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
