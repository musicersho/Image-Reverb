# T-39 PLAN — 候選材質集擴充（round11_remap_baseline → round12_expanded）

> **本檔在 round11 執行前寫成並 commit。**（比照 T-38B PLAN.md 的做法：本檔
> commit 時間必須早於 round11／round12 ROUND.md 的 commit 時間，可用
> `git log --format='%h %cI %s'` 對照佐證。）

## 0. 依據

裁決 T-38B-A 開卡（HANDOFF_T39.md）：78 面裡有 16 面（20.5%）真實材質不在
12 候選內、這些面 proxy 正確率僅 1/16（6.2%）——涵蓋率是準確率天花板，
「換問法」（T-38B）治不了。本卡逐面請使用者重新確認 16 個 proxy 面
（2026-09-02，對話紀錄見下方 §1），並依查證結果決定新增哪些候選。

## 1. 16 個 proxy 面重對映結果（使用者已逐面確認，2026-09-02）

查證方法：對每個真實材質，查建築聲學公開表格（主要來源：akustik.ua
《ABSORPTION COEFFICIENTS》，與 Egan/Long 教科書表同源同類型的公開工程
參考表）是否有可直接引用的逐頻段吸音係數；查無出處者依卡片規則
**不自創數字**，維持原候選並記錄理由。

| 面 | 真實材質 | 查證結果 | 處置 |
|---|---|---|---|
| bathroom_tiled.ceiling | 塑膠/塗料天花板 | akustik.ua「Linoleum or vinyl stuck to concrete」0.02/0.02/0.03/0.04/0.04/0.05 | **新增候選 `vinyl_panel`**，改標，proxy→false |
| stairwell_tiled.floor | 磨石子（terrazzo） | akustik.ua「Smooth marble or terrazzo slabs」0.01/0.01/0.01/0.01/0.02/0.02——與現有 `marble` 逐頻段**完全相同** | 不新增候選（加了對模擬結果零影響）；維持 `marble`，proxy 維持 true（視覺仍非拋光大理石），備註補充查證結果 |
| car_interior_suv.ceiling | 車頂棚絨面（headliner） | 查無汽車內裝織物公開逐頻段係數表（SAE 論文為付費文獻） | 維持 `curtain_fabric`，proxy 維持 true，記錄查無出處 |
| car_interior_suv.east | 車門絨面板 | 同上，查無出處 | 維持 `acoustic_panel`，proxy 維持 true，記錄查無出處 |
| CathedralRoom ×6（floor/ceiling/west/east/south/north） | 石灰岩（官網 "Limestone, concrete"） | 石灰岩公開資料約 0.02–0.05 量級、與粗面混凝土相近，但查無石灰岩專屬逐頻段表 | 維持 `concrete`，proxy 維持 true，記錄查證結果 |
| DivorceBeach ×4（west/east/south/north） | 沙岩峭壁（風化砂岩） | 查無天然砂岩/岩壁公開逐頻段係數表 | 維持 `grass_soil`，proxy 維持 true，記錄查無出處 |
| site_photo_gym.floor | 橡膠防震地墊 | akustik.ua「Rubber floor tiles 6mm」0.05/0.05/0.10/0.10/0.05/0.05 | **新增候選 `rubber_flooring`**，改標，proxy→false |
| site_photo_gym.ceiling | 白色烤漆金屬鋼構屋頂 | akustik.ua「Steel decking」0.13/0.09/0.08/0.09/0.11/0.11 | **新增候選 `metal_roof_deck`**，改標，proxy→false |

**結果**：16 個 proxy 面裡 **3 面**改標新候選、**13 面**查無公開出處維持原候選
（proxy 未歸零，符合卡片「或維持並記原因」的允許結果）。逐面備註與
`confirmed_by: "user"` 已寫入 `data/material_ground_truth.json`（commit 於
本檔之前一併提交）。

**附帶發現（非本卡範圍，記錄留給 Fable）**：`car_interior_suv.west`
與 `.east` 是同一種車門絨面板，但既有資料只有 east 標了 `proxy: true`，
west 沒有。不在本卡「16 個已使用者確認的 proxy 面」範圍內，未更動，如實
記錄於 ground_truth.json west 面的備註。

## 2. 新增候選材質（`data/materials.json` ＋ `surfaces.py`）

三個新材質的 α 值與出處已寫入 `data/materials.json`（各材質 `source`
欄位為完整出處說明）。以下是**固定寫死**的 CLIP 候選提示詞字串
（round12 起才啟用，不得跑完才改用詞；round12 未達標時只准在
round13／round14 調整這三句，既有 12 條一字不動）：

