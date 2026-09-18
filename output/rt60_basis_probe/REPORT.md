# T-58 REPORT：Sabine vs Eyring vs 幾何聲學（pra）參考 vs 產品合成路徑

## §0 摘要

本卡只量不改、不下產品決定（歸 Fable，R2 之後）。Part A 在合成的 4×3×2.5m 三條件房間（沿用 T-56 首跑的 30 條 pra IR，未重生）比較 Sabine／Eyring 公式值與 pra 幾何聲學量測值、以及產品 `ir_synth` 合成 IR 的 T30；Part B 在 T-17 手動組 5 個真實場地上，額外加入真實 IR（`output/mvp_acceptance/rt60_table.json` 的 `real_reference`）當比較基準。事前登記的假設H1～H4 判定見 §1，數字全部引用下方表 A／B／C（表格程式產出，見 `tables.md`）。

**結果**：H1 不支持｜H2 支持｜H3 不支持｜H4 不支持；表 C 5 場地判準頻段誤差絕對值中位數四個基準由小到大：sabine 0.4738、product 0.4793、eyring 0.5386、pra_median 0.8643。

## §1 假設 H1～H4 逐條判定

- **H1**：不支持——per-wall 偏差 -33.4%（為負或零）；六面 gypsum 偏差 -53.7%、六面 carpet 偏差 -30.8%（絕對值未皆小於 per-wall 絕對值 33.4%）。
- **H2**：支持——per-wall 的 Eyring 相對 pra 偏差 -37.9%，與 Sabine 偏差 -33.4% 同號（Eyring 未消除非均勻偏差）。
- **H3**：不支持——5 場地判準頻段誤差絕對值中位數：pra_median=0.8643 vs sabine=0.4738（未下降）。MIT 3 場地子集（🟡 弱證據，樣本小）：pra_median=1.1272 vs sabine=0.4738（未下降；與 5 場地方向一致）。
- **H4**：不支持——Part A 產品路徑 vs 自身 Sabine 目標，多數頻段（＞半數；6 帶需 ≥4 帶）在 ±20% 內：per_wall：4/6 頻段在 ±20% 內；control_gypsum：4/6 頻段在 ±20% 內；control_carpet：1/6 頻段在 ±20% 內。三條件合併 9/18（＝半數；僅供參考，不是判定式）。Part B 佐證（沿用 T-17 各場地既有 `analysis.json.closed_loop`；本卡**未**重量）：mit_department_store 5/6；mit_gym 5/6；mit_restaurant 6/6；racquetball_court_4 6/6；steinman_hall 6/6。

## §2 限制

- 聯合帶（88.4–353.6Hz）沒有 Sabine/Eyring 公式對應，本卡取 125Hz／250Hz 兩帶公式值**平均**近似（不是量測 IR 的聯合帶濾波，只用於 Sabine/Eyring 欄；pra_median／product／real欄的聯合帶仍是 `ir_metrics.t30_low_combined()` 對整條 IR 的真實量測，兩種計算方式不可直接當同一件事比較細節，只看方向與量級）。
- pra 的 image-source + ray tracing 本身是一個模型，不是真值；Part A 沿用 T-56 首跑（已鎖定，不可重跑），Part B 為本卡新模擬（seed 1001–1005，5 次取中位數），兩者都可能與更精細的聲學模型有落差。
- MIT 三場地（`mit_gym`／`mit_restaurant`／`mit_department_store`）在 Part B 判準頻段比較中另外用區間中位數列出，樣本只有 3 場地、15 個誤差值，弱證據，標 🟡（沿用 T-17 慣例）。
- Part B 手動尺寸與材質判定是 Opus 於 T-17 執行時的人工估計（見各 `t17_manual_*/analysis.json``notes`／`warnings`），不是實測值。
- Part B 的「產品」欄是 T-17 HEAD 時生成的既有 `ir_mono.wav`（未重生），與 Part A 的「產品」欄（本卡用當前 HEAD 的 `ir_synth.synthesize_ir()` 重新合成）不是同一次生成，兩者不可跨 Part 直接比較生成環境。
- **R4**：Part A 的 pra 參考（T-56 首跑、已鎖定不可重生）位置＝聲源 [1.0, 1.0, 1.5]／麥克風 [3.0, 2.0, 1.2]（`gen_ir_manual.PRESETS["small"]`），與產品 `ir_synth._source_mic_positions(4,3,2.5)`＝聲源 [1.0, 0.99, 1.5]／麥克風 [3.0, 2.01, 1.25] 不同（各軸最大差 5.0 cm，麥克風 z）；Part B 的 pra 房間用的就是 `_source_mic_positions`（一致）；本卡**未量化**此差異對 T30 的影響（T30 是晚期衰減斜率，預期影響小；但未驗證）。

