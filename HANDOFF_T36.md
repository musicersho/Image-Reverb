# T-36 執行交接 — CLIP 材質判定準確度診斷

> 這份是**單張任務的執行交接**，因為 T-36 是整個專案第一張「**需要使用者親自參與**」
> 的卡，流程比平常多兩個來回，用一般的 [HANDOFF.md](HANDOFF.md) 講不清楚。
>
> - **使用者**：只要讀「§1 白話版」和「§3 你要做的事」，其他章節是給 Claude 讀的。
> - **Claude（任一模型）**：先讀 [CLAUDE.md](CLAUDE.md) 知道角色 → 讀本檔 → 讀
>   [TASKS.md](TASKS.md) 的 T-36 卡逐字執行。
>
> 建立於 2026-08-31（Opus 驗證完 T-35 後）。T-36 結案後這份檔可以刪除。
>
> ✅ **2026-08-31 結案**：T-36 已通過 Opus 複驗，gate 規則已依**裁決 T-36-A**
> 就地定案（維持原樣、議題關閉，全文見 TASKS.md T-36 卡尾），Phase 1.9 治療輪
> 已開（T-36 文件修正 → T-37 → T-38 → T-39，卡片在 TASKS.md 檔尾）。
> 本檔功成身退，僅供歷史查閱；現況一律以 HANDOFF.md 與 TASKS.md 為準。

---

## §0 現在的狀態（一句話）

Phase 1.8 的 T-33 文件修正、T-34、T-35 都已 ✅ 通過並 push（最新 commit
`229fd4b T-35: 驗證通過`），程式已定稿。**下一張是 T-36，量測卡，需要你參與。**

---

## §1 白話版：T-36 到底在做什麼

**一句話：治療前先量病。**

現在的問題是：AI 看照片猜材質（用 CLIP 模型），但**從來沒有人量過它猜得準不準**。
專案 13 張真實照片目前 100% 被信心 gate 擋下，我們卻不知道到底是
「AI 猜得爛」還是「gate 規則訂得太嚴」——這兩件事的解法完全相反。

所以 T-36 要做三件事：

1. **建立標準答案**：13 張照片 × 六個面（地板／天花板／東西南北四面牆）= 78 個面，
   由**你本人**逐面確認實際材質是什麼。這叫 ground truth（標準答案）。
2. **量準確度**：拿 AI 的判定去對標準答案，算出正確率、錯在哪、錯的型態各佔多少。
3. **天花板模擬**：假設 AI 每一面都猜對，現在的 gate 規則會不會放行？
   如果**全對還是被擋**，那就是規則的問題，不是 AI 的問題。

這份報告出來以後，Fable 才能一次定案 gate 規則（不准再拖），並決定怎麼治 CLIP。

**為什麼一定要你來確認？** 因為讓 AI 自己定「標準答案」等於自己出題自己改，
量出來的數字沒有意義。這道人眼關卡跟「人耳試聽」是同等地位的東西。

---

## §2 完整流程（五個階段）

```
【階段 1】Sonnet 產標註輔助材料        ← 貼 §4.1 的 Prompt
              ↓
【階段 2】👤 你逐面確認 78 個面        ← 看 §3
              ↓
【階段 3】Sonnet 寫標準答案檔＋量測＋報告  ← 貼 §4.2 的 Prompt
              ↓
【階段 4】Opus 驗證                    ← 貼 §4.3 的 Prompt
              ↓
【階段 5】Fable gate 規則就地定案       ← 貼 §4.4 的 Prompt
```

階段 1 和階段 3 中間**一定要停下來等你**，Sonnet 不准自己跳過去填答案。

---

## §3 👤 你要做的事（階段 2）

階段 1 跑完後，Sonnet 會給你一份**逐面標註表**。每一面會附上：

- 那一面的裁切圖（讓你看得到自己在判什麼）
- 目前管線判的材質 ＋ 判定來源（`clip` / `fallback` / `out_of_domain` / 無來源）
- 12 個候選材質清單
- 場地已知資訊（例如壁球場＝木地板／硬牆、MIT 場地說明）

