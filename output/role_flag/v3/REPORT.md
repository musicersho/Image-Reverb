# T-46 步驟 4 REPORT — 13 張照片基準率變化表（裁決 T-45-A 執行卡 1/5；criteria v3）

## 硬（比對用，§2.7 分層判定依據）

| 硬（欄位，§5.2／§2.7 比對用） | 值 |
|---|---|
| criteria_version | v3 |
| criteria_commit（本檔 commit，全長） | `580771684c4d8c03b67b994171e43d46b50e9fd1` |
| B0 commit（全長） | `23f2aba` → `23f2abada92aa9d46b1da0ac1ba2a7f1dc178872` |
| 跑法 | `--fresh`（含 B0 重建，零快取） |
| baseline_stable_sha256 | `68edb28d6c218e7a620d3c65950c1cbab787e83c00c011ff85c27afddf10bc7a` |

## Provenance（只記錄、不比對；不同重跑本來就會不同，不得據此判失敗、也不得據此判通過）

| provenance（欄位，只記錄不比對） | 值 |
|---|---|
| 主 repo HEAD（產生本報告時） | `0227d783a75212fa192dfca15e0613db2e8331e2` |
| 產生時間（UTC） | 2026-09-10T06:54:24.075253+00:00 |
| 環境 | macOS-15.7.7-arm64-arm-64bit；python 3.9.6；torch 2.8.0 |

本報告由 `scripts/t46_role_flag_baseline.py` 依 [`CRITERIA_T46_v3.md`](../CRITERIA_T46_v3.md) 對 13 張照片各跑一次真實 CLI（`python -m src.image_reverb <photo> --force-low-confidence --no-viz`，預設模式與加 `--role-aware` 各一次），並在 `git worktree` 重建基線 B0（commit `23f2aba`：role_aware 尚未預設啟用的最後狀態）之真實 CLI 結果，程式化驗證：

1. **預設模式（斷言 A1～A7）**：`role_aware==false`；geometry／materials／overall confidence、gate、六面材質＋來源逐張與基線 B0 **逐值相同**；`bathroom_tiled`、`bedroom_ai_generated` 與鐵則 12 五張已知錯誤案例均回到 **BLOCK**。
2. **`--role-aware` 模式（斷言 B1～B2）**：`role_aware==true`；六面材質＋來源與 T-44 最終輪 `round17`（曾經是 `pipeline.py` 硬編碼的預設行為）**逐值相同**——旗標路徑沒壞。geometry／overall confidence／gate 只報告不斷言（無可執行基線，交 T-47）。

13 張全數通過（13/13 三項比對皆相符：與 B0、與 round11、與 round17）。完整表格見 [`tables.md`](tables.md)、B0 的持久證據見 [`baseline_23f2aba/BASELINE.stable.md`](baseline_23f2aba/BASELINE.stable.md)（§5.2 硬比對物件）與 [`baseline_23f2aba/BASELINE.md`](baseline_23f2aba/BASELINE.md)（stable 段逐字＋provenance 段，provenance 段只記錄不比對）。

## ⚠️ 已知殘留風險（誠實揭露，本卡範圍外、不阻擋本卡結論；criteria v3 §2.5）

`EXPECTED_GATE`（T-28-A／T-36 凍結表）的 geometry 欄**不作為本卡斷言**——B0 於 commit `23f2aba` 實測 `TunnelToHell.geometry_confidence=low`，表列 `medium`，是表本身過期（T-37 equirect 修正後未更新），不是本卡回歸，交 T-47／裁決 T-47-A。另外用真實 CLI 兩模式並排跑 13 張後，觀察到 `role_aware` 會透過既有的 `scene_cues["out_of_domain"]` 機制間接影響 `geometry_confidence`（`site_photo_department_store`：某面在窄候選集下被判成「object_closeup」而觸發 `apply_scene_cue_confidence()` 降級，medium→low）——這個路徑在 T-44 round17 上線時就存在，只是這次用真實 CLI 兩模式並排比較才被看見。`gate 判定段／compute_materials_confidence()／scene_cues／門檻 0.4` 全部零改動（範圍紅線），此處只誠實記錄，不在本卡處理。完整清單見 [`tables.md`](tables.md) 表 3。