## §3 給 Fable 的決策輸入（只列選項與證據，不下決定）

- **(a) 基準比較**：5 場地判準頻段誤差絕對值中位數 sabine=0.4738、eyring=0.5386、pra_median=0.8643（MIT 子集見表 C）。現有證據不支持把 `IR_RT60_BASIS` 由 sabine 換成 eyring 或 pra 量測值（sabine ≤ eyring 且 sabine ≤ pra_median）。此為證據陳述，不是產品決定；決定歸 Fable，T-17-R2 之後。
- **(b) pra 參考本身的可信度**（逐場地，程式產生）：
  - mit_department_store：preset（max_order=4／n_rays=140000），判準頻段 (pra−real)/real 範圍 +86.4%～+189.6%，全為正
  - mit_gym：preset（max_order=12／n_rays=20000），判準頻段 (pra−real)/real 範圍 -16.1%～+39.6%，有正有負
  - mit_restaurant：preset（max_order=4／n_rays=140000），判準頻段 (pra−real)/real 範圍 +142.7%～+371.1%，全為正
  - racquetball_court_4：preset（max_order=4／n_rays=140000），判準頻段 (pra−real)/real 範圍 -61.2%～-37.4%，全為負
  - steinman_hall：preset（max_order=4／n_rays=140000），判準頻段 (pra−real)/real 範圍 +70.9%～+135.1%，全為正
  `max_order=4` 的場地共 4 個，其中 3 個五格全為正，範圍 +70.9%～+371.1%。
- **(c) H1／H2 的實際意涵**：三條件 Sabine 相對 pra 的聯合帶偏差全為負（per_wall -33.4%、control_gypsum -53.7%、control_carpet -30.8%）——「Sabine 在非均勻房間相對幾何聲學參考偏長」未獲支持；H2 的「同號」只表示 Eyring 與 Sabine 同向偏短，在 H1 前提不成立下不具原假設的含意。
- **(d) H4 的實際意涵**：逐條件：per_wall 4/6（最大偏差頻段 125Hz +117.3%）；control_gypsum 4/6（最大偏差頻段 125Hz +166.8%）；control_carpet 1/6（最大偏差頻段 500Hz +395.6%）。Part B 既有 `closed_loop`：mit_department_store 5/6（超差：500Hz +50.8%）；mit_gym 5/6（超差：125Hz +30.4%）；mit_restaurant 6/6；racquetball_court_4 6/6；steinman_hall 6/6。已知機制＝T-14 裁決／T-17 裁決 B 記錄的『陡峭頻段階梯下的鄰帶耦合』；control_carpet 是極端案例，且六面地毯是地雷 #9 明列的不現實模型；本卡**未**重新驗證機制歸因（保留號 T-59）。對決策的含意：『產品 T30≈Sabine 目標』不是無條件成立，產品對真實 IR 的誤差除了材質誤差與 Sabine 偏差，還可能含這一項。

## §4 可重跑指令

```bash
source .venv/bin/activate
python scripts/t58_rt60_basis_probe.py manifest
python scripts/t58_rt60_basis_probe.py partA
python scripts/t58_rt60_basis_probe.py partB
python scripts/t58_rt60_basis_probe.py report
```
