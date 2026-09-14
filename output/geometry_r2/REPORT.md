# T-48 A 部分 — T-11 域外出口無誤放重驗（判準 v2）

> 產生日期：2026-09-14T07:26:53.195820+00:00　git_head：`714703db7419863bb0f8c2b6b36ce213f9259ce0`　git status --porcelain -- src data scripts：(空)

判準 v2（事前鎖定，見 TASKS.md T-48 卡 §8）：實際最大維 >10m 的照片，`geometry_confidence` 必須為 low 且 gate 訊息含 `--override-dims` 導引；實際 ≤10m 且有 ground truth 的照片誤差 ≤ ±30%（目前只有浴室）。任一域外照片拿到 medium／high＝域外出口誤放，記 FAIL。

## 0. 結論

**FAIL——有域外誤放或浴室誤差超標**（FAIL 筆數：1）

## 1. 逐張結果（全部 13 張，沒有只挑好看的）

| 照片 | 估計 L×W×H (m) | 最大維 | dims_source | geometry_confidence | override-dims 導引 | v2 類別 | 判定 | 細節 |
|---|---|---|---|---|---|---|---|---|
| bathroom_tiled | 3.72×4.30×4.27 | 4.30 | metric_depth | medium | 無 | domain_in_with_ground_truth | PASS | 實際進深 3.0m（範圍 [2.5, 3.5]），估計進深 3.72m，誤差 +24.0%（判準 ≤±30%） |
| bedroom_ai_generated | 5.39×6.23×3.89 | 6.23 | metric_depth | medium | 無 | unknown_no_ground_truth | 不適用（未知，不列入 v2 判定） | 無已知實際尺寸，僅記錄估計值供參考，不列入 FAIL/PASS 判定。 |
| stairwell_tiled | 6.28×7.25×9.08 | 9.08 | metric_depth | medium | 無 | unknown_no_ground_truth | 不適用（未知，不列入 v2 判定） | 無已知實際尺寸，僅記錄估計值供參考，不列入 FAIL/PASS 判定。 |
| arena_ntsu_linkou | 3.33×3.85×2.40 | 3.85 | metric_depth | low | 有 | domain_out | PASS | 實際最大維 150.0m >10m，要求 geometry_confidence=low 且 gate 訊息含 --override-dims 導引；實測 geometry_confidence=low，override-dims 導引=有 |
| car_interior_suv | 7.22×8.33×5.52 | 8.33 | metric_depth | low | 有 | not_applicable | 不適用 | 實際 ~2m，不 >10m 故不落入域外項；卡片原文「目前只有浴室」明示「≤10m 且有 ground truth」誤差判準只適用浴室一張，車內不在兩類別判準內——僅記錄估計值供參考，不列入 FAIL/PASS 判定。 |
| CathedralRoom | 8.42×14.14×4.97 | 14.14 | equirect_multiview | medium | 無 | unknown_no_ground_truth | 不適用（未知，不列入 v2 判定） | 無已知實際尺寸，僅記錄估計值供參考，不列入 FAIL/PASS 判定。 |
| DivorceBeach | 16.79×14.71×8.83 | 16.79 | equirect_multiview | low | 有 | unknown_no_ground_truth | 不適用（未知，不列入 v2 判定） | 無已知實際尺寸，僅記錄估計值供參考，不列入 FAIL/PASS 判定。 |
| site_photo_department_store | 6.04×6.97×3.92 | 6.97 | metric_depth | medium | 無 | unknown_no_ground_truth | 不適用（未知，不列入 v2 判定） | 無已知實際尺寸，僅記錄估計值供參考，不列入 FAIL/PASS 判定。 |
| site_photo_gym | 5.01×5.79×3.26 | 5.79 | metric_depth | low | 有 | unknown_no_ground_truth | 不適用（未知，不列入 v2 判定） | 無已知實際尺寸，僅記錄估計值供參考，不列入 FAIL/PASS 判定。 |
| site_photo_restaurant | 2.77×3.20×2.00 | 3.20 | metric_depth | low | 有 | unknown_no_ground_truth | 不適用（未知，不列入 v2 判定） | 無已知實際尺寸，僅記錄估計值供參考，不列入 FAIL/PASS 判定。 |
| RacquetballCourt4 | 16.10×9.39×5.55 | 16.10 | equirect_multiview | medium | 無 | domain_out | FAIL | 實際最大維 12.19m >10m，要求 geometry_confidence=low 且 gate 訊息含 --override-dims 導引；實測 geometry_confidence=medium，override-dims 導引=無 |
| SteinmanHall | 17.45×21.48×6.89 | 21.48 | equirect_multiview | low | 有 | domain_out | PASS | 實際最大維 12.2m >10m，要求 geometry_confidence=low 且 gate 訊息含 --override-dims 導引；實測 geometry_confidence=low，override-dims 導引=有 |
| TunnelToHell | 15.76×18.19×9.53 | 18.19 | metric_depth | low | 有 | unknown_no_ground_truth | 不適用（未知，不列入 v2 判定） | 無已知實際尺寸，僅記錄估計值供參考，不列入 FAIL/PASS 判定。 |

## 2. 觸發的量程／場景線索規則（讀自 `--force-low-confidence` 重跑的 analysis.json warnings，只為了印出「觸發哪條規則」的細節，不影響／不重算 gate 判定本身——判定一律依上表的預設路徑真實 CLI 輸出）

