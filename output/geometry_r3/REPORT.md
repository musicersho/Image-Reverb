# T-55 A 部分 — T-11 域外出口 v3 重驗（判準 v3；裁決 T-48-F 第 1／3 點）

> 產生日期：2026-09-15T08:04:52.976021+00:00　git_head：`2048a6c4fd1a4ba0b0160fb3f5989310df4904ea`　git status --porcelain -- src data scripts：(空)

判準 v3（事前鎖定，見 `output/geometry_r3/CRITERIA_T11_v3.md`，commit `b80a4fb`）：只做三件事——`car_interior_suv` 改歸 `domain_out_non_room`、資料集加回 `corridor_hotel_carpet.png`（14 張）、加 V5 情境；>10m 域外項與浴室 ±30% 條文與數字一字不改。`domain_out`／`domain_out_non_room` 判定公式相同（`geometry_confidence` 必須為 low 且 gate 訊息含 `--override-dims` 導引），只有敘述文字不同，前置 T-54（幾何量程規則 v2）已由 Opus 驗證工程通過（`4a9206f`）。

## 0. 結論

**PASS——domain_out 4/4＋domain_out_non_room 1/1＋浴室＋V5 全部成立**（domain_out：4/4；domain_out_non_room：1/1；浴室：PASS；V5：PASS）

## 1. 逐張結果（全部 14 張，沒有只挑好看的）

| 照片 | 估計 L×W×H (m) | 最大維 | dims_source | geometry_confidence | materials_confidence | 已擋下 | 擋在哪軸 | override-dims 導引 | v3 類別 | 判定 | 細節 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bathroom_tiled | 3.72×4.30×4.27 | 4.30 | metric_depth | medium | low | 是 | materials | 無 | domain_in_with_ground_truth | PASS | 實際進深 3.0m（範圍 [2.5, 3.5]），估計進深 3.72m，誤差 +24.0%（判準 ≤±30%） |
| bedroom_ai_generated | 5.39×6.23×3.89 | 6.23 | metric_depth | medium | low | 是 | materials | 無 | unknown_no_ground_truth | 不適用（未知，不列入 v3 判定） | 無已知實際尺寸，僅記錄估計值供參考，不列入 FAIL/PASS 判定。 |
| stairwell_tiled | 6.28×7.25×9.08 | 9.08 | metric_depth | medium | low | 是 | materials | 無 | unknown_no_ground_truth | 不適用（未知，不列入 v3 判定） | 無已知實際尺寸，僅記錄估計值供參考，不列入 FAIL/PASS 判定。 |
| arena_ntsu_linkou | 3.33×3.85×2.40 | 3.85 | metric_depth | low | low | 是 | geometry、materials | 有 | domain_out | PASS | 實際最大維 >10m（實際最大維 150.0m），要求 geometry_confidence=low 且 gate 訊息含 --override-dims 導引；實測 geometry_confidence=low，override-dims 導引=有 |
| car_interior_suv | 7.22×8.33×5.52 | 8.33 | metric_depth | low | low | 是 | geometry、materials | 有 | domain_out_non_room | PASS | 非房間空間，依 v3 判準與 >10m 域外同款：估計誤差只記錄不判（實際最大維 2.0m），要求 geometry_confidence=low 且 gate 訊息含 --override-dims 導引；實測 geometry_confidence=low，override-dims 導引=有 |
| CathedralRoom | 8.42×14.14×4.97 | 14.14 | equirect_multiview | low | low | 是 | geometry、materials | 有 | unknown_no_ground_truth | 不適用（未知，不列入 v3 判定） | 無已知實際尺寸，僅記錄估計值供參考，不列入 FAIL/PASS 判定。 |
| DivorceBeach | 16.79×14.71×8.83 | 16.79 | equirect_multiview | low | medium | 是 | geometry | 有 | unknown_no_ground_truth | 不適用（未知，不列入 v3 判定） | 無已知實際尺寸，僅記錄估計值供參考，不列入 FAIL/PASS 判定。 |
| site_photo_department_store | 6.04×6.97×3.92 | 6.97 | metric_depth | medium | low | 是 | materials | 無 | unknown_no_ground_truth | 不適用（未知，不列入 v3 判定） | 無已知實際尺寸，僅記錄估計值供參考，不列入 FAIL/PASS 判定。 |
| site_photo_gym | 5.01×5.79×3.26 | 5.79 | metric_depth | low | low | 是 | geometry、materials | 有 | unknown_no_ground_truth | 不適用（未知，不列入 v3 判定） | 無已知實際尺寸，僅記錄估計值供參考，不列入 FAIL/PASS 判定。 |
| site_photo_restaurant | 2.77×3.20×2.00 | 3.20 | metric_depth | low | low | 是 | geometry、materials | 有 | unknown_no_ground_truth | 不適用（未知，不列入 v3 判定） | 無已知實際尺寸，僅記錄估計值供參考，不列入 FAIL/PASS 判定。 |
| RacquetballCourt4 | 16.10×9.39×5.55 | 16.10 | equirect_multiview | low | low | 是 | geometry、materials | 有 | domain_out | PASS | 實際最大維 >10m（實際最大維 12.19m），要求 geometry_confidence=low 且 gate 訊息含 --override-dims 導引；實測 geometry_confidence=low，override-dims 導引=有 |
| SteinmanHall | 17.45×21.48×6.89 | 21.48 | equirect_multiview | low | low | 是 | geometry、materials | 有 | domain_out | PASS | 實際最大維 >10m（實際最大維 12.2m），要求 geometry_confidence=low 且 gate 訊息含 --override-dims 導引；實測 geometry_confidence=low，override-dims 導引=有 |
| TunnelToHell | 15.76×18.19×9.53 | 18.19 | metric_depth | low | low | 是 | geometry、materials | 有 | unknown_no_ground_truth | 不適用（未知，不列入 v3 判定） | 無已知實際尺寸，僅記錄估計值供參考，不列入 FAIL/PASS 判定。 |
| corridor_hotel_carpet | 12.79×14.76×14.69 | 14.76 | metric_depth | low | low | 是 | geometry、materials | 有 | domain_out | PASS | 實際最大維 >10m（實際最大維 30.0m），要求 geometry_confidence=low 且 gate 訊息含 --override-dims 導引；實測 geometry_confidence=low，override-dims 導引=有 |

