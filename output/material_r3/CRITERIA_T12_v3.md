# CRITERIA — T-12 v2-b 量測方法 v3

version: T-12 v3（門檻數字＝v2 不變：中位數差 ≤±20%、carpet ≥3×；只改量測方法）
approved_by: 使用者（2026-09-15，於 Fable 視窗對 TASKS.md T-56 卡草案回「T-56 守門條款 刪」＝核准其餘全文、刪除「方法有效性守門」條款）；起草 Fable（裁決 T-48-F 第 2 點，2026-09-14）；提案 Opus（T-48 驗證紀錄 F2，2026-09-14）
執行卡: T-56（TASKS.md）；本檔 commit 必須早於 T-56 任何結果 commit（WORKFLOW §7.2）

## seeds（事前鎖定，不得增減）

1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010

## conditions

per-wall（4×3×2.5m，floor=carpet／其餘 gypsum_board）、六面 gypsum_board、六面 carpet（與 T-12／T-48 同設定、同 preset、同 n_rays／time_thres）

## statistic

每條件 10 次 t30_low_combined()（88.4–353.6Hz）的中位數

## v2-b 判準

|median(per-wall) − median(gypsum)| / median(gypsum) ≤ 20% 且 median(carpet) ≥ 3 × median(per-wall)
（無方法有效性守門條款——使用者 2026-09-15 決定刪除；每條件 10 次的 min／max／(max−min)/median 仍須程式產表列出，只記錄、不改判定）

## v2-a

照量照列，標「非鑑別性（同義反覆，裁決 T-48-F 第 4 點）」，不計入 verdict

## v1 字面條件（125Hz 八度 ≈0.35s ±20%）

照量照列，只記錄不當門檻

## first_run_is_final

yes（任何重跑＝v4）

## change control

criteria_version T-12 v3 自本 commit 起鎖定；結果出來後不得修改本檔；改動＝v4 新檔＋獨立 commit＋使用者核准（WORKFLOW §7）。
