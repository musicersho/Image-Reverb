# T-41 透視照 SegFormer 重複載入去重報告

依 [TASKS.md](../../TASKS.md) T-41 卡（插卡 2/4）產出。數字全部由
[scripts/t41_rebaseline.py](../../scripts/t41_rebaseline.py) 產生，詳表見
[tables.md](tables.md)。

## 問題

`run_photo()` 對一張透視照會載入 SegFormer 兩次、完整推論兩次：
`surfaces_from_preprocess()` 已跑過一次 `_load_segmenter()`＋`segment_roles()`
並把結果存進 `detail["class_ratios"]["single"]`；`pipeline.py` 的 scene_cues 段
舊碼又對同一張 `cropped` 圖重新跑一次，只為取 `floor_pixel_ratio`／
`person_pixel_ratio`。`_load_segmenter()` 無 cache，第二次是完整
from_pretrained 載入＋完整推論，時間與記憶體峰值雙倍付費。

## 修法

scene_cues 段直接重用 `surfaces_from_preprocess()` 已經算好的
`detail["class_ratios"]["single"]`，刪掉第二次 `_load_segmenter()`／
`segment_roles()`。`floor_pixel_ratio`／`person_pixel_ratio`／`out_of_domain`／
`out_of_domain_label` 四鍵的計算式與鍵名一個字不改。

## 基線變化表（表 1，共同鐵則 8：本卡零容忍）

13 張三軸 confidence／gate／六面材質／`dims_m`／`volume_m3` **逐值不變**
（表 1 已程式化核對，任何一格漂移本腳本會直接卡關退出，不會靜默通過）。

## scene_cues 四鍵零漂移直證（表 2，陷阱 1）

`analysis.json` 從不記錄 scene_cues，單比對 JSON 證明不了數值沒變。本表對
9 張透視照各用新舊兩條路各算一次 scene_cues 並逐鍵比對，
**全部 bit-identical**（與 `scripts/test_pipeline_dedup.py` part B 同一套邏輯）。

## 耗時對照（表 3）

9 張透視照裡有 9／9 張耗時持平或改善
（環景路徑本來就不受本卡影響，僅供參照，不計入改善統計）。卡片未設定量門檻，
只要求「只允許改善」——本表逐張列出 before/after `elapsed_s` 供人工核對。

## 自我檢查程式化守門

本腳本執行時對以下任一項不符會直接 `sys.exit(1)`（🔴 卡關，不會靜默通過）：

- 13 張裡任何一張三軸 confidence／gate／六面材質／`dims_m`／`volume_m3` 有變動
- 任一張透視照的 scene_cues 四鍵新舊路不一致
- `bedroom_ai_generated` 的 materials_confidence／overall confidence 從 low 變成非 low
  （臥室紅旗，共同鐵則 7）

本次執行**全部通過**，未觸發任何卡關。