## 2. V5 情境（RacquetballCourt4 覆寫兩面材質，判準 v3）

| 指令 | exit code | override-dims 導引 | 判定 |
|---|---|---|---|
| `python -m src.image_reverb assets/reference_irs/racquetball_court_4/RacquetballCourt4.jpg --override-material north=gypsum_board --override-material ceiling=wood_panel --no-viz` | 3 | 有 | PASS |

（v3 判準要求 exit=3 且含 `--override-dims` 導引；exit=0＝FAIL，複現 T-54 修復前的域外安全缺口。完整 stdout/stderr 見 `output/geometry_r3/runs/V5_RacquetballCourt4_override_material/v5.log`。）


## 3. 已知實際尺寸對照表（v3）

| 照片 | 已知實際尺寸 | v3 類別 | 說明 |
|---|---|---|---|
| bathroom_tiled | [2.5, 3.5] | domain_in_with_ground_truth | 唯一落入 v2「≤10m 且有 ground truth」誤差 ±30% 判準的照片（卡片原文「目前只有浴室」）。 |
| bedroom_ai_generated | 未知 | unknown_no_ground_truth | 無已知實際尺寸，僅記錄估計值供參考 |
| stairwell_tiled | 未知 | unknown_no_ground_truth | 無已知實際尺寸，僅記錄估計值供參考 |
| arena_ntsu_linkou | 150.0 | domain_out | 體育館，實際最大維 ~150m，落入 v2 域外項（>10m 必須 low＋override-dims 導引）。 |
| car_interior_suv | 2.0 | domain_out_non_room | SUV 車廂，實際最大維 ~2m（非房間空間）。v2 判準文字自相矛盾記 inconclusive（見上，Opus 更正 2026-09-14）；依裁決 T-48-F 第 3 點與 T-11 原卡步驟 5「車內與超大空間允許數字不準」，v3 改歸類 domain_out_non_room：與 >10m 域外同款判準（geometry_confidence 必須 low 且 gate 訊息含 --override-dims 導引），估計誤差只記錄不判。 |
| CathedralRoom | 未知 | unknown_no_ground_truth | 無已知實際尺寸，僅記錄估計值供參考 |
| DivorceBeach | 未知 | unknown_no_ground_truth | 無已知實際尺寸，僅記錄估計值供參考 |
| site_photo_department_store | 未知 | unknown_no_ground_truth | 無已知實際尺寸，僅記錄估計值供參考 |
| site_photo_gym | 未知 | unknown_no_ground_truth | 無已知實際尺寸，僅記錄估計值供參考 |
| site_photo_restaurant | 未知 | unknown_no_ground_truth | 無已知實際尺寸，僅記錄估計值供參考 |
| RacquetballCourt4 | [12.19, 6.1, 6.1] | domain_out | 壁球場，實際 12.19×6.10×6.10m，最大維 12.19m >10m，落入 v2 域外項。 |
| SteinmanHall | [12.2, 10.4, 5.25, 11.1] | domain_out | 環景音樂廳，實測牆距 12.2/10.4/5.25/11.1m，最大單面牆距 12.2m >10m，落入 v2 域外項（環景走單面牆距判定，見 geometry.py apply_scope_confidence）。 |
| TunnelToHell | 未知 | unknown_no_ground_truth | 無已知實際尺寸，僅記錄估計值供參考 |
| corridor_hotel_carpet | 30.0 | domain_out | 旅館走廊，實際長度約 30m（T-11 原卡九張清單原有的域外案例，首次量測估 12.79m、誤差 −57%；T-36 起沿用至今的 13 張 canonical 清單已不含此照片）。依裁決 T-48-F 第 3 點補回，落入 v3 域外項（>10m 必須 low＋override-dims 導引）。 |

