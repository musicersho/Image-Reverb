# T-42 步驟 4 REPORT — 13 張照片基線變化表（插卡 3/4；鐵則 8）

## Provenance（T-49：改動前參照釘死為 OLD_COMMIT 常數，非 HEAD）

- 改動前參照 `OLD_COMMIT`（模組常數）：`ec1a7bf`
- 改動前 worktree `git rev-parse HEAD`（全長，須等於上列 commit）：`ec1a7bfd62e1810f52be5d2d6921b9d8a63422f4`
- 改動後主 repo `git rev-parse HEAD`（全長）：`4bff276ecc82c97129eeac9d1dc81aeef209febc`
- 改動後主 repo `git status --porcelain -- src scripts`：
```
 M scripts/t42_transactional_baseline.py
 M scripts/test_output_gate.py
 M src/image_reverb/pipeline.py
```
⚠️ 改動後為未 commit 工作區（執行者本次跑的當下工作區有未 commit 變更，不因此視為斷言失敗；Opus 複驗那次應為空）。
- 產生時間（UTC）：`2026-09-10T10:02:15Z`

本報告由 `scripts/t42_transactional_baseline.py --fresh` 對 13 張照片各跑兩次真實 CLI（`python -m src.image_reverb <photo> --force-low-confidence --no-viz`，分別在本卡改動前的固定 commit `OLD_COMMIT`（`git worktree`）與改動後的工作目錄），程式化驗證：

1. **gate 判定條件零改動（鐵則 6）**：13 張的 geometry／materials／overall confidence與 gate 結果，改動前後**逐值相同**——任一不同即視為斷言失敗，不寫本報告。
2. **IR bytes 完全不變**：13 張的 `ir_mono.wav` md5，改動前後**逐位元相同**——輸出交易化（archive-first／staging／成功才原子發布）只改「寫到哪、何時發布」，不改任何聲學計算內容。
3. **交易政策確實落地（改動後）**：13 張全數 `output/preprocess/<stem>/` 與 `output/<stem>/` 同時成功發布到正式位置，`output/.staging/<stem>/` 發布後不殘留。

13 張全數通過。完整表格見 [`tables.md`](tables.md)。

## 政策落地說明

`run_photo()`（`src/image_reverb/pipeline.py`）新增：

- **archive-first（可回復）**：輸入驗證通過、真正開始 preprocess 之前，把既有 `output/preprocess/<stem>/` 與 `output/<stem>/`（若存在）**移動**（不刪除）到 `output/.archive/<stem>/<時間戳>/`；輸入驗證失敗的早退（exit 2）不隔離舊檔。
- **staging**：本次所有產物（preprocess 產物＋IR／analysis／viz／wet preview）一律先寫 `output/.staging/<stem>/`（分 `preprocess/`／`final/` 兩子樹）；啟動時若偵測到上次中止殘留的 staging 會先清掉並印 note。
- **成功才發布**：合成與寫檔全部在 staging 完成後，才把兩個子樹原子 rename 到正式位置；`analysis.json`／`meta.json` 內的路徑字串一律寫正式位置（生成期間讀寫仍用 staging 路徑）。
- **gate 擋下／例外中止**：刪 staging；正式位置保持乾淨不存在（舊檔已在 archive）；gate 訊息文案改為真話（不再宣稱「不會寫出任何 WAV／JSON」，改成「本次暫存產物已清除」，並在有舊輸出時附上 archive 位置與回復方式）；exit code 語義不變（2／3／0）。

`test_output_gate.py` 新增三案例（【G】【H】【I】）對舊碼（改動前）實測 fail，詳見 TASKS.md T-42 卡「交接筆記」。
