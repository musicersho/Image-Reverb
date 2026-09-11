# T-43 步驟 4 REPORT — 13 張照片基線變化表（插卡 4/4；鐵則 8＋13）

## Provenance（改動前參照釘死為 OLD_COMMIT 常數＝T-49 v2 修正輪結果 commit）

- 改動前參照 `OLD_COMMIT`（模組常數）：`c64fba9`
- 改動前 worktree `git rev-parse HEAD`（全長，須等於上列 commit）：`c64fba9d304d2342ed88abd2cea64ddb8b4c6335`
- 改動後主 repo `git rev-parse HEAD`（全長）：`cdb4127d4253c9dbaa7db1b335d251a022df7f1e`
- 改動後主 repo `git status --porcelain -- src scripts data`：
（空，工作區乾淨）
- 產生時間（UTC）：`2026-09-11T08:11:41Z`

本報告由 `scripts/t43_provenance_baseline.py --fresh` 對 13 張照片各跑兩次真實 CLI（`python -m src.image_reverb <photo> --force-low-confidence --no-viz`，分別在本卡改動前的固定 commit `OLD_COMMIT`（`git worktree`）與改動後的工作目錄），程式化驗證：

1. **gate 判定條件零改動（鐵則 6）**：13 張的 geometry／materials／overall confidence與 gate 結果，改動前後**逐值相同**——任一不同即視為斷言失敗，不寫本報告。
2. **IR bytes 完全不變**：13 張的 `ir_mono.wav` md5，改動前後**逐位元相同**——`provenance` 只新增 `analysis.json` 欄位，不改任何聲學計算內容。
3. **新欄位確實落地（改動後）**：13 張改動後的 `analysis.json` 全數含 `provenance` 區塊。

13 張全數通過。完整表格見 [`tables.md`](tables.md)。

## 產物溯源說明

`run_photo()`（`src/image_reverb/pipeline.py`）成功路徑新增 `provenance` 區塊（`git_revision`＋dirty 標記、`input_sha256`、`materials_json_sha256`、`segmentation_model_id`／`clip_model_id`／`clip_confidence_threshold`（一律讀 `config`）、CLI 有效參數、生成時戳），單一事實來源在新模組 `src/image_reverb/provenance.py`。`scripts/t17_blind_test.py` 改為溯源驗證：來源 `analysis.json` 缺 `provenance`，或 git revision／照片 hash／模型設定與當前不符，一律 exit 非 0；`MANIFEST.json` 分開記錄 `source_provenance`（來源逐項複製）與 `packaging_git_revision`（打包當下 HEAD），不混用同一鍵名。

隔離 repo 的 v1→v2 舊碼必須 fail 重現見 `scripts/test_t17_provenance.py` 與交接筆記。
