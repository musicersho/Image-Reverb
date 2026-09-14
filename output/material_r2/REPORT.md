# T-48 B 部分 — T-12 判準 v2 量測

> 產生日期：2026-09-14T09:32:53.539675+00:00　git_head：`8bfe262b33117bc9d5e5b0c8df4c33b247d9a48a`　git status --porcelain -- src data scripts：(空)

三條 IR 由 `scripts/gen_ir_manual.py`（不改動，逐字沿用 T-12 卡「Opus 驗證結果」表格已記錄的指令）本次重生，交付到 `output/material_r2/`（紅線：不得重用 `output/` 舊 IR）：

| case | 指令 | 房間 | 交付檔案 | sha256（本次重生） |
|---|---|---|---|---|
| per-wall：floor=carpet／其餘 gypsum_board（4×3×2.5m） | `python scripts/gen_ir_manual.py small --materials floor=carpet,walls=gypsum_board` | 4×3×2.5m | `output/material_r2/per_wall_floor_carpet.wav` | `0c3e1f6ddcbf856a82043ce3538ecf77e4078b45887ae11fe5928246e83f2fba` |
| 對照組：六面 gypsum_board（4×3×2.5m） | `python scripts/gen_ir_manual.py small --materials floor=gypsum_board` | 4×3×2.5m | `output/material_r2/control_six_face_gypsum_board.wav` | `fb9248d49229ba6a238701cbf759ad22ce1028a5f2ebb7861a6690c368838295` |
| 對照組：六面 carpet（4×3×2.5m，舊六面同材質模式） | `python scripts/gen_ir_manual.py small --material carpet` | 4×3×2.5m | `output/material_r2/control_six_face_carpet.wav` | `91d4af0f0b81dcd1715481552a2f8d82859a4f7ada712b37ed89a1c6174d41c7` |

## 0. 結論

- **v2-a（公式層）**：PASS——per-wall Sabine 125Hz 0.3480s，目標 0.348s ±20%，誤差 +0.0%（同義反覆：目標值本身就是同一公式的輸出，PASS 鑑別力為零，見裁決 T-48-F F4，只記錄作為公式回歸性測試，不構成材質模組正確性證據）
- **v2-b（IR 實測層，聯合帶 T30）**：**inconclusive（diff 子判準：首跑 FAIL，方法非決定性；ratio 子判準：PASS）**——**首跑**（`d372ad9`，Part B 首次實作後隨即執行）diff 子判準 per-wall vs 六面 gypsum 對照差異 -21.1% → **FAIL**（判準 ≤±20%；原始 WAV／log 已於本卡執行期間的後續重跑覆蓋，此數字為執行者自述、無殘存產物可複核，見 §3）。依裁決 T-48-F F2（Fable，2026-09-14）：diff 子判準永久記首跑 verdict，量測方法（單次生成、無固定 seed）已證實非決定性，不得因後續重跑改記 PASS（WORKFLOW §7.5）。**本次交付版本數字（次要，僅供參考，不是結論）**：per-wall 0.9650s vs 六面 gypsum 對照 1.2052s（差異 -19.9% → PASS）。ratio 子判準（六面 carpet 對照 3.8319s / per-wall = 3.97 倍，判準 ≥3 倍）不受本卡實測到的隨機噪聲量級影響（見 §3）→ PASS
- **v1 字面條件（只記錄不當門檻）**：未達——per-wall 125Hz 八度 T30 0.7074s，字面目標 0.35s ±20%，誤差 +102.1%（裁決 B 已證八度量測受鄰帶耦合污染，此數字**不當作判準**，僅照量照列）


## 1. 逐案數值（程式量測，未手打）

| case | Sabine 125Hz (s) | 125Hz 八度 T30 (s) | 88.4–353.6Hz 聯合帶 T30 (s) |
|---|---|---|---|
| per-wall：floor=carpet／其餘 gypsum_board（4×3×2.5m） | 0.3480 | 0.7074 | 0.9650 |
| 對照組：六面 gypsum_board（4×3×2.5m） | 0.2820 | 0.8481 | 1.2052 |
| 對照組：六面 carpet（4×3×2.5m，舊六面同材質模式） | — | 3.9039 | 3.8319 |

## 2. 方法

1. `scripts/gen_ir_manual.py`（**零改動**）依上表指令重生三條 IR，程式預設寫到 `output/`，本腳本立即搬到 `output/material_r2/`（sha256 在搬移前後都算過，確認 bytes 未在搬移過程變動）。
2. v2-a：Sabine 125Hz 數字讀自 `gen_ir_manual.py` 本次執行的 stdout（程式印出，不手打）。
3. v2-b／v1：讀 `src/image_reverb/ir_metrics.py` 既有函式——`t30_low_combined()`（T-18，88.4–353.6Hz 聯合帶）與 `band_t30(ir, fs, [125])`（單一 125Hz 八度，v1 字面條件用）——對本次重生的 WAV 直接量測，不重新實作任何頻段濾波／Schroeder 積分邏輯。
4. `ir_metrics.py`、`src/`、`data/` 全程零 diff（本卡只呼叫既有函式，不修改）。


