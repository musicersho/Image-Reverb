# T-39 REPORT — 候選材質集擴充（否定結論，資料保留）

## 性質聲明（裁決 T-38B-A 新增，寫在最前面）

本卡的「加候選能提升正確率」是**待驗證的假設**，不是工程步驟可保證的結果——
全域 softmax 下加候選會重分配全部 78 面的機率（地雷 #13＋T-38B 副作用實證
同型）。**跑滿預算、誠實報告 ＝ 工程完成**；round12～round14 未同時滿足產品
採用門檻是**合法的實驗結論**，不是卡關，也不是使用者操作失敗。

## 一、16 個 proxy 面重對映（工程完成的第一部分）

16 個 proxy 面已由使用者於 2026-09-02 逐面確認（`confirmed_by: "user"`，
見 `data/material_ground_truth.json`）。查建築聲學公開表格（主要來源：
akustik.ua《Absorption Coefficients》，與 Egan/Long 教科書表同源同類型）：

- **3 面查到出處、新增候選材質**：`vinyl_panel`（bathroom_tiled 天花板）、
  `rubber_flooring`（site_photo_gym 地板）、`metal_roof_deck`
  （site_photo_gym 天花板）。三種材質的 α 值與逐句出處寫在
  `data/materials.json`。
- **13 面查無公開逐頻段出處，依卡片規則不自創數字，維持原候選並記錄
  理由**（詳見 PLAN_T39.md §1 表格）：
  - `stairwell_tiled.floor`（磨石子）——**意外發現**：磨石子（terrazzo）
    在同一份公開表格裡的數值與現有 `marble` 候選**逐頻段完全相同**
    （0.01/0.01/0.01/0.01/0.02/0.02），`marble` 不是近似值而是數值零誤差
    的精確匹配，新增候選對聲學模擬結果沒有意義。
  - 車用內裝織物（headliner／門板）×2 面、CathedralRoom 石灰岩 ×6 面、
    DivorceBeach 砂岩 ×4 面：查了多個公開表格與資料庫，均查無專屬逐頻段
    出處。
- proxy 面從 16 面降到 13 面（3 面因新增候選歸零）。

**附帶發現（非本卡範圍，記錄留給 Fable）**：`car_interior_suv.west` 與
`.east` 是同一種車門絨面板，但既有資料只有 `east` 標了 `proxy: true`，
`west` 沒有標。未更動，備註已記錄在 ground truth 檔案裡。

## 二、兩段式基線與擴充實測（對照 `round11_remap_baseline`）

| 輪次 | 候選集 | overall | floor | 非 proxy | proxy | in-set 誤判 |
|---|---|---:|---:|---:|---:|---:|
| round0_baseline（T-38B 舊基線，重對映前） | 原 12 | 31/76 | 4/13 | — | — | 9 |
| **round11_remap_baseline**（重對映後，候選未動） | 原 12 | 30/76 | 4/13 | 30/63 | 0/13 | 9 |
| round12_expanded（+3 新候選） | 15 | 28/76 | 4/13 | 28/63 | 0/13 | 10 |
| round13（調 metal_roof_deck） | 15 | 29/76 | 4/13 | 29/63 | 0/13 | 9 |
| round14（調 vinyl_panel，最終輪） | 15 | 24/76 | 4/13 | 24/63 | 0/13 | 12 |

round11 相對 round0_baseline **下降 1**（31→30）：這是量尺變誠實，不是
退步——`bathroom_tiled.ceiling` 原本用 `gypsum_board` 近似碰巧判對，重對映
成 `vinyl_panel`（當時還沒加入候選）之後必錯，如實反映涵蓋率缺口。

## 三、逐輪發生了什麼（誠實記錄，含結構性發現）

### round12 —— 加入 3 個新候選：1 面修正，3 面新副作用

- **結構性發現（決定性，不是用詞問題）**：追查 `runs/*/detail.json` 發現
  `bathroom_tiled.ceiling` 與 `site_photo_gym.ceiling` 的 `sources`／
  `faces` 完全沒有 `ceiling` 鍵——**ADE20K 分割階段就沒偵測到 ceiling
  角色像素**（`ratio < config.MIN_SURFACE_AREA_RATIO`），CLIP 從未被
  呼叫。這代表 `vinyl_panel` 與 `metal_roof_deck` 的**自身目標面在本
  13 張資料集裡結構性不可達**——這是分割階段的缺口，任何 CLIP 提示詞
  調整都碰不到（T-39 範圍紅線本來就不准動分割邏輯）。
- 唯一真正修正的目標面：`site_photo_gym.floor` → `rubber_flooring`，
  clip 信心 0.543（`top3=[rubber_flooring 0.543, acoustic_panel 0.250,
  concrete 0.090]`）。
