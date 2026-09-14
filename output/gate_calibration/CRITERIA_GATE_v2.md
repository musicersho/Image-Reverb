# CRITERIA — gate criteria v2（role_aware 模式）

version: gate v2
scope: 只作用於 role_aware=True；default 模式（role_aware=False）行為必須逐位元不變
approved_by: 使用者（2026-09-14，於 Fable 視窗以裁決 T-47-A 選項乙核准）；提案者 Fable（裁決 T-47-A，2026-09-14，docs commit a5f9e57）
evidence: T-47 結果 commit 5d1569c；dataset_manifest_sha256 c15d0a145f46ea0c6b4969fd995b5f2d543a13fb678f15671e792ae3df2b01a7；
          output/gate_calibration/tables.md 表 1～3／表 5／表 6／表 8
執行卡: T-52（TASKS.md）；本檔的 commit 必須早於 T-52 任何結果 commit（WORKFLOW §7.2）

## rule R1b（逐字；T-52 實作不得與此不同義）

R1b（只在 role_aware=True 時存在）：compute_materials_confidence() 在規則 1 之後、規則 2 之前加入——六面中任一面的來源為 "clip" 且該面的角色候選集為收窄子集（定義：len(ROLE_MATERIAL_CANDIDATES[role]) < len(CLIP_MATERIAL_PROMPTS)；現行 floor 6<12、ceiling 4<12 為收窄，wall 12=12 不收窄）→ low。

觸發時 warnings 加一條：「{面}：role_aware 收窄候選集（{role}，{n} 種）的 clip 判定未經校準（裁決 T-47-A），不計入放行；請改用預設模式（拿掉 --role-aware）或用 --override-material 覆寫」。

default 模式（role_aware=False）：所有面的候選集皆為全域集，R1b 永不觸發；規則 1～4 原文與順序不變。

與 T-47 ⑦(b) 模擬的差異：模擬只把 medium 降為 low；R1b 對 high 也生效（透視照結構上到不了 high，環景可以）。13 張兩模式無 high 案例，故 13 張結果與 tables.md 表 8 相同。

## expected_on_13

role_aware 13/13 BLOCK（bathroom_tiled 由 pass 收回）；default 13/13 BLOCK 不變；surfaces／sources 26/26 不變

## not_a_calibration

本版不宣稱 role_aware 已校準；正式校準＝T-53（需獨立校準集）

## supersedes

無（default 模式仍為裁決 T-36-A 定案的規則 1～4＋CLIP_CONFIDENCE_THRESHOLD=0.4）

## change control

criteria_version gate v2 自本 commit 起鎖定；結果出來後不得修改本檔；如需改動＝gate v3 新檔＋新獨立 commit＋使用者核准（WORKFLOW §7）。