## 3. 附錄：量測穩定性檢查（不影響上方 §0 官方判定——§0 依裁決 T-48-F F2 記「首跑 FAIL、方法 inconclusive」，本次交付版本數字僅供參考）

`gen_ir_manual.py` 呼叫的 pyroomacoustics ray tracing **沒有固定 random seed**（已實測：同一指令重跑兩次，輸出 WAV sha256 不同，樣本點最大絕對差約 0.099——見本卡交接筆記）。§0 的官方判定只用**每個 case 第一次（也是唯一交付到 `output/material_r2/` 的那次）重生結果**，不做多次重跑取平均（判準本身沒有要求，本卡也不得另外發明「取平均」這種未鎖定的判定方式）。

為了讓 Opus／Fable 判斷 v2-b 這筆 **PASS**（本次交付版本，-19.9%）是否落在量測噪聲量級內，這裡**額外**重跑 per_wall／control_gypsum 各 4 次（存於 `output/material_r2/stability_check/`，與正式交付檔案分開，不算入判定）：


- per_wall 聯合帶 T30 各次量測（含官方那次）：[0.965, 0.9279, 0.9871, 1.0092, 0.9287]

- control_gypsum 聯合帶 T30 各次量測（含官方那次）：[1.2052, 1.1547, 1.1604, 1.1508, 1.2066]

- 交叉配對後的 per_wall vs control_gypsum 差異百分比範圍：-23.1% ～ -12.3%（判準 ≤±20%；官方那次配對＝-19.9% → PASS）


**觀察**：不同次重跑的差異百分比跨越 ±20% 門檻兩側，代表這個判準在目前的量測方法（單次生成、無固定 seed）下對隨機重跑結果敏感、鑑別力薄弱——這正是本卡 §0 記「v2-b 首跑 FAIL、方法 inconclusive」、不採用本次交付版本 PASS（-19.9%）當作最終結論的原因（WORKFLOW §7.5：量測方法被證明無效時，舊結果不能直接改成 PASS）。是否改進量測方法（例如固定 seed、多次取中位數）已交由 T-56（criteria v3，裁決 T-48-F F2）處理，本卡不自行更動判準或判定方式。


**本卡執行過程中的官方量測歷史（誠實揭露，非結果篩選；修正輪 R3 更正標示，Sonnet 2026-09-14：前兩筆原始 WAV／log 已於後續重跑覆蓋，數字為執行者自述，無殘存產物可複核）**：本卡執行期間因程式本身的修正（除錯與格式修正，與量測邏輯／判準無關）重新跑過三次「官方」per_wall／control_gypsum 生成＋量測，每一次都是當時唯一交付到 `output/material_r2/` 的版本（前一次的交付檔案在下一次重跑時被覆蓋，紅線要求不得重用舊 IR，所以每次重跑本來就必須用新生成的檔案）：

| 官方重跑對應 commit | per_wall vs control_gypsum 差異 | v2-b diff 子判準 | 資料來源 |
|---|---|---|---|
| `d372ad9`（Part B 首次實作，隨即執行，**首跑 verdict**） | -21.1% | FAIL | 執行者自述、無殘存產物、不可複核（Opus 驗證紀錄 R3） |
| `dd03c0e`（新增本附錄後重跑） | -22.3% | FAIL | 執行者自述、無殘存產物、不可複核（同上） |
| `cda6b9b`（修正附錄 numpy 顯示格式後重跑，本次交付版本） | -19.9% | PASS | 可複核：`output/material_r2/` 現存交付 WAV（sha256 見上表） |

三次都不是為了「重跑到通過為止」而執行——每次重跑的直接原因記在對應 commit 訊息裡（附錄程式碼新增、顯示格式修正），跟 v2-b 的判定方向無關；但三次結果本身（-21.1%／-22.3%／-19.9%）都群聚在 ±20% 門檻附近，印證上面「觀察」段的結論：這個判準在目前的量測方法下沒有穩定的鑑別力。**依裁決 T-48-F F2（Fable，2026-09-14）：本卡 §0 官方記錄＝「首跑 FAIL、方法 inconclusive」，永久保留，不因本次交付版本剛好是 PASS 就回頭改記 PASS**（WORKFLOW §7.5）；量測方法是否修正（固定 seed／多次取中位數）由 T-56（criteria v3）另行處理，本卡不自行更動判準或判定方式。