**你只要對每一面回答「實際上是什麼材質」，從這 12 個裡挑一個：**

```
concrete（混凝土）      brick（磚）            wood_panel（木板）
gypsum_board（石膏板）  glass（玻璃）          marble（大理石）
carpet（地毯）          curtain_fabric（布簾）  acoustic_panel（吸音板）
audience_seating（觀眾席座椅）  grass_soil（草地/泥土）  generic_wall（一般牆面）
```

**看不出來就直接說 `unknown`**，這不是失敗——照片拍不到的天花板、糊掉的角落，
誠實標 `unknown` 比硬猜有價值得多。這些面會被**排除在正確率的分母外**，
不會污染數字。

**回覆方式**：一次回一批就好（例如一張照片六個面一起回），不用一次回完 78 個。
可以像這樣回：

```
bathroom_tiled：地板 marble、天花板 gypsum_board、四面牆 marble
bedroom_ai_generated：地板 carpet、天花板 unknown、四面牆 gypsum_board
```

**如果你不確定某一面**，直接說「這面我不確定，你先跟我說 AI 判什麼、
為什麼這樣判」——Sonnet 要回答你，但**不准替你決定**。

---

## §4 要貼的 Prompt（複製整段貼進新視窗）

### §4.1 階段 1 — 開 Sonnet 視窗，產標註輔助材料（模型選 Sonnet）

```
執行 TASKS.md 的任務 T-36，但這一輪只做「執行步驟 1」的前半段：產出標註輔助材料。
先讀 CLAUDE.md、HANDOFF_T36.md、以及 TASKS.md 的 T-36 卡全部內容再動工。

這一輪的範圍：對 13 張照片產出逐面標註表（每面附裁切圖、目前管線判定的材質 id
與來源、data/materials.json 的 12 個候選清單、場地已知資訊），然後停下來，
把標註表交給使用者逐面確認。

紅線：不准自己填 ground truth、不准先寫 data/material_ground_truth.json、
不准開始寫量測腳本。使用者確認完之前這張卡不算做到一半。
src/ 一行都不許改（量測期間程式定稿，共同鐵則）。

做完把標註表用好讀的方式呈現給使用者（一次呈現一到三張照片，不要一次倒 78 面），
並明確告訴使用者「看不出來就回 unknown」。
```

### §4.2 階段 3 — 你確認完之後，繼續同一個 Sonnet 視窗（不用開新視窗）

```
我已經逐面確認完了。請接著執行 TASKS.md 的 T-36 剩下的部分：

1. 把我確認的結果寫進 data/material_ground_truth.json（欄位要有 material_id 或
   "unknown"、confirmed_by: "user"、日期、備註）。我沒回答的面不准自己補。
2. 寫 scripts/t36_clip_accuracy.py（只讀 src/，不改），量準確度與錯誤型態。
3. 做「判定全對天花板模擬」——用 ground truth 唯讀呼叫 compute_materials_confidence()，
   規則零改動。
4. 產出 output/clip_accuracy/REPORT.md 與 tables.md（表格必須由程式產生）。

做完跑任務卡的「自我檢查」（含 Phase 1.8 共同鐵則 1–6），最後照 WORKFLOW.md
第 4 節做收工程序。
```

### §4.3 階段 4 — 開新視窗驗證（模型選 Opus）

```
你是驗證者，只審查不修改程式碼。請依 WORKFLOW.md 第 5 節的驗證標準，
審查任務 T-36 的成果：讀 TASKS.md 的該任務卡、讀相關程式碼、實際執行驗證指令。
最後輸出：「✅ 通過」或「❌ 退回」＋具體理由清單。若退回，把理由寫進
TASKS.md 該任務卡的「狀態」欄，改成 🟠 退回。
```

### §4.4 階段 5 — T-36 通過後，開新視窗（模型選 Fable）

