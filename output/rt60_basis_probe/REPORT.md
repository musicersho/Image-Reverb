# T-58 REPORT：Sabine vs Eyring vs 幾何聲學（pra）參考 vs 產品合成路徑

## §0 摘要

本卡只量不改、不下產品決定（歸 Fable，R2 之後）。Part A 在合成的 4×3×2.5m 三條件房間（沿用 T-56 首跑的 30 條 pra IR，未重生）比較 Sabine／Eyring 公式值與 pra 幾何聲學量測值、以及產品 `ir_synth` 合成 IR 的 T30；Part B 在 T-17 手動組 5 個真實場地上，額外加入真實 IR（`output/mvp_acceptance/rt60_table.json` 的 `real_reference`）當比較基準。事前登記的假設H1～H4 判定見 §1，數字全部引用下方表 A／B／C（表格程式產出，見 `tables.md`）。

## §1 假設 H1～H4 逐條判定

- **H1**：不支持——per-wall 偏差 -33.4%（為負或零）；六面 gypsum 偏差 -53.7%、六面 carpet 偏差 -30.8%（絕對值未皆小於 per-wall 絕對值 33.4%）。
- **H2**：支持——per-wall 的 Eyring 相對 pra 偏差 -37.9%，與 Sabine 偏差 -33.4% 同號（Eyring 未消除非均勻偏差）。
- **H3**：不支持——5 場地判準頻段誤差絕對值中位數：pra_median=0.8643 vs sabine=0.4738（未下降）。MIT 3 場地子集（🟡 弱證據，樣本小）：pra_median=1.1272 vs sabine=0.4738（方向不一致，未下降）。
- **H4**：不支持——Part A 產品路徑 vs 自身 Sabine 目標，多數頻段（≥半數）在 ±20% 內：per_wall：4/6 頻段在 ±20% 內；control_gypsum：4/6 頻段在 ±20% 內；control_carpet：1/6 頻段在 ±20% 內。Part B 佐證（沿用 T-17 各場地既有 `analysis.json.closed_loop`，未重量，僅重量一次做對照）：mit_department_store 5/6；mit_gym 5/6；mit_restaurant 6/6；racquetball_court_4 6/6；steinman_hall 6/6。

## §2 限制

- 聯合帶（88.4–353.6Hz）沒有 Sabine/Eyring 公式對應，本卡取 125Hz／250Hz 兩帶公式值**平均**近似（不是量測 IR 的聯合帶濾波，只用於 Sabine/Eyring 欄；pra_median／product／real欄的聯合帶仍是 `ir_metrics.t30_low_combined()` 對整條 IR 的真實量測，兩種計算方式不可直接當同一件事比較細節，只看方向與量級）。
- pra 的 image-source + ray tracing 本身是一個模型，不是真值；Part A 沿用 T-56 首跑（已鎖定，不可重跑），Part B 為本卡新模擬（seed 1001–1005，5 次取中位數），兩者都可能與更精細的聲學模型有落差。
- MIT 三場地（`mit_gym`／`mit_restaurant`／`mit_department_store`）在 Part B 判準頻段比較中另外用區間中位數列出，樣本只有 3 場地、15 個誤差值，弱證據，標 🟡（沿用 T-17 慣例）。
- Part B 手動尺寸與材質判定是 Opus 於 T-17 執行時的人工估計（見各 `t17_manual_*/analysis.json``notes`／`warnings`），不是實測值。
- Part B 的「產品」欄是 T-17 HEAD 時生成的既有 `ir_mono.wav`（未重生），與 Part A 的「產品」欄（本卡用當前 HEAD 的 `ir_synth.synthesize_ir()` 重新合成）不是同一次生成，兩者不可跨 Part 直接比較生成環境。

## §3 給 Fable 的決策輸入（只列選項與證據，不下決定）

- 若 H1／H2 成立（Sabine 對非均勻吸音房間系統性偏長、Eyring 不能消除）：`IR_RT60_BASIS` 若要換成 pra 幾何聲學量測值，需要另建「以量測值當目標」的合成路徑（目前 `ir_synth` 只吃公式值），屬於新開發工作，不是換一個字串常數。
- 若 H3 成立（pra 參考比 Sabine 更接近真實 IR 判準頻段）：方向上支持「以 pra 或其他幾何聲學量測值取代 Sabine 當合成目標」的假說，但 Part B 場地數少（5 場、MIT 子集僅 3 場），R2 held-out 資料回來後應一併重估。
- 若 H4 成立（產品路徑忠實反映 Sabine 目標）：現有「T-17 生成側誤差為正」的觀察，病因更可能是「Sabine 對真實房間本身的偏差」而非「產品合成環節额外引入誤差」；若 H4 不成立，則產品合成環節本身也可能是誤差來源之一，需要與材質誤差分開處理。

## §4 可重跑指令

```bash
source .venv/bin/activate
python scripts/t58_rt60_basis_probe.py manifest
python scripts/t58_rt60_basis_probe.py partA
python scripts/t58_rt60_basis_probe.py partB
python scripts/t58_rt60_basis_probe.py report
```