## 4. 與 v2 的差異（僅這三處，其餘條文與數字一字不改）

1. `car_interior_suv`：v2 記 inconclusive（判準文字自相矛盾，見 T-48 卡裁決 F3）→ v3 改歸 `domain_out_non_room`，與 >10m 域外同款判準（`geometry_confidence` 必須 low 且 override-dims 導引）；
2. 資料集加回 `corridor_hotel_carpet.png`（T-11 原卡九張清單案例，T-36 起 13 張 canonical 清單已不含）→ 14 張，歸 `domain_out`；
3. 新增 V5 情境（RacquetballCourt4 覆寫兩面材質）——T-54（`4a9206f`，已驗證）已修復此域外安全缺口，本卡驗證修復後的行為。


## 5. 方法

每張照片跑兩次真實 CLI（`python -m src.image_reverb <photo> --no-viz`）：先加 `--force-low-confidence` 讀一次完整 stdout `warnings`（不影響判定），再跑一次不帶任何旗標的真正預設路徑，v3 判定完全依此次輸出。14 張清單＝`scripts/t36_clip_accuracy.GATE_ITEMS`（13 張，唯讀引用，不重打）＋`assets/photos/corridor_hotel_carpet.png`。V5 情境額外跑一次`--override-material` 組合。逐張與 V5 的原始 CLI 輸出存於 `output/geometry_r3/runs/<name>/{default,force_low_confidence}.log` 與 `output/geometry_r3/runs/V5_RacquetballCourt4_override_material/v5.log`（gitignored，不進版控）。

