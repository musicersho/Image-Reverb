# 現行 T-04 合成測試照片

2026-09-20 起，本目錄改用九張 GPT Image 合成影像。四類基本場景沿用 T-17-R2 合成候選圖；大型演唱會巨蛋與四張補充場景重新生成。

完整需求、替換對照與預覽：[素材更新說明](../t04_refresh/README.md)。來源與指紋：[ASSET_MANIFEST.json](../t04_refresh/ASSET_MANIFEST.json)。

檔名改用 `t04_gpt_*.png`，避免新圖誤配舊的 ground truth 或快取。舊圖備份在本機 `assets/photos_legacy_20260920/`；既有報告、凍結 manifest、`data/material_ground_truth.json` 仍只對舊圖成立。固定引用舊檔名的歷史腳本應在原版 checkout 執行；不可將舊檔名直接映射到新圖做驗收。

一般開發分析可直接指定本目錄的新 PNG；逐張掃描本目錄的深度／分割工具會讀取九張新图。合成圖沒有實測尺寸、材質或 RT60 真值，也不是正式 T-17-R2 held-out 集。

> 📌 **2026-09-20 Fable 補（T-04 卡裁定 T-04-R §2 第 4 點，共用圖禁用令）**：本目錄的 `t04_gpt_{bathroom,living,corridor,car}.png` 與 T-17-R2 held-out 逐位元相同。在 T-17-R2 收工並複驗、Fable 寫下解除紀錄之前，
> **不得**對這四張執行 `python -m src.image_reverb` 或任何指定單張的分析／評測腳本，也**不得**單獨執行會掃本目錄的 `scripts/test_depth.py`／`scripts/test_segmentation.py`（只有任務卡或 WORKFLOW §5.4.1 要求的全套 `scripts/test_*.py` 例行執行才容許），
> 不得調參／標註／寫進 `data/`／當新測試夾具；上文「一般開發分析可直接指定本目錄的新 PNG」只適用其餘五張。
> 上文「不是正式 T-17-R2 held-out 集」是裁定前的紀錄，現況見 TASKS.md T-17-R2 卡**裁定 T-17-R2-S**（五張候選圖經 T-60 就位後即為正式 held-out，路徑 S）。
