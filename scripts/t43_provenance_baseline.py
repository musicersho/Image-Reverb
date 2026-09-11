#!/usr/bin/env python3
"""T-43 步驟 4（鐵則 8＋13，程式產出）：13 張照片基線變化表——驗證新增
`provenance` 生成指紋欄位不影響三軸 confidence／gate 判定與 IR bytes。

本卡（插卡 4/4）只加：(1) `run_photo()` 的 analysis payload 新增 `provenance`
區塊（純新增欄位，不進任何判定分支）；(2) 新模組
`src/image_reverb/provenance.py`（git revision／sha256 共用 helper）；
(3) `scripts/t17_blind_test.py` 改為溯源驗證。三者都不動 gate 判定條件
（`overall_confidence == "low"` 與 force 分支）、不動
`compute_materials_confidence()`／`scene_cues`／門檻 0.4、不動任何聲學計算
（`geometry.py`／`acoustics.py`／`ir_synth.py`／`ir_metrics.py`）。本腳本用
**真實 CLI**（`python -m src.image_reverb <photo> --force-low-confidence
--no-viz`，含真實幾何／分割／CLIP 模型，不打樁）對
`t36_clip_accuracy.GATE_ITEMS` 13 張照片各跑一次，程式化證明：

1. **三軸 confidence／gate 逐值不變**：拿「本卡改動前」（`git worktree` 於固定
   commit `OLD_COMMIT`＝T-49 v2 修正輪結果 commit，Opus 複驗通過）與「本卡改動
   後」（當前工作目錄）兩邊的真實 CLI 結果逐張比對。
2. **IR bytes 完全不變**：`ir_mono.wav` 的 md5 兩邊逐張比對——`provenance` 只寫
   `analysis.json`，不碰 WAV 內容。
3. **新欄位確實落地（改動後）**：13 張改動後的 `analysis.json` 都含
   `provenance` 區塊（佐證新程式碼路徑確實生效，不是本卡驗收主軸）。

跑法：`python scripts/t43_provenance_baseline.py --out-dir output/provenance/
--fresh`（13 張 ×2 邊＝26 次真實 CLI，單張約 15–40 秒）。任一斷言不成立
exit 非 0，且不寫 REPORT／tables。

鐵則 13：「改動前」參照是模組常數 `OLD_COMMIT`，不用 `HEAD`、不開 CLI 參數讓
人指定；worktree 建好後自檢 `git rev-parse HEAD` 是否等於 `OLD_COMMIT` 的全長
雜湊，不等就 `SystemExit`。REPORT 檔頭印雙邊 `git rev-parse HEAD`（改動前
worktree／改動後主 repo）與主 repo `git status --porcelain -- src scripts
data`（裁決 T-49-A：範圍含 `data`）。
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import t36_clip_accuracy as t36  # noqa: E402  （唯讀引用：GATE_ITEMS／EXPECTED_GATE）
from t36_analysis import _md_table  # noqa: E402  （唯讀引用，不重新實作表格排版）

DEFAULT_OUT_DIR = REPO_ROOT / "output" / "provenance"
# 鐵則 13（裁決 T-42-A，2026-09-10）：「改動前」參照釘死為 T-49 v2 修正輪的結果
# commit（Opus 複驗通過，HANDOFF 2026-09-11），不用 HEAD——HEAD 會隨每次收工
# commit 變動，不是穩定參照，再跑會變成「新碼比新碼」的假綠燈。
OLD_COMMIT = "c64fba9"
OLD_WORKTREE_DIR = REPO_ROOT / f".worktree_t43_old_{OLD_COMMIT}"


def _git_head(cwd: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=cwd, capture_output=True, text=True, check=True
    ).stdout.strip()


def gate_of(analysis: dict) -> str:
    return "BLOCK" if analysis["confidence"] == "low" else "pass"


def run_cli_side(photo: Path, name: str, cwd: Path) -> dict:
    """在給定 cwd（主 repo 或 worktree）跑一次真實 CLI，回傳
    `{geometry, materials, overall, gate, ir_mono_md5, has_provenance}`。
    `has_provenance` 只在 cwd=主 repo（本卡改動後）才有意義；worktree 端
    （改動前，T-43 之前的碼）預期為 False。"""
    stem = photo.stem
    out_dir = cwd / "output" / stem
    if out_dir.exists():
        shutil.rmtree(out_dir)

    cmd = [sys.executable, "-m", "src.image_reverb", str(photo), "--force-low-confidence", "--no-viz"]
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0 or not out_dir.exists():
        raise RuntimeError(
            f"{name}（cwd={cwd}）失敗：exit={proc.returncode}\n"
            f"--- stdout（末 30 行）---\n" + "\n".join(proc.stdout.splitlines()[-30:]) + "\n"
            f"--- stderr（末 30 行）---\n" + "\n".join(proc.stderr.splitlines()[-30:])
        )

    analysis = json.loads((out_dir / "analysis.json").read_text(encoding="utf-8"))
    ir_mono_md5 = hashlib.md5((out_dir / "ir_mono.wav").read_bytes()).hexdigest()

    return {
        "geometry": analysis["geometry_confidence"],
        "materials": analysis["materials_confidence"],
        "overall": analysis["confidence"],
        "gate": gate_of(analysis),
        "ir_mono_md5": ir_mono_md5,
        "has_provenance": bool(analysis.get("provenance")),
    }


def main() -> int:
    fresh = "--fresh" in sys.argv[1:]
    out_dir = DEFAULT_OUT_DIR
    if "--out-dir" in sys.argv[1:]:
        idx = sys.argv.index("--out-dir")
        out_dir = REPO_ROOT / Path(sys.argv[idx + 1])
    if not fresh:
        raise SystemExit("🔴 送審一律加 --fresh（本卡沒有快取機制，避免誤用舊產物）。")

    if OLD_WORKTREE_DIR.exists():
        subprocess.run(["git", "worktree", "remove", "--force", str(OLD_WORKTREE_DIR)], cwd=REPO_ROOT, check=False)
        shutil.rmtree(OLD_WORKTREE_DIR, ignore_errors=True)

    print(f"[worktree] git worktree add {OLD_WORKTREE_DIR.name} {OLD_COMMIT}（改動前參照，釘死常數）")
    subprocess.run(
        ["git", "worktree", "add", "--detach", str(OLD_WORKTREE_DIR), OLD_COMMIT],
        cwd=REPO_ROOT, check=True, capture_output=True, text=True,
    )

    old_head = _git_head(OLD_WORKTREE_DIR)
    expected_old_head = subprocess.run(
        ["git", "rev-parse", OLD_COMMIT], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    if old_head != expected_old_head:
        subprocess.run(["git", "worktree", "remove", "--force", str(OLD_WORKTREE_DIR)], cwd=REPO_ROOT, check=False)
        shutil.rmtree(OLD_WORKTREE_DIR, ignore_errors=True)
        raise SystemExit(
            f"🔴 卡關：worktree HEAD（{old_head}）≠ OLD_COMMIT（{OLD_COMMIT}）全長雜湊"
            f"（{expected_old_head}）——改動前參照重建失敗，不可繼續。"
        )
    print(f"[worktree] 舊碼 HEAD（改動前，OLD_COMMIT={OLD_COMMIT}）＝{old_head}")

    rows: list[dict] = []
    mismatches: list[str] = []
    try:
        for item in t36.GATE_ITEMS:
            name = item["name"]
            photo = REPO_ROOT / item["photo"]
            print(f"[{name}]")
            print(f"  （舊碼／OLD_COMMIT={OLD_COMMIT}）")
            old = run_cli_side(photo, name, OLD_WORKTREE_DIR)
            print("  （新碼／本卡改動後）")
            new = run_cli_side(photo, name, REPO_ROOT)

            for axis in ("geometry", "materials", "overall", "gate"):
                if old[axis] != new[axis]:
                    mismatches.append(
                        f"{name}：{axis} 改動前={old[axis]} != 改動後={new[axis]}（gate 判定不許變，鐵則 6）"
                    )
            if old["ir_mono_md5"] != new["ir_mono_md5"]:
                mismatches.append(
                    f"{name}：ir_mono.wav md5 改動前={old['ir_mono_md5']} != 改動後={new['ir_mono_md5']}"
                    "（provenance 只加欄位，不改任何聲學計算內容）"
                )
            if not new["has_provenance"]:
                mismatches.append(f"{name}：改動後 analysis.json 缺少 provenance 區塊")

            expected_geo, expected_mat = t36.EXPECTED_GATE[name]
            rows.append({
                "name": name,
                "geometry": new["geometry"],
                "materials": new["materials"],
                "overall": new["overall"],
                "gate": new["gate"],
                "ir_md5_match": old["ir_mono_md5"] == new["ir_mono_md5"],
                "has_provenance": new["has_provenance"],
                "match_expected_gate": (new["geometry"] == expected_geo and new["materials"] == expected_mat),
            })
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(OLD_WORKTREE_DIR)], cwd=REPO_ROOT, check=False)
        shutil.rmtree(OLD_WORKTREE_DIR, ignore_errors=True)

    if mismatches:
        print(f"\n❌ {len(mismatches)} 項斷言不成立，不寫 REPORT／tables：")
        for m in mismatches:
            print(f"  🔴 {m}")
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    table = _md_table(
        ["照片", "geometry", "materials", "overall", "gate",
         "IR md5 改動前後相符", "改動後含 provenance", "與 EXPECTED_GATE 相符"],
        [
            [r["name"], r["geometry"], r["materials"], r["overall"], r["gate"],
             "✅" if r["ir_md5_match"] else "🔴",
             "✅" if r["has_provenance"] else "🔴",
             "✅" if r["match_expected_gate"] else "🔴"]
            for r in rows
        ],
    )
    (out_dir / "tables.md").write_text(
        "## 表 1：13 張照片基線變化（T-43 產物溯源前後比對）\n\n" + table + "\n",
        encoding="utf-8",
    )

    porcelain = subprocess.run(
        ["git", "status", "--porcelain", "--", "src", "scripts", "data"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout
    new_head_after = _git_head(REPO_ROOT)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if porcelain.strip():
        porcelain_block = (
            "```\n" + porcelain + "```\n"
            "⚠️ 改動後為未 commit 工作區（執行者本次跑的當下工作區有未 commit 變更，"
            "不因此視為斷言失敗；Opus 複驗那次應為空）。\n"
        )
    else:
        porcelain_block = "（空，工作區乾淨）\n"

    report = (
        "# T-43 步驟 4 REPORT — 13 張照片基線變化表（插卡 4/4；鐵則 8＋13）\n\n"
        "## Provenance（改動前參照釘死為 OLD_COMMIT 常數＝T-49 v2 修正輪結果 commit）\n\n"
        f"- 改動前參照 `OLD_COMMIT`（模組常數）：`{OLD_COMMIT}`\n"
        f"- 改動前 worktree `git rev-parse HEAD`（全長，須等於上列 commit）：`{old_head}`\n"
        f"- 改動後主 repo `git rev-parse HEAD`（全長）：`{new_head_after}`\n"
        f"- 改動後主 repo `git status --porcelain -- src scripts data`：\n{porcelain_block}"
        f"- 產生時間（UTC）：`{generated_at}`\n\n"
        "本報告由 `scripts/t43_provenance_baseline.py --fresh` 對 13 張照片各跑兩次真實 CLI"
        "（`python -m src.image_reverb <photo> --force-low-confidence --no-viz`，"
        "分別在本卡改動前的固定 commit `OLD_COMMIT`（`git worktree`）與改動後的工作目錄），"
        "程式化驗證：\n\n"
        "1. **gate 判定條件零改動（鐵則 6）**：13 張的 geometry／materials／overall confidence"
        "與 gate 結果，改動前後**逐值相同**——任一不同即視為斷言失敗，不寫本報告。\n"
        "2. **IR bytes 完全不變**：13 張的 `ir_mono.wav` md5，改動前後**逐位元相同**"
        "——`provenance` 只新增 `analysis.json` 欄位，不改任何聲學計算內容。\n"
        "3. **新欄位確實落地（改動後）**：13 張改動後的 `analysis.json` 全數含 `provenance` 區塊。\n\n"
        f"13 張全數通過。完整表格見 [`tables.md`](tables.md)。\n\n"
        "## 產物溯源說明\n\n"
        "`run_photo()`（`src/image_reverb/pipeline.py`）成功路徑新增 `provenance` 區塊"
        "（`git_revision`＋dirty 標記、`input_sha256`、`materials_json_sha256`、"
        "`segmentation_model_id`／`clip_model_id`／`clip_confidence_threshold`（一律讀 "
        "`config`）、CLI 有效參數、生成時戳），單一事實來源在新模組 "
        "`src/image_reverb/provenance.py`。`scripts/t17_blind_test.py` 改為溯源驗證："
        "來源 `analysis.json` 缺 `provenance`，或 git revision／照片 hash／模型設定與"
        "當前不符，一律 exit 非 0；`MANIFEST.json` 分開記錄 `source_provenance`"
        "（來源逐項複製）與 `packaging_git_revision`（打包當下 HEAD），不混用同一鍵名。\n\n"
        "隔離 repo 的 v1→v2 舊碼必須 fail 重現見 `scripts/test_t17_provenance.py` 與"
        "交接筆記。\n"
    )
    (out_dir / "REPORT.md").write_text(report, encoding="utf-8")

    print(f"\n✅ 13 張照片改動前後 gate/confidence／IR md5 全數相符，REPORT 已寫入 {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