```json
{
  "vinyl_panel": "a smooth glossy plastic or vinyl panel surface, non-porous",
  "rubber_flooring": "a dark rubber or vinyl composition floor mat with a matte non-porous surface",
  "metal_roof_deck": "a painted corrugated or ribbed sheet metal roof or ceiling panel"
}
```

設計理由：三句都刻意避開既有 12 條候選的關鍵詞重疊——
`vinyl_panel` 強調「光滑不透氣」與 `gypsum_board`（"painted plasterboard
drywall"，強調板材）、`marble`（"polished... tile"，強調石材光澤）區隔；
`rubber_flooring` 強調「霧面不透氣」與 `carpet`（"thick... textile"，
強調纖維觸感）區隔；`metal_roof_deck` 強調「波浪/肋狀金屬」與 `concrete`
（強調澆置面）、`gypsum_board` 區隔。

## 3. 兩段式基線（量測歸因用，必做）

- **第一段 `round11_remap_baseline`**：16 面重對映後、候選集**未動**
  （`surfaces.py` 仍是原 12 條候選，不含本檔 §2 的三個新字串）先全量重跑
  一輪。這一輪數字預期**下降**（3 面新標的真實材質还不在候選集內，
  在候選集擴充前必錯；其餘 13 面沿用原候選，正確率不變）——這是量尺
  變誠實，不是退步，REPORT 開頭要先講明。
- **第二段 `round12_expanded`**：候選集加入 §2 三個新字串後重跑，與
  `round11_remap_baseline` 比較。**不得拿 `round0_baseline` 直接比
  `round12`**（量尺不同，比了就是造假比較）。

## 4. 預算與調整規則

- round12 之後最多再 **2 輪**調整（round13／round14），只准調
  **`vinyl_panel`／`rubber_flooring`／`metal_roof_deck` 三個新候選**的
  字串，**既有 12 條一字不動**（T-38B 已實證改它們有害無益）。跑滿即停。
- 每輪 78 面全量量測，沿用 `t38_treatment_eval.py` 與 ROUND.md 機制
  （`output/clip_treatment/rounds/`），本卡不改動該腳本。
- 門檻敏感度分析（表 7 型）在 round12（或最終輪）之後，用
  `t36_analysis.build_threshold_sensitivity()` 唯讀重算並收進 REPORT——
  候選變多會重分配所有面的機率（地雷 #13），必須重跑，不得沿用
  `round0_baseline`／`round11_remap_baseline` 的舊表。

## 5. 產品採用門檻（對 `round11_remap_baseline`，繼承卡片原文）

round12（若不需調整）或 round13／round14（若有調整，取最後一輪）
**必須同時**滿足：
1. overall 上升；2. floor 不下降；3. 原 62 個非 proxy 面正確數不下降。

三者不能同時滿足 → 不採用新候選，`surfaces.py` 新增條目還原（其餘 9
候選＋既有 12 條提示詞逐字不動）；`materials.json` 新增資料**保留**
（有出處的資料本身有價值）；ground truth 重對映**保留不回滾**（真實
就是真實）。REPORT.md 誠實記錄。

若同時滿足 → 採用該輪的新增候選作為 `surfaces.py` 正式內容並 commit，
跑基線變化表（共同鐵則 8）＋臥室紅旗檢查（共同鐵則 7）。

## 6. round12 結果與 round13 決策（round12 跑完後補寫，早於 round13 執行）

**round12_expanded 實測**：overall 28/76（round11 為 30/76，**下降**）、floor
4/13（持平）、in-set 誤判 10（round11 為 9，**上升**）。逐面追查（讀
`runs/*/detail.json` 的 `top3`/`sources`，非手打）：

- **結構性發現（決定性，非用詞問題）**：`bathroom_tiled.ceiling` 與
  `site_photo_gym.ceiling` 兩個面在 `detail.json` 的 `sources`／`faces` 完全
  沒有 `ceiling` 鍵——ADE20K 分割階段就沒偵測到 ceiling 角色像素
  （`ratio < config.MIN_SURFACE_AREA_RATIO`），CLIP **從未被呼叫**。這是
  分割階段的缺口，不是 CLIP 候選/提示詞能碰到的範圍（T-39 範圍紅線本來就
  不准動分割邏輯）。也就是說 `vinyl_panel` 與 `metal_roof_deck` 兩個新
  候選的**自身目標面在本 13 張資料集裡結構性不可達**——不管字串怎麼調，
  這兩面永遠不可能被判對。
