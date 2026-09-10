#!/usr/bin/env python3
"""T-42 步驟 4（鐵則 8，程式產出）：13 張照片基線變化表＋輸出交易化政策落地說明。

本卡（插卡 3/4）只動 `run_photo()` 的輸出編排段（archive-first 隔離舊產物＋
staging 暫存＋成功才原子發布）；gate 判定條件（`overall_confidence == "low"`
與 force 分支的觸發／放行）、`compute_materials_confidence()`、`scene_cues`
段、門檻 0.4 全部零改動（鐵則 6）。本腳本用**真實 CLI**（`python -m
src.image_reverb <photo> --force-low-confidence --no-viz`，含真實幾何／分割／
CLIP 模型，不打樁）對 `t36_clip_accuracy.GATE_ITEMS` 13 張照片各跑一次，程式化
證明：

1. **三軸 confidence／gate 逐值不變**：拿「本卡改動前」（`git worktree` 於固定
   commit `OLD_COMMIT`）與「本卡改動後」（當前工作目錄）兩邊的真實 CLI 結果
   逐張比對，不透過 `EXPECTED_GATE` 間接比較（那張表是別卡的凍結基準，本卡只
   借用來核對兩邊都跟它一致，不是本卡比較的主要依據）。
2. **IR bytes 完全不變**：`ir_mono.wav` 的 md5 兩邊逐張比對——交易化只改
   「寫到哪、何時發布」，不改內容。
3. **輸出交易政策確實落地**：改動後的每一張照片跑完，`output/preprocess/
   <stem>/` 與 `output/<stem>/` 都存在（成功發布到正式位置）、
   `output/.staging/<stem>/` 都不存在（發布後不留殘骸）。

跑法：`python scripts/t42_transactional_baseline.py --out-dir
output/transactional_output/ --fresh`（13 張 ×2 邊＝26 次真實 CLI，
單張約 15–40 秒）。任一斷言不成立 exit 非 0，且不寫 REPORT／tables。

T-49（裁決 T-42-A 執行卡 1/2，附帶發現①；鐵則 13 首例）：「改動前」參照改成
釘死的 commit 常數 `OLD_COMMIT`，不再用 `git worktree add --detach <dir> HEAD`
——收工 commit 之後 HEAD 就是新碼，若仍用 HEAD，改動後再重跑會變成「新碼比
新碼」的假綠燈，還會把 REPORT 的「改動前參照」覆寫成錯的 commit。`OLD_COMMIT`
只能是模組常數，不開 CLI 參數讓人指定（鐵則 13：參照只能是常數，不能讓人在
跑的時候換）；worktree 建好後會自檢 `git rev-parse HEAD` 是否等於 `OLD_COMMIT`
的全長雜湊，不等就 `SystemExit("🔴 卡關 …")`。REPORT 檔頭改由程式印出雙邊
`git rev-parse HEAD`（改動前 worktree／改動後主 repo）與主 repo
`git status --porcelain -- src scripts`（T-40 指紋精神）。
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

DEFAULT_OUT_DIR = REPO_ROOT / "output" / "transactional_output"
# T-49（裁決 T-42-A 附帶發現①；鐵則 13 首例）：本卡「改動前」的參照點釘死為
# 固定 commit（T-42 已驗證 REPORT 記錄的 `ec1a7bfd62e1810f52be5d2d6921b9d8a
# 63422f4` ＝ T-42 結果 commit `cf1f1ba` 的 parent），不用 HEAD——HEAD 會隨
# 每次收工 commit 變動，不是穩定參照，再跑會變成「新碼比新碼」的假綠燈。
OLD_COMMIT = "ec1a7bf"
OLD_WORKTREE_DIR = REPO_ROOT / f".worktree_t42_old_{OLD_COMMIT}"


def _git_head(cwd: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=cwd, capture_output=True, text=True, check=True
    ).stdout.strip()


def gate_of(analysis: dict) -> str:
    return "BLOCK" if analysis["confidence"] == "low" else "pass"


def run_cli_side(photo: Path, name: str, cwd: Path) -> dict:
    """在給定 cwd（主 repo 或 worktree）跑一次真實 CLI，回傳
    `{geometry, materials, overall, gate, ir_mono_md5, published_ok,
    staging_leftover}`。`published_ok`／`staging_leftover` 只在 cwd=主 repo
    （本卡改動後）才有意義；worktree 端（改動前）沒有 staging 機制，回傳
    `None`。"""
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

    is_new_code = cwd == REPO_ROOT
    published_ok = None
    staging_leftover = None
    if is_new_code:
        preprocess_dir = cwd / "output" / "preprocess" / stem
        staging_dir = cwd / "output" / ".staging" / stem
        published_ok = out_dir.exists() and preprocess_dir.exists()
        staging_leftover = staging_dir.exists()

    return {
        "geometry": analysis["geometry_confidence"],
        "materials": analysis["materials_confidence"],
        "overall": analysis["confidence"],
        "gate": gate_of(analysis),
        "ir_mono_md5": ir_mono_md5,
        "published_ok": published_ok,
        "staging_leftover": staging_leftover,
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
            print("  （舊碼／HEAD）")
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
                    "（交易化只改寫檔位置與時機，不改內容）"
                )
            if not new["published_ok"]:
                mismatches.append(f"{name}：改動後 output/preprocess/<stem>/ 與 output/<stem>/ 未同時成功發布")
            if new["staging_leftover"]:
                mismatches.append(f"{name}：改動後 output/.staging/<stem>/ 發布後仍殘留")

            expected_geo, expected_mat = t36.EXPECTED_GATE[name]
            rows.append(
                {
                    "name": name,
                    "geometry": new["geometry"],
                    "materials": new["materials"],
                    "overall": new["overall"],
                    "gate": new["gate"],
                    "ir_md5_match": old["ir_mono_md5"] == new["ir_mono_md5"],
                    "match_expected_gate": (new["geometry"] == expected_geo and new["materials"] == expected_mat),
                }
            )
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
         "與改動前 gate/confidence 相符", "IR md5 改動前後相符", "與 EXPECTED_GATE 相符"],
        [
            [r["name"], r["geometry"], r["materials"], r["overall"], r["gate"],
             "✅", "✅" if r["ir_md5_match"] else "🔴",
             "✅" if r["match_expected_gate"] else "🔴"]
            for r in rows
        ],
    )
    (out_dir / "tables.md").write_text(
        "## 表 1：13 張照片基線變化（T-42 輸出交易化前後比對）\n\n" + table + "\n",
        encoding="utf-8",
    )

    porcelain = subprocess.run(
        ["git", "status", "--porcelain", "--", "src", "scripts"],
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
        "# T-42 步驟 4 REPORT — 13 張照片基線變化表（插卡 3/4；鐵則 8）\n\n"
        "## Provenance（T-49：改動前參照釘死為 OLD_COMMIT 常數，非 HEAD）\n\n"
        f"- 改動前參照 `OLD_COMMIT`（模組常數）：`{OLD_COMMIT}`\n"
        f"- 改動前 worktree `git rev-parse HEAD`（全長，須等於上列 commit）：`{old_head}`\n"
        f"- 改動後主 repo `git rev-parse HEAD`（全長）：`{new_head_after}`\n"
        f"- 改動後主 repo `git status --porcelain -- src scripts`：\n{porcelain_block}"
        f"- 產生時間（UTC）：`{generated_at}`\n\n"
        "本報告由 `scripts/t42_transactional_baseline.py --fresh` 對 13 張照片各跑兩次真實 CLI"
        "（`python -m src.image_reverb <photo> --force-low-confidence --no-viz`，"
        "分別在本卡改動前的固定 commit `OLD_COMMIT`（`git worktree`）與改動後的工作目錄），"
        "程式化驗證：\n\n"
        "1. **gate 判定條件零改動（鐵則 6）**：13 張的 geometry／materials／overall confidence"
        "與 gate 結果，改動前後**逐值相同**——任一不同即視為斷言失敗，不寫本報告。\n"
        "2. **IR bytes 完全不變**：13 張的 `ir_mono.wav` md5，改動前後**逐位元相同**"
        "——輸出交易化（archive-first／staging／成功才原子發布）只改「寫到哪、何時發布」，"
        "不改任何聲學計算內容。\n"
        "3. **交易政策確實落地（改動後）**：13 張全數 `output/preprocess/<stem>/` 與 "
        "`output/<stem>/` 同時成功發布到正式位置，`output/.staging/<stem>/` 發布後不殘留。\n\n"
        f"13 張全數通過。完整表格見 [`tables.md`](tables.md)。\n\n"
        "## 政策落地說明\n\n"
        "`run_photo()`（`src/image_reverb/pipeline.py`）新增：\n\n"
        "- **archive-first（可回復）**：輸入驗證通過、真正開始 preprocess 之前，"
        "把既有 `output/preprocess/<stem>/` 與 `output/<stem>/`（若存在）**移動**（不刪除）到 "
        "`output/.archive/<stem>/<時間戳>/`；輸入驗證失敗的早退（exit 2）不隔離舊檔。\n"
        "- **staging**：本次所有產物（preprocess 產物＋IR／analysis／viz／wet preview）"
        "一律先寫 `output/.staging/<stem>/`（分 `preprocess/`／`final/` 兩子樹）；"
        "啟動時若偵測到上次中止殘留的 staging 會先清掉並印 note。\n"
        "- **成功才發布**：合成與寫檔全部在 staging 完成後，才把兩個子樹原子 rename 到正式位置；"
        "`analysis.json`／`meta.json` 內的路徑字串一律寫正式位置（生成期間讀寫仍用 staging 路徑）。\n"
        "- **gate 擋下／例外中止**：刪 staging；正式位置保持乾淨不存在（舊檔已在 archive）；"
        "gate 訊息文案改為真話（不再宣稱「不會寫出任何 WAV／JSON」，改成「本次暫存產物已清除」，"
        "並在有舊輸出時附上 archive 位置與回復方式）；exit code 語義不變（2／3／0）。\n\n"
        "`test_output_gate.py` 新增三案例（【G】【H】【I】）對舊碼（改動前）實測 fail，"
        "詳見 TASKS.md T-42 卡「交接筆記」。\n"
    )
    (out_dir / "REPORT.md").write_text(report, encoding="utf-8")

    print(f"\n✅ 13 張照片改動前後 gate/confidence／IR md5 全數相符，REPORT 已寫入 {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
