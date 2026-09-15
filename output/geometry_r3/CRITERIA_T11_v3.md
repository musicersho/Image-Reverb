# CRITERIA — T-11 域外出口 v3

version: T-11 v3（T-48 A 部分 v2 的延續；域外項與浴室項條文與數字不變）
approved_by: 使用者（2026-09-15，於 Fable 視窗對 TASKS.md T-55 卡草案全文回「T-55 核准」）；起草 Fable（裁決 T-48-F 第 3 點，2026-09-14）
執行卡: T-55（TASKS.md）；前置 T-54 ✅（工程）；本檔 commit 必須早於 T-55 任何結果 commit（WORKFLOW §7.2）
dataset: canonical 13 張（t36_clip_accuracy.GATE_ITEMS）＋assets/photos/corridor_hotel_carpet.png ＝ 14 張；manifest 程式產生（output/geometry_r3/DATASET_MANIFEST.json）

## 類別與判準（每張恰一類）

domain_out（實際最大維 >10m）：arena_ntsu_linkou（~150m）、RacquetballCourt4（12.19m）、SteinmanHall（12.2m 牆距）、corridor_hotel_carpet（~30m）
  → geometry_confidence 必須 low 且 gate 訊息含 --override-dims 導引；任一拿到 medium/high ＝ 域外出口誤放 FAIL

domain_out_non_room（非房間）：car_interior_suv（~2m 車廂）→ 同 domain_out 要求（low＋導引）；估計誤差只記錄不判

domain_in_with_ground_truth（≤10m 有 ground truth）：bathroom_tiled → 誤差 ≤±30%

unknown_no_ground_truth：其餘 8 張 → 只記錄

## V5 情境

RacquetballCourt4 --override-material north=gypsum_board --override-material ceiling=wood_panel → 必須 EXIT=3 且含 --override-dims 導引；exit 0 ＝ FAIL

## verdict

domain_out 4/4＋domain_out_non_room 1/1＋浴室＋V5 全部成立才 PASS；任一不成立 FAIL（逐張列）

## change control

criteria_version T-11 v3 自本 commit 起鎖定；結果出來後不得修改本檔；改動＝v4 新檔＋獨立 commit＋使用者核准（WORKFLOW §7）。
