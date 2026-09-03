# T-46 步驟 4 REPORT — 13 張照片基準率變化表（裁決 T-45-A 執行卡 1/5）

本報告由 `scripts/t46_role_flag_baseline.py` 對 13 張照片各跑一次真實 CLI（`python -m src.image_reverb <photo> --force-low-confidence --no-viz`，預設模式與加 `--role-aware` 各一次），程式化驗證：

1. **預設模式**：13 張照片的材質軸（六面材質＋來源）與 T-44 之前的最終基準 `round11_remap_baseline` **逐值相同**；`materials_confidence` 與 T-28-A／T-36 凍結表 `EXPECTED_GATE` 逐值相同；`bathroom_tiled`、`bedroom_ai_generated` 均回到 **BLOCK**。
2. **`--role-aware` 模式**：材質軸（六面材質＋來源）與 T-44 最終輪 `round17`（曾經是 `pipeline.py` 硬編碼的預設行為）**逐值相同**——旗標路徑沒壞。

13 張全數通過（13/13 兩項材質比對皆相符）。完整表格見 [`tables.md`](tables.md)。

## ⚠️ 已知殘留風險（誠實揭露，本卡範圍外、不阻擋本卡結論）

`geometry_confidence` **不**是本卡的比對對象——`round11_remap_baseline` 是純材質評測（`t38_treatment_eval.py` harness），本來就沒有 geometry 欄位；`EXPECTED_GATE`（T-28-A／T-36 凍結表）雖然有 geometry 值，但用真實 CLI 兩模式並排跑 13 張後，觀察到兩個與本卡改動無關的既有落差（列在 [`tables.md`](tables.md) 表 3）：

1. **`role_aware` 會透過既有的 `scene_cues["out_of_domain"]` 機制間接影響 geometry_confidence**（`site_photo_department_store`：某面在窄候選集下被判成「object_closeup」而觸發 `apply_scene_cue_confidence()` 降級，medium→low）。這個路徑（材質判定影響幾何信心）在 T-44 round17 上線時就存在，只是 T-44 自己的評測 harness 從未跑過真實 CLI 兩模式並排比較，這次才被看見。`gate 判定段／compute_materials_confidence()／scene_cues／門檻 0.4` 全部零改動（範圍紅線），此處只誠實記錄，不在本卡處理。
2. **`EXPECTED_GATE` 的 geometry 欄位疑似部分過期**（`TunnelToHell` 實測 `low`，表列 `medium`）——T-37（equirect 誤判修正）的動機案例正是 `TunnelToHell.jpg`，該表未見對應更新的痕跡。重新校準 geometry／gate 基準是 **T-47（gate 校準複審量測卡）** 的範圍，本卡不處理、不外推其他 11 張。