```
你是規劃者。請讀 CLAUDE.md、SPEC.md、ROADMAP.md、TASKS.md、DEV_LOG.md 最近三筆，
以及 output/clip_accuracy/REPORT.md。

目前的情況是：T-36（CLIP 材質判定準確度診斷）已驗證通過，報告出來了。
依裁決 T-33-A 裁決 C 的終止條款，請做 gate 規則「就地定案」——規則 1／2／3
與地雷 #23／#24 一次收齊，不得再展延；同時規劃 CLIP 治療卡，並評估要不要開
陳設換算公式修正輪。
```

---

## §5 給 Sonnet 的紅線清單（動工前逐條看過）

### 5.1 T-36 卡自己的紅線

1. **ground truth 不准 AI 自填**。`confirmed_by` 只有使用者真的回答過的面才能寫
   `"user"`。使用者沒回的面就留著別寫，不要猜。
2. **`unknown` 面不准算進正確率分母**，而且要回報排除了幾面。這是 Opus 的點名紅旗。
3. **天花板模擬必須唯讀 import 呼叫 `compute_materials_confidence()`**，
   不准重寫一份、不准「為了模擬方便」改參數簽章。
4. **量測期間 `src/` 一行不許改**。若量測需要的分數拿不到（例如
   `surfaces.py` 沒暴露完整候選分數），照卡片寫的降級處理：
   把那一小節標「留待治療卡」並在 REPORT 誠實記載，**不准為了量測改 `src/`**。
5. **表格由程式產生**（地雷 #15），不准手打數字進 Markdown。

### 5.2 Phase 1.8 共同鐵則（量測卡也要跑，證明沒偷改程式）

1. 十套測試全部 exit 0：`test_ir_synth`／`test_output_gate`／`test_confidence_axes`／
   `test_material_fallback`／`test_surface_trusted_scope`／`test_t30_low_combined`／
   `test_scene_text`／`test_coupled`／`test_acoustics`／`test_furnishings`
2. 六條交付 IR MD5 一條都不許變（T-14 兩條由 `test_ir_synth`【6】自動比對；
   T-20 兩條 `2adbaa75eb698772a8c9aa693179ec47`／`2dd19b6e6d351d713887636fe45cd67e`；
   T-21 兩條 `9a94ffdf5d8295aee7889729c39c9cd8`／`a1c21bcc3fd9aa3480df203a89c8cd05`）
3. `src/image_reverb/ir_metrics.py` 一行不許動
4. 不許動 `SPEC.md`／`ROADMAP.md`／`WORKFLOW.md`／`output/mvp_acceptance/`／
   `output/material_round/`
5. 新增的測試必須對舊碼實測會失敗（量測卡若沒新增行為測試，這條寫「不適用」並說明）
6. **gate 判定規則零改動**——`compute_materials_confidence()` 與 `run_photo()` 的
   gate 觸發／放行條件一行不動。T-36 是**量**規則的天花板，不是**改**規則。

### 5.3 ⚠️ T-35 留下的一個坑（一定會踩到）

`scripts/t33_material_round_tables.py` 的「陳設套用組」靠的是**舊預設**
（它只在對照組加 `--no-furnishings`）。T-35 之後預設已改成觀測模式，
那一組會跑成觀測模式，並在讀 `A_by_band` / `proportion_of_absorption_1khz` 時
`KeyError`（該腳本第 333／341 行）。

- T-33 已結案、`output/material_round/` 凍結，**這不影響 T-36 的驗收**。
- 但 **T-36 若沿用這支腳本的樣式或快取手法，套用組要顯式加 `--furnishings`**。
- 全庫掃過，這是唯一一個讀 `analysis["furnishings"]` 的下游消費端。

---

## §6 動工前要知道的既有事實（省得重查）

### 6.1 13 張照片與裁決 T-28-A 的 gate 基線

