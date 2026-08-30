# T-37 地雷 #16 修正報告

依 [TASKS.md](../../TASKS.md) T-37 卡（裁決 T-36-A 執行卡 1/3）產出。
數字全部由 [scripts/t37_rebaseline.py](../../scripts/t37_rebaseline.py) 產生，
詳表見 [tables.md](tables.md)。

## 問題

`preprocess.is_equirect()` 原本只看長寬比（2.0 ± 5%），`TunnelToHell.jpg`
（2592×1296，`SOURCES.md` 記載為一般透視照）長寬比剛好落在容差內，被靜默誤判成
360° 環景（地雷 #16，`HANDOFF.md` 第 428 行；T-36 REPORT 再現並補上量化證據）。

## 修法

長寬比通過後，加一道**極點列均勻度檢查**：equirect 的第一/最後一列依定義是
天頂/天底被拉伸成整列，相鄰像素幾乎不變；一般透視照即使長寬比巧合為 2:1，
首尾列仍是正常場景內容，相鄰像素差異明顯較大。統計量：灰階首/尾列相鄰像素
絕對差的平均值，兩者取 max，需低於 `config.EQUIRECT_POLE_DIFF_THRESHOLD`。

### 表 1：門檻推導（見 tables.md 表 1）

4 張真環景（CathedralRoom／DivorceBeach／RacquetballCourt4／SteinmanHall）的
max_diff 最大值為 **0.4859**；TunnelToHell 為 **4.5149**。取兩者幾何中點
附近的 **1.2** 當門檻——真環景側餘裕 2.47x、
TunnelToHell 側餘裕 3.76x，兩側都有充分餘裕。

`is_equirect()` 函式簽章與呼叫點不變（新增的 `pole_diff_threshold` 參數有預設值，
既有呼叫點沿用預設值不必修改）。EXIF/XMP 全景標記維持**不實作**——本卡的極點列
均勻度統計量本身餘裕已足夠大（>2x），不需要疊加更弱的輔助訊號（地雷 #16 已記載
EXIF/XMP 較弱：EchoThief 這批照片已被 Photoshop 重存，中繼資料未必還在）。

## 再基線結果（表 2／表 3，見 tables.md）

**三軸 confidence／gate**：TunnelToHell `dims_source` 從 `equirect_multiview` →
`metric_depth`，`geometry_confidence` 從
`medium` → `low`
（未比原本更自信，符合卡片驗收要求）；
其餘 12 張三軸 confidence／gate **逐值不變**（表 2 已程式化核對）。

**逐面材質判定**：TunnelToHell 的 5 面判定變動（走透視路徑後，
四面牆改為共用單一判定值——這是單張透視照的既有架構限制，不是本卡引入的新行為）；
其餘 72 面**逐面不變**（表 3 已程式化核對）。

## 自我檢查程式化守門

本腳本執行時會對以下任一項不符直接 `sys.exit(1)`（🔴 卡關，不會靜默通過）：

- 除 TunnelToHell 外，任何一張三軸 confidence／gate 有變動
- 除 TunnelToHell 外，任何一面材質判定有變動
- `bedroom_ai_generated` 的 materials_confidence／overall confidence 從 low 變成非 low
  （臥室紅旗，共同鐵則 7）

本次執行**全部通過**，未觸發任何卡關。

## 快取策略（Fable 補充事項）

本腳本**每次執行都是全量重跑**：不讀取、不寫入任何跨次重用的快取——
`output/clip_accuracy/runs/`（T-36 凍結基線）與 `output/material_round/runs/`
（T-33 凍結基線）只被唯讀取用當「before」比較基準，`output/equirect_fix/runs/`
是本次「after」的全新輸出，下次重跑會整個覆蓋重寫，不做增量快取判斷。
理由：T-40（評測快取指紋）排在本卡之後，本卡時點的快取無從辨識新舊碼，
靜默沿用會讓再基線量到修正前的行為。
