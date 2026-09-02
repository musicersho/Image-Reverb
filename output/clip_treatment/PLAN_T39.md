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
