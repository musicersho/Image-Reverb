# CRITERIA — geometry scope v2（量程規則：環景分支加三維檢查）

version: geometry scope v2
scope: 兩模式共用（geometry 不吃 role_aware）；只動 apply_scope_confidence() 的 equirect_multiview 分支；metric_depth／manual 分支不變
approved_by: 使用者（2026-09-15，於 Fable 視窗對 TASKS.md T-54 卡草案全文回「T-54 核准」）；提案者 Opus（T-48 驗證紀錄 F1／V5，2026-09-14）、起草 Fable（裁決 T-48-F，2026-09-14）
evidence: T-48 結果 commit 012a07f（output/geometry_r2/REPORT.md 表 1：RacquetballCourt4 16.10×9.39×5.55m／medium／無導引；
          CathedralRoom 8.42×14.14×4.97m／medium）；Opus V5 實測（覆寫兩面材質後 exit 0）；output/gate_calibration_v2/tables.md 表 1
執行卡: T-54（TASKS.md）；本檔 commit 必須早於 T-54 任何結果 commit（WORKFLOW §7.2）

## rule G2（逐字；T-54 實作不得與此不同義）

G2（量程規則 v2，兩模式共用；dims_source == "equirect_multiview" 分支）：保留現行「任一單面牆距 > GEOMETRY_SCOPE_MAX_M」檢查，另加「length_m／width_m／height_m 任一 > GEOMETRY_SCOPE_MAX_M」檢查（與 metric_depth 分支同式）；任一命中 → confidence: low，notes 追加一條含「超出已驗證量程」字樣並列出命中的維度／牆距與數值；兩者皆命中時只記一條、把兩組明細合併列出。

metric_depth／manual／未知 dims_source 三個分支原文不動；GEOMETRY_SCOPE_MAX_M=10.0 不動、不新增常數；--override-dims 導引沿用 pipeline.py 既有條件（est.confidence == "low" 即印），不另加訊息分支。

## expected_on_13

與 output/gate_calibration_v2/tables.md 表 1 相比，兩模式 geometry 欄僅 CathedralRoom／RacquetballCourt4 medium→low（4 格）；
materials／overall／gate 三欄 26 格不變（兩張本已 materials low／overall low／BLOCK）；gate 13/13 BLOCK 兩模式不變；
surfaces／sources 26/26 不變

## expected_V5

RacquetballCourt4 --override-material north=gypsum_board --override-material ceiling=wood_panel → EXIT=3、stderr 含
「幾何不可信 → 用 --override-dims」（舊碼 exit 0）

## not_a_calibration

本版不宣稱 10m 門檻已校準；只把環景分支補齊到與透視照分支同一語意（估計三維任一 >10m ＝ 域外）

## supersedes

T-11 決策補丁步驟 7 的環景「只比單面牆距」設計（保留該檢查、加上三維檢查；GEOMETRY_SCOPE_MAX_M 不動）

## change control

criteria_version geometry scope v2 自本 commit 起鎖定；結果出來後不得修改本檔；如需改動＝geometry scope v3 新檔＋新獨立 commit＋使用者核准（WORKFLOW §7）。