| 照片 | 觸發規則 |
|---|---|
| bathroom_tiled | （無，或全部規則皆未觸發 low） |
| bedroom_ai_generated | （無，或全部規則皆未觸發 low） |
| stairwell_tiled | （無，或全部規則皆未觸發 low） |
| arena_ntsu_linkou | floor_visibility |
| car_interior_suv | out_of_domain_material |
| CathedralRoom | （無，或全部規則皆未觸發 low） |
| DivorceBeach | scope_max_10m |
| site_photo_department_store | （無，或全部規則皆未觸發 low） |
| site_photo_gym | out_of_domain_material |
| site_photo_restaurant | floor_visibility |
| RacquetballCourt4 | （無，或全部規則皆未觸發 low） |
| SteinmanHall | scope_max_10m |
| TunnelToHell | scope_max_10m、out_of_domain_material |

## 3. 已知實際尺寸對照表

| 照片 | 已知實際尺寸 | v2 類別 | 說明 |
|---|---|---|---|
| bathroom_tiled | [2.5, 3.5] | domain_in_with_ground_truth | 唯一落入 v2「≤10m 且有 ground truth」誤差 ±30% 判準的照片（卡片原文「目前只有浴室」）。 |
| bedroom_ai_generated | 未知 | unknown_no_ground_truth | 無已知實際尺寸，僅記錄估計值供參考 |
| stairwell_tiled | 未知 | unknown_no_ground_truth | 無已知實際尺寸，僅記錄估計值供參考 |
| arena_ntsu_linkou | 150.0 | domain_out | 體育館，實際最大維 ~150m，落入 v2 域外項（>10m 必須 low＋override-dims 導引）。 |
| car_interior_suv | 2.0 | not_applicable | 實際 ~2m，不 >10m 故不落入域外項；卡片原文「目前只有浴室」明示「≤10m 且有 ground truth」誤差判準只適用浴室一張，車內不在兩類別判準內——僅記錄估計值供參考，不列入 FAIL/PASS 判定。 |
| CathedralRoom | 未知 | unknown_no_ground_truth | 無已知實際尺寸，僅記錄估計值供參考 |
| DivorceBeach | 未知 | unknown_no_ground_truth | 無已知實際尺寸，僅記錄估計值供參考 |
| site_photo_department_store | 未知 | unknown_no_ground_truth | 無已知實際尺寸，僅記錄估計值供參考 |
| site_photo_gym | 未知 | unknown_no_ground_truth | 無已知實際尺寸，僅記錄估計值供參考 |
| site_photo_restaurant | 未知 | unknown_no_ground_truth | 無已知實際尺寸，僅記錄估計值供參考 |
| RacquetballCourt4 | [12.19, 6.1, 6.1] | domain_out | 壁球場，實際 12.19×6.10×6.10m，最大維 12.19m >10m，落入 v2 域外項。 |
| SteinmanHall | [12.2, 10.4, 5.25, 11.1] | domain_out | 環景音樂廳，實測牆距 12.2/10.4/5.25/11.1m，最大單面牆距 12.2m >10m，落入 v2 域外項（環景走單面牆距判定，見 geometry.py apply_scope_confidence）。 |
| TunnelToHell | 未知 | unknown_no_ground_truth | 無已知實際尺寸，僅記錄估計值供參考 |

## 4. 域外誤放根因（程式判定：v2_category=domain_out 且 verdict=FAIL 的每一筆）

### RacquetballCourt4

實際最大維 12.19m（壁球場，實際 12.19×6.10×6.10m，最大維 12.19m >10m，落入 v2 域外項。），但預設路徑實測 `geometry_confidence=medium`（非 low），gate 未印 `--override-dims` 導引。程式重跑 `--force-low-confidence` 版讀出的 warnings 不含「超出已驗證量程」字樣（觸發規則：無）。

根因（讀 `src/image_reverb/geometry.py` `apply_scope_confidence()` 唯讀確認，本卡未改動該函式）：環景量程規則檢查的是**單一視角的原始牆距**（`wall_distances_m` 逐值比對 `GEOMETRY_SCOPE_MAX_M`），不是相加後的房間全長——這是刻意設計（避免對牆相加把有效上限拉高到約 40m，見該函式 docstring）。但代價是：當房間的實際全長 >10m、卻是由兩側**個別皆 ≤10m** 的視角相加而成時（本例估計 16.10×9.39×5.55m，沒有任何單一視角讀數本身超過 10m），量程規則不會觸發，`geometry_confidence` 停在 medium——這正是 v2 判準想抓的「域外出口誤放」，如實記為 FAIL，不得用附註豁免（WORKFLOW §5.4.1）。



## 5. 方法

每張照片跑兩次真實 CLI（`python -m src.image_reverb <photo> --no-viz`）：
1. 先加 `--force-low-confidence` 跑一次，只為了讀 `output/<stem>/analysis.json` 的完整 `warnings`（量程/場景線索規則的詳細文字），不影響任何判定。
2. 再跑一次**不帶任何旗標**（真正的預設 production 路徑），這次的 stdout/stderr 才是 gate 判定與 `--override-dims` 導引訊息的真實來源——v2 判準完全依這次輸出判定。

13 張照片清單與路徑唯一來源：`scripts/t36_clip_accuracy.GATE_ITEMS`（不重打）。逐張原始 CLI 輸出存於 `output/geometry_r2/runs/<name>/{default,force_low_confidence}.log`。