| # | name | 照片路徑 | 基線 (geometry, materials) |
|---|------|---------|---------------------------|
| 1 | bathroom_tiled | `assets/photos/bathroom_tiled.png` | medium, low |
| 2 | bedroom_ai_generated | `assets/photos/bedroom_ai_generated.png` | medium, low |
| 3 | stairwell_tiled | `assets/photos/stairwell_tiled.png` | medium, low |
| 4 | arena_ntsu_linkou | `assets/photos/arena_ntsu_linkou.png` | low, low |
| 5 | car_interior_suv | `assets/photos/car_interior_suv.png` | low, low |
| 6 | CathedralRoom | `assets/reference_irs/cathedral_room_shasta_lake_caverns/CathedralRoom.jpg` | medium, low |
| 7 | DivorceBeach | `assets/reference_irs/divorce_beach/DivorceBeach.jpg` | low, medium |
| 8 | site_photo_department_store | `assets/reference_irs/mit_department_store/site_photo_department_store.png` | medium, low |
| 9 | site_photo_gym | `assets/reference_irs/mit_gym/site_photo_gym.png` | low, low |
| 10 | site_photo_restaurant | `assets/reference_irs/mit_restaurant/site_photo_restaurant.png` | low, low |
| 11 | RacquetballCourt4 | `assets/reference_irs/racquetball_court_4/RacquetballCourt4.jpg` | medium, low |
| 12 | SteinmanHall | `assets/reference_irs/steinman_hall/SteinmanHall.jpg` | low, low |
| 13 | TunnelToHell | `assets/reference_irs/tunnel_to_hell/TunnelToHell.jpg` | medium, low |

清單與基線的**唯一可信來源**是 `scripts/t33_material_round_tables.py` 的
`GATE_ITEMS` 與 `EXPECTED_GATE`（第 61–124 行，`EXPECTED_GATE` 起於 61、`GATE_ITEMS` 起於 78），照抄不要重打。
**若實測三軸與基線不符 → 立刻停下標 🔴 卡關**，不要自己解釋掉。

### 6.2 78 面的來源分佈（裁決 T-28-A 更正 2，要對帳）

`clip 22 面`／`fallback 32 面`／`out_of_domain 13 面`／**無來源 11 面**（合計 78）。

### 6.3 三顆一定要先讀的地雷（全文在 HANDOFF.md「踩過的坑」）

- **#18 🔴**：材質誤判是 RT60 誤差的主導來源，不是幾何也不是合成引擎。
  必測反例：壁球場一面牆被判成 `curtain_fabric`，單獨毀掉整條 IR。
  **這就是 T-36 §2 要量的「in-set 誤判」型態。**
- **#23 🟠**：材質來源有第四態「**無來源**」（角色沒被觀測到，`surfaces.sources`
  沒有該面條目，CLI 印 `-`）。它**不觸發規則 1**（不逼 low），但**永久阻斷規則 3**。
  78 面裡佔 11 面。
- **#24 🔴**：透視照的 `materials_confidence == "high"` **結構性不可達**——
  規則 3 要求六面全 clip 且零 warnings，但透視照只要判到牆就必然掛上
  「看不到背後的牆」warning，條件恆假。**T-36 的天花板模擬就是為了量這個。**

### 6.4 T-36 的產出清單（不多不少）

- `data/material_ground_truth.json`
- `scripts/t36_clip_accuracy.py`
- `output/clip_accuracy/REPORT.md`
- `output/clip_accuracy/tables.md`

REPORT 結構照卡片：①準確度基準率（總體／按來源／按角色）②錯誤型態份額
③天花板模擬結果 ④治療方案候選的證據整理（**只列證據不實作**）⑤交 Fable 的問題清單。

---

## §7 卡關怎麼辦

- **Sonnet 連續 3 次嘗試同一件事失敗** → 停，在 TASKS.md T-36 卡的狀態欄寫
  `🔴 卡關` ＋原因，只 commit 文件（`docs: T-36 卡關紀錄`），請使用者去開 Fable 視窗。
- **13 張的三軸 confidence 與 §6.1 基線不符** → 這是紅旗不是小事，立刻 🔴 停。
- **Opus 退回** → 狀態改 🟠 退回＋理由寫進卡片，使用者再開 Sonnet 視窗修，
  修完重跑階段 4。
- **使用者不確定某些面** → 那些面標 `unknown` 就好，不要為了湊滿 78 面硬填。
