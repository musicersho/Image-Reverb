# Roadmap

規格詳見 [SPEC.md](SPEC.md)，相關研究調查見 [RESEARCH.md](RESEARCH.md)。

## Phase 0 — 研究與可行性驗證（現在）

目標：確認「照片 → 可聽的 IR」整條路走得通，選定 MVP 的 IR 生成路線。

- [ ] 跑通 [Image2Reverb](https://github.com/mdkberry/image2reverb)：用自己的照片生 IR，盲聽評估品質，建立 baseline
- [ ] 測試單目深度估計（Depth Anything V2 / Metric3D）對室內照片的幾何/尺度精度
- [ ] 測試語意分割對牆面/地板/天花板/材質的辨識能力
- [ ] 建立材質 → 各頻段吸音係數對照表（SPEC §6 清單）
- [ ] 用 pyroomacoustics 以手動輸入的房間參數生成 IR，卷積試聽驗證
- [ ] 下載 OpenAIR / RAF 資料集，建立「同場地照片 vs 真實 IR」評測集
- [ ] 細讀 AV-RIR 與 Differentiable Room Acoustic Rendering（2025），評估可借用的部分
- [ ] **決策點**：確定 MVP 採用路線（暫定 A+B 混合：image-source 早期反射 + shaped-noise 晚期殘響，見 SPEC §5）

## Phase 1 — MVP：照片 → IR 匯出（SPEC F-01 ~ F-09）

目標：CLI 或簡單 GUI 工具，輸入照片、輸出可用的 IR (WAV)。

- [ ] 影像分析管線：深度估計 + 材質分割 → 空間幾何與吸音係數
- [ ] 聲學參數推估：體積、Sabine/Eyring → RT60 per band、pre-delay
- [ ] IR 生成引擎 v1（A+B 混合）
- [ ] IR 匯出 WAV（48kHz/24bit，mono/stereo），可載入 Altiverb 等做 A/B
- [ ] 離線卷積試聽（dry + IR → wet）
- [ ] 分析結果視覺化（材質疊圖、參數列表）
- [ ] 參數手動覆寫（尺寸、RT60、材質）
- [ ] **驗收**：SPEC §7 三項標準

## Phase 2 — 即時效果器（SPEC F-10 ~ F-15）

目標：可在 DAW 中使用的 AU/VST3 plugin（macOS 優先）。

- [ ] JUCE 專案架構、partitioned convolution 零延遲引擎
- [ ] 參數組：Wet/Dry、Gain、Pre-delay、Size、Damping、EQ
- [ ] Python 管線整合方案定案（ONNX/CoreML 內嵌 vs local service）
- [ ] Plugin 內照片載入 UI 與分析視覺化
- [ ] IR 庫瀏覽器（內建 preset + 使用者生成）
- [ ] Stereo IR（decorrelation）
- [ ] AU / VST3 打包與 DAW 相容性測試

## Phase 3 — 進階功能（SPEC F-20 ~ F-23）

- [ ] 影片輸入：多幀融合（參考 AV-RIR），解決單張照片的視野外幾何問題
- [ ] Positioner：空間內移動音源（動態早期反射）
- [ ] 神經 IR 生成路線：以聲學參數為條件的生成模型（RESEARCH §2）取代 shaped-noise
- [ ] 空間類型 preset IR 庫（音樂廳、教堂、浴室、車內…）
- [ ] Windows 支援

## 長期願景

- [ ] 即時影片串流 → 動態空間模擬
- [ ] 使用者社群 IR 分享
- [ ] 行動裝置版本（拍照即得該空間 Reverb）