- `site_photo_gym.floor`（`rubber_flooring` 的目標面）**成功修正**：
  `clip` 來源、信心 0.543，top3 為
  `[rubber_flooring 0.543, acoustic_panel 0.250, concrete 0.090]`。這是
  唯一一個目標面真的可達且修正成功的案例。
- **新副作用（地雷 #13 型，softmax 重分配）**：
  - `SteinmanHall.ceiling` 從正確（`curtain_fabric`）翻成錯誤
    （`metal_roof_deck`，信心 0.718，`top3=[metal_roof_deck 0.718,
    curtain_fabric 0.165, acoustic_panel 0.043]`）——單一候選搶答信心
    最高的一起side effect。
  - `RacquetballCourt4.south` 從正確（`glass`）翻成錯誤（`vinyl_panel`，
    信心 0.532，`top3=[vinyl_panel 0.532, glass 0.216, gypsum_board
    0.062]`）。
  - `RacquetballCourt4.floor` 從正確（`wood_panel`，clip 信心足夠）翻成
    `fallback`（`top3=[rubber_flooring 0.388, wood_panel 0.247,
    vinyl_panel 0.171]`，top1 機率被 `rubber_flooring` 拉到門檻 0.4 以下）。

**round13 決策（事前規則，不是跑完才選）**：既然 `metal_roof_deck` 與
`vinyl_panel` 的自身目標面結構性不可達，調字串**不可能**讓它們自己變成
淨正貢獻，唯一還值得驗證的是「能不能至少把已觀測到的副作用（搶答）壓
下去」。取本輪信心最高的單一搶答（`SteinmanHall.ceiling`，`metal_roof_deck`
信心 0.718，全部副作用中最高）作為 round13 目標，只改 `metal_roof_deck`
一個候選（單一變因，比照 T-38B 規則），字串改為強調「硬質金屬光澤／
非布料」以降低與絨布垂墜的視覺混淆：

```
"a rigid painted sheet metal surface with visible corrugated or ribbed
ridges and a dull metallic sheen, not fabric or cloth"
```

若 round13 後 `SteinmanHall.ceiling` 恢復正確且未在別處製造新副作用 →
round14 比照方式處理 `vinyl_panel` 對 `RacquetballCourt4.south` 的搶答；
若 round13 沒有改善或製造更多副作用 → 停止調整（round14 不跑，預算未
用完是因為已有充分證據判定字串調整這條路無法讓兩個結構性不可達的候選
變成淨正貢獻），直接進入 §5 產品採用門檻判定與 REPORT。

## 7. round13 結果與 round14 決策（round13 跑完後補寫，早於 round14 執行）

**round13 實測**：overall 29/76（round12 為 28/76，回升 1；仍比 round11 的
30/76 少 1）、floor 4/13（持平）、in-set 誤判 9（round12 為 10，**回到
round11 水準**）。逐面核對（`runs/SteinmanHall/detail.json`）：

- `SteinmanHall.ceiling` **恢復正確**：`curtain_fabric`，clip 信心 0.571，
  `top3=[curtain_fabric 0.571, acoustic_panel 0.148, vinyl_panel 0.132]`——
  round13 改的 `metal_roof_deck` 字串加入「not fabric or cloth」後不再
  搶答，且**未在其他面新增副作用**（T-33 差異清單從 round12 的 5 張降到
  4 張，少的正是 SteinmanHall）。
- 符合 §6 預先寫死的條件（「round13 後 `SteinmanHall.ceiling` 恢復正確且
  未在別處製造新副作用 → round14 處理 `vinyl_panel`」），進入 round14。
- **round13 未解決、留給 round14 或最終報告的殘留副作用**（與
  `metal_roof_deck` 無關，round13 本來就不改這兩個候選）：
  `RacquetballCourt4.south`（`vinyl_panel` 搶走 `glass`，信心 0.548）、
  `RacquetballCourt4.floor`（`rubber_flooring` 把 `wood_panel` 信心拉到
  門檻下，fallback 判成 `gypsum_board`）。

**round14 決策（事前規則）**：只改 `vinyl_panel` 一個候選（單一變因），
針對它與 `glass` 的混淆——現有字串「glossy...non-porous」的 "glossy"
可能與玻璃的光澤語意重疊，且沒有明示「不透明/不透光」與玻璃區隔。
改法：

```
"a smooth opaque plastic or vinyl panel surface with a slight sheen,
not glass and not transparent"
```

`rubber_flooring` 對 `RacquetballCourt4.floor` 的副作用**不在本輪調整
範圍**——round14 跑完即用完 PLAN §4 的 2 輪調整預算上限，若 round14 後仍
未同時達成 §5 的三個產品採用門檻，直接停止並進入誠實 REPORT（不得為了
達標超預算加輪次）。