- 地雷 #13 型副作用（softmax 重分配，非本卡目標面）：
  - `SteinmanHall.ceiling` 從正確（`curtain_fabric`）翻成 `metal_roof_deck`
    （信心 0.718）
  - `RacquetballCourt4.south` 從正確（`glass`）翻成 `vinyl_panel`
    （信心 0.532）
  - `RacquetballCourt4.floor` 從正確（`wood_panel`）掉到 `fallback`
    （`rubber_flooring` 把 top1 機率拉到門檻 0.4 以下：
    `top3=[rubber_flooring 0.388, wood_panel 0.247, vinyl_panel 0.171]`）

### round13 —— 只調 `metal_roof_deck`：成功壓下它的副作用

字串加入「rigid」「dull metallic sheen」「not fabric or cloth」後，
`SteinmanHall.ceiling` 恢復正確（`curtain_fabric`，信心 0.571），且未在
其他面新增副作用（T-33 差異清單照片數 5→4）。in-set 誤判回到 round11
水準（9）。`RacquetballCourt4` 兩個副作用（與 `metal_roof_deck` 無關）
維持不變，符合預期。

### round14 —— 只調 `vinyl_panel`：目標沒修到，且是四輪最差的一輪

字串改成「opaque...not glass and not transparent」後，`vinyl_panel`
**沒有**修正 `RacquetballCourt4.south`（仍是 `vinyl_panel`，信心從 0.532
升到更高），反而在**未鎖定的照片**大範圍新增誤判：
`site_photo_department_store` 四面牆（原正確 `gypsum_board`）全部被
`vinyl_panel` 搶答、`CathedralRoom.west`（原正確 `concrete`）、
`RacquetballCourt4.north`（原正確 `gypsum_board`）都被搶答。T-33 差異
清單照片數擴大到 7 張（round13 為 4 張）。overall 掉到 24/76，是四輪
（round11～14）裡最差的一輪。

**round14 是 PLAN_T39.md §4 預算上限（round12 之後最多 2 輪調整）的最後
一輪，跑滿即停，不得為了達標超預算加輪次。**

## 四、為什麼「加候選集」這條路在本資料集碰到結構性天花板

三個新候選裡有兩個（`vinyl_panel`／`metal_roof_deck`）的目標面在分割
階段就不可達，等於這條路對它們**先天沒有正貢獻的上限**；唯一真正可達
的 `rubber_flooring`（修正 1 面）也在 round12 就製造了對等的副作用
（`RacquetballCourt4.floor`），round13/14 的調整只能證明「壓下已知副作用」
是可行的（round13 對 `metal_roof_deck` 成功），但**無法讓一個目標面
結構性不可達的候選變成淨正貢獻**——這與 T-38B 的結論同型：全域 12（現在
是 15）候選共用 softmax，改任一候選字串必然在未鎖定的照片製造副作用
（地雷 #13），而本卡新增候選的「收益端」先天就被分割階段的涵蓋率卡住。

## 五、產品採用門檻判定（對 `round11_remap_baseline`）

round14（最後一輪）**同時**檢驗三個門檻：

| 門檻 | round11_remap_baseline | round14（最終輪） | 結果 |
|---|---:|---:|---|
| ① overall 上升 | 30/76 | 24/76 | ❌ 下降 |
| ② floor 不下降 | 4/13 | 4/13 | ✅ 持平 |
| ③ 非 proxy 正確數不下降 | 30/63 | 24/63 | ❌ 下降 |

**三個門檻未同時滿足（①③失敗）→ 不採用新候選。**

處置（依 PLAN_T39.md §5）：
- `surfaces.py` 的 `CLIP_MATERIAL_PROMPTS` **已還原**，與 T-39 開工前
  逐位元相同（`git diff <T-39前commit> -- src/image_reverb/surfaces.py`
  只剩一段說明本次否定結論的註解，字典本體零差異）。
- `data/materials.json` 的 3 筆新材質資料**保留**（有出處的資料本身有
  價值，供 `--override-material` 手動指定；不在 CLIP 候選集裡就不影響
  自動判定）。
- `data/material_ground_truth.json` 的 16 面重對映**保留不回滾**
  （真實就是真實，其中 3 面的 `proxy` 已改為 `false`）。

## 六、門檻敏感度分析（表 7 型，對最終狀態即 `round11_remap_baseline` 的
候選集重跑）

新候選未採用，最終狀態的 CLIP 候選集與 `round11_remap_baseline` 相同，
门檻敏感度用該輪快取（`唯讀`呼叫 `t36_analysis.build_threshold_sensitivity()`）
重算：

