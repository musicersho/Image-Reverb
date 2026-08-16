# Image Reverb

> 給一張照片（或影片），AI 自動分析空間與材質，生成該空間的 Impulse Response，做出擬真的空間模擬 Reverb。

## 簡介

傳統的 Convolution Reverb（如 Audio Ease Altiverb）依賴實地錄製的 Impulse Response（IR）：
在真實空間中播放測試訊號、用麥克風收錄，才能取得該空間的聲學特徵。這意味著 IR 庫受限於
「有人去錄過的空間」。

**Image Reverb** 的目標是打破這個限制：使用者提供一張照片或一段影片，AI 自動：

1. **空間幾何判斷** — 估計房間大小、形狀、天花板高度、空間體積
2. **材質辨識** — 辨識牆面、地板、天花板的材質（木頭、水泥、玻璃、布幕、大理石…），
   對應到各頻段的吸音／散射係數
3. **聲學參數推估** — 推算 RT60（各頻段殘響時間）、Pre-delay、早期反射模式
4. **IR 生成** — 合成該空間的 Impulse Response
5. **卷積運算** — 將 IR 套用到輸入音訊，即時聽到「聲音在這個空間裡」的效果

## 系統架構（規劃中）

```
照片 / 影片
   │
   ├─ 深度估計（monocular depth）──→ 空間幾何 / 體積
   ├─ 語意分割 + 材質辨識 ────────→ 各表面吸音係數
   │
   ▼
聲學參數（RT60 per band, pre-delay, early reflections, 體積）
   │
   ▼
IR 生成引擎（幾何聲學模擬 / 參數化合成 / 神經網路生成）
   │
   ▼
IR (WAV) ──→ 卷積引擎（partitioned convolution, 即時零延遲）
                │
                ▼
            Audio Plugin (AU / VST3) 或桌面應用
```

### IR 生成的三條可能路線

| 路線 | 方法 | 優點 | 缺點 |
|------|------|------|------|
| A. 幾何聲學模擬 | Image-source + ray tracing（如 pyroomacoustics） | 物理可解釋、可調 | 需要較準確的 3D 幾何 |
| B. 參數化合成 | 依 RT60/頻段用 shaped noise 或 FDN 合成 IR | 簡單、穩定、快 | 早期反射較不真實 |
| C. 神經網路生成 | 以影像為條件的生成模型（參考 Image2Reverb, ICCV 2021） | 端到端、潛力大 | 訓練資料與品質不確定 |

## 相關研究 / 工具

- **Image2Reverb** (ICCV 2021) — 從單張影像端到端生成 IR 的先行研究
- **pyroomacoustics** — Python 房間聲學模擬（image-source method）
- **Depth Anything / MiDaS** — 單目深度估計
- **Altiverb 8** — 產品標竿：IR 瀏覽器、Positioner、EQ / Damping、Size 等參數設計值得參考

## 技術棧

尚未定案。初步方向：

- **AI 分析管線**：Python + PyTorch（深度估計、材質分割、聲學參數推估）
- **IR 生成**：Python（pyroomacoustics / 自製合成器）
- **即時音訊 / Plugin**：JUCE (C++)，或先以桌面工具形式驗證
- MVP 先做「照片 → IR (WAV) 匯出」，產出的 IR 可直接載入任何 convolution reverb 驗證效果

## 相關文件

- [SPEC.md](SPEC.md) — 產品規格書（功能需求、架構、驗收標準）
- [WORKFLOW.md](WORKFLOW.md) — 多視窗協作規則（Fable 規劃 / Opus 驗證 / Sonnet 執行）
- [TASKS.md](TASKS.md) — 可直接執行的任務卡
- [RESEARCH.md](RESEARCH.md) — 相關研究與開源專案調查
- [ROADMAP.md](ROADMAP.md) — 開發路線圖
- [TODO.md](TODO.md) — 待辦事項
- [DEV_LOG.md](DEV_LOG.md) — 開發日誌
