# T-47 REPORT — gate 校準複審量測（裁決 T-45-A 執行卡 2/5）
## 硬（欄位）

| 硬（欄位） | 值 |
|---|---|
| 跑法 | `--fresh`（零快取，全新目錄） |
| out_dir | output/gate_calibration |
| 照片張數（`t36.GATE_ITEMS`） | 13 |
## Provenance（只記錄、不比對）

| provenance（只記錄，不比對） | 值 |
|---|---|
| 主 repo HEAD（產生本報告時） | `808a6ff510e101446bc8e42baff3a70e6218fdb3` |
| git status --porcelain -- src scripts data | 見下方 |
| 產生時間（UTC） | 2026-09-11T09:37:19.291255+00:00 |
| 環境 | macOS-15.7.7-arm64-arm-64bit；python 3.9.6；torch 2.8.0 |
| code_fingerprint.repo_head（跑 CLI 當下） | `808a6ff510e101446bc8e42baff3a70e6218fdb3` |

`git status --porcelain -- src scripts data`：
```
?? scripts/t47_gate_calibration.py

```

⚠️ 執行者本次跑的當下工作區有未 commit 變更，不因此視為斷言失敗；Opus 複驗那次應為空（同 T-42／T-43／T-49 既有慣例）。

本報告由 `scripts/t47_gate_calibration.py` 對 13 張照片各跑一次真實 CLI（`python -m src.image_reverb <photo> --force-low-confidence --no-viz`，預設模式與加 `--role-aware` 各一次）＋一次逐面判定明細 harness（唯讀重用 `t36_clip_accuracy.py`／`t44_role_eval.py`／`eval_cache.py`），兩條資料來源的 `surfaces`／`surfaces_sources` 已程式化核對逐位元相符。詳表見 [tables.md](tables.md)。

## 四樣證據摘要

① **新基準率**：見 tables.md 表 1（13 張×2 模式的三軸 confidence＋gate）。

② **被放行案例清單**：`default` 模式 0 面來自 pass 案例、`role_aware` 模式 6 面來自 pass 案例，逐面 vs ground truth 見 tables.md 表 2。

③ **T-17 已知錯誤（鐵則 12）輸出佔比**：5 張已知錯誤案例中，`default` 模式 0/5 張為 pass、`role_aware` 模式 1/5 張為 pass（見 tables.md 表 3）；pass 案例裡的 in-set 誤判面數／pass 案例總評分面數：`default` 0/0、`role_aware` 1/6。

④ **臥室續擋**：`bedroom_ai_generated` 在 `default`／`role_aware` 兩模式 gate 皆為 `BLOCK`／`BLOCK`（見 tables.md 表 4，含 floor 面 top-1 機率與 0.4 門檻的距離）。

## 延伸量測（卡片明列）

⑤ 每面 top-1 機率兩模式位移、與 0.4 門檻的距離、<0.05 清單按角色分——見 tables.md 表 5，含 T-44 第四輪記錄的 9 面信心上升交叉檢查（程式化核對，9/9 通過）。

⑥ 門檻敏感度（表 7' 型）按角色、按模式各一張——見 tables.md 表 6。

⑦ 兩種唯讀模擬（只算不採用，`compute_materials_confidence()`／gate 判定段／門檻 0.4 零改動）：
  (a) 門檻依候選數 n 調整（等效全域 16 候選 softmax 的機率門檻）對 gate 的影響——見 tables.md 表 7；
  (b) `compute_materials_confidence()` 規則 4 加「候選集收窄的 clip 面不得直接 medium」對 gate 的影響——見 tables.md 表 8。

## ⚠️ 本卡不下結論（範圍紅線）

本卡只產出四樣證據與兩項延伸量測供 Fable 下裁決 T-47-A，**不對「該不該調整門檻／候選集分區表」下任何建議或結論**；⑦ 的兩個模擬公式僅供參考，未經採用，`src/` 全程零改動。