| 門檻 | 會從 fallback 轉為 clip 的面數 | 其中答對 | 其中答錯 |
|---|---|---|---|
| 0.20 | 35 | 3 | 32 |
| 0.25 | 27 | 3 | 24 |
| 0.30 | 25 | 3 | 22 |
| 0.35 | 9 | 1 | 8 |
| 0.40（現行） | 0 | 0 | 0 |

與 T-36 原始表 7 結論一致：調低門檻會同時放行「答對」與「答錯」的面，
且答錯遠多於答對，本卡不建議調整門檻（門檻 0.4 本來就在 T-39 範圍紅線內
不准動）。

## 七、共同鐵則自我檢查

1. **測試套件全部 exit 0**：`scripts/test_*.py` 全部 **17 支**（含新增
   `test_t39_materials_invariant.py`）逐支單獨執行，全部 `EXIT=0`。
   `test_t39_materials_invariant.py` 對 T-39 前的舊碼（`git worktree` 出
   `a42066c`）實測 `KeyError: 材質表裡沒有 id 'vinyl_panel'`，`EXIT=1`，
   證明診斷力。
2. **六條交付 IR MD5 逐條比對**（重新生成比對，非 `git status` 論證）：
   - `chk_bath.wav`（T-20）= `2adbaa75eb698772a8c9aa693179ec47` ✅
   - `chk_church.wav`（T-20）= `2dd19b6e6d351d713887636fe45cd67e` ✅
   - `coupled_neighbor_voices.wav`（T-21）= `9a94ffdf5d8295aee7889729c39c9cd8` ✅
   - `coupled_stadium_corridor.wav`（T-21）= `a1c21bcc3fd9aa3480df203a89c8cd05` ✅
   - T-14 兩條由 `test_ir_synth.py` 硬編碼比對通過（同上第 1 項）
3. **`src/image_reverb/ir_metrics.py` 零 diff**：
   `git diff a42066c -- src/image_reverb/ir_metrics.py` 輸出為空。
4. **`SPEC.md`／`ROADMAP.md`／`WORKFLOW.md`／三個凍結目錄零改動**：
   `git diff a42066c -- SPEC.md ROADMAP.md WORKFLOW.md output/mvp_acceptance/
   output/material_round/ output/clip_accuracy/` 輸出為空。
5. **新測試診斷力**：見第 1 項（修 bug 類，對舊碼實測 fail）。
6. **gate 判定規則零改動**：`classify_region_material()`／
   `compute_materials_confidence()` 全程零 diff（`git diff a42066c --
   src/image_reverb/surfaces.py` 只有 `CLIP_MATERIAL_PROMPTS` 字典後方
   新增一段註解，字典本體與兩個函式逐位元相同）。`CLIP_OOD_PROMPTS`／
   門檻 0.4 由 `test_t39_materials_invariant.py`【5】程式驗證零改動。
7. **臥室紅旗**：`python -m src.image_reverb assets/photos/
   bedroom_ai_generated.png --no-viz` 實測，`geometry=medium,
   materials=low, overall=low`，**仍是擋（未從擋變放）**，與歷來記錄一致。
8. **基線變化表**：由於最終狀態的 `src/image_reverb/surfaces.py` 與
   T-39 開工前**逐位元相同**（只多一段不影響執行的註解），`round11_
   remap_baseline` 本身就是用這份逐位元相同的程式碼跑出的 13 張真實
   結果，可直接當作最終狀態的 13 張 3 軸信心／gate 對照表：其
   `cross_check_treatment()` 對 T-33 凍結快取的差異只有 **2 項**，且
   全部屬於 `TunnelToHell`（T-37 修正後與 T-33 凍結快取本來就不同，見
   HANDOFF_T38.md 地雷 B 記載的既有預期），其餘 12 張逐值不變。

## 八、Opus 驗證重點對照

- α 數字出處：3 個新材質皆引用同一份公開表格（akustik.ua，與 Egan/Long
  同源同類型）的具體欄位，逐句寫在 `data/materials.json` 的 `source`
  欄位。
- ground truth 重對映使用者確認紀錄：16 面全部 `confirmed_by: "user"`，
  對話紀錄見本次對話歷史（使用者於 2026-09-02 回覆「都同意」逐面確認）。
- 既有 12 材質 α／12 條提示詞漂移：`test_t39_materials_invariant.py`
  【1】【2】程式驗證零漂移。
- 門檻敏感度重跑：見第六節。
- round12→round0_baseline 直接比較：本報告全程只對照
  `round11_remap_baseline`，round0_baseline 只在第二節表格列出作對照
  參考，不作為門檻判定基準。
- 超出 2 輪調整預算：round12（首跑）＋round13／round14（調整）＝
  預算上限剛好用滿，未超支。
- 否定結論標成失敗或卡關：本報告全程標記為 ✅ 工程完成、產品不採用，
  不是 🔴 卡關。
