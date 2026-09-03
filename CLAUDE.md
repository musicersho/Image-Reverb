# Image Reverb — 給每個 Claude 視窗的入口說明

**每個新視窗開始工作前，必讀本檔案。** 本專案由沒有程式背景的使用者主導（Vibe Coding），
所有溝通使用繁體中文，所有指令由 Claude 執行，不要叫使用者自己改程式碼。

> 📍 **讀完本檔請接著讀 [HANDOFF.md](HANDOFF.md)** — 目前進度、上一輪推翻了什麼、
> 下一步該做什麼、以及踩過的坑。避免重複踩雷。

## 專案是什麼

照片/影片 → AI 分析空間幾何與材質 → 生成 Impulse Response (IR) → Convolution Reverb。
詳見 [SPEC.md](SPEC.md)（規格）、[RESEARCH.md](RESEARCH.md)（相關研究）、[ROADMAP.md](ROADMAP.md)（路線圖）。

## 三種模型的分工（重要）

| 模型 | 角色 | 做什麼 |
|------|------|--------|
| **Fable** | 地圖規劃 | 拆任務、寫 TASKS.md、做架構決策、Phase 結束時重新規劃 |
| **Opus** | 強驗證 | 依 WORKFLOW.md 的驗證標準審查 Sonnet 的成果，只審不寫 |
| **Sonnet** | 工兵執行 | 按 [TASKS.md](TASKS.md) 的任務卡逐字執行，不自行擴大範圍 |

**如果你是 Sonnet**：打開 [TASKS.md](TASKS.md)，找到使用者指定的任務編號（如 T-01），
逐字照做。禁止：跳過驗證步驟、修改任務範圍、動別的任務的檔案、修改 SPEC/ROADMAP。
遇到卡關超過 3 次嘗試 → 停下來，在任務卡狀態寫「🔴 卡關」＋原因，請使用者去問 Fable。

**如果你是 Opus**：打開 [WORKFLOW.md](WORKFLOW.md) 的「驗證標準」章節，
對指定任務執行審查，輸出**四軸判定**（工程／實驗／產品／MVP，見 WORKFLOW §3）與具體理由；
**禁止只寫「✅ 通過」**；驗收門檻有錯要走 WORKFLOW §7 變更控制，不得用附註豁免。不要順手修程式碼。

**如果你是 Fable**：負責 TASKS.md 的增修與架構決策，維持任務卡格式一致。

**所有模型**（2026-09-03 起）：任務狀態一律四軸（工程／實驗／產品／MVP，WORKFLOW §3）；
結果出來後不得改同版驗收門檻（WORKFLOW §7）；`MVP PASS` 只能由 T-17 系列驗收卡寫。

## 每次收工（換視窗/存檔前）必做

依 [WORKFLOW.md](WORKFLOW.md) 的「收工程序」：更新 TASKS.md 任務狀態 → 補 DEV_LOG.md
→ 通過驗證的任務才 commit（格式 `T-XX: 描述`）→ push。**沒做收工程序不准結束。**

## 技術環境

- macOS (Apple Silicon)、Python 虛擬環境在 `.venv/`（T-00 建立後）
- 跑任何 Python 前先 `source .venv/bin/activate`
- 產出的音訊檔放 `output/`、測試素材放 `assets/`、程式碼放 `scripts/`（Phase 0）與 `src/`（Phase 1）
